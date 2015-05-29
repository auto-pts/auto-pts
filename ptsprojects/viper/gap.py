"""GAP test cases"""

import os

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.viper.iut_ctrl import ViperCtl

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.viper.iut_ctrl import ViperCtl

# TODO should be set in config file
VIPER_SRC_PATH = os.getenv("HOME") + "/src/forto-comm/"
APP_BIN_NAME = "pts.elf"

def test_cases():
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    test_cases = [
        TestCase("GAP", "TC_IDLE_NAMP_BV_02_C",
                 [TestFunc(ViperCtl.new_viper, VIPER_SRC_PATH + "samples/bluetooth/peripheral/", APP_BIN_NAME),
                  TestFuncCleanUp(ViperCtl.close_viper)]),
        TestCase("GAP", "TC_CONN_UCON_BV_01_C",
                 [TestFunc(ViperCtl.new_viper, VIPER_SRC_PATH + "samples/bluetooth/peripheral/", APP_BIN_NAME),
                  TestFuncCleanUp(ViperCtl.close_viper)]),
        TestCase("GAP", "TC_CONN_UCON_BV_02_C",
                 [TestFunc(ViperCtl.new_viper, VIPER_SRC_PATH + "samples/bluetooth/peripheral/", APP_BIN_NAME),
                  TestFuncCleanUp(ViperCtl.close_viper)]),
        ]

    return test_cases

def main():
    """Main."""

    import ptscontrol
    pts = ptscontrol.PyPTS()

    test_cases_ = test_cases()

    for test_case in test_cases_:
        print
        print test_case
        for cmd in test_case.cmds:
            print cmd

if __name__ == "__main__":
    main()


