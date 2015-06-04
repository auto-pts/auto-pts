#!/usr/bin/env python

import os
import argparse
import autoptsclient_common as autoptsclient
import ptsprojects.aosp_bluez as autoprojects

def parse_args():
    """Parses command line arguments and options"""

    arg_parser = argparse.ArgumentParser(
        description = "PTS automation client")

    arg_parser.add_argument("server_address",
                            help = "IP address of the PTS automation server")

    arg_parser.add_argument("workspace",
                            help = "Path to PTS workspace to use for testing." \
                            "It should have pqw6 extension. The file should " \
                            "be located on the Windows machine, where the PTS" \
                            "automation server is running")

    args = arg_parser.parse_args()

    return args

def main():
    """Main."""

    args = parse_args()

    proxy = autoptsclient.init_core(args.server_address, args.workspace)

    # test_cases = autoprojects.rfcomm.test_cases(proxy)
    # test_cases = autoprojects.l2cap.test_cases(proxy)
    test_cases = autoprojects.gap.test_cases(proxy)

    autoprojects.iut_ctrl.init()
    autoptsclient.run_test_cases(proxy, test_cases)
    autoprojects.iut_ctrl.cleanup()

    print "\nBye!"

    proxy.unregister_xmlrpc_ptscallback()

    # not the cleanest but the easiest way to exit the server thread
    os._exit(0)

if __name__ == "__main__":

    # os._exit: not the cleanest but the easiest way to exit the server thread
    try:
        main()

    # SystemExit is thrown in arg_parser.parse_args
    except (KeyboardInterrupt, SystemExit):
        os._exit(15)

    except:
        import traceback
        traceback.print_exc()
        os._exit(16)
