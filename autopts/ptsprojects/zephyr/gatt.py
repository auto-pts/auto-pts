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

"""GATT test cases"""
import logging

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import SynchPoint, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.gatt_wid import gatt_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.pybtp.types import UUID, Addr, IOCap, Perm, Prop
from autopts.utils import ResultWithFlag
from autopts.wid.gatt import gattc_wid_hdl_multiple_indications


class Value:
    one_byte_1 = '01'
    one_byte_2 = '02'
    eight_bytes_1 = '0123456789ABCDEF'
    eight_bytes_2 = 'FEDCBA9876543210'
    long_1 = eight_bytes_1 * 4
    long_2 = eight_bytes_2 * 4
    long_3 = eight_bytes_2 * 7
    long_4 = one_byte_1 * 64
    long_5 = eight_bytes_1 * 10
    long_6 = one_byte_2 * 512


def update_service_gatt_sr_gas_bv_01_c():
    btp.gap_wait_for_disconnection(30)
    btp.gatts_change_database(0, 0, 0x02)


def verify_gatt_sr_gpa_bv_04_c(description):
    """Verification function for GATT/SR/GPA/BV-04-C

    Verification is a bit trickier with GATT/SR/GPA/BV-04-C, PTS can ask to
    verify different things between different test case executions. PTS can
    ask:

    1) Please confirm IUT contain: Attribute Handle = '0006'O
       Properties = '02'O,Handle = '0007'O,UUID = '2A00'O

    Ideally, handle properties and UUID would be read by auto-pts from the
    IUT. For now support for multiple tuple of strings to verify is
    implemented in this function. The logical operator between the tuples of
    strings is OR. That is, for the total verification to pass verification of
    one of the tuples must pass.

    """
    logging.debug("Verifying %r", description)
    verification_pass = False

    verify = (
        ("Attribute Handle = '0006'",
         "Properties = '02'",
         "Handle = '0007'",
         "UUID = '%s'" % UUID.device_name),)

    for verify_tuple in verify:
        logging.debug("tuple to verify %r", verify_tuple)

        for text in verify_tuple:
            logging.debug("Verifying: %r", text)
            if text.upper() not in description.upper():
                logging.debug("Verifying fail: %s", text)
                break  # for text in verify_tuple
        else:
            logging.debug("Verifying pass")
            verification_pass = True

        if verification_pass:
            break

    logging.debug("Verification pass: %s", verification_pass)
    return verification_pass


def set_pixits(ptses):
    """Setup GATT profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("GATT", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("GATT", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("GATT", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("GATT", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("GATT", "TSPX_time_guard", "180000")
    pts.set_pixit("GATT", "TSPX_selected_handle", "0012")
    pts.set_pixit("GATT", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("GATT", "TSPX_iut_use_dynamic_bd_addr", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_is_client_periphral", "TRUE")
    pts.set_pixit("GATT", "TSPX_iut_is_server_central", "FALSE")
    pts.set_pixit("GATT", "TSPX_mtu_size", "23")
    pts.set_pixit("GATT", "TSPX_pin_code", "0000")
    pts.set_pixit("GATT", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("GATT", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("GATT", "TSPX_tester_appearance", "0000")
    pts.set_pixit("GATT", "TSPX_bearer_for_le", "EATT")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]

    pts2.set_pixit("GATT", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("GATT", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("GATT", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("GATT", "TSPX_delete_link_key", "TRUE")
    pts2.set_pixit("GATT", "TSPX_time_guard", "180000")
    pts2.set_pixit("GATT", "TSPX_selected_handle", "0012")
    pts2.set_pixit("GATT", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("GATT", "TSPX_iut_use_dynamic_bd_addr", "FALSE")
    pts2.set_pixit("GATT", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts2.set_pixit("GATT", "TSPX_iut_is_client_periphral", "TRUE")
    pts2.set_pixit("GATT", "TSPX_iut_is_server_central", "FALSE")
    pts2.set_pixit("GATT", "TSPX_mtu_size", "23")
    pts2.set_pixit("GATT", "TSPX_pin_code", "0000")
    pts2.set_pixit("GATT", "TSPX_use_dynamic_pin", "FALSE")
    pts2.set_pixit("GATT", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("GATT", "TSPX_tester_appearance", "0000")


def test_cases_server(ptses):
    """Returns a list of GATT Server test cases"""

    pts = ptses[0]

    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pre_conditions = [
                    TestFunc(btp.core_reg_svc_gap),
                    TestFunc(stack.gap_init, iut_device_name),
                    TestFunc(btp.core_reg_svc_gatt),
                    TestFunc(btp.gap_read_ctrl_info),
                    TestFunc(lambda: pts.update_pixit_param(
                        "GATT", "TSPX_bd_addr_iut",
                        stack.gap.iut_addr_get_str())),
                    TestFunc(lambda: set_addr(
                        stack.gap.iut_addr_get_str())),
                    TestFunc(lambda: pts.update_pixit_param(
                        "GATT", "TSPX_iut_use_dynamic_bd_addr",
                        "TRUE" if stack.gap.iut_addr_is_random()
                        else "FALSE")),
                    TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                    TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public),
                    TestFunc(stack.gatt_init)
    ]

    init_server = [
                     TestFunc(btp.gatts_add_svc, 1, UUID.SVND16_0),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND16_0),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_enc | Perm.write_enc,
                              UUID.VND16_1),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_authn | Perm.write_authn,
                              UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                    TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_authz | Perm.write_authz,
                              UUID.VND16_3),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.notify | Prop.indicate,
                              Perm.read | Perm.write,
                              UUID.VND16_4),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write,
                              UUID.CCC),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.notify | Prop.indicate,
                              Perm.read | Perm.write,
                              UUID.VND16_5),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write,
                              UUID.CCC),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write_wo_resp | Prop.auth_swrite,
                              Perm.read | Perm.write,
                              UUID.VND16_6),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                    TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write_wo_resp | Prop.auth_swrite,
                              Perm.read_authn | Perm.write_authn,
                              UUID.VND16_7),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                      TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.ext_prop,
                              Perm.read | Perm.write,
                              UUID.VND16_8),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CEP),
                     TestFunc(btp.gatts_set_val, 0, '0100'),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_enc | Perm.write_enc,
                              UUID.VND16_9),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_enc | Perm.write_enc,
                              UUID.VND16_10),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND128_1),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),

                     TestFunc(btp.gatts_add_svc, 0, UUID.SVND16_1),
                     TestFunc(btp.gatts_add_inc_svc, 1),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND16_0),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND16_1),
                     TestFunc(btp.gatts_set_val, 0, Value.long_2),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read_enc | Perm.write_enc,
                              UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.long_3),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read,
                              Perm.read,
                              UUID.VND16_3),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1 * 10),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write,
                              UUID.VND16_4),
                     TestFunc(btp.gatts_set_val, 0, Value.long_4),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND16_5),
                     TestFunc(btp.gatts_set_val, 0, Value.long_5),

                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write,
                              UUID.VND16_6),
                     TestFunc(btp.gatts_set_val, 0, Value.long_6),

                     TestFunc(btp.gatts_start_server)
                     ]

    custom_test_cases = [
        ZTestCase("GATT", "GATT/SR/GAN/BV-02-C",
                  pre_conditions + init_server + [
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("GATT/SR/GAN/BV-02-C", 1),
                                SynchPoint("GATT/SR/GAN/BV-02-C_LT2", 1)]),
                      TestFunc(get_stack().synch.add_synch_element,
                               [SynchPoint("GATT/SR/GAN/BV-02-C_LT2", 308),
                                SynchPoint("GATT/SR/GAN/BV-02-C", 93)]),
                  ],
                  generic_wid_hdl=gatt_wid_hdl,
                  lt2="GATT/SR/GAN/BV-02-C_LT2"),
        ZTestCase("GATT", "GATT/SR/GAS/BV-03-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=gatt_wid_hdl,
                  lt2="GATT/SR/GAS/BV-03-C-LT2"),
        ZTestCase("GATT", "GATT/SR/GAI/BI-01-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=gattc_wid_hdl_multiple_indications),
        # TODO rewrite GATT/SR/GAS/BV-01-C
        ZTestCase("GATT", "GATT/SR/GAS/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(update_service_gatt_sr_gas_bv_01_c, post_wid=96)],
                  generic_wid_hdl=gatt_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('GATT')
    tc_list = []

    for tc_name in test_case_name_list:
        if not tc_name.startswith('GATT/SR'):
            continue
        instance = ZTestCase('GATT', tc_name,
                             cmds=pre_conditions + init_server,
                             generic_wid_hdl=gatt_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]
    iut_device_name2 = get_unique_name(pts2)

    pre_conditions_lt2 = [
                        TestFunc(lambda: pts2.update_pixit_param(
                                "GATT", "TSPX_bd_addr_iut", iut_addr.get(timeout=90, clear=True))),
                        TestFunc(lambda: pts2.update_pixit_param(
                                "GATT", "TSPX_iut_use_dynamic_bd_addr",
                                "TRUE" if stack.gap.iut_addr_is_random() else "FALSE"))
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("GATT", "GATT/SR/GAS/BV-03-C-LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=gatt_wid_hdl),
        ZTestCaseSlave("GATT", "GATT/SR/GAN/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=gatt_wid_hdl),
    ]

    return tc_list + test_cases_lt2


def test_cases_client(pts):
    """Returns a list of GATT Client test cases

    pts -- Instance of PyPTS

    """

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "GATT", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init)
    ]

    custom_test_cases = [
        # PTS issue #15965
        # ZTestCase("GATT", "GATT/CL/GAW/BV-02-C",
    ]

    test_case_name_list = pts.get_test_case_list('GATT')
    tc_list = []

    for tc_name in test_case_name_list:
        if not tc_name.startswith('GATT/CL'):
            continue
        instance = ZTestCase("GATT", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=gatt_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list


def test_cases(ptses):
    """Returns a list of GATT test cases"""

    tc_list = test_cases_client(ptses[0])
    tc_list += test_cases_server(ptses)

    return tc_list
