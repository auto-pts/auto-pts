import subprocess
import os
import logging
import socket
import binascii
import shlex
import btpdef
from btp import btp_hdr_check, BTPError
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
                "-serial mon:stdio -serial unix:/tmp/bt-server-bredr "
                "-serial unix:%s -kernel %s" %
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

    def accept(self):
        """Accept incomming Zephyr connection"""
        logging.debug("%s", self.accept.__name__)

        # Set 10 second socket timeout on accept
        self.sock.settimeout(10.0)
        self.conn, self.addr = self.sock.accept()

    def read(self, timeout=20.0):
        """Read BTP data from socket

        timeout - BTP socket timeout in seconds (20 seconds by default)"""
        logging.debug("%s", self.read.__name__)
        toread_hdr_len = HDR_LEN
        hdr = bytearray(toread_hdr_len)
        hdr_memview = memoryview(hdr)

        # In case of BTP events, the timeout shall be adjustable,
        # update socket timeout if needed.
        if self.conn.gettimeout() is not timeout:
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


class ZephyrCtl:
    '''Zephyr OS Control Class'''

    def __init__(self, kernel_image, tty_file, board_name=None):
        """Constructor."""
        log("%s.%s kernel_image=%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, kernel_image, tty_file,
            board_name)

        if tty_file:
            if (not tty_file.startswith("/dev/tty") and
                not tty_file.startswith("/dev/pts")):
                raise Exception("%s is not a TTY file!" % repr(tty_file))
            if not os.path.exists(tty_file):
                raise Exception("%s TTY file does not exist!" % repr(tty_file))

        if not os.path.isfile(kernel_image):
            raise Exception("kernel_image %s is not a file!" % repr(kernel_image))

        self.kernel_image = kernel_image
        self.tty_file = tty_file
        if self.tty_file: # board is not used with qemu
            self.board = Board(board_name, kernel_image, tty_file)
        self.qemu_process = None
        self.socat_process = None
        self.btp_socket = None

    def start(self):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.btp_socket = BTPSocket()
        self.btp_socket.open()

        if self.tty_file:
            socat_cmd = ("socat -x -v %s,raw,b115200 UNIX-CONNECT:%s" %
                         (self.tty_file, BTP_ADDRESS))

            log("Starting socat process: %s", socat_cmd)

            # socat dies after socket is closed, so no need to kill it
            self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                                  shell=False,
                                                  stdout=IUT_LOG_FO,
                                                  stderr=IUT_LOG_FO)

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


class Board:
    """HW DUT board"""

    arduino_101 = "arduino_101"
    mountatlas = "mountatlas"
    crb = "crb"

    # for command line options
    names = [
        arduino_101,
        mountatlas,
        crb
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
            self.crb : self._get_reset_cmd_crb
        }

        reset_cmd_getter = reset_cmd_getters[self.name]

        reset_cmd = reset_cmd_getter()

        return reset_cmd

    def _get_reset_cmd_arduino_101(self):
        """Return reset command for Arduino 101 DUT

        Dependency: Zephyr SDK

        """
        openocd_bin = "/opt/zephyr-sdk/sysroots/i686-pokysdk-linux/usr/bin/openocd"
        openocd_scripts = "/opt/zephyr-sdk/sysroots/i686-pokysdk-linux/usr/share/openocd/scripts"
        openocd_cfg = os.path.join(
            os.path.split(self.kernel_image)[0],
            "../../../../../boards/x86/arduino_101/support/openocd.cfg")

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_mountatlas(self):
        """Return reset command for MountAtlas DUT

        Dependency: zflash

        """
        openocd_bin = "/usr/local/zflash/openocd/bin/openocd"
        openocd_scripts = "/usr/local/zflash/openocd/share/scripts"
        openocd_cfg = "/usr/local/zflash/boards/mountatlas/openocd.cfg"

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_crb(self):
        """Return magic string for resetting CRB DUT

        """
        return ('sh -c \'echo -n -e "\xAA\xBB\\x00\\x00\\x00" > %s\'' %
                self.tty_file)

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
