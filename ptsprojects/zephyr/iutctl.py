import subprocess
import os
import signal
import logging
import socket
import binascii
import shlex
import time
from btpparser import enc_frame, dec_hdr, dec_data, HDR_LEN

log = logging.debug
ZEPHYR = None

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

# qemu log file object
IUT_LOG_FO = None


class BTPSocket(object):

    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def open(self):
        """Open sockets for Viper"""
        if os.path.exists(BTP_ADDRESS):
            os.remove(BTP_ADDRESS)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(BTP_ADDRESS)

        # queue only one connection
        self.sock.listen(1)

    def accept(self):
        """Accept incomming Zephyr connection"""
        logging.debug("%s", self.accept.__name__)

        # This will hang forever if Zephyr don't try to connect
        self.conn, self.addr = self.sock.accept()
        self.conn.settimeout(120) # BTP socket timeout in seconds

    def read(self):
        """Read BTP data from socket"""
        logging.debug("%s", self.read.__name__)
        toread_hdr_len = HDR_LEN
        hdr = bytearray(toread_hdr_len)
        hdr_memview = memoryview(hdr)

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

    def __init__(self, iut_init):
        """Constructor."""
        log("%s.%s iut_init=%s",
            self.__class__, self.__init__.__name__, iut_init)

        self.iut_init = iut_init
        self.iut_process = None

    def start(self):
        """Start the BTP tester of the Zephyr OS

        [1] Currently BTP lacks connection establishment handshake. Also, when
            BTP tester starts, it flushes all the data from the UART pipe. Due
            to this, tester application running in QEMU flushes first BTP
            message it receives. Hence, BTP communication between BTP tester
            and auto-pts breaks. This does not happen when tester application
            runs on hardware.

            There are two possible workarounds to this problem:

            1. Revert zephyr commit that flushes UART pipe,
               4800266cc652a70572255affa14dd93846d701c3

            2. Put auto-pts to sleep after starting tester in QEMU

            Workaround 2 is currently implemented in this function.

            Once handshake is implemented in BTP the workarounds will not be
            needed anymore.

            BTP connection establishment handshake issue:
            https://01.org/jira/browse/BZ-192

        """

        log("%s.%s", self.__class__, self.start.__name__)

        self.btp_socket = BTPSocket()
        self.btp_socket.open()
        # The os.setsid() is passed in the argument preexec_fn so
        # it's run after the fork() and before  exec() to run the shell.
        self.iut_process = subprocess.Popen([self.iut_init], shell=False,
                                            stdout=IUT_LOG_FO,
                                            stderr=IUT_LOG_FO,
                                            preexec_fn=os.setsid)
        time.sleep(1) # see [1]
        self.btp_socket.accept()

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.iut_process and self.iut_process.poll() is None:
            # Send the signal to all the process groups
            os.killpg(os.getpgid(self.iut_process.pid), signal.SIGTERM)
            self.iut_process.wait()
            self.iut_process = None


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

def init(iut_init):
    """IUT init routine

    iut_init - Script that will be executed as one of TC pre-run commands.
               It may be used to e.g. reset IUT etc.
    """
    global IUT_LOG_FO
    global ZEPHYR

    IUT_LOG_FO = open("iut-zephyr.log", "w")

    ZEPHYR = ZephyrCtl(iut_init)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, ZEPHYR
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
