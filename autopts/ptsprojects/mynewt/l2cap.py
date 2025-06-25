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

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase
from autopts.ptsprojects.stack import L2cap, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

l2cap_wid_hdl = get_wid_handler("mynewt", "l2cap")
le_psm = 128
psm_unsupported = 241
psm_authentication_required = 242
psm_authorization_required = 243
psm_encryption_key_size_required = 244
psm_encryption_required = 245
le_initial_mtu = 120
le_mps = 100
le_mtu = 260


def set_pixits(ptses):
    """Setup L2CAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("L2CAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("L2CAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_pin_code", "0000")
    pts.set_pixit("L2CAP", "TSPX_delete_ltk", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_l2ca_inmtu", "02A0")
    pts.set_pixit("L2CAP", "TSPX_iut_supported_max_channels", "5")
    pts.set_pixit("L2CAP", "TSPX_tester_mps", "0017")
    pts.set_pixit("L2CAP", "TSPX_tester_mtu", "02A0")
    pts.set_pixit("L2CAP", "TSPX_iut_role_initiator", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_spsm", "0000")
    pts.set_pixit("L2CAP", "TSPX_psm", "0001")
    pts.set_pixit("L2CAP", "TSPX_psm_unsupported", "0000")
    pts.set_pixit("L2CAP", "TSPX_psm_authentication_required", "00F2")
    pts.set_pixit("L2CAP", "TSPX_psm_authorization_required", "00F3")
    pts.set_pixit("L2CAP", "TSPX_psm_encryption_key_size_required", "00F4")
    pts.set_pixit("L2CAP", "TSPX_psm_encryption_required", "00F5")
    pts.set_pixit("L2CAP", "TSPX_time_guard", "180000")
    pts.set_pixit("L2CAP", "TSPX_timer_rtx", "10000")
    pts.set_pixit("L2CAP", "TSPX_timer_rtx_max", "1000")
    pts.set_pixit("L2CAP", "TSPX_timer_rtx_min", "60000")
    pts.set_pixit("L2CAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("L2CAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_iut_SDU_size_in_bytes", "144")
    pts.set_pixit("L2CAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("L2CAP", "TSPX_generate_local_busy", "TRUE")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmps_min", "0064")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmps_max", "0064")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmtu_min", "0040")
    pts.set_pixit("L2CAP", "TSPX_l2ca_cbmtu_max", "00E6")


def test_cases(ptses):
    """Returns a list of L2CAP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()
    iut_device_name = get_unique_name(pts)
    stack.gap_init(iut_device_name)

    common = [TestFunc(btp.core_reg_svc_gap),
              TestFunc(btp.core_reg_svc_l2cap),
              TestFunc(btp.gap_read_ctrl_info),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_bd_addr_iut",
                  stack.gap.iut_addr_get_str())),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_iut_supported_max_channels", "2")),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_tester_mps", format(le_mps, '04x'))),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_tester_mtu", format(le_mtu, '04x'))),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_spsm", format(le_psm, '04x'))),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_psm_unsupported", format(psm_unsupported, '04x'))),
              TestFunc(lambda: pts.update_pixit_param(
                  "L2CAP", "TSPX_l2ca_num_concurrent_credit_based_connections", "2")),
              TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    pre_conditions = common + [
        TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, le_psm)
    ]

    pre_conditions_auth = common + [
        TestFunc(stack.l2cap_init, psm_authentication_required, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, psm_authentication_required)
    ]

    pre_conditions_keysize = common + [
        TestFunc(stack.l2cap_init, psm_encryption_key_size_required, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, psm_encryption_key_size_required)
    ]

    pre_conditions_author = common + [
        TestFunc(stack.l2cap_init, psm_authorization_required, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, psm_authorization_required)
    ]

    pre_conditions_encryption = common + [
        TestFunc(stack.l2cap_init, psm_encryption_required, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, psm_encryption_required, le_initial_mtu)
    ]

    pre_conditions_unacceptable_parameters = common + [
        TestFunc(stack.l2cap_init, le_psm, le_initial_mtu),
        TestFunc(btp.l2cap_le_listen, le_psm, le_initial_mtu, L2cap.unacceptable_parameters)
    ]

    pre_conditions_gatt = common + [
              TestFunc(btp.core_reg_svc_gatt),
    ]

    custom_test_cases = [
        # Connection Parameter Update
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-04-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.psm_set(psm_unsupported))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-10-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.psm_set(psm_authentication_required))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-11-C",
                  pre_conditions_auth,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-12-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.psm_set(psm_authorization_required))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-13-C",
                  pre_conditions_author,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-14-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.psm_set(psm_encryption_key_size_required))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-15-C",
                  pre_conditions_keysize,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-25-C",
                  pre_conditions_encryption,
                  generic_wid_hdl=l2cap_wid_hdl),
        # Enhanced Credit Based Flow Control Channel
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-11-C",
                  pre_conditions_auth,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-13-C",
                  pre_conditions_author,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-15-C",
                  pre_conditions_keysize,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-27-C",
                  pre_conditions_unacceptable_parameters,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-29-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.num_channels_set(1))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BV-32-C",
                  pre_conditions_encryption,
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BI-02-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.l2cap.hold_credits_set(1))],
                  generic_wid_hdl=l2cap_wid_hdl),
        ZTestCase("L2CAP", "L2CAP/ECFC/BI-06-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.update_pixit_param(
                      "L2CAP", "TSPX_l2ca_cbmps_min", "0040"))],
                  generic_wid_hdl=l2cap_wid_hdl),
        # Collision mitigation handling
        ZTestCase("L2CAP", "L2CAP/TIM/BV-03-C",
                  pre_conditions_gatt,
                  generic_wid_hdl=l2cap_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('L2CAP')
    tc_list = []
    for tc_name in test_case_name_list:
        if tc_name.startswith(('L2CAP/COS', 'L2CAP/ECFC', 'L2CAP/LE/CFC')):
            instance = ZTestCase('L2CAP', tc_name,
                                 pre_conditions,
                                 generic_wid_hdl=l2cap_wid_hdl)
        else:
            instance = ZTestCase('L2CAP', tc_name,
                                 common,
                                 generic_wid_hdl=l2cap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
