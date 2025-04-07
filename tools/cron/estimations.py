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
import logging
import os
import sys
from datetime import timedelta

from autopts.client import run_or_not
from autopts.ptsprojects.testcase_db import TestCaseTable
from tools.cron.common import catch_exceptions, load_config, parse_yaml
from tools.cron.remote_terminal import RemoteTerminalClientProxy


log = logging.info

if sys.platform == 'win32':
    from tools.cron.cache_testcases import cache_test_cases


def remote_cache_test_cases(config):
    remote_config = config['cron']['remote_machine']

    with RemoteTerminalClientProxy(remote_config['terminal_ip'],
                                   remote_config['terminal_port'],
                                   remote_config.get('socket_timeout', None)
                                   ) as client:
        repo_info = config['cron']['remote_machine']['git']['autopts']

        if 'checkout_cmd' in repo_info:
            log(client.run_command(repo_info['checkout_cmd'], repo_info['path']))
        else:
            log(client.run_command(f"git fetch {repo_info['remote']}", repo_info['path']))
            log(client.run_command(f"git checkout {repo_info['remote']}/{repo_info['branch']}", repo_info['path']))

        file_name = 'cached_testcases.yaml'
        cmd = f"python ./tools/cron/cache_testcases.py {config['auto_pts']['workspace']} {file_name}"
        log(client.run_command(cmd, repo_info['path']))

        file_bin = client.copy_file(os.path.join(repo_info['path'], file_name))
        if file_bin is None:
            log(f'Failed to copy the {file_name} from the remote machine')
            return

        with open(config['cron']['test_case_estimation']['cache_file_path'], 'wb') as handle:
            handle.write(file_bin.data)


def update_cached_test_cases(config):
    if sys.platform == 'win32':
        workspace = config['auto_pts']['workspace']
        cache_file_path = config['cron']['test_case_estimation']['cache_file_path']

        return cache_test_cases(workspace, cache_file_path)

    else:
        return remote_cache_test_cases(config)


@catch_exceptions(cancel_on_failure=True)
def update_cached_test_cases_job(cfg, **kwargs):
    log(f'Started {update_cached_test_cases_job.__name__} Job, config: {cfg}')

    config = load_config(cfg)

    update_cached_test_cases(config)

    log(f'The {update_cached_test_cases_job.__name__} Job finished')


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


def get_estimations(config, included_tc, excluded_tc, limit=None):
    test_cases = estimate_test_cases(config, included_tc, excluded_tc)

    if limit:
        if len(included_tc) == 1:
            test_cases = test_cases[:limit]
        else:
            profile_count = {prefix: 0 for prefix in included_tc}
            tc_list = []
            for profile in included_tc:
                for test_case in test_cases:
                    if profile_count[profile] == limit:
                        break
                    if test_case.startswith(profile):
                        tc_list.append(test_case)
                        profile_count[profile] += 1

            test_cases = tc_list

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
