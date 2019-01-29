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

from pybtp import defs
from pybtp.types import BTPError
from pybtp.iutctl_common import BTPWorker

log = logging.debug
MYNEWT = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

# qemu log file object
IUT_LOG_FO = None


class MynewtCtl:
    '''Mynewt OS Control Class'''

    def __init__(self, kernel_image, tty_file, board_name=None):
        """Constructor."""
        log("%s.%s kernel_image=%s tty_file=%s board_name=%s",
            self.__class__, self.__init__.__name__, kernel_image, tty_file,
            board_name)

        self.kernel_image = kernel_image
        self.tty_file = tty_file

        if self.tty_file and board_name:  # DUT is a hardware board, not QEMU
            self.board = Board(board_name, kernel_image, tty_file)
        else:  # DUT is QEMU or a board that won't be reset
            self.board = None

        self.qemu_process = None
        self.socat_process = None
        self.btp_socket = None

    def start(self):
        """Starts the Mynewt OS"""

        log("%s.%s", self.__class__, self.start.__name__)

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

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        if self.board:
            self.board.reset()

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

        if self.qemu_process and self.qemu_process.poll() is None:
            self.qemu_process.terminate()
            self.qemu_process.wait()  # do not let zombies take over
            self.qemu_process = None


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

    def __init__(self, board_name, kernel_image, tty_file):
        """Constructor of board"""
        if board_name not in self.names:
            raise Exception("Board name %s is not supported!" % board_name)

        self.name = board_name
        self.kernel_image = kernel_image
        self.tty_file = tty_file
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with openocd

        With introduction of persistent storage in DUT flashing kernel image in
        addition to reset will become necessary

        """
        log("About to reset DUT: %r", self.reset_cmd)

        reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                         shell=False,
                                         stdout=IUT_LOG_FO,
                                         stderr=IUT_LOG_FO)

        if reset_process.wait():
            logging.error("reset failed")

        # success = False
        # retry_max = 1
        # retry_count = 0
        #
        # while (not success) and (retry_count < retry_max):
        #     reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
        #                                      shell=False,
        #                                      stdout=IUT_LOG_FO,
        #                                      stderr=IUT_LOG_FO)
        #     if reset_process.wait() != 0:
        #         logging.error("reset failed")
        #         retry_count += 1
        #         time.sleep(5)
        #     else:
        #         success = True

    def get_reset_cmd(self):
        """Return reset command for a board"""

        return 'nrfjprog -f nrf52 -r'


def get_iut():
    return MYNEWT


def init_stub():
    """IUT init routine for testings"""
    global MYNEWT
    MYNEWT = MynewtCtlStub()


def init(kernel_image, tty_file, board=None):
    """IUT init routine

    kernel_image -- Path to Mynewt kernel image
    tty_file -- Path to TTY file, if specified QEMU will not be used and
                BTP communication with HW DUT will be done over this TTY.
    board -- HW DUT board to use for testing. This parameter is used only
             if tty_file is specified
    """
    global IUT_LOG_FO
    global MYNEWT

    IUT_LOG_FO = open("iut-mynewt.log", "w")

    MYNEWT = MynewtCtl(kernel_image, tty_file, board)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, MYNEWT
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if MYNEWT:
        MYNEWT.stop()
        MYNEWT = None
