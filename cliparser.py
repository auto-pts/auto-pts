#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2025, Atmosic.
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
import sys
import time
from distutils.spawn import find_executable

from autopts.config import CLIENT_PORT, MAX_SERVER_RESTART_TIME, SERIAL_BAUDRATE, SERVER_PORT
from autopts.ptsprojects.boards import com_to_tty, get_debugger_snr, get_free_device, get_tty, tty_exists
from autopts.ptsprojects.testcase_db import DATABASE_FILE
from autopts.utils import active_hub_server_replug_usb, get_tc_from_wid, load_wid_report, raise_on_global_end, ykush_replug_usb

log = logging.debug
IUT_MODES = ['tty', 'qemu', 'native', 'btpclient_path']


class CliParser(argparse.ArgumentParser):
    def __init__(self, iut_modes=None, board_names=None, add_help=True, *args, **kwargs):
        super().__init__(description='PTS automation client', add_help=add_help)

        if iut_modes is None:
            iut_modes = IUT_MODES

        self.add_argument("--iut-mode", "--iut_mode", type=str, choices=iut_modes, default=None,
                          help="Specify the mode of the IUT (Identity Under Test). "
                               "If the option is not provided, mode will be inferred "
                               "from the parameters.")

        self.add_argument("-i", "--ip_addr", nargs="+",
                          help="IP address of the PTS automation servers. "
                          "If running with multiple servers(PTS dongles), "
                          "specify the IP addresses separated by a space, "
                          "e.g. \"-i 192.168.2.2 192.168.2.2\"")

        self.add_argument("-l", "--local_addr", nargs="+", default=None,
                          help="Local IP address of PTS automation client. "
                          "If running with multiple servers(PTS dongles), "
                          "specify the IP addresses separated by a space, "
                          "e.g. \"-l 192.168.2.1 192.168.2.1\"")

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

        self.add_argument("--test-cases-file", type=argparse.FileType('r'),
                          help="A file with names of test cases to run. "
                                "One test case per line. Use instead of -c option.")

        self.add_argument("-e", "--excluded", nargs='+', default=[],
                          help="Names of test cases to exclude. Groups of "
                               "test cases can be specified by profile names")

        self.add_argument("--test_case_limit", nargs='?', type=int, default=0,
                          help="Limit of test cases to run")

        self.add_argument("-r", "--retry", type=int, default=0,
                          help="Repeat test if failed. Parameter specifies "
                               "maximum repeat count per test")

        self.add_argument("--repeat_until_fail", action='store_true', default=False,
                          help="Repeat test case until non-pass verdict")

        self.add_argument("--stress_test", action='store_true', default=False,
                          help="Repeat every test even if previous result was PASS")

        self.add_argument("-S", "--srv_port", type=int, nargs="+", default=[SERVER_PORT],
                          help="Specify the server port number. "
                          "If running with multiple servers(PTS dongles), "
                          "specify the ports separated by a space, "
                          "e.g. \"-S 65000 65002 65004\"")

        self.add_argument("-C", "--cli_port", type=int, nargs="+", default=[CLIENT_PORT],
                          help="Specify the client port number. "
                          "If running with multiple servers(PTS dongles), "
                          "specify the ports separated by a space, "
                          "e.g. \"-C 65001 65003 65005\"")

        self.add_argument("--tty-baudrate", "--tty_baudrate", type=int, default=SERIAL_BAUDRATE,
                          help="The TTY baudrate.")

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

        self.add_argument('--nc', dest='copy', action='store_false',
                          help='Do not copy workspace, open original one. '
                               'Warning: workspace file might be modified', default=True)

        self.add_argument("--rtscts", dest='rtscts', action="store_true", default=False,
                          help="Enable UART hardware flow control.")

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
        self.add_argument("--usb-replug-available", "--usb_replug_available", type=bool,
                          default=False, help=argparse.SUPPRESS)

        self.add_argument("--project_path", type=str, help=argparse.SUPPRESS)

        self.add_argument('--nb', dest='no_build', action='store_true',
                          help='Skip build and flash in bot mode.', default=False)

        self.add_argument("--btattach-bin", "--btattach_bin", default=None,
                          help="The path to the btattach executable, e.g. /usr/bin/btattach")
        self.add_argument("--btattach-at-every-test-case", "--btattach_at_every_test_case",
                          action='store_true', default=False,
                          help="The path to the btattach executable, e.g. /usr/bin/btattach")
        self.add_argument("--btproxy-bin", "--btproxy_bin", default=None,
                          help="The path to the btproxy executable, e.g. /usr/bin/btproxy")
        self.add_argument("--qemu-bin", "--qemu_bin", default=None,
                          help="The path to the QEMU executable, e.g. /usr/bin/qemu-system-arm")
        self.add_argument("--qemu-options", "--qemu_options", type=str, default="",
                          help="Additional options for the qemu, e.g. -cpu cortex-m3 -machine lm3s6965evb")
        self.add_argument("--kernel-cpu", "--kernel_cpu", default="qemu_cortex_m3",
                          help="The type of CPU that will be used for building an image, e.g. qemu_cortex_m3")

        self.add_argument("--hci", type=int, default=None,
                          help="Specify the number of the HCI controller")
        self.add_argument("--hid-vid", "--hid_vid", type=str, default=None,
                          help="Specify the VID of the USB device used as a HCI controller "
                          "(hexadecimal string, e.g. '2fe3')")
        self.add_argument("--hid-pid", "--hid_pid", type=str, default=None,
                          help="Specify the PID of the USB device used as a HCI controller "
                          "(hexadecimal string, e.g. '000b')")
        self.add_argument("--hid-serial", "--hid_serial", type=str, default=None,
                          help="Specify the serial number of the USB device used as a HCI controller")
        self.add_argument("--btmgmt-bin", "--btmgmt_bin", type=str, default=None,
                          help="The path to the btmgmt executable, e.g. /usr/bin/btmgmt")
        self.add_argument("--setcap-cmd", "--setcap_cmd", type=str, default=None,
                          help="Command to set HCI access permissions for zephyr.exe in native mode, "
                          "e.g. sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe "
                          "To allow sudo setcap without password, add to visudo a line like this: "
                          "youruser ALL=(ALL) NOPASSWD: /usr/sbin/setcap")

        self.add_argument("-t", "--tty-file",
                          help="If TTY(or COM) is specified, BTP communication "
                               "with OS running on hardware will be done over "
                               "this TTY. Hence, QEMU will not be used.")

        self.add_argument("--net-tty-file", dest='net_tty_file', type=str, default=None,
                          help="This can be used to log output from network core of IUT "
                               "(if additional port is available). Value should match "
                               "the COM/tty file port that outputs log from the network core. "
                               "There's no indication which COM port maps to the network "
                               "core.")

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

        self.add_argument("--rtt-log-syncto",
                          help="Specify the number of seconds that the RTT logging"
                          "should continue after the test has finished executing.",
                          type=float, default=0)

        self.add_argument("--gdb",
                          help="Skip board resets to avoid gdb server disconnection.",
                          action='store_true', default=False)

        self.add_argument("--btp-tcp-ip", "--btp_tcp_ip", type=str, default='127.0.0.1',
                          help="IP for external btp client over TCP/IP.")
        self.add_argument("--btp-tcp-port", "--btp_tcp_port", type=int, default=None,
                          help="Port for external btp client over TCP/IP.")

        self.add_argument("--btpclient_path", type=str, default=None,
                          help="Path to btpclient.")

        self.add_argument("--wid_run", nargs=2, metavar=("SERVICE", "WID"),
                          help="Run testcases based on service and wid")

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

    def _replug_and_find_tty(self, args):
        log(f'{self._replug_and_find_tty.__name__}')

        if not args.ykush and not args.active_hub_server:
            return False

        if args.ykush:
            device_id = args.tty_alias if args.tty_alias else args.tty_file
            ykush_replug_usb(args.ykush, device_id=device_id, delay=args.ykush_replug_delay)
        elif args.active_hub_server:
            active_hub_server_replug_usb(args.active_hub_server)

        if args.tty_alias:
            while not os.path.islink(args.tty_alias) and not os.path.exists(os.path.realpath(args.tty_alias)):
                raise_on_global_end()
                log(f'Waiting for TTY {args.tty_alias} to appear...\n')
                time.sleep(1)

            args.tty_file = os.path.realpath(args.tty_alias)
        elif args.debugger_snr:
            args.tty_file = get_tty(args.debugger_snr, args.board_name)
        else:
            args.tty_file, args.debugger_snr = get_free_device(args.board_name)

        if not tty_exists(args.tty_file):
            return False

        return True

    def wid_run_tcs(self, args):
        """
        If --wid_run SERVICE WID was provided:
        - load the CSV mapping
        - lookup testcases for (service, wid)
        - print them before execution
        - and append to args.test_cases so they get executed like normal.
        """
        if not args.wid_run:
            return

        mapping = load_wid_report()
        service, wid = args.wid_run

        tcs = get_tc_from_wid(service, wid, mapping)
        if not tcs:
            print(f"No testcases found for service={service}, wid={wid}")
            return

        print(f"Testcases for {service} {wid}:")
        for tc in tcs:
            print(tc)

        # Append found test cases to test cases list
        args.test_cases = list(args.test_cases) + tcs

    def find_tty(self, args):
        log(f'{self.find_tty.__name__}')

        if args.tty_file:
            args.tty_alias = None
            log(f'Using tty_file={args.tty_file}')
        elif args.tty_alias:
            args.tty_file = os.path.realpath(args.tty_alias)
            log(f'Using tty_alias={args.tty_alias} -> tty_file={args.tty_file}')
        elif args.debugger_snr:
            args.tty_file = get_tty(args.debugger_snr, args.board_name)
            log(f'Using debugger_snr={args.debugger_snr} -> tty_file={args.tty_file}')
        else:
            args.tty_file, args.debugger_snr = get_free_device(args.board_name)
            log(f'Found free TTY tty_file={args.tty_file} debugger_snr={args.debugger_snr}')

        if not tty_exists(args.tty_file):
            log(f'The TTY tty_file={args.tty_file} does not exist.')
            # If an active hub is used, the board could be unplugged right now
            if not self._replug_and_find_tty(args):
                return f'TTY IUT mode: {repr(args.tty_file)} serial port does not exist!\n'

        if args.debugger_snr is None:
            args.debugger_snr = get_debugger_snr(args.tty_file)

        if args.tty_file.startswith("COM"):
            try:
                args.tty_file = com_to_tty(args.tty_file)
            except ValueError:
                return f'TTY IUT mode: Port {args.tty_file} is not a valid COM port!\n'

        return ''

    def check_args_tty(self, args):
        if not args.board_name:
            return 'TTY IUT mode: specify board_name\n'

        return self.find_tty(args)

    def check_args_qemu(self, args):
        if not args.qemu_bin:
            return 'QEMU IUT mode: specify qemu_bin parameter to use this mode\n'

        if not find_executable(args.qemu_bin):
            return f'QEMU IUT mode: qemu_bin={args.qemu_bin}, but not found!\n'

        if args.kernel_image:
            if not os.path.isfile(args.kernel_image):
                return f'QEMU IUT mode: kernel_image={repr(args.kernel_image)} is not a file!\n'
        elif not args.project_path:
            return 'QEMU IUT mode: specify kernel_image or project_path to use this IUT mode\n'

        return ''

    def check_args_native(self, args):
        if args.kernel_image:
            if not os.path.isfile(args.kernel_image):
                return f'Native IUT mode: kernel_image {repr(args.kernel_image)} is not a file!\n'
        elif not args.project_path:
            return 'Native IUT mode: specify kernel_image or project_path to use this IUT mode\n'

        if args.tty_file or args.tty_alias or args.debugger_snr:
            return self.find_tty(args)

        return ''

    def check_args_btpclient_path(self, args):
        if not os.path.exists(args.btpclient_path):
            return (
                f'btpclient: Path {repr(args.btpclient_path)} of btp client '
                'does not exist!\n'
            )
        return ''

    def check_args_btp_tcp_client(self, args):
        if not 49152 <= args.btp_tcp_port <= 65535:
            return (
                f'btp_tcp_client mode: Invalid server port number={args.btp_tcp_port}, expected '
                'range <49152,65535>'
            )
        return ''

    def get_iut_mode(self, args):
        # Specify IUT mode explicitly, or it will be inferred
        # from the parameters.
        if args.iut_mode:
            return args.iut_mode

        if args.qemu_bin:
            return 'qemu'

        if args.kernel_image or args.hid_serial or args.hci:
            return 'native'

        if args.btpclient_path:
            return 'btpclient_path'

        if args.btp_tcp_port:
            return 'btp_tcp_client'

        return 'tty'

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

        if args.btproxy_bin and not is_executable(args.btproxy_bin):
            return args, f'The btproxy_bin={args.btproxy_bin} is not an executable file'

        if args.btattach_bin and not is_executable(args.btattach_bin):
            return args, f'The btattach_bin={args.btattach_bin} is not an executable file'

        if args.ykush or args.active_hub_server:
            args.usb_replug_available = True
        else:
            args.usb_replug_available = False

        args.superguard = 60 * args.superguard

        if not args.ip_addr:
            args.ip_addr = ['127.0.0.1'] * len(args.srv_port)

        if not args.local_addr:
            args.local_addr = ['127.0.0.1'] * len(args.cli_port)

        args.iut_mode = self.get_iut_mode(args)
        if sys.platform == "win32" and args.iut_mode in ['qemu', 'native']:
            errmsg = f'The {args.iut_mode} mode is not supported under Windows!'
            return args, errmsg

        check_method = getattr(self, f'check_args_{args.iut_mode}')
        errmsg = check_method(args)

        if args.wid_run:
            self.wid_run_tcs(args)

        return args, errmsg


def is_executable(path):
    return os.path.exists(path) and os.access(path, os.X_OK)
