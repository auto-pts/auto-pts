#!/usr/bin/env python

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

import importlib
import sys
from pathlib import Path

from autopts import bot
from autopts import client as autoptsclient
from autopts.bot.common import BotClient, BotConfigArgs
from autopts.ptsprojects.zephyr.iutctl import get_iut

PROJECT_NAME = Path(__file__).stem


class ExternalBotConfigArgs(BotConfigArgs):
    def __init__(self, args):
        super().__init__(args)


class ExternalBotCliParser(bot.common.BotCliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ExternalBotClient(BotClient):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.zephyr')
        super().__init__(get_iut, project, 'zephyr', ExternalBotConfigArgs,
                         ExternalBotCliParser)
        self.config_default = "prj.conf"

    def apply_config(self, args, config, value):
        # apply overlays, build and flash
        pass

    def start(self, args=None):
        main(self)


class ExternalClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'zephyr', True)


BotClient = ExternalBotClient


def main(bot_client):
    bot.common.cleanup()
    cfg = bot_client.bot_config
    args = cfg['auto_pts']

    # Do something before testing

    try:
        summary, results, descriptions, regressions, progresses, \
            args['pts_ver'], args['platform'] = bot_client.run_tests()
    finally:
        pass

    # Do something after testing, e.g. send logs.

    bot.common.cleanup()

    print("\nDone, bye!")
    sys.stdout.flush()

    return 0
