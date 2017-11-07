#!/usr/bin/env python

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
