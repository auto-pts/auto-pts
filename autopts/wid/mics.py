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


def hdl_wid_20001(_: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_1(_: WIDParams):
    """Please make sure IUT has set its Mute state to Disabled (0x02)"""
    stack = get_stack()
    btp.mics_mute_read()
    ev = stack.mics.wait_mute_state_ev(30, remove=True)
    if ev and ev[0] == 2:
        # mute == 2
        return True

    btp.mics_mute_disable()
    ev = stack.mics.wait_mute_state_ev(30, remove=False)
    if ev and ev[0] != 2:
        # mute != 2
        return False

    return True


def hdl_wid_5(_: WIDParams):
    """
    Please update the Mute characteristic to 0 or 1
    (whichever is different than the value in step 1) then send notification
    of the Mute characteristic.
    """
    stack = get_stack()
    if stack.mics.mute_state == 0:
        btp.mics_mute()
    else:
        btp.mics_unmute()

    ev = stack.mics.wait_mute_state_ev(30, remove=False)
    if ev is None:
        return False

    return True


def hdl_wid_6(_: WIDParams):
    """Please make sure the Mute characteristic is initially set to 0 or 1."""
    stack = get_stack()
    btp.mics_mute_read()
    ev = stack.mics.wait_mute_state_ev(30, remove=False)
    if ev is None:
        return False

    stack.mics.mute_state = ev[0]

    if stack.mics.mute_state not in [0, 1]:
        return False

    return True
