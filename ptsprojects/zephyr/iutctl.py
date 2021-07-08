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

import socket
import subprocess
import os
import logging
import shlex
import sys
import time
import serial

from pybtp import defs
from pybtp.types import BTPError
from pybtp.iutctl_common import BTPWorker, BTP_ADDRESS, BTMON, RTT, get_debugger_snr

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"

SERIAL_BAUDRATE = 115200


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


class ZephyrCtl:
    """Zephyr OS Control Class"""

    def __init__(self, args):
        """Constructor."""
        log("%s.%s kernel_image=%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, args.kernel_image,
            args.tty_file, args.board_name)

        self.debugger_snr = None
        self.kernel_image = args.kernel_image
        self.tty_file = args.tty_file
        self.hci = args.hci
        self.native = None

        if self.tty_file and args.board_name:  # DUT is a hardware board, not QEMU
            self.debugger_snr = get_debugger_snr(self.tty_file)
            self.board = Board(args.board_name, args.kernel_image, self)
        else:  # DUT is QEMU or a board that won't be reset
            self.board = None

        self.qemu_process = None
        self.native_process = None
        self.socat_process = None
        self.btp_socket = None
        self.test_case = None
        self.iut_log_file = None

        if self.debugger_snr:
            self.btp_address = BTP_ADDRESS + self.debugger_snr
        else:
            self.btp_address = BTP_ADDRESS

        self.rtt_logger = RTT() if args.rtt_log else None
        self.btmon = BTMON() if args.btmon else None

    def start(self, test_case):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.test_case = test_case
        self.iut_log_file = open(os.path.join(test_case.log_dir, "autopts-iutctl-zephyr.log"), "a")

        self.flush_serial()

        self.btp_socket = BTPWorker()
        self.btp_socket.open(self.btp_address)

        if self.tty_file:
            if sys.platform == "win32":
                # On windows socat.exe does not support setting serial baud rate.
                # Set it with 'mode' from cmd.exe
                com = "COM" + str(int(self.tty_file["/dev/ttyS".__len__():]) + 1)
                mode_cmd = (">nul 2>nul cmd.exe /c \"mode " + com + "BAUD=115200 PARITY=n DATA=8 STOP=1\"")
                os.system(mode_cmd)

                socat_cmd = ("socat.exe -x -v tcp:" + socket.gethostbyname(socket.gethostname()) +
                             ":%s,retry=100,interval=1 %s,raw,b115200" %
                             (self.btp_socket.sock.getsockname()[1], self.tty_file))
            else:
                socat_cmd = ("socat -x -v %s,rawer,b115200 UNIX-CONNECT:%s" %
                             (self.tty_file, self.btp_address))

            log("Starting socat process: %s", socat_cmd)

            # socat dies after socket is closed, so no need to kill it
            self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                                  shell=False,
                                                  stdout=self.iut_log_file,
                                                  stderr=self.iut_log_file)
        elif self.hci is not None:
            socat_cmd = ("socat -x -v %%s,rawer,b115200 UNIX-CONNECT:%s &" %
                         self.btp_address)

            native_cmd = ("%s --bt-dev=hci%d --attach_uart_cmd=\"%s\"" %
                          (self.kernel_image, self.hci, socat_cmd))

            log("Starting native zephyr process: %s", native_cmd)

            # TODO check if zephyr process has started correctly
            self.native_process = subprocess.Popen(shlex.split(native_cmd),
                                                   shell=False,
                                                   stdout=self.iut_log_file,
                                                   stderr=self.iut_log_file)
        else:
            qemu_cmd = get_qemu_cmd(self.kernel_image)

            log("Starting QEMU zephyr process: %s", qemu_cmd)

            # TODO check if zephyr process has started correctly
            self.qemu_process = subprocess.Popen(shlex.split(qemu_cmd),
                                                 shell=False,
                                                 stdout=self.iut_log_file,
                                                 stderr=self.iut_log_file)

        self.btp_socket.accept()

    def flush_serial(self):
        log("%s.%s", self.__class__, self.flush_serial.__name__)
        # Try to read data or timeout
        try:
            ser = serial.Serial(port=self.tty_file,
                                baudrate=SERIAL_BAUDRATE, timeout=1)
            ser.read(99999)
            ser.close()
        except serial.SerialException:
            pass

    def btmon_start(self):
        if self.btmon:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_btmon.log')
            self.btmon.start(log_file, self.debugger_snr)

    def btmon_stop(self):
        if self.btmon:
            self.btmon.stop()

    def rtt_logger_start(self):
        if self.rtt_logger:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_iutctl.log')
            self.rtt_logger.start('Logger', log_file, self.debugger_snr)

    def rtt_logger_stop(self):
        if self.rtt_logger:
            self.rtt_logger.stop()

    def reset(self):
        """Restart IUT related processes and reset the IUT"""
        log("%s.%s", self.__class__, self.reset.__name__)

        self.stop()
        self.start(self.test_case)
        self.flush_serial()

        if not self.board:
            return

        self.rtt_logger_stop()
        self.btmon_stop()

        self.board.reset()

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        self.reset()

        tuple_hdr, tuple_data = self.btp_socket.read()

        try:
            if (tuple_hdr.svc_id != defs.BTP_SERVICE_ID_CORE or
                    tuple_hdr.op != defs.CORE_EV_IUT_READY):
                raise BTPError("Failed to get ready event")
        except BTPError as err:
            log("Unexpected event received (%s), expected IUT ready!", err)
            self.stop()
        else:
            log("IUT ready event received OK")

        self.rtt_logger_start()
        self.btmon_start()

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.native_process and self.native_process.poll() is None:
            self.native_process.terminate()
            self.native_process.wait()  # do not let zombies take over
            self.native_process = None

        if self.qemu_process and self.qemu_process.poll() is None:
            time.sleep(1)
            self.qemu_process.terminate()
            self.qemu_process.wait()  # do not let zombies take over
            self.qemu_process = None

        if self.iut_log_file:
            self.iut_log_file.close()
            self.iut_log_file = None

        self.rtt_logger_stop()
        self.btmon_stop()

        if self.socat_process:
            self.socat_process.terminate()
            self.socat_process.wait()
            self.socat_process = None


class ZephyrCtlStub:
    """Zephyr OS Control Class with stubs for testing"""

    def __init__(self):
        """Constructor."""

    def start(self):
        """Starts the Zephyr OS"""
        log("%s.%s", self.__class__, self.start.__name__)

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)


class Board:
    """HW DUT board"""

    nrf52 = "nrf52"
    reel = "reel_board"

    # for command line options
    names = [
        nrf52,
        reel
    ]

    def __init__(self, board_name, kernel_image, iutctl):
        """Constructor of board"""
        if board_name not in self.names:
            raise Exception("Board name %s is not supported!" % board_name)

        self.name = board_name
        self.kernel_image = kernel_image
        self.iutctl = iutctl
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with openocd

        With introduction of persistent storage in DUT flashing kernel image in
        addition to reset will become necessary

        """
        log("About to reset DUT: %r", self.reset_cmd)

        reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                         shell=False,
                                         stdout=self.iutctl.iut_log_file,
                                         stderr=self.iutctl.iut_log_file)
        if reset_process.wait():
            logging.error("openocd reset failed")

    @staticmethod
    def get_openocd_reset_cmd(openocd_bin, openocd_scripts, openocd_cfg):
        """Compute openocd reset command"""
        if not os.path.isfile(openocd_bin):
            raise Exception("openocd {} not found!".format(openocd_bin))

        if not os.path.isdir(openocd_scripts):
            raise Exception("openocd scripts {} not found!".format(openocd_scripts))

        if not os.path.isfile(openocd_cfg):
            raise Exception("openocd config {} not found!".format(openocd_cfg))

        reset_cmd = ('%s -s %s -f %s -c "init" -c "targets 1" '
                     '-c "reset halt" -c "reset run" -c "shutdown"' %
                     (openocd_bin, openocd_scripts, openocd_cfg))

        return reset_cmd

    def get_reset_cmd(self):
        """Return reset command for a board"""
        reset_cmd_getters = {
            self.nrf52: self._get_reset_cmd_nrf52,
            self.reel: self._get_reset_cmd_reel
        }

        reset_cmd_getter = reset_cmd_getters[self.name]

        reset_cmd = reset_cmd_getter()

        return reset_cmd

    def _get_reset_cmd_nrf52(self):
        """Return reset command for nRF52 DUT

        Dependency: nRF5x command line tools

        """
        return 'nrfjprog -f nrf52 -r -s ' + self.iutctl.debugger_snr

    @staticmethod
    def _get_reset_cmd_reel():
        """Return reset command for Reel_Board DUT

        Dependency: pyocd command line tools

        """
        return 'pyocd cmd -c reset'


def get_iut():
    return ZEPHYR


def init_stub():
    """IUT init routine for testings"""
    global ZEPHYR
    ZEPHYR = ZephyrCtlStub()


def init(args):
    """IUT init routine

    args -- Argument
    """
    global ZEPHYR

    ZEPHYR = ZephyrCtl(args)


def cleanup():
    """IUT cleanup routine"""
    global ZEPHYR
    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
