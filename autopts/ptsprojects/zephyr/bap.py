#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

"""BAP test cases"""

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.bap_wid import bap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    """Setup BAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("BAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("BAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("BAP", "TSPX_time_guard", "180000")
    pts.set_pixit("BAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit(
        "BAP",
        "TSPX_tester_database_file",
        r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_PXP_db")
    pts.set_pixit("BAP", "TSPX_mtu_size", "64")
    pts.set_pixit("BAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("BAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("BAP", "TSPX_pin_code", "0000")
    pts.set_pixit("BAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("BAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("BAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("BAP", "TSPX_Step_Size", "1")
    pts.set_pixit("BAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("BAP", "TSPX_VS_Codec_ID", "ffff")
    pts.set_pixit("BAP", "TSPX_VS_Company_ID", "ffff")


def test_cases(ptses):
    """Returns a list of BAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_iut_use_dynamic_bd_addr",
                          "TRUE" if stack.gap.iut_addr_is_random()
                          else "FALSE")),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
                      TestFunc(stack.gatt_init),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.gap_set_gendiscov),
                      TestFunc(btp.core_reg_svc_pacs),
                      TestFunc(btp.core_reg_svc_ascs),
                      TestFunc(btp.core_reg_svc_bap),
                      TestFunc(stack.ascs_init),
                      TestFunc(stack.bap_init), ]

    custom_test_cases = [
        # Errata in progress since the PTS should use
        # TSPX_VS_Company_ID and TSPX_VS_Codec_ID instead.
        ZTestCase("BAP", "BAP/UCL/SCC/BV-033-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/UCL/SCC/BV-034-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('BAP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("BAP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=bap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
