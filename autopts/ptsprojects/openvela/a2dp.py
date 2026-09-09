#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""openvela A2DP test cases"""

from autopts.ptsprojects.openvela.testcase import OpenVelaTestCase
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.wid.a2dp import a2dp_wid_hdl


def set_pixits(ptses):
    """Set A2DP PIXIT values.

    TSPX_bd_addr_iut is intentionally not set here: the IUT address depends on
    whichever controller is attached to the emulator, so it is read from the IUT
    at runtime in test_cases() instead of being hardcoded.
    """
    pts = ptses[0]
    pts.set_pixit("A2DP", "TSPX_time_guard", "300000")

    # Keep both sides bonded across cases. The IUT keeps its bond, so letting
    # PTS drop its link key leaves the two disagreeing and authentication ends
    # in HCI_PIN_OR_KEY_MISSING before AVDTP is reached. Same reasoning as
    # rfcomm, hfp and hid, and it pairs with hdl_wid_12 not unpairing either.
    pts.set_pixit("A2DP", "TSPX_delete_link_key", "FALSE")


def test_cases(ptses):
    """Build A2DP test case list"""
    pts = ptses[0]
    stack = get_stack()

    pts_bd_addr = pts.q_bd_addr

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init),
        # Without a2dp_init() stack.a2dp stays None and the A2DP event handlers
        # have nowhere to record connected / audio_streaming, so WIDs that check
        # the IUT's reported state cannot work.
        TestFunc(stack.a2dp_init),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.gap_set_powered_on),
        # Read the real IUT address from the controller and push it into the
        # PIXIT, otherwise PTS tries to reach a stale hardcoded address and
        # every test times out without the IUT ever seeing a single packet.
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
            "A2DP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.gap_set_connectable),
        TestFunc(btp.gap_set_general_discoverable),
        TestFunc(btp.core_reg_svc_a2dp),
    ]

    test_case_name_list = pts.get_test_case_list('A2DP')
    tc_list = []

    for tc_name in test_case_name_list:
        # The shim's bt_a2dp_connect/disconnect/start/stop are role-specific in
        # the Framework (sink vs source service), so tell the IUT which role to
        # play before the test runs. 0 = sink, 1 = source. It must come after
        # core_reg_svc_a2dp (which registers the A2DP service handlers), so the
        # SET_ROLE command has a handler to hit.
        role = 1 if '/SRC/' in tc_name else 0
        pre = pre_conditions + [TestFunc(btp.a2dp_set_role, role)]

        instance = OpenVelaTestCase('A2DP', tc_name,
                                    cmds=pre,
                                    generic_wid_hdl=a2dp_wid_hdl)
        tc_list.append(instance)

    return tc_list
