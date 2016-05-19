#!/usr/bin/env python

"""Zephyr auto PTS client"""

import os
import sys
import argparse
import autoptsclient_common as autoptsclient
import ptsprojects.nble as autoprojects

# re-use zephyr iutctl
import ptsprojects.zephyr.iutctl
autoprojects.iutctl = ptsprojects.zephyr.iutctl

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
                            "automation server is running")

    arg_parser.add_argument("kernel_image",
                            help="Zephyr OS kernel image to be used for "
                            "testing. Normally a zephyr.elf file.")

    arg_parser.add_argument("-t", "--tty-file",
                            help="If TTY is specified, BTP communication "
                            "with Zephyr OS running on hardware will "
                            "be done over this TTY. Hence, QEMU will "
                            "not be used.")

    arg_parser.add_argument("--bd-addr",
                            help="Clients bluetooth address")

    arg_parser.add_argument("--pts-debug", action='store_true', default=False,
                            help="Enable PTS debug logs")

    board_names = autoprojects.iutctl.Board.names
    default_board = board_names[0]
    arg_parser.add_argument("-b", "--board",
                            help="Used DUT board. This option is used to "
                            "select DUT reset command that is run before "
                            "each test case. Supported boards: %s. "
                            "By default %s is used." %
                            (", ".join(board_names,), default_board),
                            choices=board_names,
                            default=default_board)

    arg_parser.add_argument("-c", "--test-cases", nargs='+',
                            help="Names of test cases to run.")

    args = arg_parser.parse_args()

    return args

def update_pixit(proxy):
    """Function used to update PIXIT parameters.

    PIXITs are set to default everytime the TPG is updated. To avoid starting
    PTS in gui mode to update the PIXITs, this can be done using this function.
    Then we're sure that those are set to appropriate value.
    """
    proxy.update_pixit_param("GATT", "TSPX_delete_link_key", "TRUE")
    proxy.update_pixit_param("GATT", "TSPX_delete_ltk", "TRUE")
    proxy.update_pixit_param("GATT", "TSPX_iut_use_dynamic_bd_addr", "TRUE")
    proxy.update_pixit_param("GAP", "TSPX_using_public_device_address", "FALSE")
    proxy.update_pixit_param("GAP", "TSPX_using_random_device_address", "TRUE")
    proxy.update_pixit_param("GAP", "TSPX_iut_device_name_in_adv_packet_for_random_address",
                             "Tester")
    proxy.update_pixit_param("SM", "TSPX_peer_addr_type", "01")


    return

def main():
    """Main."""
    if os.geteuid() == 0: # root privileges are not needed
        sys.exit("Please do not run this program as root.")

    args = parse_args()

    proxy = autoptsclient.init_core(args.server_address, args.workspace,
                                    args.bd_addr, args.pts_debug)

    autoprojects.iutctl.init(args.kernel_image, args.tty_file, args.board)

    # in some networks initial connection setup is very slow, so, contact the
    # server only once to get data needed to create test cases
    pts_bd_addr = proxy.bd_addr()

    update_pixit(proxy)

    test_cases = autoprojects.gap.test_cases(pts_bd_addr)
    test_cases += autoprojects.gatt.test_cases(pts_bd_addr)
    test_cases += autoprojects.sm.test_cases(pts_bd_addr)

    # assumes that test case names are unique across profiles
    if args.test_cases:
        test_cases = [tc for tc in test_cases if tc.name in args.test_cases]

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
