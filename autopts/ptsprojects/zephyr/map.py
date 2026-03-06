#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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
from autopts.ptsprojects.stack import MAPInfo, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.map_wid import map_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("MAP", "TSPX_auth_password", "0000")
    pts.set_pixit("MAP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("MAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("MAP", "TSPX_client_class_of_device", "100204")
    pts.set_pixit("MAP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("MAP", "TSPX_initial_path", "")
    pts.set_pixit("MAP", "TSPX_l2cap_psm", "1001")
    pts.set_pixit("MAP", "TSPX_no_confirmations", "FALSE")
    pts.set_pixit("MAP", "TSPX_pin_code", "0000")
    pts.set_pixit("MAP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("MAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("MAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("MAP", "TSPX_server_class_of_device", "100204")
    pts.set_pixit("MAP", "TSPX_time_guard", "60000")
    pts.set_pixit("MAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("MAP", "TSPX_SPP_rfcomm_channel", "03")
    pts.set_pixit("MAP", "TSPX_filter_period_begin", "20100101T000000+0000")
    pts.set_pixit("MAP", "TSPX_filter_period_end", "20111231T125959+0000")
    pts.set_pixit("MAP", "TSPX_filter_recipient", "IUT")
    pts.set_pixit("MAP", "TSPX_filter_originator", "PTS")
    pts.set_pixit("MAP", "TSPX_filter_last_activity_begin", "20100101T000000+0000")
    pts.set_pixit("MAP", "TSPX_filter_last_activity_end", "20111231T125959+0000")
    pts.set_pixit("MAP", "TSPX_default_message_upload_folder_in_msg", "draft")
    pts.set_pixit("MAP", "TSPX_default_test_folder_in_msg", "inbox")
    pts.set_pixit("MAP", "TSPX_message_notification_l2cap_psm", "2025")
    pts.set_pixit("MAP", "TSPX_message_notification_rfcomm_channel", "30")
    pts.set_pixit("MAP", "TSPX_upload_msg_phonenumber", "0000000")
    pts.set_pixit("MAP", "TSPX_upload_msg_emailaddress", "Iut_emailaddress")
    pts.set_pixit("MAP", "TSPX_Automation", "FALSE")


def test_cases(ptses):
    """
    Returns a list of MAP test cases
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
                 "MAP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_map),
        TestFunc(stack.map_init)
    ]

    set_conn = [
        TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
    ]

    custom_test_cases = [
        ZTestCase("MAP", "MAP/MCE/MFB/BV-01-C",
                  pre_conditions + set_conn,
                  generic_wid_hdl=map_wid_hdl),
        ZTestCase("MAP", "MAP/MSE/MFB/BV-02-C",
                  pre_conditions + set_conn,
                  generic_wid_hdl=map_wid_hdl),
        ZTestCase("MAP", "MAP/MSE/GOEP/SRMP/BV-03-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.map.set_pre_conditions(MAPInfo.LOCAL_SRMP, 1))],
                  generic_wid_hdl=map_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('MAP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('MAP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=map_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
