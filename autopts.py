"""PTS automation IronPython script

To use it you have to have installed COM interop assembly to the bin directory
of PTS, like:

cp Interop.PTSConrol.dll C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\bin\

Since PTS requires admin rights, you have to run this script as admin. You need
to use 32 bit IronPython to run this script because PTS is a 32 bit
application.

Run this is script in admin terminal as follows:

ipy.exe autopts.py

"""

import os
import sys
import logging
import argparse

from ptsprojects.utils import exec_adb_root
from ptsprojects.testcase import get_max_test_case_desc
import ptscontrol
import ptsprojects.aosp_bluez as autoprojects

# instance of ptscontrol.PyPTS
PTS = None

log = logging.debug

def parse_args():
    """Parses command line arguments and options"""
    required_ext = ".pqw6" # valid PTS workspace file extension

    arg_parser = argparse.ArgumentParser(
        description = "PTS automation IronPython script")

    arg_parser.add_argument(
        "workspace",
        help = "Path to PTS workspace to use for testing. It should have %s "
        "extension" % (required_ext,))

    args = arg_parser.parse_args()

    # check that aruments and options are sane
    if not os.path.isfile(args.workspace):
        raise Exception("Workspace file '%s' does not exist" %
                        (args.workspace,))

    specified_ext = os.path.splitext(args.workspace)[1]
    if required_ext != specified_ext:
        raise Exception(
            "Workspace file '%s' extension is wrong, should be %s" %
            (args.workspace, required_ext))

    return args

def init_pts(workspace):
    """Initializes PTS COM objects
    
    workspace -- Path to PTS workspace to use for testing.

    """
    global PTS

    PTS = ptscontrol.PyPTS()
    PTS.open_workspace(workspace)

def init():
    "Initialization procedure"

    args = parse_args()

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    logging.basicConfig(format = '%(name)s [%(asctime)s] %(message)s',
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    init_pts(args.workspace)
    exec_adb_root()

def main():
    """Main."""
    init()

    test_cases = autoprojects.rfcomm.test_cases(PTS)
    # test_cases = autoprojects.l2cap.test_cases(PTS)
    # test_cases = autoprojects.gap.test_cases(PTS)

    log("Running test cases...")

    num_test_cases = len(test_cases)
    num_test_cases_width = len(str(num_test_cases))
    max_project_name, max_test_case_name = get_max_test_case_desc(test_cases)
    margin = 3

    for index, test_case in enumerate(test_cases):
        print (str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case.project_name.ljust(max_project_name + margin) +
               test_case.name.ljust(max_test_case_name + margin - 1)),
        PTS.run_test_case_object(test_case)
        print test_case.status

    print "\nBye!"

if __name__ == "__main__":
    main()
