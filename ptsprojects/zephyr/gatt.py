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

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp, MMI
    from ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp, MMI
    from ptsprojects.zephyr.ztestcase import ZTestCase

from pybtp import btp
from pybtp.types import UUID, Addr, IOCap, Prop, Perm
from time import sleep
import logging
from ptsprojects.stack import get_stack
from ptsprojects.zephyr.gatt_wid import gatt_wid_hdl
from ptsprojects.zephyr.gattc_wid import gattc_wid_hdl


class Value:
    one_byte = '01'
    two_bytes = '0123'
    eight_bytes_1 = '0123456789ABCDEF'
    eight_bytes_2 = 'FEDCBA9876543210'
    long_1 = eight_bytes_1 * 4
    long_2 = eight_bytes_2 * 4


iut_attr_db_off = 0x000b


def __get_attr_hdl_str(offset):
    return '{0:x}'.format(iut_attr_db_off + offset, 'x')


def __get_attr_u16_hdl_str(offset):
    return '{0:04x}'.format(iut_attr_db_off + offset, 'x')


def __get_attr_u16_hdl_uc_str(offset):
    return '{0:04x}'.format(iut_attr_db_off + offset, 'X')


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

    pts -- Instance of PyPTS"""

    if len(ptses) < 2:
        return

    pts = ptses[0]
    pts2 = ptses[1]

    pts.set_pixit("GATT", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("GATT", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("GATT", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("GATT", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("GATT", "TSPX_time_guard", "180000")
    pts.set_pixit("GATT", "TSPX_selected_handle", "0012")
    pts.set_pixit("GATT", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("GATT", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_use_dynamic_bd_addr", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("GATT", "TSPX_tester_database_file",
                  "C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\GATT_Qualification_Test_Databases.xml")
    pts.set_pixit("GATT", "TSPX_iut_is_client_periphral", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_is_server_central", "FALSE")
    pts.set_pixit("GATT", "TSPX_mtu_size", "23")
    pts.set_pixit("GATT", "TSPX_pin_code", "0000")
    pts.set_pixit("GATT", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("GATT", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("GATT", "TSPX_tester_appearance", "0000")


    pts2.set_pixit("GATT", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("GATT", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("GATT", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("GATT", "TSPX_delete_link_key", "TRUE")
    pts2.set_pixit("GATT", "TSPX_time_guard", "180000")
    pts2.set_pixit("GATT", "TSPX_selected_handle", "0012")
    pts2.set_pixit("GATT", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("GATT", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts2.set_pixit("GATT", "TSPX_iut_use_dynamic_bd_addr", "FALSE")
    pts2.set_pixit("GATT", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts2.set_pixit("GATT", "TSPX_tester_database_file",
                  "C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\GATT_Qualification_Test_Databases.xml")
    pts2.set_pixit("GATT", "TSPX_iut_is_client_periphral", "FALSE")
    pts2.set_pixit("GATT", "TSPX_iut_is_server_central", "FALSE")
    pts2.set_pixit("GATT", "TSPX_mtu_size", "23")
    pts2.set_pixit("GATT", "TSPX_pin_code", "0000")
    pts2.set_pixit("GATT", "TSPX_use_dynamic_pin", "FALSE")
    pts2.set_pixit("GATT", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("GATT", "TSPX_tester_appearance", "0000")


def test_cases_server(ptses):
    """Returns a list of GATT Server test cases"""

    if len(ptses) < 2:
        return []

    pts = ptses[0]
    pts2 = ptses[1]

    pts_bd_addr = pts.q_bd_addr
    stack = get_stack()

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "GATT", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "GATT", "TSPX_iut_use_dynamic_bd_addr",
                          "TRUE" if stack.gap.iut_addr_is_random()
                          else "FALSE")),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.gap_set_gendiscov)]

    pre_conditions_1 = [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.core_reg_svc_gatt),
                        TestFunc(btp.gap_read_ctrl_info),
                        TestFunc(lambda: pts.update_pixit_param(
                            "GATT", "TSPX_bd_addr_iut",
                            stack.gap.iut_addr_get_str())),
                        TestFunc(lambda: pts.update_pixit_param(
                            "GATT", "TSPX_iut_use_dynamic_bd_addr",
                            "TRUE" if stack.gap.iut_addr_is_random()
                            else "FALSE")),
                        TestFunc(stack.gatt_init)]

    pre_conditions_lt2 = [TestFunc(lambda: pts2.update_pixit_param(
                                   "GATT", "TSPX_bd_addr_iut",
                                   stack.gap.iut_addr_get_str())),
                          TestFunc(lambda: pts2.update_pixit_param(
                                   "GATT", "TSPX_iut_use_dynamic_bd_addr",
                                   "TRUE" if stack.gap.iut_addr_is_random()
                                   else "FALSE"))]

    init_server_1 = [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.nofity,
                              Perm.read | Perm.write, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1 * 10),
                     TestFunc(btp.gatts_add_svc, 0, UUID.VND16_3),
                     TestFunc(btp.gatts_add_inc_svc, 1),
                     TestFunc(btp.gatts_add_char, 0, 0x00, 0x00, UUID.VND16_4),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read_authz,
                              UUID.VND128_1),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0, Prop.read,
                              Perm.read_authn, UUID.VND128_2),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0, Prop.read,
                              Perm.read_enc, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write, UUID.VND16_5),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write, UUID.VND16_3),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_start_server)]

    init_server_2 = [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write_wo_resp | Prop.auth_swrite,
                              Perm.read | Perm.write, UUID.VND128_1),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.nofity | Prop.indicate,
                              Perm.read | Perm.write, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write, UUID.CCC),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write_authz, UUID.VND128_2),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write_authn, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                     TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                              Perm.read | Perm.write_enc, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write,
                              Perm.read | Perm.write_authz, UUID.VND16_3),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                              Perm.read | Perm.write_authn, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                              Perm.read | Perm.write_enc, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, Value.long_1),
                     TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                     TestFunc(btp.gatts_start_server)]

    init_server_3 = [TestFunc(btp.gatts_add_svc, 1, UUID.VND16_1),
                     TestFunc(btp.gatts_add_char, 0, Prop.read,
                              Perm.read, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, '1234'),
                     TestFunc(btp.gatts_add_svc, 0, UUID.VND16_3),
                     TestFunc(btp.gatts_add_inc_svc, 1),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read | Prop.write | Prop.ext_prop,
                              Perm.read | Perm.write, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, '1234'),
                     TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CEP),
                     TestFunc(btp.gatts_set_val, 0, '0100'),
                     TestFunc(btp.gatts_add_char, 0,
                              Prop.read, Perm.read, UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, '1234'),
                     TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CUD),
                     TestFunc(btp.gatts_set_val, 0, '73616d706c652074657874'),
                     TestFunc(btp.gatts_add_desc, 0,
                              Perm.read | Perm.write_authz | Perm.write_authn,
                              UUID.SCC),
                     TestFunc(btp.gatts_set_val, 0, '0000'),
                     TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read,
                              UUID.VND16_2),
                     TestFunc(btp.gatts_set_val, 0, '0000'),
                     TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CPF),
                     TestFunc(btp.gatts_set_val, 0, '0600A327010100'),
                     TestFunc(btp.gatts_start_server),
                     TestFunc(btp.gap_adv_ind_on, start_wid=1)]

    test_cases = [
        ZTestCase("GATT", "GATT/SR/GAC/BV-01-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-01-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-02-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-03-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-04-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-05-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-06-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-01-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-01-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-02-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-03-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-04-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-05-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-03-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-06-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-07-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-08-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-09-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-10-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-11-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-04-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-12-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-13-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-14-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-15-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-16-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-17-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-05-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-18-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-19-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-20-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-21-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BI-22-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-06-C",
                  pre_conditions_1 + init_server_3,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-07-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-08-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-02-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-03-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-02-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-03-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-04-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-05-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-06-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-05-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-07-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-08-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-09-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-11-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-12-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-13-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-06-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-10-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-11-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-07-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-08-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-09-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-32-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BI-33-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAN/BV-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAI/BV-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        # TODO rewrite GATT/SR/GAS/BV-01-C
        ZTestCase("GATT", "GATT/SR/GAS/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),

                   # Service Changed is triggered for bonded devices only
                   TestFunc(btp.gap_wait_for_connection,
                            post_wid=1, skip_call=(2,)),
                   TestFunc(btp.gap_pair, post_wid=1, skip_call=(2,)),

                   TestFunc(btp.gap_wait_for_disconnection, post_wid=96),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1, post_wid=96),
                   TestFunc(btp.gatts_start_server, post_wid=96)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-02-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-03-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl,
                  lt2="GATT/SR/GAS/BV-03-C-LT2"),
        ZTestCaseSlave("GATT", "GATT/SR/GAS/BV-03-C-LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-04-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-05-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-06-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAS/BV-07-C",
                  cmds=pre_conditions_1 +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAT/BV-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-01-C",
                  pre_conditions_1 + init_server_2,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-02-C",
                  pre_conditions_1 + init_server_3,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-03-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-04-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-05-C",
                  pre_conditions_1 + init_server_3,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-06-C",
                  pre_conditions_1 + init_server_3,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-07-C",
                  pre_conditions_1 + init_server_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-08-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        # TODO rewrite GATT/SR/GPA/BV-11-C
        ZTestCase("GATT", "GATT/SR/GPA/BV-11-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '65'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CPF),
                   TestFunc(btp.gatts_set_val, 0, '04000127010100'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CPF),
                   TestFunc(btp.gatts_set_val, 0, '06001027010200'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '651234'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '13001600'),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-12-C",
                  pre_conditions_1 + init_server_3,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/UNS/BI-01-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/UNS/BI-02-C",
                  pre_conditions_1,
                  generic_wid_hdl=gatt_wid_hdl),
    ]

    return test_cases


def test_cases_client(pts):
    """Returns a list of GATT Client test cases

    pts -- Instance of PyPTS

    """

    pts_bd_addr = pts.q_bd_addr
    stack = get_stack()

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "GATT", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    test_cases = [
        ZTestCase("GATT", "GATT/CL/GAC/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gattc_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gattc_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-04-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-05-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAD/BV-06-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-07-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-09-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-10-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-11-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-04-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_val=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={52: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-12-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-13-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-14-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-15-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-16-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-17-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-18-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-19-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-20-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-21-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BI-22-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAR/BV-07-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=58),
                   TestFunc(btp.gattc_read_rsp, store_val=True,
                            start_wid=58),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={52: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-35-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        # PTS issue #15965
        ZTestCase("GATT", "GATT/CL/GAW/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-02-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-03-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-04-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-05-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-06-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BV-05-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-07-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-08-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-09-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-11-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-12-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-13-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BV-08-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BV-09-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-33-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAW/BI-34-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAN/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAI/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/CL/GAS/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        # PTS CASE0036198
        ZTestCase("GATT", "GATT/CL/GAT/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
        # PTS CASE0036198
        ZTestCase("GATT", "GATT/CL/GAT/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gatt_wid_hdl),
    ]

    return test_cases


def test_cases(ptses):
    """Returns a list of GATT test cases"""

    stack = get_stack()

    stack.gap_init()

    test_cases = test_cases_client(ptses[0])
    test_cases += test_cases_server(ptses)

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
            str_cmd = str(cmd)

            if isinstance(cmd, TestFunc):
                if cmd.func == btp.gatts_add_char:
                    str_cmd += ", Properties: %s" % Prop.decode(cmd.args[1])
                    str_cmd += ", Permissions: %s" % Perm.decode(cmd.args[2])
                elif cmd.func == btp.gatts_add_desc:
                    str_cmd += ", Permissions: %s" % Perm.decode(cmd.args[1])

            print "%d) %s" % (index, str_cmd)


if __name__ == "__main__":
    main()
