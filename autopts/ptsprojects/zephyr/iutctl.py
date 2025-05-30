#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2025, Atmosic.
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

from autopts.ptsprojects.boards import Board, get_debugger_snr, tty_to_com
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.iutctl_common import BTP_ADDRESS, BTPSocketSrv, BTPWorker
from autopts.rtt import BTMON, RTTLogger
from autopts.utils import get_global_end

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"

SERIAL_BAUDRATE = int(os.getenv("AUTOPTS_SERIAL_BAUDRATE", "115200"))
CLI_SUPPORT = ['tty', 'hci', 'qemu']


def get_qemu_cmd(kernel_image):
    """Returns qemu command to start Zephyr

    kernel_image -- Path to Zephyr kernel image"""

    qemu_cmd = (
        f"{QEMU_BIN} -cpu cortex-m3 -machine lm3s6965evb -nographic "
        f"-serial mon:stdio "
        f"-serial unix:{BTP_ADDRESS} "
        f"-serial unix:/tmp/bt-server-bredr "
        f"-kernel {kernel_image}"
    )

    return qemu_cmd


class ZephyrCtl:
    """Zephyr OS Control Class"""

    def __init__(self, args):
        """Constructor."""
        log("%s.%s kernel_image=%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, args.kernel_image,
            args.tty_file, args.board_name)

        self.pylink_reset = args.pylink_reset
        self.device_core = args.device_core
        self.debugger_snr = args.debugger_snr
        self.kernel_image = args.kernel_image
        self.tty_file = args.tty_file
        self.hci = args.hci
        self.native = None
        self.gdb = args.gdb
        self.is_running = False

        if self.tty_file and args.board_name:  # DUT is a hardware board, not QEMU
            if self.debugger_snr is None:
                self.debugger_snr = get_debugger_snr(self.tty_file)
            self.board = Board(args.board_name, self)
        else:  # DUT is QEMU or a board that won't be reset
            self.board = None

        self.qemu_process = None
        self.native_process = None
        self.socat_process = None
        self.socket_srv = None
        self.btp_socket = None
        self.test_case = None
        self.iut_log_file = None
        self.rtt_logger = None
        self.btmon = None

        if self.debugger_snr:
            self.btp_address = BTP_ADDRESS + self.debugger_snr
            self.rtt_logger = RTTLogger() if args.rtt_log else None
            self.btmon = BTMON() if args.btmon else None
        else:
            self.btp_address = BTP_ADDRESS

    def start(self, test_case):
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.is_running = True
        self.test_case = test_case

        # We will reset HW after BTP socket is open. If the board was
        # reset before this happened, it is possible to receive none,
        # partial or whole IUT ready event. Flush serial to ignore it.
        self.flush_serial()

        self.socket_srv = BTPSocketSrv(test_case.log_dir)
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)

        if self.tty_file:
            if sys.platform == "win32":
                # On windows socat.exe does not support setting serial baud rate.
                # Set it with 'mode' from cmd.exe
                com = tty_to_com(self.tty_file)
                mode_cmd = (">nul 2>nul cmd.exe /c \"mode " + com + f"BAUD={SERIAL_BAUDRATE} PARITY=n DATA=8 STOP=1\"")
                os.system(mode_cmd)

                socat_cmd = (
                    f"socat.exe -x -v tcp:{socket.gethostbyname(socket.gethostname())}:"
                    f"{self.socket_srv.sock.getsockname()[1]},retry=100,interval=1 "
                    f"{self.tty_file},raw,b{SERIAL_BAUDRATE}"
                )
            else:
                socat_cmd = f"socat -x -v {self.tty_file},rawer,b{SERIAL_BAUDRATE} UNIX-CONNECT:{self.btp_address}"

            log("Starting socat process: %s", socat_cmd)

            # socat dies after socket is closed, so no need to kill it
            self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                                  shell=False,
                                                  stdout=subprocess.DEVNULL,
                                                  stderr=subprocess.DEVNULL)
        elif self.hci is not None:
            self.iut_log_file = open(test_case.log_dir / "autopts-iutctl-zephyr.log", "a")
            socat_cmd = f"socat -x -v %%s,rawer,b{SERIAL_BAUDRATE} UNIX-CONNECT:{self.btp_address} &"

            native_cmd = (
                f"{self.kernel_image} --bt-dev=hci{self.hci} "
                f'--attach_uart_cmd="{socat_cmd}"'
            )

            log("Starting native zephyr process: %s", native_cmd)

            # TODO check if zephyr process has started correctly
            self.native_process = subprocess.Popen(shlex.split(native_cmd),
                                                   shell=False,
                                                   stdout=self.iut_log_file,
                                                   stderr=self.iut_log_file)
        else:
            self.iut_log_file = open(test_case.log_dir / "autopts-iutctl-zephyr.log", "a")
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
            if sys.platform == 'win32':
                tty = tty_to_com(self.tty_file)
            else:
                tty = self.tty_file

            # The main reason why we do not use serial.Serial for
            # boards is to have only one, generic implementation of
            # BTPWorker/BTPSocket. Although we can still use it for
            # flushing serial if the data does not matter.
            ser = serial.Serial(port=tty,
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
            self.btmon.start('btmonitor', log_file, self.device_core, self.debugger_snr)

    def btmon_stop(self):
        if self.btmon:
            self.btmon.stop()

    def rtt_logger_start(self):
        if self.rtt_logger:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_iutctl.log')
            self.rtt_logger.start('Logger', log_file, self.device_core, self.debugger_snr)

    def rtt_logger_stop(self):
        if self.rtt_logger:
            time.sleep(0.1)  # Make sure all logs have been collected, in case test failed early.
            self.rtt_logger.stop()

    def wait_iut_ready_event(self, reset=True):
        """Wait until IUT sends ready event after power up"""
        stack = get_stack()

        if reset:
            # For HW, the IUT ready event is triggered at board.reset()
            self.stop()
            # For QEMU, the IUT ready event is sent at startup of the process.
            self.start(self.test_case)

        else:
            if not self.gdb:
                ev = stack.core.wait_iut_ready_ev(30)
                # If the board has reset unexpectedly in the middle of a test case,
                # two IUT events may be received because of cleanup.
                stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY].clear()
                if not ev:
                    self.stop()
                    raise Exception('IUT ready event NOT received!')

            log("IUT ready event received OK")
            self.rtt_logger_start()
            self.btmon_start()

    def hw_reset(self):
        if not self.gdb and self.board:
            stack = get_stack()

            # For HW, the IUT ready event is triggered at its reset.
            # Since the board.reset() is called at the end of each
            # test case, to avoid double reset let's use 'hw_reset'
            # only if it was not received, e.g. at the beginning of
            # the first test case.
            if len(stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY]) == 0:
                self.board.reset()

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if not self.is_running:
            return

        self.rtt_logger_stop()
        self.btmon_stop()

        stack = get_stack()
        if not self.gdb and self.board and \
                stack.core and not get_global_end():

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

        if self.socat_process:
            self.socat_process.terminate()
            self.socat_process.wait()
            self.socat_process = None

        self.is_running = False


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
