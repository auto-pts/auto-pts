#!/usr/bin/env python
#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
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
import copy
import logging
import signal
import sys
import threading
import time

import schedule

from autopts.bot.common import get_absolute_module_path, load_module_from_path
from autopts.utils import have_admin_rights, log_running_threads, set_global_end

log = logging.debug


def add_to_scheduler(bot_client):
    scheduler_config = bot_client.bot_config.get('scheduler', [])
    scheduled = False

    for day in scheduler_config:
        hour = scheduler_config[day]
        getattr(schedule.every(), day).at(hour).do(bot_client.start)
        scheduled = True

    return scheduled


def run_scheduler():
    while schedule.get_jobs():
        schedule.run_pending()
        time.sleep(60)


def parse_config_path():
    config_path = None
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        config_path = sys.argv[1]
    return config_path


def import_bot_projects():
    config_path = parse_config_path()
    if not config_path:
        config_path = 'config'

    # Path to the config file can be specified as 'config',
    # 'config.py' or 'path/to/config.py'.
    config_path = get_absolute_module_path(config_path)
    if not config_path:
        return None, config_path

    module = load_module_from_path(config_path)
    return copy.deepcopy(getattr(module, "BotProjects", None)), config_path


def import_bot_module(project):
    # Path to the external bot module
    module_name = project.get('bot_module', None)

    if module_name is None:
        # Use a default bot module from AutoPTS repo
        module_name = project.get('name')

    # Path to the bot module can be specified as 'module',
    # 'module.py' or 'path/to/module.py'.
    module_path = get_absolute_module_path(module_name)
    if not module_path:
        return None, module_path

    return load_module_from_path(module_path)


def get_client(module, project):
    bot_client_class = getattr(module, 'BotClient', None)

    if bot_client_class:
        bot_client = bot_client_class()
        errmsg = bot_client.parse_config_and_args(project)
        if errmsg:
            print(errmsg)
            return None

        if bot_client.args.simple_mode:
            bot_client.start = super(bot_client.__class__, bot_client).start
    else:
        print(f'BotClient not implemented for project {project["name"]}'
              f"Please check the 'bot_module' variable from config.py for any errors.")
        return None

    return bot_client


def print_bad_config_message():
    text = 'Could not load any BotProjects. '
    config_path = parse_config_path()

    if not config_path:
        text += 'Please provide a path/to/bot_config.py file.'
    else:
        text += f'Is the {config_path} a valid config file?'

    print(text)


def main():
    logging.basicConfig(level=logging.DEBUG)

    bot_projects, _ = import_bot_projects()
    if not bot_projects:
        print_bad_config_message()
        return 1

    bot_clients = []
    for project in bot_projects:
        bot_module = import_bot_module(project)

        bot_client = get_client(bot_module, project)

        if bot_client is None:
            return 1

        if add_to_scheduler(bot_client):
            continue

        bot_clients.append(bot_client)

    for bot_client in bot_clients:
        bot_client.start()

    run_scheduler()

    return 0


if __name__ == "__main__":
    def sigint_handler(sig, frame):
        """Thread safe SIGINT interrupting"""
        set_global_end()

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
    finally:
        set_global_end()
        log_running_threads()
        sys.exit(rc)
