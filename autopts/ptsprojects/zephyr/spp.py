#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026, NXP.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.spp_wid import spp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

def set_pixits(ptses):
    pts = ptses[0]

    # Keep time guard and use implicit send similar to RFCOMM profile
    pts.set_pixit("SPP", "TSPX_time_guard", "180000")
    pts.set_pixit("SPP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("SPP", "TSPX_delete_link_key", "TRUE")

def test_cases(ptses):
    """
    Returns a list of SPP test cases
    ptses -- list of PyPTS instances
    """
    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all SPP test cases
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(stack.sdp_init),
        TestFunc(lambda: pts.update_pixit_param(
            "SPP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        # Register both SDP & RFCOMM service since SPP relies on them
        TestFunc(btp.core_reg_svc_sdp),
        TestFunc(btp.core_reg_svc_rfcomm),
        TestFunc(btp.core_reg_svc_spp),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(stack.rfcomm_init),
        TestFunc(stack.spp_init),
    ]

    test_case_name_list = pts.get_test_case_list('SPP')
    tc_list = []

    # Use the same preconditions and the SPP-specific WID handler
    for tc_name in test_case_name_list:
        instance = ZTestCase('SPP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=spp_wid_hdl)
        tc_list.append(instance)

    return tc_list
