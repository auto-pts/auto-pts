#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2025, Atmosic.
# Copyright (c) 2025, Codecoup.
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
import shlex
import socket
import subprocess
import sys
import time

import serial

from autopts.config import FILE_PATHS
from autopts.ptsprojects.boards import Board, tty_to_com
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.iutctl_common import BTP_ADDRESS, BTPSocketSrv, BTPWorker, LoggerWorker
from autopts.pybtp.types import BTPInitError
from autopts.rtt import BTMON, RTTLogger
from autopts.utils import get_global_end

log = logging.debug


def get_qemu_cmd(kernel_image, qemu_bin, btp_address=BTP_ADDRESS, qemu_options="", **kwargs):
    """Returns a command to QEMU

    kernel_image -- Path to kernel image"""

    qemu_cmd = (
        f"{qemu_bin} -nographic "
        f"-serial mon:stdio "
        f"-serial unix:{btp_address} "
        f"-serial unix:/tmp/bt-server-bredr "
        f"-kernel {kernel_image} "
        f"{qemu_options}"
    )

    return qemu_cmd


def get_native_cmd(kernel_image, hci, tty_baudrate, btp_address, rtscts, log_dir, **kwargs):
    """Return native command"""

    flow_control = "crtscts" if rtscts else ""

    flash_bin_dir = os.path.join(FILE_PATHS['FLASH_BIN_DIR'], os.path.basename(log_dir), 'flash.bin')
    os.makedirs(os.path.dirname(flash_bin_dir), exist_ok=True)

    return (
        f"{kernel_image} --bt-dev=hci{hci} --flash={flash_bin_dir} "
        f'--attach_uart_cmd="socat %s,rawer,b{tty_baudrate},{flow_control} UNIX-CONNECT:{btp_address} &"'
    )


def get_btattach_cmd(btattach_bin, tty, tty_baudrate, **kwargs):
    return f"{btattach_bin} -B {tty} -S {tty_baudrate} -P h4"


def get_btproxy_cmd(btproxy_bin, hci, **kwargs):
    return f"{btproxy_bin} -u -i {hci} -z"


class IutCtl:
    """Generic IUT Control Class"""

    def __init__(self, args):
        """Constructor."""
        log(f"{self.__class__}.{self.__init__.__name__} kernel_image={args.kernel_image} "
            f"tty_file={args.tty_file} board_name={args.board_name}")

        self.iut_mode = args.iut_mode
        self.pylink_reset = args.pylink_reset
        self.device_core = args.device_core
        self.debugger_snr = args.debugger_snr
        self.kernel_image = args.kernel_image
        self.tty_file = args.tty_file
        self._net_tty_file = args.net_tty_file
        self.tty_baudrate = args.tty_baudrate
        self.btattach_bin = args.btattach_bin
        self.btproxy_bin = args.btproxy_bin
        self.qemu_bin = args.qemu_bin
        self.qemu_options = args.qemu_options
        self.btmgmt_bin = args.btmgmt_bin
        self.hid_vid = args.hid_vid
        self.hid_pid = args.hid_pid
        self.hid_serial = args.hid_serial
        self.hci = args.hci
        self.gdb = args.gdb
        self.is_running = False
        self.board = None
        self.btp_address = BTP_ADDRESS
        self._socat_process = None
        self.socket_srv = None
        self.btp_socket = None
        self.test_case = None
        self._rtt_logger = None
        self._rtt_logger_name = 'Logger'
        self._btmon_rtt_name = 'btmonitor'
        self._btmon = None
        self._uart_logger = None
        self.rtscts = args.rtscts
        self._start_mode = None
        self._stop_mode = None
        self.get_btproxy_cmd = get_btproxy_cmd
        self.get_qemu_cmd = get_qemu_cmd
        self.get_btattach_cmd = get_btattach_cmd
        self.get_native_cmd = get_native_cmd
        self.boot_log = ''

        if args.board_name:
            self.board = Board(args.board_name, self)

            if self.debugger_snr:
                self.btp_address = BTP_ADDRESS + self.debugger_snr
                self._rtt_logger = RTTLogger(args.rtt_log_syncto) if args.rtt_log else None
                self._btmon = BTMON() if args.btmon else None

        if self.iut_mode == "tty":
            self._start_mode = self._start_tty_mode
            self._stop_mode = self._stop_tty_mode

        elif self.iut_mode == "qemu":
            from autopts.ptsprojects.utils.btattach import Btattach
            from autopts.ptsprojects.utils.btproxy import Btproxy
            from autopts.ptsprojects.utils.qemu import QEMU
            self._qemu = QEMU()
            self._start_mode = self._start_qemu_mode
            self._stop_mode = self._stop_qemu_mode
            self._btproxy = Btproxy() if self.btproxy_bin else None
            self._btattach = Btattach() if self.btattach_bin else None

        elif self.iut_mode == "native":
            from autopts.ptsprojects.utils.btattach import Btattach
            from autopts.ptsprojects.utils.native import NativeIUT
            self._native = NativeIUT()
            self._start_mode = self._start_native_mode
            self._stop_mode = self._stop_native_mode
            self._btattach = Btattach() if self.btattach_bin else None

        else:
            raise Exception(f"Mode {self.iut_mode} is not supported.")

    def start(self, test_case):
        """Starts the IUT"""

        log(f"{self.__class__}.{self.start.__name__}")

        self.is_running = True
        self.test_case = test_case

        self._start_mode(test_case)

    def _start_tty_mode(self, test_case):
        do_reset = not self.gdb

        stack = get_stack()
        if do_reset and len(stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY]) == 0:
            # For HW, the IUT ready event is triggered at its reset.
            # Since the board.reset() is called at the end of each
            # test case, to avoid double reset let's use board.reset()
            # only if it was not received, e.g. at the beginning of
            # the first test case.
            self.board.reset()

        # If the board has been reset before BTP socket is open, it is possible
        # to receive none, a partial or whole IUT ready event.
        # Flush serial to ignore it.
        self.flush_serial(self.rtscts)

        self.socket_srv = BTPSocketSrv(test_case.log_dir)
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)
        flow_control = "crtscts" if self.rtscts else ""

        if sys.platform == "win32":
            # On windows socat.exe does not support setting serial baud rate.
            # Set it with 'mode' from cmd.exe
            com = tty_to_com(self.tty_file)
            # RTS=HS -> (Hardware Handshaking)
            # RTS=OFF
            handshake_mode = "hs" if self.rtscts else "off"
            mode_cmd = (
                f'>nul 2>nul cmd.exe /c "mode {com} '
                f'BAUD={self.tty_baudrate} PARITY=n DATA=8 STOP=1 RTS={handshake_mode}"'
            )
            os.system(mode_cmd)

            socat_cmd = (
                f"socat.exe -x -v tcp:{socket.gethostbyname(socket.gethostname())}:"
                f"{self.socket_srv.sock.getsockname()[1]},retry=100,interval=1 "
                f"{self.tty_file},raw,b{self.tty_baudrate},{flow_control}"
            )
        else:
            socat_cmd = (
                f"socat -x -v {self.tty_file},rawer,b{self.tty_baudrate},{flow_control} UNIX-CONNECT:{self.btp_address}"
            )

        log(f"Starting socat process: {socat_cmd}")

        # socat dies after socket is closed, so no need to kill it
        self._socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                               shell=False,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)

        self.btp_socket.accept()

        if do_reset and len(stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY]) == 0:
            # Reset the board here to capture the IUT Ready event at
            # the beginning of the first test case.
            self.board.reset()

    def _start_qemu_mode(self, test_case):
        self.socket_srv = BTPSocketSrv(test_case.log_dir)
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)

        if self._btattach:
            btattach_cmd = self.get_btattach_cmd(btattach_bin=self.btattach_bin,
                                                 tty=self.tty_file,
                                                 tty_baudrate=self.tty_baudrate)
            self.hci = self._btattach.start(btattach_cmd, log_dir=test_case.log_dir)

        if self._btproxy:
            if self.hid_serial:
                from autopts.ptsprojects.utils.btproxy import find_hci_device
                self.hci = find_hci_device(self.hid_vid, self.hid_pid, self.hid_serial)
                if self.hci is None:
                    raise Exception(f"Could not find the device: VID={self.hid_vid} "
                                    f"PID={self.hid_pid} SN={self.hid_serial}")

            btproxy_cmd = self.get_btproxy_cmd(btproxy_bin=self.btproxy_bin,
                                               hci=self.hci)
            self._btproxy.start(btproxy_cmd, self.hci, test_case.log_dir, self.btmgmt_bin)

        qemu_cmd = self.get_qemu_cmd(kernel_image=self.kernel_image,
                                     qemu_bin=self.qemu_bin,
                                     btp_address=self.btp_address,
                                     qemu_options=self.qemu_options)

        log(f"Starting QEMU process: {qemu_cmd}")

        self._qemu.start(qemu_cmd, self.boot_log, test_case.log_dir)

        self.btp_socket.accept()

    def _start_native_mode(self, test_case):
        self.socket_srv = BTPSocketSrv(test_case.log_dir)
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)

        if self._btattach:
            btattach_cmd = self.get_btattach_cmd(btattach_bin=self.btattach_bin,
                                                 tty=self.tty_file,
                                                 tty_baudrate=self.tty_baudrate)
            self.hci = self._btattach.start(btattach_cmd, log_dir=test_case.log_dir)

        if self.hid_serial:
            from autopts.ptsprojects.utils.btproxy import find_hci_device
            self.hci = find_hci_device(self.hid_vid, self.hid_pid, self.hid_serial)
            if self.hci is None:
                raise Exception(f"Could not find the device: VID={self.hid_vid} "
                                f"PID={self.hid_pid} SN={self.hid_serial}")

        if self.btmgmt_bin:
            from autopts.ptsprojects.utils.btproxy import btmgmt_power_off_hci
            btmgmt_power_off_hci(self.btmgmt_bin, self.hci)

        native_cmd = self.get_native_cmd(kernel_image=self.kernel_image,
                                         hci=self.hci,
                                         tty_baudrate=self.tty_baudrate,
                                         btp_address=self.btp_address,
                                         rtscts=self.rtscts,
                                         log_dir=test_case.log_dir)

        log(f"Starting native process: {native_cmd}")

        self._native.start(native_cmd, test_case.log_dir)

        self.btp_socket.accept()

    def flush_serial(self, rtscts=False):
        log("%s.%s", self.__class__, self.flush_serial.__name__)
        # Try to read data or timeout
        try:
            if sys.platform == 'win32':
                tty = tty_to_com(self.tty_file)
            else:
                tty = self.tty_file

            # The main reason why we do not use serial.Serial for
            # boards is to have only one, generic implementation of
            # BTPWorker/BTPSocket. Although we can still use it for
            # flushing serial if the data does not matter.
            ser = serial.Serial(port=tty,
                                baudrate=self.tty_baudrate,
                                rtscts=rtscts,
                                timeout=1)
            ser.read(99999)
            ser.close()
        except serial.SerialException:
            pass

    def btmon_start(self):
        if self._btmon:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_btmon.log')
            self._btmon.start(self._btmon_rtt_name, log_file, self.device_core, self.debugger_snr)

    def btmon_stop(self):
        if self._btmon:
            self._btmon.stop()

    def rtt_logger_start(self):
        if self._rtt_logger:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_iutctl.log')
            self._rtt_logger.start(self._rtt_logger_name, log_file, self.device_core,
                                   self.debugger_snr)

    def rtt_logger_stop(self):
        if self._rtt_logger:
            time.sleep(0.1)  # Make sure all logs have been collected, in case test failed early.
            self._rtt_logger.stop()

    def wait_iut_ready_event(self, reset=True):
        """Wait until IUT sends ready event after power up"""
        if self.gdb:
            return

        stack = get_stack()

        if reset:
            # Some test cases require the IUT to be reset during the test.
            if self.iut_mode == "tty":
                # For HW, the IUT ready event is triggered at board.reset().
                # There is no need to reopen the BTP socket.
                stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY].clear()
                self.board.reset()
            else:
                # For QEMU, the IUT ready event is sent at startup of the process.
                self.stop()
                self.start(self.test_case)

        ev = stack.core.wait_iut_ready_ev(30)
        # Clear, because if the board has reset unexpectedly in the middle
        # of a test case, two IUT events may be received because of cleanup.
        stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY].clear()
        if not ev:
            self.stop()
            raise BTPInitError('IUT ready event NOT received!')

        log("IUT ready event received OK")

        if not reset:
            # Final steps of IUT startup. The IUT is ready, let's open the loggers.

            if self._net_tty_file:
                self._uart_logger = LoggerWorker(self._net_tty_file, self.tty_baudrate,
                                                 self.test_case.log_dir)
                self._uart_logger.start()

            self.rtt_logger_start()
            self.btmon_start()

    def get_supported_svcs(self):
        btp.read_supp_svcs()

    def stop(self):
        """Powers off the IUT"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if not self.is_running:
            return

        self._stop_mode()

        self.is_running = False

    def _stop_tty_mode(self):
        self.rtt_logger_stop()
        self.btmon_stop()

        stack = get_stack()
        if not self.gdb and stack.core and not get_global_end():

            stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY].clear()
            self.board.reset()

            # We have to wait for IUT ready event before we close socket
            ev = stack.core.wait_iut_ready_ev(30, False)
            if ev:
                log("IUT ready event received OK")
            else:
                log('IUT ready event NOT received!')

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self._net_tty_file:
            self._uart_logger.close()

        if self._socat_process:
            self._socat_process.terminate()
            self._socat_process.wait()
            self._socat_process = None

    def _stop_qemu_mode(self):
        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self._btattach:
            self._btattach.close()

        if self._qemu:
            self._qemu.close()

        if self._btproxy:
            self._btproxy.close()

        if self.board:
            self.board.reset()

    def _stop_native_mode(self):
        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self._btattach:
            self._btattach.close()

        if self._native:
            self._native.close()

        if self.board:
            self.board.reset()
