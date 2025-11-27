from autopts.pybtp.types import AVDTPMediaType, AVDTPTsep, A2DPCodecType

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, nxp.
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
from autopts.ptsprojects.zephyr.a2dp_wid import a2dp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("A2DP", "TSPX_security_enabled", "False")
    pts.set_pixit("A2DP", "TSPX_bd_addr_iut", "123456789012")
    pts.set_pixit("A2DP", "TSPX_SRC_class_of_device", "080418")
    pts.set_pixit("A2DP", "TSPX_SNK_class_of_device", "04041C")
    pts.set_pixit("A2DP", "TSPX_pin_code", "0000")
    pts.set_pixit("A2DP", "TSPX_delete_link_key", "False")
    pts.set_pixit("A2DP", "TSPX_time_guard", "300000")
    pts.set_pixit("A2DP", "TSPX_use_implicit_send", "True")
    pts.set_pixit("A2DP", "TSPX_media_directory", "C:\\Program Files\\Bluetooth SIG\\Bluetooth PTS\\bin\\audio")
    pts.set_pixit("A2DP", "TSPX_auth_password", "0000")
    pts.set_pixit("A2DP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("A2DP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("A2DP", "TSPX_l2cap_psm", "1011")
    pts.set_pixit("A2DP", "TSPX_no_confirmations", "False")
    pts.set_pixit("A2DP", "TSPX_mpeg24_bitrate", "00000000000000000000000")
    pts.set_pixit("A2DP", "TSPX_mpeg24_bitrate_support", "False")
    pts.set_pixit("A2DP", "TSPX_mpegd_bitrate", "00000000000000000000000")
    pts.set_pixit("A2DP", "TSPX_mpegd_bitrate_support", "False")


def test_cases(ptses):
    """
    Returns a list of A2DP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(lambda: pts.update_pixit_param(
            "A2DP", "TSPX_delete_link_key", "True")),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "A2DP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_a2dp),
        TestFunc(stack.a2dp_init),
    ]

    custom_test_cases = [
    ]

    test_case_name_list = pts.get_test_case_list('A2DP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        if tc_name.startswith("A2DP/SNK/") and tc_name != 'A2DP/SNK/SYN/BV-01-C':
            instance = ZTestCase("A2DP", tc_name,
                                cmds=pre_conditions +
                                [TestFunc(btp.a2dp_register_endpoint, AVDTPMediaType.audio,
                                        AVDTPTsep.SINK, A2DPCodecType.SBC, 0, None)],
                                generic_wid_hdl=a2dp_wid_hdl)
        elif tc_name == 'A2DP/SNK/SYN/BV-01-C':
            instance = ZTestCase("A2DP", tc_name,
                                cmds=pre_conditions +
                                [TestFunc(btp.a2dp_register_endpoint, AVDTPMediaType.audio,
                                        AVDTPTsep.SINK, A2DPCodecType.SBC, 1, None)],
                                generic_wid_hdl=a2dp_wid_hdl)
        elif tc_name.startswith("A2DP/SRC/"):
            instance = ZTestCase("A2DP", tc_name,
                                cmds=pre_conditions +
                                [TestFunc(btp.a2dp_register_endpoint, AVDTPMediaType.audio,
                                        AVDTPTsep.SOURCE, A2DPCodecType.SBC, 0, None)],
                                generic_wid_hdl=a2dp_wid_hdl)
        tc_list.append(instance)

    return tc_list
