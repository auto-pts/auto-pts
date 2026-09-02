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

"""Configuration variables"""
import argparse
import os.path
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from autopts.autopts_types import AutoPTSMode
from autopts.ptsprojects.testcase_db import DATABASE_FILE

SERVER_PORT = 65000
CLIENT_PORT = 65001
BTMON_PORT = 65432

MAX_SERVER_RESTART_TIME = 120

SERIAL_BAUDRATE = int(os.getenv("AUTOPTS_SERIAL_BAUDRATE", "115200"))

AUTOPTS_ROOT_DIR = os.path.dirname(  # auto-pts repo directory
                os.path.dirname(  # autopts module directory
                    os.path.abspath(__file__)))  # this file directory

FILE_PATHS = {}


def generate_file_paths(file_paths=None, autopts_root_dir=AUTOPTS_ROOT_DIR):
    if file_paths and 'TMP_DIR' in file_paths:
        FILE_PATHS['TMP_DIR'] = file_paths['TMP_DIR']
    else:
        FILE_PATHS['TMP_DIR'] = os.path.join(autopts_root_dir, 'tmp')

    FILE_PATHS.update({
        'ALL_STATS_RESULTS_XML_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'all_stats_results.xml'),
        'TC_STATS_RESULTS_XML_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'tc_stats_results.xml'),
        'TEST_CASES_JSON_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'test_cases_file.json'),
        'ALL_STATS_JSON_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'all_stats.json'),
        'TC_STATS_JSON_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'tc_stats.json'),
        'TEST_CASE_DB_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'TestCase.db'),
        'BOT_STATE_JSON_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'bot_state.json'),
        'BOT_STATE_DIR': os.path.join(FILE_PATHS['TMP_DIR'], 'final_state'),
        'REPORT_README_MD_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'README.md'),
        'REPORT_DIR': os.path.join(FILE_PATHS['TMP_DIR'], 'autopts_report'),
        'IUT_LOGS_DIR': os.path.join(autopts_root_dir, 'logs'),
        'OLD_LOGS_DIR': os.path.join(autopts_root_dir, 'oldlogs'),
        'PTS_XMLS_DIR': os.path.join(FILE_PATHS['TMP_DIR'], 'XMLs'),
        'REPORT_XLSX_FILE': os.path.join(autopts_root_dir, "report.xlsx"),
        'REPORT_TXT_FILE': os.path.join(autopts_root_dir, "report.txt"),
        'REPORT_DIFF_TXT_FILE': os.path.join(FILE_PATHS['TMP_DIR'], "report-diff.txt"),
        'ERROR_TXT_FILE': os.path.join(FILE_PATHS['TMP_DIR'], 'error.txt'),
        'WID_USE_CSV_FILE': os.path.join(AUTOPTS_ROOT_DIR, 'wid_usage_report.csv'),
        # 'BOT_LOG_FILE': os.path.join(autopts_root_dir, 'autoptsclient_bot.log'),
    })

    if file_paths:
        FILE_PATHS.update(file_paths)

    return FILE_PATHS


generate_file_paths({}, AUTOPTS_ROOT_DIR)


class IUTMode(str, Enum):
    TTY = 'tty'
    QEMU = 'qemu'
    NATIVE = 'native'
    BTPCLIENT_PATH = 'btpclient_path'
    BTPCLIENT_TCP = 'btpclient_tcp'


class ConfigCategory(str, Enum):
    GENERAL = 'General'
    CONNECTION = 'Connection'
    LOGGING = 'Logging'
    RECOVERY = 'Recovery'
    TEST_CASE_EXECUTION = 'Test Case Execution'
    DATABASE = 'Database'
    HARDWARE = 'Hardware'
    QEMU = 'QEMU'
    HCI = 'HCI'
    BUILD = 'Build'
    PTS = 'PTS'
    OTHER = 'Other'


@dataclass(slots=True)
class CliArgument:
    flags: list[str] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)


@dataclass(slots=True)
class ConfigParameter:
    default_factory: Callable[[argparse.Namespace], Any] | None = None
    data_type: Any = Any
    config_key: list[str] | str | None = None
    default: Any = None
    iut_param: bool = False
    category: ConfigCategory = ConfigCategory.GENERAL
    hidden: bool = False

    choices: list | None = None
    cli_example: str | None = None
    config_file_example: float | int | str | bool | dict | list | None = None

    short_help: str = ''
    help: str = ''
    cli: CliArgument | list[CliArgument] | None = None

    def get_value(self, namespace):
        values = [
            getattr(namespace, cli.kwargs["dest"], None)
            for cli in self.cli
        ]

        values = [v for v in values if v is not None]

        if not values:
            return None

        if all(isinstance(v, list) for v in values):
            result = []
            for v in values:
                result.extend(v)
            return result

        if len(values) == 1:
            return values[0]

        raise ValueError("Multiple CLI representations supplied")

    @staticmethod
    def get_argparse_type(data_type: Any):
        origin = get_origin(data_type)

        if origin is list:
            return get_args(data_type)[0]

        if origin is tuple:
            raise NotImplementedError

        if origin is None:
            return data_type

        return str


class ParameterMissingException(Exception):
    pass


def parameter_missing(cfg, name):
    raise ParameterMissingException(f"Missing a required config parameter: {name}")


class ConfigDefinition:

    parameters = {
        "config_path": ConfigParameter(
            data_type=str,
            default="",
            category=ConfigCategory.GENERAL,
            cli=CliArgument(
                kwargs={
                    "nargs": "?",
                    "type": str,
                },
            ),
            cli_example="path/to/my_bot_config.py",
            help="Path to bot config.py to use for testing."),

        "iut_mode": ConfigParameter(
            data_type=list[str],
            category=ConfigCategory.GENERAL,
            iut_param=True,
            choices=[IUTMode.TTY, IUTMode.NATIVE, IUTMode.QEMU,
                     IUTMode.BTPCLIENT_PATH, IUTMode.BTPCLIENT_TCP],
            cli=CliArgument(
                flags=["--iut-mode", "--iut_mode"],
                kwargs={
                    "nargs": "+",
                    "action": "extend",
                    "type": str,
                },
            ),
            short_help="Specify the mode of the IUT.",
            help="Specify the mode of the IUT (Identity Under Test). "
                 "If the option is not provided, mode will be inferred "
                 "from the parameters.",
        ),

        "autopts_mode": ConfigParameter(
            data_type=str,
            default=AutoPTSMode.AUTO_TCP_IP,
            category=ConfigCategory.GENERAL,
            choices=[AutoPTSMode.AUTO_TCP_IP, AutoPTSMode.GUI_CLIENT_ONLY,
                     AutoPTSMode.FAKE_PROXY, AutoPTSMode.AUTO_CLIENT_ONLY],
            cli=CliArgument(
                flags=["--autopts-mode", "--autopts_mode"],
                kwargs={
                    "type": str,
                }
            ),
            help="Specify AutoPTS client mode, which determines the method "
                 "of communication with the PTS.",
        ),

        "workspace": ConfigParameter(
            data_type=str,
            default="",
            category=ConfigCategory.GENERAL,
            cli=CliArgument(
                kwargs={
                    "nargs": "?",
                    "type": str,
                },
            ),
            cli_example="autoptsclient-zephyr.py path/to/zephyr.pqw6",
            config_file_example="path/to/zephyr.pqw6",
            help="Path to PTS workspace file to use for testing. It should have pqw6 "
                 "extension. The file should be located on the machine, where automation "
                 "server is running."),

        "copy_workspace": ConfigParameter(
            data_type=bool,
            default=True,
            category=ConfigCategory.GENERAL,
            cli=CliArgument(
                flags=["--nc"],
                kwargs={
                    "dest": "copy_workspace",
                    "action": "store_false",
                },
            ),
            help="Open the original PTS workspace instead of copying it. "
                 "Warning: workspace file might be modified by the PTS.",
        ),

        "srv_port": ConfigParameter(
            data_type=list[int],
            default=[SERVER_PORT],
            category=ConfigCategory.CONNECTION,
            cli=CliArgument(
                flags=["-S", "--srv_port"],
                kwargs={
                    "nargs": "+",
                    "type": int,
                },
            ),
            cli_example="65000 65002 65004",
            config_file_example=[65000, 65002, 65004],
            help="Ports of the interface exposed by the AutoPTS servers. "
                 "One port corresponds to one PTS instance.",
        ),

        "cli_port": ConfigParameter(
            data_type=list[int],
            default=[CLIENT_PORT],
            category=ConfigCategory.CONNECTION,
            cli=CliArgument(
                flags=["-C", "--cli_port"],
                kwargs={
                    "nargs": "+",
                    "type": int,
                },
            ),
            cli_example="65001 65003 65005",
            config_file_example=[65001, 65003, 65005],
            help="Ports of the callback interface exposed by AutoPTS client. "
                 "One port corresponds to one PTS instance.",
        ),

        "ip_addr": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.CONNECTION,
            config_key="server_ip",
            cli=CliArgument(
                flags=["-i", "--ip_addr"],
                kwargs={
                    "nargs": "+",
                    "type": str,
                },
            ),
            cli_example="192.168.2.2 192.168.2.2",
            config_file_example="192.168.2.2 192.168.2.2",
            help="IP addresses of the interface exposed by the AutoPTS servers. "
                 "One IP corresponds to one PTS instance.",
        ),

        "local_addr": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.CONNECTION,
            config_key="local_ip",
            cli=CliArgument(
                flags=["-l", "--local_addr"],
                kwargs={
                    "nargs": "+",
                    "type": str,
                },
            ),
            cli_example="192.168.2.1 192.168.2.1",
            config_file_example="192.168.2.1 192.168.2.1",
            short_help="Local IP addresses of the AutoPTS client.",
            help="Local IP addresses of the interface exposed by the AutoPTS servers. "
                 "One IP corresponds to one PTS instance.",
        ),

        "bd_addr": ConfigParameter(
            data_type=str,
            default="",
            category=ConfigCategory.GENERAL,
            cli=CliArgument(
                flags=["-a", "--bd-addr"],
                kwargs={
                    "type": str,
                }
            ),
            cli_example="12:34:56:65:43:21",
            config_file_example="12:34:56:65:43:21",
            short_help="Bluetooth device address of the IUT.",
            help="Bluetooth device address of the IUT.",
        ),

        "enable_max_logs": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.LOGGING,
            cli=CliArgument(
                flags=["-d", "--debug-logs"],
                kwargs={
                    "dest": "enable_max_logs",
                    "action": "store_true",
                },
            ),
            short_help="Enable PTS maximum logging.",
            help="Enable the PTS maximum logging. Equivalent to running "
                 "test case in PTS GUI using 'Run (Debug Logs)'.",
        ),

        "test_cases": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["-c", "--test-cases"],
                kwargs={
                    "nargs": "+",
                    "action": "extend",
                    "type": str,
                },
            ),
            cli_example="GAP/BROB/BCST/BV-01-C GAP/CONN",
            config_file_example=["GAP/BROB/BCST/BV-01-C", "GAP/CONN"],
            short_help="Names of test cases to run.",
            help="Names of test cases to run. Groups of test cases can "
                 "be specified by profile names. Option can be used multiple times.",
        ),

        "test_cases_file": ConfigParameter(
            data_type=Path,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--test-cases-file"],
                kwargs={
                    "type": argparse.FileType("r"),
                },
            ),
            cli_example="path/to/testcases.txt",
            config_file_example="path/to/testcases.txt",
            short_help="Read test cases from a file.",
            help="A file containing test case names, one per line. "
                 "Use instead of the --test-cases/-c option.",
        ),

        "excluded": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["-e", "--excluded"],
                kwargs={
                    "nargs": "+",
                    "type": str,
                },
            ),
            cli_example="GAP/BROB/BCST/BV-01-C GAP/CONN",
            config_file_example=["GAP/BROB/BCST/BV-01-C", "GAP/CONN"],
            short_help="Names of test cases to exclude.",
            help="Names of test cases to exclude. Groups of test cases "
                 "can also be specified by profile names.",
        ),

        "test_case_limit": ConfigParameter(
            data_type=int,
            default=0,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--test_case_limit"],
                kwargs={"type": int}
            ),
            cli_example="100",
            config_file_example=100,
            short_help="Maximum number of test cases to execute.",
            help="Limit the number of executed test cases. "
                 "All remaining test cases will be skipped.",
        ),

        "retry": ConfigParameter(
            data_type=int,
            default=0,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["-r", "--retry"],
                kwargs={"type": int},
            ),
            cli_example="3",
            config_file_example=3,
            short_help="Retry failed test cases.",
            help="Repeat a failed test case. The value specifies "
                 "the maximum number of retries per test case.",
        ),

        "no_retry_on_regression": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--no_retry_on_regression"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Retry only regression failures.",
            help="Retry failed test cases only if the failure is considered "
                 "a regression. Non-regression failures are not retried even "
                 "when the retry count is greater than zero.",
        ),

        "repeat_until_fail": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--repeat_until_fail"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Repeat until a test no longer passes.",
            help="Repeat each test case until the verdict is different from PASS.",
        ),

        "stress_test": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--stress_test"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Repeat all test cases. The repeat counter will be set to 'retry' parameter value.",
            help="Repeat every test case even if the previous execution passed. "
                 "The repeat counter will be set to 'retry' parameter value.",
        ),

        "tty_file": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["-t", "--tty-file"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="/dev/ttyACM0",
            help="Use the specified TTY/COM device for BTP communication with the "
                 "IUT. QEMU and HCI modes are disabled when this option is used.",
        ),

        "tty_alias": ConfigParameter(
            data_type=list[str],
            default="",
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--tty_alias"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example="/dev/serial/by-id/usb-SEGGER_J-Link_001234567890-if02",
            short_help="TTY alias(es) to be resolved.",
        ),

        "tty_baudrate": ConfigParameter(
            data_type=list[int],
            default=SERIAL_BAUDRATE,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--tty-baudrate", "--tty_baudrate"],
                kwargs={
                    "type": int,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="115200",
            config_file_example=115200,
            short_help="TTY baudrate.",
            help="Baudrate used for TTY communication.",
        ),

        "net_tty_file": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--net-tty-file"],
                kwargs={
                    "dest": "net_tty_file",
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="/dev/ttyACM1",
            help="TTY/COM device used to capture logs from the network core, "
                 "if the board exposes a separate serial port.",
        ),

        "device_core": ConfigParameter(
            data_type=list[str],
            default="NRF52840_XXAA",
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--device_core"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="NRF52840_XXAA",
            help="Device core used for J-Link related features such as RTT "
                 "logging and btmon.",
        ),

        "recovery": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.RECOVERY,
            cli=CliArgument(
                flags=["--recovery"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Enable automatic recovery.",
            help="Specify if autoptsclient should try to recover itself "
                 "after a negative test status.",
        ),

        "not_recover": ConfigParameter(
            data_type=list[str],
            default=["PASS", "INCONC", "FAIL", "NOT_IMPLEMENTED", "INDCSV"],
            category=ConfigCategory.RECOVERY,
            cli=CliArgument(
                flags=["--not_recover"],
                kwargs={
                    "nargs": "+",
                    "type": str,
                },
            ),
            cli_example='"PASS" "BTP ERROR"',
            config_file_example=["PASS", "BTP ERROR"],
            short_help="Statuses that should not trigger recovery.",
            help="Specify test statuses for which autoptsclient should not "
                 "attempt recovery.",
        ),

        "superguard": ConfigParameter(
            data_type=float,
            default=0,
            category=ConfigCategory.RECOVERY,
            cli=CliArgument(
                flags=["--superguard"],
                kwargs={
                    "type": float,
                    "metavar": "MINUTES",
                },
            ),
            cli_example="15",
            short_help="Recovery timeout in minutes.",
            help="Specify the amount of time in minutes after which "
                 "SuperGuard will trigger recovery steps.",
        ),

        "max_server_restart_time": ConfigParameter(
            data_type=int,
            default=MAX_SERVER_RESTART_TIME,
            category=ConfigCategory.RECOVERY,
            cli=CliArgument(
                flags=["--max_server_restart_time"],
                kwargs={
                    "type": int,
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example=f"{MAX_SERVER_RESTART_TIME}",
            help="Maximum time allowed for restarting the automation server.",
        ),

        "ykush": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.RECOVERY,
            iut_param=True,
            cli=CliArgument(
                flags=["--ykush"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                    "metavar": "YKUSH_PORT",
                },
            ),
            cli_example="1 3",
            short_help="YKUSH ports used during recovery.",
            help="Specify YKUSH downstream port numbers used during recovery "
                 "to power cycle the IUT device.",
        ),

        "rtscts": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--rtscts"],
                kwargs={
                    "dest": "rtscts",
                    "action": "store_true",
                },
            ),
            help="Enable UART RTS/CTS hardware flow control.",
        ),

        "debugger_snr": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["-j", "--jlink"],
                kwargs={
                    "dest": "debugger_snr",
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="1050123456",
            help="Specify the J-Link serial number manually.",
        ),

        "board_name": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            config_key=["board", "board_name"],
            cli=CliArgument(
                flags=["-b", "--board"],
                kwargs={
                    "dest": "board_name",
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            short_help="Board name.",
            help="Board used for testing. The selected board determines the "
                 "board-specific reset and build/flash implementation.",
        ),

        "pylink_reset": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--pylink_reset"],
                kwargs={
                    "action": "store_true",
                },
            ),
            help="Use pylink reset for board recovery/reset.",
        ),

        "store": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.DATABASE,
            cli=CliArgument(
                flags=["-s", "--store"],
                kwargs={
                    "action": "store_true",
                    "help": argparse.SUPPRESS,
                },
            ),
            help="Enable storing test results in TestCase.db.",
        ),

        "sudo": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.OTHER,
            cli=CliArgument(
                flags=["--sudo"],
                kwargs={
                    "action": "store_true",
                    "help": argparse.SUPPRESS,
                },
            ),
            help="Allow running with with elevated privileges.",
        ),

        "database_file": ConfigParameter(
            data_type=str,
            default=DATABASE_FILE,
            category=ConfigCategory.DATABASE,
            cli=CliArgument(
                flags=["--database-file"],
                kwargs={
                    "type": str,
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example=f"{DATABASE_FILE}",
            help="Path to the SQLite database file used for test results.",
        ),

        "ykush_replug_delay": ConfigParameter(
            data_type=list[float],
            default=3,
            category=ConfigCategory.RECOVERY,
            iut_param=True,
            cli=CliArgument(
                flags=["--ykush_replug_delay"],
                kwargs={
                    "type": float,
                    "nargs": "+",
                    "action": "extend",
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example="3",
            help="Time needed for the device to cool down after YKUSH power off.",
        ),

        "active_hub_server": ConfigParameter(
            data_type=list[dict],
            default=None,
            category=ConfigCategory.RECOVERY,
            iut_param=True,
            config_file_example={
                'ip': '127.0.0.1',
                'tcp_port': 65100,
                'usb_port': 4,
                'replug_delay': 5,
            },
            help="Configuration of an external active USB hub server.",
        ),

        "usb_replug_available": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.RECOVERY,
            iut_param=True,
            cli=CliArgument(
                flags=["--usb-replug-available", "--usb_replug_available"],
                kwargs={
                    "action": "store_true",
                },
            ),
            help="Specify whether USB replug functionality is available.",
        ),

        "project_path": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.BUILD,
            iut_param=True,
            cli=CliArgument(
                flags=["--project_path"],
                kwargs={
                    "type": str,
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example="path/to/tester/dir",
            short_help="Project repository path.",
            help="Absolute path to the project repository containing "
                 "sources needed to build the tester application.",
        ),

        "tester_app_dir": ConfigParameter(
            data_type=Path,
            default=Path("tests", "bluetooth", "tester"),
            category=ConfigCategory.BUILD,
            cli=CliArgument(
                flags=["--tester_app_dir"],
                kwargs={
                    "type": Path,
                    "help": argparse.SUPPRESS,
                },
            ),
            cli_example="path/to/tester/dir",
            short_help="Tester application directory.",
            help="Path to the tester application relative to project_path. "
                 "Used for build and flash in bot mode.",
        ),

        "pts_addr_map": ConfigParameter(
            data_type=dict,
            default_factory=dict,
            category=ConfigCategory.GENERAL,
            help="Mapping of PTS instances to Bluetooth addresses.",
            config_file_example={
                'GAP/CONN/CPUP/BV-08-C': '12:34:56:65:43:21',
                'GAP/CONN/CPUP/BV-10-C': '12:34:56:65:43:21',
            },
        ),

        "restricted_pts_addrs": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.GENERAL,
            config_file_example=['12:34:56:65:43:21'],
            help="List of Bluetooth addresses of the PTS dongles that will be used "
                 "only during test cases specified with pts_addr_map.",
        ),

        "pts_addr": ConfigParameter(
            data_type=list[str],
            default_factory=list,
            category=ConfigCategory.GENERAL,
            config_file_example=['12:34:56:65:43:21'],
            help="List of Bluetooth addresses of the PTS dongles. Required only "
                 f"for {AutoPTSMode.GUI_CLIENT_ONLY} mode.",
        ),

        "iut_targets": ConfigParameter(
            data_type=dict | list,
            default=None,
            category=ConfigCategory.GENERAL,
            config_file_example=[
                {
                    'name': 'iut0',
                    'board': 'nrf54l',
                    'kernel_cpu': 'native_sim',
                    'setcap_cmd': 'sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep '
                                  '/path/to/zephyr.exe',
                    'tty_baudrate': 1000000,
                    'tty_alias': '/dev/serial/by-id/usb-SEGGER_J-Link_001234567890-if02',
                    'debugger_snr': '1234567890',
                    'device_core': 'Cortex-M33',
                    'build_env_cmd': 'source /path/to/.venv/bin/activate',
                    'hci': 0,
                    'active_hub_server': {
                        'ip': '127.0.0.1',
                        'tcp_port': 65100,
                        'usb_port': 4,
                        'replug_delay': 5,
                    },
                    'btmon': True,
                },
                {
                    'name': 'iut1',
                    'board': 'nrf54l',
                    'kernel_cpu': 'native_sim',
                    'setcap_cmd': 'sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep '
                                  '/path/to/zephyr.exe',
                    'tty_baudrate': 1000000,
                    'tty_alias': '/dev/serial/by-id/usb-SEGGER_J-Link_009876543210-if02',
                    'debugger_snr': '9876543210',
                    'device_core': 'Cortex-M33',
                    'build_env_cmd': 'source /path/to/.venv/bin/activate',
                    'hci': 1,
                    'btmon': True,
                }
            ],
            help="Provide a dictionary containing multiple IUT targets configurations. "
                 "Required for test cases with multiple IUTs.",
        ),

        "iut_targets_args": ConfigParameter(
            data_type=dict,
            default_factory=dict,
            category=ConfigCategory.GENERAL,
            hidden=True,
            help="Helper containing the parsed IUT targets configurations. Ignore.",
        ),

        "iut_target_selection": ConfigParameter(
            data_type=dict | str,
            default=None,
            category=ConfigCategory.GENERAL,
            cli=CliArgument(
                flags=["--iut_target_selection"],
                kwargs={"type": str},
            ),
            cli_example="path/to/targets.json",
            config_file_example={
                'default_iut_map': {
                    0: 'iut0',
                },
                'rules': [
                    {
                        'iut_map': {
                            0: 'iut1',
                        },
                        'test_cases': [
                            'GAP/CONN/CPUP/BV-08-C',
                            'GAP/CONN/CPUP/BV-10-C',
                        ],
                    },
                    {
                        'iut_map': {
                            0: 'iut1',
                            1: 'iut0',
                        },
                        'test_cases': [
                            'CSIP/SR/SP/BV-06-C',
                        ],
                    }
                ]
            },
            help="Mapping of IUT targets to specific test cases. Specify a dictionary with the mapping"
                 "or a path to a JSON file containing the dictionary.",
        ),

        "no_build": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.BUILD,
            cli=CliArgument(
                flags=["--nb"],
                kwargs={
                    "dest": "no_build",
                    "action": "store_true",
                },
            ),
            help="Skip build and flash steps in bot mode.",
        ),

        "btattach_bin": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=["--btattach-bin", "--btattach_bin"],
                kwargs={"type": str},
            ),
            cli_example="/usr/bin/btattach",
            help="Path to the btattach executable.",
        ),

        "btattach_at_every_test_case": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.HARDWARE,
            iut_param=True,
            cli=CliArgument(
                flags=[
                    "--btattach-at-every-test-case",
                    "--btattach_at_every_test_case",
                ],
                kwargs={
                    "action": "store_true",
                },
            ),
            help="Restart btattach before executing every test case.",
        ),

        "btproxy_bin": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.HARDWARE,
            cli=CliArgument(
                flags=["--btproxy-bin", "--btproxy_bin"],
                kwargs={"type": str},
            ),
            cli_example="/usr/bin/btproxy",
            help="Path to the btproxy executable.",
        ),

        "qemu_bin": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.QEMU,
            iut_param=True,
            cli=CliArgument(
                flags=["--qemu-bin", "--qemu_bin"],
                kwargs={"type": str},
            ),
            cli_example="/usr/bin/qemu-system-arm",
            help="Path to the QEMU executable.",
        ),

        "qemu_options": ConfigParameter(
            data_type=list[str],
            default="",
            category=ConfigCategory.QEMU,
            iut_param=True,
            cli=CliArgument(
                flags=["--qemu-options", "--qemu_options"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="-cpu cortex-m3 -machine lm3s6965evb",
            help="Additional command line options passed to QEMU.",
        ),

        "kernel_cpu": ConfigParameter(
            data_type=list[str],
            default="qemu_cortex_m3",
            category=ConfigCategory.QEMU,
            iut_param=True,
            cli=CliArgument(
                flags=["--kernel-cpu", "--kernel_cpu"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                },
            ),
            cli_example="qemu_cortex_m3",
            help="CPU type used when building the kernel image.",
        ),

        "hci": ConfigParameter(
            data_type=list[int],
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--hci"],
                kwargs={
                    "type": int,
                },
            ),
            cli_example="0",
            help="Specify the HCI controller number.",
        ),

        "hid_vid": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--hid-vid", "--hid_vid"],
                kwargs={"type": str},
            ),
            cli_example="2fe3",
            help="Specify the USB vendor ID of the HCI controller "
                 "(hexadecimal string).",
        ),

        "hid_pid": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--hid-pid", "--hid_pid"],
                kwargs={"type": str},
            ),
            cli_example="000b",
            help="Specify the USB product ID of the HCI controller "
                 "(hexadecimal string).",
        ),

        "hid_serial": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--hid-serial", "--hid_serial"],
                kwargs={"type": str},
            ),
            cli_example="1234567890123456",
            help="Specify the USB serial number of the HCI controller.",
        ),

        "btmgmt_bin": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--btmgmt-bin", "--btmgmt_bin"],
                kwargs={"type": str},
            ),
            cli_example="/usr/bin/btmgmt",
            help="Path to the btmgmt executable.",
        ),

        "setcap_cmd": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.HCI,
            iut_param=True,
            cli=CliArgument(
                flags=["--setcap-cmd", "--setcap_cmd"],
                kwargs={"type": str},
            ),
            cli_example="sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe",
            short_help="Command used to grant HCI capabilities.",
            help="Command used to grant the required Linux capabilities for native "
                 "HCI mode (for example using setcap).",
        ),

        "btmon": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.LOGGING,
            iut_param=True,
            cli=CliArgument(
                flags=["--btmon"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Capture btmon logs.",
            help="Capture btsnoop logs over RTT and decode them with btmon. "
                 "Requires RTT support on the IUT.",
        ),

        "rtt_log": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.LOGGING,
            iut_param=True,
            cli=CliArgument(
                flags=["--rtt-log"],
                kwargs={
                    "action": "store_true",
                },
            ),
            short_help="Capture RTT logs.",
            help="Capture IUT logs from the RTT buffer. Requires RTT support "
                 "on the IUT.",
        ),

        "rtt_log_syncto": ConfigParameter(
            data_type=float,
            default=0,
            category=ConfigCategory.LOGGING,
            iut_param=True,
            cli=CliArgument(
                flags=["--rtt-log-syncto"],
                kwargs={
                    "type": float,
                },
            ),
            cli_example="5",
            help="Continue RTT logging for the specified number of seconds "
                 "after the test case finishes.",
        ),

        "gdb": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.OTHER,
            iut_param=True,
            cli=CliArgument(
                flags=["--gdb"],
                kwargs={
                    "action": "store_true",
                },
            ),
            help="Skip board resets to avoid disconnecting the GDB server.",
        ),

        "btp_tcp_ip": ConfigParameter(
            data_type=list[str],
            default="127.0.0.1",
            category=ConfigCategory.CONNECTION,
            iut_param=True,
            cli=CliArgument(
                flags=["--btp-tcp-ip", "--btp_tcp_ip"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="127.0.0.1",
            help="IP address of the external BTP client.",
        ),

        "btp_tcp_port": ConfigParameter(
            data_type=list[int],
            default=None,
            category=ConfigCategory.CONNECTION,
            iut_param=True,
            cli=CliArgument(
                flags=["--btp-tcp-port", "--btp_tcp_port"],
                kwargs={
                    "type": int,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="9000",
            help="TCP port used by the external BTP client.",
        ),

        "btpclient_path": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.CONNECTION,
            iut_param=True,
            cli=CliArgument(
                flags=["--btpclient-path", "--btpclient_path"],
                kwargs={
                    "type": str,
                    "nargs": "+",
                    "action": "extend",
                },
            ),
            cli_example="/path/to/btpclient",
            help="Path to the external BTP client executable.",
        ),

        "wid_run": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            cli=CliArgument(
                flags=["--wid_run", "--wid-run"],
                kwargs={
                    "type": str,
                    "nargs": 2,
                    "metavar": ("SERVICE", "WID"),
                },
            ),
            cli_example="GAP 35",
            help="Run all test cases from the selected service/profile that "
                 "use the specified WID.",
        ),

        "external_audio": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.HARDWARE,
            cli=CliArgument(
                flags=["--external-audio"],
                kwargs={
                    "type": str,
                },
            ),
            cli_example="wireplumber",
            help="Type of external audio support to use.",
        ),

        "kernel_image": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.BUILD,
            cli=[
                CliArgument(
                    flags=["--kernel-image", "--kernel_image"],
                    kwargs={
                        "nargs": "+",
                        "action": "extend",
                        "type": str,
                    },
                ),
                CliArgument(
                    kwargs={
                        "nargs": "?",
                        "dest": "kernel_image_positional",
                        "type": str,
                    },
                ),
            ],
            cli_example="autoptsclient-zephyr.py path/to/zephyr.pqw6 path/to/zephyr.exe",
            config_file_example="path/to/zephyr.exe",
            help="OS kernel image to be used for testing, e.g. elf file for qemu, exe for native."),

        "cron_optim": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.OTHER,
            config_file_example=True,
            help="Terminate PTS.exe and Fts.exe before pulling PTS logs from autopts server",
        ),

        "simple_mode": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.OTHER,
            config_file_example=True,
            help="Start testing with the simple client layer. Allows for using bot config file without entering "
                 "Bot layers, so it skips build-and-flash stage and postprocessing logs.",
        ),

        "use_backup": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.RECOVERY,
            config_file_example=True,
            help="The bot collects a backup of the stats, so in case of unexpected termination "
                 "the bot can continue the test series from the test case where it was interrupted. "
                 "Useful with a cron that can detect the bot's crash or freeze and restart it automatically.",
        ),

        "wid_usage": ConfigParameter(
            data_type=bool,
            default=False,
            category=ConfigCategory.TEST_CASE_EXECUTION,
            config_file_example=True,
            help="Generate a csv wid report with specific wids and tests using them.",
        ),

        "project_repos": ConfigParameter(
            data_type=list[str],
            default=None,
            category=ConfigCategory.BUILD,
            config_file_example=["path/to/repo1", "path/to/repo2"],
            help="An additional argument that is used for build and flash stage. "
                 "Its usage is board-specific.",
        ),

        "server_args": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.OTHER,
            config_file_example="-S 65000 65002",
            help="autopts server arguments used in AUTO_CLIENT_ONLY mode.",
        ),

        "build_env_cmd": ConfigParameter(
            data_type=str,
            default=None,
            category=ConfigCategory.BUILD,
            config_file_example="source ~/zephyrproject/.venv/bin/activate",
            help="Add the `build_env_cmd` option to allow configuring a shell command that "
                 "activates the environment before running `west build` or `west flash`.",
        ),
    }

    for key in parameters:
        parameter = parameters[key]
        if parameter.cli is not None:
            action = None

            clis = parameter.cli if isinstance(parameter.cli, list) else [parameter.cli]
            for cli in clis:
                if cli.kwargs.get("dest", None) is None:
                    cli.kwargs["dest"] = key

                cli.kwargs["help"] = parameter.short_help if parameter.short_help else parameter.help

                if action is None:
                    action = cli.kwargs.get("action", None)

            if action == "store_true":
                parameter.cli_example = ""
                parameter.config_file_example = True
            elif action == "store_false":
                parameter.cli_example = ""
                parameter.config_file_example = False

            if parameter.config_file_example is None:
                parameter.config_file_example = str(parameter.cli_example)


if __name__ == '__main__':
    """Run this to regenerate the doc/bot_config.md"""

    from pathlib import Path
    from typing import get_args, get_origin

    def _type_name(t) -> str:
        """Convert Python type to readable string."""
        origin = get_origin(t)
        if origin is not None:
            args = ", ".join(_type_name(a) for a in get_args(t))
            return f"{origin.__name__}[{args}]"

        if hasattr(t, "__name__"):
            return t.__name__

        return str(t)

    def generate_markdown(output: str | Path) -> None:
        output = Path(output)

        lines: list[str] = []

        lines.append("# AutoPTS Configuration\n")

        categories = {}

        for name, param in ConfigDefinition.parameters.items():
            categories.setdefault(param.category, []).append((name, param))

        lines.append("## Table of Contents\n")

        for category in ConfigCategory:
            params = categories.get(category)
            if not params:
                continue

            lines.append(f"- [{category.value}](#{category.value.lower()})")

            for name, param in params:
                if param.hidden:
                    continue
                lines.append(f"  - [`{name}`](#{name.lower()})")

        lines.append("")

        for category in ConfigCategory:
            params = categories.get(category)
            if not params:
                continue

            lines.append(f"\n## {category.value}\n")

            for name, param in params:
                if param.hidden:
                    continue

                lines.append(f'<a id="{name}"></a>')
                lines.append("")
                lines.append(f"### `{name}`\n")

                if param.short_help:
                    lines.append(param.short_help)
                    lines.append("")

                lines.append("| Property | Value |")
                lines.append("|----------|-------|")

                lines.append(f"| Type | `{_type_name(param.data_type)}` |")
                lines.append(f"| Default | `{param.default}` |")

                if param.iut_param:
                    lines.append("| IUT parameter | Yes |")

                if param.choices:
                    choices = ", ".join(f"`{c}`" for c in param.choices)
                    lines.append(f"| Choices | {choices} |")

                if param.cli:
                    cli = param.cli if isinstance(param.cli, list) else [param.cli]

                    flags = []

                    for arg in cli:
                        if arg.flags:
                            flags.extend(arg.flags)

                    cli_flags = ", ".join(f"`{f}`" for f in flags)
                else:
                    cli_flags = "N/A"

                lines.append(f"| CLI | {cli_flags} |")

                lines.append("")

                if param.help:
                    lines.append("#### Description\n")
                    lines.append(param.help)
                    lines.append("")

                if param.cli_example or param.config_file_example:
                    lines.append("#### Example\n")

                    if param.cli_example:
                        lines.append("**CLI**")
                        if getattr(param.cli, "flags", None):
                            lines.append("```bash")
                            lines.append(f'{param.cli.flags[0]} {param.cli_example}')
                        else:
                            lines.append('(positional argument)')
                            lines.append("```bash")
                            lines.append(f'{repr(param.cli_example)}')
                        lines.append("```")
                        lines.append("")

                    if param.config_file_example:
                        lines.append("**Bot config file**")
                        lines.append("```python")
                        lines.append(f'"{name}": {repr(param.config_file_example)}')
                        lines.append("```")
                        lines.append("")

        output.write_text("\n".join(lines), encoding="utf-8")

    output = os.path.join(AUTOPTS_ROOT_DIR, "doc/bot/bot_config.md")
    generate_markdown(output)
