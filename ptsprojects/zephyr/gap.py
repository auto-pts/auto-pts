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
    from ptsprojects.zephyr.ztestcase import ZTestCase

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase

from time import sleep
from pybtp import btp
from pybtp.types import Addr, IOCap, AdType, AdFlags, Prop, Perm
import binascii
import gatt
from ptsprojects.stack import get_stack
from gap_wid import gap_wid_hdl, hdl_wid_161


class UUID:
    gap_svc = '1800'
    device_name = '2a00'
    VND16_1 = 'AA50'
    VND16_2 = 'AA51'


class SVC:
    gap = (None, None, UUID.gap_svc)


class CHAR:
    name = (None, None, None, UUID.device_name)


init_gatt_db=[TestFunc(btp.core_reg_svc_gatt),
              TestFunc(btp.gatts_add_svc, 0, gatt.UUID.VND16_1),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_authn,
                       gatt.UUID.VND16_2),
              TestFunc(btp.gatts_set_val, 0, '01'),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_enc, gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 0, '02'),
              TestFunc(btp.gatts_add_char, 0,
                       gatt.Prop.read | gatt.Prop.auth_swrite,
                       gatt.Perm.read | gatt.Perm.write,
                       gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 0, '03'),
              TestFunc(btp.gatts_start_server)]

iut_device_name = 'Tester'
iut_manufacturer_data = 'ABCD'
iut_attr_db_off = 0x000b


class AdData:
    ad_manuf = (AdType.manufacturer_data, 'ABCD')
    ad_name_sh = (AdType.name_short, binascii.hexlify(iut_device_name))

# Advertising data
ad = [(AdType.uuid16_some, '1111'),
      (AdType.gap_appearance, '1111'),
      (AdType.name_short, binascii.hexlify('Tester')),
      (AdType.manufacturer_data, '11111111'),
      (AdType.uuid16_svc_data, '111111')]


def __get_attr_u16_hdl_str(offset):
    return '{0:04x}'.format(iut_attr_db_off + offset, 'x')


def test_cases(pts):
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    ad_str_flags = str(AdType.flags).zfill(2) + \
                   str(AdFlags.br_edr_not_supp).zfill(2)
    ad_str_flags_len = str(len(ad_str_flags)/2).zfill(2)
    ad_str_name_short = str(AdType.name_short).zfill(2) + \
                        binascii.hexlify(iut_device_name)
    ad_str_name_short_len = str(len(ad_str_name_short)/2).zfill(2)
    ad_pixit = ad_str_flags_len + ad_str_flags + ad_str_name_short_len + \
               ad_str_name_short

    # Set GAP common PIXIT values
    pts.update_pixit_param("GAP", "TSPX_delete_link_key", "TRUE")
    pts.update_pixit_param("GAP", "TSPX_advertising_data", ad_pixit)

    pre_conditions=[TestFunc(btp.core_reg_svc_gap),
                    TestFunc(stack.gap_init, iut_device_name,
                             iut_manufacturer_data),
                    TestFunc(btp.gap_read_ctrl_info),
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
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(pts.update_pixit_param, "GAP",
                                 "TSPX_iut_device_name_in_adv_packet_for_random_address",
                                 iut_device_name)],
                  generic_wid_hdl=gap_wid_hdl),
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
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        # Set RPA update to 1 minute (60*1000=60000 ms)
                        TestFunc(pts.update_pixit_param, "GAP",
                                 "TSPX_iut_private_address_interval", '60000'),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78),
                        TestFunc(btp.gap_pair, start_wid=108),
                        TestFunc(btp.gap_start_discov, type='passive',
                                 mode='observe', start_wid=204),
                        TestFunc(sleep, 10, start_wid=204),
                        TestFunc(btp.gap_stop_discov, start_wid=204),
                        TestFunc(btp.check_discov_results,discovered=True,
                                 start_wid=204),
                        ],
                  ),
        ZTestCase("GAP", "GAP/DISC/NONM/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=5),
                   TestFunc(btp.gap_set_nondiscov, start_wid=5),
                   TestFunc(btp.gap_adv_ind_on, start_wid=5)]),
        ZTestCase("GAP", "GAP/DISC/NONM/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nondiscov, start_wid=72),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=72)]),
        ZTestCase("GAP", "GAP/DISC/LIMM/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_set_limdiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=59)]),
        ZTestCase("GAP", "GAP/DISC/LIMM/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_limdiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=50)]),
        ZTestCase("GAP", "GAP/DISC/GENM/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=51)]),
        ZTestCase("GAP", "GAP/DISC/GENM/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=52)]),
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
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        # Set RPA update to 1 minute (60*1000=60000 ms)
                        TestFunc(pts.update_pixit_param, "GAP",
                                 "TSPX_iut_private_address_interval", '60000'),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78),
                        TestFunc(btp.gap_pair, start_wid=108),
                        TestFunc(btp.gap_start_discov, type='passive',
                                 mode='observe', start_wid=204),
                        TestFunc(sleep, 10, start_wid=204),
                        TestFunc(btp.gap_stop_discov, start_wid=204),
                        TestFunc(btp.check_discov_results,discovered=True,
                                 start_wid=204)]),
        ZTestCase("GAP", "GAP/IDLE/NAMP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatt),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gattc_disc_prim_uuid, Addr.le_public,
                            pts_bd_addr, UUID.gap_svc, start_wid=73),
                   TestFunc(btp.gattc_disc_prim_uuid_find_attrs_rsp,
                            (SVC.gap,), store_attrs=True, start_wid=73),
                   TestFunc(btp.gattc_disc_all_chrc, Addr.le_public,
                            pts_bd_addr, None, None, (SVC.gap, 1),
                            start_wid=73),
                   TestFunc(btp.gattc_disc_all_chrc_find_attrs_rsp,
                            (CHAR.name,), store_attrs=True, start_wid=73),
                   TestFunc(btp.gattc_read_char_val, Addr.le_public,
                            pts_bd_addr, (CHAR.name, 1), start_wid=73),
                   TestFunc(btp.gattc_read_rsp, start_wid=73),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/IDLE/NAMP/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatt),
                   TestFunc(btp.gatts_add_svc, 0, UUID.gap_svc),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read | Perm.write, UUID.device_name),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78)]),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=122),
                   TestFunc(btp.gap_set_gendiscov, start_wid=122),
                   TestFunc(btp.gap_adv_ind_on, start_wid=54)]),
        ZTestCase("GAP", "GAP/CONN/NCON/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=121),
                   TestFunc(btp.gap_set_limdiscov, start_wid=121),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=55)]),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nondiscov, start_wid=74),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=74)]),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_gendiscov, start_wid=75),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=75)]),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_limdiscov, start_wid=76),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=76)]),
        ZTestCase("GAP", "GAP/CONN/UCON/BV-06-C",
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_set_gendiscov, start_wid=91),
                        TestFunc(btp.gap_adv_ind_on, start_wid=91),
                        TestFunc(btp.gap_wait_for_connection, start_wid=91),
                        TestFunc(btp.gap_disconn, start_wid=77),

                        # Apparently PTS don't take into account value of
                        # TSPX_iut_private_address_interval, so let's simulate
                        # change of RPA
                        TestFunc(btp.gap_adv_off, start_wid=90),
                        TestFunc(btp.gap_read_ctrl_info, start_wid=90),
                        TestFunc(btp.gap_set_gendiscov, start_wid=90),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                 start_wid=90)]),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-03-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/ACEP/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, start_wid=78),
                   TestFunc(btp.gap_disconn, start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/GCEP/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, start_wid=78),
                   TestFunc(btp.gap_disconn, start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/DCEP/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=21)]),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh])]),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh])]),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/CPUP/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=21),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                            start_wid=21)]),
        ZTestCase("GAP", "GAP/CONN/TERM/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/PRDA/BV-01-C",
                  edit1_wids={1002: (btp.var_store_get_passkey)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_set_gendiscov, start_wid=91),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                 start_wid=91),
                        TestFunc(btp.gap_identity_resolved_ev, post_wid=1002),
                        TestFunc(btp.gap_disconn, start_wid=77)]),
        ZTestCase("GAP", "GAP/CONN/PRDA/BV-02-C",
                  edit1_wids={1002: (btp.var_store_get_passkey)},
                  ok_cancel_wids={174: (btp.gap_rpa_conn)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_pair, start_wid=108),
                        TestFunc(btp.gap_identity_resolved_ev, post_wid=1002),
                        TestFunc(btp.gap_conn, start_wid=142)]),
        ZTestCase("GAP", "GAP/BOND/NBON/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78)]),
        ZTestCase("GAP", "GAP/BOND/NBON/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100)]),
         ZTestCase("GAP", "GAP/BOND/NBON/BV-03-C",
                   pre_conditions +
                   [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                    TestFunc(btp.gap_set_conn, start_wid=91),
                    TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                             start_wid=91),]),
         ZTestCase("GAP", "GAP/BOND/BON/BV-01-C",
                   edit1_wids={1002: btp.var_store_get_passkey},
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                  start_wid=91),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108)]),
         ZTestCase("GAP", "GAP/BOND/BON/BV-02-C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108)]),
         ZTestCase("GAP", "GAP/BOND/BON/BV-03-C",
                   edit1_wids={1002: btp.var_store_get_passkey},
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                  start_wid=91)]),
         ZTestCase("GAP", "GAP/BOND/BON/BV-04-C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108),
                         TestFunc(btp.gap_disconn, pts_bd_addr,
                                  Addr.le_public, start_wid=77)]),
         ZTestCase("GAP", "GAP/SEC/AUT/BV-11-C",
                   edit1_wids={139: __get_attr_u16_hdl_str(3),
                               1002: btp.var_store_get_passkey},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn, start_wid=91),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                  start_wid=91)]),
         ZTestCase("GAP", "GAP/SEC/AUT/BV-12-C",
                   edit1_wids={139: __get_attr_u16_hdl_str(3),
                               1002: btp.var_store_get_passkey},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_conn, start_wid=78)]),
         ZTestCase("GAP", "GAP/SEC/AUT/BV-13-C",
                   edit1_wids={139: __get_attr_u16_hdl_str(3),
                               1002: btp.var_store_get_passkey},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78)]),
         ZTestCase("GAP", "GAP/SEC/AUT/BV-14-C",
                   edit1_wids={139: __get_attr_u16_hdl_str(3),
                               1002: btp.var_store_get_passkey},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_set_conn, start_wid=91),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                  start_wid=91),
                         TestFunc(btp.gap_set_io_cap, IOCap.display_only,
                                  start_wid=139)]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-17-C",
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
         ZTestCase("GAP", "GAP/SEC/AUT/BV-18-C",
                   cmds=pre_conditions +
                        [TestFunc(btp.core_reg_svc_gatt),
                         TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh]),
                         TestFunc(btp.gattc_read, Addr.le_public,
                                  pts_bd_addr, "0001", start_wid=112),
                         TestFunc(btp.gattc_read_rsp, store_val=False,
                                  start_wid=112),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108)]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-19-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, start_wid=78),
                        TestFunc(btp.gap_pair, start_wid=108, skip_call=(2,)),
                        TestFunc(btp.gattc_read, Addr.le_public,
                                 pts_bd_addr, "0001", start_wid=112),
                        TestFunc(btp.gattc_read_rsp, store_val=False,
                                 post_wid=112),
                        TestFunc(btp.gap_disconn, start_wid=44)]),
         ZTestCase("GAP", "GAP/SEC/AUT/BV-20-C",
                   edit1_wids={1002: btp.var_store_get_passkey},
                   cmds=pre_conditions +
                        [TestFunc(btp.core_reg_svc_gatt),
                         TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn, start_wid=91),
                         TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                  start_wid=91),
                         # This sleep is workaround, because apparently PTS is
                         # asking for service request before it receives
                         # HCI encryption change event.
                         TestFunc(sleep, 2, start_wid=112),
                         TestFunc(btp.gattc_read, Addr.le_public,
                                  pts_bd_addr, "0001", start_wid=112),
                         TestFunc(btp.gattc_read_rsp, store_val=False,
                                  start_wid=112)]),
        # TODO: Inform about lost bond
        ZTestCase("GAP", "GAP/SEC/AUT/BV-21-C",
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_gatt),
                        TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, start_wid=78),
                        TestFunc(btp.gap_pair, start_wid=108),
                        TestFunc(btp.gap_disconn, start_wid=44)]),
        # TODO: Inform about lost bond
        ZTestCase("GAP", "GAP/SEC/AUT/BV-22-C",
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_gatt),
                        TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_set_conn, start_wid=91),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                 start_wid=91),
                        TestFunc(btp.gattc_read, Addr.le_public,
                                 pts_bd_addr, "0001", start_wid=112),
                        TestFunc(btp.gattc_read_rsp, store_val=False,
                                 start_wid=112),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=108)]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-23-C",
                  edit1_wids={1002: btp.var_store_get_passkey,
                              144: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh])]),
        ZTestCase("GAP", "GAP/SEC/AUT/BV-24-C",
                  edit1_wids={1002: btp.var_store_get_passkey,
                              144: __get_attr_u16_hdl_str(3)},
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, start_wid=78),
                        TestFunc(btp.gap_disconn, start_wid=44)]),
         ZTestCase("GAP", "GAP/SEC/CSIGN/BV-01-C",
                   pre_conditions +
                   [TestFunc(btp.core_reg_svc_gatt),
                    TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                    TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                             start_wid=78),
                    TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                             start_wid=108),
                    TestFunc(btp.gattc_signed_write, Addr.le_public,
                             pts_bd_addr, "0001", "01", start_wid=125),
                    TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                             start_wid=77)]),
        ZTestCase("GAP", "GAP/SEC/CSIGN/BV-02-C",
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/CSIGN/BI-01-C",
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        ZTestCase("GAP", "GAP/SEC/CSIGN/BI-02-C",
                  edit1_wids={161: hdl_wid_161},
                  verify_wids={130: lambda x: (btp.gatts_verify_write_success(x) and
                                               btp.gatts_verify_write_success(x) and
                                               btp.gatts_verify_write_fail(x))},
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh]),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77)]),
        ZTestCase("GAP", "GAP/SEC/CSIGN/BI-03-C",
                  edit1_wids={161: hdl_wid_161},
                  verify_wids={130: btp.gatts_verify_write_fail},
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_gendiscov, start_wid=91),
                        TestFunc(btp.gap_set_conn, start_wid=91),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                 start_wid=91),
                        TestFunc(btp.gap_wait_for_connection, post_wid=91),
                        TestFunc(btp.gap_adv_off, post_wid=91),
                        TestFunc(btp.gap_disconn, start_wid=77),
                        TestFunc(btp.gap_unpair, start_wid=135)]),
        ZTestCase("GAP", "GAP/SEC/CSIGN/BI-04-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output)],
                  generic_wid_hdl=gap_wid_hdl),
        # ZTestCase("GAP", "GAP/PRIV/CONN/BV-10-C",
        #           edit1_wids={1002: (btp.var_store_get_passkey, pts_bd_addr,
        #                              Addr.le_public)},
        #           cmds=pre_conditions +
        #                [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
        #                 TestFunc(pts.update_pixit_param, "GAP",
        #                          "TSPX_iut_device_name_in_adv_packet_for_random_address",
        #                          iut_device_name),
        #
        #                 # Set RPA update to 15 minutes (15*60*1000=900000 ms)
        #                 TestFunc(pts.update_pixit_param, "GAP",
        #                          "TSPX_iut_private_address_interval", '900000'),
        #                 TestFunc(btp.gap_set_conn),
        #                 TestFunc(btp.gap_set_gendiscov),
        #                 TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh]),
        #                 # Don't disable advertising here
        #                 TestFunc(btp.gap_disconn, start_wid=77)]),
            # Workaround BZ-197 and PTS issue #15170
            ZTestCase("GAP", "GAP/PRIV/CONN/BV-10-C",
                      edit1_wids={1002: btp.var_store_get_passkey},
                      cmds=pre_conditions +
                           [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                            TestFunc(pts.update_pixit_param, "GAP",
                                     "TSPX_iut_device_name_in_adv_packet_for_random_address",
                                     iut_device_name),

                            # Simulate RPA update every 10 seconds (10*1000=10000 ms)
                            TestFunc(pts.update_pixit_param, "GAP",
                                     "TSPX_iut_private_address_interval",
                                     '10000'),
                            TestFunc(btp.gap_set_conn),
                            TestFunc(btp.gap_set_gendiscov),

                            # This step is used to speed up test execution, so
                            # that RPA is updated every 10 seconds. This shall
                            # be skipped on first wid: 91 requesting to send
                            # advertising report. Here, we are disabling
                            # previously started advertising, to generate new
                            # RPA to be used when advertising is started again.
                            TestFunc(btp.gap_adv_off, start_wid=91,
                                     skip_call=(1,)),
                            TestFunc(sleep, 10, start_wid=91, skip_call=(1,)),
                            TestFunc(btp.gap_read_ctrl_info, start_wid=91,
                                     skip_call=(1,)),

                            TestFunc(btp.gap_adv_ind_on,
                                     sd=[AdData.ad_name_sh], start_wid=91),
                            # Don't disable advertising here
                            TestFunc(btp.gap_disconn, start_wid=77)]),
        ZTestCase("GAP", "GAP/PRIV/CONN/BV-11-C",
                  edit1_wids={1002: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, post_wid=78),
                        TestFunc(btp.gap_pair, start_wid=108),
                        TestFunc(btp.gap_conn, start_wid=2142),
                        TestFunc(btp.gap_conn, start_wid=148)],
                  # Please confirm IUT does not perform the Connection
                  # Establishment procedure since the resolvable private
                  # address is incorrect.
                  verify_wids={148: btp.verify_not_connected}),
        ZTestCase("GAP", "GAP/ADV/BV-01-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "GAP/ADV/BV-02-C",
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "GAP/ADV/BV-03-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_set_gendiscov),
                        TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "GAP/ADV/BV-04-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "GAP/ADV/BV-10-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "GAP/ADV/BV-11-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        # GAP/GAT/BV-01-C
        # wid: 158 description: IUT support both Central and Peripheral roles.
        # Click Yes if IUT act as Central role to execute this test otherwise
        # click No to act as Peripheral role.
        #
        # Testing central role.
        ZTestCase("GAP", "GAP/GAT/BV-01-C",
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78)]),
        # Testing peripheral role.
        ZTestCase("GAP", "GAP/GAT/BV-01-C",
                  no_wid=158,
                  cmds=pre_conditions + init_gatt_db +
                       [TestFunc(btp.gap_set_conn, start_wid=9),
                        TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_name_sh],
                                 start_wid=9)]),
    ]

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
            print "%d) %s" % (index, cmd)

if __name__ == "__main__":
    main()
