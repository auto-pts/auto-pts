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

from ptsprojects.zephyr.iutctl import get_zephyr
import btp
import binascii
import gatt


class Addr:
    le_public = 0
    le_random = 1


init_gatt_db=[TestFunc(btp.core_reg_svc_gatts),
              TestFunc(btp.gatts_add_svc, 0, gatt.UUID.gap_svc),
              TestFunc(btp.gatts_add_char, 1, gatt.Prop.read | gatt.Prop.write,
                       gatt.Perm.read | gatt.Perm.write, gatt.UUID.device_name),
              TestFunc(btp.gatts_set_val, 2, binascii.hexlify('Tester GAP')),
              TestFunc(btp.gatts_add_char, 1, gatt.Prop.read | gatt.Prop.write,
                       gatt.Perm.read | gatt.Perm.write, gatt.UUID.appearance),
              TestFunc(btp.gatts_set_val, 4, '1234'),

              TestFunc(btp.gatts_add_svc, 0, gatt.UUID.VND16_1),
              TestFunc(btp.gatts_add_char, 6, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_authn,
                       gatt.UUID.VND16_2),
              TestFunc(btp.gatts_set_val, 7, '01'),
              TestFunc(btp.gatts_add_char, 6, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_enc, gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 9, '02'),
              TestFunc(btp.gatts_add_char, 6,
                       gatt.Prop.read | gatt.Prop.auth_swrite,
                       gatt.Perm.read | gatt.Perm.write,
                       gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 11, '03'),
              TestFunc(btp.gatts_start_server)]


class AdType:
    flags = 1
    uuid16_some = 2
    name_short = 8
    uuid16_svc_data = 22
    gap_appearance = 25
    manufacturer_data = 255

# Advertising data
ad = [(AdType.uuid16_some, '1111'),
      (AdType.gap_appearance, '1111'),
      (AdType.name_short, binascii.hexlify('Tester')),
      (AdType.manufacturer_data, '11111111'),
      (AdType.uuid16_svc_data, '111111')]


def test_cases(pts_bd_addr):
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""
    zephyrctl = get_zephyr()

    test_cases = [
        ZTestCase("GAP", "TC_BROB_BCST_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_adv_ind_on)]),
        # TODO 14427 - PTS Issue
        # ZTestCase("GAP", "TC_BROB_BCST_BV_02_C",
        #           [TestFunc(btp.core_reg_svc_gap),
        #            TestFunc(btp.gap_set_nondiscov),
        #            TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_BROB_OBSV_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_start_discov_pasive, start_wid=12),
                   TestFunc(btp.gap_device_found_ev, Addr.le_public,
                            pts_bd_addr, start_wid=4)]),
        # TODO 14436 - PTS Issue
        # ZTestCase("GAP", "TC_BROB_OBSV_BV_02_C",),
        # ZTestCase("GAP", "TC_DISC_NONM_BV_01_C",),
        ZTestCase("GAP", "TC_DISC_NONM_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # ZTestCase("GAP", "TC_DISC_LIMM_BV_03_C",),
        # ZTestCase("GAP", "TC_DISC_LIMM_BV_04_C",),
        # ZTestCase("GAP", "TC_DISC_GENM_BV_03_C",),
        # ZTestCase("GAP", "TC_DISC_GENM_BV_04_C",),
        # ZTestCase("GAP", "TC_DISC_LIMP_BV_01_C",),
        # ZTestCase("GAP", "TC_DISC_LIMP_BV_02_C",),
        # ZTestCase("GAP", "TC_DISC_LIMP_BV_03_C",),
        # ZTestCase("GAP", "TC_DISC_LIMP_BV_04_C",),
        # ZTestCase("GAP", "TC_DISC_LIMP_BV_05_C",),
        # ZTestCase("GAP", "TC_DISC_GENP_BV_01_C",),
        # ZTestCase("GAP", "TC_DISC_GENP_BV_02_C",),
        # ZTestCase("GAP", "TC_DISC_GENP_BV_03_C",),
        # ZTestCase("GAP", "TC_DISC_GENP_BV_04_C",),
        # ZTestCase("GAP", "TC_DISC_GENP_BV_05_C",),
        # ZTestCase("GAP", "TC_IDLE_NAMP_BV_01_C",),
        # ZTestCase("GAP", "TC_IDLE_NAMP_BV_02_C",),
        # ZTestCase("GAP", "TC_CONN_NCON_BV_01_C",),
        # ZTestCase("GAP", "TC_CONN_NCON_BV_02_C",),
        # ZTestCase("GAP", "TC_CONN_NCON_BV_03_C",),
        ZTestCase("GAP", "TC_CONN_UCON_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_UCON_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # ZTestCase("GAP", "TC_CONN_UCON_BV_03_C",),
        # ZTestCase("GAP", "TC_CONN_ACEP_BV_01_C",),
        # ZTestCase("GAP", "TC_CONN_GCEP_BV_01_C",),
        # ZTestCase("GAP", "TC_CONN_GCEP_BV_02_C",),
        # ZTestCase("GAP", "TC_CONN_DCEP_BV_01_C",),
        # ZTestCase("GAP", "TC_CONN_DCEP_BV_02_C",),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_03_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # ZTestCase("GAP", "TC_CONN_CPUP_BV_04_C",),
        # ZTestCase("GAP", "TC_CONN_CPUP_BV_05_C",),
        # ZTestCase("GAP", "TC_CONN_CPUP_BV_06_C",),
        # ZTestCase("GAP", "TC_CONN_TERM_BV_01_C",),
        # Not supported by Zephyr yet
        # ZTestCase("GAP", "TC_BOND_NBON_BV_02_C",),
        # Not supported by Zephyr yet
        # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",),
        # Not supported by Zephyr yet
         # ZTestCase("GAP", "TC_BOND_NBON_BV_03_C",),
         ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
                   edit1_wids={1002: btp.var_get_passkey},
                   cmds=[TestFunc(btp.core_reg_svc_gap),
                         TestFunc(btp.gap_set_io_cap, 0),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=108),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108),
                         TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                  Addr.le_public, True, start_wid=108)]),
         # PTS issue #14444
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 2),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=108),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108)]),
         # wid: 118
         # style: MMI_Style_Ok_Cancel1 0x11041
         # description: Please press ok to disconnect the link.
         #
         # We should click ok, and then wait for gap_disconnected_ev
         # (sth like a PostFunc)
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 3),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=118)]),
         # PTS issue #14444
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 4),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=108),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108)]),
         # PTS issue #14445
         # ZTestCase("GAP", "TC_BOND_BON_BV_02_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=108)]),
         # PTS issue #14449
         # ZTestCase("GAP", "TC_BOND_BON_BV_02_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 3),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108)]),
         ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
                   cmds=[TestFunc(btp.core_reg_svc_gap),
                         TestFunc(btp.gap_set_io_cap, 3),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on)]),
         # Missing functionality - We respond "None" instead of the passkey
         # ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=1002)]),
         # wid: 1001
         # style: MMI_Style_Ok 0x11040
         # description: The Secure ID is 398563. Press OK to continue.
         # ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 2),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=150)]),
         ZTestCase("GAP", "TC_BOND_BON_BV_04_C",
                   cmds=[TestFunc(btp.core_reg_svc_gap),
                         TestFunc(btp.gap_set_io_cap, 3),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=78),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108),
                         TestFunc(btp.gap_disconn, pts_bd_addr,
                                  Addr.le_public, start_wid=77),
                         TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=77)]),
         # Missing functionality - We respond "None" instead of the passkey
         # ZTestCase("GAP", "TC_SEC_AUT_BV_11_C",
         #           edit1_wids={139: "0008",
         #                       1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=1002)]),
         # PTS issue #14452
         # ZTestCase("GAP", "TC_SEC_AUT_BV_12_C",
         #           edit1_wids={139: "0008"},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=40),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=40),
         #                 TestFunc(btp.gattc_exchange_mtu, Addr.le_public,
         #                          pts_bd_addr, start_wid=40)]),
         # PTS issue #14454
         # ZTestCase("GAP", "TC_SEC_AUT_BV_13_C",
         #           edit1_wids={139: "0008",
         #                       1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=40),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=40),
         #                 TestFunc(btp.gattc_exchange_mtu, Addr.le_public,
         #                          pts_bd_addr, start_wid=40),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=40)]),
         # PTS issue #14454
         # ZTestCase("GAP", "TC_SEC_AUT_BV_14_C",
         #           edit1_wids={139: "0008",
         #                       1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=91)]),
         # PTS issue #14474
         # ZTestCase("GAP", "TC_SEC_AUT_BV_16_C",
         #           edit1_wids={140: "000a"},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 3),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
         #                          start_wid=44),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=44)]),
         # PTS issue #14445, 14457
         # ZTestCase("GAP", "TC_SEC_AUT_BV_18_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                  TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gattc_read, Addr.le_public,
         #                          pts_bd_addr, "0001", start_wid=112),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=108)]),
         # wid: 118
         # style: MMI_Style_Ok_Cancel1 0x11041
         # description: Please press ok to disconnect the link.
         #
         # We should click ok, and then wait for gap_disconnected_ev
         # (sth like a PostFunc)
         # ZTestCase("GAP", "TC_SEC_AUT_BV_20_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=91),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gattc_read, Addr.le_public,
         #                          pts_bd_addr, "0001", start_wid=112)]),
         # wid: 118
         # style: MMI_Style_Ok_Cancel1 0x11041
         # description: Please press ok to disconnect the link.
         #
         # We should click ok, and then wait for gap_disconnected_ev
         # (sth like a PostFunc)
         # ZTestCase("GAP", "TC_SEC_AUT_BV_22_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=91)]),
         # PTS issue #duplicated bond request
         # ZTestCase("GAP", "TC_SEC_CSIGN_BV_01_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=108),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=77),
         #                 TestFunc(btp.gattc_signed_write, Addr.le_public,
         #                          pts_bd_addr, "0001", "01", start_wid=125)]),
         # wid: 118
         # style: MMI_Style_Ok_Cancel1 0x11041
         # description: Please press ok to disconnect the link.
         #
         # We should click ok, and then wait for gap_disconnected_ev
         # (sth like a PostFunc)
         # + PTS issue Asking to disconnect while already disconnected
         # ZTestCase("GAP", "TC_SEC_CSIGN_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 3),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
         #                          start_wid=77),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=77),
         #                 TestFunc(btp.gattc_signed_write, Addr.le_public,
         #                          pts_bd_addr, "0001", "01", start_wid=125)]),
         # Missing functionality - We respond "None" instead of the passkey
         # ZTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 0),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=1002)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_io_cap, 3),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_01_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_io_cap, 3),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_02_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_io_cap, 3),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        # By now, we cannot remove bonding 
        # wid: 135
        # description: Please have Upper Tester remove the bonding information
        #              of the PTS. Press OK to continue
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_03_C",
        #           cmds=init_gatt_db + \
        #                [TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, 3),
        #                 TestFunc(btp.gap_set_conn),
        #                 TestFunc(btp.gap_adv_ind_on),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=91),
        #                 TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
        #                          start_wid=77),
        #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_04_C",
                  cmds=[TestFunc(btp.core_reg_svc_gatts),
                        TestFunc(btp.gatts_add_svc, 0, gatt.UUID.VND16_1),
                        TestFunc(btp.gatts_add_char, 1,
                                 gatt.Prop.read | gatt.Prop.auth_swrite,
                                 gatt.Perm.read | gatt.Perm.write_authn,
                                 gatt.UUID.VND16_3),
                        TestFunc(btp.gatts_set_val, 2, '01'),
                        TestFunc(btp.gatts_start_server),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_io_cap, 3),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_ADV_BV_01_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_02_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_03_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_set_gendiscov),
                        TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_ADV_BV_04_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_10_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_11_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_GAT_BV_01_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=78)]),
        ZTestCase("GAP", "TC_GAT_BV_01_C",
                  no_wid=158,
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn, start_wid=9),
                        TestFunc(btp.gap_adv_ind_on, start_wid=9)]),
        ZTestCase("GAP", "TC_GAT_BV_05_C",
                  cmds=init_gatt_db + \
                      [TestFunc(btp.core_reg_svc_gap),
                       TestFunc(btp.gap_set_conn, start_wid=91),
                       TestFunc(btp.gap_adv_ind_on, start_wid=91)]),
        ZTestCase("GAP", "TC_GAT_BV_06_C",
                  cmds=init_gatt_db + \
                      [TestFunc(btp.core_reg_svc_gap),
                       TestFunc(btp.gap_set_conn, start_wid=91),
                       TestFunc(btp.gap_adv_ind_on, start_wid=91)]),
    ]

    return test_cases


def main():
    """Main."""
    import sys
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
