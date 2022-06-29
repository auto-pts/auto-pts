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
import sys
import signal
import schedule
import threading
import cron_config
from time import sleep
from argparse import Namespace
from os.path import dirname, abspath
from autopts.winutils import have_admin_rights
from tools.cron.common import kill_processes, set_end as set_end_common, set_cron_cfg

END = False
AUTOPTS_REPO=dirname(dirname(dirname(abspath(__file__))))


def set_end():
    global END
    END = True
    set_end_common()


if __name__ == '__main__':
    def sigint_handler(sig, frame):
        set_end()
        if sys.platform != 'win32':
            signal.signal(signal.SIGINT, prev_sigint_handler)
            threading.Thread(target=signal.raise_signal(signal.SIGINT)).start()
        else:
            kill_processes('python.exe')
            kill_processes('PTS.exe')
            kill_processes('Fts.exe')

    print('Cron started')

    if have_admin_rights():  # root privileges are not needed
        print('Please do not run this program as root.')
        sys.exit(1)

    for cron in cron_config.github_crons:
        for tag in cron.tags:
            cfg = cron.tags[tag].cfg

            job_config = vars(cron_config.default_job).copy()
            job_config.update(vars(cron.tags[tag]))
            cron.tags[tag] = Namespace(**job_config)

            if not os.path.exists(os.path.join(AUTOPTS_REPO, 'autopts/bot/{}.py'.format(cfg))):
                raise Exception('{} config does not exists!'.format(cfg))

    for job in cron_config.cyclical_jobs:
        cfg = job.cfg
        if not os.path.exists(os.path.join(AUTOPTS_REPO, 'autopts/bot/{}.py'.format(cfg))):
            raise Exception('{} config does not exists!'.format(cfg))

    prev_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, sigint_handler)

    for job in cron_config.cyclical_jobs:
        job_dict = vars(cron_config.default_job).copy()
        job_dict.update(vars(job))

        getattr(schedule.every(), job_dict['day']).at(job_dict['hour']).do(job.func, **job_dict)

    set_cron_cfg(cron_config)

    try:
        for cron in cron_config.github_crons:
            cron.start()

        while not END:
            schedule.run_pending()
            sleep(1)
    finally:
        for cron in cron_config.github_crons:
            cron.end = True
        set_end()

    print('Cron finished')
