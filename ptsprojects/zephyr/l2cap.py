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

from pybtp import btp
from pybtp.types import Addr
from ptsprojects.stack import get_stack


def test_cases(pts):
    """Returns a list of L2CAP test cases
    pts -- Instance of PyPTS"""

    le_psm = 128

    pts.update_pixit_param("L2CAP", "TSPX_le_psm", format(le_psm, '04x'))

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    stack.gap_init()

    pre_conditions=[TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.core_reg_svc_l2cap),
                    TestFunc(btp.gap_read_ctrl_info),
                    TestFunc(lambda: pts.update_pixit_param(
                             "L2CAP", "TSPX_bd_addr_iut",
                             stack.gap.iut_addr_get_str())),
                    TestFunc(lambda: pts.update_pixit_param(
                             "L2CAP", "TSPX_iut_address_type_random",
                             "TRUE" if stack.gap.iut_addr_is_random() else "FALSE"))]

    test_cases = [
        # Connection Parameter Update
        ZTestCase("L2CAP", "L2CAP/LE/CPU/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("L2CAP", "L2CAP/LE/CPU/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),
        ZTestCase("L2CAP", "L2CAP/LE/CPU/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn,
                            pts_bd_addr, Addr.le_public, start_wid=51),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),
        ZTestCase("L2CAP", "L2CAP/LE/CPU/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on)]),

        # Command Reject
        ZTestCase("L2CAP", "L2CAP/LE/REJ/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("L2CAP", "L2CAP/LE/REJ/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22)]),

        # LE Credit Based Flow Control Mode
        ZTestCase("L2CAP", "L2CAP/COS/CFC/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "L2CAP/COS/CFC/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "L2CAP/COS/CFC/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_data_rcv_ev, 0, True, start_wid=15),
                   TestFunc(btp.l2cap_disconnected_ev, 0, post_wid=40)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("L2CAP", "L2CAP/COS/CFC/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "L2CAP/COS/CFC/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_connected_ev, start_wid=41)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=39)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_connected_ev, start_wid=41),
                   TestFunc(btp.l2cap_data_rcv_ev, 0, True, start_wid=41)],
                  verify_wids={40: btp.verify_description}),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 60,
                             start_wid=43)],
                  verify_wids={37: "FF" * 60}),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            241, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=41)]),
                  # "LE_PSM not supported" Result expected.
                  # Verification is not needed, because if we received
                  # disconnected event, that means connection was rejected.
                  # verify_wids={42: btp.verify_description}),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 10, start_wid=43)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_send_data, 0, "FF", 40, start_wid=43)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.l2cap_disconn, 0, start_wid=14),
                   TestFunc(btp.l2cap_disconnected_ev, 0, start_wid=14)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-16-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=41)]),
                  # "LE_PSM not supported" Result expected.
                  # Verification is not needed, because if we received
                  # disconnected event, that means connection was rejected.
                  # verify_wids={48: btp.verify_description}),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-18-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=41)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-19-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=41)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-20-C",
                  pre_conditions +
                  [TestFunc(btp.l2cap_le_listen, le_psm),
                   TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_connected_ev, start_wid=15),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=22),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=22)]),
        ZTestCase("L2CAP", "L2CAP/LE/CFC/BV-21-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn, start_wid=15),
                   TestFunc(btp.gap_adv_ind_on, start_wid=15),
                   TestFunc(btp.l2cap_conn, pts_bd_addr, Addr.le_public,
                            le_psm, start_wid=41),
                   TestFunc(btp.l2cap_disconnected_ev, 0, False,
                            start_wid=41)]),
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
