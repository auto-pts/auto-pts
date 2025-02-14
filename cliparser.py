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
import argparse
import logging
import os
import time

from distutils.spawn import find_executable
from autopts.config import SERVER_PORT, CLIENT_PORT, MAX_SERVER_RESTART_TIME
from autopts.ptsprojects.boards import tty_exists, com_to_tty, get_debugger_snr
from autopts.ptsprojects.testcase_db import DATABASE_FILE
from autopts.utils import ykush_replug_usb, raise_on_global_end, active_hub_server_replug_usb

log = logging.debug


class CliParser(argparse.ArgumentParser):
    def __init__(self, cli_support=None, board_names=None, add_help=True):
        super().__init__(description='PTS automation client', add_help=add_help)

        self.add_argument("-i", "--ip_addr", nargs="+",
                          help="IP address of the PTS automation servers")

        self.add_argument("-l", "--local_addr", nargs="+", default=None,
                          help="Local IP address of PTS automation client")

        self.add_argument("-a", "--bd-addr",
                          help="Bluetooth device address of the IUT")

        self.add_argument("-d", "--debug-logs", dest="enable_max_logs",
                          action='store_true', default=False,
                          help="Enable the PTS maximum logging. Equivalent "
                               "to running test case in PTS GUI using "
                               "'Run (Debug Logs)'")

        self.add_argument("-c", "--test-cases", nargs='+', default=[],
                          action="extend",
                          help="Names of test cases to run. Groups of "
                               "test cases can be specified by profile names."
                                "Option can be used multiple times.")

        self.add_argument("-e", "--excluded", nargs='+', default=[],
                          help="Names of test cases to exclude. Groups of "
                               "test cases can be specified by profile names")

        self.add_argument("--test_case_limit", nargs='?', type=int, default=0,
                          help="Limit of test cases to run")

        self.add_argument("-r", "--retry", type=int, default=0,
                          help="Repeat test if failed. Parameter specifies "
                               "maximum repeat count per test")

        self.add_argument("--stress_test", action='store_true', default=False,
                          help="Repeat every test even if previous result was PASS")

        self.add_argument("-S", "--srv_port", type=int, nargs="+", default=[SERVER_PORT],
                          help="Specify the server port number."
                            " If running with three dongles, this may be on the form:"
                            " \"-S 65000 65002 65004\"")

        self.add_argument("-C", "--cli_port", type=int, nargs="+", default=[CLIENT_PORT],
                          help="Specify the client port number."
                            " If running with three dongles, this may be on the form:"
                            " \"-C 65001 65003 65005\"")

        self.add_argument("--recovery", action='store_true', default=False,
                          help="Specify if autoptsclient should try to recover"
                               " itself after wrong status.")

        self.add_argument("--not_recover", nargs='+',
                          default=['PASS', 'INCONC', 'FAIL', 'NOT_IMPLEMENTED', 'INDCSV'],
                          help="Specify at which statuses autoptsclient should "
                               "try to recover itself.")

        self.add_argument("--superguard", default=0, metavar='MINUTES', type=float,
                          help="Specify amount of time in minutes, after which"
                               " super guard will blindly trigger recovery steps.")

        self.add_argument("--ykush", metavar='YKUSH_PORT',
                          help="Specify ykush downstream port number, so on BTP TIMEOUT "
                               "the iut device could be powered off and on.")

        self.add_argument("--pylink_reset", action='store_true', default=False,
                          help="Use pylink reset.")

        # Hidden option to save test cases data in TestCase.db
        self.add_argument("-s", "--store", action="store_true",
                          default=False, help=argparse.SUPPRESS)

        self.add_argument("--sudo", action="store_true",
                          default=False, help=argparse.SUPPRESS)

        self.add_argument("--database-file", type=str, default=DATABASE_FILE,
                          help=argparse.SUPPRESS)

        self.add_argument("--max_server_restart_time", type=int, default=MAX_SERVER_RESTART_TIME,
                          help=argparse.SUPPRESS)

        self.add_argument("--tty_alias", type=str, default='', help=argparse.SUPPRESS)

        self.add_argument("--ykush_replug_delay", type=float, default=3, help=argparse.SUPPRESS)

        self.add_argument("--active-hub-server", type=str, help=argparse.SUPPRESS)

        if cli_support is None:
            return

        self.cli_support = cli_support

        if 'qemu' in self.cli_support:
            self.add_argument("--qemu_bin", default=None)

        if 'hci' in self.cli_support:
            self.add_argument("--hci", type=int, default=None,
                              help="Specify the number of the"
                                   " HCI controller(currently only used "
                                   "under native posix)")

        if 'tty' in self.cli_support and board_names:
            self.add_argument("-t", "--tty-file",
                              help="If TTY(or COM) is specified, BTP communication "
                                   "with OS running on hardware will be done over "
                                   "this TTY. Hence, QEMU will not be used.")

            self.add_argument("-j", "--jlink", dest="debugger_snr", type=str, default=None,
                              help="Specify jlink serial number manually.")

            self.add_argument("-b", "--board", dest='board_name', type=str, choices=board_names,
                              help="Used DUT board. This option is used to "
                                   "select DUT reset command that is run before "
                                   "each test case. If board is not specified DUT "
                                   "will not be reset.")

            self.add_argument("--btmon",
                              help="Capture iut btsnoop logs from device over RTT"
                              "and catch them with btmon. Requires rtt support"
                              "on IUT.", action='store_true', default=False)

            self.add_argument("--device_core", default='NRF52840_XXAA',
                              help="Specify the device core for JLink related features, "
                                   "e.g. BTMON or RTT logging.")

            self.add_argument("--rtt-log",
                              help="Capture iut logs from device over RTT. "
                              "Requires rtt support on IUT.",
                              action='store_true', default=False)

            self.add_argument("--gdb",
                              help="Skip board resets to avoid gdb server disconnection.",
                              action='store_true', default=False)

        if 'btp_tcp' in self.cli_support:
            self.add_argument("--btp-tcp-ip", type=str, default='127.0.0.1',
                              help="IP for external btp client over TCP/IP.")
            self.add_argument("--btp-tcp-port", type=str, default=64000,
                              help="Port for external btp client over TCP/IP.")

        if 'btpclient_path' in self.cli_support:
            self.add_argument("--btpclient_path", type=str, default=None,
                              help="Path to btpclient.")

        self.add_positional_args()

    def add_positional_args(self):
        self.add_argument("workspace", nargs='?', default=None,
                          help="Path to PTS workspace file to use for "
                          "testing. It should have pqw6 extension. "
                          "The file should be located on the "
                          "machine, where automation server is running.")

        self.add_argument("kernel_image", nargs='?', default=None,
                          help="OS kernel image to be used for testing,"
                          "e.g. elf file for qemu, exe for native.")

    def check_args_tty(self, args):
        if args.ykush or args.active_hub_server:
            if args.tty_alias:
                device_id = None
            else:
                device_id = args.tty_file

            if args.ykush:
                # If ykush is used, the board could be unplugged right now
                ykush_replug_usb(args.ykush, device_id=device_id, delay=args.ykush_replug_delay)
            elif args.active_hub_server:
                active_hub_server_replug_usb(args.active_hub_server)

            if args.tty_alias:
                while not os.path.islink(args.tty_alias) and not os.path.exists(os.path.realpath(args.tty_alias)):
                    raise_on_global_end()
                    log(f'Waiting for TTY {args.tty_alias} to appear...\n')
                    time.sleep(1)

                args.tty_file = os.path.realpath(args.tty_alias)

            if args.debugger_snr is None:
                args.debugger_snr = get_debugger_snr(args.tty_file)

        if not tty_exists(args.tty_file):
            return 'TTY mode: {} serial port does not exist!\n'.format(repr(args.tty_file))

        if args.tty_file.startswith("COM"):
            try:
                args.tty_file = com_to_tty(args.tty_file)
            except ValueError:
                return 'TTY mode: Port {} is not a valid COM port!\n'.format(args.tty_file)

        return ''

    def check_args_qemu(self, args):
        msg = ''

        if args.qemu_bin and not find_executable(args.qemu_bin):
            msg += 'QEMU mode: {} is needed but not found!\n'.format(args.qemu_bin)

        if args.kernel_image is None or not os.path.isfile(args.kernel_image):
            msg += 'QEMU mode: kernel_image {} is not a file!\n'.format(repr(args.kernel_image))

        return msg

    def check_args_hci(self, args):
        if args.hci is None:
            return 'HCI mode: hci port was not specified!\n'

        if args.kernel_image is None or not os.path.isfile(args.kernel_image):
            return 'HCI mode: kernel_image {} is not a file!\n'.format(
                repr(args.kernel_image))

        args.sudo = True

        return ''

    def check_args_btpclient_path(self, args):
        if not os.path.exists(args.btpclient_path):
            return 'btpclient: Path {} of btp client ' \
                   ' does not exist!\n'.format(repr(args.btpclient_path))

        return ''

    def check_args_btp_tcp(self, args):
        if not 49152 <= args.btp_tcp_port <= 65535:
            return 'btp_tcp mode: Invalid server port number={}, expected' \
                   ' range <49152,65535>'.format(args.btp_tcp_port)
        return ''

    def parse(self, arg_ns=None):
        """Parsing and sanity check command line arguments
        Args:
            arg_ns: namespace of arguments and parameters to overwrite
                    with the command line arguments parser

        Returns: (args, errmsg)
            where
            args: namespace of parameters overwritten with parsed
                  command line arguments
            errmsg: an error message if parsing failed, otherwise empty string
        """
        args = self.parse_args(None, arg_ns)

        args.superguard = 60 * args.superguard
        errmsg = ''

        if not args.ip_addr:
            args.ip_addr = ['127.0.0.1'] * len(args.srv_port)

        if not args.local_addr:
            args.local_addr = ['127.0.0.1'] * len(args.cli_port)

        for cli in self.cli_support:
            check_method = getattr(self, 'check_args_{}'.format(cli))
            msg = check_method(args)

            if msg != '':
                errmsg += msg
            else:
                errmsg = ''
                break

        return args, errmsg
