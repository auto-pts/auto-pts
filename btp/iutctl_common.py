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

import os
import logging
import socket
import binascii
import threading
import Queue

import defs
from types import BTPError
from parser import enc_frame, dec_hdr, dec_data, HDR_LEN

log = logging.debug

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

EVENT_HANDLER = None

def set_event_handler(event_handler):
    """This is required by BTPWorker to drive stack"""
    global EVENT_HANDLER

    EVENT_HANDLER = event_handler

class BTPSocket(object):

    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def open(self):
        """Open BTP socket for IUT"""
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

        self._rx_queue = Queue.Queue()
        self._running = threading.Event()

        self._rx_worker = threading.Thread(target=self._rx_task)

        self.event_handler_cb = None

    def _rx_task(self):
        while self._running.is_set():
            try:
                data = super(BTPWorker, self).read(timeout=1.0)

                hdr = data[0]
                if hdr.op >= 0x80:
                    # Do not put handled events on RX queue
                    ret = EVENT_HANDLER(*data)
                    if ret is True:
                        continue

                self._rx_queue.put(data)
            except socket.timeout:
                pass

    @staticmethod
    def _read_timeout(flag):
        flag.clear()

    def read(self, timeout=20.0):
        logging.debug("%s", self.read.__name__)

        flag = threading.Event()
        flag.set()

        t = threading.Timer(timeout, self._read_timeout, [flag])
        t.start()

        while flag.is_set():
            if self._rx_queue.empty():
                continue

            t.cancel()

            data = self._rx_queue.get()
            self._rx_queue.task_done()

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

            if tuple_hdr.op == defs.BTP_STATUS:
                raise BTPError("Error opcode in response!")

            if op != tuple_hdr.op:
                raise BTPError("Invalid opcode 0x%.2x in the response, expected "
                               "0x%.2x!" % (tuple_hdr.op, op))

            if cb and callable(cb):
                ret = cb(tuple_data, user_data)
            else:
                return tuple_data

    def _reset_rx_queue(self):
        while not self._rx_queue.empty():
            try:
                self._rx_queue.get_nowait()
            except Queue.Empty:
                continue

            self._rx_queue.task_done()

    def accept(self, timeout=10.0):
        logging.debug("%s", self.accept.__name__)

        super(BTPWorker, self).accept(timeout)

        self._running.set()
        self._rx_worker.start()

    def close(self):
        self._running.clear()

        if self._rx_worker.is_alive():
            self._rx_worker.join()

        self._reset_rx_queue()

        super(BTPWorker, self).close()

    def register_event_handler(self, event_handler):
        self.event_handler_cb = event_handler
