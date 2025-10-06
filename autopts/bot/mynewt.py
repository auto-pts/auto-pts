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
import importlib
import os
import sys
import traceback
from pathlib import Path

from autopts import bot
from autopts.bot.common import BuildAndFlashException
from autopts.client import Client
from autopts.ptsprojects.boards import get_board_type, get_build_and_flash
from autopts.ptsprojects.mynewt.iutctl import get_iut, log

PROJECT_NAME = Path(__file__).stem


def check_call(cmd, env=None, cwd=None, shell=True):
    return bot.common.check_call(cmd, env, cwd, shell)


def check_output(cmd, cwd=None, shell=True, env=None):
    return bot.common.check_output(cmd, env, cwd, shell)


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

        log(f"TTY path: {args.tty_file}")

        if not args.no_build:
            build_and_flash = get_build_and_flash(args.board_name)
            board_type = get_board_type(args.board_name)

            try:
                build_and_flash(args.project_path, board_type, overlay, args.debugger_snr)
            except BaseException as e:
                traceback.print_exception(e)
                self.error_txt_content += "Build and flash step failed\n"
                raise BuildAndFlashException from e

    def start(self, args=None):
        print("Mynewt bot start!")

        if sys.platform == 'win32':
            if 'MSYS2_BASH_PATH' not in os.environ:
                print('Set environmental variable MSYS2_BASH_PATH.')
                return 0
            # In case wsl was configured and its bash has higher prio than msys2 bash
            os.environ['PATH'] = '/usr/bin:' + os.environ['PATH']

        if not os.path.exists(self.file_paths['BOT_STATE_JSON_FILE']):
            if self.bot_config.get('newt_upgrade', False):
                bot.common.check_call(['newt', 'upgrade', '-f', '--shallow=0'],
                                      cwd=self.bot_config['project_path'])

        super().start(args)

    def generate_attachments(self, report_data, attachments):
        project_path = os.path.abspath(self.bot_config['auto_pts']['project_path'])
        build_info_file = get_build_info_file(project_path)
        attachments.append(build_info_file)

    def compose_mail(self, mail_ctx):
        if 'subject' not in mail_ctx:
            mail_ctx['subject'] = "[Mynewt Nimble] AutoPTS test session results"

        return super().compose_mail(mail_ctx)


class MynewtClient(Client):
    def __init__(self):
        super().__init__(get_iut, sys.modules['autopts.ptsprojects.zephyr'], 'mynewt')


BotClient = MynewtBotClient
