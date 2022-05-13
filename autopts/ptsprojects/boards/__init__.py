#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2021, Nordic Semiconductor ASA.
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
import sys
import shlex
import serial.tools.list_ports
import logging
import pkgutil
import importlib
import subprocess
from collections import defaultdict

# For each new board just create a <new-board-name>.py file that contains reset_cmd() function and list
# of supported boards.

log = logging.debug
devices_in_use = []


class Board:
    """HW DUT board"""

    def __init__(self, board_name, iutctl):
        """Constructor of board"""

        self.name = board_name
        self.iutctl = iutctl
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with
        """
        log("About to reset DUT: %r", self.reset_cmd)

        reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                         shell=False,
                                         stdout=self.iutctl.iut_log_file,
                                         stderr=self.iutctl.iut_log_file)

        if reset_process.wait(20):
            logging.error("reset failed")

    def get_reset_cmd(self):
        """Setup reset command"""

        board_mod = importlib.import_module(__package__ + '.' + self.name)

        if board_mod is None:
            raise Exception("Board name %s is not supported!" % self.name)

        return board_mod.reset_cmd(self.iutctl)


def get_build_and_flash(board_name):
    board_mod = importlib.import_module(__package__ + '.' + board_name)

    if board_mod is None:
        raise Exception("Board name %s is not supported!" % board_name)

    try:
        return getattr(board_mod, 'build_and_flash')
    except AttributeError:
        return None


def get_board_type(board_name):
    board_mod = importlib.import_module(__package__ + '.' + board_name)

    if board_mod is None:
        raise Exception("Board name %s is not supported!" % board_name)

    try:
        return getattr(board_mod, 'board_type')
    except AttributeError:
        return None


def get_available_boards(project):
    names = []

    for m in pkgutil.iter_modules(__path__):
        board_mod = importlib.import_module(__package__ + '.' + m.name)

        if project in board_mod.supported_projects:
            names.append(m.name)

    return names


def get_openocd_reset_cmd(openocd_bin, openocd_scripts, openocd_cfg):
    """Compute openocd reset command"""
    if not os.path.isfile(openocd_bin):
        raise Exception("openocd {} not found!".format(openocd_bin))

    if not os.path.isdir(openocd_scripts):
        raise Exception("openocd scripts {} not found!".format(openocd_scripts))

    if not os.path.isfile(openocd_cfg):
        raise Exception("openocd config {} not found!".format(openocd_cfg))

    reset_cmd = ('%s -s %s -f %s -c "init" -c "targets 1" '
                 '-c "reset halt" -c "reset run" -c "shutdown"' %
                 (openocd_bin, openocd_scripts, openocd_cfg))

    return reset_cmd


def get_device_list():
    """Returns dictionary of <tty>: <jlink_srn> (eg. {'/dev/ttyUSB0': 'xxxxxx'}) of found devices"""

    device_list = {}

    for dev in serial.tools.list_ports.comports():
        if dev.serial_number is not None:
            device_list[dev.device] = dev.serial_number.lstrip("0")

    return device_list


def get_free_device(board=None):
    """Returns tty path and jlink serial number of a free device."""
    devices = get_device_list()

    SNR_PREFIX_FOR_BOARD = defaultdict(str, {
        'nrf52': '68',
        'nrf53': ('96', '105'),
    })

    for tty, snr in devices.items():
        if tty not in devices_in_use and snr.startswith(SNR_PREFIX_FOR_BOARD[board]):
            devices_in_use.append(tty)
            return tty, snr

    return None, None


def get_debugger_snr(tty):
    """Return jlink serial number of the device with the given tty.
    """
    jlink = None
    devices = get_device_list()
    if sys.platform == 'win32':
        tty = tty_to_com(tty)

    for dev in devices.keys():
        if dev == tty:
            jlink = devices[dev]
            break

    return jlink


def get_tty(debugger_snr):
    """Return tty or COM of the device with given serial number.
    """
    tty = None
    devices = get_device_list()

    for dev in devices.keys():
        if devices[dev] == debugger_snr:
            tty = dev
            break

    return tty


def release_device(tty):
    if tty and tty in devices_in_use:
        devices_in_use.remove(tty)


def tty_exists(tty):
    if tty is None:
        return False

    if sys.platform == 'win32' and tty.startswith('/dev/ttyS'):
        tty = tty_to_com(tty)

    return tty in [port.device for port in serial.tools.list_ports.comports()]


def com_to_tty(com):
    if com.startswith('COM'):
        return '/dev/ttyS' + str(int(com['COM'.__len__():]) - 1)
    elif com.startswith('/dev/ttyS'):
        return com
    return None


def tty_to_com(tty):
    if tty.startswith('/dev/ttyS'):
        return 'COM' + str(int(tty['/dev/ttyS'.__len__():]) + 1)
    elif tty.startswith('COM'):
        return tty
    return None
