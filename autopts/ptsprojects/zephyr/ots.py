#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

ots_wid_hdl = get_wid_handler("zephyr", "ots")


def set_pixits(ptses):
    """Setup OTS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("OTS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("OTS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("OTS", "TSPX_time_guard", "180000")
    pts.set_pixit("OTS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("OTS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("OTS", "TSPX_mtu_size", 23)
    pts.set_pixit("OTS", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("OTS", "TSPX_pin_code", "0000")
    pts.set_pixit("OTS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("OTS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("OTS", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("OTS", "TSPX_iut_object_name", "Object 1 with very long name")
    pts.set_pixit("OTS", "TSPX_iut_object_size_create", "100")
    pts.set_pixit("OTS", "TSPX_iut_object_read_offset", "20")
    pts.set_pixit("OTS", "TSPX_iut_object_write_offset", "20")
    pts.set_pixit("OTS", "TSPX_iut_object_write_length", "20")


def test_cases(ptses):
    """
    Returns a list of OTS test cases
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
        TestFunc(lambda: pts.update_pixit_param("OTS", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_ots),
        TestFunc(stack.ots_init)
    ]

    pre_conditions_props = [
        TestFunc(btp.otc_register_object, 0, "Object 1 with very long name", 0x01, 0xff, 100, 50)

    ]

    pre_conditions_no_props = [
        TestFunc(btp.otc_register_object, 0, "Object 1 with very long name", 0x01, 0x00, 100, 50)
    ]

    custom_test_cases = [
        ZTestCase('OTS', 'OTS/SR/OAE/BI-06-C',
                  cmds=pre_conditions + pre_conditions_no_props,
                  generic_wid_hdl=ots_wid_hdl),
        ZTestCase('OTS', 'OTS/SR/OAE/BI-07-C',
                  cmds=pre_conditions + pre_conditions_no_props,
                  generic_wid_hdl=ots_wid_hdl),
        ZTestCase('OTS', 'OTS/SR/OAE/BI-08-C',
                  cmds=pre_conditions + pre_conditions_no_props,
                  generic_wid_hdl=ots_wid_hdl),
        ZTestCase('OTS', 'OTS/SR/OAE/BI-09-C',
                  cmds=pre_conditions + pre_conditions_no_props,
                  generic_wid_hdl=ots_wid_hdl),
        ZTestCase('OTS', 'OTS/SR/OLE/BI-03-C',
                  cmds=pre_conditions,
                  generic_wid_hdl=ots_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('OTS')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('OTS', tc_name, cmds=pre_conditions + pre_conditions_props,
                             generic_wid_hdl=ots_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
