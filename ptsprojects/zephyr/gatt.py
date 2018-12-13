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
    from ptsprojects.zephyr.ztestcase import ZTestCase

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


def test_cases_server(pts):
    """Returns a list of GATT Server test cases"""

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
                            else "FALSE"))]

    init_gatt_db = [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                    TestFunc(btp.gatts_add_char, 0,
                             Prop.read | Prop.write | Prop.nofity,
                             Perm.read | Perm.write, UUID.VND16_2),
                    TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1 * 10),
                    TestFunc(btp.gatts_start_server)]

    test_cases = [
        ZTestCase("GATT", "GATT/SR/GAC/BV-01-C",
                  pre_conditions_1 + init_gatt_db,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-01-C",
                  pre_conditions_1 + init_gatt_db,
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAD/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={23: ("UUID= '%s" % UUID.gatt_svc,
                                    "start handle = '0001'",
                                    "end handle = '0004'")}),
        ZTestCase("GATT", "GATT/SR/GAD/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_3),
                   TestFunc(btp.gatts_add_inc_svc, 1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={24: ("Attribute Handle = '%s'" %
                                    __get_attr_u16_hdl_uc_str(5),
                                    "Included Service Attribute handle = '%s'"
                                    % __get_attr_u16_hdl_uc_str(1),
                                    "End Group Handle = '%s'" %
                                    __get_attr_u16_hdl_uc_str(3),
                                    "Service UUID = '%s'" % UUID.VND16_1)}),
        ZTestCase("GATT", "GATT/SR/GAD/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={25: ("UUID= '%s'" % UUID.gatt_svc,
                                    "handle='0002'")}),
        ZTestCase("GATT", "GATT/SR/GAD/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAD/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read | Perm.write,
                            UUID.VND16_3),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, 0x00, 0x00, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-02-C",
                  edit1_wids={118: "ffff"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.broadcast, Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read_authz,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-04-C",
                  edit1_wids={2000: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read_authn, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read_enc, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_set_enc_key_size, 2, 0x0f),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND128_1),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-06-C",
                  edit1_wids={111: UUID.VND16_2,
                              110: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                          TestFunc(btp.gatts_add_char, 0, 0x00, 0x00,
                                   UUID.VND16_2),
                          TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                          TestFunc(btp.gatts_start_server),
                          TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-07-C",
                  edit1_wids={119: UUID.VND16_3},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                          TestFunc(btp.gatts_add_char, 0,
                                   Prop.broadcast | Prop.read,
                                   Perm.read | Perm.write, UUID.VND16_2),
                          TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                          TestFunc(btp.gatts_start_server),
                          TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-08-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-09-C",
                  edit1_wids={113: UUID.VND16_2,
                              112: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read_authz, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-10-C",
                  edit1_wids={115: UUID.VND16_2,
                              114: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read_authn, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-11-C",
                  edit1_wids={121: __get_attr_u16_hdl_str(3),
                              122: UUID.VND16_2},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                          TestFunc(btp.gatts_add_char, 0, Prop.read,
                                   Perm.read_enc, UUID.VND16_2),
                          TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                          TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                          TestFunc(btp.gatts_start_server),
                          TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={52: ("Please confirm IUT Handle='%s'" %
                                    __get_attr_hdl_str(3),
                                    "value='" + Value.long_1 + "'")}),
        ZTestCase("GATT", "GATT/SR/GAR/BI-12-C",
                  edit1_wids={110: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                          TestFunc(btp.gatts_add_char, 0, 0x00, 0x00,
                                   UUID.VND16_2),
                          TestFunc(btp.gatts_set_val, 0, Value.long_1),
                          TestFunc(btp.gatts_start_server),
                          TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-13-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-14-C",
                  edit1_wids={118: "ffff"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write | Prop.nofity,
                               Perm.read | Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.long_1),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-15-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read_authz,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-16-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read_authn,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-17-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read_enc, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={56: ("Please confirm IUT Handle pair",
                                    "0007", "0005",
                                    "value='00001800280000002A00'")}),
        ZTestCase("GATT", "GATT/SR/GAR/BI-18-C",
                  edit1_wids={110: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.write, Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write | Prop.nofity,
                               Perm.read | Perm.write, UUID.VND16_3),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-19-C",
                  edit1_wids={118: "ffff"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.write, Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read, Perm.read, UUID.VND16_3),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write | Prop.nofity,
                               Perm.read | Perm.write, UUID.VND16_4),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write | Prop.nofity,
                               Perm.read | Perm.write, UUID.VND16_5),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-20-C",
                  edit1_wids={123: "0003", 124: "0005"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read, Perm.read, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read, Perm.read_authz, UUID.VND16_3),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write,
                               Perm.read | Perm.write, UUID.VND16_4),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-21-C",
                  edit1_wids={123: "0003", 124: "0005"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read, Perm.read_authn, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read, Perm.read, UUID.VND16_3),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.read | Prop.write,
                               Perm.read | Perm.write, UUID.VND16_4),
                      TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BI-22-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.appearance),
                   TestFunc(btp.gatts_set_val, 0, '0512'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read_enc, UUID.gender),
                   TestFunc(btp.gatts_set_val, 0, '01'),
                   TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.date_of_birth),
                   TestFunc(btp.gatts_set_val, 0, '20151124'),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.battery_level),
                   TestFunc(btp.gatts_set_val, 0, '10'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAR/BV-06-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_2),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-07-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAR/BV-08-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GAW/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read | Prop.write_wo_resp,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={75: ("Please confirm IUT Write characteristic "
                                    "handle= '%s'O value= 'BE'O" %
                                    __get_attr_u16_hdl_uc_str(3),)}),
        ZTestCase("GATT", "GATT/SR/GAW/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.auth_swrite,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.auth_swrite,
                            Perm.read | Perm.write_authn, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.eight_bytes_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-02-C",
                  edit1_wids={118: "ffff"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.broadcast | Prop.read | Prop.write_wo_resp,
                               Perm.read | Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read, Perm.read,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-04-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_authz, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_authn, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-06-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_enc, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-07-C",
                  edit1_wids={118: "ffff"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.broadcast | Prop.read | Prop.write_wo_resp,
                               Perm.read | Perm.write, UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.long_1),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-08-C",
                  edit1_wids={120: "0002"},
                  cmds=pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                      TestFunc(btp.gatts_add_char, 0,
                               Prop.broadcast | Prop.read, Perm.read,
                               UUID.VND16_2),
                      TestFunc(btp.gatts_set_val, 0, Value.long_1),
                      TestFunc(btp.gatts_start_server),
                      TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-09-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-11-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_authz, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-12-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_authn, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-13-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write_enc, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_set_enc_key_size, 0, 0x0f),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-10-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.device_name),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.appearance),
                   TestFunc(btp.gatts_set_val, 0, Value.long_2),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.broadcast | Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.device_name),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, Value.two_bytes),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write, UUID.VND16_3),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-32-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.one_byte),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAW/BI-33-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, Value.long_1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GAN/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.nofity | Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '00'),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write, UUID.CCC),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1),
                   TestFunc(sleep, 1, start_wid=92),
                   TestFunc(btp.gatts_set_val, iut_attr_db_off + 3, '01',
                            start_wid=92)]),
        ZTestCase("GATT", "GATT/SR/GAI/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.indicate | Prop.read, Perm.read,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '00'),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write, UUID.CCC),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1),
                   TestFunc(sleep, 1, start_wid=98),
                   TestFunc(btp.gatts_set_val, iut_attr_db_off + 3, '01',
                            start_wid=98)]),
        ZTestCase("GATT", "GATT/SR/GAS/BV-01-C",
                  edit1_wids={2000: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1),

                   # Service Changed is triggered for bonded devices only
                   TestFunc(btp.gap_wait_for_connection,
                            start_wid=1, skip_call=(2,)),
                   TestFunc(btp.gap_pair, start_wid=1, skip_call=(2,)),

                   TestFunc(btp.gap_wait_for_disconnection, post_wid=96),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1, post_wid=96),
                   TestFunc(btp.gatts_start_server, post_wid=96)]),
        ZTestCase("GATT", "GATT/SR/GAT/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.indicate | Prop.read, Perm.read,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '00'),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write, UUID.CCC),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1),
                   TestFunc(sleep, 1, start_wid=98),
                   TestFunc(btp.gatts_set_val, iut_attr_db_off + 3, '01',
                            start_wid=98)]),
        ZTestCase("GATT", "GATT/SR/GPA/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={102: ("Attribute Handle = '0001'",
                                     "Primary Service = '%s'" %
                                     UUID.VND16_1)}),
        ZTestCase("GATT", "GATT/SR/GPA/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 1, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_3),
                   TestFunc(btp.gatts_add_inc_svc, 1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={102: ("Attribute Handle = '%s'" %
                                     __get_attr_u16_hdl_str(1),
                                     "Secondary Service = '%s'" %
                                     UUID.VND16_1)}),
        ZTestCase("GATT", "GATT/SR/GPA/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_svc, 0, UUID.VND16_3),
                   TestFunc(btp.gatts_add_inc_svc, 1),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={102: ("Attribute Handle = '%s'" %
                                     __get_attr_u16_hdl_uc_str(5),
                                     "Included Service Attribute handle = '%s'"
                                     % __get_attr_u16_hdl_uc_str(1),
                                     "End Group Handle = '%s" %
                                     __get_attr_u16_hdl_str(3),
                                     "Service UUID = '%s'" % UUID.VND16_1)}),
        ZTestCase("GATT", "GATT/SR/GPA/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={102: verify_gatt_sr_gpa_bv_04_c}),
        ZTestCase("GATT", "GATT/SR/GPA/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.ext_prop,
                            Perm.read | Perm.write, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CEP),
                   TestFunc(btp.gatts_set_val, 0, '0100'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={52: ("Handle='%s'" % __get_attr_hdl_str(4),
                                    "value='0001'")}),
        ZTestCase("GATT", "GATT/SR/GPA/BV-06-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read, Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CUD),
                   TestFunc(btp.gatts_set_val, 0, '73616d706c652074657874'),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-07-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0,
                            Prop.read | Prop.write | Prop.nofity,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read | Perm.write,
                            UUID.CCC),
                   TestFunc(btp.gatts_set_val, 0, '0000'),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        ZTestCase("GATT", "GATT/SR/GPA/BV-08-C",
                  pre_conditions_1 +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.broadcast | Prop.read,
                            Perm.read, UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_add_desc, 0,
                            Perm.read | Perm.write_authz | Perm.write_authn,
                            UUID.SCC),
                   TestFunc(btp.gatts_set_val, 0, '0000'),
                   TestFunc(btp.gatts_start_server)],
                  generic_wid_hdl=gatt_wid_hdl),
        # PTS crashes in GUI mode with message:
        # "An internal error occurred. Please restart the PTS.
        # Code: 0xE0434352"
        # In auto mode PTS crashes, hence the status of test case is Started
        # PTS issue #14437, #14275, TSE #7063
        ZTestCase("GATT", "GATT/SR/GPA/BV-11-C",
                  pre_conditions +
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
                            Perm.read, UUID.VND16_4),
                   TestFunc(btp.gatts_set_val, 0, '01020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CPF),
                   TestFunc(btp.gatts_set_val, 0, '08001727010300'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '65123401020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '0d0010001300'),

                   # Workaround: PTS requires 5 Aggregate Descriptors
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '65123401020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '0d0010001300'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '65123401020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '0d0010001300'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '65123401020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '0d0010001300'),
                   TestFunc(btp.gatts_add_char, 0, Prop.read | Prop.write,
                            Perm.read, UUID.VND16_5),
                   TestFunc(btp.gatts_set_val, 0, '65123401020304'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CAF),
                   TestFunc(btp.gatts_set_val, 0, '0d0010001300'),

                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)]),
        ZTestCase("GATT", "GATT/SR/GPA/BV-12-C",
                  pre_conditions +
                  [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                   TestFunc(btp.gatts_add_char, 0, Prop.read, Perm.read,
                            UUID.VND16_2),
                   TestFunc(btp.gatts_set_val, 0, '0000'),
                   TestFunc(btp.gatts_add_desc, 0, Perm.read, UUID.CPF),
                   TestFunc(btp.gatts_set_val, 0, '0600A327010100'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_adv_ind_on, start_wid=1)],
                  verify_wids={104: ("Value = '0000'",
                                     "Attribute Handle = '%s'" %
                                     __get_attr_u16_hdl_str(4),
                                     "Format = '06'",
                                     "Exponent = 0",
                                     "Uint = '27A3'",
                                     "Namespace = '01'",
                                     "Description = '0001'")}),
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
                      TestFunc(btp.core_reg_svc_gatt)]

    test_cases = [
        ZTestCase("GATT", "GATT/CL/GAC/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_exchange_mtu,
                            Addr.le_public, pts_bd_addr,
                            start_wid=12),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=69),
                   TestFunc(btp.gattc_write_long_rsp, start_wid=69),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAD/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_disc_prim_uuid,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, start_wid=18),
                   TestFunc(btp.gattc_disc_prim_uuid_rsp, True, start_wid=18),
                   TestFunc(btp.gattc_disc_prim_uuid,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, start_wid=20),
                   TestFunc(btp.gattc_disc_prim_uuid_rsp, True, start_wid=20),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={19: btp.verify_description,
                               21: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAD/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   # NOTE: We cannot discover all services at first, so we look
                   # for included at once
                   TestFunc(btp.gattc_find_included,
                            Addr.le_public, pts_bd_addr, '0001',
                            'FFFF', start_wid=15),
                   TestFunc(btp.gattc_find_included_rsp, True, start_wid=15),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={24: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAD/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_disc_all_chrc,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_2, MMI.arg_3, start_wid=27),
                   TestFunc(btp.gattc_disc_all_chrc_rsp, True, start_wid=27),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={28: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAD/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_disc_chrc_uuid,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, MMI.arg_3, start_wid=29),
                   TestFunc(btp.gattc_disc_chrc_uuid_rsp, True, start_wid=29),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={30: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAD/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_disc_all_desc,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=31),
                   TestFunc(btp.gattc_disc_all_desc_rsp, True, start_wid=31),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={32: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_val=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={50: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-02-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={41: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={42: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-04-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp,
                            store_rsp=True, start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={43: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-05-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={44: btp.verify_description}),
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
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={41: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-13-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_long,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, 1, start_wid=53),
                   TestFunc(btp.gattc_read_long_rsp, store_rsp=True,
                            start_wid=53),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={46: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-14-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-15-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={42: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-16-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={43: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-17-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={44: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BV-05-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp,
                            store_val=True, start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={55: btp.verify_multiple_read_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-18-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp, store_rsp=True,
                            start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={41: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-19-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp, store_rsp=True,
                            start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-20-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp, store_rsp=True,
                            start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={42: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-21-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp, store_rsp=True,
                            start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={43: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BI-22-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read_multiple,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, MMI.arg_2, start_wid=57),
                   TestFunc(btp.gattc_read_multiple_rsp,
                            store_rsp=True, start_wid=57),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={44: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAR/BV-06-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=58),
                   TestFunc(btp.gattc_read_rsp, store_val=True,
                            start_wid=58),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={59: btp.verify_description}),
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
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, store_rsp=True,
                            start_wid=48),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={47: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_without_rsp,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, '12', MMI.arg_2, start_wid=70),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        # PTS issue #15965
        ZTestCase("GATT", "GATT/CL/GAW/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_signed_write,
                            Addr.le_public, pts_bd_addr,
                            MMI.arg_1, '12', None, start_wid=72),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAW/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAW/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={61: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={62: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={63: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={64: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={65: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAW/BI-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12' * 23, MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={61: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={62: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-09-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, MMI.arg_2, '12', None,
                            start_wid=77),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=77),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={66: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-11-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={63: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-12-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={64: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-13-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={65: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, start_wid=74),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAW/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '12', MMI.arg_2,
                            start_wid=76),
                   TestFunc(btp.gattc_write_long_rsp, start_wid=76),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAW/BI-33-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '1234', MMI.arg_2,
                            start_wid=80),
                   TestFunc(btp.gattc_write_rsp, True, start_wid=80),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={67: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAW/BI-34-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write_long, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, 0, '1234', MMI.arg_2,
                            start_wid=81),
                   TestFunc(btp.gattc_write_long_rsp, True, start_wid=81),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)],
                  verify_wids={67: btp.verify_description}),
        ZTestCase("GATT", "GATT/CL/GAN/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_cfg_notify, Addr.le_public,
                            pts_bd_addr, 1, MMI.arg_1, start_wid=91),
                   TestFunc(btp.gattc_notification_ev, pts_bd_addr,
                            Addr.le_public, 1, start_wid=91),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAI/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                          TestFunc(btp.gattc_cfg_indicate, Addr.le_public,
                                   pts_bd_addr, 1, MMI.arg_1, start_wid=99),
                          TestFunc(btp.gattc_notification_ev, pts_bd_addr,
                                   Addr.le_public, 2, start_wid=99),
                          TestFunc(btp.gap_disconn, pts_bd_addr,
                                   Addr.le_public, start_wid=3)]),
        ZTestCase("GATT", "GATT/CL/GAS/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        # PTS CASE0036198
        ZTestCase("GATT", "GATT/CL/GAT/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, start_wid=48),
                   TestFunc(btp.gattc_read_rsp, False, False, 40,
                            start_wid=49),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
        # PTS CASE0036198
        ZTestCase("GATT", "GATT/CL/GAT/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=2),
                   TestFunc(btp.gattc_write, Addr.le_public,
                            pts_bd_addr, MMI.arg_1, '12', MMI.arg_2,
                            start_wid=74),
                   TestFunc(btp.gattc_write_rsp, False, 40, start_wid=71),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=3)]),
    ]

    return test_cases


def test_cases(pts):
    """Returns a list of GATT test cases"""

    stack = get_stack()

    stack.gap_init()

    pts.update_pixit_param("GATT", "TSPX_delete_link_key", "TRUE")
    pts.update_pixit_param("GATT", "TSPX_delete_ltk", "TRUE")

    test_cases = test_cases_client(pts)
    test_cases += test_cases_server(pts)

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
