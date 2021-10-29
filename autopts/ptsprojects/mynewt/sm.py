#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

"""SM test cases"""

from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.mynewt.sm_wid import sm_wid_hdl
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase


def set_pixits(ptses):
    """Setup SM profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("SM", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("SM", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("SM", "TSPX_time_guard", "180000")
    pts.set_pixit("SM", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("SM", "TSPX_new_key_failed_count", "0")
    pts.set_pixit("SM", "TSPX_Bonding_Flags", "01")
    pts.set_pixit("SM", "TSPX_ATTR_HANDLE", "0000")
    pts.set_pixit("SM", "TSPX_ATTR_VALUE", "0000000000000000")
    pts.set_pixit("SM", "TSPX_Min_Encryption_Key_Length", "07")
    pts.set_pixit("SM", "TSPX_OOB_Data", "0000000000000000FE12036E5A889F4D")
    pts.set_pixit("SM", "TSPX_tester_role_optional", "L2CAP_ROLE_INITIATOR")


def test_cases(ptses):
    """Returns a list of SM test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    stack.gap_init()

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_iut_device_name_in_adv_packet_for_random_address",
                          iut_device_name)),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_OOB_Data", stack.gap.oob_legacy)),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_Bonding_Flags", "01"
                          if stack.gap.current_settings_get('Bondable')
                          else "00")),
                      # FIXME Find better place to store PTS bdaddr
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
        ZTestCase("SM", "SM/CEN/PROT/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/PROT/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/JW/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/JW/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/JW/BI-03-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/PKE/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_set_mitm_off),
                   TestFunc(btp.gap_set_bondable_off)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/OOB/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BV-10-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/OOB/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_oob_legacy_set_data, stack.gap.oob_legacy)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/SIP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_display)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/SIP/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_display),
                   TestFunc(btp.gap_set_mitm_off)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/SIE/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/SCJW/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_set_mitm_off),
                   TestFunc(btp.gap_set_bondable_off)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/SCPK/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_set_mitm_off),
                   TestFunc(btp.gap_set_bondable_off)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/SCPK/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_set_bondable_on)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/SCJW/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_set_mitm_off),
                   TestFunc(btp.gap_set_bondable_off)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/SCPK/BI-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only)],
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/CEN/SCOB/BV-04-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        ZTestCase("SM", "SM/PER/SCOB/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('SM')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('SM', tc_name,
                             pre_conditions +
                             [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                             generic_wid_hdl=sm_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
