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

"""AutoPTS Cron with GitHub CI

Schedule cyclical jobs or trigger them with magic sentence in Pull Request comment.

Copy this file to root dir of auto-pts repo and adjust to your preferences.

If your ssh private key has password, before running the cron,
start ssh agent in the same console:
$ eval `ssh-agent`
$ ssh-add path/to/id_rsa
"""
import argparse
import copy
import json
import logging
import re
import sys
import signal
import schedule
import threading
from argparse import Namespace
from datetime import timedelta, datetime
from time import sleep
from os.path import dirname, abspath

# Needed if autopts is not installed as a module
AUTOPTS_REPO=dirname(dirname(dirname(abspath(__file__))))
sys.path.extend([AUTOPTS_REPO])

from autopts.utils import get_global_end, set_global_end, have_admin_rights, terminate_process
from autopts.bot.common import load_module_from_path
from tools.cron.estimations import get_estimations
from tools.cron.common import set_cron_cfg, load_config
from tools.cron.cron_gui import CronGUI, RequestPuller


if sys.platform == 'win32':
    import pythoncom


pullers = {}
cron_gui = None
log = logging.info
cron_config = None


class CancelJob:
    def __init__(self, canceled):
        self.canceled = canceled


class CliParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description='AutoPTS cron', add_help=True)

        self.add_argument("config_path", type=str,
                          help="Path to cron config .py file.")

        self.add_argument('--gui', action='store_true', default=False,
                          help="Open cron window.")


class AutoPTSMagicTagParser(argparse.ArgumentParser):
    def __init__(self, add_help=True):
        super().__init__(description='Github Magic Tag parser', add_help=add_help)

        self.add_argument("included", nargs='*', default=[],
                          help="abc")

        self.add_argument("-e", "--excluded", nargs='+', default=[],
                          help="Names of test cases to exclude. Groups of "
                               "test cases can be specified by profile names")

        self.add_argument("--test_case_limit", "--test-case-limit", nargs='?', type=int, default=0,
                          help="Limit of test cases to run")


def run_pending_thread_func():
    if sys.platform == 'win32':
        pythoncom.CoInitialize()

    while not get_global_end():
        schedule.run_pending()
        sleep(1)

    if sys.platform == 'win32':
        pythoncom.CoUninitialize()


def cron_puller_toggled(*args):
    name, enable, pull_time_offset = args
    for cron in cron_config.github_crons:
        if cron.name == name:
            cron.set_pull_time_offset(pull_time_offset)
            cron.enabled = enable

            if enable:
                log(f'Resumed pulling for puller {cron.name}')
            else:
                log(f'Paused pulling for puller {cron.name}')
            break


def pr_choose_start_time(job_config):
    prio = job_config.get('job_priority', 0)
    est_duration = job_config.get('estimated_duration', timedelta(minutes=1))
    delay = job_config.get('delay', timedelta(minutes=1))
    start_time = datetime.today() + delay
    all_jobs = schedule.jobs[:]

    # prio == 0 means the highest priority to start
    if prio > 0:
        for job in all_jobs:
            if start_time < job.next_run < start_time + est_duration and \
               prio >= job.job_func.keywords.get('job_priority', 0):
                start_time = job.next_run + job.job_func.keywords.get(
                    'estimated_duration', timedelta(minutes=1))

    return start_time


def pr_job_finish_wrapper(job_func, job_name, *args, **kwargs):
    try:
        result = job_func(*args, **kwargs)
    finally:
        schedule.cancel_job(schedule.get_jobs(job_name)[0])
        if cron_gui:
            cron_gui_update_job_list()

    return result


def cron_comment(cron, pr_number, text):
    rsp = cron.post_pr_comment(pr_number, f'{text}')
    log(text)
    return rsp


def check_supported_profiles(test_case_prefixes, job_config):
    if not job_config['included']:
        # 'included' parameter not specified in job config. Assume
        # all profiles supported on this server.
        return True, test_case_prefixes

    job_config_prefixes = re.sub(r'\s+', r' ', job_config['included']).strip().split(' ')

    test_cases_to_run = []
    for prefix in test_case_prefixes:
        for profile in job_config_prefixes:
            if prefix.startswith(profile):
                # At least one prefix matched
                test_cases_to_run.append(prefix)

    if test_cases_to_run:
        return True, test_cases_to_run

    # Not even a single test case prefix is supported on this test server.
    # Ignore the command.
    return False, []


def magic_tag_cb(cron, comment_info):
    magic_tag = comment_info['magic_tag']
    tag_config = cron.tags[magic_tag]
    tag_config['magic_tag_cb'](cron, comment_info)


def autopts_magic_tag_cb(cron, comment_info):
    body = comment_info['comment_body']
    magic_tag = comment_info['magic_tag']
    command_args = body[len(magic_tag):].split(' ')
    command_args = [x for x in command_args if x.strip()]

    configs = []
    for board in cron.tags[magic_tag]['configs']:
        config = copy.deepcopy(cron.tags[magic_tag]['configs'][board])
        parser = config.get('magic_tag_parser', AutoPTSMagicTagParser)()
        try:
            parsed_args = parser.parse_args(command_args)
            if len(parsed_args.included) == 0 and 'default_test_cases' in config:
                parsed_args.included = config['default_test_cases'].split()
        except BaseException as e:
            log(e)
            continue

        is_supported, supported_test_cases = check_supported_profiles(parsed_args.included, config)
        if not is_supported:
            log('Magic tag detected but no test case can be matched')
            continue

        config['included'] = supported_test_cases
        config['excluded'] = parsed_args.excluded
        config['board'] = board
        config['test_case_limit'] = parsed_args.test_case_limit
        configs.append(config)

    if not configs:
        return

    pr_number = comment_info['pr_number']
    pr_info = cron.get_pr_info(pr_number)
    if not pr_info:
        log('Failed to read PR info')
        return

    pr_info.update(comment_info)

    for config in configs:
        schedule_pr_job(cron, pr_info, config)


def schedule_pr_job(cron, pr_info, job_config):
    try:
        cfg_dict = load_config(job_config['cfg'])
        included_tc = job_config['included']
        excluded_tc = job_config['excluded']

        test_cases, est_duration = get_estimations(cfg_dict, included_tc, excluded_tc,
                                                   job_config['test_case_limit'])

        if est_duration:
            # Estimated duration does not include build/flash time. Let's add some
            # minutes just to get closer to real time for short test runs.
            est_duration += timedelta(minutes=10)

        test_case_count = len(test_cases)

        if test_case_count > 0:
            if job_config['test_case_limit']:
                job_config['included'] = test_cases

            estimations = f', test case count: {test_case_count}, ' \
                          f'estimated duration: {est_duration}'
            estimations += f'<details><summary>Test cases to be run</summary>{"<br>".join(test_cases)}</details>\n'
        else:
            estimations = f', test case count: estimation not available'

        job_config.pop('test_case_limit')
        job_config['estimated_duration'] = est_duration
    except Exception as e:
        # Probably the configuration missed some parameters,
        # skip estimation this time.
        logging.exception(e)
        estimations = ''

    start_time = pr_choose_start_time(job_config)
    start_time_str = start_time.strftime('%H:%M:%S')
    post_text = f'Scheduled PR {pr_info["html_url"]}, board: {job_config["board"]}, ' \
                f'estimated start time: {start_time_str}{estimations}'

    pr_number = pr_info['pr_number']
    rsp = cron_comment(cron, pr_number, post_text)
    cron_comment_url = json.loads(rsp.text)['html_url']
    job_name = f'PR {cron_comment_url}'

    job_config['included'] = ' '.join(job_config['included'])
    job_config['excluded'] = ' '.join(job_config['excluded'])
    job_config['cancel_job'] = CancelJob(False)

    if pr_info['html_url'].startswith('https://github.com/auto-pts/auto-pts'):
        try:
            vm_autopts = job_config['remote_machine']['git']['autopts']
            vm_autopts['checkout_cmd'] = f"git fetch {vm_autopts['remote']} & " \
                                         f"git fetch {vm_autopts['remote']} pull/{pr_number}/head & " \
                                         f"git checkout FETCH_HEAD & " \
                                         f"set GIT_COMMITTER_NAME=Name & set GIT_COMMITTER_EMAIL=temp@example.com & " \
                                         f"git pull --rebase {vm_autopts['remote']} {vm_autopts['branch']} > NUL 2>&1"
        except KeyError:
            pass

    getattr(schedule.every(), start_time.strftime('%A').lower()) \
        .at(start_time.strftime('%H:%M:%S')) \
        .do(lambda *args, **kwargs: pr_job_finish_wrapper(
            job_config['func'], job_name, *args, **kwargs),
            cron=cron, pr_cfg=pr_info,
            **job_config).tag(job_name)

    if cron_gui:
        cron_gui_update_job_list()

    return start_time


def cancel_job(name):
    log(f'Canceled {name} job')
    job = schedule.get_jobs(name)[0]
    schedule.cancel_job(job)
    kwargs = job.job_func.keywords
    kwargs['cancel_job'].canceled = True
    if 'pr_cfg' in kwargs and 'cron' in kwargs:
        pr_cfg = kwargs['pr_cfg']
        msg = f'Job triggered with {pr_cfg["html_url"]} has been canceled'
        kwargs['cron'].post_pr_comment(pr_cfg['number'], msg)

    if cron_gui:
        cron_gui_update_job_list()


def cancel_pr_job(cron, comment_info):
    body = comment_info['comment_body']
    magic_tag = comment_info['magic_tag']
    command_args = body[len(magic_tag):].strip().split(' ')
    job_name = f'PR {command_args[0]}'
    cancel_job(job_name)


def cron_gui_update_job_list():
    job_list = []
    for job in schedule.get_jobs():
        job_name = list(job.tags)[0]
        job_list.append({'name': job_name,
                         'info': f"""name: {job_name}
next run: {job.next_run}
job config: {job}"""})
    cron_gui.update_job_list(job_list)


def run_cron_gui():
    global cron_gui
    cron_gui = CronGUI(cancel_job)

    for cron in cron_config.github_crons:
        pullers[cron.name] = RequestPuller(
            name=cron.name, pull_time_offset=cron.pull_time_offset,
            toggle_cb=cron_puller_toggled)

    cron_gui.update_puller_list(pullers.values())

    cron_gui_update_job_list()

    cron_gui.mainloop()


def get_job_config(job, defaults):
    job_config = {}

    if isinstance(defaults, Namespace):
        defaults = vars(defaults)

    if isinstance(job, Namespace):
        job = vars(job)

    # Set cron configs that are default for all jobs
    if defaults is not None:
        job_config.update(defaults)

    # Apply cron configs from config.py
    if 'cfg' in job:
        config = load_config(job['cfg'])

        if 'cron' in config:
            job_config.update(config['cron'])

    # Overwrite default/config.py parameters with values
    # directly specified in job config namespace.
    job_config.update(job)

    return job_config


def main():
    def sigint_handler(sig, frame):
        get_global_end()
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, prev_sigint_handler)
            threading.Thread(target=signal.raise_signal(signal.SIGINT)).start()
        else:
            terminate_process(name='PTS')
            terminate_process(name='Fts')
            terminate_process(cmdline='autoptsserver.py')
            terminate_process(cmdline='autoptsclient_bot.py')

    args = CliParser().parse_args()

    global cron_config
    cron_config = load_module_from_path(args.config_path)

    if not cron_config:
        sys.exit(f'Could not load cron config from path {args.config_path}')

    set_cron_cfg(cron_config)

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    log('Cron started')

    if have_admin_rights():  # root privileges are not needed
        log('Please do not run this program as root.')
        sys.exit(1)

    for cron in cron_config.github_crons:
        for tag in cron.tags:
            for board in cron.tags[tag]['configs']:
                cron.tags[tag]['configs'][board] = get_job_config(
                    cron.tags[tag]['configs'][board], getattr(cron_config, 'default_job', None))

            if 'magic_tag_cb' not in cron.tags[tag]:
                cron.tags[tag]['magic_tag_cb'] = autopts_magic_tag_cb

        cron.tags['#AutoPTS cancel'] = {'magic_tag_cb': cancel_pr_job}

    for job in cron_config.cyclical_jobs:
        job_config = get_job_config(job, getattr(cron_config, 'default_job', None))
        job_config['cancel_job'] = CancelJob(False)

        if 'name' in job_config:
            job_name = job_config['name']
        else:
            job_name = f'cyclical {job_config["day"]} {job_config["hour"]} {job_config["cfg"]}'

        getattr(schedule.every(), job_config['day']).at(job_config['hour']) \
            .do(job.func, **job_config).tag(job_name)

    prev_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, sigint_handler)

    try:
        for cron in cron_config.github_crons:
            cron.handle_magic_tag = magic_tag_cb
            cron.start()

        if args.gui:
            threading.Thread(target=run_pending_thread_func).start()
            run_cron_gui()
        else:
            run_pending_thread_func()
    finally:
        for cron in cron_config.github_crons:
            cron.end = True
        set_global_end()

    log('Cron finished')


if __name__ == '__main__':
    main()
