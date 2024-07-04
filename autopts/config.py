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

MAX_SERVER_RESTART_TIME = 60

AUTOPTS_ROOT_DIR = os.path.dirname(  # auto-pts repo directory
                os.path.dirname(  # autopts module directory
                    os.path.abspath(__file__)))  # this file directory

TMP_DIR = 'tmp'
ALL_STATS_RESULTS_XML = os.path.join(TMP_DIR, 'all_stats_results.xml')
TC_STATS_RESULTS_XML = os.path.join(TMP_DIR, 'tc_stats_results.xml')
TEST_CASES_JSON = os.path.join(TMP_DIR, 'test_cases_file.json')
ALL_STATS_JSON = os.path.join(TMP_DIR, 'all_stats.json')
TC_STATS_JSON = os.path.join(TMP_DIR, 'tc_stats.json')
TEST_CASE_DB = os.path.join(TMP_DIR, 'TestCase.db')
BOT_STATE_JSON = os.path.join(TMP_DIR, 'bot_state.json')
REPORT_README_MD = os.path.join(TMP_DIR, 'README.md')
AUTOPTS_REPORT_FOLDER = os.path.join(TMP_DIR, 'autopts_report')
IUT_LOGS_FOLDER = 'logs'
PTS_XMLS_FOLDER = os.path.join(TMP_DIR, 'XMLs')
ERRATA_DIR_PATH = os.path.join(AUTOPTS_ROOT_DIR, 'errata')
REPORT_XLSX = "report.xlsx"
REPORT_TXT = "report.txt"
REPORT_DIFF_TXT = "report-diff.txt"
ERROR_TXT = 'error.txt'
