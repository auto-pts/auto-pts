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
from autopts.ptsprojects.zephyr.iutctl import get_iut
from autopts.pybtp import btp

log = logging.debug


# wid handlers section begin
def hdl_wid_143(_):
    """Confirm IUT readiness and read controller information."""
    zephyrctl = get_iut()

    zephyrctl.wait_iut_ready_event()
    btp.core_reg_svc_gap()
    btp.gap_read_ctrl_info()

    return True


def hdl_wid_175(_):
    """
    Please confirm that IUT reports the Confirm Value Failed to the Upper Tester
    """

    stack = get_stack()
    _, _, reason = stack.gap.gap_wait_for_pairing_fail(10)

    # BT_SMP_ERR_CONFIRM_FAILED(0x04) is converted to BT_SECURITY_ERR_AUTH_FAIL(0x01)
    # in zephyr host.
    if reason == 0x01:
        return True

    return False
