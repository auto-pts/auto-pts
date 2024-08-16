#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant.
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

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.ptsprojects.zephyr.bas_wid import bas_wid_hdl
from autopts.client import get_unique_name
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("BAS", "TSPX_time_guard", "180000")
    pts.set_pixit("BAS", "TSPX_use_implicit_send", "TRUE")


def test_cases(ptses):
    """
    Returns a list of BAS test cases
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
                 "BAS", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_bas),
        TestFunc(stack.bas_init)
        # TestFunc(btp.gap_set_conn),
        # TestFunc(btp.gap_set_gendiscov),
        # TestFunc(lambda: pts.update_pixit_param(
        #             "HAS", "TSPX_iut_use_dynamic_bd_addr",
        #             "TRUE" if stack.gap.iut_addr_is_random()
        #             else "FALSE")),
    ]

    test_case_name_list = pts.get_test_case_list('BAS')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('BAS', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=bas_wid_hdl)

        tc_list.append(instance)

    return tc_list

