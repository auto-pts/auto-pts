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

"""Mynewt auto PTS client"""

import os
import sys
import argparse

import autoptsclient_common as autoptsclient
import ptsprojects.mynewt as autoprojects
import ptsprojects.stack as stack
from pybtp import btp
from ptsprojects.mynewt.iutctl import get_iut


def check_args(args):
    """Sanity check command line arguments"""

    tty_file = args.tty_file
    ip_addr = args.ip_addr

    if not ip_addr:
        sys.exit("Server IP address not specified!")

    if tty_file:
        if (not tty_file.startswith("/dev/tty") and
                not tty_file.startswith("/dev/pts")):
            sys.exit("%s is not a TTY file!" % repr(tty_file))
        if not os.path.exists(tty_file):
            sys.exit("%s TTY file does not exist!" % repr(tty_file))


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = autoptsclient.CliParser("PTS automation client")

    arg_parser.add_argument("-t", "--tty-file",
                            help="If TTY is specified, BTP communication "
                            "with Mynewt OS running on hardware will "
                            "be done over this TTY. Hence, QEMU will "
                            "not be used.")

    board_names = autoprojects.iutctl.Board.names
    arg_parser.add_argument("-b", "--board",
                            help="Used DUT board. This option is used to "
                            "select DUT reset command that is run before "
                            "each test case. If board is not specified DUT "
                            "will not be reset. Supported boards: %s. " %
                            (", ".join(board_names,),), choices=board_names)

    # Hidden option to save test cases data in TestCase.db
    arg_parser.add_argument("-s", "--store", action="store_true",
                            default=False, help=argparse.SUPPRESS)

    args = arg_parser.parse_args()

    check_args(args)

    return args


def main():
    """Main."""
    if os.geteuid() == 0:  # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    if args.store:
        tc_db_table_name = "mynewt_" + str(args.board)
    else:
        tc_db_table_name = None

    ptses = autoptsclient.init_pts(args, tc_db_table_name)

    btp.init(get_iut)
    autoprojects.iutctl.init(args.tty_file, args.board)

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init([pts.callback_thread for pts in ptses])

    # Setup project PIXITS
    autoprojects.gap.set_pixits(ptses[0])
    autoprojects.sm.set_pixits(ptses[0])
    autoprojects.l2cap.set_pixits(ptses[0])
    autoprojects.gatt.set_pixits(ptses[0])
    autoprojects.mesh.set_pixits(ptses)

    test_cases = autoprojects.gap.test_cases(ptses[0])
    test_cases += autoprojects.gatt.test_cases(ptses[0])
    test_cases += autoprojects.sm.test_cases(ptses[0])
    test_cases += autoprojects.l2cap.test_cases(ptses[0])
    test_cases += autoprojects.mesh.test_cases(ptses)

    autoptsclient.run_test_cases(ptses, test_cases, args)

    autoprojects.iutctl.cleanup()

    print("\nBye!")
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

    except BaseException:
        import traceback
        traceback.print_exc()
        os._exit(16)
