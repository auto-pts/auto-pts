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
import logging
import sys
import signal
import pythoncom
import schedule
import threading
from datetime import timedelta, datetime
from time import sleep
from argparse import Namespace
from os.path import dirname, abspath

# Needed if autopts is not installed as a module
AUTOPTS_REPO=dirname(dirname(dirname(abspath(__file__))))
sys.path.extend([AUTOPTS_REPO])

from autopts.utils import get_global_end, set_global_end, have_admin_rights
from autopts.bot.common import get_absolute_module_path, load_module_from_path
from tools.cron.common import kill_processes, set_cron_cfg
from tools.cron.cron_gui import CronGUI, RequestPuller

pullers = {}
cron_gui = None
log = logging.info


class CliParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description='AutoPTS cron', add_help=True)

        self.add_argument("config_path", type=str,
                          help="Path to cron config .py file.")

        self.add_argument('--gui', action='store_true', default=False,
                          help="Open cron window.")


def run_pending_thread_func():
    pythoncom.CoInitialize()

    while not get_global_end():
        schedule.run_pending()
        sleep(1)

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


def pr_choose_start_time(delay):
    start_time = datetime.today() + delay
    run_time = 0.0  # TODO run time estimation and prioritising
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


def pr_job_finish_wrapper(job_func, job_name, *args, **kwargs):
    result = job_func(*args, **kwargs)

    if cron_gui:
        schedule.cancel_job(schedule.get_jobs(job_name)[0])
        cron_gui_update_job_list()

    return result


def schedule_pr_job(cron, pr_url, tag_cfg, pr_cfg, delay):
    start_time = pr_choose_start_time(delay)
    job_name = f'PR {pr_url}'

    getattr(schedule.every(), start_time.strftime('%A').lower()) \
        .at(start_time.strftime('%H:%M:%S')) \
        .do(lambda *args, **kwargs: pr_job_finish_wrapper(
            tag_cfg.func, job_name, *args, **kwargs),
            cron=cron, pr_cfg=pr_cfg, **vars(tag_cfg)).tag(job_name)

    if cron_gui:
        cron_gui_update_job_list()

    return start_time


def cancel_job(name):
    log(f'Canceled {name} job')
    job = schedule.get_jobs(name)[0]
    schedule.cancel_job(job)


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


def main():
    def sigint_handler(sig, frame):
        get_global_end()
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, prev_sigint_handler)
            threading.Thread(target=signal.raise_signal(signal.SIGINT)).start()
        else:
            kill_processes('python.exe')
            kill_processes('PTS.exe')
            kill_processes('Fts.exe')

    args = CliParser().parse_args()

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
            cfg = cron.tags[tag].cfg

            job_config = vars(cron_config.default_job).copy()
            job_config.update(vars(cron.tags[tag]))
            cron.tags[tag] = Namespace(**job_config)

            if not get_absolute_module_path(cfg):
                raise Exception('{} config does not exists!'.format(cfg))

    for job in cron_config.cyclical_jobs:
        cfg = job.cfg
        if not get_absolute_module_path(cfg):
            raise Exception('{} config does not exists!'.format(cfg))

    prev_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, sigint_handler)

    for job in cron_config.cyclical_jobs:
        job_dict = vars(cron_config.default_job).copy()
        job_dict.update(vars(job))

        if 'name' in job_dict:
            job_name = job_dict['name']
        else:
            job_name = f'cyclical {job_dict["day"]} {job_dict["hour"]} {job_dict["cfg"]}'

        getattr(schedule.every(), job_dict['day']).at(job_dict['hour']) \
            .do(job.func, **job_dict).tag(job_name)

    try:
        for cron in cron_config.github_crons:
            cron.schedule_job_cb = schedule_pr_job
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
