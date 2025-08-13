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

import logging
import time

from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


def hdl_wid_3(_: WIDParams):
    time.sleep(2)
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return True


def hdl_wid_49(_: WIDParams):
    time.sleep(30)
    return True


def hdl_wid_92(_: WIDParams):
    time.sleep(2)
    return True


def hdl_wid_98(_: WIDParams):
    time.sleep(5)
    return True


def hdl_wid_118(_: WIDParams):
    return f'{65000:04x}'
