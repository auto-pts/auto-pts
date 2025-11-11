#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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
from autopts.ptsprojects.zephyr.avrcp_wid import avrcp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr, AVRCPChangePathDirection


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("AVRCP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("AVRCP", "TSPX_bd_addr_iut", "A0CDF377E54B")
    pts.set_pixit("AVRCP", "TSPX_class_of_device", "20050C")
    pts.set_pixit("AVRCP", "TSPX_player_feature_bitmask", "FFFFFFFFFFFFFF7F1F00000000000000")
    pts.set_pixit("AVRCP", "TSPX_pin_code", "0000")
    pts.set_pixit("AVRCP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("AVRCP", "TSPX_time_guard", "300000")
    pts.set_pixit("AVRCP", "TSPX_avrcp_only", "TRUE")
    pts.set_pixit("AVRCP", "TSPX_search_string", "1")
    pts.set_pixit("AVRCP", "TSPX_establish_avdtp_stream", "FALSE")
    pts.set_pixit("AVRCP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("AVRCP", "TSPX_avrcp_version", "")
    pts.set_pixit("AVRCP", "TSPX_tester_av_role", "")
    pts.set_pixit("AVRCP", "TSPX_auth_password", "0000")
    pts.set_pixit("AVRCP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("AVRCP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("AVRCP", "TSPX_l2cap_psm", "1011")
    pts.set_pixit("AVRCP", "TSPX_no_confirmations", "FALSE")
    pts.set_pixit("AVRCP", "TSPX_no_cover_art_folder", "")
    pts.set_pixit("AVRCP", "TSPX_tester_initiates_connection", "TRUE")
    pts.set_pixit("AVRCP", "TSPX_empty_folder", "")


def test_cases(ptses):
    """
    Returns a list of AVRCP test cases
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
                 "AVRCP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_avrcp),
        TestFunc(stack.avrcp_init),
    ]

    custom_test_cases = [
        ZTestCase("AVRCP", "AVRCP/TG/MCN/CB/BI-02-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "AVRCP", "TSPX_empty_folder", "empty_folder")),
                          TestFunc(btp.avrcp_tg_change_path,
                                   AVRCPChangePathDirection.FOLDER_DOWN,
                                   "empty_folder")],
                  generic_wid_hdl=avrcp_wid_hdl),
        ZTestCase("AVRCP", "AVRCP/TG/MCN/CB/BI-03-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "AVRCP", "TSPX_empty_folder", "empty_folder")),
                          TestFunc(btp.avrcp_tg_change_path,
                                   AVRCPChangePathDirection.FOLDER_DOWN,
                                   "empty_folder")],
                  generic_wid_hdl=avrcp_wid_hdl),
        ZTestCase("AVRCP", "AVRCP/TG/CA/BI-08-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "AVRCP", "TSPX_no_cover_art_folder", "no_cover_art_folder")),
                          TestFunc(btp.avrcp_tg_change_path,
                                   AVRCPChangePathDirection.FOLDER_DOWN,
                                   "no_cover_art_folder")],
                  generic_wid_hdl=avrcp_wid_hdl),
        ZTestCase("AVRCP", "AVRCP/TG/CA/BI-09-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "AVRCP", "TSPX_no_cover_art_folder", "no_cover_art_folder")),
                          TestFunc(btp.avrcp_tg_change_path,
                                   AVRCPChangePathDirection.FOLDER_DOWN,
                                   "no_cover_art_folder")],
                  generic_wid_hdl=avrcp_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('AVRCP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('AVRCP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=avrcp_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
