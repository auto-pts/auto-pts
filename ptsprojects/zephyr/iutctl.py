#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

import subprocess
import os
import logging
import socket
import binascii
import shlex
import threading
import Queue

import btpdef
from btp import btp_hdr_check, BTPError, event_handler
from btpparser import enc_frame, dec_hdr, dec_data, HDR_LEN

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

# qemu log file object
IUT_LOG_FO = None


def get_qemu_cmd(kernel_image):
    """Returns qemu command to start Zephyr

    kernel_image -- Path to Zephyr kernel image"""

    qemu_cmd = ("%s -cpu cortex-m3 -machine lm3s6965evb -nographic "
                "-serial mon:stdio "
                "-serial unix:%s "
                "-serial unix:/tmp/bt-server-bredr "
                "-kernel %s" %
                (QEMU_BIN, BTP_ADDRESS, kernel_image))

    return qemu_cmd


class BTPSocket(object):

    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def open(self):
        """Open BTP socket for Zephyr"""
        if os.path.exists(BTP_ADDRESS):
            os.remove(BTP_ADDRESS)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(BTP_ADDRESS)

        # queue only one connection
        self.sock.listen(1)

    def accept(self, timeout=10.0):
        """Accept incomming Zephyr connection

        timeout - accept timeout in seconds"""

        self.sock.settimeout(timeout)
        self.conn, self.addr = self.sock.accept()
        self.sock.settimeout(None)

    def read(self, timeout=20.0):
        """Read BTP data from socket

        timeout - read timeout in seconds"""
        toread_hdr_len = HDR_LEN
        hdr = bytearray(toread_hdr_len)
        hdr_memview = memoryview(hdr)
        self.conn.settimeout(timeout)

        # Gather frame header
        while toread_hdr_len:
            nbytes = self.conn.recv_into(hdr_memview, toread_hdr_len)
            hdr_memview = hdr_memview[nbytes:]
            toread_hdr_len -= nbytes

        tuple_hdr = dec_hdr(hdr)
        toread_data_len = tuple_hdr.data_len

        logging.debug("Received: hdr: %r %r", tuple_hdr, hdr)

        data = bytearray(toread_data_len)
        data_memview = memoryview(data)

        # Gather optional frame data
        while toread_data_len:
            nbytes = self.conn.recv_into(data_memview, toread_data_len)
            data_memview = data_memview[nbytes:]
            toread_data_len -= nbytes

        tuple_data = dec_data(data)
        log("Received data: %r, %r", tuple_data, data)
        self.conn.settimeout(None)

        return tuple_hdr, tuple_data

    def send(self, svc_id, op, ctrl_index, data):
        """Send BTP formated data over socket"""
        logging.debug("%s, %r %r %r %r",
                      self.send.__name__, svc_id, op, ctrl_index, data)

        if isinstance(data, int):
            data = str(data)
            if len(data) == 1:
                data = "0%s" % data
                data = binascii.unhexlify(data)

        hex_data = binascii.hexlify(data)
        logging.debug("btpclient command: send %d %d %d %s",
                      svc_id, op, ctrl_index, hex_data)

        bin = enc_frame(svc_id, op, ctrl_index, data)

        logging.debug("sending frame %r", bin)
        self.conn.send(bin)

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

        self.sock = None
        self.conn = None
        self.addr = None


class BTPWorker(BTPSocket):
    def __init__(self):
        super(BTPWorker, self).__init__()

        self.__rx_queue__ = Queue.Queue()
        self.__running__ = threading.Event()

        self.__rx_worker__ = threading.Thread(target=self.__rx_task__)

    def __rx_task__(self):
        while self.__running__.is_set():
            try:
                data = super(BTPWorker, self).read(timeout=1.0)

                hdr = data[0]
                if hdr.op >= 0x80:
                    event_handler(*data)

                self.__rx_queue__.put(data)
            except socket.timeout:
                pass

    @staticmethod
    def __read_timeout__(flag):
        flag.clear()

    def read(self, timeout=20.0):
        logging.debug("%s", self.read.__name__)

        flag = threading.Event()
        flag.set()

        t = threading.Timer(timeout, self.__read_timeout__, [flag])
        t.start()

        while flag.is_set():
            if self.__rx_queue__.empty():
                continue

            t.cancel()

            data = self.__rx_queue__.get()
            self.__rx_queue__.task_done()

            return data

        raise socket.timeout

    def send_wait_rsp(self, svc_id, op, ctrl_index, data, cb=None, user_data=None):
        super(BTPWorker, self).send(svc_id, op, ctrl_index, data)
        ret = True

        while ret:
            tuple_hdr, tuple_data = self.read()

            if tuple_hdr.svc_id != svc_id:
                raise BTPError("Incorrect service ID %s in the response, expected "
                               "%s!" % (tuple_hdr.svc_id, svc_id))

            if tuple_hdr.op == btpdef.BTP_STATUS:
                raise BTPError("Error opcode in response!")

            if op != tuple_hdr.op:
                raise BTPError("Invalid opcode 0x%.2x in the response, expected "
                               "0x%.2x!" % (tuple_hdr.op, op))

            if cb and callable(cb):
                ret = cb(tuple_data, user_data)
            else:
                return tuple_data

    def __reset_rx_queue__(self):
        while not self.__rx_queue__.empty():
            try:
                self.__rx_queue__.get_nowait()
            except Queue.Empty:
                continue

            self.__rx_queue__.task_done()

    def accept(self, timeout=10.0):
        logging.debug("%s", self.accept.__name__)

        super(BTPWorker, self).accept(timeout)

        self.__running__.set()
        self.__rx_worker__.start()

    def close(self):
        self.__running__.clear()
        self.__rx_worker__.join()
        self.__reset_rx_queue__()

        super(BTPWorker, self).close()


class ZephyrCtl:
    '''Zephyr OS Control Class'''

    def __init__(self, kernel_image, tty_file, board_name=None):
        """Constructor."""
        log("%s.%s kernel_image=%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, kernel_image, tty_file,
            board_name)

        self.kernel_image = kernel_image
        self.tty_file = tty_file

        if self.tty_file and board_name: # DUT is a hardware board, not QEMU
            self.board = Board(board_name, kernel_image, tty_file)
        else: # DUT is QEMU or a board that won't be reset
            self.board = None

        self.qemu_process = None
        self.socat_process = None
        self.btp_socket = None

    def start(self):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.btp_socket = BTPWorker()
        self.btp_socket.open()

        if self.tty_file:
            socat_cmd = ("socat -x -v %s,rawer,b115200 UNIX-CONNECT:%s" %
                         (self.tty_file, BTP_ADDRESS))

            log("Starting socat process: %s", socat_cmd)

            # socat dies after socket is closed, so no need to kill it
            self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                                  shell=False,
                                                  stdout=IUT_LOG_FO,
                                                  stderr=IUT_LOG_FO)

            if self.board:
                self.board.reset()

        else:
            qemu_cmd = get_qemu_cmd(self.kernel_image)

            log("Starting QEMU zephyr process: %s", qemu_cmd)

            # TODO check if zephyr process has started correctly
            self.qemu_process = subprocess.Popen(shlex.split(qemu_cmd),
                                                 shell=False,
                                                 stdout=IUT_LOG_FO,
                                                 stderr=IUT_LOG_FO)

        self.btp_socket.accept()

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        tuple_hdr, tuple_data = self.btp_socket.read()

        try:
            btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_CORE,
                          btpdef.CORE_EV_IUT_READY)
        except BTPError as err:
            log("Unexpected event received (%s), expected IUT ready!", err)
            self.stop()
        else:
            log("IUT ready event received OK")

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.qemu_process and self.qemu_process.poll() is None:
            self.qemu_process.terminate()
            self.qemu_process.wait()  # do not let zombies take over
            self.qemu_process = None


class ZephyrCtlStub:
    '''Zephyr OS Control Class with stubs for testing'''

    def __init__(self):
        """Constructor."""
        pass

    def start(self):
        """Starts the Zephyr OS"""
        log("%s.%s", self.__class__, self.start.__name__)

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

    def wait_iut_ready_event(self):
        """Wait for IUT to be ready Zephyr OS"""
        log("%s.%s", self.__class__, self.wait_iut_ready_event.__name__)


class Board:
    """HW DUT board"""

    arduino_101 = "arduino_101"
    mountatlas = "mountatlas"
    crb = "crb"
    nrf52 = "nrf52"

    # for command line options
    names = [
        arduino_101,
        mountatlas,
        crb,
        nrf52
    ]

    def __init__(self, board_name, kernel_image, tty_file):
        """Constructor of board"""
        if board_name not in self.names:
            raise Exception("Board name %s is not supported!" % board_name)

        self.name = board_name
        self.kernel_image = kernel_image
        self.tty_file = tty_file
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with openocd

        With introduction of persistent storage in DUT flashing kernel image in
        addition to reset will become necessary

        """
        log("About to reset DUT: %r", self.reset_cmd)

        reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                         shell=False,
                                         stdout=IUT_LOG_FO,
                                         stderr=IUT_LOG_FO)
        if reset_process.wait():
            logging.error("openocd reset failed")

    def get_openocd_reset_cmd(self, openocd_bin, openocd_scripts, openocd_cfg):
        """Compute openocd reset command"""
        if not os.path.isfile(openocd_bin):
            raise Exception("openocd %r not found!", openocd_bin)

        if not os.path.isdir(openocd_scripts):
            raise Exception("openocd scripts %r not found!", openocd_scripts)

        if not os.path.isfile(openocd_cfg):
            raise Exception("openocd config %r not found!", openocd_cfg)

        reset_cmd = ('%s -s %s -f %s -c "init" -c "targets 1" '
                     '-c "reset halt" -c "reset run" -c "shutdown"' %
                     (openocd_bin, openocd_scripts, openocd_cfg))

        return reset_cmd

    def get_reset_cmd(self):
        """Return reset command for a board"""
        reset_cmd_getters = {
            self.arduino_101 : self._get_reset_cmd_arduino_101,
            self.mountatlas : self._get_reset_cmd_mountatlas,
            self.crb : self._get_reset_cmd_crb,
            self.nrf52 : self._get_reset_cmd_nrf52
        }

        reset_cmd_getter = reset_cmd_getters[self.name]

        reset_cmd = reset_cmd_getter()

        return reset_cmd

    def _get_reset_cmd_arduino_101(self):
        """Return reset command for Arduino 101 DUT

        Dependency: Zephyr SDK

        """
        openocd_bin = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/bin/openocd"
        openocd_scripts = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/share/openocd/scripts"
        openocd_cfg = os.path.join(
            os.path.split(self.kernel_image)[0],
            "../../../../../boards/x86/arduino_101/support/openocd.cfg")

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_mountatlas(self):
        """Return reset command for MountAtlas DUT

        Dependency: zflash

        """
        openocd_bin = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/bin/openocd"
        openocd_scripts = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/share/openocd/scripts"
        openocd_cfg = os.path.join(
            os.path.split(self.kernel_image)[0],
            "../../../../../boards/x86/quark_se_c1000_devboard/support/")

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_crb(self):
        """Return magic string for resetting CRB DUT

        """
        return ('sh -c \'echo -n -e "\xAA\xBB\\x00\\x00\\x00" > %s\'' %
                self.tty_file)

    def _get_reset_cmd_nrf52(self):
        """Return reset command for nRF52 DUT

        Dependency: nRF5x command line tools

        """
        return 'nrfjprog -f nrf52 -r'

def get_zephyr():
    return ZEPHYR


def init_stub():
    """IUT init routine for testings"""
    global ZEPHYR
    ZEPHYR = ZephyrCtlStub()

def init(kernel_image, tty_file, board=None):
    """IUT init routine

    kernel_image -- Path to Zephyr kernel image
    tty_file -- Path to TTY file, if specified QEMU will not be used and
                BTP communication with HW DUT will be done over this TTY.
    board -- HW DUT board to use for testing. This parameter is used only
             if tty_file is specified
    """
    global IUT_LOG_FO
    global ZEPHYR

    IUT_LOG_FO = open("iut-zephyr.log", "w")

    ZEPHYR = ZephyrCtl(kernel_image, tty_file, board)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, ZEPHYR
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
