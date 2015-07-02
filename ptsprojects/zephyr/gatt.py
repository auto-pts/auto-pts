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
from msgdefs import *

def test_cases():
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    zephyrctl = get_zephyr()

    test_cases = [
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
