#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

"""CSIP test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import SynchPoint, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave, ZTestCaseSlave2
from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.utils import ResultWithFlag

csip_wid_hdl = get_wid_handler("zephyr", "csip")


def set_pixits(ptses):
    """Setup CSIP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("CSIP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("CSIP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("CSIP", "TSPX_time_guard", "180000")
    pts.set_pixit("CSIP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("CSIP", "TSPX_tester_database_file",
                  r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_CSIP_db.xml")
    pts.set_pixit("CSIP", "TSPX_mtu_size", "23")
    pts.set_pixit("CSIP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("CSIP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("CSIP", "TSPX_pin_code", "0000")
    pts.set_pixit("CSIP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("CSIP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("CSIP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("CSIP", "TSPX_target_service", "5F03")
    pts.set_pixit("CSIP", "TSPX_set_size", "3")
    pts.set_pixit("CSIP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CSIP", "TSPX_private_addr_int", "120000")
    pts.set_pixit("CSIP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]
    pts2.set_pixit("CSIP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("CSIP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("CSIP", "TSPX_time_guard", "180000")
    pts2.set_pixit("CSIP", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("CSIP", "TSPX_tester_database_file",
                   r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_CSIP_db.xml")
    pts2.set_pixit("CSIP", "TSPX_mtu_size", "23")
    pts2.set_pixit("CSIP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts2.set_pixit("CSIP", "TSPX_delete_link_key", "FALSE")
    pts2.set_pixit("CSIP", "TSPX_pin_code", "0000")
    pts2.set_pixit("CSIP", "TSPX_use_dynamic_pin", "FALSE")
    pts2.set_pixit("CSIP", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("CSIP", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("CSIP", "TSPX_target_service", "5F03")
    pts2.set_pixit("CSIP", "TSPX_set_size", "3")
    pts2.set_pixit("CSIP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts2.set_pixit("CSIP", "TSPX_private_addr_int", "120000")
    pts2.set_pixit("CSIP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")

    if len(ptses) < 3:
        return

    pts3 = ptses[2]
    pts3.set_pixit("CSIP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts3.set_pixit("CSIP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts3.set_pixit("CSIP", "TSPX_time_guard", "180000")
    pts3.set_pixit("CSIP", "TSPX_use_implicit_send", "TRUE")
    pts3.set_pixit("CSIP", "TSPX_tester_database_file",
                   r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_CSIP_db.xml")
    pts3.set_pixit("CSIP", "TSPX_mtu_size", "23")
    pts3.set_pixit("CSIP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts3.set_pixit("CSIP", "TSPX_delete_link_key", "FALSE")
    pts3.set_pixit("CSIP", "TSPX_pin_code", "0000")
    pts3.set_pixit("CSIP", "TSPX_use_dynamic_pin", "FALSE")
    pts3.set_pixit("CSIP", "TSPX_delete_ltk", "TRUE")
    pts3.set_pixit("CSIP", "TSPX_security_enabled", "FALSE")
    pts3.set_pixit("CSIP", "TSPX_target_service", "5F03")
    pts3.set_pixit("CSIP", "TSPX_set_size", "3")
    pts3.set_pixit("CSIP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts3.set_pixit("CSIP", "TSPX_private_addr_int", "120000")
    pts3.set_pixit("CSIP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")


def test_cases(ptses):
    """Returns a list of CSIP test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param("CSIP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(btp.core_reg_svc_csis),
        TestFunc(stack.csip_init),
        TestFunc(lambda: set_addr(
            stack.gap.iut_addr_get_str())),
    ]

    custom_test_cases = [
        ZTestCase("CSIP", "CSIP/CL/SP/BV-07-C", cmds=pre_conditions +
                  [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-07-C", 20100),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT2", 20100),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT3", 20100)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-07-C", 20101),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT2", 20101),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT3", 20101)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-07-C", 4),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT2", 4),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT3", 4)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-07-C", 20115),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT2", 20115),
                                SynchPoint("CSIP/CL/SP/BV-07-C_LT3", 20115)]),
                      # More SyncPoint will be needed, but for now Zephyr does not reach the next wid
                  ],
                  generic_wid_hdl=csip_wid_hdl,
                  lt2="CSIP/CL/SP/BV-07-C_LT2",
                  lt3="CSIP/CL/SP/BV-07-C_LT3"),
        ZTestCase("CSIP", "CSIP/CL/SP/BV-03-C", cmds=pre_conditions +
                  [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-03-C", 20100),
                                SynchPoint("CSIP/CL/SP/BV-03-C_LT2", 20100),
                                SynchPoint("CSIP/CL/SP/BV-03-C_LT3", 20100)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-03-C", 20110),
                                SynchPoint("CSIP/CL/SP/BV-03-C_LT2", 20110),
                                SynchPoint("CSIP/CL/SP/BV-03-C_LT3", 20110)]),
                  ],
                  generic_wid_hdl=csip_wid_hdl,
                  lt2="CSIP/CL/SP/BV-03-C_LT2",
                  lt3="CSIP/CL/SP/BV-03-C_LT3"),
        ZTestCase("CSIP", "CSIP/CL/SP/BV-04-C", cmds=pre_conditions +
                  [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-04-C", 20100),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT2", 20100),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT3", 20100)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-04-C", 20110),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT2", 20110),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT3", 20110)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SP/BV-04-C", 20110),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT2", 20110),
                                SynchPoint("CSIP/CL/SP/BV-04-C_LT3", 20110)]),
                  ],
                  generic_wid_hdl=csip_wid_hdl,
                  lt2="CSIP/CL/SP/BV-04-C_LT2",
                  lt3="CSIP/CL/SP/BV-04-C_LT3"),
        ZTestCase("CSIP", "CSIP/CL/SPE/BI-01-C", cmds=pre_conditions +
                  [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SPE/BI-01-C", 20100),
                                SynchPoint("CSIP/CL/SPE/BI-01-C_LT2", 20100),
                                SynchPoint("CSIP/CL/SPE/BI-01-C_LT3", 20100)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("CSIP/CL/SPE/BI-01-C", 20110),
                                SynchPoint("CSIP/CL/SPE/BI-01-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=csip_wid_hdl,
                  lt2="CSIP/CL/SPE/BI-01-C_LT2",
                  lt3="CSIP/CL/SPE/BI-01-C_LT3"),
    ]

    test_case_name_list = pts.get_test_case_list('CSIP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("CSIP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=csip_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
        TestFunc(lambda: pts2.update_pixit_param(
            "CSIP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90, clear=False))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("CSIP", "CSIP/CL/SP/BV-07-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave("CSIP", "CSIP/CL/SP/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave("CSIP", "CSIP/CL/SP/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave("CSIP", "CSIP/CL/SPE/BI-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=csip_wid_hdl),
    ]

    if len(ptses) < 3:
        return tc_list + test_cases_lt2

    pts3 = ptses[2]

    pre_conditions_lt3 = [
        TestFunc(lambda: pts3.update_pixit_param(
            "CSIP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90, clear=False))),
        TestFunc(btp.set_lt3_addr, pts3.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt3 = [
        ZTestCaseSlave2("CSIP", "CSIP/CL/SP/BV-07-C_LT3",
                        cmds=pre_conditions_lt3,
                        generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave2("CSIP", "CSIP/CL/SP/BV-03-C_LT3",
                        cmds=pre_conditions_lt3,
                        generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave2("CSIP", "CSIP/CL/SP/BV-04-C_LT3",
                        cmds=pre_conditions_lt3,
                        generic_wid_hdl=csip_wid_hdl),
        ZTestCaseSlave2("CSIP", "CSIP/CL/SPE/BI-01-C_LT3",
                        cmds=pre_conditions_lt3,
                        generic_wid_hdl=csip_wid_hdl),
    ]

    return tc_list + test_cases_lt2 + test_cases_lt3
