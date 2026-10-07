#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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

from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.ptsprojects.mynewt.rap_wid import rap_wid_hdl
from autopts.client import get_unique_name
from autopts.pybtp.types import Addr, AdType, AdFlags, uuid_to_le_hex_str, UUID
from autopts.utils import ResultWithFlag


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("RAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("RAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("RAP", "TSPX_time_guard", "180000")
    pts.set_pixit("RAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("RAP", "TSPX_mtu_size", "60")
    pts.set_pixit("RAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("RAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("RAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("RAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]
    pts2.set_pixit("RAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("RAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("RAP", "TSPX_time_guard", "180000")
    pts2.set_pixit("RAP", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("RAP", "TSPX_mtu_size", "60")
    pts2.set_pixit("RAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts2.set_pixit("RAP", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("RAP", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("RAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")


def test_cases(ptses):
    """
    Returns a list of RAP test cases
    ptses -- list of PyPTS instances
    """

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    ad = {
        AdType.name_full: iut_device_name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: uuid_to_le_hex_str(UUID.RAS),
    }

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "RAP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt_cl),
        TestFunc(stack.gatt_cl_init),
        TestFunc(btp.core_reg_svc_rap),
        TestFunc(stack.rap_init)
    ]

    pre_conditions_2 = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "RAP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt_cl),
        TestFunc(stack.gatt_cl_init),
        TestFunc(btp.core_reg_svc_rap),
        TestFunc(stack.rap_init),
        TestFunc(lambda: set_addr(
            stack.gap.iut_addr_get_str())),
    ]

    pre_conditions_server = pre_conditions + [
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(lambda: btp.gap_start_advertising(ad=ad)),
    ]

    test_case_name_list = pts.get_test_case_list('RAP')
    tc_list = []

    custom_test_cases = [
        ZTestCase("RAP", "RAP/RES/RSPF/BV-02-C",
                  pre_conditions_2 + [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("RAP/RES/RSPF/BV-02-C", 20001),
                                SynchPoint("RAP/RES/RSPF/BV-02-C_LT2", 20001)]),
                  ],
                  generic_wid_hdl=rap_wid_hdl,
                  lt2="RAP/RES/RSPF/BV-02-C_LT2"),
        ZTestCase("RAP", "RAP/RES/RSPF/BV-03-C",
                  pre_conditions_2 + [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("RAP/RES/RSPF/BV-03-C", 20001),
                                SynchPoint("RAP/RES/RSPF/BV-03-C_LT2", 20001)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("RAP/RES/RSPF/BV-03-C", 8),
                                SynchPoint("RAP/RES/RSPF/BV-03-C_LT2", 3)]),
                  ],
                  generic_wid_hdl=rap_wid_hdl,
                  lt2="RAP/RES/RSPF/BV-03-C_LT2"),
        ZTestCase("RAP", "RAP/RES/RSPF/BV-04-C",
                  pre_conditions_2,
                  generic_wid_hdl=rap_wid_hdl,
                  lt2="RAP/RES/RSPF/BV-04-C_LT2"),
        ZTestCase("RAP", "RAP/RES/RSPF/BV-05-C",
                  pre_conditions_2,
                  generic_wid_hdl=rap_wid_hdl,
                  lt2="RAP/RES/RSPF/BV-05-C_LT2"),
    ]

    for tc_name in test_case_name_list:
        instance = ZTestCase('RAP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=rap_wid_hdl)

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
                 "RAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90, clear=True))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("RAP", "RAP/RES/RSPF/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=rap_wid_hdl),
        ZTestCaseSlave("RAP", "RAP/RES/RSPF/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=rap_wid_hdl),
        ZTestCaseSlave("RAP", "RAP/RES/RSPF/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=rap_wid_hdl),
        ZTestCaseSlave("RAP", "RAP/RES/RSPF/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=rap_wid_hdl),
    ]
    return tc_list + test_cases_lt2
