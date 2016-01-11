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


def test_cases():
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""
    zephyrctl = get_zephyr()

    test_cases = [
        # QTestCase("GAP", "TC_BROB_BCST_BV_01_C",),
        # QTestCase("GAP", "TC_BROB_BCST_BV_02_C",),
        # QTestCase("GAP", "TC_BROB_OBSV_BV_01_C",),
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
        # QTestCase("GAP", "TC_BOND_NBON_BV_01_C",),
        # QTestCase("GAP", "TC_BOND_NBON_BV_02_C",),
        # QTestCase("GAP", "TC_BOND_NBON_BV_03_C",),
        # QTestCase("GAP", "TC_BOND_BON_BV_01_C",),
        # QTestCase("GAP", "TC_BOND_BON_BV_02_C",),
        # QTestCase("GAP", "TC_BOND_BON_BV_03_C",),
        # QTestCase("GAP", "TC_BOND_BON_BV_04_C",),
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
        # QTestCase("GAP", "TC_GAT_BV_01_C",),
        # QTestCase("GAP", "TC_GAT_BV_05_C",),
        # QTestCase("GAP", "TC_GAT_BV_06_C",),
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
