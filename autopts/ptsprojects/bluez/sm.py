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
from autopts.ptsprojects.bluez.btestcase import BTestCase
from autopts.ptsprojects.bluez.sm_wid import sm_wid_hdl


def set_pixits(ptses):
    """Setup SM profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("SM", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("SM", "TSPX_SMP_pin_code", "111111")
    pts.set_pixit("SM", "TSPX_OOB_Data", "0000000000000000FE12036E5A889F4D")
    pts.set_pixit("SM", "TSPX_peer_addr_type", "00")
    pts.set_pixit("SM", "TSPX_own_addr_type", "00")
    pts.set_pixit("SM", "TSPX_conn_interval_min", "0190")
    pts.set_pixit("SM", "TSPX_conn_interval_max", "0190")
    pts.set_pixit("SM", "TSPX_conn_latency", "0000")
    pts.set_pixit("SM", "TSPX_client_class_of_device", "100104")
    pts.set_pixit("SM", "TSPX_server_class_of_device", "100104")
    pts.set_pixit("SM", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("SM", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("SM", "TSPX_pin_code", "1234")
    pts.set_pixit("SM", "TSPX_ATTR_HANDLE", "0000")
    pts.set_pixit("SM", "TSPX_ATTR_VALUE", "0000000000000000")
    pts.set_pixit("SM", "TSPX_delay_variation_in", "FFFFFFFF")
    pts.set_pixit("SM", "TSPX_delay_variation_out", "FFFFFFFF")
    pts.set_pixit("SM", "TSPX_flushto", "FFFF")
    pts.set_pixit("SM", "TSPX_inmtu", "02A0")
    pts.set_pixit("SM", "TSPX_inquiry_length", "17")
    pts.set_pixit("SM", "TSPX_latency_in", "FFFFFFFF")
    pts.set_pixit("SM", "TSPX_latency_out", "FFFFFFFF")
    pts.set_pixit("SM", "TSPX_linkto", "3000")
    pts.set_pixit("SM", "TSPX_max_nbr_retransmissions", "10")
    pts.set_pixit("SM", "TSPX_no_fail_verdicts", "FALSE")
    pts.set_pixit("SM", "TSPX_outmtu", "02A0")
    pts.set_pixit("SM", "TSPX_tester_role_optional", "L2CAP_ROLE_INITIATOR")
    pts.set_pixit("SM", "TSPX_page_scan_mode", "00")
    pts.set_pixit("SM", "TSPX_page_scan_repetition_mode", "00")
    pts.set_pixit("SM", "TSPX_peak_bandwidth_in", "00000000")
    pts.set_pixit("SM", "TSPX_peak_bandwidth_out", "00000000")
    pts.set_pixit("SM", "TSPX_psm", "0011")
    pts.set_pixit("SM", "TSPX_service_type_in", "01")
    pts.set_pixit("SM", "TSPX_service_type_out", "01")
    pts.set_pixit("SM", "TSPX_support_retransmissions", "TRUE")
    pts.set_pixit("SM", "TSPX_time_guard", "180000")
    pts.set_pixit("SM", "TSPX_timer_ertx", "120000")
    pts.set_pixit("SM", "TSPX_timer_ertx_max", "300000")
    pts.set_pixit("SM", "TSPX_timer_ertx_min", "60000")
    pts.set_pixit("SM", "TSPX_timer_rtx", "10000")
    pts.set_pixit("SM", "TSPX_timer_rtx_max", "60000")
    pts.set_pixit("SM", "TSPX_timer_rtx_min", "1000")
    pts.set_pixit("SM", "TSPX_token_bucket_size_in", "00000000")
    pts.set_pixit("SM", "TSPX_token_bucket_size_out", "00000000")
    pts.set_pixit("SM", "TSPX_token_rate_in", "00000000")
    pts.set_pixit("SM", "TSPX_token_rate_out", "00000000")
    pts.set_pixit("SM", "TSPX_rfc_mode_mode", "03")
    pts.set_pixit("SM", "TSPX_rfc_mode_tx_window_size", "08")
    pts.set_pixit("SM", "TSPX_rfc_mode_max_transmit", "03")
    pts.set_pixit("SM", "TSPX_rfc_mode_retransmission_timeout", "07D0")
    pts.set_pixit("SM", "TSPX_rfc_mode_monitor_timeout", "2EE0")
    pts.set_pixit("SM", "TSPX_rfc_mode_maximum_pdu_size", "02A0")
    pts.set_pixit("SM", "TSPX_extended_window_size", "0012")
    pts.set_pixit("SM", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("SM", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("SM", "TSPX_iut_SDU_size_in_bytes", "144")
    pts.set_pixit("SM", "TSPX_secure_simple_pairing_pass_key_confirmation",
                  "FALSE")
    pts.set_pixit("SM", "TSPX_Min_Encryption_Key_Length", "07")
    pts.set_pixit("SM", "TSPX_Bonding_Flags", "00")
    pts.set_pixit("SM", "TSPX_delete_ltk", "FALSE")
    pts.set_pixit("SM", "TSPX_mtu_size", "23")
    pts.set_pixit("SM", "TSPX_new_key_failed_count", "0")


def test_cases(ptses):
    """Returns a list of SM test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    stack.gap_init(name=iut_device_name)

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SM", "TSPX_peer_addr_type",
                          "01" if stack.gap.iut_addr_is_random() else "00")),
                      # FIXME Find better place to store PTS bdaddr
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
        BTestCase("SM", "SM/MAS/PROT/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/PROT/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BI-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BI-03-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/SIGN/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.core_reg_svc_gatt)],
                  generic_wid_hdl=sm_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('SM')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = BTestCase('SM', tc_name,
                             pre_conditions +
                             [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                             generic_wid_hdl=sm_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
