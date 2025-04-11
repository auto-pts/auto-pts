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

import binascii
import logging
import os
import queue
import re
import socket
import sys
import threading
from abc import abstractmethod
from datetime import datetime

from autopts.pybtp import defs
from autopts.pybtp.parser import HDR_LEN, dec_data, dec_hdr, enc_frame, repr_hdr
from autopts.pybtp.types import BTPError
from autopts.utils import get_global_end, raise_on_global_end

log = logging.debug

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

EVENT_HANDLER = None


def set_event_handler(event_handler):
    """This is required by BTPWorker to drive stack"""
    global EVENT_HANDLER

    EVENT_HANDLER = event_handler


class BTPSocket:

    def __init__(self, log_dir=None):
        self.conn = None
        self.addr = None
        self.btp_service_id_dict = None
        self.log_file = open(os.path.join(log_dir, "autopts-iutctl.log"), "a")
        self.btp_service_id_dict = self.get_svc_id()

    @abstractmethod
    def open(self, address):
        pass

    @abstractmethod
    def accept(self, timeout=10.0):
        pass

    @staticmethod
    def get_svc_id():
        """Looks for BTP_SVC_ID variables from the defs.py"""
        btp_service_ids = {}

        for name, value in vars(defs).items():
            if name.startswith('BTP_SERVICE_ID_') and isinstance(value, int):
                trimmed_name = name.replace('BTP_SERVICE_ID_', '')
                btp_service_ids[trimmed_name] = value

        return btp_service_ids

    def write_to_log(self, req, data, hex_data):
        """Log decoded header and raw data"""
        current_time = datetime.now().strftime('%H:%M:%S:%f')
        f = self.log_file
        indent = ' ' * 18

        hex_data = hex_data[:14] + "|" + hex_data[14 + 1:]

        if len(hex_data) > 47:
            # This ensures clean text indentation for longer raw data, with 16 bytes per line
            hex_data = '\n' + indent + re.sub(r'(.{48})', r'\1\n' + indent, hex_data)

        if req:
            f.write(f'{current_time[:-3]}\t> {self.parse_data(data)} {hex_data}\n')
        else:
            f.write(f'{current_time[:-3]}\t< {self.parse_data(data)} {hex_data}\n')

    def write_err_status(self, data, hex_data, status):
        """Log command status value for error response"""
        current_time = datetime.now().strftime('%H:%M:%S:%f')
        f = self.log_file
        status_values = {
            1: 'Fail',
            2: 'Unknown Command',
            3: 'Not Ready',
            4: 'Invalid Index'
        }
        err_status = status_values[int(status)]
        f.write(f'{current_time[:-3]}\t<- Response:  {self.parse_data(data)} {hex_data} {err_status}\n')

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
                raise OSError
            logging.debug("Read %d bytes", nbytes)
            hdr_memview = hdr_memview[nbytes:]
            toread_hdr_len -= nbytes

        hex_hdr = ' '.join(hdr.hex()[i:i + 2] for i in range(0, len(hdr.hex()), 2))
        tuple_hdr = dec_hdr(hdr)
        toread_data_len = tuple_hdr.data_len

        logging.debug("Received: hdr: %s %r", repr_hdr(tuple_hdr), hdr)

        data = bytearray(toread_data_len)
        data_memview = memoryview(data)

        # Gather optional frame data
        while toread_data_len:
            nbytes = self.conn.recv_into(data_memview, toread_data_len)
            logging.debug("Read %d bytes data", nbytes)
            if nbytes == 0 and toread_data_len != 0:
                raise OSError
            data_memview = data_memview[nbytes:]
            toread_data_len -= nbytes

        data_string = binascii.hexlify(data).decode('utf-8')
        data_string = ' '.join(f'{data_string[i:i + 2]}' for i in range(0, len(data_string), 2))
        raw_data = hex_hdr if data_string == '' else hex_hdr + ' ' + data_string

        if tuple_hdr.op == 0:
            self.write_err_status(tuple_hdr, raw_data, data_string)
        else:
            # 0 for logging response, 1 for command
            self.write_to_log(0, tuple_hdr, raw_data)
        log(f"Received data: { {data_string} }, {data}")

        self.conn.settimeout(None)
        return tuple_hdr, dec_data(data)

    def send(self, svc_id, op, ctrl_index, data):
        """Send BTP formated data over socket"""
        logging.debug("%s, %r %r %r %r",
                      self.send.__name__, svc_id, op, ctrl_index, str(data))

        frame = enc_frame(svc_id, op, ctrl_index, data)

        logging.debug("sending frame %r", frame.hex())

        hex_data = ' '.join(frame.hex()[i:i + 2] for i in range(0, len(frame.hex()), 2))
        tuple_data = (svc_id, op, ctrl_index, len(data) if isinstance(data, (str, bytearray)) else data)
        # 0 for logging response, 1 for command
        self.write_to_log(1, tuple_data, hex_data)
        self.conn.send(frame)

    def parse_data(self, data):
        def get_btp_cmd_name(prefix, op_code):
            """Looks for BTP Command variables from the defs.py"""
            if op_code in ('0x0', '0x00'):
                return 'BTP_ERROR'
            for key, value in vars(defs).items():
                if (key.startswith(f'BTP_{prefix}_CMD_') and value == int(op_code, 16)) or\
                        (key.startswith(f'BTP_{prefix}_EV_') and value == int(op_code, 16)):
                    return key

            return 'BTP Undecoded'  # Return if no matching variable is found

        parsed_data = ''
        svc_name = ''
        if isinstance(data, str):
            svc_id = data[:2]
            opc = data[2:4]
        else:
            svc_id, opc, ctrl_idx, data_len = data[0], data[1], data[2], data[3]
        for name, btp_id in self.btp_service_id_dict.items():
            if btp_id == int(svc_id):
                svc_name += name
                break

        indent = "\n" + (" " * 17)

        def to_hex(x):
            return f"0x{int(x):02x}"
        btp_command = get_btp_cmd_name(svc_name, to_hex(opc))
        parsed_data += f'{btp_command} ({to_hex(svc_id)}|{to_hex(opc)}|{to_hex(ctrl_idx)}){indent} ' \
                       f'raw data ({data_len}):'

        return parsed_data

    @abstractmethod
    def close(self):
        self.log_file.close()
        self.log_file = None
        pass


class BTPSocketSrv(BTPSocket):

    def __init__(self, log_dir=None):
        super().__init__(log_dir)
        self.sock = None

    def open(self, addres=BTP_ADDRESS, port=0):
        """Open BTP socket for IUT"""
        if os.path.exists(addres):
            os.remove(addres)

        if sys.platform == "win32":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((socket.gethostname(), port))
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
        super().close()
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

        self.event_handler_cb = None

    def _rx_task(self):
        log(f'{threading.current_thread().name} started')
        socket_ok = True
        while self._running.is_set() and not get_global_end():
            try:
                data = self._socket.read(timeout=1.0)

                hdr = data[0]
                if hdr.op >= 0x80:
                    # Do not put handled events on RX queue
                    ret = EVENT_HANDLER(*data)
                    if ret is True:
                        continue

                self._rx_queue.put(data)
                socket_ok = True
            except socket.timeout:
                # this one is expected so ignore
                pass
            except OSError:
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
            raise_on_global_end()

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
                    f"Incorrect service ID {tuple_hdr.svc_id} in the response, expected {svc_id}!"
                )

            if tuple_hdr.op == defs.BTP_STATUS:
                raise BTPError("Error opcode in response!")

            if op != tuple_hdr.op:
                raise BTPError(
                    f"Invalid opcode 0x{tuple_hdr.op:02x} in the response, expected 0x{op:02x}!"
                )

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
            while self._rx_worker.is_alive() and not get_global_end():
                log('Waiting for _rx_worker to finish ...')
                self._rx_worker.join(timeout=1)

        self._reset_rx_queue()

        self._socket.close()

    def register_event_handler(self, event_handler):
        self.event_handler_cb = event_handler
