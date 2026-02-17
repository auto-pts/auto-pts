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
from autopts.ptsprojects.iutctl import IutCtl

log = logging.debug

CLI_SUPPORT = ['tty', 'hci', 'qemu']


class ZephyrCtl(IutCtl):
    """Zephyr OS Control Class"""

    def __init__(self, args):
        super().__init__(args)
        self._rtt_logger_name = "Logger"
        self.boot_log = "Booting Zephyr OS build"

    def stop(self):
        super().stop()

    def remove_flash_bin(self):
        flash_bin = os.path.join(AUTOPTS_ROOT_DIR, 'flash.bin')
        if os.path.exists(flash_bin):
            os.remove(flash_bin)


def init_iutctl(args):
    """IUT init routine

    args -- Argument
    """
    return ZephyrCtl(args)
