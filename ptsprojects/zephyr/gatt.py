"""GATT test cases"""

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
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    zephyrctl = get_zephyr()

    test_cases = [
        #QTestCase("GATT", "TC_GAC_SR_BV_01_C"),
        QTestCase("GATT", "TC_GAD_SR_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GATT", "TC_GAD_SR_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GATT", "TC_GAD_SR_BV_03_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_add_inc_svc, 1),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GATT", "TC_GAD_SR_BV_04_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_add_char, 1, 0x1a, 0x03, 'bbbb'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GATT", "TC_GAD_SR_BV_05_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_add_char, 1, 0x1a, 0x03, 'bbbb'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("GATT", "TC_GAD_SR_BV_06_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.core_reg_svc_rsp_succ),
                   TestFunc(btp.gatts_add_svc, 0, 'aaaa'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_add_char, 1, 0x1a, 0x03, 'bbbb'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_add_desc, 2, 0x03, 'cccc'),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gatts_command_succ_rsp),
                   TestFunc(btp.gap_adv_ind_on)]),
        #QTestCase("GATT", "TC_GAR_SR_BV_01_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_01_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_02_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_05_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_03_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_06_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_07_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_08_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_11_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_04_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_12_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_13_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_14_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_17_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_05_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_18_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_19_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_22_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_06_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_23_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_24_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_27_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_07_C"),
        #QTestCase("GATT", "TC_GAR_SR_BV_08_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_28_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_29_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_30_C"),
        #QTestCase("GATT", "TC_GAR_SR_BI_33_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_01_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_02_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_01_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_03_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_02_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_03_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_06_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_05_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_07_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_08_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_09_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_13_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_06_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_10_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_14_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_15_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_19_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_07_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_08_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_20_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_21_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_24_C"),
        #QTestCase("GATT", "TC_GAW_SR_BV_09_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_25_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_26_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_27_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_31_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_32_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_33_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_34_C"),
        #QTestCase("GATT", "TC_GAW_SR_BI_35_C"),
        #QTestCase("GATT", "TC_GAN_SR_BV_01_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_01_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_02_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_03_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_04_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_05_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_06_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_07_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_08_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_11_C"),
        #QTestCase("GATT", "TC_GPA_SR_BV_12_C"),
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
