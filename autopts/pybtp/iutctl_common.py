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

import logging
import os
import queue
import socket
import sys
import threading
import binascii


from abc import abstractmethod

from .btp import defs
from .btp.btpdefs.types import BTPError
from .parser import enc_frame, dec_hdr, dec_data, HDR_LEN
from .btp.btp import event_handler

log = logging.debug

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"


class BTPSocket:

    def __init__(self):
        self.conn = None
        self.addr = None

    @abstractmethod
    def open(self, address):
        pass

    @abstractmethod
    def accept(self, timeout=10.0):
        pass

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
            if nbytes == 0 and toread_hdr_len != 0:
                # The connection is closed and the BTPSocket should be reinited
                raise socket.error
            logging.debug("Read %d bytes", nbytes)
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
            logging.debug("Read %d bytes data", nbytes)
            if nbytes == 0 and toread_data_len != 0:
                raise socket.error
            data_memview = data_memview[nbytes:]
            toread_data_len -= nbytes

        data_string = binascii.hexlify(data).decode('utf-8')
        data_string = ' '.join(f'{data_string[i:i+2]}' for i in range(0, len(data_string), 2))
        log(f"Received data: { {data_string} }, {data}")

        self.conn.settimeout(None)
        return tuple_hdr, dec_data(data)

    def send(self, svc_id, op, ctrl_index, data):
        """Send BTP formated data over socket"""
        logging.debug("%s, %r %r %r %r",
                      self.send.__name__, svc_id, op, ctrl_index, str(data))

        frame = enc_frame(svc_id, op, ctrl_index, data)

        logging.debug("sending frame %r", frame.hex())
        self.conn.send(frame)

    @abstractmethod
    def close(self):
        pass


class BTPSocketSrv(BTPSocket):

    def __init__(self):
        super().__init__()
        self.sock = None

    def open(self, addres=BTP_ADDRESS):
        """Open BTP socket for IUT"""
        if os.path.exists(addres):
            os.remove(addres)

        if sys.platform == "win32":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((socket.gethostname(), 0))
        else:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(addres)

        # queue only one connection
        self.sock.listen(1)

    def accept(self, timeout=10.0):

        """Accept incomming Zephyr connection

        timeout - accept timeout in seconds"""

        self.sock.settimeout(timeout)
        self.conn, self.addr = self.sock.accept()
        self.sock.settimeout(None)

    def close(self):
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
            self.sock.close()
        except BaseException as e:
            logging.exception(e)
        self.sock = None
        self.conn = None
        self.addr = None


class BTPSocketCli(BTPSocket):

    def open(self, addr):
        self.addr = addr

    def accept(self, timeout=10.0):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(self.addr)

    def close(self):
        try:
            if self.conn:
                self.conn.shutdown(socket.SHUT_RDWR)
                self.conn.close()
        except OSError as e:
            logging.exception(e)
        finally:
            self.conn = None
            self.addr = None


class BTPWorker:
    def __init__(self, sock):
        super().__init__()

        self._socket = sock
        self._rx_queue = queue.Queue()
        self._running = threading.Event()
        self._lock = threading.Lock()

        self._rx_worker = threading.Thread(target=self._rx_task)
        self._rx_worker.name = f'BTPWorker{self._rx_worker.name}'

        self.event_handler_cb = event_handler

    def _rx_task(self):
        log(f'{threading.current_thread().name} started')
        socket_ok = True
        while self._running.is_set():
            try:
                data = self._socket.read(timeout=1.0)

                hdr = data[0]
                if hdr.op >= 0x80:
                    # Do not put handled events on RX queue
                    ret = self.event_handler_cb(*data)
                    if ret is True:
                        continue

                self._rx_queue.put(data)
                socket_ok = True
            except socket.timeout:
                # this one is expected so ignore
                pass
            except socket.error:
                if socket_ok:
                    socket_ok = False
                    log('socket.error: BTPSocket is closed')
            except Exception as e:
                logging.error("%r", e)

        log(f'{threading.current_thread().name} finishing...')

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

    def send(self, svc_id, op, ctrl_index, data):
        self._lock.acquire()
        try:
            self._socket.send(svc_id, op, ctrl_index, data)
        finally:
            self._lock.release()

    def send_wait_rsp(self, svc_id, op, ctrl_index, data):
        self._lock.acquire()
        try:
            self._socket.send(svc_id, op, ctrl_index, data)
            tuple_hdr, tuple_data = self.read()

            if tuple_hdr.svc_id != svc_id:
                raise BTPError(
                    "Incorrect service ID %s in the response, expected %s!" %
                    (tuple_hdr.svc_id, svc_id))

            if tuple_hdr.op == defs.BTP_STATUS:
                raise BTPError("Error opcode in response!")

            if op != tuple_hdr.op:
                raise BTPError(
                    "Invalid opcode 0x%.2x in the response, expected 0x%.2x!" %
                    (tuple_hdr.op, op))

            return tuple_data
        finally:
            self._lock.release()

    def _reset_rx_queue(self):
        while not self._rx_queue.empty():
            try:
                self._rx_queue.get_nowait()
            except queue.Empty:
                continue

            self._rx_queue.task_done()

    def accept(self, timeout=10.0):
        logging.debug("%s", self.accept.__name__)

        self._socket.accept(timeout)

        self._running.set()
        self._rx_worker.start()

    def close(self):
        if self._running.is_set():
            self._running.clear()

            # is_alive returns True if a thread has not been started
            # and may result in deadlock here.
            while self._rx_worker.is_alive():
                log('Waiting for _rx_worker to finish ...')
                self._rx_worker.join(timeout=1)

        self._reset_rx_queue()

        self._socket.close()

    def register_event_handler(self, _event_handler):
        self.event_handler_cb = _event_handler
