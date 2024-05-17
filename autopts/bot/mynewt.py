#!/usr/bin/env python
#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
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
import subprocess
import sys
import time
from pathlib import Path

from autopts import bot
from autopts.bot.common import BuildAndFlashException
from autopts.bot.common_features.github import update_sources
from autopts.client import Client
from autopts.ptsprojects.boards import release_device, get_build_and_flash, get_board_type
from autopts.ptsprojects.mynewt.iutctl import get_iut, log
from autopts.ptsprojects.testcase_db import DATABASE_FILE
from autopts.bot.common_features import github, report, mail, google_drive


PROJECT_NAME = Path(__file__).stem


def check_call(cmd, env=None, cwd=None, shell=True):
    if sys.platform == 'win32':
        cmd = subprocess.list2cmdline(cmd)
        cmd = [os.path.expandvars('$MSYS2_BASH_PATH'), '-c', cmd]
    return bot.common.check_call(cmd, env, cwd, shell)


def check_output(cmd, cwd=None, shell=True, env=None):
    if sys.platform == 'win32':
        cmd = [os.path.expandvars('$MSYS2_BASH_PATH'), '-c', cmd]
    return subprocess.check_output(cmd, cwd=cwd, shell=shell, env=env)


def get_target_description(project_path):
    return check_output('newt target show bttester', shell=True, cwd=project_path)


def get_target_config(project_path):
    return check_output('newt target config flat bttester', shell=True, cwd=project_path)


def get_newt_info(project_path):
    return check_output('newt info', shell=True, cwd=project_path)


def get_newt_version(project_path):
    return check_output('newt version', shell=True, cwd=project_path)


def get_build_info_file(project_path):
    file_name = "build_info.txt"
    build_info_str = ''

    build_info_str += 'newt info:\n'
    build_info_str += get_newt_info(project_path).decode()
    build_info_str += '\n'

    build_info_str += 'newt version:\n'
    build_info_str += get_newt_version(project_path).decode()
    build_info_str += '\n'

    build_info_str += 'newt target show:\n'
    build_info_str += get_target_description(project_path).decode()
    build_info_str += '\n'

    build_info_str += 'newt target config:\n'
    build_info_str += get_target_config(project_path).decode()
    build_info_str += '\n'

    with open(file_name, "w") as text_file:
        text_file.write(build_info_str)

    return file_name


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

    body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session</h1>
    {}
    <h2>1. IUT Setup</h2>
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
    <h3>Logs</h3>
    {}
    <p>Sincerely,</p>
    <p> {}</p>
    '''.format(additional_info, args["board"], mail_ctx["mynewt_repo_status"], args['platform'],
               args['pts_ver'], mail_ctx["elapsed_time"], mail_ctx["summary"],
               mail_ctx["regression"], mail_ctx["log_url"], mail_cfg['name'])

    if 'subject' in mail_cfg:
        subject = mail_cfg['subject']
    else:
        subject = "[Mynewt Nimble] AutoPTS test session results"

    return subject, body


class MynewtBotConfigArgs(bot.common.BotConfigArgs):
    def __init__(self, args):
        super().__init__(args)
        self.board_name = args['board']
        self.tty_file = args.get('tty_file', None)


class MynewtBotCliParser(bot.common.BotCliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MynewtBotClient(bot.common.BotClient):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.mynewt')
        super().__init__(get_iut, project, 'mynewt', MynewtBotConfigArgs,
                         MynewtBotCliParser)

    def apply_config(self, args, config, value):
        overlay = {}

        if 'overlay' in value:
            overlay = value['overlay']

        if args.rtt_log:
            overlay['CONSOLE_RTT'] = '1'
            overlay['BTTESTER_BTP_LOG'] = '1'
            overlay['CONSOLE_UART_FLOW_CONTROL'] = 'UART_FLOW_CTL_RTS_CTS'

        log("TTY path: %s" % args.tty_file)

        if not args.no_build:
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)

            try:
                build_and_flash(args.project_path, board_type, overlay, args.debugger_snr)
            except:
                report.make_error_txt('Build and flash step failed')
                raise BuildAndFlashException

            time.sleep(10)

    def start(self, args=None):
        main(self)


class MynewtClient(Client):
    def __init__(self):
        super().__init__(get_iut, sys.modules['autopts.ptsprojects.zephyr'], 'mynewt')


BotClient = MynewtBotClient


def main(bot_client):
    print("Mynewt bot start!")

    if sys.platform == 'win32':
        if 'MSYS2_BASH_PATH' not in os.environ:
            print('Set environmental variable MSYS2_BASH_PATH.')
            return 0
        # In case wsl was configured and its bash has higher prio than msys2 bash
        os.environ['PATH'] = '/usr/bin:' + os.environ['PATH']

    bot.common.pre_cleanup()

    start_time = time.time()

    cfg = bot_client.bot_config
    args = cfg['auto_pts']

    if 'database_file' not in args:
        args['database_file'] = DATABASE_FILE

    if 'githubdrive' in cfg:
        update_sources(cfg['githubdrive']['path'],
                       cfg['githubdrive']['remote'],
                       cfg['githubdrive']['branch'], True)

    if args.get('newt_upgrade', False):
        bot.common.check_call(['newt', 'upgrade', '-f', '--shallow=0'], cwd=args['project_path'])

    if 'git' in cfg:
        repos_info = github.update_repos(args['project_path'], cfg["git"])
        repo_status = report.make_repo_status(repos_info)
    else:
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
    args['pts_ver'] = stats.pts_ver
    args['platform'] = stats.platform

    results = collections.OrderedDict(sorted(results.items()))

    pts_logs, xmls = report.pull_server_logs(bot_client.args)

    report_file = report.make_report_xlsx(results, summary, regressions,
                                          progresses, descriptions, xmls, PROJECT_NAME)
    report_txt = report.make_report_txt(results, regressions,
                                        progresses, repo_status, PROJECT_NAME)
    logs_folder = report.archive_testcases("logs")

    build_info_file = get_build_info_file(os.path.abspath(args['project_path']))

    end_time = time.time()
    url = None

    if 'gdrive' in cfg:
        drive = google_drive.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload(report_file)
        drive.upload(report_txt)
        drive.upload_folder(logs_folder)
        drive.upload(build_info_file)
        drive.upload(args['database_file'])
        drive.upload_folder(pts_logs)

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {"summary": mail.status_dict2summary_html(summary),
                    "regression": mail.regressions2html(regressions,
                                                        descriptions),
                    "mynewt_repo_status": repo_status}

        # Summary

        # Regression and test case description

        # Log in Google drive in HTML format
        if 'gdrive' in cfg and url:
            mail_ctx["log_url"] = mail.url2html(url,
                                                "Results on Google Drive")
        else:
            mail_ctx["log_url"] = "Not Available"

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
