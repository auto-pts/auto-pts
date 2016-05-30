"""SM test cases"""

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
import ptsprojects.zephyr.btp as btp


class Addr:
    le_public = 0
    le_random = 1


def test_cases(pts_bd_addr):
    """Returns a list of SM test cases
    pts -- Instance of PyPTS"""

    test_cases = [
        ZTestCase("SM", "TC_PROT_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=109)]),
        ZTestCase("SM", "TC_JW_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "TC_JW_BI_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "TC_JW_BI_03_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "TC_PKE_BV_02_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_PKE_BV_05_C",
                  [TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "TC_PKE_BI_03_C",
                  edit1_wids={106: btp.var_get_wrong_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_OOB_BV_06_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.core_reg_svc_gatts),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_OOB_BV_08_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on)]),
        # ZTestCase("SM", "TC_OOB_BV_02_C",
        # ZTestCase("SM", "TC_OOB_BV_04_C",
        # ZTestCase("SM", "TC_OOB_BV_10_C",
        # ZTestCase("SM", "TC_OOB_BI_02_C",
        ZTestCase("SM", "TC_EKS_BV_02_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_EKS_BI_02_C",
                  [TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("SM", "TC_KDU_BV_01_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        # ZTestCase("SM", "TC_KDU_BV_02_C",
        #           edit1_wids={104: btp.var_get_passkey},
        #           cmds=[TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, 0),
        #                 TestFunc(btp.gap_adv_ind_on, start_wid=15),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=15),
        #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
        #                          Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_KDU_BV_07_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=15)]),
        ZTestCase("SM", "TC_SIP_BV_01_C",
                  edit1_wids={104: btp.var_get_passkey},
                  cmds=[TestFunc(btp.gap_set_io_cap, 0),
                        TestFunc(btp.core_reg_svc_gap),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=109),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=109),
                        TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
                                 Addr.le_public, True, start_wid=109)]),
        ZTestCase("SM", "TC_SIE_BV_01_C",
                  [TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=109),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=109),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=109),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=109)]),
    ]

    return test_cases


def main():
    """Main."""
    import sys
    import ptsprojects.nble.iutctl as iutctl

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
