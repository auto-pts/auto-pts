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

from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase
from autopts.ptsprojects.mynewt.gatt_wid import gatt_wid_hdl


class Value:
    one_byte = '01'
    two_bytes = '0123'
    eight_bytes_1 = '0123456789ABCDEF'
    eight_bytes_2 = 'FEDCBA9876543210'
    long_1 = eight_bytes_1 * 4
    long_2 = eight_bytes_2 * 4


iut_attr_db_off = 0x000b


def hdl_str(hdl):
    return '{0:x}'.format(hdl)


def u16_hdl_str(hdl):
    return '{0:04x}'.format(hdl)


def u16_hdl_uc_str(hdl):
    return '{0:04x}'.format(hdl)


class PTS_DB:
    PTS_UUID_FMT = '0000{}8c26476f89a7a108033a69c7'
    SVC = PTS_UUID_FMT.format('0001')
    CHR_NO_PERM = PTS_UUID_FMT.format('0002')
    CHR_READ = PTS_UUID_FMT.format('0003')
    CHR_RELIABLE_WRITE = PTS_UUID_FMT.format('0004')
    CHR_WRITE_NO_RSP = PTS_UUID_FMT.format('0005')
    CHR_READ_WRITE = PTS_UUID_FMT.format('0006')
    CHR_READ_WRITE_ENC = PTS_UUID_FMT.format('0007')
    CHR_READ_WRITE_AUTHEN = PTS_UUID_FMT.format('0008')
    CHR_READ_WRITE_AUTHOR = PTS_UUID_FMT.format('0009')
    DSC_READ = PTS_UUID_FMT.format('000a')
    DSC_WRITE = PTS_UUID_FMT.format('000b')
    DSC_READ_WRITE = PTS_UUID_FMT.format('000c')
    DSC_READ_WRITE_ENC = PTS_UUID_FMT.format('000d')
    DSC_READ_WRITE_AUTHEN = PTS_UUID_FMT.format('000e')
    INC_SVC = PTS_UUID_FMT.format('000f')
    CHR_READ_WRITE_ALT = PTS_UUID_FMT.format('0010')

    CHR_NO_PERM_ID = 0
    CHR_READ_ID = 1
    CHR_RELIABLE_WRITE_ID = 2
    CHR_WRITE_NO_RSP_ID = 3
    CHR_READ_WRITE_ID = 4
    CHR_READ_WRITE_ENC_ID = 5
    CHR_READ_WRITE_AUTHEN_ID = 6
    CHR_READ_WRITE_AUTHOR_ID = 7
    DSC_READ_ID = 8
    DSC_WRITE_ID = 9
    DSC_READ_WRITE_ID = 10
    DSC_READ_WRITE_ENC_ID = 11
    DSC_READ_WRITE_AUTHEN_ID = 12
    CHR_READ_WRITE_ALT_ID = 13

    iut_attr_db_off = 26

    SVC_HDL = u16_hdl_str(iut_attr_db_off + 0)
    CHR_NO_PERM_HDL = u16_hdl_str(iut_attr_db_off + 2)
    CHR_READ_HDL = u16_hdl_str(iut_attr_db_off + 4)
    CHR_RELIABLE_WRITE_HDL = u16_hdl_str(iut_attr_db_off + 7)
    CHR_WRITE_NO_RSP_HDL = u16_hdl_str(iut_attr_db_off + 9)
    CHR_READ_WRITE_HDL = hdl_str(iut_attr_db_off + 11)
    CHR_READ_WRITE_ENC_HDL = u16_hdl_str(iut_attr_db_off + 14)
    CHR_READ_WRITE_AUTHEN_HDL = u16_hdl_str(iut_attr_db_off + 16)
    CHR_READ_WRITE_AUTHOR_HDL = u16_hdl_str(iut_attr_db_off + 18)
    DSC_READ_HDL = u16_hdl_str(iut_attr_db_off + 19)
    DSC_WRITE_HDL = u16_hdl_str(iut_attr_db_off + 20)
    DSC_READ_WRITE_HDL = u16_hdl_str(iut_attr_db_off + 21)
    DSC_READ_WRITE_ENC_HDL = u16_hdl_str(iut_attr_db_off + 22)
    DSC_READ_WRITE_AUTHEN_HDL = u16_hdl_str(iut_attr_db_off + 23)
    SVC_END_HDL = u16_hdl_str(iut_attr_db_off + 23)
    INC_SVC_HDL = u16_hdl_str(iut_attr_db_off + 25)
    CHR_READ_WRITE_ALT_HDL = u16_hdl_str(iut_attr_db_off + 27)


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
    pts.set_pixit("GATT", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_use_dynamic_bd_addr", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit(
        "GATT",
        "TSPX_tester_database_file",
        r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\GATT_Qualification_Test_Databases.xml")
    pts.set_pixit("GATT", "TSPX_iut_is_client_periphral", "FALSE")
    pts.set_pixit("GATT", "TSPX_iut_is_server_central", "FALSE")
    pts.set_pixit("GATT", "TSPX_mtu_size", "23")
    pts.set_pixit("GATT", "TSPX_pin_code", "0000")
    pts.set_pixit("GATT", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("GATT", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("GATT", "TSPX_tester_appearance", "0000")


def test_cases_server(pts):
    """Returns a list of GATT Server test cases"""

    stack = get_stack()

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

    pre_conditions_2 = [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.core_reg_svc_gatt),
                        TestFunc(btp.gap_read_ctrl_info),
                        TestFunc(lambda: pts.update_pixit_param(
                            "GATT", "TSPX_bd_addr_iut",
                            stack.gap.iut_addr_get_str())),
                        TestFunc(lambda: pts.update_pixit_param(
                            "GATT", "TSPX_iut_use_dynamic_bd_addr",
                            "TRUE" if stack.gap.iut_addr_is_random()
                            else "FALSE")),
                        TestFunc(btp.gap_set_gendiscov),
                        TestFunc(btp.gap_set_conn)]

    custom_test_cases = [
        ZTestCase("GATT", "GATT/SR/GAS/BV-01-C",
                  edit1_wids={2000: btp.var_store_get_passkey},
                  cmds=pre_conditions_2 +
                  [TestFunc(btp.gap_adv_ind_on, start_wid=1),
                   # Service Changed is triggered for bonded devices only
                   TestFunc(btp.gap_wait_for_connection,
                            start_wid=1),
                   TestFunc(btp.gap_pair, start_wid=1),
                   TestFunc(btp.gap_wait_for_disconnection, post_wid=96),
                   TestFunc(btp.gatts_change_database, 35, 37, 0,
                            post_wid=96)]),
        ZTestCase("GATT", "GATT/SR/UNS/BI-02-C",
                  pre_conditions_2,
                  generic_wid_hdl=gatt_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('GATT')
    tc_list = []

    for tc_name in test_case_name_list:
        if not tc_name.startswith('GATT/SR'):
            continue
        instance = ZTestCase('GATT', tc_name,
                             cmds=pre_conditions_1,
                             generic_wid_hdl=gatt_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list


def test_cases_client(pts):
    """Returns a list of GATT Client test cases

    pts -- Instance of PyPTS

    """

    pts_bd_addr = pts.q_bd_addr
    stack = get_stack()

    pre_conditions_cl = [TestFunc(btp.core_reg_svc_gap),
                         TestFunc(btp.gap_read_ctrl_info),
                         TestFunc(lambda: pts.update_pixit_param(
                             "GATT", "TSPX_bd_addr_iut",
                             stack.gap.iut_addr_get_str())),
                         TestFunc(btp.core_reg_svc_gatt),
                         TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
                         TestFunc(stack.gatt_init),
                         TestFunc(stack.gatt_cl_init)]

    custom_test_cases = [
        # Not supported
        # PTS issue #15965
        # ZTestCase("GATT", "GATT/CL/GAW/BV-02-C",
    ]

    test_case_name_list = pts.get_test_case_list('GATT')
    tc_list = []

    for tc_name in test_case_name_list:
        if not tc_name.startswith('GATT/CL'):
            continue
        instance = ZTestCase("GATT", tc_name,
                             cmds=pre_conditions_cl,
                             generic_wid_hdl=gatt_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list


def test_cases(ptses):
    """Returns a list of GATT test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    stack = get_stack()
    iut_device_name = get_unique_name(pts)

    stack.gap_init(iut_device_name)

    tc_list = test_cases_client(pts)
    tc_list += test_cases_server(pts)

    return tc_list
