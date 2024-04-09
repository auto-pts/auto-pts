#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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
import os
import sys
import logging
from datetime import timedelta
from tools.cron.common import parse_yaml
from autopts.client import run_or_not
from autopts.ptsprojects.testcase_db import TestCaseTable

log = logging.info

if sys.platform == 'win32':
    from tools.cron.cache_testcases import cache_test_cases


def update_cached_test_cases(config):
    if sys.platform == 'win32':
        workspace = config['auto_pts']['workspace']
        cache_file_path = config['cron']['test_case_estimation']['cache_file_path']

        return cache_test_cases(workspace, cache_file_path)


def estimate_test_cases(config, included, excluded):
    profiles = parse_yaml(config['cron']['test_case_estimation']['cache_file_path'])
    test_cases = []

    for profile in profiles:
        for tc in profiles[profile]:
            if run_or_not(tc, included, excluded):
                test_cases.append(tc)

    return test_cases


def estimate_test_cases_duration(database_file, table_name, test_cases, max_count):
    database = TestCaseTable(table_name, database_file)
    est_duration = database.estimate_session_duration(test_cases, max_count)
    return est_duration


def get_estimations(config, included_tc, excluded_tc):
    test_cases = estimate_test_cases(config, included_tc, excluded_tc)

    est_duration = None
    database_file = config['auto_pts'].get('database_file', None)

    if database_file and test_cases:
        table_name = f"{config['name']}_{config['auto_pts']['board']}"
        table_name = config['auto_pts'].get('table_name', table_name)
        max_count = config['auto_pts'].get('retry', 0) + 1

        est_duration = estimate_test_cases_duration(
            database_file, table_name, test_cases, max_count)

        if est_duration:
            est_duration = timedelta(seconds=int(est_duration))

    return test_cases, est_duration
