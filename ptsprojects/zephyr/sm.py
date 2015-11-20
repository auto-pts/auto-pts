"""SM test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

from ptsprojects.zephyr.iutctl import get_zephyr
import btp

def test_cases():
    """Returns a list of SM test cases
    pts -- Instance of PyPTS"""

    zephyrctl = get_zephyr()

    test_cases = [
        QTestCase("SM", "TC_PROT_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_conn, "00:1B:DC:06:06:CA", 0, start_wid = 100),
                    TestFunc(btp.gap_connected_ev, "00:1B:DC:06:06:CA", 1, start_wid = 100),
                    TestFunc(btp.gap_pair, "00:1B:DC:06:06:CA", 0, start_wid = 100)]),
        QTestCase("SM", "TC_PROT_BV_02_C",
        #QTestCase("SM", "TC_JW_BV_02_C",
        #QTestCase("SM", "TC_JW_BV_05_C",
        #QTestCase("SM", "TC_JW_BI_01_C",
        #QTestCase("SM", "TC_JW_BI_02_C",
        #QTestCase("SM", "TC_JW_BI_03_C",
        #QTestCase("SM", "TC_JW_BI_04_C",
        #QTestCase("SM", "TC_PKE_BV_01_C",
        #QTestCase("SM", "TC_PKE_BV_02_C",
        #QTestCase("SM", "TC_PKE_BV_04_C",
        #QTestCase("SM", "TC_PKE_BV_05_C",
        #QTestCase("SM", "TC_PKE_BI_01_C",
        #QTestCase("SM", "TC_PKE_BI_02_C",
        #QTestCase("SM", "TC_PKE_BI_03_C",
        #QTestCase("SM", "TC_OOB_BV_05_C",
        #QTestCase("SM", "TC_OOB_BV_06_C",
        #QTestCase("SM", "TC_OOB_BV_07_C",
        #QTestCase("SM", "TC_OOB_BV_08_C",
        #QTestCase("SM", "TC_EKS_BV_01_C",
        #QTestCase("SM", "TC_EKS_BV_02_C",
        #QTestCase("SM", "TC_EKS_BI_01_C",
        #QTestCase("SM", "TC_EKS_BI_02_C",
        #QTestCase("SM", "TC_SIGN_BV_01_C",
        #QTestCase("SM", "TC_SIGN_BV_03_C",
        #QTestCase("SM", "TC_SIGN_BI_01_C",
        #QTestCase("SM", "TC_KDU_BV_01_C",
        #QTestCase("SM", "TC_KDU_BV_02_C",
        #QTestCase("SM", "TC_KDU_BV_03_C",
        #QTestCase("SM", "TC_KDU_BV_09_C",
        #QTestCase("SM", "TC_KDU_BV_04_C",
        #QTestCase("SM", "TC_KDU_BV_05_C",
        #QTestCase("SM", "TC_KDU_BV_06_C",
        #QTestCase("SM", "TC_KDU_BV_08_C",
        #QTestCase("SM", "TC_KDU_BV_07_C",
        #QTestCase("SM", "TC_SIP_BV_01_C",
        #QTestCase("SM", "TC_SIP_BV_02_C",
        #QTestCase("SM", "TC_SIE_BV_01_C",
    ]

    return test_cases

def main():
    """Main."""
    import sys
    import ptsprojects.zephyr.iutctl as iutctl

    iutctl.init_stub()

    # to be able to successfully create ZephyrCtl in QTestCase
    iutctl.ZEPHYR_KERNEL_IMAGE = sys.argv[0]

    test_cases_ = test_cases()

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
