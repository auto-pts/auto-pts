#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
# Copyright (c) 2021, Nordic Semiconductor ASA.
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

import collections
import datetime
import importlib
import os
import sys
import time
from pathlib import Path

import serial

from autopts import bot
from autopts.ptsprojects.zephyr import ZEPHYR_PROJECT_URL
from autopts import client as autoptsclient
from autopts.bot.common import BotConfigArgs, BotClient
from autopts.ptsprojects.boards import get_free_device, tty_to_com, release_device, get_tty, get_debugger_snr,\
    get_build_and_flash, get_board_type
from autopts.ptsprojects.testcase_db import DATABASE_FILE
from autopts.ptsprojects.zephyr.iutctl import get_iut, log


PROJECT_NAME = Path(__file__).stem


def flush_serial(tty):
    """Clear the serial port buffer
    :param tty: file path of the terminal
    :return: None
    """
    if not tty:
        return

    if sys.platform == 'win32':
        com = tty_to_com(tty)
        ser = serial.Serial(com, 115200, timeout=5)
        ser.flushInput()
        ser.flushOutput()
    else:
        bot.common.check_call(['while', 'read', '-t', '0', 'var', '<', tty, ';', 'do',
                               'continue;', 'done'])


def apply_overlay(zephyr_wd, cfg_name, overlay):
    """Duplicates default_conf configuration file and applies overlay changes
    to it.
    :param zephyr_wd: Zephyr source path
    :param cfg_name: new configuration file name
    :param overlay: defines changes to be applied
    :return: None
    """
    tester_app_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")
    cwd = os.getcwd()

    os.chdir(tester_app_dir)

    with open(cfg_name, 'w') as config:
        for k, v in list(overlay.items()):
            config.write("{}={}\n".format(k, v))

    os.chdir(cwd)


def zephyr_hash_url(commit):
    """ Create URL for commit in Zephyr
    :param commit: Commit ID to append
    :return: URL of commit
    """
    return "{}/commit/{}".format(ZEPHYR_PROJECT_URL,
                                 commit)


def make_readme_md(start_time, end_time, repos_info, pts_ver):
    """Creates README.md for Github logging repo
    """
    readme_file = 'tmp/README.md'

    Path(os.path.dirname(readme_file)).mkdir(parents=True, exist_ok=True)

    with open(readme_file, 'w') as f:
        readme_body = '''# AutoPTS report

    Start time: {}

    End time: {}

    PTS version: {}

    Repositories:

    '''.format(start_time, end_time, pts_ver)
        f.write(readme_body)

        f.writelines(
            ['\t{}: {} [{}]\n'.format(name, info['commit'], info['desc']) for name, info in repos_info.items()])

    return readme_file


def compose_mail(args, mail_cfg, mail_ctx):
    """ Create a email body
    """

    iso_cal = datetime.date.today().isocalendar()
    ww_dd_str = "WW%s.%s" % (iso_cal[1], iso_cal[2])

    body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session - {} </h1>
    <h2>1. IUT Setup</h2>
    <p><b> Type:</b> Zephyr <br>
    <b> Board:</b> {} <br>
    <b> Source:</b> {} </p>
    <h2>2. PTS Setup</h2>
    <p><b> OS:</b> Windows 10 <br>
    <b> Platform:</b> {} <br>
    <b> Version:</b> {} </p>
    <h2>3. Test Results</h2>
    <p><b>Execution Time</b>: {}</p>
    {}
    {}
    {}
    <h3>Logs</h3>
    {}
    <p>Sincerely,</p>
    <p> {}</p>
    '''.format(ww_dd_str, args["board"], mail_ctx["repos_info"], args['platform'],
               args['pts_ver'], mail_ctx["elapsed_time"], mail_ctx["summary"],
               mail_ctx["regression"], mail_ctx["progresses"],
               mail_ctx["log_url"], mail_cfg['name'])

    if 'subject' in mail_cfg:
        subject = mail_cfg['subject']
    else:
        subject = "AutoPTS test session results"

    subject = "%s - %s" % (subject, ww_dd_str)

    return subject, body


class ZephyrBotConfigArgs(BotConfigArgs):
    def __init__(self, args):
        super().__init__(args)
        self.board_name = args['board']
        self.tty_file = args['tty_file']


class ZephyrBotCliParser(bot.common.BotCliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ZephyrBotClient(BotClient):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.zephyr')
        super().__init__(get_iut, project, 'zephyr', ZephyrBotConfigArgs,
                         ZephyrBotCliParser)
        self.config_default = "prj.conf"

    def apply_config(self, args, config, value):
        if 'overlay' in value:
            apply_overlay(args.project_path, config,
                          value['overlay'])

        log("TTY path: %s" % args.tty_file)

        if not args.no_build:
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)
            build_and_flash(args.project_path, board_type, args.debugger_snr, config)

            flush_serial(args.tty_file)
            time.sleep(10)


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'zephyr', True)


SimpleClient = ZephyrClient
BotCliParser = ZephyrBotCliParser


def main(cfg):
    bot.common.pre_cleanup()

    start_time = time.time()
    start_time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    args = cfg['auto_pts']

    if 'database_file' not in args:
        args['database_file'] = DATABASE_FILE

    args['kernel_image'] = os.path.join(args['project_path'], 'tests',
                                        'bluetooth', 'tester', 'outdir',
                                        'zephyr', 'zephyr.elf')

    if 'git' in cfg:
        repos_info = bot.common.update_repos(args['project_path'], cfg["git"])
        repo_status = bot.common.make_repo_status(repos_info)
    else:
        repos_info = {}
        repo_status = ''

    if 'ykush' in args:
        autoptsclient.board_power(args['ykush'], True)
        time.sleep(1)

    if 'tty_file' not in args:
        if 'debugger_snr' not in args:
            args['tty_file'], args['debugger_snr'] = get_free_device(args['board'])
        else:
            args['tty_file'] = get_tty(args['debugger_snr'])

        if args['tty_file'] is None:
            sys.exit('No free device found!')
    elif 'debugger_snr' not in args:
        args['debugger_snr'] = get_debugger_snr(args['tty_file'])

    try:
        summary, results, descriptions, regressions, progresses, args['pts_ver'], args['platform'] = \
            ZephyrBotClient().run_tests(args, cfg.get('iut_config', {}))
    finally:
        release_device(args['tty_file'])

    results = collections.OrderedDict(sorted(results.items()))

    args_ns = ZephyrBotConfigArgs(args)
    pts_logs, xmls = bot.common.pull_server_logs(args_ns)

    report_file = bot.common.make_report_xlsx(results, summary, regressions,
                                              progresses, descriptions, xmls, PROJECT_NAME)
    report_txt = bot.common.make_report_txt(results, regressions,
                                            progresses, repo_status, PROJECT_NAME)

    end_time = time.time()
    end_time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    url = None
    github_link = None
    report_folder = None

    if 'githubdrive' in cfg or 'gdrive' in cfg:
        iut_logs = 'logs/'
        readme_file = make_readme_md(start_time_stamp, end_time_stamp,
                                     repos_info, args['pts_ver'])
        report_folder = bot.common.make_report_folder(iut_logs, pts_logs, xmls, report_file,
                                                      report_txt, readme_file,
                                                      args['database_file'],
                                                      '_iut_zephyr_' + start_time_stamp)

    if 'githubdrive' in cfg:
        print("Uploading to Github ...")
        commit_msg_pattern = '{branch}_{timestamp}_{commit_sha}'
        branch = 'no_branch'
        commit_sha = 'no_sha'

        if 'commit_msg' in cfg['githubdrive'] and \
                cfg['githubdrive']['commit_msg'] is not None:
            commit_msg_pattern = cfg['githubdrive']['commit_msg']

        if 'git' in cfg:
            commit_sha = repos_info['zephyr']['commit']
            branch = cfg['git']['zephyr']['branch']

        commit_msg = commit_msg_pattern.format(
            timestamp=start_time_stamp, branch=branch, commit_sha=commit_sha)
        github_link, report_folder = bot.common.github_push_report(
            report_folder, cfg['githubdrive'], commit_msg)

    if 'gdrive' in cfg:
        print("Uploading to GDrive ...")
        bot.common.archive_testcases(report_folder, depth=2)
        drive = bot.common.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload_folder(report_folder)

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {"summary": bot.common.status_dict2summary_html(summary),
                    "regression": bot.common.regressions2html(regressions,
                                                              descriptions),
                    "repos_info": repo_status,
                    "progresses": bot.common.progresses2html(progresses,
                                                             descriptions)
                    }

        # Summary

        # Regression and test case description

        # Log in Google drive in HTML format
        if 'gdrive' in cfg and url:
            mail_ctx["log_url"] = bot.common.url2html(url, "Results on Google Drive")

        if 'githubdrive' in cfg and github_link:
            if 'log_url' in mail_ctx:
                mail_ctx["log_url"] += '<br>'
            else:
                mail_ctx["log_url"] = ''
            mail_ctx['log_url'] += bot.common.url2html(github_link, 'Results on Github')

        if 'log_url' not in mail_ctx:
            mail_ctx['log_url'] = 'Not Available'

        # Elapsed Time
        mail_ctx["elapsed_time"] = str(datetime.timedelta(
            seconds=(end_time - start_time)))

        subject, body = compose_mail(args, cfg['mail'], mail_ctx)

        bot.common.send_mail(cfg['mail'], subject, body,
                             [report_file, report_txt])

        print("Done")

    bot.common.cleanup()

    print("\nBye!")
    sys.stdout.flush()
    return 0
