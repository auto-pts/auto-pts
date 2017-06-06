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

"""Zephyr auto PTS client"""

import os
import sys
import argparse
import autoptsclient_common as autoptsclient
import ptsprojects.zephyr as autoprojects

def parse_args():
    """Parses command line arguments and options"""

    arg_parser = argparse.ArgumentParser(
        description = "PTS automation client")

    arg_parser.add_argument("server_address",
                            help="IP address of the PTS automation server")

    arg_parser.add_argument("workspace",
                            help="Path to PTS workspace file to use for "
                            "testing. It should have pqw6 extension. "
                            "The file should be located on the "
                            "Windows machine, where the PTS "
                            "automation server is running. It is also "
                            "possible to use workspace provided with "
                            "the auto-pts, in that case this arguments "
                            "must be set to one of the  following: "
                            "zephyr-hci")

    # If DUT is QEMU kernel_image is passed to QEMU. If DUT is Arduino101 board
    # kernel_image helps locate openocd.cfg needed by the openocd reset command
    arg_parser.add_argument("kernel_image",
                            help="Zephyr OS kernel image to be used for "
                            "testing. Normally a zephyr.elf file.")

    arg_parser.add_argument("-t", "--tty-file",
                            help="If TTY is specified, BTP communication "
                            "with Zephyr OS running on hardware will "
                            "be done over this TTY. Hence, QEMU will "
                            "not be used.")

    arg_parser.add_argument("-a", "--bd-addr",
                            help="Bluetooth device address of the IUT")

    arg_parser.add_argument("-d", "--debug-logs", dest="enable_max_logs",
                            action='store_true', default=False,
                            help="Enable the PTS maximum logging. Equivalent "
                            "to running test case in PTS GUI using "
                            "'Run (Debug Logs)'")

    board_names = autoprojects.iutctl.Board.names
    arg_parser.add_argument("-b", "--board",
                            help="Used DUT board. This option is used to "
                            "select DUT reset command that is run before "
                            "each test case. If board is not specified DUT "
                            "will not be reset. Supported boards: %s. " %
                            (", ".join(board_names,),), choices=board_names)

    arg_parser.add_argument("-c", "--test-cases", nargs='+',
                            help="Names of test cases to run. Groups of test "
                            "cases can be specified by profile names: "
                            "GATT, GATTS, GATTC, GAP, L2CAP, RFCOMM, SM")

    args = arg_parser.parse_args()

    return args

def main():
    """Main."""
    if os.geteuid() == 0: # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    pts = autoptsclient.init_core(args.server_address, args.workspace,
                                  args.bd_addr, args.enable_max_logs)

    autoprojects.iutctl.init(args.kernel_image, args.tty_file, args.board)

    test_cases = autoprojects.gap.test_cases(pts)
    test_cases += autoprojects.gatt.test_cases(pts)
    test_cases += autoprojects.sm.test_cases(pts)
    test_cases += autoprojects.l2cap.test_cases(pts)

    if args.test_cases:
        test_cases = autoptsclient.get_test_cases_subset(
            test_cases, args.test_cases)

    autoptsclient.run_test_cases(pts, test_cases)

    autoprojects.iutctl.cleanup()

    print "\nBye!"
    sys.stdout.flush()

    pts.unregister_xmlrpc_ptscallback()

    # not the cleanest but the easiest way to exit the server thread
    os._exit(0)

if __name__ == "__main__":

    # os._exit: not the cleanest but the easiest way to exit the server thread
    try:
        main()

    except KeyboardInterrupt: # Ctrl-C
        os._exit(14)

    # SystemExit is thrown in arg_parser.parse_args and in sys.exit
    except SystemExit:
        raise # let the default handlers do the work

    except:
        import traceback
        traceback.print_exc()
        os._exit(16)
