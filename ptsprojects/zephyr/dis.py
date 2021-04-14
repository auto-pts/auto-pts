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
from pybtp.types import Addr, Prop, Perm
from . import gatt
from ptsprojects.stack import get_stack
from ptsprojects.zephyr.dis_wid import dis_wid_hdl


class Value:
    one_byte = '01'
    two_bytes = '0123'
    eight_bytes_1 = '0123456789ABCDEF'
    eight_bytes_2 = 'FEDCBA9876543210'
    long_1 = eight_bytes_1 * 4
    long_2 = eight_bytes_2 * 4


iut_attr_db_off = 0x000b


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


def set_pixits(pts):
    """Setup DIS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    pts -- Instance of PyPTS"""


    pts.set_pixit("DIS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("DIS", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)
    pts.set_pixit("DIS", "TSPX_time_guard", "180000")
    pts.set_pixit("DIS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("DIS", "TSPX_tester_database_file",
                  "C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PS_DIS.xml")
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


iut_device_name = 'Tester'.encode('utf-8')
iut_manufacturer_data = 'ABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'
iut_attr_db_off = 0x000b


def test_cases(ptses):
    """Returns a list of DIS Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
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

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    test_cases = [
        ZTestCase("DIS", "DIS/SR/SD/BV-01-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-01-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-02-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-03-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-04-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-05-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-06-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/DEC/BV-09-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/SD/BV-01-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-01-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-02-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-03-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-04-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-05-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-06-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
        ZTestCase("DIS", "DIS/SR/CR/BV-09-C",
                  pre_conditions + init_server,
                  generic_wid_hdl=dis_wid_hdl),
    ]
    return test_cases


def main():
    """Main."""
    import ptsprojects.zephyr.iutctl as iutctl

    iutctl.init_stub()

    test_cases_ = test_cases("AB:CD:EF:12:34:56")

    for test_case in test_cases_:
        print()
        print(test_case)

        if test_case.edit1_wids:
            print(("edit1_wids: %r" % test_case.edit1_wids))

        if test_case.verify_wids:
            print(("verify_wids: %r" % test_case.verify_wids))

        for index, cmd in enumerate(test_case.cmds):
            str_cmd = str(cmd)

            if isinstance(cmd, TestFunc):
                if cmd.func == btp.gatts_add_char:
                    str_cmd += ", Properties: %s" % Prop.decode(cmd.args[1])
                    str_cmd += ", Permissions: %s" % Perm.decode(cmd.args[2])
                elif cmd.func == btp.gatts_add_desc:
                    str_cmd += ", Permissions: %s" % Perm.decode(cmd.args[1])

            print(("%d) %s" % (index, str_cmd)))


if __name__ == "__main__":
    main()
