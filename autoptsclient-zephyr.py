#!/usr/bin/env python

"""Zephyr auto PTS client"""

import os
import sys
import argparse
import autoptsclient_common as autoptsclient
import ptsprojects.zephyr as autoprojects
from ConfigParser import SafeConfigParser

def parse_args():
    """Parses command line arguments and options"""

    conf_file = SafeConfigParser()
    if not conf_file.read("autoptsclient.conf"):
        print ("autoptsclient.conf configuration file not present."
               "See README for detailed information.")
        os._exit(0)

    arg_parser = argparse.ArgumentParser(
        description = "PTS automation client")

    arg_parser.add_argument("config",
                            help="Configuration used for testing. "
                            "It has to be specified in autoptsclient.conf. "
                            "See README for more information.",
                            choices=conf_file.sections())

    arg_parser.add_argument("-a", "--bd-addr",
                            help="Bluetooth device address of the IUT")

    arg_parser.add_argument("-d", "--debug-logs", dest="enable_max_logs",
                            action='store_true', default=False,
                            help="Enable the PTS maximum logging. Equivalent "
                            "to running test case in PTS GUI using "
                            "'Run (Debug Logs)'")

    arg_parser.add_argument("-c", "--test-cases", nargs='+',
                            help="Names of test cases to run. Groups of test "
                            "cases can be specified by profile names: "
                            "GATT, GATTS, GATTC, GAP, L2CAP, RFCOMM, SM")

    args = arg_parser.parse_args()

    try:
        server_address = conf_file.get(args.config, 'SERVER_ADDRESS', False)
    except:
        print "SERVER_ADDRESS not specified, see README"
        os._exit(0)

    try:
        workspace = conf_file.get(args.config, 'PTS_WORKSPACE_PATH', False)
    except:
        print "PTS_WORKSPACE_PATH not specified, see README"
        os._exit(0)

    try:
        iut_init = conf_file.get(args.config, 'IUT_INIT_SCRIPT', False)
    except:
        print "IUT_INIT_SCRIPT not specified, see README"
        os._exit(0)

    return args, server_address, workspace, iut_init

def main():
    """Main."""
    if os.geteuid() == 0: # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args, server_address, workspace, iut_init = parse_args()

    pts = autoptsclient.init_core(server_address, workspace,
                                  args.bd_addr, args.enable_max_logs)

    autoprojects.iutctl.init(iut_init)

    # use nble test cases if script name contains "nble"
    if "nble" in os.path.basename(sys.argv[0]):
        import ptsprojects.nble as autoprojects_nble
        test_cases = autoprojects_nble.gap.test_cases(pts)
        test_cases += autoprojects_nble.gatt.test_cases(pts)
        test_cases += autoprojects_nble.sm.test_cases(pts)
        test_cases += autoprojects_nble.l2cap.test_cases(pts)

    else: # use zephyr test cases
        test_cases = autoprojects.gap.test_cases(pts)
        test_cases += autoprojects.gatt.test_cases(pts)
        test_cases += autoprojects.sm.test_cases(pts)

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
