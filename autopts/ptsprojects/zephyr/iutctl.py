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

from autopts.ptsprojects.iutctl import IutCtl

log = logging.debug
ZEPHYR = None

CLI_SUPPORT = ['tty', 'hci', 'qemu']


class ZephyrCtl(IutCtl):
    """Zephyr OS Control Class"""

    def __init__(self, args):
        super().__init__(args)
        self._rtt_logger_name = "Logger"
        self.boot_log = "Booting Zephyr OS build"


def get_iut():
    return ZEPHYR


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
