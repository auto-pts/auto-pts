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

from autopts.ptsprojects.zephyr.iutctl import get_iut
from autopts.pybtp import btp

log = logging.debug


# wid handlers section begin
def hdl_wid_143(desc):
    zephyrctl = get_iut()

    zephyrctl.wait_iut_ready_event()
    btp.core_reg_svc_gap()
    btp.gap_read_ctrl_info()

    return True
