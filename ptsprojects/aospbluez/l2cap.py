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
    from ptsprojects.utils import btmgmt

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.utils import btmgmt


def test_cases(pts):
    """Returns a list of L2CAP test cases
    pts -- Instance of PyPTS

    Initial IUT config: powered connectable br/edr le advertising
    Bluetooth in UI should be turned off then:

    Not needed for Nexus 7
    echo 1 > /sys/class/rfkill/rfkill0/state

    setprop ctl.start hciattach
    btmgmt le on
    btmgmt connectable on
    btmgmt advertising on
    btmgmt ssp on
    btmgmt power on

    PIXIT TSPX_delete_link_key must be set to TRUE, that is cause in automation
    there is no API call respective to the "Delete Link Key" PTS toolbar
    button.

    """


    test_cases = [
        TestCase("L2CAP", "TC_COS_CED_BV_01_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_03_C",
                 TestCmd("l2test -y -N 1 -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_04_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),

        # TODO: PTS issue #12351
        # the command is
        # btmgmt power off && btmgmt ssp off && btmgmt power on && l2test -r -P 4113 00:1B:DC:07:32:03 && btmgmt ssp on
        #
        # for some reason without power off I get
        # "Set Secure Simple Pairing for hci0 failed with status 0x0a (Busy)"
        # so problem with that command also ssp on won't run before l2test is killed, which
        # will kill whole command
        #
        # Hence, support for multiple commands is needed
        # run_test_case("L2CAP", "TC_COS_CED_BV_05_C", "btmgmt ssp off;l2test -r -P 4113 %s; btmgmt ssp on" % (pts.bd_addr(),))
        TestCase("L2CAP", "TC_COS_CED_BV_07_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49)),
        TestCase("L2CAP", "TC_COS_CED_BV_08_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49)),
        TestCase("L2CAP", "TC_COS_CED_BV_09_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_11_C",
                 TestCmd("l2test -u -P 4113 %s" % pts.bd_addr(), start_wid = 49)),

        TestCase("L2CAP", "TC_COS_CED_BI_01_C"),

        # TODO: just like TC_COS_CED_BV_05_C
        # TestCase("L2CAP", "TC_COS_CFD_BV_01_C")
        TestCase("L2CAP", "TC_COS_CFD_BV_02_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_03_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_08_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_09_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_11_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_12_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_IEX_BV_01_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_IEX_BV_02_C"),

        TestCase("L2CAP", "TC_COS_ECH_BV_01_C"),
        TestCase("L2CAP", "TC_COS_ECH_BV_02_C",
                 TestCmd("l2ping -c1 %s" % pts.bd_addr(), start_wid = 26)),

        TestCase("L2CAP", "TC_COS_CFC_BV_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -y -N 1 -b 40 -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22)]),
        TestCase("L2CAP", "TC_COS_CFC_BV_02_C",
                 TestCmd("l2test -y -N 1 -b 1 -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_CFC_BV_03_C",
                 TestCmd("l2test -u -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_CFC_BV_04_C",
                 [TestCmd("l2test -u -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22),
                  TestFunc(btmgmt.advertising_on)]),

        # TODO: this one requiers two l2test processes
        # TestCase("L2CAP", "TC_COS_CFC_BV_05_C", "l2test -u -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22),

        TestCase("L2CAP", "TC_CLS_UCD_BV_01_C"),
        TestCase("L2CAP", "TC_CLS_UCD_BV_02_C",
                 TestCmd("l2test -s -G -N 1 -P 4113 %s" % pts.bd_addr(), start_wid = 49)),
        TestCase("L2CAP", "TC_CLS_UCD_BV_03_C",
                 TestCmd("l2test -s -E -G -N 1 -P 4113 %s" % pts.bd_addr(), start_wid = 49)),

        TestCase("L2CAP", "TC_EXF_BV_01_C"),
        TestCase("L2CAP", "TC_EXF_BV_02_C"),
        TestCase("L2CAP", "TC_EXF_BV_03_C"),
        TestCase("L2CAP", "TC_EXF_BV_05_C"),

        TestCase("L2CAP", "TC_CMC_BV_01_C",
                  TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_04_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_05_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_06_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_07_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_08_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_09_C",
                 TestCmd("l2test -r -X basic -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_10_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),

        TestCase("L2CAP", "TC_CMC_BV_11_C",
                 TestCmd("l2test -n -P 4113 %s" % pts.bd_addr(), start_wid = 49, stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BV_12_C",
                 TestCmd("l2test -z -X ertm %s" % pts.bd_addr(), start_wid = 49)),
        TestCase("L2CAP", "TC_CMC_BV_13_C",
                 TestCmd("l2test -z -X streaming %s" % pts.bd_addr(), start_wid = 49)),
        TestCase("L2CAP", "TC_CMC_BV_14_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_15_C",
                 TestCmd("l2test -r -X streaming -P 4113")),

        TestCase("L2CAP", "TC_CMC_BI_01_C",
                 TestCmd("l2test -r -X ertm -P 4113", stop_wid = 22)),
        TestCase("L2CAP", "TC_CMC_BI_02_C",
                 TestCmd("l2test -r -X ertm -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_03_C",
                 TestCmd("l2test -r -X streaming -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_04_C",
                 TestCmd("l2test -r -X streaming -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_05_C",
                 TestCmd("l2test -r -X basic -P 4113", stop_wid = 22)),
        TestCase("L2CAP", "TC_CMC_BI_06_C",
                 TestCmd("l2test -r -X basic -P 4113", stop_wid = 22)),

        TestCase("L2CAP", "TC_FOC_BV_01_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_FOC_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_FOC_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),

        TestCase("L2CAP", "TC_OFS_BV_01_C",
                 TestCmd("l2test -x -X ertm -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_OFS_BV_03_C",
                 TestCmd("l2test -x -X streaming -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_04_C",
                 TestCmd("l2test -d -X streaming -P 4113 -F 0")),
        TestCase("L2CAP", "TC_OFS_BV_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_06_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_OFS_BV_07_C",
                 TestCmd("l2test -x -X streaming -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_08_C",
                 TestCmd("l2test -d -X streaming -P 4113")),

        TestCase("L2CAP", "TC_ERM_BV_01_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 3 -Y 3")),
        TestCase("L2CAP", "TC_ERM_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2 -Y 2")),
        TestCase("L2CAP", "TC_ERM_BV_06_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2 -Y 2")),
        TestCase("L2CAP", "TC_ERM_BV_07_C",
                 TestCmd("l2test -r -H 1000 -K 10000 -X ertm -P 4113", start_wid = 15),
                 no_wid = 19),
        TestCase("L2CAP", "TC_ERM_BV_08_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_09_C",
                 TestCmd("l2test -X ertm -P 4113")),

        # TODO: occasionally on flo fails with PTS has received an unexpected
        # L2CAP_DISCONNECT_REQ from the IUT. Sometimes passes.
        # sometimes: "MTC: The Retransmission Timeout Timer (adjusted) of PTS
        # has timed out. The IUT should have sent a S-frame by now."
        # Sometimes passes.
        # also fails in gui if you restart l2cap and run test case again.
        # only solvable by clicking "Delete Link Key" toolbar button of PTS.
        # thought TSPX_delete_link_key is set to TRUE
        TestCase("L2CAP", "TC_ERM_BV_10_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),

        TestCase("L2CAP", "TC_ERM_BV_11_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1 -Q 1")),
        TestCase("L2CAP", "TC_ERM_BV_12_C",
                 TestCmd("l2test -x -X ertm -P 4113 -R -N 1 -Q 1")),
        TestCase("L2CAP", "TC_ERM_BV_13_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BV_14_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 4")),
        TestCase("L2CAP", "TC_ERM_BV_15_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 4")),
        TestCase("L2CAP", "TC_ERM_BV_17_C",
                 TestCmd("l2test -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_18_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_19_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_20_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_21_C",
                 TestCmd("l2test -x -X ertm -P 4113 -D 2000 -N 2")),
        TestCase("L2CAP", "TC_ERM_BV_22_C",
                 TestCmd("l2test -r -H 1000 -K 10000 -X ertm -P 4113", start_wid = 15),
                 no_wid = 19),
        TestCase("L2CAP", "TC_ERM_BV_23_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),

        TestCase("L2CAP", "TC_ERM_BI_02_C",
                 TestCmd("l2test -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BI_03_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BI_04_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BI_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),

        TestCase("L2CAP", "TC_STM_BV_01_C",
                 TestCmd("l2test -x -X streaming -P 4113 -N 3 -Y 3")),
        TestCase("L2CAP", "TC_STM_BV_02_C",
                 TestCmd("l2test -d -X streaming -P 4113")),
        TestCase("L2CAP", "TC_STM_BV_03_C",
                 TestCmd("l2test -x -X streaming -P 4113 -N 2")),

        # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13206
        # TODO DANGEROUS CASE: crashes pts sometimes, report to  as pts bug?
        # TestCase("L2CAP", "TC_FIX_BV_01_C",
        #          TestCmd("l2test -z -P 4113 %s" % pts.bd_addr(), start_wid = 49))

        TestCase("L2CAP", "TC_LE_CPU_BV_01_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % pts.bd_addr())),
        TestCase("L2CAP", "TC_LE_CPU_BV_02_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -n -V le_public -J 4 %s" % pts.bd_addr(), stop_wid = 22)]),

        TestCase("L2CAP", "TC_LE_CPU_BI_01_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % pts.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_LE_CPU_BI_02_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestCmd("l2test -r -V le_public -J 4")]),

        TestCase("L2CAP", "TC_LE_REJ_BI_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -n -V le_public -J 4 %s" % pts.bd_addr(), stop_wid = 22)]),
        TestCase("L2CAP", "TC_LE_REJ_BI_02_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % pts.bd_addr(), stop_wid = 22)),

        TestCase("L2CAP", "TC_LE_CFC_BV_01_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % pts.bd_addr())),

        TestCase("L2CAP", "TC_LE_CFC_BV_02_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 22)),

        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_03_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestFunc(pts.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "FALSE"),
                  TestCmd("l2test -x -N 1 -V le_public %s" % pts.bd_addr(), stop_wid = 22),
                  TestFuncCleanUp(btmgmt.advertising_off),
                  TestFuncCleanUp(pts.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "TRUE")]),

        TestCase("L2CAP", "TC_LE_CFC_BV_04_C",
                 TestCmd("l2test -n -V le_public -P 241 %s" % pts.bd_addr())),

        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_05_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestFunc(pts.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "FALSE"),
                  TestCmd("l2test -r -V le_public -J 4")]),

        # PTS issue #12853
        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_06_C",
                 [TestCmd("l2test -x -b 1 -V le_public %s" % pts.bd_addr()),
                  TestFuncCleanUp(pts.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "TRUE")]),

        # does not pass in automation mode and makes PTS unstable:
        # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13225
        # TestCase("L2CAP", "TC_LE_CFC_BV_07_C",
        #          [TestFunc(btmgmt.advertising_off),
        #           TestCmd("l2test -u -V le_public %s" % pts.bd_addr(),
        #                   start_wid = 51, stop_wid = 22)]),
        TestCase("L2CAP", "TC_LE_CFC_BI_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -u -V le_public %s" % pts.bd_addr())]),
        TestCase("L2CAP", "TC_LE_CFC_BV_08_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % pts.bd_addr(), stop_wid = 14)),
        TestCase("L2CAP", "TC_LE_CFC_BV_09_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % pts.bd_addr())),
        TestCase("L2CAP", "TC_LE_CFC_BV_16_C",
                 [TestCmd("l2test -n -V le_public -P 37 %s" % pts.bd_addr()),
                  TestFuncCleanUp(btmgmt.advertising_on)])

        # PTS issue #12730
        # l2test -s -N 1 <bdaddr>
        # l2test -s -N 1 -V le_public <bdaddr>
        # TestCase("L2CAP", "TC_LE_CID_BV_02_I",  "")

        # PTS issue #12730
        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        # l2test -w -N 1
        # l2test -w -N 1 -V le_public
        # TestCase("L2CAP", "TC_LE_CID_BV_01_C",  "")
    ]

    return test_cases

def main():
    """Main."""

    import ptscontrol
    pts = ptscontrol.PyPTS()

    test_cases_ = test_cases(pts)

    for test_case in test_cases_:
        print
        print test_case
        for cmd in test_case.cmds:
            print cmd

if __name__ == "__main__":
    main()
