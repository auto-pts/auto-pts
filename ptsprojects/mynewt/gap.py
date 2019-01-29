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

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.mynewt.ztestcase import ZTestCase

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.mynewt.ztestcase import ZTestCase

from time import sleep
from pybtp import btp
from pybtp.types import Addr, IOCap, AdType, AdFlags, Prop, Perm
import binascii
import gatt
from ptsprojects.stack import get_stack
from gap_wid import gap_wid_hdl, hdl_wid_161


class UUID:
    gap_svc = '1800'
    device_name = '2A00'
    VND16_1 = 'AA50'
    VND16_2 = 'AA51'


class SVC:
    gap = (None, None, UUID.gap_svc)


class CHAR:
    name = (None, None, None, UUID.device_name)


init_gatt_db = [TestFunc(btp.core_reg_svc_gatt),
                TestFunc(btp.gatts_add_svc, 0, gatt.PTS_DB.SVC),
                TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                         gatt.Perm.read | gatt.Perm.read_authn,
                         gatt.PTS_DB.CHR_READ_WRITE_AUTHEN),
                TestFunc(btp.gatts_set_val,
                         gatt.PTS_DB.CHR_READ_WRITE_AUTHEN_ID, '01'),
                TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                         gatt.Perm.read | gatt.Perm.read_enc,
                         gatt.PTS_DB.CHR_READ_WRITE_ENC),
                TestFunc(btp.gatts_set_val,
                         gatt.PTS_DB.CHR_READ_WRITE_ENC_ID, '02'),
                # TestFunc(btp.gatts_add_char, 0,
                #          gatt.Prop.read | gatt.Prop.auth_swrite,
                #          gatt.Perm.read | gatt.Perm.write,
                #          gatt.UUID.VND16_3),
                # TestFunc(btp.gatts_set_val, 0, '03'),
                TestFunc(btp.gatts_start_server)]

iut_device_name = 'Tester'
iut_manufacturer_data = 'ABCD'
iut_ad_uri = '162F'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '11'
iut_svcs = '1111'


class AdData:
    ad_manuf = (AdType.manufacturer_data, 'ABCD')
    ad_name_sh = (AdType.name_short, binascii.hexlify(iut_device_name))
    ad_tx_pwr = (AdType.tx_power, '00')
    ad_uri = (AdType.uri, iut_ad_uri)


# Advertising data
ad = [(AdType.uuid16_some, '1111'),
      (AdType.gap_appearance, '1111'),
      (AdType.name_short, binascii.hexlify('Tester')),
      (AdType.manufacturer_data, '11111111'),
      (AdType.uuid16_svc_data, '111111')]

def set_pixits(pts):
    """Setup GAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    pts -- Instance of PyPTS"""

    ad_str_flags = str(AdType.flags).zfill(2) + \
                   str(AdFlags.br_edr_not_supp).zfill(2)
    ad_str_flags_len = str(len(ad_str_flags) / 2).zfill(2)
    ad_str_name_short = str(AdType.name_short).zfill(2) + \
                        binascii.hexlify(iut_device_name)
    ad_str_name_short_len = str(len(ad_str_name_short) / 2).zfill(2)
    ad_pixit = ad_str_flags_len + ad_str_flags + ad_str_name_short_len + \
               ad_str_name_short

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
    pts.set_pixit("GAP", "TSPX_advertising_data", ad_pixit)
    pts.set_pixit("GAP", "TSPX_iut_device_IRK_for_resolvable_privacy_address_generation_procedure",
                  "00000000000000000000000000000000")
    pts.set_pixit("GAP", "TSPX_tester_device_IRK_for_resolvable_privacy_address_generation_procedure",
                  "0123456789ABCDEF0123456789ABCDEF")
    pts.set_pixit("GAP",
                  "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)
    pts.set_pixit("GAP", "TSPX_Tgap_104", "60000")
    pts.set_pixit("GAP", "TSPX_URI", "162F2F7777772E626C7565746F6F74682E636F6D")


def test_cases(pts):
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs, iut_ad_uri),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_bd_addr_PTS",
            pts_bd_addr.replace(':', ''))),
        TestFunc(pts.update_pixit_param, "GAP",
                 "TSPX_iut_private_address_interval",
                 '30000'),
        TestFunc(lambda: pts.update_pixit_param("GAP", "TSPX_URI", iut_ad_uri)),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_iut_privacy_enabled",
            "TRUE" if stack.gap.iut_has_privacy() else "FALSE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_public_device_address",
            "FALSE" if stack.gap.iut_addr_is_random() else "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "GAP", "TSPX_using_random_device_address",
            "TRUE" if stack.gap.iut_addr_is_random() else "FALSE")),

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    test_cases = [
        ZTestCase("GAP", "GAP/BROB/BCST/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/BCST/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/BCST/BV-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/BCST/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        # TODO: GAP/BROB/BCST/BV-05-C
        ZTestCase("GAP", "GAP/BROB/OBSV/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/OBSV/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/OBSV/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BROB/OBSV/BV-06-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/NONM/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/NONM/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMM/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMM/BV-04-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENM/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENM/BV-04-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMP/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMP/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMP/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMP/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/LIMP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENP/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENP/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENP/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENP/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/GENP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/DISC/RPA/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/IDLE/NAMP/BV-01-C",
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
        ZTestCase("GAP", "GAP/IDLE/NAMP/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCON/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-06-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/SCEP/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/SCEP/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-04-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-05-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-06-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-08-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/TERM/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/PRDA/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/PRDA/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/NBON/BV-01-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/NBON/BV-02-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/NBON/BV-03-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/BON/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/BON/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/BON/BV-03-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/BOND/BON/BV-04-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-11-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-12-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-13-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-14-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-17-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatt),
                   TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, "0001", start_wid=112),
                   TestFunc(btp.gattc_read_rsp, store_val=False,
                            post_wid=112),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=108),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, "0001", start_wid=108),
                   TestFunc(btp.gattc_read_rsp, store_val=False,
                            post_wid=108),
                   TestFunc(btp.gap_disconn, start_wid=44)]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-18-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-19-C",
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, start_wid=78),
                   TestFunc(btp.gap_pair, start_wid=108),
                   TestFunc(btp.gattc_read, Addr.le_public,
                            pts_bd_addr, "0001", start_wid=112),
                   TestFunc(btp.gattc_read_rsp, store_val=False,
                            post_wid=112),
                   TestFunc(btp.gap_disconn, start_wid=44)]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-20-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-21-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-22-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-23-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-24-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/PRIV/CONN/BV-10-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/PRIV/CONN/BV-11-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/PRIV/CONN/BI-01-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-05-C",
                  pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-10-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-11-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/ADV/BV-17-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        # GAP/GAT/BV-01-C
        # wid: 158 description: IUT support both Central and Peripheral roles.
        # Click Yes if IUT act as Central role to execute this test otherwise
        # click No to act as Peripheral role.
        #
        # Testing central role.
        ZTestCase("GAP", "GAP/GAT/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        # Testing peripheral role.
        ZTestCase("GAP", "GAP/GAT/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/GAT/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
    ]

    return test_cases


def main():
    """Main."""
    import ptsprojects.mynewt.iutctl as iutctl

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
            print "%d) %s" % (index, cmd)


if __name__ == "__main__":
    main()
