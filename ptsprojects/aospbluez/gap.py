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

"""GAP test cases"""

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
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    test_cases = [
        TestCase("GAP", "TC_MOD_NDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_off)),

        TestCase("GAP", "TC_MOD_LDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_MOD_LDIS_BV_02_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_MOD_LDIS_BV_03_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),

        TestCase("GAP", "TC_MOD_GDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_on)),
        TestCase("GAP", "TC_MOD_GDIS_BV_02_C"),

        TestCase("GAP", "TC_MOD_NCON_BV_01_C",
                 TestFunc(btmgmt.connectable_off)),

        TestCase("GAP", "TC_MOD_CON_BV_01_C",
                 TestFunc(btmgmt.connectable_on)),

        TestCase("GAP", "TC_DISC_NONM_BV_01_C",
                 [TestFunc(btmgmt.connectable_off),
                  TestFunc(btmgmt.advertising_on)]),

        TestCase("GAP", "TC_DISC_NONM_BV_02_C",
                 [TestFunc(btmgmt.connectable_on),
                  TestFunc(btmgmt.discoverable_off)]),

        TestCase("GAP", "TC_DISC_LIMM_BV_01_C",
                 TestFunc(btmgmt.discoverable_limited, 30), no_wid = 120),
        TestCase("GAP", "TC_DISC_LIMM_BV_02_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_DISC_LIMM_BV_03_C",
                 TestFunc(btmgmt.discoverable_limited, 30), no_wid = 120),

        TestCase("GAP", "TC_DISC_LIMM_BV_04_C",
                 [TestFunc(btmgmt.discoverable_off),
                  TestFunc(btmgmt.power_off),
                  TestFunc(btmgmt.bredr_off),
                  TestFunc(btmgmt.power_on),
                  TestFunc(btmgmt.discoverable_limited, 30)]),

        TestCase("GAP", "TC_DISC_GENM_BV_01_C",
                 TestFunc(btmgmt.discoverable_on), no_wid = 120),
        TestCase("GAP", "TC_DISC_GENM_BV_02_C",
                 TestFunc(btmgmt.bredr_on)),
        TestCase("GAP", "TC_DISC_GENM_BV_03_C", no_wid = 120),

        TestCase("GAP", "TC_DISC_GENM_BV_04_C",
                 [TestFunc(btmgmt.power_off),
                  TestFunc(btmgmt.bredr_off),
                  TestFunc(btmgmt.power_on),
                  TestFunc(btmgmt.discoverable_on),
                  TestFuncCleanUp(btmgmt.bredr_on)]),

        # TODO grep for pts in output of "find -l" to find the answer to the last
        # pts dialog
        TestCase("GAP", "TC_DISC_LIMP_BV_01_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_02_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_03_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_04_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_05_C", TestCmd("btmgmt find -l")),

        TestCase("GAP", "TC_DISC_GENP_BV_01_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_02_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_03_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_04_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_05_C", TestCmd("btmgmt find -l")),

        TestCase("GAP", "TC_IDLE_GIN_BV_01_C",
                 TestCmd("btmgmt find", start_wid = 146)),
        TestCase("GAP", "TC_IDLE_LIN_BV_01_C",
                 TestCmd("hcitool scan --iac=liac", start_wid = 146)),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_IDLE_NAMP_BV_01_C"),

        TestCase("GAP", "TC_IDLE_NAMP_BV_02_C",
                 TestFunc(btmgmt.advertising_on)),

        TestCase("GAP", "TC_CONN_NCON_BV_01_C",
                 TestFunc(btmgmt.connectable_off), no_wid = 120),
        TestCase("GAP", "TC_CONN_NCON_BV_02_C", no_wid = 120),
        TestCase("GAP", "TC_CONN_NCON_BV_03_C", no_wid = 120),

        TestCase("GAP", "TC_CONN_DCON_BV_01_C",
                 TestFunc(btmgmt.connectable_on), no_wid = 120),

        TestCase("GAP", "TC_CONN_UCON_BV_01_C"),
        TestCase("GAP", "TC_CONN_UCON_BV_02_C"),
        TestCase("GAP", "TC_CONN_UCON_BV_03_C"),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_CONN_ACEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_GCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_GCEP_BV_02_C"),

        # TestCase("GAP", "TC_CONN_SCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_DCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_DCEP_BV_03_C"),
        TestCase("GAP", "TC_CONN_CPUP_BV_01_C",
                 TestFunc(btmgmt.advertising_on)),
        # TestCase("GAP", "TC_CONN_CPUP_BV_02_C",
        #          TestFunc(btmgmt.advertising_on)),
        TestCase("GAP", "TC_CONN_CPUP_BV_03_C",
                 TestFunc(btmgmt.advertising_on)),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_CONN_CPUP_BV_04_C"),
        # TestCase("GAP", "TC_CONN_CPUP_BV_05_C"),
        # TestCase("GAP", "TC_CONN_CPUP_BV_06_C"),
        # TestCase("GAP", "TC_CONN_TERM_BV_01_C"),
        # TestCase("GAP", "TC_CONN_PRDA_BV_01_C"),
        # TestCase("GAP", "TC_CONN_PRDA_BV_02_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_01_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_02_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_03_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_01_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_02_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_03_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_04_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_11_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_12_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_13_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_14_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_17_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_18_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_19_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_20_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_21_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_22_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_23_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_24_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BV_01"),
        # TestCase("GAP", "TC_SEC_CSIGN_BV_02"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_01_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_02_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_03_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_04_C"),
        #
        # PTS issue #12951
        # Note: PIXITs required to be changed:
        # TSPX_using_public_device_address: FALSE
        # TSPX_using_random_device_address: TRUE
        # echo 30 > /sys/kernel/debug/bluetooth/hci0/
        #                                 rpa_timeout
        # btmgmt power off
        # btmgmt privacy on
        # btmgmt power on
        # TestCase("GAP", "TC_PRIV_CONN_BV_10_C")
        #
        # INC
        # PTS issue #12952
        # JIRA #BA-186
        # TestCase("GAP", "TC_PRIV_CONN_BV_11_C")
        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_ADV_BV_02_C"),
        # TestCase("GAP", "TC_ADV_BV_03_C"),
        # TestCase("GAP", "TC_ADV_BV_05_C"),
        # TestCase("GAP", "TC_GAT_BV_01_C"),
        # TestCase("GAP", "TC_DM_NCON_BV_01_C"),
        # TestCase("GAP", "TC_DM_CON_BV_01_C"),
        # TestCase("GAP", "TC_DM_NBON_BV_01_C", TestFunc(btmgmt.bondable_off)),
        # TODO: must script/automate haltest
        # TestCase("TC_DM_BON_BV_01_C"),
        TestCase("GAP", "TC_DM_GIN_BV_01_C"),
        TestCase("GAP", "TC_DM_LIN_BV_01_C"),
        TestCase("GAP", "TC_DM_NAD_BV_01_C"),
        # TestCase("GAP", "TC_DM_NAD_BV_02_C"),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_DM_LEP_BV_01_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_02_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_04_C",
        #          TestCmd("l2test -n %s" % pts.bd_addr())),
        # TestCase("GAP", "TC_DM_LEP_BV_05_C",
        #          [TestCmd("btmgmt find -b"),
        #           TestCmd("l2test -n %s" % pts.bd_addr())])

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_DM_LEP_BV_06_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_07_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_08_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_09_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_10_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_11_C"),
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
