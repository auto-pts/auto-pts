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

import os
import sys
import schedule
import time

from bot.config import BotProjects
from bot.zephyr import main as zephyr

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
}


def main():
    for project in BotProjects:
        # TODO Solve the issue of overlapping jobs
        if 'scheduler' in project:
            for day, time_ in project['scheduler'].items():
                weekdays2schedule[day].at(time_).do(
                    project2main[project['name']], project)

            while True:
                schedule.run_pending()
                time.sleep(60)
        else:
            project2main[project['name']](project)


if __name__ == "__main__":
    if os.geteuid() == 0:  # root privileges are not needed
        print("Please do not run this program as root.")
        sys.exit(1)

    try:
        main()
        os._exit(0)
    except KeyboardInterrupt:  # Ctrl-C
        os._exit(14)
    except SystemExit:
        raise
    except:
        import traceback

        traceback.print_exc()
        os._exit(16)
