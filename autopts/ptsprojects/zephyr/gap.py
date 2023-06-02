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
from autopts.pybtp.types import Addr, IOCap, AdType, AdFlags, Prop, Perm, UUID, UriScheme
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.ptsprojects.zephyr.gap_wid import gap_wid_hdl
from time import sleep


class SVC:
    gap = (None, None, UUID.gap_svc)


class CHAR:
    name = (None, None, None, UUID.device_name)

init_gatt_db = [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                TestFunc(btp.gatts_add_char, 0, Prop.read,
                         Perm.read | Perm.read_authn,
                         UUID.VND16_2),
                TestFunc(btp.gatts_set_val, 0, '01'),
                TestFunc(btp.gatts_add_char, 0, Prop.read,
                         Perm.read | Perm.read_enc,
                         UUID.VND16_3),
                TestFunc(btp.gatts_set_val, 0, '02'),
                TestFunc(btp.gatts_add_char, 0,
                         Prop.read | Prop.auth_swrite,
                         Perm.read | Perm.write,
                         UUID.VND16_4),
                TestFunc(btp.gatts_set_val, 0, '03'),
                TestFunc(btp.gatts_add_char, 0,
                         Prop.read | Prop.write,
                         Perm.read_authn | Perm.write_authn,
                         UUID.VND16_5),
                TestFunc(btp.gatts_set_val, 0, '04'),
                TestFunc(btp.gatts_start_server)]

init_gatt_db2 = [TestFunc(btp.gatts_add_svc, 0, UUID.VND16_1),
                 TestFunc(btp.gatts_add_char, 0,
                         Prop.read | Prop.auth_swrite,
                         Perm.read | Perm.write_authn,
                         UUID.VND16_4),
                TestFunc(btp.gatts_set_val, 0, '03'),
                TestFunc(btp.gatts_start_server)]

iut_manufacturer_data = 'ABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'
iut_uri = UriScheme.https + 'github.com/auto-pts'.encode()


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
    pts.set_pixit("GAP", "TSPX_use_dynamic_pin", "FALSE")
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
    pts.set_pixit("GAP", "TSPX_iut_private_address_interval", "30000")
    pts.set_pixit("GAP", "TSPX_iut_privacy_enabled", "FALSE")
    pts.set_pixit("GAP", "TSPX_psm", "1001")
    pts.set_pixit("GAP", "TSPX_psm_2", "2001")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_interval_min", "00C8")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_interval_max", "03C0")
    pts.set_pixit("GAP", "TSPX_iut_valid_connection_latency", "0006")
    pts.set_pixit("GAP", "TSPX_iut_valid_timeout_multiplier", "0962")
    pts.set_pixit("GAP", "TSPX_iut_connection_parameter_timeout", "30000")
    pts.set_pixit("GAP", "TSPX_iut_invalid_connection_interval_min", "0008")
    pts.set_pixit("GAP", "TSPX_iut_invalid_connection_interval_max", "00AA")
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
    pts.set_pixit("GAP", "TSPX_conn_update_peripheral_latency", "0001")
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
    pts.set_pixit("GAP", "TSPX_URI", "176769746875622E636F6D2F6175746F2D707473")
    pts.set_pixit("GAP", "TSPX_periodic_advertising_data", "0201040503001801180D095054532D4741502D3036423803190000")
    pts.set_pixit("GAP", "TSPX_Min_Encryption_Key_Size", "07")
    pts.set_pixit("GAP", "TSPX_broadcast_code", "8ED03323D1205E2D58191BF6285C3182")
    pts.set_pixit("GAP", "TSPX_gap_iut_role", "Peripheral")


def test_cases(ptses):
    """Returns a list of GAP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr

    iut_device_name = get_unique_name(pts)
    ad_str_flags = str(AdType.flags).zfill(2) + \
                   str(AdFlags.br_edr_not_supp).zfill(2)
    ad_str_flags_len = str(len(ad_str_flags) // 2).zfill(2)
    ad_str_name = str(AdType.name_full).zfill(2) + \
                        bytes.hex(iut_device_name)
    ad_str_name_len = format((len(ad_str_name) // 2), 'x').zfill(2)
    ad_pixit = ad_str_flags_len + ad_str_flags + ad_str_name_len + ad_str_name

    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs, iut_uri),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_delete_link_key", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_privacy_enabled",
            "TRUE" if stack.gap.iut_has_privacy() else "FALSE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_public_device_address",
            "FALSE" if stack.gap.iut_addr_is_random() else "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_random_device_address",
            "TRUE" if stack.gap.iut_addr_is_random() else "FALSE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_advertising_data", ad_pixit)),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_delete_ltk", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_invalid_connection_interval_min", format(0x0c80, '04x'))),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_invalid_connection_interval_max", format(0x0c80, '04x'))),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_invalid_connection_latency", format(0x0000, '04x'))),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_invalid_conn_update_supervision_timeout", format(0x0c80, '04x'))),

        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_io_cap, IOCap.keyboard_display),

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
        ZTestCase("GAP", "GAP/SEC/CSIGN/BI-04-C",
                  cmds=pre_conditions + init_gatt_db2,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-21-C",
                  cmds=pre_conditions + [TestFunc(sleep, 1, post_wid=108)],
                  generic_wid_hdl=gap_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('GAP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('GAP', tc_name,
                             cmds=pre_conditions + init_gatt_db,
                             generic_wid_hdl=gap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
