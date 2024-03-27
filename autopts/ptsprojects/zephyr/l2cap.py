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

"""L2CAP test cases"""

from autopts.pybtp import btp, defs
from autopts.pybtp.types import Addr, L2CAPConnectionResponse, IOCap
from autopts.client import get_unique_name
from autopts.wid import l2cap_wid_hdl
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase


le_psm = 128
psm_unsupported = 241
le_initial_mtu = 120
le_initial_mtu_equal_mps = 96
bredr_psm = 4097
bredr_spsm = 129


def set_pixits(ptses):
    """Setup L2CAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("L2CAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("L2CAP", "TSPX_bd_addr_iut_le", "DEADBEEFDEAD")
    pts.set_pixit("L2CAP", "TSPX_client_class_of_device", "100104")
    pts.set_pixit("L2CAP", "TSPX_server_class_of_device", "100104")
    pts.set_pixit("L2CAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_pin_code", "0000")
    pts.set_pixit("L2CAP", "TSPX_delete_ltk", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_flushto", "FFFF")
    pts.set_pixit("L2CAP", "TSPX_inmtu", "02A0")
    pts.set_pixit("L2CAP", "TSPX_no_fail_verdicts", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_iut_supported_max_channels", "5")
    pts.set_pixit("L2CAP", "TSPX_IUT_mps", "0030")
    pts.set_pixit("L2CAP", "TSPX_outmtu", "02A0")
    pts.set_pixit("L2CAP", "TSPX_tester_mps", "0017")
    pts.set_pixit("L2CAP", "TSPX_tester_mtu", "02A0")
    pts.set_pixit("L2CAP", "TSPX_iut_role_initiator", "True")
    pts.set_pixit("L2CAP", "TSPX_spsm", "0000")
    if (1 == defs.BTP_BR_EDR):
        pts.set_pixit("L2CAP", "TSPX_psm", "1001")
    else:
        pts.set_pixit("L2CAP", "TSPX_psm", "0001")
    pts.set_pixit("L2CAP", "TSPX_psm_unsupported", "0000")
    pts.set_pixit("L2CAP", "TSPX_psm_authentication_required", "00F2")
    pts.set_pixit("L2CAP", "TSPX_psm_authorization_required", "00F3")
    pts.set_pixit("L2CAP", "TSPX_psm_encryption_key_size_required", "00F4")
    pts.set_pixit("L2CAP", "TSPX_time_guard", "180000")
    pts.set_pixit("L2CAP", "TSPX_timer_ertx", "120000")
    pts.set_pixit("L2CAP", "TSPX_timer_ertx_max", "300000")
    pts.set_pixit("L2CAP", "TSPX_timer_ertx_min", "60000")
    pts.set_pixit("L2CAP", "TSPX_timer_rtx", "10000")
    if (1 == defs.BTP_BR_EDR):
        pts.set_pixit("L2CAP", "TSPX_timer_rtx_max", "100000")
    else:
        pts.set_pixit("L2CAP", "TSPX_timer_rtx_max", "100000")
    pts.set_pixit("L2CAP", "TSPX_timer_rtx_min", "60000")
    pts.set_pixit("L2CAP", "TSPX_rfc_mode_tx_window_size", "08")
    pts.set_pixit("L2CAP", "TSPX_rfc_mode_max_transmit", "03")
    pts.set_pixit("L2CAP", "TSPX_rfc_mode_retransmission_timeout", "07D0")
    pts.set_pixit("L2CAP", "TSPX_rfc_mode_monitor_timeout", "2EE0")
    pts.set_pixit("L2CAP", "TSPX_rfc_mode_maximum_pdu_size", "02A0")
    pts.set_pixit("L2CAP", "TSPX_extended_window_size", "0012")
    pts.set_pixit("L2CAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("L2CAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_iut_SDU_size_in_bytes", "144")
    pts.set_pixit("L2CAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_iut_address_type_random", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_tester_adv_interval_min", "0030")
    pts.set_pixit("L2CAP", "TSPX_tester_adv_interval_max", "0050")
    pts.set_pixit("L2CAP", "TSPX_tester_le_scan_interval", "0C80")
    pts.set_pixit("L2CAP", "TSPX_tester_le_scan_window", "0C80")
    pts.set_pixit("L2CAP", "TSPX_tester_conn_interval_min", "0028")
    pts.set_pixit("L2CAP", "TSPX_tester_conn_interval_max", "0050")
    pts.set_pixit("L2CAP", "TSPX_tester_conn_latency", "0000")
    pts.set_pixit("L2CAP", "TSPX_tester_supervision_timeout", "00C8")
    pts.set_pixit("L2CAP", "TSPX_tester_min_CE_length", "0050")
    pts.set_pixit("L2CAP", "TSPX_tester_max_CE_length", "0C80")
    pts.set_pixit("L2CAP", "TSPX_generate_local_busy", "TRUE")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmps_min", "0040")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmps_max", "0100")


def test_cases(ptses):
    """Returns a list of L2CAP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    iut_device_name = get_unique_name(pts)
    stack.gap_init(iut_device_name)

    if (1 == defs.BTP_BR_EDR):
        common = [TestFunc(btp.core_reg_svc_gap),
                TestFunc(btp.core_reg_svc_l2cap),
                TestFunc(btp.gap_read_ctrl_info),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_bd_addr_iut",
                    stack.gap.iut_addr_get_str())),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_bd_addr_iut_le",
                    stack.gap.iut_addr_get_str())),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_spsm", format(bredr_spsm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_authentication_required", format(bredr_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_authorization_required", format(bredr_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_encryption_key_size_required", format(bredr_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_encryption_required", format(bredr_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_unsupported", format(psm_unsupported, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_iut_supported_max_channels", "2")),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_num_concurrent_credit_based_connections", "2")),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmps_min", format(64, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmps_max", format(256, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmtu_min", format(64, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmtu_max", format(256, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_iut_address_type_random",
                    "TRUE" if stack.gap.iut_addr_is_random()
                    else "FALSE")),
                TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]
    else:
        common = [TestFunc(btp.core_reg_svc_gap),
                TestFunc(btp.core_reg_svc_l2cap),
                TestFunc(btp.gap_read_ctrl_info),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_bd_addr_iut",
                    stack.gap.iut_addr_get_str())),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_bd_addr_iut_le",
                    stack.gap.iut_addr_get_str())),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_spsm", format(le_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_authentication_required", format(le_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_authorization_required", format(le_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_encryption_key_size_required", format(le_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_encryption_required", format(le_psm, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_psm_unsupported", format(psm_unsupported, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_iut_supported_max_channels", "2")),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_num_concurrent_credit_based_connections", "2")),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmps_min", format(64, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmps_max", format(256, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmtu_min", format(64, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_l2ca_cbmtu_max", format(256, '04x'))),
                TestFunc(lambda: pts.update_pixit_param(
                    "L2CAP", "TSPX_iut_address_type_random",
                    "TRUE" if stack.gap.iut_addr_is_random()
                    else "FALSE")),
                TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    if (1 == defs.BTP_BR_EDR):
        pre_conditions = common + [TestFunc(stack.l2cap_init, bredr_psm, le_initial_mtu)]
        pre_conditions_success = common + [TestFunc(stack.l2cap_init, bredr_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_psm, le_initial_mtu,
                                                    L2CAPConnectionResponse.success)]
        pre_conditions_authen = common + [TestFunc(stack.l2cap_init, bredr_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_psm, le_initial_mtu,
                                                L2CAPConnectionResponse.insufficient_authentication)]
        pre_conditions_keysize = common + [TestFunc(stack.l2cap_init, bredr_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_psm, le_initial_mtu,
                                                    L2CAPConnectionResponse.insufficient_encryption_key_size)]
        pre_conditions_author = common + [TestFunc(stack.l2cap_init, bredr_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_psm, le_initial_mtu,
                                                L2CAPConnectionResponse.insufficient_authorization)]
        pre_conditions_ecbfc_success = common + [TestFunc(stack.l2cap_init, bredr_spsm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_spsm, le_initial_mtu,
                                                    L2CAPConnectionResponse.success)]
        pre_conditions_ecbfc_keysize = common + [TestFunc(stack.l2cap_init, bredr_spsm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_spsm, le_initial_mtu,
                                                    L2CAPConnectionResponse.insufficient_encryption_key_size)]
        pre_conditions_ecbfc_authen = common + [TestFunc(stack.l2cap_init, bredr_spsm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_spsm, le_initial_mtu,
                                        L2CAPConnectionResponse.insufficient_authentication)]
        pre_conditions_ecbfc_author = common + [TestFunc(stack.l2cap_init, bredr_spsm, le_initial_mtu),
                                        TestFunc(btp.l2cap_bredr_listen, bredr_spsm, le_initial_mtu,
                                                L2CAPConnectionResponse.insufficient_authorization)]
    else:        
        pre_conditions = common + [TestFunc(stack.l2cap_init, le_psm, le_initial_mtu)]
        pre_conditions_success = common + [TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_le_listen, le_psm, le_initial_mtu,
                                                    L2CAPConnectionResponse.success)]
        pre_conditions_authen = common + [TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_le_listen, le_psm, le_initial_mtu,
                                                L2CAPConnectionResponse.insufficient_authentication)]
        pre_conditions_keysize = common + [TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_le_listen, le_psm, le_initial_mtu,
                                                    L2CAPConnectionResponse.insufficient_encryption_key_size)]
        pre_conditions_author = common + [TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
                                        TestFunc(btp.l2cap_le_listen, le_psm, le_initial_mtu,
                                                L2CAPConnectionResponse.insufficient_authorization)]
    if (1 == defs.BTP_BR_EDR):
        custom_test_cases = [
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-04-C",
                    pre_conditions +
                    [TestFunc(lambda: stack.l2cap.psm_set(psm_unsupported))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-11-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-13-C",
                    pre_conditions_author,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-15-C",
                    pre_conditions_keysize,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-25-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            # Enhanced Credit Based Flow Control Channel
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-04-C",
                    pre_conditions +
                    [TestFunc(lambda: stack.l2cap.initial_mtu_set(le_initial_mtu_equal_mps))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-11-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-13-C",
                    pre_conditions_author,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-15-C",
                    pre_conditions_keysize,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-24-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_l2ca_cbmps_max", format(64, '04x')))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-25-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-29-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-32-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-01-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-02-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1)),
                    TestFunc(lambda: stack.l2cap.hold_credits_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-07-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.hold_credits_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/TIM/BV-03-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False")),
                    TestFunc(btp.core_reg_svc_gatt)],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CED/BV-05-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CED/BV-12-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CED/BV-13-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CED/BI-02-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CFD/BV-01-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/CFD/BV-02-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/IEX/BV-01-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-45-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-46-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-48-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-52-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-54-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-55-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-57-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-58-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-60-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-71-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-72-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-79-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-09-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-40-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-47-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-53-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-56-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-59-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-12-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-61-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-13-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-62-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-63-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-14-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-15-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-64-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-16-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-70-C",
                    pre_conditions_ecbfc_keysize +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param(
                        "L2CAP", "TSPX_psm_encryption_key_size_required", format(bredr_spsm, '04x')))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-67-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-68-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-51-C",
                    pre_conditions_ecbfc_authen +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param(
                        "L2CAP", "TSPX_psm_authentication_required", format(bredr_spsm, '04x')))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-69-C",
                    pre_conditions_ecbfc_author +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081")),
                    TestFunc(lambda: pts.update_pixit_param(
                        "L2CAP", "TSPX_psm_authorization_required", format(bredr_spsm, '04x')))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-65-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-42-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-49-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-50-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-10-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-11-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-66-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-73-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-76-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-77-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-78-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-05-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-06-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-07-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-08-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: stack.l2cap.psm_set(bredr_spsm)),
                    TestFunc(lambda: stack.l2cap.initial_mtu_set(le_initial_mtu_equal_mps)),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_psm", "0081"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CID/BV-01-C",
                    pre_conditions_success +
                    [TestFunc(btp.l2cap_le_listen, 0x40, le_initial_mtu, L2CAPConnectionResponse.success)],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CID/BV-02-C",
                    pre_conditions_success +
                    [TestFunc(btp.l2cap_le_listen, bredr_spsm, le_initial_mtu, L2CAPConnectionResponse.success),
                    TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CID/BV-03-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(btp.l2cap_le_listen, 0x40, le_initial_mtu, L2CAPConnectionResponse.success)],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CID/BV-04-C",
                    pre_conditions_ecbfc_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                    generic_wid_hdl=l2cap_wid_hdl),
        ]
    else:
        custom_test_cases = [
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-04-C",
                    pre_conditions +
                    [TestFunc(lambda: stack.l2cap.psm_set(psm_unsupported))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-11-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-13-C",
                    pre_conditions_author,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-15-C",
                    pre_conditions_keysize,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-25-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            # Enhanced Credit Based Flow Control Channel
            ZTestCase("L2CAP", "L2CAP/COS/ECFC/BV-04-C",
                    pre_conditions +
                    [TestFunc(lambda: stack.l2cap.initial_mtu_set(le_initial_mtu_equal_mps))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-11-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-13-C",
                    pre_conditions_author,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-15-C",
                    pre_conditions_keysize,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-24-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_l2ca_cbmps_max", format(64, '04x')))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-25-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-29-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BV-32-C",
                    pre_conditions_authen,
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-01-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-02-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.num_channels_set(1)),
                    TestFunc(lambda: stack.l2cap.hold_credits_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/ECFC/BI-07-C",
                    pre_conditions_success +
                    [TestFunc(lambda: stack.l2cap.hold_credits_set(1))],
                    generic_wid_hdl=l2cap_wid_hdl),
            ZTestCase("L2CAP", "L2CAP/TIM/BV-03-C",
                    pre_conditions_success +
                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False")),
                    TestFunc(btp.core_reg_svc_gatt)],
                    generic_wid_hdl=l2cap_wid_hdl),
        ]

    test_case_name_list = pts.get_test_case_list('L2CAP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('L2CAP', tc_name,
                             pre_conditions_success,
                             generic_wid_hdl=l2cap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        if (tc_name.startswith("L2CAP/ERM/") or tc_name.startswith("L2CAP/STM/") or tc_name.startswith("L2CAP/OFS/")):
            new_instance = ZTestCase("L2CAP", tc_name,
                                    pre_conditions_success +
                                    [TestFunc(lambda: pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "False"))],
                                    generic_wid_hdl=l2cap_wid_hdl)
            instance = new_instance

        tc_list.append(instance)

    return tc_list
