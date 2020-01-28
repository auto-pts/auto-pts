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

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.bluez.btestcase import BTestCase

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.bluez.btestcase import BTestCase

from pybtp import btp
from pybtp.types import Addr, IOCap
from ptsprojects.stack import get_stack
from sm_wid import sm_wid_hdl


def set_pixits(pts):
    """Setup SM profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    pts -- Instance of PyPTS"""

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


def test_cases(pts):
    """Returns a list of SM test cases
    pts -- Instance of PyPTS"""

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    stack.gap_init()

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

    test_cases = [
        BTestCase("SM", "SM/MAS/PROT/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/PROT/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/JW/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/JW/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BI-02-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/JW/BI-03-C",
                  pre_conditions,
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/JW/BI-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/PKE/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/PKE/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/PKE/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/PKE/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/PKE/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/PKE/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/PKE/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/OOB/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/OOB/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/OOB/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/OOB/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/EKS/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/EKS/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/EKS/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/EKS/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/SIGN/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.core_reg_svc_gatt)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/SIGN/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/SIGN/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/KDU/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/KDU/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/KDU/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/KDU/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/KDU/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/KDU/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/KDU/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/SIP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/MAS/SIP/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
        BTestCase("SM", "SM/SLA/SIE/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=sm_wid_hdl),
    ]

    return test_cases


def main():
    """Main."""
    import ptsprojects.zephyr.iutctl as iutctl

    iutctl.init_stub()

    test_cases_ = test_cases("AB:CD:EF:12:34:56")

    for test_case in test_cases_:
        print
        print test_case

        if test_case.edit1_wids:
            print "edit1_wids: %r" % test_case.edit1_wids

        if test_case.verify_wids:
            print "verify_wids: %r" % test_case.verify_wids

        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)


if __name__ == "__main__":
    main()
