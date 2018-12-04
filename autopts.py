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

"""Windows PTS automation IronPython script

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

import winutils
from ptsprojects.utils import exec_adb_root
from ptsprojects.testcase import get_max_test_case_desc
import ptscontrol
import ptsprojects.aospbluez as autoprojects

# instance of ptscontrol.PyPTS
PTS = None

log = logging.debug


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = argparse.ArgumentParser(
        description="PTS automation IronPython script")

    arg_parser.add_argument(
        "workspace",
        help="Path to PTS workspace to use for testing. It should have pqw6 "
        "extension")

    args = arg_parser.parse_args()

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
    winutils.exit_if_not_admin()

    args = parse_args()

    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
              "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format=format,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)

    init_pts(args.workspace)
    exec_adb_root()


def run_test_case(pts, test_case):
    """Runs the test case specified by a TestCase instance.

    This method will cause the status of TestCase to be updated
    automatically and its on_implicit_send to be called from PTSSender

    """
    log("Starting TestCase %s %s", run_test_case.__name__, test_case)

    pts.register_ptscallback(test_case)

    test_case.pre_run()
    error_code = pts.run_test_case(test_case.project_name, test_case.name)
    test_case.post_run(error_code)

    pts.unregister_ptscallback()

    log("Done TestCase %s %s", run_test_case.__name__, test_case)


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

    PTS.set_call_timeout(120000)  # milliseconds

    for index, test_case in enumerate(test_cases):
        print (str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case.project_name.ljust(max_project_name + margin) +
               test_case.name.ljust(max_test_case_name + margin - 1)),
        run_test_case(PTS, test_case)
        print test_case.status

    print "\nBye!"


if __name__ == "__main__":
    main()
