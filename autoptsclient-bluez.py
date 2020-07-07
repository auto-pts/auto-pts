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
from distutils.spawn import find_executable

import autoptsclient_common as autoptsclient
import ptsprojects.bluez as autoprojects
import ptsprojects.stack as stack
from pybtp import btp
from ptsprojects.bluez.iutctl import get_iut


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = autoptsclient.CliParser(description="PTS automation client")

    arg_parser.add_argument("btpclient_path",
                            help="Path to Bluez tool btpclient")

    # IUT specific arguments below

    args = arg_parser.parse_args()

    return args


def main():
    """Main."""
    if os.geteuid() == 0:  # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    ptses = autoptsclient.init_pts(args)

    btp.init(get_iut)

    autoprojects.iutctl.AUTO_PTS_LOCAL = autoptsclient.AUTO_PTS_LOCAL
    autoprojects.iutctl.init(args.btpclient_path)

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init([pts.callback_thread for pts in ptses])

    autoprojects.gap.set_pixits(ptses[0])
    autoprojects.sm.set_pixits(ptses[0])

    test_cases = autoprojects.gap.test_cases(ptses[0])
    test_cases += autoprojects.sm.test_cases(ptses[0])

    autoptsclient.run_test_cases(ptses, test_cases, args)

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
