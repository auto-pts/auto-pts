#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup.
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

"""AutoPTS Bisect
Performs auto git-bisect process for the given test case
Returns first bad commit or None in case of fail.

Usage:
$ python3 autopts_bisect.py <bot_config> <test_case> <last_good_commit> <last_bad_commit>
e.g.:
$ python3 autopts_bisect.py config_zephyr_bisect SM/CEN/JW/BV-05-C 7ab16c457b304ccff82056243e1cee8913263d3e

If last_bad_commit is empty, then takes HEAD commit.
"""

import importlib
import os
import re
import subprocess
import sys
import time
import traceback
import mimetypes
from os.path import dirname, abspath

AUTOPTS_REPO = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, AUTOPTS_REPO)

from autopts.bot.common import send_mail

mimetypes.add_type('text/plain', '.log')

run_test_fun = None


def set_run_test_fun(fun):
    global run_test_fun
    run_test_fun = fun


def call_and_result(cmd, cwd):
    return subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            cwd=cwd
                            ).stdout.read().decode()


def get_regressions(report):
    """Returns list of regress test cases read from report.txt
    :param report path to report.txt
    """
    test_cases = []

    with open(report, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if 'REGRESSION' in line:
            tc = re.sub(' +', ' ', line).split(r' ')[1]
            test_cases.append(tc)
    return test_cases


def bisect_start(cwd=None):
    cmd = 'git bisect start'
    print('Running: ', cmd)
    return call_and_result(cmd, cwd)


def bisect_good(cwd=None, commit=''):
    cmd = 'git bisect good {}'.format(commit)
    print('Running: ', cmd)
    return call_and_result(cmd, cwd)


def bisect_bad(cwd=None, commit=''):
    cmd = 'git bisect bad {}'.format(commit)
    print('Running: ', cmd)
    return call_and_result(cmd, cwd)


def bisect_reset(cwd):
    cmd = 'git bisect reset'
    print('Running: ', cmd)
    return call_and_result(cmd, cwd)


def get_sha(cwd):
    cmd = 'git show -s --format=%H'
    return call_and_result(cmd, cwd)


def bisect(cfg, test_case, good_commit, bad_commit=''):
    """Performs bisect test for broken test.
    :param cfg name of config file that exists in autopts/bot/
    :param test_case name of the test case
    :param good_commit last commit sha that allowed to pass the test case
    :param bad_commit last commit sha that possibly breaks the test case
    """

    print('Bisect started testing of test_case={} cfg={}'.format(test_case, cfg))
    included = '-c {} '.format(test_case)

    conf_path = os.path.join(AUTOPTS_REPO, 'autopts/bot/{}.py'.format(cfg))
    if not os.path.isfile(conf_path):
        print('{} does not exists!'.format(conf_path))
        return None

    mod = importlib.import_module('autopts.bot.' + cfg)
    project_repo = mod.BotProjects[0]['auto_pts']['project_path']

    last_bad = get_sha(project_repo)

    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded='')
    server_options = '-S 65000 65002 --ykush 1 2 --superguard 14'
    report = os.path.join(AUTOPTS_REPO, 'report.txt')
    res = None

    if os.path.exists(report):
        os.remove(report)

    try:
        if res := bisect_start(project_repo):
            raise Exception('bisect_start failed: {}'.format(res))

        if res := bisect_bad(project_repo, bad_commit):
            raise Exception('bisect_bad failed: {}'.format(res))

        if 'error' in (res := bisect_good(project_repo, good_commit)):
            raise Exception('bisect_good failed {}'.format(res))

        while True:
            run_test_fun(bot_options, server_options, AUTOPTS_REPO)
            if not os.path.exists(report):
                raise Exception('Bot failed during bisect run')
            with open(report) as f:
                content = f.read()
            os.remove(report)
            if 'PASS' in content:
                print(res := bisect_good(project_repo))
            else:
                print(res := bisect_bad(project_repo))
            if 'is the first bad commit' in res:
                break
        first_bad = get_sha(project_repo)
    except Exception as e:
        traceback.print_exc()
        print(e)
        first_bad = last_bad = None
    finally:
        bisect_reset(project_repo)

    print('Bisect finished test of test_case={} cfg={}'.format(test_case, cfg))

    return first_bad, last_bad, res


class Bisect:
    def __init__(self, cfg_name):
        self.cfg_name = cfg_name
        self.cfg_dict, self.cfg_path = self.load_cfg(cfg_name)
        self.good_commit = self.cfg_dict['bisect']['good_commit']
        self.mail = self.cfg_dict['bisect']['mail']
        self.time_limit = float(self.cfg_dict['bisect']['time_limit'])
        self.tc_limit = int(self.cfg_dict['bisect']['tc_limit'])

    def update_good_commit(self, commit):
        """Replaces value of good_commit in bisect configuration of
        config .py file.
        """

        with open(self.cfg_path, 'r+') as f:
            data = f.read()
            data = re.sub(r'(?<=\'good_commit\':)\s+\'?[A-Za-z0-9_-]+\'?',
                          ' \'{}\''.format(commit), data)
            f.seek(0)
            f.write(data)
            f.truncate()

    def load_cfg(self, cfg):
        cfg_path = os.path.join(AUTOPTS_REPO, 'autopts/bot/{}.py'.format(cfg))
        if not os.path.isfile(cfg_path):
            raise Exception('{} does not exists!'.format(cfg_path))

        mod = importlib.import_module('autopts.bot.' + cfg)
        return mod.BotProjects[0], cfg_path

    def send_mail(self, test_case, result):
        """Sends email with biesect result for one test case
        :param test_case name of the test case
        :param result of auto git bisect
        """

        email_cfg = self.mail

        body = '''
        <p>This is automated email and do not reply.</p>
        <h1>AutoPTS Bisect results  </h1>
        <p>Test case: {}</p>
        <p>Config file: {}</p>
        <p>Bisect result:</p>
        {}
        <p>Sincerely,</p>
        <p> {}</p>
        '''.format(test_case, self.cfg_name, result, email_cfg['name'])

        subject = 'AutoPTS Bisect - results'
        send_mail(email_cfg, subject, body)

    def run_bisect(self, report):
        first_bad, last_bad = None, None
        test_cases = get_regressions(report)
        start = time.time()

        for i, tc in enumerate(test_cases):
            first_bad, last_bad, res = bisect(self.cfg_name,
                                              tc, self.good_commit)
            self.send_mail(tc, res)

            end = time.time()
            run_time = (end - start) / 3600
            print('Time {}'.format(run_time))

            if run_time >= self.time_limit or \
                    i >= self.tc_limit:
                break

        if last_bad is not None:
            self.update_good_commit(last_bad)


if __name__ == '__main__':
    from tools.cron.common import run_test

    set_run_test_fun(run_test)

    if len(sys.argv) == 3:
        sys.exit('Usage:\n'
                 '$ python3 {} <bot_config> <test_case> <last_good_commit> <last_bad_commit>\n'
                 'e.g. $ python3 {} config_bisect SM/CEN/JW/BV-05-C 7ab16c457b304ccff82056243e1cee8913263d3e\n'
                 'If last_bad_commit is empty then takes HEAD commit.'.format(sys.argv[0], sys.argv[0]))

    conf = sys.argv[1]
    tc = sys.argv[2]
    good = sys.argv[3]
    bad = sys.argv[4] if len(sys.argv) >= 5 else ''

    first_bad, last_bad, res = bisect(conf, tc, good, bad)
    print('Bisect result:\n{}'.format(res))

    # Bisect('config_zephyr_bisect').run_bisect(r'C:/Users/Codecoup/workspace/auto-pts/report.txt')
