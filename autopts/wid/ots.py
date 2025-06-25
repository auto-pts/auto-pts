#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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


def hdl_wid_0(params: WIDParams):
    """Please make sure no object is stored on the IUT"""

    # Currently this relies on IUT configuration, we don't have BTP command for this

    return True


def hdl_wid_1(params: WIDParams):
    """Please make sure at least one object is stored on the IUT."""

    return True


def hdl_wid_2(params: WIDParams):
    """Please make sure at least two objects are stored on the IUT."""

    return True


def hdl_wid_150(params: WIDParams):
    """Please continue to wait for 30 seconds timeout to close object transfer channel."""

    return True


def hdl_wid_20001(params: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_20109(params: WIDParams):
    """Description: Verify that the Implementation Under Test (IUT) can send
       indication.Expected Value: Any value"""

    return True
