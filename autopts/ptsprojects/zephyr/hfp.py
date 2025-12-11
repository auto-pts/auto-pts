#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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
from autopts.ptsprojects.zephyr.hfp_ag_wid import hfp_ag_wid_hdl
from autopts.ptsprojects.zephyr.hfp_hf_wid import hfp_hf_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp, defs
from autopts.pybtp.types import Addr, IOCap


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("HFP", "TSPX_time_guard", "180000")
    pts.set_pixit("HFP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("HFP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("HFP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("HFP", "TSPX_server_channel_tester", "01")
    pts.set_pixit("HFP", "TSPX_phone_number_memory", "1")


def test_cases(ptses):
    """
    Returns a list of HFP_AG test cases
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
        TestFunc(lambda: pts.update_pixit_param("HFP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
    ]

    ag_pre_conditions = pre_conditions + [
        TestFunc(btp.core_reg_svc_hfp_ag),
        TestFunc(stack.hfp_ag_init),
        TestFunc(btp.hfp_ag_set_default_indicator_value, 1, 5, 0, 5),
        TestFunc(btp.hfp_ag_set_memory_dial_mapping, "1", "1234567"),
        TestFunc(btp.hfp_ag_set_voice_tag_number, "1234567"),
    ]

    hf_pre_conditions = pre_conditions + [
        TestFunc(btp.core_reg_svc_hfp_hf),
        TestFunc(stack.hfp_hf_init),
    ]

    custom_test_cases = [
        ZTestCase("HFP", "HFP/AG/IIC/BV-03-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_default_indicator_value, 0, 5, 0, 5),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/NUM/BV-01-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_subscriber_number,
                                 [{'number': "1234", 'type': 128, 'service': 4},
                                  {'number': "4321", 'type': 128, 'service': 4}]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ATH/BV-09-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_ACTIVE},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ICA/BV-07-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_WAITING},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ECS/BV-02-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-01-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ECS/BV-02-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-04-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-05-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-06-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-07-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/RHH/BV-08-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ATH/BV-03-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_OUTGOING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_ACTIVE},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ATH/BV-05-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_OUTGOING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_ACTIVE},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/TWC/BV-04-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_ongoing_calls,
                                 [{'number': "1234567",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_INCOMING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_HELD},
                                  {'number': "7654321",
                                   'type': 0,
                                   'direction': defs.BTP_HFP_AG_CALL_DIR_OUTGOING,
                                   'status': defs.BTP_HFP_AG_CALL_STATUS_ACTIVE},]),],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ACC/BV-16-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param("HFP",
                                 "TSPX_iut_Synchronous_Connection_method",
                                 "Without a call setup"))],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/ACC/BV-17-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param("HFP",
                                 "TSPX_iut_Synchronous_Connection_method",
                                 "Without a call setup"))],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/OCL/BV-01-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_last_number, "1234567", 0)],
                  generic_wid_hdl=hfp_ag_wid_hdl),
        ZTestCase("HFP", "HFP/AG/TWC/BV-05-C",
                  cmds=ag_pre_conditions +
                       [TestFunc(btp.hfp_ag_set_last_number, "7654321", 0)],
                  generic_wid_hdl=hfp_ag_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list("HFP")
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        if "HFP/AG" in tc_name:
            instance = ZTestCase("HFP", tc_name, cmds=ag_pre_conditions, generic_wid_hdl=hfp_ag_wid_hdl)
        else:
            instance = ZTestCase("HFP", tc_name, cmds=hf_pre_conditions, generic_wid_hdl=hfp_hf_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
