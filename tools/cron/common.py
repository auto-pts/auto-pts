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

"""AutoPTS Cron with Github CI

Schedule cyclical jobs or trigger them with magic sentence in Pull Request comment.

Copy this file to root dir of auto-pts repo and adjust to your preferences.

If your ssh private key has password, before running the cron,
start ssh agent in the same console:
$ eval `ssh-agent`
$ ssh-add path/to/id_rsa
"""

import os
import re
import sys
import json
import shutil
import schedule
import requests
import importlib
import mimetypes
import functools
import traceback
import subprocess
from os import listdir
from pathlib import Path
from time import sleep, time
from threading import Thread
from os.path import dirname, abspath
from datetime import datetime, timedelta, date
from requests.structures import CaseInsensitiveDict
from autopts_bisect import Bisect, set_run_test_fun
from autopts.bot.common import update_sources, send_mail, update_repos

AUTOPTS_REPO=dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, AUTOPTS_REPO)


if sys.platform == 'win32':
    import wmi

END = False
CRON_CFG = None
mimetypes.add_type('text/plain', '.log')


def set_cron_cfg(cfg):
    global CRON_CFG
    CRON_CFG = cfg


def set_end():
    global END
    END = True


def catch_exceptions(cancel_on_failure=False):
    def _catch_exceptions(job_func):
        @functools.wraps(job_func)
        def __catch_exceptions(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                print(traceback.format_exc())
                if cancel_on_failure:
                    magic_tag = kwargs['magic_tag'] if 'magic_tag' in kwargs else None
                    send_mail_exception(kwargs['cfg'], traceback.format_exc(), magic_tag)
                    return schedule.CancelJob
        return __catch_exceptions
    return _catch_exceptions


def catch_connection_error(func):
    def _catch_exceptions(*args, **kwargs):
        while not END:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                print('Internet connection error')
                sleep(1)
    return _catch_exceptions


def report_to_review_msg(report_path):
    failed_statuses = ['INCONC', 'FAIL', 'UNKNOWN VERDICT: NONE',
                       'BTP ERROR', 'XML-RPC ERROR', 'BTP TIMEOUT']
    fails = []
    msg = 'AutoPTS Bot results:\n'

    with open(report_path, 'r') as f:
        while True:
            line = f.readline()

            if not line:
                break

            if any(status in line for status in failed_statuses):
                fails.append(line.strip())

    if len(fails) > 0:
        msg += 'Failed tests:\n{}'.format('\n'.join(fails))
    else:
        msg += 'No failed test found.\n'

    return msg


def send_mail_exception(conf_name, exception, magic_tag=None):
    iso_cal = date.today().isocalendar()
    ww_dd_str = 'WW%s.%s' % (iso_cal[1], iso_cal[2])

    if magic_tag is not None:
        job_type_info = '<p>Session was triggered with magic sentence: {}</p>'.format(magic_tag)
    else:
        job_type_info = '<p>Session was triggered with cyclical schedule</p>'

    body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session - {} - FAILED </h1>
    {}
    <p>Config file: {}</p>
    <p>Exception: {}</p>
    <p>Sincerely,</p>
    <p> {}</p>
    '''.format(ww_dd_str, job_type_info, conf_name, exception, CRON_CFG.email['name'])

    attachments = []
    for file in ['stdout_autoptsbot.log', 'stdout_autoptsserver.log']:
        if os.path.exists(file):
            attachments.append(file)

    subject = 'AutoPTS session FAILED - fail logs'
    send_mail(CRON_CFG.email, subject, body, attachments)


class GithubCron(Thread):
    base_url = 'https://api.github.com'

    def __init__(self, interval, magic_tags, repo_owner, repo_name, permitted_logins, access_token=None):
        super().__init__()
        self.config = {'base_url': self.base_url,
                       'owner': repo_owner,
                       'repo': repo_name,
                       'access_token': access_token
                       }
        self.end = False
        self.interval = interval
        self.tags = magic_tags
        self.last_comment_id = 0
        self.permitted_logins = permitted_logins
        self.since_offset = 15  # minutes before
        self.schedule_delay = 1  # minutes after parsing GET response

    def check_token(self):
        if 'access_token' not in self.config or self.config['access_token'] is None:
            raise Exception('Github token was not provided')

    @catch_connection_error
    def get(self, url, params):
        headers = CaseInsensitiveDict()
        if 'access_token' in self.config and self.config['access_token'] is not None:
            headers['Authorization'] = 'token {access_token}'.format(**self.config)

        resp = requests.get(url, params, headers=headers)

        return resp

    @catch_connection_error
    def post(self, url, params):
        headers = CaseInsensitiveDict()
        if 'access_token' in self.config and self.config['access_token'] is not None:
            headers['Authorization'] = 'token {access_token}'.format(**self.config)

        resp = requests.post(url, data=json.dumps(params), headers=headers)

        return resp

    def post_pr_comment(self, pr_number, comment_body):
        self.check_token()
        url = '{base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments'.format(
            pr_number=pr_number, **self.config)

        params = {
            'body': comment_body,
            'accept': 'application/vnd.github.v3+json',
        }

        rsp = self.post(url, params)

        return rsp

    def get_pr_comments_with_magic_tag(self):
        tagged_comments = []

        since = datetime.utcnow() - timedelta(minutes=self.since_offset)
        url = '{base_url}/repos/{owner}/{repo}/issues/comments'.format(**self.config)

        params = {
            'since': since.strftime('%Y%m%dT%H%M%SZ'),
            'accept': 'application/vnd.github.v3+json',
            'per_page': 100,
            'page': 1,
            'sort': 'updated',
            'direction': 'asc'
        }

        resp = self.get(url, params)
        try:
            comments = resp.json()
        except:
            comments = []

        for comment in comments:
            comment_id = comment['id']
            if comment_id <= self.last_comment_id:
                continue
            self.last_comment_id = comment_id

            if 'pull' not in comment['html_url']:
                continue

            login = comment['user']['login']
            if not any(login == perm_login for perm_login in self.permitted_logins):
                continue

            body = comment['body']
            for tag in self.tags:
                if body.startswith(tag):
                    comment['magic_tag'] = tag
                    break

            if 'magic_tag' not in comment:
                continue

            tagged_comments.append(comment)

        return tagged_comments

    def run(self):
        while not self.end:
            print('{} Github cron is running'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S ')))
            tagged_comments = self.get_pr_comments_with_magic_tag()

            for comment in tagged_comments:
                github_pr_number = int(re.findall(r'(?<=pull\/)\d+?(?=#)', comment['html_url'])[0])
                url = '{base_url}/repos/{owner}/{repo}/pulls/{issue_nr}'.format(**self.config,
                                                                                issue_nr=github_pr_number)

                params = {'accept': 'application/vnd.github.v3+json'}
                resp = self.get(url, params)
                try:
                    pr = resp.json()
                except:
                    continue

                tag_cfg = self.tags[comment['magic_tag']]
                pr_cfg = {
                    'number': github_pr_number,
                    'source_repo_owner': pr['user']['login'],
                    'repo_name': pr['head']['repo']['name'],
                    'source_branch': pr['head']['ref'],
                    'head_sha': pr['head']['sha'],
                    'comment_body': comment['body'],
                    'magic_tag': comment['magic_tag'],
                    'autopts_selftest': tag_cfg.autopts_selftest if hasattr(tag_cfg, 'autopts_selftest') else False
                }

                start_time = pr_choose_start_time() + timedelta(minutes=self.schedule_delay)
                today_str = (start_time).strftime('%H:%M:%S')
                getattr(schedule.every(), start_time.strftime('%A').lower()).at(today_str).do(
                    tag_cfg.func, cron=self, pr_cfg=pr_cfg, **vars(tag_cfg))

                post_text = 'Scheduled PR #{} after {}.'.format(comment['html_url'], today_str)
                self.post_pr_comment(github_pr_number, post_text)
                print(post_text)

            i = 0
            while i < self.interval and not self.end:
                sleep(1)
                i += 1


def pr_choose_start_time():
    start_time = datetime.today()
    run_time = 10.0
    all_jobs = schedule.jobs[:]

    while True:
        for job in [j for j in all_jobs]:
            if job.next_run < start_time or \
                    job.next_run > start_time + timedelta(hours=run_time):
                all_jobs.remove(job)

        if not len(all_jobs):
            break

        start_time = datetime.today() + timedelta(hours=run_time)
    return start_time + timedelta(minutes=1)


def kill_processes(name):
    c = wmi.WMI()
    own_id = os.getpid()
    for ps in c.Win32_Process(name=name):
        try:
            if ps.ProcessId != own_id:
                ps.Terminate()
                print('{} process (PID {}) terminated successfully'.format(name, ps.ProcessId))
        except:
            print('There is no {} process running with id: {}'.format(name, ps.ProcessId))


def clear_workspace(workspace_dir):
    if workspace_dir:
        with os.scandir(workspace_dir) as files:
            for f in files:
                if f.is_dir():
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    try:
                        if not f.name.endswith(('.pqw6', '.pts')):
                            os.remove(f)
                    except:
                        pass


def check_call(cmd, env=None, cwd=None, shell=True):
    """Run command with arguments.  Wait for command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets current directory before execution
    :param shell: if true, the command will be executed through the shell
    :return: returncode
    """
    executable = '/bin/bash'
    cmd = subprocess.list2cmdline(cmd)

    if sys.platform == 'win32':
        executable = None

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell, executable=executable)


def load_config(cfg):
    cfg_path = os.path.join(AUTOPTS_REPO, 'autopts/bot/{}.py'.format(cfg))
    if not os.path.isfile(cfg_path):
        print('{} does not exists!'.format(cfg_path))
        return None

    mod = importlib.import_module('autopts.bot.' + cfg)
    return mod.BotProjects[0]


def find_latest_db(test_case_db_name, logging_repo, branch='main',
                   remote='origin', init_depth=4):
    newest_db = None
    newest_db_modify_date = None

    def recursive(directory, depth):
        nonlocal newest_db, newest_db_modify_date
        depth -= 1

        with os.scandir(directory) as iterator:
            for f in iterator:
                if f.is_dir() and depth > 0:
                    if f.name.endswith('.git'):
                        continue
                    recursive(f.path, depth)
                elif f.name.endswith(test_case_db_name):
                    modify_date = os.path.getmtime(f.path)
                    if newest_db is None or modify_date > newest_db_modify_date:
                        newest_db = f.path
                        newest_db_modify_date = os.path.getmtime(f.path)
        return newest_db

    update_sources(logging_repo, remote, branch, True)
    recursive(logging_repo, init_depth)
    return newest_db


def pre_cleanup(autopts_repo, project_repo, test_case_db_path='TestCase.db'):
    kill_processes('PTS.exe')
    kill_processes('Fts.exe')
    kill_processes('python.exe')
    pre_cleanup_files(autopts_repo, project_repo, test_case_db_path)


def pre_cleanup_files(autopts_repo, project_repo, test_case_db_path='TestCase.db'):
    files_to_save = [
        os.path.join(autopts_repo, 'tmp/'),
        os.path.join(autopts_repo, 'logs/'),
        os.path.join(autopts_repo, 'report.txt'),
        os.path.join(autopts_repo, 'report.xlsx'),
        test_case_db_path,
        os.path.join(autopts_repo, 'stdout_autoptsbot.log'),
        os.path.join(autopts_repo, 'stdout_autoptsserver.log'),
    ]

    files_to_remove = [
        r'~/Documents/Frontline Test Equipment',
    ]

    if 'zephyr' in project_repo:
        files_to_remove.append(os.path.join(project_repo,
                                            'tests/bluetooth/tester/build/'))
    elif 'mynewt' in project_repo:
        files_to_remove.append(os.path.join(project_repo,
                                            'bin/targets'))
    try:
        now = time()
        days_of_validity = 7
        oldlogs_dir = os.path.join(autopts_repo, 'oldlogs/')
        save_dir = os.path.join(oldlogs_dir, datetime.now().strftime("%Y_%m_%d_%H_%M"))
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        for file in listdir(oldlogs_dir):
            file_path = os.path.join(oldlogs_dir, file)
            if os.stat(file_path).st_mtime < now - days_of_validity * 86400:
                files_to_remove.append(file_path)

        for file in files_to_remove:
            file_path = os.path.join(autopts_repo, file)
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path, ignore_errors=True)

        for file in files_to_save:
            file_path = os.path.join(autopts_repo, file)
            if os.path.exists(file_path):
                shutil.move(file_path, os.path.join(save_dir, os.path.basename(file_path)))
    except:
        pass


def update_zephyr_tools(wsl=False):
    if sys.platform == 'win32' and not wsl:
        installer_file = 'install_zephyr_tools.bat'
    else:
        installer_file = './install_zephyr_tools.sh'

    script_dir = os.path.dirname(__file__)

    if not os.path.exists(os.path.join(script_dir, installer_file)):
        print('Installer {} does not exists!'.format(installer_file))
        return

    zephyr_sdk_github = GithubCron(60, [], 'zephyrproject-rtos', 'sdk-ng', [])
    tag_url = 'https://api.github.com/repos/zephyrproject-rtos/sdk-ng/tags'

    params = {'accept': 'application/vnd.github.v3+json', }
    resp = zephyr_sdk_github.get(tag_url, params)
    try:
        tags = resp.json()
    except:
        return

    version_tag = None

    for tag in tags:
        if 'rc' not in tag['name'] and 'beta' not in tag['name']:
            version_tag = tag['name']
            break

    if version_tag is None:
        sys.exit('Parsing zephyr toolchain failed!')

    cmd = [installer_file, version_tag]

    if sys.platform == 'win32' and wsl:
        cmd = subprocess.list2cmdline(cmd)
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl

    check_call(cmd, cwd=script_dir, shell=not wsl)


def git_stash_clear(cwd):
    cmd = 'git stash clear'
    print('Running: ', cmd)
    check_call(cmd.split(), cwd=cwd)


def git_checkout(branch, cwd):
    cmd = 'git checkout {}'.format(branch)
    print('Running: ', cmd)
    check_call(cmd.split(), cwd=cwd)


def git_rebase_abort(cwd):
    cmd = 'git rebase --abort'
    print('Running: ', cmd)
    check_call(cmd.split(), cwd=cwd)


def merge_pr_branch(pr_source_repo_owner, pr_source_branch, repo_name, project_repo):
    cmd = 'git fetch https://github.com/{}/{}.git'.format(
        pr_source_repo_owner, repo_name)
    print('Running: ', cmd)
    check_call(cmd.split(), cwd=project_repo)

    cmd = 'git pull --rebase https://github.com/{}/{}.git {}'.format(
        pr_source_repo_owner, repo_name, pr_source_branch)
    print('Running: ', cmd)
    check_call(cmd.split(), cwd=project_repo)


def run_test(bot_options, server_options, autopts_repo):
    # Start subprocess running autoptsserver
    srv_cmd = 'python autoptsserver.py {} >> stdout_autoptsserver.log 2>&1'.format(server_options)
    print('Running: ', srv_cmd)
    srv_process = subprocess.Popen(srv_cmd.split(),
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=autopts_repo)

    sleep(60)

    # Start subprocess of autoptsclient_bot
    bot_cmd = 'python autoptsclient_bot.py {}' \
              ' >> stdout_autoptsbot.log 2>&1'.format(bot_options)
    print('Running: ', bot_cmd)
    bot_process = subprocess.Popen(bot_cmd.split(),
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=autopts_repo)

    sleep(5)
    try:
        # Main thread waits for at least one of subprocesses to finish
        while srv_process.poll() is None and bot_process.poll() is None:
            sleep(5)
    except:
        pass

    # Terminate the other subprocess if it is still running
    if srv_process.poll() is None:
        srv_process.terminate()

    if bot_process.poll() is None:
        bot_process.terminate()

    sleep(10)
    kill_processes('PTS.exe')
    kill_processes('Fts.exe')
    kill_processes('python.exe')


@catch_exceptions(cancel_on_failure=True)
def zephyr_pr_job(cron, cfg, pr_cfg, server_options, update_tools=False, **kwargs):
    print('Started PR Job: repo_name={repo_name} PR={number} src_owner={source_repo_owner}'
          ' branch={source_branch} head_sha={head_sha} comment={comment_body} '
          'magic_tag={magic_tag} cfg={cfg}'.format(**pr_cfg, cfg=cfg))

    cfg_dict = load_config(cfg)
    if update_tools:
        update_zephyr_tools(wsl=cfg_dict['auto_pts'].get('wsl', False))

    included = re.sub(r'\s+', r' ', pr_cfg['comment_body'][len(pr_cfg['magic_tag']):]).strip()
    excluded = ''

    if included and not included.isspace():
        included = ' -c {}'.format(included)
    else:
        included = ''

    if excluded and not excluded.isspace():
        excluded = ' -e {}'.format(excluded)
    else:
        excluded = ''

    PROJECT_REPO = cfg_dict['auto_pts']['project_path']
    test_case_db_name = 'TestCase.db'
    autopts_test_case_db = os.path.join(AUTOPTS_REPO, test_case_db_name)

    pre_cleanup(AUTOPTS_REPO, PROJECT_REPO, test_case_db_name)

    # Copy TestCase.db from previous build to catch regressions
    if 'githubdrive' in cfg_dict:
        database_repo = cfg_dict['githubdrive']['path']
        test_case_db_path = find_latest_db(test_case_db_name, database_repo)

        if test_case_db_path is None:
            raise Exception('Database file {} do not exists'.format(test_case_db_path))

        print('Copied database from {}'.format(test_case_db_path))
        shutil.copy(test_case_db_path, autopts_test_case_db)

    clear_workspace(os.path.join(AUTOPTS_REPO, 'autopts/workspaces/zephyr/zephyr-master'))
    git_stash_clear(PROJECT_REPO)
    update_sources(PROJECT_REPO, 'origin', 'main', True)
    merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                    pr_cfg['repo_name'], PROJECT_REPO)

    # To prevent update of zephyr project repo by bot, set 'update_repo'
    # to False in zephyr['git'] of config.py

    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded=excluded)
    run_test(bot_options, server_options, AUTOPTS_REPO)

    # report.txt is created at the very end of bot run, so
    # it should exists if bot completed tests fully
    if not os.path.exists(os.path.join(AUTOPTS_REPO, 'report.txt')):
        raise Exception('Bot failed before report creation')

    print('Zephyr PR Job finished')

    cron.post_pr_comment(
        pr_cfg['number'], report_to_review_msg('report.txt'))

    # To prevent scheduler from cyclical running of the job
    return schedule.CancelJob


@catch_exceptions(cancel_on_failure=True)
def zephyr_job(cfg, server_options, included='', excluded='', bisect=None, update_tools=False, **kwargs):
    print('Started Zephyr Job', cfg)

    cfg_dict = load_config(cfg)
    if update_tools:
        update_zephyr_tools(wsl=cfg_dict['auto_pts'].get('wsl', False))

    if included and not included.isspace():
        included = ' -c {}'.format(included)

    if excluded and not excluded.isspace():
        excluded = ' -e {}'.format(excluded)

    PROJECT_REPO = cfg_dict['auto_pts']['project_path']

    test_case_db_name = 'TestCase.db'
    autopts_test_case_db = os.path.join(AUTOPTS_REPO, test_case_db_name)

    pre_cleanup(AUTOPTS_REPO, PROJECT_REPO, test_case_db_name)

    # Copy TestCase.db from previous build to catch regressions
    if 'githubdrive' in cfg_dict:
        database_repo = cfg_dict['githubdrive']['path']
        test_case_db_path = find_latest_db(test_case_db_name, database_repo)

        if test_case_db_path is None:
            raise Exception('Database file {} do not exists'.format(test_case_db_path))

        print('Copied database from {}'.format(test_case_db_path))
        shutil.copy(test_case_db_path, autopts_test_case_db)

    clear_workspace(os.path.join(AUTOPTS_REPO, 'autopts/workspaces/zephyr/zephyr-master'))
    git_stash_clear(os.path.join(PROJECT_REPO))

    # To prevent update of zephyr project repo by bot, set 'update_repo'
    # to False in zephyr['git'] of config.py

    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded=excluded)
    run_test(bot_options, server_options, AUTOPTS_REPO)

    # report.txt is created at the very end of bot run, so
    # it should exists if bot completed tests fully
    report = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report):
        raise Exception('Bot failed before report creation')

    if bisect:
        Bisect(bisect).run_bisect(report)

    print('Zephyr Job finished')


@catch_exceptions(cancel_on_failure=True)
def nimble_job(cfg, server_options, included='', excluded='', **kwargs):
    print('Started NimBLE Job', cfg)

    if included and not included.isspace():
        included = ' -c {}'.format(included)

    if excluded and not excluded.isspace():
        excluded = ' -e {}'.format(excluded)

    cfg_dict = load_config(cfg)
    PROJECT_REPO = cfg_dict['auto_pts']['project_path']

    test_case_db_name = 'TestCase.db'

    pre_cleanup(AUTOPTS_REPO, PROJECT_REPO, test_case_db_name)

    clear_workspace(os.path.join(AUTOPTS_REPO, 'autopts/workspaces/Mynewt Nimble Host'))
    git_stash_clear(os.path.join(PROJECT_REPO, 'repos/apache-mynewt-nimble'))

    # To prevent update of Mynewt project repo by bot, set 'update_repo'
    # to False in mynewt['git'] of config.py

    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded=excluded)
    run_test(bot_options, server_options, AUTOPTS_REPO)

    report = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report):
        raise Exception('Bot failed before report creation')

    print('NimBLE Job finished')


@catch_exceptions(cancel_on_failure=True)
def vm_pr_job(cron, cfg, pr_cfg, **kwargs):
    print('Started PR Job: repo_name={repo_name} PR={number} src_owner={source_repo_owner}'
          ' branch={source_branch} head_sha={head_sha} '
          'comment={comment_body} magic_tag={magic_tag} cfg={cfg}'.format(**pr_cfg, cfg=cfg))

    included = re.sub(r'\s+', r' ', pr_cfg['comment_body'][len(pr_cfg['magic_tag']):]).strip()
    excluded = ''

    if included and not included.isspace():
        included = ' -c {}'.format(included)
    else:
        included = ''

    if excluded and not excluded.isspace():
        excluded = ' -e {}'.format(excluded)
    else:
        excluded = ''

    cfg_dict = load_config(cfg)
    PROJECT_REPO = cfg_dict['auto_pts']['project_path']
    test_case_db_name = 'TestCase.db'
    pre_cleanup_files(AUTOPTS_REPO, PROJECT_REPO, test_case_db_name)

    if 'git' in cfg_dict:
        update_repos(PROJECT_REPO, cfg_dict['git'])

    try:
        if pr_cfg.get('autopts_selftest', False):
            merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                            pr_cfg['repo_name'], AUTOPTS_REPO)
        else:
            merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                            pr_cfg['repo_name'], PROJECT_REPO)
    except:
        git_rebase_abort(AUTOPTS_REPO)
        cron.post_pr_comment(pr_cfg['number'], 'Failed to merge the branch')
        return schedule.CancelJob

    # To prevent update of the project repo by bot, set 'update_repo'
    # to False in ['git'] of config.py

    python_ver = '3' if sys.platform != 'win32' else ''

    # Start subprocess of autoptsclient_bot
    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded=excluded)
    bot_cmd = 'python{} autoptsclient_bot.py {}' \
              ' >> stdout_autoptsbot.log 2>&1'.format(python_ver, bot_options)
    print('Running: ', bot_cmd)
    bot_process = subprocess.Popen(bot_cmd.split(),
                                   shell=False,
                                   cwd=AUTOPTS_REPO)

    sleep(5)
    try:
        while bot_process.poll() is None:
            sleep(5)
    except:
        pass

    # after-cleanup
    if pr_cfg.get('autopts_selftest', False):
        git_checkout('-', AUTOPTS_REPO)

    # report.txt is created at the very end of bot run, so
    # it should exists if bot completed tests fully
    report_path = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report_path):
        raise Exception('Bot failed before report creation')

    print('{} PR Job finished'.format(pr_cfg['repo_name']))

    cron.post_pr_comment(
        pr_cfg['number'], report_to_review_msg(report_path))

    # To prevent scheduler from cyclical running of the job
    return schedule.CancelJob


@catch_exceptions(cancel_on_failure=True)
def win_autopts_pr_job(cron, cfg, pr_cfg, server_options, **kwargs):
    print('Started PR Job: repo_name={repo_name} PR={number} src_owner={source_repo_owner}'
          ' branch={source_branch} head_sha={head_sha} '
          'comment={comment_body} magic_tag={magic_tag} cfg={cfg}'.format(**pr_cfg, cfg=cfg))

    included = re.sub(r'\s+', r' ', pr_cfg['comment_body'][len(pr_cfg['magic_tag']):]).strip()
    excluded = ''

    if included and not included.isspace():
        included = ' -c {}'.format(included)
    else:
        included = ''

    if excluded and not excluded.isspace():
        excluded = ' -e {}'.format(excluded)
    else:
        excluded = ''

    cfg_dict = load_config(cfg)
    PROJECT_REPO = cfg_dict['auto_pts']['project_path']
    test_case_db_name = 'TestCase.db'
    pre_cleanup_files(AUTOPTS_REPO, PROJECT_REPO, test_case_db_name)

    if 'git' in cfg_dict:
        update_repos(PROJECT_REPO, cfg_dict['git'])

    try:
        merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                        pr_cfg['repo_name'], AUTOPTS_REPO)
    except:
        git_rebase_abort(AUTOPTS_REPO)
        cron.post_pr_comment(pr_cfg['number'], 'Failed to merge the branch')
        return schedule.CancelJob

    # To prevent update of the project repo by bot, set 'update_repo'
    # to False in ['git'] of config.py

    bot_options = '{cfg} --not_recover PASS {included} {excluded}'.format(
        cfg=cfg, included=included, excluded=excluded)
    run_test(bot_options, server_options, AUTOPTS_REPO)

    # after-cleanup
    git_checkout('-', AUTOPTS_REPO)

    # report.txt is created at the very end of bot run, so
    # it should exists if bot completed tests fully
    report_path = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report_path):
        raise Exception('Bot failed before report creation')

    print('{} PR Job finished'.format(pr_cfg['repo_name']))

    cron.post_pr_comment(
        pr_cfg['number'], report_to_review_msg(report_path))

    # To prevent scheduler from cyclical running of the job
    return schedule.CancelJob


set_run_test_fun(run_test)
