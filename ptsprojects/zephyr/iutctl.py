import subprocess
import os
import logging
import socket
import binascii
import shlex
from btpparser import enc_frame, dec_hdr, dec_data
from msgdefs import HDR_LEN

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"
QEMU_UNIX_PATH = "/tmp/ubt_tester"

# qemu log file object
QEMU_LOG_FO = None

# microkernel.elf
ZEPHYR_KERNEL_IMAGE = None

class ZephyrCtl:
    '''Zephyr OS Control Class'''

    def __init__(self):
        """Constructor."""

        assert ZEPHYR_KERNEL_IMAGE, "Kernel image file is not set!"


        self.kernel_image = ZEPHYR_KERNEL_IMAGE
        self.qemu_process = None
        self.sock = None
        self.conn = None
        self.addr = None

    def start(self):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        qemu_cmd = "%s -cpu cortex-m3 -machine lm3s6965evb -nographic " \
                        "-serial mon:stdio -serial unix:/tmp/bt-server-bredr " \
                        "-serial unix:%s -kernel %s" \
                        % (QEMU_BIN, QEMU_UNIX_PATH, self.kernel_image)

        log("Starting QEMU zephyr process: %s", qemu_cmd)

        # TODO check if zephyr process has started correctly
        self.qemu_process = subprocess.Popen(shlex.split(qemu_cmd),
                                             shell = False,
                                             stdout = QEMU_LOG_FO,
                                             stderr = QEMU_LOG_FO)

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        self.sock = None
        self.conn = None
        self.addr = None

        if self.qemu_process.poll() is None:
            self.qemu_process.terminate()
            self.qemu_process.wait() # do not let zombies take over

    def socks_open(self):
        """Open sockets for Viper"""
        if os.path.exists(QEMU_UNIX_PATH):
            os.remove(QEMU_UNIX_PATH)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(QEMU_UNIX_PATH)

        #queue only one connection
        self.sock.listen(1)

    def socks_accept(self):
        """Accept incomming Zephyr connection"""
        #This will hang forever if Zephyr don't try to connect
        self.conn, self.addr = self.sock.accept()

        self.conn.setblocking(0)

    def sock_read(self, svc_id, op, data):
        """Read BTP data from socket"""
        toread_hdr_len = HDR_LEN
        hdr = bytearray(toread_hdr_len)
        hdr_memview = memoryview(hdr)

        #Gather frame header
        while toread_hdr_len:
            try:
                nbytes = self.conn.recv_into(hdr_memview, toread_hdr_len)
                hdr_memview = hdr_memview[nbytes:]
                toread_hdr_len -= nbytes
            except:
                #TODO timeout
                continue

        tuple_hdr = dec_hdr(hdr)
        toread_data_len = tuple_hdr.data_len

        log("Received hdr: %s", tuple_hdr)

        if not toread_data_len:
            if tuple_hdr.svc_id != svc_id:
                log("Received wrong hdr, expected svc id = %s, got = %s",
                    binascii.hexlify(svc_id), binascii.hexlify(tuple_hdr.svc_id))
            if tuple_hdr.op != op:
                log("Received wrong hdr, expected opcode = %s, got = %s",
                    binascii.hexlify(op), binascii.hexlify(tuple_hdr.op))
            return

        data = bytearray(toread_data_len)
        data_memview = memoryview(data)

        #Gather optional frame data
        while toread_data_len:
            try:
                nbytes = self.conn.recv_into(data_memview, toread_data_len)
                data_memview = data_memview[nbytes:]
                toread_data_len -= nbytes
            except:
                #TODO timeout
                continue

        tuple_data = dec_data(data)

        log("Received data: %s", tuple_data)

        if tuple_data != data:
            #TODO handle if received other than expected data
            log("Received wrong data, expected data = %s, got = %s",
                    binascii.hexlify(data), binascii.hexlify(tuple_data))

    def sock_send(self, svc_id, op, data):
        """Send BTP formated data over socket"""
        bin = enc_frame(svc_id, op, data)
        self.conn.send(bin)

def get_zephyr():
    return ZEPHYR

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

    if ZEPHYR is None:
        return

    ZEPHYR.stop()
    ZEPHYR = None
