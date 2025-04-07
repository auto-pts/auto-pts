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
import copy
import functools
import json
import logging
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import traceback
from datetime import date, datetime, timedelta
from os import listdir
from os.path import abspath, dirname
from pathlib import Path
from time import sleep, time

import requests
import schedule


AUTOPTS_REPO = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, AUTOPTS_REPO)

from autopts.bot.common import load_module_from_path, save_files
from autopts.bot.common_features.github import update_repos
from autopts.bot.common_features.mail import send_mail
from autopts.config import FILE_PATHS, generate_file_paths
from autopts.utils import get_global_end, terminate_process
from tools.cron.autopts_bisect import Bisect, set_run_test_fun
from tools.cron.compatibility import (
    find_by_autopts_hash,
    find_by_project_hash,
    find_by_pts_ver,
    find_latest,
    get_hash_from_reference,
)
from tools.cron.remote_terminal import RemoteTerminalClientProxy
from tools.merge_db import TestCaseTable


if sys.platform == 'win32':
    import wmi

log = logging.info
CRON_CFG = {}
mimetypes.add_type('text/plain', '.log')


def set_cron_cfg(cfg):
    global CRON_CFG
    CRON_CFG = cfg


def catch_exceptions(cancel_on_failure=False):
    def _catch_exceptions(job_func):
        @functools.wraps(job_func)
        def __catch_exceptions(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                log(traceback.format_exc())
                if hasattr(CRON_CFG, 'email'):
                    magic_tag = kwargs['magic_tag'] if 'magic_tag' in kwargs else None
                    send_mail_exception(kwargs['cfg'], CRON_CFG.email, traceback.format_exc(), magic_tag)

                if cancel_on_failure:
                    return schedule.CancelJob
        return __catch_exceptions
    return _catch_exceptions


def catch_connection_error(func):
    def _catch_exceptions(*args, **kwargs):
        while not get_global_end():
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                log('Internet connection error')
                sleep(1)
    return _catch_exceptions


def sleep_job(cancel_object, delay):
    timeout_flag = threading.Event()

    def set_timeout_flag():
        timeout_flag.set()

    timer = threading.Timer(delay, set_timeout_flag)
    timer.start()

    while not cancel_object.canceled and not timeout_flag.is_set():
        sleep(1)

    timer.cancel()


def report_to_review_msg(report_path):
    failed = []
    passed = []
    msg = 'AutoPTS Bot results:\n'

    with open(report_path, 'r') as f:
        f.readline()

        while True:
            line = f.readline()

            if not line:
                break

            if 'PASS' in line:
                passed.append(line.strip())
            else:
                failed.append(line.strip())

    if len(failed) > 0:
        msg += f'<details><summary>Failed tests ({len(failed)})</summary>{"<br>".join(failed)}</details>\n'
    else:
        msg += 'No failed test found.\n'

    if len(passed) > 0:
        msg += f'<details><summary>Successful tests ({len(passed)})</summary>{"<br>".join(passed)}</details>\n'

    return msg


def error_to_review_msg(config):
    error_txt_path = config['file_paths']['ERROR_TXT_FILE']
    msg = 'AutoPTS Bot failed:\n'

    if not os.path.exists(error_txt_path):
        msg += 'Reason unknown'
        return msg

    with open(error_txt_path, 'r') as f:
        while True:
            line = f.readline()

            if not line:
                break

            msg += line

    return msg


def send_mail_exception(conf_name, email_cfg, exception, magic_tag=None):
    if not email_cfg.get('recipients', False):
        log('No recipients in mail config')
        return

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


def clear_workspace(workspace_dir):
    if workspace_dir:
        with os.scandir(workspace_dir) as files:
            for f in files:
                if f.is_dir():
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    try:
                        if not f.name.endswith(('.pqw6', '.pts', '.gitignore', '.xlsx', '.bls', '.bqw')):
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

    return copy.deepcopy(mod.BotProjects[0])


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


def pre_cleanup(config):
    terminate_processes(config)

    pre_cleanup_files(config)

    workspace_path = find_workspace_in_tree(
        os.path.join(config['cron']['autopts_repo'],
                     'autopts/workspaces'),
        config['auto_pts']['workspace'])
    clear_workspace(workspace_path)


def ssh_run_commands(hostname, username, password, commands):
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)

    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd)
        log(f"Command: {cmd}")
        log(stdout.read().decode())
        log(stderr.read().decode())

    client.close()


def ssh_copy_file(hostname, username, password,
                  remote_file_path, local_file_path):
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password)

    sftp = client.open_sftp()
    sftp.get(remote_file_path, local_file_path)

    sftp.close()
    client.close()


def pre_cleanup_files(config):
    file_paths = config['file_paths']
    autopts_repo = config['cron']['autopts_repo']
    project_repo = config['auto_pts']['project_path']

    files_to_save = [
        file_paths['TMP_DIR'],
        file_paths['IUT_LOGS_DIR'],
        file_paths['REPORT_TXT_FILE'],
        file_paths['REPORT_XLSX_FILE'],
        os.path.join(autopts_repo, 'TestCase.db'),
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

        save_files(files_to_save, save_dir)
    except:
        pass


def git_stash_clear(cwd):
    cmd = 'git stash clear'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=cwd)


def git_reset_head(cwd):
    cmd = 'git reset HEAD --hard'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=cwd)
    cmd = 'git clean -fdx'
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


def parse_yaml(file_path):
    import yaml
    parsed_dict = {}

    if os.path.exists(file_path):
        with open(file_path, 'r') as stream:
            parsed_dict = yaml.safe_load(stream)

    return parsed_dict


def start_vm(config, checkout_repos=False):
    # Reset the VM state
    config = config['cron']

    if checkout_repos:
        git_reset_head(config['vm']['path'])

        # Checkout the VM instance to branch with specific PTS version
        if 'pts_ver' in config:
            vm_yaml = parse_yaml(config['vm']['yaml'])
            vm_commit = vm_yaml[config['pts_ver']]
            git_checkout(vm_commit, config['vm']['path'])

    log(f"Starting VM with: {config['vm']['vm_start_cmd']}")
    subprocess.Popen(shlex.split(config['vm']['vm_start_cmd']),
                     shell=False,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     cwd=config['vm']['path'])

    with RemoteTerminalClientProxy(config['remote_machine']['terminal_ip'],
                                   config['remote_machine']['terminal_port'],
                                   config['remote_machine'].get(
                                       'socket_timeout', None)
                                   ) as client:

        timeout_flag = threading.Event()

        def set_timeout_flag():
            timeout_flag.set()

        timer = threading.Timer(config['vm']['max_start_time'], set_timeout_flag)
        timer.start()

        while True:
            try:
                log(client.run_command(f"echo Connected", None))
                break
            except BaseException:
                if timeout_flag.is_set():
                    return

                log("Awaiting VM to start...")
                sleep(5)

        timer.cancel()


def start_remote_autoptsserver(config, checkout_repos):
    with RemoteTerminalClientProxy(config['remote_machine']['terminal_ip'],
                                   config['remote_machine']['terminal_port'],
                                   config['remote_machine'].get(
                                       'socket_timeout', None)
                                   ) as client:
        if checkout_repos:
            for repo in config['remote_machine']['git']:
                repo_info = config['remote_machine']['git'][repo]

                if 'checkout_cmd' in repo_info:
                    log(client.run_command(repo_info['checkout_cmd'], repo_info['path']))
                else:
                    log(client.run_command(f"git fetch {repo_info['remote']}", repo_info['path']))
                    log(client.run_command(f"git checkout {repo_info['remote']}/{repo_info['branch']}", repo_info['path']))

        log(f"Starting process on the remote machine: {config['server_start_cmd']}")
        log(client.open_process(config['server_start_cmd'],
                                config['remote_machine']['git']['autopts']['path']))


def close_vm(config):
    config = config['cron']
    log(f"Closing VM with: {config['vm']['vm_close_cmd']}")
    try:
        with RemoteTerminalClientProxy(config['remote_machine']['terminal_ip'],
                                       config['remote_machine']['terminal_port'],
                                       config['remote_machine'].get('close_vm_socket_timeout', 5)
                                       ) as client:
            log(client.run_command(config['vm']['vm_close_cmd'], None))
        sleep(config['vm']['max_close_time'])
    except BaseException as e:
        log(f"Remote server at IP {config['remote_machine']['terminal_ip']} "
            f"port {config['remote_machine']['terminal_port']} is not reachable")


def close_remote_autoptsserver(config):
    log(f"Closing remote autoptsserver and PTS")
    try:
        config = config['cron']['remote_machine']
        with RemoteTerminalClientProxy(config['terminal_ip'],
                                       config['terminal_port'],
                                       config.get('close_remote_autoptsserver_socket_timeout', 5)
                                       ) as client:
            client.terminate_process(None, 'PTS', None)
            client.terminate_process(None, 'FTS', None)
            client.terminate_process(None, None, 'autoptsserver.py')
    except BaseException as e:
        log(f"Remote server at IP {config['terminal_ip']} port {config['terminal_port']} is not reachable")


def win_start_autoptsserver(config):
    log(f"Running: {config['server_start_cmd']}")
    srv_process = subprocess.Popen(shlex.split(config['server_start_cmd']),
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=config['autopts_repo'])
    return srv_process


def terminate_processes(config):
    if 'remote_machine' in config['cron']:
        close_remote_autoptsserver(config)
        terminate_process(cmdline='autoptsclient_bot.py')
    elif sys.platform == 'win32':
        terminate_process(name='PTS')
        terminate_process(name='Fts')
        terminate_process(cmdline='autoptsserver.py')
        terminate_process(cmdline='autoptsclient_bot.py')

    if 'vm' in config['cron']:
        close_vm(config)

    if 'active_hub_server_start_cmd' in config['cron']:
        terminate_process(cmdline='active_hub_server.py')


def _start_processes(config, checkout_repos):
    srv_process = None

    if 'active_hub_server_start_cmd' in config['cron']:
        log(f"Running: {config['cron']['active_hub_server_start_cmd']}")
        subprocess.Popen(config['cron']['active_hub_server_start_cmd'],
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         cwd=config['cron']['autopts_repo'])

    if 'vm' in config['cron']:
        try:
            start_vm(config, checkout_repos=checkout_repos)
        except BaseException as e:
            close_vm(config)
            raise e

    config = config['cron']

    if 'remote_machine' in config:
        # Start the autoptsserver.py on the remote machine
        start_remote_autoptsserver(config, checkout_repos)
    elif sys.platform == 'win32' and config['server_start_cmd']:
        # Start subprocess running autoptsserver.py
        srv_process = win_start_autoptsserver(config)
    # else assume that autoptsserver is already available somewhere

    sleep_job(config['cancel_job'], config['bot_start_delay'])
    if config['cancel_job'].canceled:
        if srv_process and srv_process.poll() is None:
            srv_process.terminate()

        return

    log(f"Running: {config['bot_start_cmd']}")
    bot_process = subprocess.Popen(config['bot_start_cmd'],
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   cwd=config['autopts_repo'])

    return srv_process, bot_process


def _restart_processes(config):
    while not config['cron']['cancel_job'].canceled:
        try:
            terminate_processes(config)
            return _start_processes(config, checkout_repos=False)
        except OSError:
            log(traceback.format_exc())


def _run_test(config):
    test_cases_completed = False
    backup = config['auto_pts'].get('use_backup', False)
    timeguard = config['cron']['test_run_timeguard']
    startup_fail_count = config['cron'].get('startup_fail_max_count', 2)
    results_file_path = config['file_paths']['TC_STATS_JSON_FILE']
    all_stats_file_path = config['file_paths']['ALL_STATS_JSON_FILE']
    report_file_path = config['file_paths']['REPORT_TXT_FILE']
    error_file_path = config['file_paths']['ERROR_TXT_FILE']

    srv_process, bot_process = _start_processes(config, checkout_repos=True)
    last_check_time = time()

    # Main thread waits for at least one of subprocesses to finish
    while not config['cron']['cancel_job'].canceled:
        sleep_job(config['cron']['cancel_job'], config['cron']['check_interval'])

        if os.path.exists(error_file_path):
            break

        if srv_process and srv_process.poll() is not None:
            log('server process finished.')
            break

        if bot_process.poll() is not None:
            log('bot process finished.')
            if os.path.exists(report_file_path):
                break

            elif backup:
                log("Autopts bot terminated before report creation. Restarting processes...")
                srv_process, bot_process = _restart_processes(config)
                sleep_job(config['cron']['cancel_job'], timeguard)

        if not backup:
            continue

        current_time = time()

        if not test_cases_completed and not os.path.exists(results_file_path):
            if timedelta(seconds=current_time - last_check_time) > timedelta(seconds=timeguard):
                if startup_fail_count == 0:
                    log("Test run has not been started on time. No more retries...")
                    break

                startup_fail_count -= 1
                log("Test run has not been started on time. Restarting processes...")
                srv_process, bot_process = _restart_processes(config)

            continue

        startup_fail_count = config['cron'].get('startup_fail_max_count', 2)
        last_check_time = current_time

        if (not test_cases_completed and
                timedelta(seconds=current_time - os.path.getmtime(results_file_path)) > timedelta(seconds=timeguard)):
            if os.path.exists(all_stats_file_path):
                try:
                    with open(all_stats_file_path, 'r') as f:
                        data = json.load(f)
                        test_cases_completed = data.get('test_run_completed', False)
                except BaseException as e:
                    log(e)

            # Do not restart bot if test_run_completed, because pulling PTS logs at the end
            # of the bot run takes a while, and it should not be interrupted.
            if test_cases_completed:
                log("Bot completed running the test cases. Waiting for report to be generated ...")
            else:
                log("Test run results have not been updated for a while. Restarting processes...")
                srv_process, bot_process = _restart_processes(config)
                sleep_job(config['cron']['cancel_job'], timeguard)


def run_test(config):
    if config['cron']['cancel_job'].canceled:
        return

    try:
        _run_test(config)
    except:
        log(traceback.format_exc())
    finally:
        terminate_processes(config)


def parse_test_cases_from_comment(pr_cfg):
    included = re.sub(r'\s+', r' ', pr_cfg['comment_body'][len(pr_cfg['magic_tag']):]).strip()
    excluded = ''

    return included, excluded


def get_cron_config(cfg, **kwargs):
    cron_config = load_config(cfg)
    if 'cron' not in cron_config:
        cron_config['cron'] = {}

    config = cron_config['cron']
    config.update(kwargs)

    if 'project_path' not in config:
        config['project_path'] = cron_config['auto_pts']['project_path']

    update_repos(config['project_path'], cron_config['git'])

    if 'autopts_repo' not in config:
        config['autopts_repo'] = AUTOPTS_REPO

    file_paths = cron_config.get('file_paths', {})
    if 'TMP_DIR' not in file_paths:
        file_paths['TMP_DIR'] = os.path.join(config['autopts_repo'],
                                             os.path.basename(FILE_PATHS['TMP_DIR']))

    cron_config['file_paths'] = generate_file_paths(
        file_paths=file_paths, autopts_root_dir=config['autopts_repo'])

    if 'compatibility_csv' in config:
        if 'project_hash' in config:
            project_hash = get_hash_from_reference(config['project_path'], config['project_hash'])
            pts_ver, autopts_hash, _ = find_by_project_hash(
                config['compatibility_csv'], config['project_path'], project_hash)
        elif 'autopts_hash' in config:
            autopts_hash = get_hash_from_reference(config['autopts_repo'], config['project_hash'])
            pts_ver, _, project_hash = find_by_autopts_hash(
                config['compatibility_csv'], config['autopts_repo'], autopts_hash)
        elif 'pts_ver' in config:
            pts_ver = config['pts_ver']
            _, autopts_hash, project_hash = find_by_pts_ver(
                config['compatibility_csv'], pts_ver)
        else:
            pts_ver, autopts_hash, project_hash = find_latest(config['compatibility_csv'])

        config['pts_ver'] = pts_ver
        config['autopts_hash'] = autopts_hash
        config['project_hash'] = project_hash

    if 'remote_machine' in config and 'autopts_hash' in config:
        config['remote_machine']['git']['autopts']['branch'] = config['autopts_hash']

    if 'pre_cleanup' not in config:
        config['pre_cleanup'] = pre_cleanup

    if 'bot_options_append' not in config:
        config['bot_options_append'] = ''

    if 'included' in config and config['included'].strip():
        config['bot_options_append'] += f" -c {config['included']}"

    if 'excluded' in config and config['excluded'].strip():
        config['bot_options_append'] += f" -e {config['excluded']}"

    if 'test_case_limit' in config and config['test_case_limit']:
        config['bot_options_append'] += f" --test_case_limit {config['test_case_limit']}"

    if 'bot_start_cmd' not in config:
        bot_args = f'{cfg} {config["bot_options_append"]}'
        config['bot_start_cmd'] = \
            f'python autoptsclient_bot.py {bot_args} >> stdout_autoptsbot.log 2>&1'

    if 'bot_start_delay' not in config:
        config['bot_start_delay'] = 60  # seconds

    if 'server_start_cmd' not in config:
        server_options = config.get('server_options', '')
        config['server_start_cmd'] = \
            f'python autoptsserver.py {server_options} >> stdout_autoptsserver.log 2>&1'

    if 'test_run_timeguard' not in config:
        config['test_run_timeguard'] = 20 * 60  # seconds

    if 'check_interval' not in config:
        config['check_interval'] = 60  # seconds

    return cron_config


def _generic_pr_job(cron, cfg, pr_cfg, **kwargs):
    if kwargs['cancel_job'].canceled:
        return None

    log('Started PR Job: repo_name={repo_name} PR={number} src_owner={source_repo_owner}'
        ' branch={source_branch} head_sha={head_sha} comment={comment_body} '
        'magic_tag={magic_tag} cfg={cfg}'.format(**pr_cfg, cfg=cfg))

    config = get_cron_config(cfg, **kwargs)

    # Path to the project
    PROJECT_REPO = config['auto_pts']['project_path']

    # Delete AutoPTS logs, tmp files, old bin directories, kill old PTS.exe, ...
    config['cron']['pre_cleanup'](config)

    # Update repo.
    # To prevent update of the repo by bot, remember to set 'update_repo'
    # to False in m['git']['repo_name']['update_repo'] of config.py
    pr_repo_name_in_config = config['cron']['pr_repo_name_in_config']
    config['git'][pr_repo_name_in_config]['update_repo'] = True
    update_repos(PROJECT_REPO, config['git'])

    # Merge PR branch into local instance of tested repo
    if not os.path.isabs(config['git'][pr_repo_name_in_config]['path']):
        repo_path = os.path.join(PROJECT_REPO, config['git'][pr_repo_name_in_config]['path'])
    else:
        repo_path = os.path.abspath(config['git'][pr_repo_name_in_config]['path'])

    try:
        merge_pr_branch(pr_cfg['source_repo_owner'], pr_cfg['source_branch'],
                        pr_cfg['repo_name'], repo_path)
    except:
        git_rebase_abort(repo_path)
        return 'Failed to merge the PR branch'

    if 'mail' in config and 'additional_info_path' in config['mail']:
        with open(config['mail']['additional_info_path'], 'w') as file:
            file.write(f'PR comment: {pr_cfg["html_url"]}')

    # Run AutoPTS server and bot
    run_test(config)

    git_checkout(config['git'][pr_repo_name_in_config]['branch'], repo_path)

    if kwargs['cancel_job'].canceled:
        return None

    # report.txt is created at the very end of bot run, so
    # it should exist if bot completed tests fully
    report = os.path.join(config['cron']['autopts_repo'], 'report.txt')
    if not os.path.exists(report):
        return error_to_review_msg(config)

    log(f'{pr_cfg["repo_name"]} PR Job finished')

    return report_to_review_msg(report)


@catch_exceptions(cancel_on_failure=True)
def generic_pr_job(cron, cfg, pr_cfg, **kwargs):
    msg = 'Job failed at setup'
    try:
        msg = _generic_pr_job(cron, cfg, pr_cfg, **kwargs)
    finally:
        if msg:
            cron.post_pr_comment(pr_cfg['number'], msg)

    # To prevent scheduler from cyclical running of the job
    return schedule.CancelJob


@catch_exceptions(cancel_on_failure=True)
def generic_test_job(cfg, *args, **kwargs):
    log(f'Started {cfg} Job')

    config = get_cron_config(cfg, **kwargs)

    config['cron']['pre_cleanup'](config)

    if 'autopts_hash' in config['cron']:
        # Checkout AutoPTS to selected version
        git_checkout(config['cron']['autopts_hash'],
                     config['cron']['autopts_repo'])

    run_test(config)

    if kwargs['cancel_job'].canceled:
        return schedule.CancelJob

    # report.txt is created at the very end of bot run, so
    # it should exist if bot completed tests fully
    report = os.path.join(config['cron']['autopts_repo'], 'report.txt')
    if not os.path.exists(report):
        raise Exception('Bot failed before report creation')

    if 'bisect' in config:
        Bisect(config['bisect']).run_bisect(report)

    log(f'{cfg} Job finished')


def update_repos_job(cfg, **kwargs):
    log(f'Started {cfg} Job')

    cfg_dict = load_config(cfg)

    update_repos('', cfg_dict['git'])

    log(f'The {cfg} Job finished')


def start_vm_job(cfg, **kwargs):
    log(f'Started {start_vm_job.__name__} Job, config: {cfg}')

    config = load_config(cfg)

    start_vm(config, checkout_repos=True)

    log(f'The {start_vm_job.__name__} Job finished')


def close_vm_job(cfg, **kwargs):
    log(f'Started {start_vm_job.__name__} Job, config: {cfg}')

    config = load_config(cfg)

    close_vm(config)

    log(f'The {start_vm_job.__name__} Job finished')


def merge_db_job(cfg, **kwargs):
    log(f'Started {merge_db_job.__name__} Job, config: {cfg}')

    config = load_config(cfg)
    config = config['cron']['merge_db']

    if os.path.exists(config['merged_db_file']):
        os.remove(config['merged_db_file'])

    database = TestCaseTable(config['database_files'], config['merged_db_file'])
    database.merge_databases()

    log(f'The {merge_db_job.__name__} Job finished')


def newt_update_job(cfg, **kwargs):
    log(f'Started {newt_update_job.__name__} Job, config: {cfg}')

    config = get_cron_config(cfg, **kwargs)

    prj_path = config['auto_pts']['project_path']
    newt_repo_path = config['auto_pts']['newt_repo_path']
    newt_exe = config['auto_pts']['newt_exe']
    newt_path = config['auto_pts']['newt_path']

    cmd = f'git pull origin && ./build.sh && mv {newt_exe} {newt_path}'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=newt_repo_path)

    cmd = 'newt upgrade'
    log(f'Running: {cmd}')
    check_call(cmd.split(), cwd=prj_path)

    log(f'The {newt_update_job.__name__} Job finished')


set_run_test_fun(run_test)
