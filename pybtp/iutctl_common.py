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
import signal
import socket
import subprocess
import sys
import threading
import time
import pylink
import re

from pybtp import defs
from pybtp.types import BTPError
from pybtp.parser import enc_frame, dec_hdr, dec_data, HDR_LEN

log = logging.debug

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

EVENT_HANDLER = None


def set_event_handler(event_handler):
    """This is required by BTPWorker to drive stack"""
    global EVENT_HANDLER

    EVENT_HANDLER = event_handler


class BTPSocket:

    def __init__(self):
        self.sock = None
        self.conn = None
        self.addr = None

    def open(self, btp_address=BTP_ADDRESS):
        """Open BTP socket for IUT"""
        if os.path.exists(btp_address):
            os.remove(btp_address)

        if sys.platform == "win32":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((socket.gethostname(), 0))
        else:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(btp_address)

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
            if nbytes == 0 and toread_hdr_len != 0:
                raise socket.error
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

        tuple_data = bytes(str(dec_data(data)), 'utf-8').decode("unicode_escape").replace("b'", "'")

        log("Received data: %r, %r", tuple_data, data)
        self.conn.settimeout(None)
        return tuple_hdr, dec_data(data)

    def send(self, svc_id, op, ctrl_index, data):
        """Send BTP formated data over socket"""
        logging.debug("%s, %r %r %r %r",
                      self.send.__name__, svc_id, op, ctrl_index, str(data))

        frame = enc_frame(svc_id, op, ctrl_index, data)

        logging.debug("sending frame %r", frame.hex())
        self.conn.send(frame)

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


class BTPWorker(BTPSocket):
    def __init__(self):
        super().__init__()

        self._rx_queue = queue.Queue()
        self._running = threading.Event()
        self._lock = threading.Lock()

        self._rx_worker = threading.Thread(target=self._rx_task)

        self.event_handler_cb = None

    def _rx_task(self):
        while self._running.is_set():
            try:
                data = super().read(timeout=1.0)

                hdr = data[0]
                if hdr.op >= 0x80:
                    # Do not put handled events on RX queue
                    ret = EVENT_HANDLER(*data)
                    if ret is True:
                        continue

                self._rx_queue.put(data)
            except (socket.timeout, socket.error):
                pass  # these are expected so ignore
            except Exception as e:
                logging.error("%r", e)

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

    def send_wait_rsp(self, svc_id, op, ctrl_index, data):
        self._lock.acquire()
        try:
            super().send(svc_id, op, ctrl_index, data)
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

        super().accept(timeout)

        self._running.set()
        self._rx_worker.start()

    def close(self):
        self._running.clear()

        if self._rx_worker.is_alive():
            self._rx_worker.join()

        self._reset_rx_queue()

        super().close()

    def register_event_handler(self, event_handler):
        self.event_handler_cb = event_handler


def get_debugger_snr(tty_file):
    debuggers = subprocess.Popen('nrfjprog --com',
                                 shell=True,
                                 stdout=subprocess.PIPE
                                 ).stdout.read().decode()

    if sys.platform == "win32":
        COM = "COM" + str(int(tty_file["/dev/ttyS".__len__():]) + 1)
        reg = "[0-9]+(?=\s+" + COM + ".+)"
    else:
        reg = "[0-9]+(?=\s+" + tty_file + ".+)"

    try:
        return re.findall(reg, debuggers)[0]
    except:
        sys.exit("No debuggers associated with the device found")


class RTT:
    def __init__(self):
        self.read_thread = None
        self.stop_thread = threading.Event()
        self.log_filename = None
        self.log_file = None
        self.jlink = None
        pylink.logger.setLevel(logging.WARNING)

    def _get_buffer_index(self, buffer_name):
        timeout = time.time() + 10
        num_up = 0
        while True:
            try:
                num_up = self.jlink.rtt_get_num_up_buffers()
                break
            except pylink.errors.JLinkRTTException:
                if time.time() > timeout:
                    break
                time.sleep(0.1)

        for buf_index in range(num_up):
            buf = self.jlink.rtt_get_buf_descriptor(buf_index, True)
            if buf.name == buffer_name:
                return buf_index

    def _read_from_buffer(self, jlink, buffer_index, stop_thread, file):
        while not stop_thread.is_set() and jlink.connected():
            byte_list = jlink.rtt_read(buffer_index, 1024)
            try:
                if len(byte_list) > 0:
                    file.write(bytes(byte_list))
                    file.flush()
            except UnicodeDecodeError:
                continue

    def start(self, buffer_name, log_filename, debugger_snr=None):
        log("%s.%s", self.__class__, self.start.__name__)
        self.log_filename = log_filename
        target_device = "NRF52840_XXAA"
        self.jlink = pylink.JLink()
        self.jlink.open(serial_no=debugger_snr)
        self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        self.jlink.connect(target_device)
        self.jlink.rtt_start()

        buffer_index = self._get_buffer_index(buffer_name)
        self.stop_thread.clear()
        self.log_file = open(self.log_filename, 'ab')
        self.read_thread = threading.Thread(target=self._read_from_buffer,
                                            args=(self.jlink,
                                                  buffer_index,
                                                  self.stop_thread,
                                                  self.log_file))
        self.read_thread.start()

    def stop(self):
        log("%s.%s", self.__class__, self.stop.__name__)
        self.stop_thread.set()

        if self.read_thread:
            self.read_thread.join()
            self.read_thread = None
            self.jlink.rtt_stop()
            self.jlink.close()

        if self.log_file:
            self.log_file.close()
            self.log_file = None


class BTMON:
    def __init__(self):
        self.btmon_process = None
        self.pty_name = None
        self.log_file = None

    def start(self, log_file, debugger_snr):
        log("%s.%s", self.__class__, self.start.__name__)
        self.log_file = log_file
        cmd = ['btmon', '-J', 'NRF52,' + debugger_snr, '-w', self.log_file]

        self.btmon_process = subprocess.Popen(cmd,
                                              shell=False,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)

    def stop(self):
        log("%s.%s", self.__class__, self.stop.__name__)
        if self.btmon_process and self.btmon_process.poll() is None:
            self.btmon_process.send_signal(signal.SIGINT)
            self.btmon_process.wait()
            self.btmon_process = None
