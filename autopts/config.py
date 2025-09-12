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
        'FLASH_BIN_DIR': os.path.join(FILE_PATHS['TMP_DIR'], 'flash_bins'),
        # 'BOT_LOG_FILE': os.path.join(autopts_root_dir, 'autoptsclient_bot.log'),
    })

    if file_paths:
        FILE_PATHS.update(file_paths)

    return FILE_PATHS


generate_file_paths({}, AUTOPTS_ROOT_DIR)
