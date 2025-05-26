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

import importlib
import os
import sys
import time
import traceback
from pathlib import Path

import serial

from autopts import bot
from autopts import client as autoptsclient
from autopts.bot.common import BotClient, BotConfigArgs, BuildAndFlashException
from autopts.bot.common_features import report
from autopts.ptsprojects.boards import get_board_type, get_build_and_flash, tty_to_com
from autopts.ptsprojects.zephyr import ZEPHYR_PROJECT_URL
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
    tester_app_dir = os.getenv("AUTOPTS_SOURCE_DIR_APP")
    if tester_app_dir is None:
        tester_app_dir = os.path.join("tests", "bluetooth", "tester")
    cwd = os.getcwd()

    os.chdir(os.path.join(zephyr_wd, tester_app_dir))

    with open(cfg_name, 'w') as config:
        for k, v in list(overlay.items()):
            config.write(f"{k}={v}\n")

    os.chdir(cwd)


def zephyr_hash_url(commit):
    """ Create URL for commit in Zephyr
    :param commit: Commit ID to append
    :return: URL of commit
    """
    return f"{ZEPHYR_PROJECT_URL}/commit/{commit}"


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
        if isinstance(pre_overlay, str):
            pre_overlay = [pre_overlay]

        post_overlay = value.get('post_overlay', [])
        if isinstance(post_overlay, str):
            post_overlay = [post_overlay]

        configs = []
        for name in pre_overlay + [config] + post_overlay:
            if name in self.iut_config and 'overlay' in self.iut_config[name] \
                    and len(self.iut_config[name]['overlay']) and name != 'prj.conf':
                apply_overlay(args.project_path, name,
                              self.iut_config[name]['overlay'])
            elif not os.path.exists(os.path.join(args.project_path, "tests", "bluetooth", "tester", name)):
                log(f'Overlay {name} is not a file.')
                continue

            configs.append(name)

        # The order is used in the -DEXTRA_CONF_FILE="<overlay1>;<...>" option.
        overlays = ';'.join(configs)

        log(f"TTY path: {args.tty_file}")

        if not args.no_build:
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)

            try:
                build_and_flash(args.project_path, board_type, args.debugger_snr,
                                overlays, args.project_repos)

                flush_serial(args.tty_file)
            except BaseException as e:
                traceback.print_exception(e)
                report.make_error_txt('Build and flash step failed', self.file_paths['ERROR_TXT_FILE'])
                raise BuildAndFlashException

            time.sleep(10)

    def start(self, args=None):
        super().start(args)

    def upload_logs_to_github(self, report_data):
        commit_msg_pattern = '{branch}_{start_time_stamp}_{commit_sha}'
        branch = 'no_branch'
        commit_sha = 'no_sha'

        if 'commit_msg' in self.bot_config['githubdrive'] and \
                self.bot_config['githubdrive']['commit_msg'] is not None:
            commit_msg_pattern = self.bot_config['githubdrive']['commit_msg']

        if 'git' in self.bot_config:
            commit_sha = report_data['repos_info']['zephyr']['commit']
            branch = self.bot_config['git']['zephyr']['branch']

        report_data['commit_msg'] = commit_msg_pattern.format(
            branch=branch, commit_sha=commit_sha, **report_data)

        super().upload_logs_to_github(report_data)

    def compose_mail(self, mail_ctx):
        if 'subject' not in mail_ctx:
            mail_ctx['subject'] = "[Zephyr] AutoPTS test session results"

        return super().compose_mail(mail_ctx)


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, sys.modules['autopts.ptsprojects.zephyr'], 'zephyr')


BotClient = ZephyrBotClient
