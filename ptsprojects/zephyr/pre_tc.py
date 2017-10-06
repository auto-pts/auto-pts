#!/usr/bin/env python3

import os
import sys
import atexit
import subprocess
import signal

PROFILE = None
TEST_CASE = None

BTMON_PROC = None
BTMON_LOG = None
# XXX: Fill me - btmon path example: /home/user/bluez/monitor/btmon
BTMON_PATH = None

# XXX: Fill me - logs dir example: /home/user/btmon_logs/
LOGS_DIR = None

def cleanup():
    if BTMON_PROC != None:
        BTMON_PROC.terminate()

        BTMON_PROC.wait()

def run_btmon():
    global BTMON_PROC, TEST_CASE

    TEST_CASE = TEST_CASE.replace("/", "-")

    BTMON_PROC = subprocess.Popen([BTMON_PATH, "-w", LOGS_DIR + PROFILE + "/" +
                                  TEST_CASE], shell=False,
                                  stdout=subprocess.DEVNULL)

def main():
    global PROFILE, TEST_CASE

    atexit.register(cleanup)

    PROFILE = sys.argv[1]
    TEST_CASE = sys.argv[2]

    if os.path.exists(LOGS_DIR + PROFILE) == False:
        os.makedirs(LOGS_DIR + PROFILE)

    run_btmon()

    while True:
        line = sys.stdin.readline()

        if line == "#close\n":
            BTMON_PROC.terminate()
            BTMON_PROC.wait()

            break

if __name__ == "__main__":
    main()
