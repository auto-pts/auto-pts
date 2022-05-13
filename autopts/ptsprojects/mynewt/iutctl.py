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

import socket
import subprocess
import logging
import shlex
import os
import sys
import serial

from autopts.pybtp import defs, btp
from autopts.ptsprojects.boards import Board, get_debugger_snr, tty_to_com
from autopts.pybtp.types import BTPError
from autopts.pybtp.iutctl_common import BTPWorker, BTP_ADDRESS, RTT, BTMON, BTPSocketSrv

log = logging.debug
MYNEWT = None
import importlib
IUT_LOG_FO = None
SERIAL_BAUDRATE = 115200
CLI_SUPPORT = ['tty']


class MynewtCtl:
    """Mynewt OS Control Class"""

    def __init__(self, args):
        """Constructor."""
        log("%s.%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, args.tty_file,
            args.board_name)

        assert args.tty_file and args.board_name

        self.tty_file = args.tty_file
        self.debugger_snr = get_debugger_snr(self.tty_file) \
            if args.debugger_snr is None else args.debugger_snr
        self.board = Board(args.board_name, self)
        self.socat_process = None
        self.socket_srv = None
        self.btp_socket = None
        self.test_case = None
        self.iut_log_file = None

        if self.debugger_snr:
            self.btp_address = BTP_ADDRESS + self.debugger_snr
            self.rtt_logger = RTT() if args.rtt_log else None
            self.btmon = BTMON() if args.btmon else None
        else:
            self.btp_address = BTP_ADDRESS

    def start(self, test_case):
        """Starts the Mynewt OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.test_case = test_case
        self.iut_log_file = open(os.path.join(test_case.log_dir, "autopts-iutctl-mynewt.log"), "a")

        self.flush_serial()

        self.socket_srv = BTPSocketSrv()
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)

        if sys.platform == "win32":
            # On windows socat.exe does not support setting serial baud rate.
            # Set it with 'mode' from cmd.exe
            com = tty_to_com(self.tty_file)
            mode_cmd = (">nul 2>nul cmd.exe /c \"mode " + com + "BAUD=115200 PARITY=n DATA=8 STOP=1\"")
            os.system(mode_cmd)

            socat_cmd = ("socat.exe -x -v tcp:" + socket.gethostbyname(socket.gethostname()) +
                         ":%s,retry=100,interval=1 %s,raw,b115200" %
                         (self.socket_srv.sock.getsockname()[1], self.tty_file))
        else:
            socat_cmd = ("socat -x -v %s,rawer,b115200 UNIX-CONNECT:%s" %
                         (self.tty_file, self.btp_address))

        log("Starting socat process: %s", socat_cmd)

        # socat dies after socket is closed, so no need to kill it
        self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
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
            self.btmon.start(log_file, self.debugger_snr)

    def btmon_stop(self):
        if self.btmon:
            self.btmon.stop()

    def rtt_logger_start(self):
        if self.rtt_logger:
            log_file = os.path.join(self.test_case.log_dir,
                                    self.test_case.name.replace('/', '_') +
                                    '_iutctl.log')
            self.rtt_logger.start('Terminal', log_file, self.debugger_snr)

    def rtt_logger_stop(self):
        if self.rtt_logger:
            self.rtt_logger.stop()

    def reset(self):
        """Restart IUT related processes and reset the IUT"""
        log("%s.%s", self.__class__, self.reset.__name__)

        self.stop()
        self.start(self.test_case)
        self.flush_serial()

        self.rtt_logger_stop()
        self.btmon_stop()

        self.board.reset()

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        self.reset()

        tuple_hdr, tuple_data = self.btp_socket.read()

        try:
            if (tuple_hdr.svc_id != defs.BTP_SERVICE_ID_CORE or
                    tuple_hdr.op != defs.CORE_EV_IUT_READY):
                raise BTPError("Failed to get ready event")
        except BTPError as err:
            log("Unexpected event received (%s), expected IUT ready!", err)
            self.stop()
            raise err
        else:
            log("IUT ready event received OK")

        self.rtt_logger_start()
        self.btmon_start()

    def get_supported_svcs(self):
        btp.read_supp_svcs()

    def stop(self):
        """Powers off the Mynewt OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.socat_process and self.socat_process.poll() is None:
            self.socat_process.terminate()
            self.socat_process.wait()

        if self.board:
            self.board.reset()

        if self.iut_log_file:
            self.iut_log_file.close()
            self.iut_log_file = None

        self.rtt_logger_stop()
        self.btmon_stop()

        if self.socat_process:
            self.socat_process.terminate()
            self.socat_process.wait()
            self.socat_process = None


class MynewtCtlStub:
    """Mynewt OS Control Class with stubs for testing"""

    def __init__(self):
        """Constructor."""

    def start(self):
        """Starts the Mynewt OS"""
        log("%s.%s", self.__class__, self.start.__name__)

    def stop(self):
        """Powers off the Mynewt OS"""
        log("%s.%s", self.__class__, self.stop.__name__)


def get_iut():
    return MYNEWT


def init_stub():
    """IUT init routine for testings"""
    global MYNEWT
    MYNEWT = MynewtCtlStub()


def init(args):
    """IUT init routine

    tty_file -- Path to TTY file. BTP communication with HW DUT will be done
    over this TTY.
    board -- HW DUT board to use for testing.
    """
    global MYNEWT

    MYNEWT = MynewtCtl(args)


def cleanup():
    """IUT cleanup routine"""
    global MYNEWT

    if MYNEWT:
        MYNEWT.stop()
        MYNEWT = None
