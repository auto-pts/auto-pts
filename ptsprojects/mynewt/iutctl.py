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

import subprocess
import logging
import shlex

import serial

from pybtp import defs
from pybtp.types import BTPError
from pybtp.iutctl_common import BTPWorker, BTP_ADDRESS

log = logging.debug
MYNEWT = None
IUT_LOG_FO = None
SERIAL_BAUDRATE = 115200


class MynewtCtl:
    '''Mynewt OS Control Class'''

    def __init__(self, tty_file, board_name):
        """Constructor."""
        log("%s.%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, tty_file,
            board_name)

        assert tty_file and board_name

        self.tty_file = tty_file
        self.board = Board(board_name, tty_file)

        self.socat_process = None
        self.btp_socket = None

    def start(self):
        """Starts the Mynewt OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.flush_serial()

        self.btp_socket = BTPWorker()
        self.btp_socket.open()

        socat_cmd = ("socat -x -v %s,rawer,b115200 UNIX-CONNECT:%s" %
                     (self.tty_file, BTP_ADDRESS))

        log("Starting socat process: %s", socat_cmd)

        # socat dies after socket is closed, so no need to kill it
        self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                              shell=False,
                                              stdout=IUT_LOG_FO,
                                              stderr=IUT_LOG_FO)

        self.btp_socket.accept()

    def flush_serial(self):
        log("%s.%s", self.__class__, self.flush_serial.__name__)
        # Try to read data or timeout
        ser = serial.Serial(port=self.tty_file,
                            baudrate=SERIAL_BAUDRATE, timeout=1)
        ser.read(99999)
        ser.close()

    def reset(self):
        """Restart IUT related processes and reset the IUT"""
        log("%s.%s", self.__class__, self.reset.__name__)

        self.stop()
        self.start()
        self.flush_serial()
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
        else:
            log("IUT ready event received OK")

    def stop(self):
        """Powers off the Mynewt OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.socat_process and self.socat_process.poll() is None:
            self.socat_process.terminate()
            self.socat_process.wait()


class MynewtCtlStub:
    '''Mynewt OS Control Class with stubs for testing'''

    def __init__(self):
        """Constructor."""
        pass

    def start(self):
        """Starts the Mynewt OS"""
        log("%s.%s", self.__class__, self.start.__name__)

    def stop(self):
        """Powers off the Mynewt OS"""
        log("%s.%s", self.__class__, self.stop.__name__)


class Board:
    """HW DUT board"""

    # for command line options
    names = [
        'nordic_pca10056'
    ]

    def __init__(self, board_name, tty_file):
        """Constructor of board"""
        if board_name not in self.names:
            raise Exception("Board name %s is not supported!" % board_name)

        self.name = board_name
        self.tty_file = tty_file
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with
        """
        log("About to reset DUT: %r", self.reset_cmd)

        reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                         shell=False,
                                         stdout=IUT_LOG_FO,
                                         stderr=IUT_LOG_FO)

        if reset_process.wait():
            logging.error("reset failed")

    def get_reset_cmd(self):
        """Return reset command for a board"""

        return 'nrfjprog -f nrf52 -r'


def get_iut():
    return MYNEWT


def init_stub():
    """IUT init routine for testings"""
    global MYNEWT
    MYNEWT = MynewtCtlStub()


def init(tty_file, board):
    """IUT init routine

    tty_file -- Path to TTY file. BTP communication with HW DUT will be done
    over this TTY.
    board -- HW DUT board to use for testing.
    """
    global IUT_LOG_FO
    global MYNEWT

    IUT_LOG_FO = open("iut-mynewt.log", "w")

    MYNEWT = MynewtCtl(tty_file, board)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, MYNEWT
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if MYNEWT:
        MYNEWT.stop()
        MYNEWT = None
