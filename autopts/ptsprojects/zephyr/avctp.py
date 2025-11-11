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
from autopts.ptsprojects.zephyr.avctp_wid import avctp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("AVCTP", "TSPX_avctp_psm", "0017")
    pts.set_pixit("AVCTP", "TSPX_avctp_profile_id", "110E")
    pts.set_pixit("AVCTP", "TSPX_connect_avdtp", "FALSE")
    pts.set_pixit("AVCTP", "TSPX_bd_addr_iut", "A0CDF377E54B")
    pts.set_pixit("AVCTP", "TSPX_pin_code", "0000")
    pts.set_pixit("AVCTP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("AVCTP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("AVCTP", "TSPX_class_of_device", "20050C")
    pts.set_pixit("AVCTP", "TSPX_player_feature_bitmask", "FFFFFFFFFFFFFF7F1F00000000000000")
    pts.set_pixit("AVCTP", "TSPX_avrcp_version", "")
    pts.set_pixit("AVCTP", "TSPX_establish_avdtp_stream", "FALSE")
    pts.set_pixit("AVCTP", "TSPX_tester_av_role", "")
    pts.set_pixit("AVCTP", "TSPX_time_guard", "180000")
    pts.set_pixit("AVCTP", "TSPX_avrcp_only", "TRUE")
    pts.set_pixit("AVCTP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("AVCTP", "TSPX_media_directory", "")
    pts.set_pixit("AVCTP", "TSPX_no_confirmations", "FALSE")
    pts.set_pixit("AVCTP", "TSPX_auth_password", "0000")
    pts.set_pixit("AVCTP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("AVCTP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("AVCTP", "TSPX_l2cap_psm", "1011")


def test_cases(ptses):
    """
    Returns a list of AVCTP test cases
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
                 "AVCTP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_avctp),
        TestFunc(stack.avctp_init),
        TestFunc(btp.core_reg_svc_avrcp),
        TestFunc(stack.avrcp_init),
    ]

    test_case_name_list = pts.get_test_case_list('AVCTP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('AVCTP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=avctp_wid_hdl)

        tc_list.append(instance)

    return tc_list
