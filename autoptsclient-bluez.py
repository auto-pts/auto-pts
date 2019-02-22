#!/usr/bin/env python

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

"""Bluez auto PTS client"""

import os
import sys
import argparse
from distutils.spawn import find_executable

import autoptsclient_common as autoptsclient
import ptsprojects.bluez as autoprojects
import ptsprojects.stack as stack
from pybtp import btp
from ptsprojects.bluez.iutctl import get_iut


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = argparse.ArgumentParser(description="PTS automation client")

    arg_parser.add_argument("-i", "--ip_addr", nargs="+",
                            help="IP address of the PTS automation servers")

    arg_parser.add_argument("-l", "--local_addr", default=None,
                            help="Local IP address of PTS automation client")

    arg_parser.add_argument("-a", "--bd-addr",
                            help="Bluetooth device address of the IUT")

    arg_parser.add_argument("workspace",
                            help="Path to PTS workspace file to use for "
                            "testing. It should have pqw6 extension. "
                            "The file should be located on the "
                            "Windows machine, where the PTS automation server "
                            "is running. It is also possible to use default "
                            "workspace provided with the auto-pts, in that "
                            "case this arguments must be set to one of the "
                            "following: bluez")

    arg_parser.add_argument("btpclient_path",
                            help="Path to Bluez tool btpclient")

    arg_parser.add_argument("-d", "--debug-logs", dest="enable_max_logs",
                            action='store_true', default=False,
                            help="Enable the PTS maximum logging. Equivalent "
                            "to running test case in PTS GUI using "
                            "'Run (Debug Logs)'")

    arg_parser.add_argument("-c", "--test-cases", nargs='+',
                            help="Names of test cases to run. Groups of test "
                            "cases can be specified by profile names: "
                            "GAP")

    args = arg_parser.parse_args()

    return args


def main():
    """Main."""
    if os.geteuid() == 0:  # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    callback_thread = autoptsclient.init_core()

    ptses = []
    for ip in args.ip_addr:
        ptses.append(autoptsclient.init_pts(ip, args.workspace, args.bd_addr,
                                            args.enable_max_logs,
                                            callback_thread, None,
                                            args.local_addr))

    btp.init(get_iut)

    autoprojects.iutctl.AUTO_PTS_LOCAL = autoptsclient.AUTO_PTS_LOCAL
    autoprojects.iutctl.init(args.btpclient_path)

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init(callback_thread.set_pending_response,
                          callback_thread.clear_pending_responses)

    test_cases = autoprojects.gap.test_cases(ptses[0])
    test_cases += autoprojects.sm.test_cases(ptses[0])

    additional_test_cases = []

    if args.test_cases:
        test_cases = autoptsclient.get_test_cases_subset(test_cases,
                                                         args.test_cases)

    autoptsclient.run_test_cases(ptses, test_cases, additional_test_cases, 0)

    autoprojects.iutctl.cleanup()

    print "\nBye!"
    sys.stdout.flush()

    for pts in ptses:
        pts.unregister_xmlrpc_ptscallback()

    # not the cleanest but the easiest way to exit the server thread
    os._exit(0)


if __name__ == "__main__":
    # os._exit: not the cleanest but the easiest way to exit the server thread
    try:
        main()

    except KeyboardInterrupt:  # Ctrl-C
        os._exit(14)

    # SystemExit is thrown in arg_parser.parse_args and in sys.exit
    except SystemExit:
        raise  # let the default handlers do the work

    except Exception:
        import traceback
        traceback.print_exc()
        os._exit(16)
