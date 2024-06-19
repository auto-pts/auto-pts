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

SERVER_PORT = 65000
CLIENT_PORT = 65001
BTMON_PORT = 65432

MAX_SERVER_RESTART_TIME = 60

TMP_DIR = 'tmp/'
ALL_STATS_RESULTS_XML = TMP_DIR + 'all_stats_results.xml'
TC_STATS_RESULTS_XML = TMP_DIR + 'tc_stats_results.xml'
TEST_CASES_JSON = TMP_DIR + 'test_cases_file.json'
ALL_STATS_JSON = TMP_DIR + 'all_stats.json'
TC_STATS_JSON = TMP_DIR + 'tc_stats.json'
TEST_CASE_DB = TMP_DIR + 'TestCase.db'
BOT_STATE_JSON = TMP_DIR + 'bot_state.json'
