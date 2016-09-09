"""L2CAP test cases"""

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


def test_cases(pts):
    """Returns a list of L2CAP test cases
    pts -- Instance of PyPTS"""

    pts.update_pixit_param("L2CAP", "TSPX_iut_address_type_random", "TRUE")

    pts_bd_addr = pts.q_bd_addr

    pre_conditions=[TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_read_ctrl_info),
                    TestFunc(btp.wrap, pts.update_pixit_param,
                             "L2CAP", "TSPX_bd_addr_iut",
                             btp.get_stored_bd_addr)]

    test_cases = [
        # Connection Parameter Update
        ZTestCase("L2CAP", "TC_LE_CPU_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_connected_ev,
                            pts_bd_addr, Addr.le_public, start_wid=15)]),
        ZTestCase("L2CAP", "TC_LE_CPU_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_connected_ev,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),
        ZTestCase("L2CAP", "TC_LE_CPU_BI_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_connected_ev,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),
        ZTestCase("L2CAP", "TC_LE_CPU_BI_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on)]),

        # Command Reject
        ZTestCase("L2CAP", "TC_LE_REJ_BI_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("L2CAP", "TC_LE_REJ_BI_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),

        # LE Credit Based Flow Control Mode
        ZTestCase("L2CAP", "TC_COS_CFC_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "TC_COS_CFC_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "TC_COS_CFC_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "TC_COS_CFC_BV_04_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "TC_COS_CFC_BV_05_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            128, start_wid=41),
                   TestFunc(btp.l2cap_conn_rsp, start_wid=41)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_01_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_l2cap),
                        TestFunc(btp.l2cap_le_listen, 128),
                        TestFunc(btp.gap_set_conn, start_wid=15),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                                 128, start_wid=41),
                        TestFunc(btp.l2cap_conn_rsp, start_wid=41),
                        TestFunc(btp.l2cap_disconnected_ev, 0, True,
                                 start_wid=39)],
                  verify_wids={39: btp.verify_description}),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_02_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_l2cap),
                        TestFunc(btp.l2cap_le_listen, 128),
                        TestFunc(btp.gap_set_conn, start_wid=15),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                                 128, start_wid=41),
                        TestFunc(btp.l2cap_conn_rsp, start_wid=41),
                        TestFunc(btp.l2cap_connected_ev, start_wid=41),
                        TestFunc(btp.l2cap_data_rcv_ev, 0, True, start_wid=41)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_03_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_l2cap),
                        TestFunc(btp.l2cap_le_listen, 128),
                        TestFunc(btp.gap_set_conn, start_wid=15),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.l2cap_connected_ev, start_wid=15),
                        TestFunc(btp.l2cap_send_data, 0, "FF", 60,
                                 start_wid=43)],
                  verify_wids={37: "FF" * 60}),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_04_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_l2cap),
                        TestFunc(btp.gap_set_conn, start_wid=15),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                                 241, start_wid=41),
                        TestFunc(btp.l2cap_conn_rsp, start_wid=41),
                        TestFunc(btp.l2cap_disconnected_ev, 0, False,
                                 start_wid=41)]),
                  # "LE_PSM not supported" Result expected.
                  # Verification is not needed, because if we received
                  # disconnected event, that means connection was rejected.
                  # verify_wids={42: btp.verify_description}),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_05_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_06_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_07_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BI_01_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_08_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_diconn, 0, start_wid=14),
                   TestFunc(btp.l2cap_disconnected_ev, 0, start_wid=14),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=14),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=14)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_09_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_l2cap),
                   TestFunc(btp.l2cap_le_listen, 128),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "TC_LE_CFC_BV_16_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_l2cap),
                        TestFunc(btp.gap_set_conn, start_wid=15),
                        TestFunc(btp.gap_adv_ind_on, start_wid=15),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=15),
                        TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                                 128, start_wid=41),
                        TestFunc(btp.l2cap_conn_rsp, start_wid=41),
                        TestFunc(btp.l2cap_disconnected_ev, 0, False,
                                 start_wid=41)]),
                  # "LE_PSM not supported" Result expected.
                  # Verification is not needed, because if we received
                  # disconnected event, that means connection was rejected.
                  # verify_wids={48: btp.verify_description}),
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
