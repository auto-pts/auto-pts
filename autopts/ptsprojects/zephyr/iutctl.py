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

from autopts.config import AUTOPTS_ROOT_DIR
from autopts.ptsprojects.iutctl import IutCtl, IutCtlWrapper

log = logging.debug
ZEPHYR = None

CLI_SUPPORT = ['tty', 'hci', 'qemu']


def create_zephyr_ctl_class(use_wrapper: bool):
    base = IutCtlWrapper if use_wrapper else IutCtl

    class ZephyrCtl(base):
        """Zephyr OS Control Class"""

        def __init__(self, args):
            super().__init__(args)
            self._rtt_logger_name = "Logger"
            self.boot_log = "Booting Zephyr OS build"

        def remove_flash_bin(self):
            flash_bin = os.path.join(AUTOPTS_ROOT_DIR, 'flash.bin')
            if os.path.exists(flash_bin):
                os.remove(flash_bin)

    return ZephyrCtl


def get_iut():
    return ZEPHYR


def init(args):
    """IUT init routine

    args -- Argument
    """
    global ZEPHYR

    if len(args.iut_targets_args) == 1:
        use_wrapper = False
        args = next(iter(args.iut_targets_args.values()))
    else:
        use_wrapper = True

    zephyr_ctl_class = create_zephyr_ctl_class(use_wrapper)

    ZEPHYR = zephyr_ctl_class(args)


def cleanup():
    """IUT cleanup routine"""
    global ZEPHYR
    if ZEPHYR:
        ZEPHYR.stop()
        ZEPHYR = None
