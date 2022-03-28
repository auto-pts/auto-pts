#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
import atexit

PROFILE = None
TEST_CASE = None

# XXX: Fill me - logs dir example: /home/user/btmon_logs/
LOGS_DIR = 'iut_logs/'


def cleanup():
    pass


def main():
    return  # Remove this if any subprocess is implemented
    global PROFILE, TEST_CASE

    atexit.register(cleanup)

    PROFILE = sys.argv[1]
    TEST_CASE = sys.argv[2]

    if not os.path.exists(LOGS_DIR + PROFILE):
        os.makedirs(LOGS_DIR + PROFILE)

    # Start some subprocess here

    while True:
        line = sys.stdin.readline()

        if line == "#close\n":
            # Terminate subprocess here
            break


if __name__ == "__main__":
    main()
