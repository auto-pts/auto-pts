import subprocess
import os
import logging
import socket
import binascii
import shlex
from btpparser import enc_frame, dec_hdr, dec_data, HDR_LEN

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"
QEMU_UNIX_PATH = "/tmp/bt-stack-tester"

# qemu log file object
QEMU_LOG_FO = None

# microkernel.elf
ZEPHYR_KERNEL_IMAGE = None


def get_qemu_cmd(kernel_image):
    """Returns qemu command to start Zephyr

    kernel_image -- Path to Zephyr kernel image"""

    qemu_cmd = ("%s -cpu cortex-m3 -machine lm3s6965evb -nographic "
                "-serial mon:stdio -serial unix:/tmp/bt-server-bredr "
                "-serial unix:%s -kernel %s" %
                (QEMU_BIN, QEMU_UNIX_PATH, kernel_image))

    return qemu_cmd


class BTPSocket(object):
    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def open(self):
        """Open sockets for Viper"""
        if os.path.exists(QEMU_UNIX_PATH):
            os.remove(QEMU_UNIX_PATH)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(QEMU_UNIX_PATH)

        # queue only one connection
        self.sock.listen(1)

    def accept(self):
        """Accept incomming Zephyr connection"""
        logging.debug("%s", self.accept.__name__)

        # This will hang forever if Zephyr don't try to connect
        self.conn, self.addr = self.sock.accept()

        self.conn.setblocking(0)

    def read(self):
        """Read BTP data from socket"""
        logging.debug("%s", self.read.__name__)
        toread_hdr_len = HDR_LEN
        hdr = bytearray(toread_hdr_len)
        hdr_memview = memoryview(hdr)

        # Gather frame header
        while toread_hdr_len:
            try:
                nbytes = self.conn.recv_into(hdr_memview, toread_hdr_len)
                hdr_memview = hdr_memview[nbytes:]
                toread_hdr_len -= nbytes
            except:
                # TODO timeout
                continue

        tuple_hdr = dec_hdr(hdr)
        toread_data_len = tuple_hdr.data_len

        logging.debug("Received: hdr: %r %r", tuple_hdr, hdr)

        data = bytearray(toread_data_len)
        data_memview = memoryview(data)

        # Gather optional frame data
        while toread_data_len:
            try:
                nbytes = self.conn.recv_into(data_memview, toread_data_len)
                data_memview = data_memview[nbytes:]
                toread_data_len -= nbytes
            except:
                # TODO timeout
                continue

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

    def __init__(self):
        """Constructor."""

        assert ZEPHYR_KERNEL_IMAGE, "Kernel image file is not set!"

        self.kernel_image = ZEPHYR_KERNEL_IMAGE
        self.qemu_process = None
        self.btp_socket = None

    def start(self):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        qemu_cmd = get_qemu_cmd(self.kernel_image)

        self.btp_socket = BTPSocket()
        self.btp_socket.open()

        log("Starting QEMU zephyr process: %s", qemu_cmd)

        # TODO check if zephyr process has started correctly
        self.qemu_process = subprocess.Popen(shlex.split(qemu_cmd),
                                             shell=False,
                                             stdout=QEMU_LOG_FO,
                                             stderr=QEMU_LOG_FO)

        self.btp_socket.accept()

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


def get_zephyr():
    return ZEPHYR


def init_stub():
    """IUT init routine for testings"""
    global ZEPHYR
    ZEPHYR = ZephyrCtlStub()


def init(kernel_image):
    """IUT init routine

    kernel_image -- Path to Zephyr kernel image"""

    global QEMU_LOG_FO
    global ZEPHYR_KERNEL_IMAGE
    global ZEPHYR

    QEMU_LOG_FO = open("qemu-zephyr.log", "w")

    if not os.path.isfile(kernel_image):
        raise Exception("QEMU kernel image %s is not a file!" %
                        repr(kernel_image))

    ZEPHYR_KERNEL_IMAGE = kernel_image

    ZEPHYR = ZephyrCtl()


def cleanup():
    """IUT cleanup routine"""
    global QEMU_LOG_FO, ZEPHYR
    QEMU_LOG_FO.close()
    QEMU_LOG_FO = None

    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
