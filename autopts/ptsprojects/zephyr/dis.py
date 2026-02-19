#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

"""DIS test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

dis_wid_hdl = get_wid_handler("zephyr", "dis")

iut_manufacturer_data = 'ABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'


def set_pixits(ptses):
    """Setup DIS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("DIS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("DIS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("DIS", "TSPX_time_guard", "180000")
    pts.set_pixit("DIS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("DIS", "TSPX_mtu_size", "23")
    pts.set_pixit("DIS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("DIS", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("DIS", "TSPX_pin_code", "0000")
    pts.set_pixit("DIS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("DIS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("DIS", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("DIS", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("DIS", "TSPX_tester_appearance", "0000")


def test_cases(ptses):
    """Returns a list of DIS Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_delete_link_key", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)),

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
    ]

    test_case_name_list = pts.get_test_case_list('DIS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("DIS", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=dis_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
