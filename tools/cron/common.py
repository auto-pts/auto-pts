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

"""AutoPTS Cron with GitHub CI

Schedule cyclical jobs or trigger them with magic sentence in Pull Request comment.

You can create your own jobs in separate .py file and set them in cron_config.py.

If your ssh private key has password, before running the cron,
start ssh agent in the same console:
$ eval `ssh-agent`
$ ssh-add path/to/id_rsa
"""
import logging
import os
import re
import shlex
import sys
import shutil
import schedule
import requests
import mimetypes
import functools
import traceback
import subprocess
from os import listdir
from pathlib import Path
from time import sleep, time
from os.path import dirname, abspath
from datetime import datetime, date
from autopts_bisect import Bisect, set_run_test_fun
from autopts.bot.common import update_sources, send_mail, update_repos,\
    load_module_from_path

AUTOPTS_REPO=dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, AUTOPTS_REPO)


if sys.platform == 'win32':
    import wmi

log = logging.info
END = False
CRON_CFG = {}
mimetypes.add_type('text/plain', '.log')


def set_cron_cfg(cfg):
    global CRON_CFG
    CRON_CFG = cfg


def set_end():
    global END
    END = True


def get_end():
    global END
    return END


def catch_exceptions(cancel_on_failure=False):
    def _catch_exceptions(job_func):
        @functools.wraps(job_func)
        def __catch_exceptions(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                log(traceback.format_exc())
                if 'email' in CRON_CFG:
                    magic_tag = kwargs['magic_tag'] if 'magic_tag' in kwargs else None
                    send_mail_exception(kwargs['cfg'], CRON_CFG['email'], traceback.format_exc(), magic_tag)

                if cancel_on_failure:
                    return schedule.CancelJob
        return __catch_exceptions
    return _catch_exceptions


def catch_connection_error(func):
    def _catch_exceptions(*args, **kwargs):
        while not END:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                log('Internet connection error')
                sleep(1)
    return _catch_exceptions


def report_to_review_msg(report_path):
    failed_statuses = ['INCONC', 'FAIL', 'UNKNOWN VERDICT: NONE',
                       'BTP ERROR', 'XML-RPC ERROR', 'BTP TIMEOUT']
    failed = []
    passed = []
    msg = 'AutoPTS Bot results:\n'

    with open(report_path, 'r') as f:
        while True:
            line = f.readline()

            if not line:
                break

            if any(status in line for status in failed_statuses):
                failed.append(line.strip())
            elif 'PASS' in line:
                passed.append(line.strip())

    if len(failed) > 0:
        msg += f'<details><summary>Failed tests</summary>{"<br>".join(failed)}</details>\n'
    else:
        msg += 'No failed test found.\n'

    if len(passed) > 0:
        msg += f'<details><summary>Successful tests</summary>{"<br>".join(passed)}</details>\n'

    return msg


def send_mail_exception(conf_name, email_cfg, exception, magic_tag=None):
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
    '''.format(ww_dd_str, job_type_info, conf_name, exception, email_cfg['name'])

    attachments = []
    for file in ['stdout_autoptsbot.log', 'stdout_autoptsserver.log']:
        if os.path.exists(file):
            attachments.append(file)

    subject = 'AutoPTS session FAILED - fail logs'
    send_mail(email_cfg, subject, body, attachments)


def kill_processes(name):
    c = wmi.WMI()
    own_id = os.getpid()
    for ps in c.Win32_Process(name=name):
        try:
            if ps.ProcessId != own_id:
                ps.Terminate()
                log('{} process (PID {}) terminated successfully'.format(name, ps.ProcessId))
        except:
            log('There is no {} process running with id: {}'.format(name, ps.ProcessId))


def clear_workspace(workspace_dir):
    if workspace_dir:
        with os.scandir(workspace_dir) as files:
            for f in files:
                if f.is_dir():
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    try:
                        if not f.name.endswith(('.pqw6', '.pts', '.gitignore', '.xlsx')):
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
    mod = load_module_from_path(cfg)
    if not mod:
        raise Exception(f'Could not load the config {cfg}')

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


def find_workspace_in_tree(tree_path, workspace, init_depth=4):
    workspace_path = None

    def recursive(directory, depth):
        nonlocal workspace_path
        depth -= 1
        if workspace_path:
            return

        with os.scandir(directory) as iterator:
            for f in iterator:
                if f.is_dir():
                    if f.name.endswith('.git'):
                        continue

                    if f.name == workspace:
                        workspace_path = f.path
                        return

                    if depth > 0:
                        recursive(f.path, depth)
        return

    recursive(tree_path, init_depth)
    return workspace_path


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


def git_stash_clear(cwd):
    cmd = 'git stash clear'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=cwd)


def git_checkout(branch, cwd):
    cmd = 'git checkout {}'.format(branch)
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=cwd)


def git_rebase_abort(cwd):
    cmd = 'git rebase --abort'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=cwd)


def merge_pr_branch(pr_source_repo_owner, pr_source_branch, repo_name, project_repo):
    cmd = 'git fetch https://github.com/{}/{}.git'.format(
        pr_source_repo_owner, repo_name)
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=project_repo)

    cmd = 'git pull --rebase https://github.com/{}/{}.git {}'.format(
        pr_source_repo_owner, repo_name, pr_source_branch)
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=project_repo)


def run_test(bot_options, server_options, autopts_repo):
    if sys.platform == 'win32':
        # Start subprocess running autoptsserver
        srv_cmd = 'python autoptsserver.py {} >> stdout_autoptsserver.log 2>&1'.format(server_options)
        log(f'Running: {srv_cmd}')
        srv_process = subprocess.Popen(shlex.split(srv_cmd),
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       cwd=autopts_repo)

        sleep(60)
    else:
        # Assume that autoptsserver is available remotely on virtual machine
        srv_process = None

    # Start subprocess of autoptsclient_bot
    bot_cmd = 'python autoptsclient_bot.py {}' \
              ' >> stdout_autoptsbot.log 2>&1'.format(bot_options)
    log(f'Running: {bot_cmd}')
    bot_process = subprocess.Popen(shlex.split(bot_cmd),
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=autopts_repo)

    sleep(5)
    try:
        # Main thread waits for at least one of subprocesses to finish
        while (srv_process is None or srv_process.poll() is None) and \
                bot_process.poll() is None:
            sleep(5)
    except:
        pass

    if srv_process is None:
        # autoptsserver is running on virtual machine
        return

    # Terminate the other subprocess if it is still running
    if srv_process.poll() is None:
        srv_process.terminate()

    if bot_process.poll() is None:
        bot_process.terminate()

    sleep(10)
    kill_processes('PTS.exe')
    kill_processes('Fts.exe')
    kill_processes('python.exe')


def parse_test_cases_from_comment(pr_cfg):
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

    return included, excluded


@catch_exceptions(cancel_on_failure=True)
def generic_pr_job(cron, cfg, pr_cfg, server_options, pr_repo_name_in_config,
                   bot_options_append='', **kwargs):
    log('Started PR Job: repo_name={repo_name} PR={number} src_owner={source_repo_owner}'
        ' branch={source_branch} head_sha={head_sha} comment={comment_body} '
        'magic_tag={magic_tag} cfg={cfg}'.format(**pr_cfg, cfg=cfg))

    cfg_dict = load_config(cfg)

    included, excluded = parse_test_cases_from_comment(pr_cfg)

    # Path to the project
    PROJECT_REPO = cfg_dict['auto_pts']['project_path']

    # Delete AutoPTS logs, tmp files, old bin directories, kill old PTS.exe, ...
    pre_cleanup(AUTOPTS_REPO, PROJECT_REPO)

    # Find PTS workspace path and delete PTS logs
    workspace_path = find_workspace_in_tree(
        os.path.join(AUTOPTS_REPO, 'autopts/workspaces'), cfg_dict['auto_pts']['workspace'])
    clear_workspace(workspace_path)

    # Update repo.
    # To prevent update of the repo by bot, remember to set 'update_repo'
    # to False in m['git']['repo_name']['update_repo'] of config.py
    cfg_dict['git'][pr_repo_name_in_config]['update_repo'] = True
    update_repos(PROJECT_REPO, cfg_dict['git'])

    # Merge PR branch into local instance of tested repo
    if not os.path.isabs(cfg_dict['git'][pr_repo_name_in_config]['path']):
        repo_path = os.path.join(PROJECT_REPO, cfg_dict['git'][pr_repo_name_in_config]['path'])
    else:
        repo_path = os.path.abspath(cfg_dict['git'][pr_repo_name_in_config]['path'])

    try:
        merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                        pr_cfg['repo_name'], repo_path)
    except:
        git_rebase_abort(repo_path)
        cron.post_pr_comment(pr_cfg['number'], 'Failed to merge the branch')
        return schedule.CancelJob

    # Run AutoPTS server and bot
    bot_options = f'{cfg} {included} {excluded} {bot_options_append}'
    run_test(bot_options, server_options, AUTOPTS_REPO)

    git_checkout(cfg_dict['git'][pr_repo_name_in_config]['branch'], repo_path)

    # report.txt is created at the very end of bot run, so
    # it should exist if bot completed tests fully
    report = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report):
        raise Exception('Bot failed before report creation')

    log(f'{pr_cfg["repo_name"]} PR Job finished')

    # Post in PR comment with results
    cron.post_pr_comment(
        pr_cfg['number'], report_to_review_msg(report))

    # To prevent scheduler from cyclical running of the job
    return schedule.CancelJob


@catch_exceptions(cancel_on_failure=True)
def generic_test_job(cfg, server_options, included='', excluded='',
                     bisect=None, bot_options_append='', **kwargs):
    log(f'Started {cfg} Job')

    cfg_dict = load_config(cfg)

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

        log('Copied database from {}'.format(test_case_db_path))
        shutil.copy(test_case_db_path, autopts_test_case_db)

    workspace_path = find_workspace_in_tree(
        os.path.join(AUTOPTS_REPO, 'autopts/workspaces'), cfg_dict['auto_pts']['workspace'])
    clear_workspace(workspace_path)

    # To prevent update of the project repo by bot, set 'update_repo'
    # to False in zephyr['git'] of config.py

    bot_options = f'{cfg} {included} {excluded} {bot_options_append}'
    run_test(bot_options, server_options, AUTOPTS_REPO)

    # report.txt is created at the very end of bot run, so
    # it should exist if bot completed tests fully
    report = os.path.join(AUTOPTS_REPO, 'report.txt')
    if not os.path.exists(report):
        raise Exception('Bot failed before report creation')

    if bisect:
        Bisect(bisect).run_bisect(report)

    log(f'{cfg} Job finished')


def update_repos_job(cfg, **kwargs):
    log(f'Started {cfg} Job')

    cfg_dict = load_config(cfg)

    update_repos('', cfg_dict['git'])

    log(f'The {cfg} Job finished')


set_run_test_fun(run_test)
