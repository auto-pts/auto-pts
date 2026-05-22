#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, NXP.
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
from autopts.ptsprojects.zephyr.pbap_wid import pbap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

AUTH_PASSWORD = '0000'


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("PBAP", "TSPX_auth_password", AUTH_PASSWORD)
    pts.set_pixit("PBAP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("PBAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("PBAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("PBAP", "TSPX_pin_code", '0000')
    pts.set_pixit("PBAP", "TSPX_time_guard", "300000")
    pts.set_pixit("PBAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("PBAP", "TSPX_server_class_of_device", "100204")
    pts.set_pixit("PBAP", "TSPX_client_class_of_device", "100204")
    # pts.set_pixit("PBAP", "TSPX_PSE_vCardSelector", "0000000000000001")
    pts.set_pixit("PBAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("PBAP", "TSPX_telecom_folder_path", "telecom")
    pts.set_pixit("PBAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("PBAP", "TSPX_SPP_rfcomm_channel", "03")
    pts.set_pixit("PBAP", "TSPX_l2cap_psm", "1005")
    pts.set_pixit("PBAP", "TSPX_rfcomm_channel", "2")
    pts.set_pixit("PBAP", "TSPX_no_confirmations", "FALSE")
    pts.set_pixit("PBAP", "TSPX_Automation", "FALSE")
    pts.set_pixit("PBAP", "TSPX_search_criteria", "PTS")
    pts.set_pixit("PBAP", "TSPX_PullVCardEntry_invalid_value", "F1984D696B612048C3A46B6B696E656E")


def test_cases(ptses):
    """
    Returns a list of PBAP test cases
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
                 "PBAP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_pbap),
        TestFunc(stack.pbap_init)
    ]

    custom_test_cases = []

    test_case_name_list = pts.get_test_case_list('PBAP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        if tc_name in ['PBAP/PCE/PBF/BV-03-C', 'PBAP/PCE/PDF/BV-06-C', 'PBAP/PSE/PBF/BV-03-C', 'PBAP/PSE/PDF/BV-06-C']:
            instance = ZTestCase("PBAP", tc_name,
                                cmds=pre_conditions +
                                [TestFunc(btp.pbap_disable_auto_send)],
                                generic_wid_hdl=pbap_wid_hdl)
        else:
            instance = ZTestCase('PBAP', tc_name, cmds=pre_conditions,
                                        generic_wid_hdl=pbap_wid_hdl)
        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
