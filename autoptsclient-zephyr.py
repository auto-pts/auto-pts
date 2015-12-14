#!/usr/bin/env python

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
                            help = "IP address of the PTS automation server")

    arg_parser.add_argument("workspace",
                            help = "Path to PTS workspace file to use for "
                                    "testing. It should have pqw6 extension. "
                                    "The file should be located on the "
                                    "Windows machine, where the PTS "
                                    "automation server is running")

    arg_parser.add_argument("kernel_image",
                            help = "Zephyr OS kernel image to be used in QEMU. "
                                    "Normally a microkernel.elf file.")

    arg_parser.add_argument("--bd-addr",
                            help = "Clients bluetooth address")

    args = arg_parser.parse_args()

    return args

def main():
    """Main."""
    if os.geteuid() == 0: # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    proxy = autoptsclient.init_core(args.server_address, args.workspace,
                                    args.bd_addr)

    autoprojects.iutctl.init(args.kernel_image)

    # in some networks initial connection setup is very slow, so, contact the
    # server only once to get data needed to create test cases
    pts_bdaddr = proxy.bd_addr()

    test_cases = autoprojects.gap.test_cases()
    test_cases += autoprojects.gatt.test_cases(proxy)
    test_cases += autoprojects.sm.test_cases(pts_bdaddr)

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

    except KeyboardInterrupt: # Ctrl-C
        os._exit(14)

    # SystemExit is thrown in arg_parser.parse_args and in sys.exit
    except SystemExit:
        raise # let the default handlers do the work

    except:
        import traceback
        traceback.print_exc()
        os._exit(16)
