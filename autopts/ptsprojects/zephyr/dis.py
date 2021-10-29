#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

"""DIS test cases"""

from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr import gatt
from autopts.ptsprojects.zephyr.dis_wid import dis_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase


class Value:
    one_byte = '01'
    two_bytes = '0123'
    eight_bytes_1 = '0123456789ABCDEF'
    eight_bytes_2 = 'FEDCBA9876543210'
    long_1 = eight_bytes_1 * 4
    long_2 = eight_bytes_2 * 4


# these UUIDs are in little endian
class DIS_DB:
    SVC = '0A18'
    CHR_MAN_NAME = '292A'
    CHR_MODEL_NUM = '242A'
    CHR_SER_NUM = '252A'
    CHR_HW_REV = '272A'
    CHR_FW_REV = '262A'
    CHR_SW_REV = '282A'
    CHR_PnP_ID = '502A'


# Vendor ID Source field, a Vendor ID field, a Product ID field and a Product Version field
# BT SIG assigned Device ID - Nordic Semi - dummy Product ID - Dummy Product Version (1.0.0)
# all values in little endian
dis_pnp_char_val = '0100E5FE110011'

iut_manufacturer_data = 'ABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'
iut_attr_db_off = 0x000b


def set_pixits(ptses):
    """Setup DIS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("DIS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("DIS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("DIS", "TSPX_time_guard", "180000")
    pts.set_pixit("DIS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("DIS", "TSPX_tester_database_file",
                  r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PS_DIS.xml")
    pts.set_pixit("DIS", "TSPX_mtu_size", "23")
    pts.set_pixit("DIS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("DIS", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("DIS", "TSPX_pin_code", "0000")
    pts.set_pixit("DIS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("DIS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("DIS", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("MESH", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("DIS", "TSPX_tester_appearance", "0000")


init_server = [TestFunc(btp.core_reg_svc_gatt),
               TestFunc(btp.gatts_add_svc, 0, DIS_DB.SVC),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_MAN_NAME),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_MODEL_NUM),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_SER_NUM),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_HW_REV),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_FW_REV),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_SW_REV),
               TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                        gatt.Perm.read, DIS_DB.CHR_PnP_ID),
               TestFunc(btp.gatts_set_val, 0, dis_pnp_char_val),
               TestFunc(btp.gatts_start_server)]


def test_cases(ptses):
    """Returns a list of DIS Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_delete_link_key", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "DIS", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)),

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
    ]

    test_case_name_list = pts.get_test_case_list('DIS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("DIS", tc_name,
                             cmds=pre_conditions + init_server,
                             generic_wid_hdl=dis_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
