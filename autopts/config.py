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

import os.path
from enum import StrEnum

SERVER_PORT = 65000
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


class IUTMode(StrEnum):
    """How AutoPTS runs and communicates with the IUT.

    Set with the iut_mode parameter, or inferred from other
    parameters if not set.
    """

    TTY = 'tty'
    """IUT on a board, BTP over its serial port (tty_file)."""

    QEMU = 'qemu'
    """IUT emulated with QEMU (qemu_bin), BTP over a UNIX socket."""

    NATIVE = 'native'
    """IUT built as a native executable (kernel_image) using a local
    HCI controller (hci or hid_*), BTP over a UNIX socket."""

    BTPCLIENT_PATH = 'btpclient_path'
    """IUT is a BTP client executable (btpclient_path), e.g. BlueZ
    btpclient, BTP over a UNIX socket."""

    BTPCLIENT_TCP = 'btpclient_tcp'
    """External BTP client at btp_tcp_ip:btp_tcp_port, BTP over TCP."""
