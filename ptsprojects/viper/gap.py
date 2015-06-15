"""GAP test cases"""

import os

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.viper.qtestcase import QTestCase

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.viper.qtestcase import QTestCase

def test_cases():
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    test_cases = [
        QTestCase("GAP", "TC_IDLE_NAMP_BV_02_C"),
        QTestCase("GAP", "TC_CONN_UCON_BV_01_C"),
        QTestCase("GAP", "TC_CONN_UCON_BV_02_C")
    ]

    return test_cases

def main():
    """Main."""
    import sys
    import ptsprojects.viper.iutctrl as iutctrl

    # to be able to successfully create ViperCtl in QTestCase
    iutctrl.VIPER_KERNEL_IMAGE = sys.argv[0]

    test_cases_ = test_cases()

    for test_case in test_cases_:
        print
        print test_case
        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)

if __name__ == "__main__":
    main()
