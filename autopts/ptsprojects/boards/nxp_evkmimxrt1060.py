#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2023, NXP.
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

from autopts.ptsprojects.boards import Jlink

log = logging.debug

DEVICE_NAME = 'MIMXRT1062XXX6A'
supported_projects = ['zephyr']


def reset_cmd(iutctl):
    return Jlink(iutctl.debugger_snr, iutctl.device_core).reset_command
