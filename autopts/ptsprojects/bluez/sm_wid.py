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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


# wid handlers section begin
def hdl_wid_100(_: WIDParams):
    btp.gap_conn()
    btp.gap_wait_for_connection()
    btp.gap_pair()
    return True


def hdl_wid_102(_: WIDParams):
    btp.gap_disconn()
    return True


def hdl_wid_108(_: WIDParams):
    return True


def hdl_wid_109(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_115(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True
