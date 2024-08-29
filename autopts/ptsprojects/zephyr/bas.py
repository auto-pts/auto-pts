#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant A/S.
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

    pts.set_pixit("BAS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("BAS", "TSPX_time_guard", "180000")
    pts.set_pixit("BAS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("BAS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("BAS", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_BAS_db.xml")
    pts.set_pixit("BAS", "TSPX_mtu_size", "23")
    pts.set_pixit("BAS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("BAS", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("BAS", "TSPX_pin_code", "0000")
    pts.set_pixit("BAS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("BAS", "TSPX_delete_ltk", "FALSE")
    pts.set_pixit("BAS", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("BAS", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("BAS", "TSPX_tester_appearance", "0000")
    pts.set_pixit("BAS", "TSPX_iut_Battery_Low_Energy", "0017")
    pts.set_pixit("BAS", "TSPX_iut_Battery_Critical_Energy", "0005")

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
    ]

    test_case_name_list = pts.get_test_case_list('BAS')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('BAS', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=bas_wid_hdl)

        tc_list.append(instance)

    return tc_list
