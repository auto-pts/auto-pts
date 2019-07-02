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

"""AOSP BlueZ auto PTS client"""

import os
import sys
import autoptsclient_common as autoptsclient
import ptsprojects.aospbluez as autoprojects


def parse_args():
    """Parses command line arguments and options"""

    arg_parser = autoptsclient.CliParser(description="PTS automation client")

    # IUT specific arguments below

    args = arg_parser.parse_args()

    return args


def main():
    """Main."""
    if os.geteuid() == 0:  # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    proxy = autoptsclient.init_core(args.server_address, args.workspace)

    test_cases = autoprojects.rfcomm.test_cases(proxy)
    # test_cases = autoprojects.l2cap.test_cases(proxy)
    # test_cases = autoprojects.gap.test_cases(proxy)

    autoprojects.iutctl.init()
    autoptsclient.run_test_cases(proxy, test_cases)
    autoprojects.iutctl.cleanup()

    print "\nBye!"
    sys.stdout.flush()

    proxy.unregister_xmlrpc_ptscallback()

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
