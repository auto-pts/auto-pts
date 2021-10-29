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

"""GAP test cases"""

from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap, UUID, Prop, Perm, AdType
from autopts.client import get_unique_name
from autopts.wid.gap import hdl_wid_161
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.bluez.btestcase import BTestCase
from autopts.ptsprojects.bluez.gap_wid import gap_wid_hdl


class SVC:
    gap = (None, None, UUID.gap_svc)


class CHAR:
    name = (None, None, None, UUID.device_name)


init_gatt_db = [TestFunc(btp.core_reg_svc_gatt),
                TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                TestFunc(btp.gatts_add_char, 0, Prop.read,
                         Perm.read | Perm.read_authn,
                         UUID.VND16_2),
                TestFunc(btp.gatts_set_val, 0, '01'),
                TestFunc(btp.gatts_add_char, 0, Prop.read,
                         Perm.read | Perm.read_enc, UUID.VND16_3),
                TestFunc(btp.gatts_set_val, 0, '02'),
                TestFunc(btp.gatts_add_char, 0,
                         Prop.read | Prop.auth_swrite,
                         Perm.read | Perm.write,
                         UUID.VND16_3),
                TestFunc(btp.gatts_set_val, 0, '03'),
                TestFunc(btp.gatts_start_server)]


iut_manufacturer_data = 'FFFFABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'
iut_attr_db_off = 0x000b


def set_pixits(ptses):
    """Setup GAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    # Set GAP common PIXIT values
    pts.set_pixit("GAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("GAP", "TSPX_bd_addr_PTS", "C000DEADBEEF")
    pts.set_pixit("GAP", "TSPX_broadcaster_class_of_device", "100104")
    pts.set_pixit("GAP", "TSPX_observer_class_of_device", "100104")
    pts.set_pixit("GAP", "TSPX_peripheral_class_of_device", "100104")
    pts.set_pixit("GAP", "TSPX_central_class_of_device", "100104")
    pts.set_pixit("GAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("GAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("GAP", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("GAP", "TSPX_mtu_size", "23")
    pts.set_pixit("GAP", "TSPX_delete_ltk", "FALSE")
    pts.set_pixit("GAP", "TSPX_pin_code", "0000")
    pts.set_pixit("GAP", "TSPX_time_guard", "300000")
    pts.set_pixit("GAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("GAP", "TSPX_secure_simple_pairing_pass_key_confirmation",
                  "FALSE")
    pts.set_pixit("GAP", "TSPX_using_public_device_address", "TRUE")
    pts.set_pixit("GAP", "TSPX_using_random_device_address", "FALSE")
    pts.set_pixit("GAP", "TSPX_lim_adv_timeout", "30720")
    pts.set_pixit("GAP", "TSPX_gen_disc_adv_min", "30720")
    pts.set_pixit("GAP", "TSPX_lim_disc_scan_min", "10240")
    pts.set_pixit("GAP", "TSPX_gen_disc_scan_min", "10240")
    pts.set_pixit("GAP", "TSPX_database_file", "Database-GAP.sig")
    pts.set_pixit("GAP", "TSPX_iut_rx_mtu", "23")
    pts.set_pixit("GAP", "TSPX_iut_private_address_interval", "5000")
    pts.set_pixit("GAP", "TSPX_iut_privacy_enabled", "FALSE")
    pts.set_pixit("GAP", "TSPX_psm", "1001")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_interval_min", "00C8")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_interval_max", "03C0")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_latency", "0006")
    pts.set_pixit("GAP", "TSPX_iut_valid_timeout_multiplier", "0962")
    pts.set_pixit("GAP", "TSPX_iut_connection_parameter_timeout", "30000")
    pts.set_pixit("GAP", "TSPX_iut_invalid_connection_interval_min", "0000")
    pts.set_pixit("GAP", "TSPX_iut_invalid_connection_interval_max", "0000")
    pts.set_pixit("GAP", "TSPX_iut_invalid_connection_latency", "0000")
    pts.set_pixit("GAP", "TSPX_iut_invalid_conn_update_supervision_timeout", "0800")
    pts.set_pixit("GAP", "TSPX_LE_scan_interval", "0010")
    pts.set_pixit("GAP", "TSPX_LE_scan_window", "0010")
    pts.set_pixit("GAP", "TSPX_con_interval_min", "0032")
    pts.set_pixit("GAP", "TSPX_con_interval_max", "0046")
    pts.set_pixit("GAP", "TSPX_con_latency", "0001")
    pts.set_pixit("GAP", "TSPX_supervision_timeout", "07D0")
    pts.set_pixit("GAP", "TSPX_minimum_ce_length", "0000")
    pts.set_pixit("GAP", "TSPX_maximum_ce_length", "0000")
    pts.set_pixit("GAP", "TSPX_conn_update_int_min", "0032")
    pts.set_pixit("GAP", "TSPX_conn_update_int_max", "0046")
    pts.set_pixit("GAP", "TSPX_conn_update_slave_latency", "0001")
    pts.set_pixit("GAP", "TSPX_conn_update_supervision_timeout", "01F4")
    pts.set_pixit("GAP", "TSPX_pairing_before_service_request", "FALSE")
    pts.set_pixit("GAP", "TSPX_iut_mandates_mitm", "FALSE")
    pts.set_pixit("GAP", "TSPX_encryption_before_service_request", "FALSE")
    pts.set_pixit("GAP", "TSPX_tester_appearance", "0000")
    pts.set_pixit("GAP", "TSPX_advertising_data", "")
    pts.set_pixit("GAP", "TSPX_iut_device_IRK_for_resolvable_privacy_address_generation_procedure",
                  "00000000000000000000000000000000")
    pts.set_pixit("GAP", "TSPX_tester_device_IRK_for_resolvable_privacy_address_generation_procedure",
                  "0123456789ABCDEF0123456789ABCDEF")
    pts.set_pixit("GAP",
                  "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("GAP", "TSPX_Tgap_104", "60000")
    pts.set_pixit("GAP", "TSPX_URI", "162F2F7777772E626C7565746F6F74682E636F6D")


def test_cases(ptses):
    """Returns a list of GAP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    ad_str_manufacturer_data = str(format(AdType.manufacturer_data, 'x')).zfill(2) + \
                               iut_manufacturer_data
    ad_str_manufacturer_data_len = str(len(ad_str_manufacturer_data) / 2).zfill(2)

    ad_pixit = ad_str_manufacturer_data_len + ad_str_manufacturer_data

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.gap_reset),
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.gap_set_bondable_on),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_privacy_enabled",
            "TRUE" if stack.gap.iut_has_privacy() else "FALSE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_public_device_address",
            "FALSE" if stack.gap.iut_addr_is_random() else "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_private_device_address",
            "TRUE" if stack.gap.iut_addr_is_random() else "FALSE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_advertising_data", ad_pixit)),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_random_device_address",
            "TRUE" if stack.gap.iut_addr_is_random()
            else "FALSE")),

        # We do this on test case, because previous one could
        # update this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
        BTestCase("GAP", "GAP/BROB/BCST/BV-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BROB/OBSV/BV-06-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/IDLE/NAMP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatt),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gattc_read_uuid, Addr.le_public,
                            pts_bd_addr, '0001', 'FFFF', UUID.device_name,
                            start_wid=73),
                   TestFunc(btp.gattc_read_uuid_rsp, post_wid=73),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        BTestCase("GAP", "GAP/CONN/UCON/BV-06-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/NBON/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/NBON/BV-02-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/NBON/BV-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/BON/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/BON/BV-02-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/BON/BV-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/BOND/BON/BV-04-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-11-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-12-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-13-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-14-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-17-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatt),
                   TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, start_wid=78),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, "0001", start_wid=112),
                   # Bonding shall start automatically, so ignore wid: 108
                   # "Please start the Bonding Procedure..."

                   # Await read response after bonding
                   TestFunc(btp.gattc_read_rsp, store_val=False,
                            post_wid=108),
                   TestFunc(btp.gap_disconn, start_wid=44)]),
        BTestCase("GAP", "GAP/SEC/AUT/BV-18-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-19-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, start_wid=78),
                   TestFunc(btp.gap_pair, start_wid=108, skip_call=(2,)),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, "0001", start_wid=112),
                   TestFunc(btp.gattc_read_rsp, store_val=False,
                            post_wid=112),
                   TestFunc(btp.gap_disconn, start_wid=44)]),
        BTestCase("GAP", "GAP/SEC/AUT/BV-20-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        # TODO: Inform about lost bond
        # BTestCase("GAP", "GAP/SEC/AUT/BV-22-C",
        #           cmds=pre_conditions,
        #           generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-23-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/AUT/BV-24-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/CSIGN/BV-01-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/CSIGN/BV-02-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/CSIGN/BI-01-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/CSIGN/BI-02-C",
                  edit1_wids={161: hdl_wid_161},
                  verify_wids={130: lambda x: (
                          btp.gatts_verify_write_success(x) and
                          btp.gatts_verify_write_success(x) and
                          btp.gatts_verify_write_fail(x))},
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gap_set_conn),
                   TestFunc(lambda: btp.gap_adv_ind_on(ad=get_stack().gap.ad,
                                                       sd=get_stack().gap.sd)),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        BTestCase("GAP", "GAP/SEC/CSIGN/BI-03-C",
                  cmds=pre_conditions + init_gatt_db +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/SEC/CSIGN/BI-04-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/PRIV/CONN/BV-10-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        BTestCase("GAP", "GAP/PRIV/CONN/BI-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        # GAP/GAT/BV-01-C
        # wid: 158 description: IUT support both Central and Peripheral roles.
        # Click Yes if IUT act as Central role to execute this test otherwise
        # click No to act as Peripheral role.
        #
        # Testing central role.
        BTestCase("GAP", "GAP/GAT/BV-01-C",
                  cmds=pre_conditions + init_gatt_db,
                  generic_wid_hdl=gap_wid_hdl),
        # Testing peripheral role.
        BTestCase("GAP", "GAP/GAT/BV-01-C",
                  #   no_wid=158,
                  cmds=pre_conditions + init_gatt_db,
                  generic_wid_hdl=gap_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('GAP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = BTestCase('GAP', tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=gap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
