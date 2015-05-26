"""GAP test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp


def test_cases():
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    test_cases = []

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


