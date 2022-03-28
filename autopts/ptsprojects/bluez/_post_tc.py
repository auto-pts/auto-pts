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

import sys
import subprocess


def remove_paired_devices():

    proc = subprocess.Popen(['bluetoothctl', 'paired-devices'],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()

    if not stdout:
        print("No device paired")
        return

    print("stdout: %s" % stdout)
    print("stderr: %s" % stderr)

    dev_list = stdout.splitlines()
    for dev in dev_list:
        info = dev.split()
        print("info: %s" % info)
        print("info[1]: %s" % info[1])

        subprocess.Popen(['bluetoothctl', 'remove', info[1]],
                         shell=False,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)


def power_reset():

    print("Power off")
    proc = subprocess.Popen(['bluetoothctl', 'power', 'off'],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.communicate()

    print("Power on")
    proc = subprocess.Popen(['bluetoothctl', 'power', 'on'],
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.communicate()


def main():

    remove_paired_devices()
    power_reset()

    while True:
        line = sys.stdin.readline()

        if line == "#close\n":

            break


if __name__ == "__main__":
    main()
