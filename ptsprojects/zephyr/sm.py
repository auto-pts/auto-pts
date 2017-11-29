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

import btp.btp as btp


class Addr:
    le_public = 0
    le_random = 1


class IOCap:
    display_only = 0
    display_yesno = 1
    keyboard_only = 2
    no_input_output = 3


def test_cases(pts):
    """Returns a list of SM test cases
    pts -- Instance of PyPTS"""

    pts_bd_addr = pts.q_bd_addr

    pts.update_pixit_param("SM", "TSPX_peer_addr_type", "01")

    pre_conditions=[TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_read_ctrl_info),
                    TestFunc(btp.wrap, pts.update_pixit_param,
                             "SM", "TSPX_bd_addr_iut",
                             btp.get_stored_bd_addr)]

    test_cases = [
        ZTestCase("SM", "SM/MAS/PROT/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100)]),
        ZTestCase("SM", "SM/SLA/PROT/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=109)]),
        ZTestCase("SM", "SM/SLA/JW/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "SM/MAS/JW/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_disconn, pts_bd_addr,
                            Addr.le_public, start_wid=102),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=102)]),
        ZTestCase("SM", "SM/MAS/JW/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100)]),
        ZTestCase("SM", "SM/SLA/JW/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "SM/SLA/JW/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "SM/MAS/JW/BI-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100)]),
        ZTestCase("SM", "SM/MAS/PKE/BV-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr,
                                 Addr.le_public, start_wid=100)]),
        ZTestCase("SM", "SM/SLA/PKE/BV-02-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/PKE/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr,
                            Addr.le_public, start_wid=100)]),
        ZTestCase("SM", "SM/SLA/PKE/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "SM/MAS/PKE/BI-01-C",
                  edit1_wids={106: btp.var_store_get_wrong_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr,
                                 Addr.le_public, start_wid=100)]),
        ZTestCase("SM", "SM/MAS/PKE/BI-02-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr,
                                 Addr.le_public, start_wid=100)]),
        ZTestCase("SM", "SM/SLA/PKE/BI-03-C",
                  edit1_wids={106: btp.var_store_get_wrong_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/OOB/BV-05-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr,
                                 Addr.le_public, start_wid=100)]),
        ZTestCase("SM", "SM/SLA/OOB/BV-06-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/OOB/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_conn, pts_bd_addr,
                            Addr.le_public, start_wid=100),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100)]),
        ZTestCase("SM", "SM/SLA/OOB/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("SM", "SM/MAS/EKS/BV-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=100)]),
        ZTestCase("SM", "SM/SLA/EKS/BV-02-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/EKS/BI-01-C",
                  edit1_wids={104: "000000"},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=100)]),
        ZTestCase("SM", "SM/SLA/EKS/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                   TestFunc(btp.gap_adv_ind_on, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/SIGN/BV-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115,
                                 skip_call=(1,)),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115),
                        TestFunc(btp.gattc_signed_write, Addr.le_public,
                                 pts_bd_addr, "0001", "01", start_wid=110)]),
        ZTestCase("SM", "SM/MAS/SIGN/BV-03-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115),
                        TestFunc(btp.gap_disconnected_ev, post_wid=104)]),
        ZTestCase("SM", "SM/MAS/SIGN/BI-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115),
                        TestFunc(btp.gap_disconnected_ev, post_wid=104)]),
        ZTestCase("SM", "SM/SLA/KDU/BV-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/SLA/KDU/BV-02-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/SLA/KDU/BV-03-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/MAS/KDU/BV-04-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=100)]),
        ZTestCase("SM", "SM/MAS/KDU/BV-05-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=100)]),
        ZTestCase("SM", "SM/MAS/KDU/BV-06-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=100),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=100),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=100)]),
        ZTestCase("SM", "SM/SLA/KDU/BV-07-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=115)]),
        ZTestCase("SM", "SM/SLA/SIP/BV-01-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_adv_ind_on, start_wid=115),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=109),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=109)]),
        ZTestCase("SM", "SM/MAS/SIP/BV-02-C",
                  edit1_wids={104: btp.var_store_get_passkey},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=101),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=101)]),
        ZTestCase("SM", "SM/SLA/SIE/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
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
