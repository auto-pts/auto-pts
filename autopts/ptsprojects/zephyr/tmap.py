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

import struct
from enum import IntEnum

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.tmap_wid import tmap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("TMAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("TMAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("TMAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("TMAP", "TSPX_time_guard", "180000")
    pts.set_pixit("TMAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("TMAP", "TSPX_tester_database_file",
                  r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_TMAP_db.xml")
    pts.set_pixit("TMAP", "TSPX_mtu_size", "64")
    pts.set_pixit("TMAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("TMAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("TMAP", "TSPX_pin_code", "0000")
    pts.set_pixit("TMAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("TMAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("TMAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("TMAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("TMAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("TMAP", "TSPX_Connection_Interval", "120")
    pts.set_pixit("TMAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("TMAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("TMAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("TMAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("TMAP", "TSPX_TARGET_LATENCY", "TARGET_LOWER_LATENCY")
    pts.set_pixit("TMAP", "TSPX_TARGET_PHY", "LE_2M_PHY")


def test_cases(ptses):
    """
    Returns a list of TMAP test cases
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
        TestFunc(lambda: pts.update_pixit_param("TMAP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(btp.core_reg_svc_tmap),
        TestFunc(btp.core_reg_svc_vcp),
        TestFunc(btp.core_reg_svc_tbs),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(stack.cap_init),
        TestFunc(stack.tmap_init),
        TestFunc(stack.vcp_init),
        TestFunc(stack.tbs_init),
        TestFunc(stack.csip_init),
    ]

    test_case_name_list = pts.get_test_case_list('TMAP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('TMAP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=tmap_wid_hdl)

        tc_list.append(instance)

    return tc_list
