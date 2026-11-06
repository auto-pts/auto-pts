#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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

"""Definitions of config.py and CLI parameters"""
import argparse
import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from autopts.autopts_types import AutoPTSMode
from autopts.config import CLIENT_PORT, MAX_SERVER_RESTART_TIME, SERIAL_BAUDRATE, SERVER_PORT, IUTMode
from autopts.ptsprojects.testcase_db import DATABASE_FILE


@dataclass(slots=True)
class ConfigParameter:
    """Parameter that can be set in config.py and, if it has flags or
    is positional, in CLI.

    type is the value type, or the type of list items if nargs is set.
    Values of int and float parameters from config.py are converted
    to that type.
    """
    type: Any = str
    default: Any = None
    # Keys of the parameter in config.py, the parameter name by default
    config_key: list[str] | str | None = None
    # Can be set separately for each IUT
    iut_param: bool = False
    choices: list | None = None

    flags: list[str] = field(default_factory=list)
    positional: bool = False
    nargs: int | str | None = None
    action: str | None = None
    metavar: str | tuple[str, ...] | None = None
    # Not in CLI help
    cli_hidden: bool = False

    short_help: str = ''
    help: str = ''

    def get_default(self) -> Any:
        return copy.deepcopy(self.default)

    def convert(self, value: Any) -> Any:
        """Convert a config.py value to the parameter type."""
        if value is None or self.type not in (int, float):
            return value

        if isinstance(value, list):
            return [self.type(v) for v in value]

        return self.type(value)

    def get_argparse_kwargs(self) -> dict[str, Any]:
        """Return add_argument() kwargs for the flags."""
        kwargs: dict[str, Any] = {
            "help": argparse.SUPPRESS if self.cli_hidden else (self.short_help or self.help),
        }

        if self.type is bool:
            kwargs["action"] = "store_false" if self.default else "store_true"
            return kwargs

        kwargs["type"] = self.type
        for name in ("nargs", "action", "metavar", "choices"):
            value = getattr(self, name)
            if value is not None:
                kwargs[name] = value

        return kwargs


class ConfigDefinition:

    parameters = {
        "config_path": ConfigParameter(
            type=str,
            default="",
            positional=True,
            help="Path to bot config.py to use for testing."),

        "iut_mode": ConfigParameter(
            type=str,
            iut_param=True,
            choices=[IUTMode.TTY, IUTMode.NATIVE, IUTMode.QEMU,
                     IUTMode.BTPCLIENT_PATH, IUTMode.BTPCLIENT_TCP],
            flags=["--iut-mode", "--iut_mode"],
            nargs="+",
            action="extend",
            short_help="Specify the mode of the IUT.",
            help="Specify the mode of the IUT (Identity Under Test). "
                 "If the option is not provided, mode will be inferred "
                 "from the parameters.",
        ),

        "autopts_mode": ConfigParameter(
            type=str,
            default=AutoPTSMode.AUTO_TCP_IP,
            choices=[AutoPTSMode.AUTO_TCP_IP, AutoPTSMode.GUI_CLIENT_ONLY,
                     AutoPTSMode.FAKE_PROXY, AutoPTSMode.AUTO_CLIENT_ONLY],
            flags=["--autopts-mode", "--autopts_mode"],
            help="Specify AutoPTS client mode, which determines the method "
                 "of communication with the PTS.",
        ),

        "workspace": ConfigParameter(
            type=str,
            default="",
            positional=True,
            help="Path to PTS workspace file to use for testing. It should have pqw6 "
                 "extension. The file should be located on the machine, where automation "
                 "server is running."),

        "copy_workspace": ConfigParameter(
            type=bool,
            default=True,
            flags=["--nc"],
            help="Open the original PTS workspace instead of copying it. "
                 "Warning: workspace file might be modified by the PTS.",
        ),

        "srv_port": ConfigParameter(
            type=int,
            default=[SERVER_PORT],
            flags=["-S", "--srv_port"],
            nargs="+",
            help="Ports of the interface exposed by the AutoPTS servers. "
                 "One port corresponds to one PTS instance.",
        ),

        "cli_port": ConfigParameter(
            type=int,
            default=[CLIENT_PORT],
            flags=["-C", "--cli_port"],
            nargs="+",
            help="Ports of the callback interface exposed by AutoPTS client. "
                 "One port corresponds to one PTS instance.",
        ),

        "server_count": ConfigParameter(
            type=int,
            default=None,
            help="Number of PTS instances. Defaults to the number of cli_port.",
        ),

        "ip_addr": ConfigParameter(
            type=str,
            default=[],
            config_key="server_ip",
            flags=["-i", "--ip_addr"],
            nargs="+",
            help="IP addresses of the interface exposed by the AutoPTS servers. "
                 "One IP corresponds to one PTS instance.",
        ),

        "local_addr": ConfigParameter(
            type=str,
            default=[],
            config_key="local_ip",
            flags=["-l", "--local_addr"],
            nargs="+",
            short_help="Local IP addresses of the AutoPTS client.",
            help="Local IP addresses of the interface exposed by the AutoPTS servers. "
                 "One IP corresponds to one PTS instance.",
        ),

        "bd_addr": ConfigParameter(
            type=str,
            default="",
            flags=["-a", "--bd-addr"],
            short_help="Bluetooth device address of the IUT.",
            help="Bluetooth device address of the IUT.",
        ),

        "enable_max_logs": ConfigParameter(
            type=bool,
            default=False,
            flags=["-d", "--debug-logs"],
            short_help="Enable PTS maximum logging.",
            help="Enable the PTS maximum logging. Equivalent to running "
                 "test case in PTS GUI using 'Run (Debug Logs)'.",
        ),

        "test_cases": ConfigParameter(
            type=str,
            default=[],
            flags=["-c", "--test-cases"],
            nargs="+",
            action="extend",
            short_help="Names of test cases to run.",
            help="Names of test cases to run. Groups of test cases can "
                 "be specified by profile names. Option can be used multiple times.",
        ),

        "test_cases_file": ConfigParameter(
            type=argparse.FileType('r'),
            flags=["--test-cases-file"],
            short_help="Read test cases from a file.",
            help="A file containing test case names, one per line. "
                 "Use instead of the --test-cases/-c option.",
        ),

        "excluded": ConfigParameter(
            type=str,
            default=[],
            flags=["-e", "--excluded"],
            nargs="+",
            short_help="Names of test cases to exclude.",
            help="Names of test cases to exclude. Groups of test cases "
                 "can also be specified by profile names.",
        ),

        "test_case_limit": ConfigParameter(
            type=int,
            default=0,
            flags=["--test_case_limit"],
            short_help="Maximum number of test cases to execute.",
            help="Limit the number of executed test cases. "
                 "All remaining test cases will be skipped.",
        ),

        "retry": ConfigParameter(
            type=int,
            default=0,
            flags=["-r", "--retry"],
            short_help="Retry failed test cases.",
            help="Repeat a failed test case. The value specifies "
                 "the maximum number of retries per test case.",
        ),

        "no_retry_on_regression": ConfigParameter(
            type=bool,
            default=False,
            flags=["--no_retry_on_regression"],
            short_help="Retry only regression failures.",
            help="Retry failed test cases only if the failure is considered "
                 "a regression. Non-regression failures are not retried even "
                 "when the retry count is greater than zero.",
        ),

        "repeat_until_fail": ConfigParameter(
            type=bool,
            default=False,
            flags=["--repeat_until_fail"],
            short_help="Repeat until a test no longer passes.",
            help="Repeat each test case until the verdict is different from PASS.",
        ),

        "stress_test": ConfigParameter(
            type=bool,
            default=False,
            flags=["--stress_test"],
            short_help="Repeat all test cases. The repeat counter will be set to 'retry' parameter value.",
            help="Repeat every test case even if the previous execution passed. "
                 "The repeat counter will be set to 'retry' parameter value.",
        ),

        "tty_file": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["-t", "--tty-file"],
            nargs="+",
            action="extend",
            help="Use the specified TTY/COM device for BTP communication with the "
                 "IUT. QEMU and HCI modes are disabled when this option is used.",
        ),

        "tty_alias": ConfigParameter(
            type=str,
            default="",
            iut_param=True,
            flags=["--tty_alias"],
            nargs="+",
            action="extend",
            cli_hidden=True,
            short_help="TTY alias(es) to be resolved.",
        ),

        "tty_baudrate": ConfigParameter(
            type=int,
            default=SERIAL_BAUDRATE,
            iut_param=True,
            flags=["--tty-baudrate", "--tty_baudrate"],
            nargs="+",
            action="extend",
            short_help="TTY baudrate.",
            help="Baudrate used for TTY communication.",
        ),

        "net_tty_file": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--net-tty-file"],
            nargs="+",
            action="extend",
            help="TTY/COM device used to capture logs from the network core, "
                 "if the board exposes a separate serial port.",
        ),

        "device_core": ConfigParameter(
            type=str,
            default="NRF52840_XXAA",
            iut_param=True,
            flags=["--device_core"],
            nargs="+",
            action="extend",
            help="Device core used for J-Link related features such as RTT "
                 "logging and btmon.",
        ),

        "recovery": ConfigParameter(
            type=bool,
            default=False,
            flags=["--recovery"],
            short_help="Enable automatic recovery.",
            help="Specify if autoptsclient should try to recover itself "
                 "after a negative test status.",
        ),

        "not_recover": ConfigParameter(
            type=str,
            default=["PASS", "INCONC", "FAIL", "NOT_IMPLEMENTED", "INDCSV"],
            flags=["--not_recover"],
            nargs="+",
            short_help="Statuses that should not trigger recovery.",
            help="Specify test statuses for which autoptsclient should not "
                 "attempt recovery.",
        ),

        "superguard": ConfigParameter(
            type=float,
            default=0,
            flags=["--superguard"],
            metavar="MINUTES",
            short_help="Recovery timeout in minutes.",
            help="Specify the amount of time in minutes after which "
                 "SuperGuard will trigger recovery steps.",
        ),

        "dongle_init_retry": ConfigParameter(
            type=int,
            default=5,
            help="Number of PTS dongle initialization retries.",
        ),

        "max_server_restart_time": ConfigParameter(
            type=int,
            default=MAX_SERVER_RESTART_TIME,
            flags=["--max_server_restart_time"],
            cli_hidden=True,
            help="Maximum time allowed for restarting the automation server.",
        ),

        "ykush": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--ykush"],
            nargs="+",
            action="extend",
            metavar="YKUSH_PORT",
            short_help="YKUSH ports used during recovery.",
            help="Specify YKUSH downstream port numbers used during recovery "
                 "to power cycle the IUT device.",
        ),

        "rtscts": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--rtscts"],
            help="Enable UART RTS/CTS hardware flow control.",
        ),

        "debugger_snr": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["-j", "--jlink"],
            nargs="+",
            action="extend",
            help="Specify the J-Link serial number manually.",
        ),

        "board_name": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            config_key=["board", "board_name"],
            flags=["-b", "--board"],
            nargs="+",
            action="extend",
            short_help="Board name.",
            help="Board used for testing. The selected board determines the "
                 "board-specific reset and build/flash implementation.",
        ),

        "pylink_reset": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--pylink_reset"],
            help="Use pylink reset for board recovery/reset.",
        ),

        "store": ConfigParameter(
            type=bool,
            default=False,
            flags=["-s", "--store"],
            cli_hidden=True,
            help="Enable storing test results in TestCase.db.",
        ),

        "sudo": ConfigParameter(
            type=bool,
            default=False,
            flags=["--sudo"],
            cli_hidden=True,
            help="Allow running with with elevated privileges.",
        ),

        "database_file": ConfigParameter(
            type=str,
            default=DATABASE_FILE,
            flags=["--database-file"],
            cli_hidden=True,
            help="Path to the SQLite database file used for test results.",
        ),

        "ykush_replug_delay": ConfigParameter(
            type=float,
            default=3,
            iut_param=True,
            flags=["--ykush_replug_delay"],
            nargs="+",
            action="extend",
            cli_hidden=True,
            help="Time needed for the device to cool down after YKUSH power off.",
        ),

        "active_hub_server": ConfigParameter(
            type=list[dict],
            default=None,
            iut_param=True,
            help="Configuration of an external active USB hub server.",
        ),

        "usb_replug_available": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--usb-replug-available", "--usb_replug_available"],
            cli_hidden=True,
            help="Specify whether USB replug functionality is available.",
        ),

        "project_path": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--project_path"],
            cli_hidden=True,
            short_help="Project repository path.",
            help="Absolute path to the project repository containing "
                 "sources needed to build the tester application.",
        ),

        "tester_app_dir": ConfigParameter(
            type=Path,
            default=Path("tests", "bluetooth", "tester"),
            flags=["--tester_app_dir"],
            cli_hidden=True,
            short_help="Tester application directory.",
            help="Path to the tester application relative to project_path. "
                 "Used for build and flash in bot mode.",
        ),

        "pts_addr_map": ConfigParameter(
            type=dict,
            default={},
            help="Mapping of PTS instances to Bluetooth addresses.",
        ),

        "restricted_pts_addrs": ConfigParameter(
            type=list[str],
            default=[],
            help="List of Bluetooth addresses of the PTS dongles that will be used "
                 "only during test cases specified with pts_addr_map.",
        ),

        "pts_addr": ConfigParameter(
            type=str | list[str],
            default="",
            help="List of Bluetooth addresses of the PTS dongles. Required only "
                 f"for {AutoPTSMode.GUI_CLIENT_ONLY} mode.",
        ),

        "iut_targets": ConfigParameter(
            type=dict | list,
            default=None,
            help="Provide a dictionary containing multiple IUT targets configurations. "
                 "Required for test cases with multiple IUTs.",
        ),

        "iut_targets_args": ConfigParameter(
            type=dict,
            default={},
            help="Helper containing the parsed IUT targets configurations. Ignore.",
        ),

        "iut_target_selection": ConfigParameter(
            type=str,
            default=None,
            flags=["--iut_target_selection"],
            help="Mapping of IUT targets to specific test cases. Specify a dictionary with the mapping"
                 "or a path to a JSON file containing the dictionary.",
        ),

        "no_build": ConfigParameter(
            type=bool,
            default=False,
            flags=["--nb"],
            help="Skip build and flash steps in bot mode.",
        ),

        "btattach_bin": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--btattach-bin", "--btattach_bin"],
            help="Path to the btattach executable.",
        ),

        "btattach_at_every_test_case": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--btattach-at-every-test-case", "--btattach_at_every_test_case"],
            help="Restart btattach before executing every test case.",
        ),

        "btproxy_bin": ConfigParameter(
            type=str,
            default=None,
            flags=["--btproxy-bin", "--btproxy_bin"],
            help="Path to the btproxy executable.",
        ),

        "qemu_bin": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--qemu-bin", "--qemu_bin"],
            help="Path to the QEMU executable.",
        ),

        "qemu_options": ConfigParameter(
            type=str,
            default="-cpu cortex-m3 -machine lm3s6965evb",
            iut_param=True,
            flags=["--qemu-options", "--qemu_options"],
            nargs="+",
            action="extend",
            help="Additional command line options passed to QEMU.",
        ),

        "kernel_cpu": ConfigParameter(
            type=str,
            default="qemu_cortex_m3",
            iut_param=True,
            flags=["--kernel-cpu", "--kernel_cpu"],
            nargs="+",
            help="CPU type used when building the kernel image.",
        ),

        "hci": ConfigParameter(
            type=int,
            default=None,
            iut_param=True,
            flags=["--hci"],
            help="Specify the HCI controller number.",
        ),

        "hid_vid": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--hid-vid", "--hid_vid"],
            help="Specify the USB vendor ID of the HCI controller "
                 "(hexadecimal string).",
        ),

        "hid_pid": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--hid-pid", "--hid_pid"],
            help="Specify the USB product ID of the HCI controller "
                 "(hexadecimal string).",
        ),

        "hid_serial": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--hid-serial", "--hid_serial"],
            help="Specify the USB serial number of the HCI controller.",
        ),

        "btmgmt_bin": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--btmgmt-bin", "--btmgmt_bin"],
            help="Path to the btmgmt executable.",
        ),

        "setcap_cmd": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--setcap-cmd", "--setcap_cmd"],
            short_help="Command used to grant HCI capabilities.",
            help="Command used to grant the required Linux capabilities for native "
                 "HCI mode (for example using setcap).",
        ),

        "btmon": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--btmon"],
            short_help="Capture btmon logs.",
            help="Capture btsnoop logs over RTT and decode them with btmon. "
                 "Requires RTT support on the IUT.",
        ),

        "rtt_log": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--rtt-log"],
            short_help="Capture RTT logs.",
            help="Capture IUT logs from the RTT buffer. Requires RTT support "
                 "on the IUT.",
        ),

        "rtt_log_syncto": ConfigParameter(
            type=float,
            default=0,
            iut_param=True,
            flags=["--rtt-log-syncto"],
            help="Continue RTT logging for the specified number of seconds "
                 "after the test case finishes.",
        ),

        "gdb": ConfigParameter(
            type=bool,
            default=False,
            iut_param=True,
            flags=["--gdb"],
            help="Skip board resets to avoid disconnecting the GDB server.",
        ),

        "btp_tcp_ip": ConfigParameter(
            type=str,
            default="127.0.0.1",
            iut_param=True,
            flags=["--btp-tcp-ip", "--btp_tcp_ip"],
            nargs="+",
            action="extend",
            help="IP address of the external BTP client.",
        ),

        "btp_tcp_port": ConfigParameter(
            type=int,
            default=None,
            iut_param=True,
            flags=["--btp-tcp-port", "--btp_tcp_port"],
            nargs="+",
            action="extend",
            help="TCP port used by the external BTP client.",
        ),

        "btpclient_path": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--btpclient-path", "--btpclient_path"],
            nargs="+",
            action="extend",
            help="Path to the external BTP client executable.",
        ),

        "wid_run": ConfigParameter(
            type=str,
            default=None,
            flags=["--wid_run", "--wid-run"],
            nargs=2,
            metavar=("SERVICE", "WID"),
            help="Run all test cases from the selected service/profile that "
                 "use the specified WID.",
        ),

        "external_audio": ConfigParameter(
            type=str,
            default=None,
            flags=["--external-audio"],
            help="Type of external audio support to use.",
        ),

        "kernel_image": ConfigParameter(
            type=str,
            default=None,
            iut_param=True,
            flags=["--kernel-image", "--kernel_image"],
            positional=True,
            nargs="+",
            action="extend",
            help="OS kernel image to be used for testing, e.g. elf file for qemu, exe for native."),

        "cron_optim": ConfigParameter(
            type=bool,
            default=False,
            help="Terminate PTS.exe and Fts.exe before pulling PTS logs from autopts server",
        ),

        "simple_mode": ConfigParameter(
            type=bool,
            default=False,
            flags=["--simple"],
            help="Start testing with the simple client layer. Allows for using bot config file without entering "
                 "Bot layers, so it skips build-and-flash stage and postprocessing logs.",
        ),

        "use_backup": ConfigParameter(
            type=bool,
            default=False,
            help="The bot collects a backup of the stats, so in case of unexpected termination "
                 "the bot can continue the test series from the test case where it was interrupted. "
                 "Useful with a cron that can detect the bot's crash or freeze and restart it automatically.",
        ),

        "wid_usage": ConfigParameter(
            type=bool,
            default=False,
            help="Generate a csv wid report with specific wids and tests using them.",
        ),

        "project_repos": ConfigParameter(
            type=list[str],
            default=None,
            config_key=["repos", "project_repos"],
            help="An additional argument that is used for build and flash stage. "
                 "Its usage is board-specific.",
        ),

        "server_args": ConfigParameter(
            type=str,
            default=None,
            help="autopts server arguments used in AUTO_CLIENT_ONLY mode.",
        ),

        "build_env_cmd": ConfigParameter(
            type=str,
            default=None,
            help="Add the `build_env_cmd` option to allow configuring a shell command that "
                 "activates the environment before running `west build` or `west flash`.",
        ),
    }


def get_config_values(config: dict[str, Any]) -> dict[str, Any]:
    """Return values of all parameters from config.py dictionary.

    Parameters missing in config get their default values.
    """
    values = {}

    for name, parameter in ConfigDefinition.parameters.items():
        keys = parameter.config_key or name
        if isinstance(keys, str):
            keys = [keys]

        key = next((k for k in keys if k in config), None)
        if key is None:
            values[name] = parameter.get_default()
        else:
            values[name] = parameter.convert(config[key])

    return values
