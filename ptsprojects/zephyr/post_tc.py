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
import subprocess
import signal

CONFIG_PROC = None
# XXX: Fill me - nrfjprog path example: /home/user/tool/nrfjprog
CONFIG_PATH = None


def cleanup():
    pass


def reset_controler():
    global CONFIG_PROC

    CONFIG_PROC = subprocess.Popen([CONFIG_PATH, "-r"], shell=False)

    (stdoutdata, stderrdata) = CONFIG_PROC.communicate()

    print(stdoutdata, stderrdata)


def main():
    atexit.register(cleanup)

    reset_controler()

    while True:
        line = sys.stdin.readline()

        if line == "#close\n":
            CONFIG_PROC.terminate()
            CONFIG_PROC.wait()

            break


if __name__ == "__main__":
    main()
