#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025-2026 NXP
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

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.rfcomm_wid import rfcomm_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("RFCOMM", "TSPX_time_guard", "180000")
    pts.set_pixit("RFCOMM", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("RFCOMM", "TSPX_server_channel_iut", "05")
    pts.set_pixit("RFCOMM", "TSPX_serviceclassid_uuid16", "1101")
    pts.set_pixit("RFCOMM", "TSPX_delete_link_key", "TRUE")


def test_cases(ptses):
    """
    Returns a list of RFCOMM test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "RFCOMM", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_rfcomm),
        TestFunc(stack.rfcomm_init),
    ]

    test_case_name_list = pts.get_test_case_list('RFCOMM')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('RFCOMM', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=rfcomm_wid_hdl)

        tc_list.append(instance)

    return tc_list
