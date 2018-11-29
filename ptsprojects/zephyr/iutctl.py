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
import os
import logging
import shlex

from pybtp import defs
from pybtp.types import BTPError
from pybtp.iutctl_common import BTPWorker

log = logging.debug
ZEPHYR = None

# qemu binary should be installed in shell PATH
QEMU_BIN = "qemu-system-arm"

# BTP communication transport: unix domain socket file name
BTP_ADDRESS = "/tmp/bt-stack-tester"

# qemu log file object
IUT_LOG_FO = None


def get_qemu_cmd(kernel_image):
    """Returns qemu command to start Zephyr

    kernel_image -- Path to Zephyr kernel image"""

    qemu_cmd = ("%s -cpu cortex-m3 -machine lm3s6965evb -nographic "
                "-serial mon:stdio "
                "-serial unix:%s "
                "-serial unix:/tmp/bt-server-bredr "
                "-kernel %s" %
                (QEMU_BIN, BTP_ADDRESS, kernel_image))

    return qemu_cmd


class ZephyrCtl:
    '''Zephyr OS Control Class'''

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
        """Starts the Zephyr OS"""

        log("%s.%s", self.__class__, self.start.__name__)

        self.btp_socket = BTPWorker()
        self.btp_socket.open()

        if self.tty_file:
            socat_cmd = ("socat -x -v %s,rawer,b115200 UNIX-CONNECT:%s" %
                         (self.tty_file, BTP_ADDRESS))

            log("Starting socat process: %s", socat_cmd)

            # socat dies after socket is closed, so no need to kill it
            self.socat_process = subprocess.Popen(shlex.split(socat_cmd),
                                                  shell=False,
                                                  stdout=IUT_LOG_FO,
                                                  stderr=IUT_LOG_FO)
        else:
            qemu_cmd = get_qemu_cmd(self.kernel_image)

            log("Starting QEMU zephyr process: %s", qemu_cmd)

            # TODO check if zephyr process has started correctly
            self.qemu_process = subprocess.Popen(shlex.split(qemu_cmd),
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
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.qemu_process and self.qemu_process.poll() is None:
            self.qemu_process.terminate()
            self.qemu_process.wait()  # do not let zombies take over
            self.qemu_process = None


class ZephyrCtlStub:
    '''Zephyr OS Control Class with stubs for testing'''

    def __init__(self):
        """Constructor."""
        pass

    def start(self):
        """Starts the Zephyr OS"""
        log("%s.%s", self.__class__, self.start.__name__)

    def stop(self):
        """Powers off the Zephyr OS"""
        log("%s.%s", self.__class__, self.stop.__name__)


class Board:
    """HW DUT board"""

    arduino_101 = "arduino_101"
    c1000 = "c1000"
    nrf52 = "nrf52"

    # for command line options
    names = [
        arduino_101,
        c1000,
        nrf52
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
            logging.error("openocd reset failed")

    def get_openocd_reset_cmd(self, openocd_bin, openocd_scripts, openocd_cfg):
        """Compute openocd reset command"""
        if not os.path.isfile(openocd_bin):
            raise Exception("openocd %r not found!", openocd_bin)

        if not os.path.isdir(openocd_scripts):
            raise Exception("openocd scripts %r not found!", openocd_scripts)

        if not os.path.isfile(openocd_cfg):
            raise Exception("openocd config %r not found!", openocd_cfg)

        reset_cmd = ('%s -s %s -f %s -c "init" -c "targets 1" '
                     '-c "reset halt" -c "reset run" -c "shutdown"' %
                     (openocd_bin, openocd_scripts, openocd_cfg))

        return reset_cmd

    def get_reset_cmd(self):
        """Return reset command for a board"""
        reset_cmd_getters = {
            self.arduino_101: self._get_reset_cmd_arduino_101,
            self.c1000: self._get_reset_cmd_c1000,
            self.nrf52: self._get_reset_cmd_nrf52
        }

        reset_cmd_getter = reset_cmd_getters[self.name]

        reset_cmd = reset_cmd_getter()

        return reset_cmd

    def _get_reset_cmd_arduino_101(self):
        """Return reset command for Arduino 101 DUT

        Dependency: Zephyr SDK

        """
        openocd_bin = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/bin/openocd"
        openocd_scripts = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/share/openocd/scripts"
        openocd_cfg = os.path.join(
            os.path.split(self.kernel_image)[0],
            "../../../../../../boards/x86/arduino_101/support/openocd.cfg")

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_c1000(self):
        """Return reset command for C1000 DUT

        Dependency: zflash

        """
        openocd_bin = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/bin/openocd"
        openocd_scripts = "/opt/zephyr-sdk/sysroots/x86_64-pokysdk-linux/usr/share/openocd/scripts"
        openocd_cfg = os.path.join(
            os.path.split(self.kernel_image)[0],
            "../../../../../../boards/x86/quark_se_c1000_devboard/support/")

        return self.get_openocd_reset_cmd(openocd_bin, openocd_scripts,
                                          openocd_cfg)

    def _get_reset_cmd_nrf52(self):
        """Return reset command for nRF52 DUT

        Dependency: nRF5x command line tools

        """
        return 'nrfjprog -f nrf52 -r'


def get_iut():
    return ZEPHYR


def init_stub():
    """IUT init routine for testings"""
    global ZEPHYR
    ZEPHYR = ZephyrCtlStub()


def init(kernel_image, tty_file, board=None):
    """IUT init routine

    kernel_image -- Path to Zephyr kernel image
    tty_file -- Path to TTY file, if specified QEMU will not be used and
                BTP communication with HW DUT will be done over this TTY.
    board -- HW DUT board to use for testing. This parameter is used only
             if tty_file is specified
    """
    global IUT_LOG_FO
    global ZEPHYR

    IUT_LOG_FO = open("iut-zephyr.log", "w")

    ZEPHYR = ZephyrCtl(kernel_image, tty_file, board)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, ZEPHYR
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
