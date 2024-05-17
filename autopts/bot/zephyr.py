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
import logging
import os
import sys
import time
import traceback
from pathlib import Path

import serial

from autopts import bot
from autopts.bot.common_features.github import update_sources
from autopts.ptsprojects.zephyr import ZEPHYR_PROJECT_URL
from autopts import client as autoptsclient

from autopts.bot.common import BotConfigArgs, BotClient, BuildAndFlashException
from autopts.ptsprojects.boards import tty_to_com, release_device, get_build_and_flash, get_board_type
from autopts.ptsprojects.testcase_db import DATABASE_FILE
from autopts.ptsprojects.zephyr.iutctl import get_iut, log
from autopts.bot.common_features import github, report, mail, google_drive

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

    additional_info = ''
    if 'additional_info_path' in mail_cfg:
        try:
            with open(mail_cfg['additional_info_path']) as file:
                additional_info = f'{file.read()} <br>'
        except Exception as e:
            logging.exception(e)

    iso_cal = datetime.date.today().isocalendar()
    ww_dd_str = "WW%s.%s" % (iso_cal[1], iso_cal[2])

    body = f'''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session - {ww_dd_str} </h1>
    {additional_info}
    <h2>1. IUT Setup</h2>
    <p><b> Type:</b> Zephyr <br>
    <b> Board:</b> {args['board']} <br>
    <b> Source:</b> {mail_ctx['repos_info']} </p>
    <h2>2. PTS Setup</h2>
    <p><b> OS:</b> Windows 10 <br>
    <b> Platform:</b> {args['platform']} <br>
    <b> Version:</b> {args['pts_ver']} </p>
    <h2>3. Test Results</h2>
    <p><b>Execution Time</b>: {mail_ctx['elapsed_time']}</p>
    {mail_ctx['summary']}
    <h3>Logs</h3>
    {mail_ctx['log_url']}
    <p>Sincerely,</p>
    <p>{mail_cfg['name']}</p>
'''

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
        self.tty_file = args.get('tty_file', None)


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
        pre_overlay = value.get('pre_overlay', [])
        if type(pre_overlay) == str:
            pre_overlay = [pre_overlay]

        post_overlay = value.get('post_overlay', [])
        if type(post_overlay) == str:
            post_overlay = [post_overlay]

        configs = []
        for name in pre_overlay + [config] + post_overlay:
            if name in self.iut_config and 'overlay' in self.iut_config[name] \
                    and len(self.iut_config[name]['overlay']):
                apply_overlay(args.project_path, name,
                              self.iut_config[name]['overlay'])
            elif not os.path.exists(os.path.join(args.project_path, "tests", "bluetooth", "tester", name)):
                log(f'Overlay {name} is not a file.')
                continue

            configs.append(name)

        # The order is used in the -DOVERLAY_CONFIG="<overlay1>;<...>" option.
        overlays = ';'.join(configs)

        log("TTY path: %s" % args.tty_file)

        if not args.no_build:
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)

            try:
                build_and_flash(args.project_path, board_type, args.debugger_snr,
                                overlays, args.project_repos)

                flush_serial(args.tty_file)
            except BaseException as e:
                traceback.print_exception(e)
                report.make_error_txt('Build and flash step failed')
                raise BuildAndFlashException

            time.sleep(10)

    def start(self, args=None):
        main(self)


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, sys.modules['autopts.ptsprojects.zephyr'], 'zephyr')


BotClient = ZephyrBotClient


def main(bot_client):
    bot.common.pre_cleanup()

    start_time = time.time()
    start_time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    cfg = bot_client.bot_config
    args = cfg['auto_pts']

    if 'database_file' not in args:
        args['database_file'] = DATABASE_FILE

    if 'githubdrive' in cfg:
        update_sources(cfg['githubdrive']['path'],
                       cfg['githubdrive']['remote'],
                       cfg['githubdrive']['branch'], True)

    args['kernel_image'] = os.path.join(args['project_path'], 'tests',
                                        'bluetooth', 'tester', 'outdir',
                                        'zephyr', 'zephyr.elf')

    if 'git' in cfg:
        repos_info = github.update_repos(args['project_path'], cfg["git"])
        repo_status = report.make_repo_status(repos_info)
        args['repos'] = cfg['git']
    else:
        repos_info = {}
        repo_status = ''

    try:
        stats = bot_client.run_tests()
    finally:
        release_device(bot_client.args.tty_file)

    summary = stats.get_status_count()
    results = stats.get_results()
    descriptions = stats.get_descriptions()
    regressions = stats.get_regressions()
    progresses = stats.get_progresses()
    new_cases = stats.get_new_cases()
    deleted_cases = []
    args['pts_ver'] = stats.pts_ver
    args['platform'] = stats.platform

    results = collections.OrderedDict(sorted(results.items()))

    pts_logs, xmls = report.pull_server_logs(bot_client.args)

    report_file = report.make_report_xlsx(results, summary, regressions,
                                          progresses, descriptions, xmls, PROJECT_NAME)
    report_txt = report.make_report_txt(results, regressions,
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

        report_diff_txt, deleted_cases = report.make_report_diff(cfg['githubdrive'], results,
                                                                 regressions, progresses, new_cases)

        report_folder = report.make_report_folder(iut_logs, pts_logs, xmls, report_file,
                                                  report_txt, report_diff_txt, readme_file,
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
        github_link, report_folder = report.github_push_report(
            report_folder, cfg['githubdrive'], commit_msg)

    if 'gdrive' in cfg:
        print("Uploading to GDrive ...")
        report.archive_testcases(report_folder, depth=2)
        drive = google_drive.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload_folder(report_folder)

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {'repos_info': repo_status,
                    'summary': f'''{mail.status_dict2summary_html(summary)}
{mail.regressions2html(regressions, descriptions)}
{mail.progresses2html(progresses, descriptions)}
{mail.new_cases2html(new_cases, descriptions)}
{mail.deleted_cases2html(deleted_cases, descriptions)}''',
                    }

        # Summary

        # Regression and test case description

        # Log in Google drive in HTML format
        if 'gdrive' in cfg and url:
            mail_ctx["log_url"] = mail.url2html(url, "Results on Google Drive")

        if 'githubdrive' in cfg and github_link:
            if 'log_url' in mail_ctx:
                mail_ctx["log_url"] += '<br>'
            else:
                mail_ctx["log_url"] = ''
            mail_ctx['log_url'] += mail.url2html(github_link, 'Results on Github')

        if 'log_url' not in mail_ctx:
            mail_ctx['log_url'] = 'Not Available'

        # Elapsed Time
        mail_ctx["elapsed_time"] = str(datetime.timedelta(
            seconds=(int(end_time - start_time))))

        subject, body = compose_mail(args, cfg['mail'], mail_ctx)

        mail.send_mail(cfg['mail'], subject, body,
                       [report_file, report_txt])

        print("Done")

    bot.common.cleanup()

    print("\nBye!")
    sys.stdout.flush()
    return 0
