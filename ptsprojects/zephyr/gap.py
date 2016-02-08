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


class Addr:
    le_public = 0
    le_random = 1


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
        # ZTestCase("GAP", "TC_BOND_NBON_BV_01_C",),
        # ZTestCase("GAP", "TC_BOND_NBON_BV_02_C",),
        # ZTestCase("GAP", "TC_BOND_NBON_BV_03_C",),
        # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",),
        # ZTestCase("GAP", "TC_BOND_BON_BV_02_C",),
        # ZTestCase("GAP", "TC_BOND_BON_BV_03_C",),
        # ZTestCase("GAP", "TC_BOND_BON_BV_04_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_11_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_12_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_13_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_14_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_16_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_18_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_20_C",),
        # ZTestCase("GAP", "TC_SEC_AUT_BV_22_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BV_01_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_01_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_02_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_03_C",),
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_04_C",),
        # ZTestCase("GAP", "TC_ADV_BV_01_C",),
        # ZTestCase("GAP", "TC_ADV_BV_02_C",),
        # ZTestCase("GAP", "TC_ADV_BV_03_C",),
        # ZTestCase("GAP", "TC_ADV_BV_04_C",),
        # ZTestCase("GAP", "TC_ADV_BV_10_C",),
        # ZTestCase("GAP", "TC_ADV_BV_11_C",),
        # ZTestCase("GAP", "TC_GAT_BV_01_C",),
        # ZTestCase("GAP", "TC_GAT_BV_05_C",),
        # ZTestCase("GAP", "TC_GAT_BV_06_C",),
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
