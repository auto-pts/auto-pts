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

import atexit
import os
import subprocess
import sys
import threading
import time

PROFILE = None
TEST_CASE = None

RTT2PTY_PROC = None
RTT2PTY_CONSOLE_PROC = None
RTT2PTY_PATH = "rtt2pty"

CAT_PROC = None

BTMON_PROC = None
# XXX: Fill me - btmon path example: /home/user/bluez/monitor/btmon
BTMON_PATH = 'btmon'

# XXX: Fill me - logs dir example: /home/user/btmon_logs/
LOGS_DIR = 'iut_logs/'


def popen_and_call(cmd, **popen_args):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    onExit when the subprocess completes.
    onExit is a callable object, and popenArgs is a list/tuple of args that
    would give to subprocess.Popen.
    """

    def print_output(out, err):
        for line in iter(out.readline, b''):
            print(line.strip())

        for line in iter(err.readline, b''):
            print(line.strip())

    def run_in_thread(proc):
        proc.wait()
        rc = proc.returncode
        return rc

    proc = subprocess.Popen(cmd, **popen_args)

    t = threading.Thread(target=print_output, args=(proc.stdout, proc.stderr))
    t.start()

    thread = threading.Thread(target=run_in_thread, args=(proc,))
    thread.start()

    return proc


def cleanup(proc):
    if proc is not None and proc.poll() is None:
        proc.terminate()
        proc.wait()


def cleanup_all():
    cleanup(BTMON_PROC)
    cleanup(RTT2PTY_PROC)
    cleanup(CAT_PROC)
    cleanup(RTT2PTY_CONSOLE_PROC)


def run_btmon():
    global BTMON_PROC, TEST_CASE

    TEST_CASE = TEST_CASE.replace("/", "-")
    log_file = LOGS_DIR + PROFILE + "/" + TEST_CASE + "_btmon.log"

    cmd = [BTMON_PATH, "-J", "NRF52", "-w", log_file]
    print("Executing command: {}".format(' '.join(cmd)))

    BTMON_PROC = popen_and_call(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=False)


def run_rtt2pty():
    global RTT2PTY_PROC

    subprocess.check_call('rm -rf ./auto-pts-tester', shell=True)

    cmd = [RTT2PTY_PATH, "-2", "-b", "bttester", "-l", "auto-pts-tester"]
    print("Executing command: {}".format(' '.join(cmd)))

    RTT2PTY_PROC = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=False)

    # RTT2PTY_PROC = popen_and_call(
    #     cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)


def run_rtt2pty_console():
    global RTT2PTY_CONSOLE_PROC

    subprocess.check_call('rm -rf ./iut_console', shell=True)

    cmd = [RTT2PTY_PATH, "-2", "-l", "iut_console"]
    print("Executing command: {}".format(' '.join(cmd)))

    RTT2PTY_CONSOLE_PROC = popen_and_call(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

    time.sleep(3)

    run_cat()


def run_cat():
    global CAT_PROC

    log_file = LOGS_DIR + PROFILE + "/" + TEST_CASE + "_iut.log"

    cmd = 'cat {} | tee {}'.format('./iut_console', log_file)
    print("Executing command: {}".format(cmd))

    CAT_PROC = popen_and_call(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)


def main():
    global PROFILE, TEST_CASE

    atexit.register(cleanup_all)

    PROFILE = sys.argv[1]
    TEST_CASE = sys.argv[2]

    if not os.path.exists(LOGS_DIR + PROFILE):
        os.makedirs(LOGS_DIR + PROFILE)

    print("#DBG# " + TEST_CASE)

    # run_rtt2pty()
    # run_btmon()
    # run_rtt2pty_console()

    while True:
        line = sys.stdin.readline()

        if line == "#close\n":
            cleanup_all()
            break


if __name__ == "__main__":
    main()
