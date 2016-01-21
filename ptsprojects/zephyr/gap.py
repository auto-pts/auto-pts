"""GAP test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

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
              TestFunc(btp.gatts_start_server)]


def test_cases(pts_bd_addr):
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""
    zephyrctl = get_zephyr()

    test_cases = [
        QTestCase("GAP", "TC_BROB_BCST_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_adv_ind_on)]),
        # TODO 14427 - PTS Issue
        # QTestCase("GAP", "TC_BROB_BCST_BV_02_C",
        #           [TestFunc(btp.core_reg_svc_gap),
        #            TestFunc(btp.gap_set_nondiscov),
        #            TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GAP", "TC_BROB_OBSV_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_start_discov_pasive, start_wid=12),
                   TestFunc(btp.gap_device_found_ev, Addr.le_public,
                            pts_bd_addr, start_wid=4)]),
        # TODO 14436 - PTS Issue
        # QTestCase("GAP", "TC_BROB_OBSV_BV_02_C",),
        # QTestCase("GAP", "TC_DISC_NONM_BV_01_C",),
        QTestCase("GAP", "TC_DISC_NONM_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # QTestCase("GAP", "TC_DISC_LIMM_BV_03_C",),
        # QTestCase("GAP", "TC_DISC_LIMM_BV_04_C",),
        # QTestCase("GAP", "TC_DISC_GENM_BV_03_C",),
        # QTestCase("GAP", "TC_DISC_GENM_BV_04_C",),
        # QTestCase("GAP", "TC_DISC_LIMP_BV_01_C",),
        # QTestCase("GAP", "TC_DISC_LIMP_BV_02_C",),
        # QTestCase("GAP", "TC_DISC_LIMP_BV_03_C",),
        # QTestCase("GAP", "TC_DISC_LIMP_BV_04_C",),
        # QTestCase("GAP", "TC_DISC_LIMP_BV_05_C",),
        # QTestCase("GAP", "TC_DISC_GENP_BV_01_C",),
        # QTestCase("GAP", "TC_DISC_GENP_BV_02_C",),
        # QTestCase("GAP", "TC_DISC_GENP_BV_03_C",),
        # QTestCase("GAP", "TC_DISC_GENP_BV_04_C",),
        # QTestCase("GAP", "TC_DISC_GENP_BV_05_C",),
        # QTestCase("GAP", "TC_IDLE_NAMP_BV_01_C",),
        # QTestCase("GAP", "TC_IDLE_NAMP_BV_02_C",),
        # QTestCase("GAP", "TC_CONN_NCON_BV_01_C",),
        # QTestCase("GAP", "TC_CONN_NCON_BV_02_C",),
        # QTestCase("GAP", "TC_CONN_NCON_BV_03_C",),
        QTestCase("GAP", "TC_CONN_UCON_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GAP", "TC_CONN_UCON_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # QTestCase("GAP", "TC_CONN_UCON_BV_03_C",),
        # QTestCase("GAP", "TC_CONN_ACEP_BV_01_C",),
        # QTestCase("GAP", "TC_CONN_GCEP_BV_01_C",),
        # QTestCase("GAP", "TC_CONN_GCEP_BV_02_C",),
        # QTestCase("GAP", "TC_CONN_DCEP_BV_01_C",),
        # QTestCase("GAP", "TC_CONN_DCEP_BV_02_C",),
        QTestCase("GAP", "TC_CONN_CPUP_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GAP", "TC_CONN_CPUP_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GAP", "TC_CONN_CPUP_BV_03_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        # QTestCase("GAP", "TC_CONN_CPUP_BV_04_C",),
        # QTestCase("GAP", "TC_CONN_CPUP_BV_05_C",),
        # QTestCase("GAP", "TC_CONN_CPUP_BV_06_C",),
        # QTestCase("GAP", "TC_CONN_TERM_BV_01_C",),
        # Not supported by Zephyr yet
        # QTestCase("GAP", "TC_BOND_NBON_BV_01_C",),
        # Not supported by Zephyr yet
        # QTestCase("GAP", "TC_BOND_NBON_BV_02_C",),
        # Not supported by Zephyr yet
        # QTestCase("GAP", "TC_BOND_NBON_BV_03_C",),
        QTestCase("GAP", "TC_BOND_BON_BV_01_C",
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
        # QTestCase("GAP", "TC_BOND_BON_BV_01_C",
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
        # QTestCase("GAP", "TC_BOND_BON_BV_01_C",
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
        # QTestCase("GAP", "TC_BOND_BON_BV_01_C",
        #           cmds=[TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, 4),
        #                 TestFunc(btp.gap_set_conn),
        #                 TestFunc(btp.gap_adv_ind_on),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=108),
        #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
        #                          start_wid=108)]),
        # PTS issue #14445
        # QTestCase("GAP", "TC_BOND_BON_BV_02_C",
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
        # QTestCase("GAP", "TC_BOND_BON_BV_02_C",
        #           cmds=[TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, 3),
        #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
        #                          start_wid=78),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=78),
        #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
        #                          start_wid=108)]),
        QTestCase("GAP", "TC_BOND_BON_BV_03_C",
                  cmds=[TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_io_cap, 3),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on)]),
        # Missing functionality - We respond "None" instead of the passkey
        # QTestCase("GAP", "TC_BOND_BON_BV_03_C",
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
        # QTestCase("GAP", "TC_BOND_BON_BV_03_C",
        #           cmds=[TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, 2),
        #                 TestFunc(btp.gap_set_conn),
        #                 TestFunc(btp.gap_adv_ind_on),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=91),
        #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=150)]),
        QTestCase("GAP", "TC_BOND_BON_BV_04_C",
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
        # QTestCase("GAP", "TC_SEC_AUT_BV_11_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_12_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_13_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_14_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_16_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_18_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_20_C",),
        # QTestCase("GAP", "TC_SEC_AUT_BV_22_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BV_01_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BI_01_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BI_02_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BI_03_C",),
        # QTestCase("GAP", "TC_SEC_CSIGN_BI_04_C",),
        # QTestCase("GAP", "TC_ADV_BV_01_C",),
        # QTestCase("GAP", "TC_ADV_BV_02_C",),
        # QTestCase("GAP", "TC_ADV_BV_03_C",),
        # QTestCase("GAP", "TC_ADV_BV_04_C",),
        # QTestCase("GAP", "TC_ADV_BV_10_C",),
        # QTestCase("GAP", "TC_ADV_BV_11_C",),
        QTestCase("GAP", "TC_GAT_BV_01_C",
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=78)]),
        QTestCase("GAP", "TC_GAT_BV_01_C",
                  no_wid=158,
                  cmds=init_gatt_db + \
                       [TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_set_conn, start_wid=9),
                        TestFunc(btp.gap_adv_ind_on, start_wid=9)]),
        QTestCase("GAP", "TC_GAT_BV_05_C",
                  cmds=init_gatt_db + \
                      [TestFunc(btp.core_reg_svc_gap),
                       TestFunc(btp.gap_set_conn, start_wid=91),
                       TestFunc(btp.gap_adv_ind_on, start_wid=91)]),
        QTestCase("GAP", "TC_GAT_BV_06_C",
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

    # to be able to successfully create ZephyrCtl in QTestCase
    iutctl.ZEPHYR_KERNEL_IMAGE = sys.argv[0]

    test_cases_ = test_cases()

    for test_case in test_cases_:
        print
        print test_case
        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)

if __name__ == "__main__":
    main()
