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
import subprocess
import shlex


def run_checks(py_files):
    ignore_dict = {
        "ptsprojects/ptstypes.py": "E501,E221,E203,E221",
        "ptscontrol.py": "E402",
        "ptsprojects/zephyr/iutctl.py": "E501",
        "test/test-mmi-parser.py": "E122,E501,E402",
        "tools/btpclient.py": "E402",
        "tools/create-workspace.py": "E402"
    }

    total_files = len(py_files)
    total_files_width = len(str(total_files))
    print("Will run check for %d files" % total_files)

    for count, fl in enumerate(py_files):
        cmd = "pycodestyle"
        if fl in ignore_dict:
            cmd += " --ignore " + ignore_dict[fl]
        cmd += " " + fl

        print("{:>{}}/{} Running check {}".format(
            count + 1, total_files_width, total_files, cmd))

        try:
            subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            print("\nCheck failed:\n", exc.output.decode("utf-8"))
            sys.exit(1)


def main():
    top_level = subprocess.check_output(
        "git rev-parse --show-toplevel", shell=True).strip()
    os.chdir(top_level)
    files = subprocess.check_output("git ls-files", shell=True).decode("utf-8")
    py_files = [fl for fl in files.splitlines() if fl.endswith(".py")]

    run_checks(py_files)


if __name__ == "__main__":
    main()
