#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
# Copyright (c) 2021, Nordic Semiconductor ASA.
# Copyright (c) 2025, Atmosic.
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

import glob
import importlib
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import serial

from autopts import bot
from autopts import client as autoptsclient
from autopts.bot.common import BotClient, BotConfigArgs, BuildAndFlashException, check_call
from autopts.ptsprojects.boards import get_board_type, get_build_and_flash, tty_to_com
from autopts.ptsprojects.zephyr import ZEPHYR_PROJECT_URL
from autopts.ptsprojects.zephyr.iutctl import get_iut, log

PROJECT_NAME = Path(__file__).stem


def build_image(zephyr_wd, cpu_type, conf_file=None, env_cmd=None):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param cpu_type: IUT
    :param conf_file: configuration file to be used
    :param env_cmd: a command to for environment activation, e.g. source /path/to/venv/activate
    """
    log(f"{build_image.__name__}: {zephyr_wd} {cpu_type} {conf_file} {env_cmd}")

    if env_cmd:
        env_cmd = env_cmd.split() + ['&&']
    else:
        env_cmd = []

    tester_dir = os.path.join(zephyr_wd, "tests/bluetooth/tester")

    shutil.rmtree(os.path.join(tester_dir, 'build'), ignore_errors=True)

    cmd = ['west', 'build', '-p', 'auto', '-b', cpu_type]
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        cmd.extend(('--', f'-DEXTRA_CONF_FILE=\'{conf_file}\''))

    check_call(env_cmd + cmd, cwd=tester_dir)


def flush_serial(tty, rtscts=False, baudrate=115200):
    """Clear the serial port buffer
    :param tty: file path of the terminal
    :return: None
    """
    if not tty:
        return

    if sys.platform == 'win32':
        com = tty_to_com(tty)
        ser = serial.Serial(com,
                            baudrate,
                            rtscts=rtscts,
                            timeout=5)
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


def zephyr_get_assertion_info(test_case_name):
    logs_dir = os.path.join(os.getcwd(), 'logs')
    pattern = test_case_name.replace('/', '_')
    search_pattern = os.path.join(logs_dir, '**', f'{pattern}_*', f'{pattern}_iut.log')
    log_files = glob.glob(search_pattern, recursive=True)

    for log_file in log_files:
        with open(log_file, encoding='utf-8') as f:
            for line in f:
                if 'ASSERTION' in line:
                    return line.strip()

    return None


class ZephyrBotConfigArgs(BotConfigArgs):
    def __init__(self, args):
        super().__init__(args)


class ZephyrBotCliParser(bot.common.BotCliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ZephyrBotClient(BotClient):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.zephyr')
        super().__init__(get_iut, project, 'zephyr', ZephyrBotConfigArgs,
                         ZephyrBotCliParser)
        self.config_default = "prj.conf"
        self.fail_info_parser = zephyr_get_assertion_info

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

        if args.iut_mode != 'tty':
            iut = self.get_iut()
            if not iut.kernel_image:
                iut.kernel_image = os.path.join(args.project_path, "tests/bluetooth/tester/build/zephyr/zephyr")
                if args.iut_mode == 'qemu':
                    iut.kernel_image += '.elf'
                else:
                    iut.kernel_image += '.exe'

        if args.no_build:
            if args.setcap_cmd:
                check_call(args.setcap_cmd.split())

            return

        if args.iut_mode == 'tty':
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)

            try:
                build_and_flash(args.project_path, board_type, args.debugger_snr,
                                overlays, args.project_repos, args.build_env_cmd)

                flush_serial(args.tty_file, rtscts=args.rtscts, baudrate=args.tty_baudrate)
            except BaseException as e:
                traceback.print_exception(e)
                self.error_txt_content += "Build and flash step failed\n"
                raise BuildAndFlashException from e

            time.sleep(10)
        else:
            build_image(args.project_path, args.kernel_cpu, overlays, args.build_env_cmd)
            if args.setcap_cmd:
                check_call(args.setcap_cmd.split())

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
