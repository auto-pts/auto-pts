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
import logging
import os
import signal
import sys
import threading
import time
import _locale
import schedule
import importlib
from argparse import ArgumentParser, RawTextHelpFormatter, SUPPRESS

from autopts.client import set_end
from autopts.bot.config import BotProjects
from autopts.bot.zephyr import main as zephyr
from autopts.bot.mynewt import main as mynewt
from autopts.winutils import have_admin_rights

# TODO Find more sophisticated way
weekdays2schedule = {
    'monday': schedule.every().monday,
    'tuesday': schedule.every().tuesday,
    'wednesday': schedule.every().wednesday,
    'thursday': schedule.every().thursday,
    'friday': schedule.every().friday,
    'saturday': schedule.every().saturday,
    'sunday': schedule.every().sunday,
}

project2main = {
    'zephyr': zephyr,
    'mynewt': mynewt,
}


class CliParser(ArgumentParser):
    def __init__(self, parents):
        super().__init__(formatter_class=RawTextHelpFormatter,
                         usage=sys.argv[0] + ' [project|myconfig] [-h] [<other project specific options>]',
                         parents=parents,
                         description='''AutoPTS Bot Client v0.x

optional positional arguments:
  {mynewt,zephyr,myconfig}
                        Select project to run as a simple client or
                        give the name of custom configuration file.
    mynewt              Run as autoptsclient-mynewt.py
    zephyr              Run as autoptsclient-zephyr.py
    myconfig            Name of custom autopts/bot/myconfig.py file. ''', epilog='''
Example usage:
Run bot with the default autopts/bot/config.py:
$ python autoptsclient_bot.py

Run bot with a custom config py file. myconfig is an example name,
but the file must be in autopts/bot/.:
$ python autoptsclient_bot.py myconfig

Run bot as a simple client, e.g. for 'zephyr' project:
$ python autoptsclient_bot.py zephyr zephyr-master -t /dev/ttyACM0 -l 192.168.3.1 -i 192.168.3.2 -b nrf52 -c GAP

Run bot with overwritten options of config.py:
$ python autoptsclient_bot.py -c GAP/CONN --rtt-log

Print help for 'zephyr' project:
$ python autoptsclient_bot.py zephyr -h''')
        # Just ignore the other project-specific positional arguments
        self.add_argument('other', nargs='*', default=None, help=SUPPRESS)


def main():
    # Workaround for logging error: "UnicodeEncodeError: 'charmap' codec can't
    # encode character '\xe6' in position 138: character maps to <undefined>",
    # which occurs under Windows with default encoding other than cp1252
    # each time log() is called.
    _locale._getdefaultlocale = (lambda *arg: ['en_US', 'utf8'])

    bot_projects = []
    parents = []
    mod = None

    if len(sys.argv) > 1 and os.path.isfile('autopts/bot/' + sys.argv[1] + '.py'):
        conf = sys.argv.pop(1)
        mod = importlib.import_module('autopts.bot.' + conf)

        if conf in project2main.keys():
            parents.append(mod.BotCliParser(add_help=False))
        else:
            bot_projects += mod.BotProjects
    else:
        bot_projects = BotProjects

    arg_parser = CliParser(parents)
    arg_parser.parse_known_args()

    if len(bot_projects) == 0 and mod is not None:
        mod.SimpleClient().start()

    for project in bot_projects:
        # TODO Solve the issue of overlapping jobs
        if 'scheduler' in project:
            for day, time_ in list(project['scheduler'].items()):
                weekdays2schedule[day].at(time_).do(
                    project2main[project['name']], project)

            while True:
                schedule.run_pending()
                time.sleep(60)
        else:
            project2main[project['name']](project)

    return 0


if __name__ == "__main__":
    def sigint_handler(sig, frame):
        """Thread safe SIGINT interrupting"""
        set_end()

        if sys.platform != "win32":
            signal.signal(signal.SIGINT, prev_sigint_handler)
            threading.Thread(target=signal.raise_signal(signal.SIGINT)).start()

    rc = 1

    if have_admin_rights():  # root privileges are not needed
        print("Please do not run this program as root.")
        sys.exit(1)

    try:
        prev_sigint_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, sigint_handler)

        rc = main()
    except KeyboardInterrupt:  # Ctrl-C
        rc = 14
    except SystemExit:
        raise
    except BaseException as e:
        logging.exception(e)
        import traceback

        traceback.print_exc()
        rc = 16

    set_end()
    sys.exit(rc)
