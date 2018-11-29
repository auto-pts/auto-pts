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

import logging
import subprocess

# make sure adb is in path or modify this variable
ADB = "adb"
USE_ADB = True

log = logging.debug


def exec_iut_cmd(iut_cmd, wait=False, use_adb_shell=USE_ADB):
    """Runs command in the IUT

    [1] Command is split to make this function platform independent, this is
    cause on Linux command must be a sequence or shell=True must be passed to
    Popen. On Windows in IronPython command can be a string.

    """
    if use_adb_shell:
        cmd = "%s shell %s" % (ADB, iut_cmd)
    else:
        cmd = iut_cmd

    log("starting child process %s", iut_cmd)

    process = subprocess.Popen(cmd.split(),  # see [1]
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

    process_desc = "%s pid %s" % (repr(cmd), process.pid)

    log("started child process %s", process_desc)

    # TODO: communicate waits, this means output of not waited commands is not
    # logged, using logging.root.handlers[0].stream as stdout and stderr when
    # creating process causes exceptions "IOError: System.IO.IOException: The
    # OS handle's position is not what FileStream expected.". So find a trivial
    # way to log the output of non-blocking (wait is False) processes
    if wait:
        output = process.communicate()[0]
        if output:
            log("child process %s output:\n%s", process_desc, output)

    return process


def exec_adb_root():
    """Runs 'adb root' in Android IUT.

    This is needed cause IUT commands require root permissions

    """
    if not USE_ADB:
        return

    """Runs "adb root" command"""
    exec_iut_cmd("adb root", True, False)
    # it takes an instance of time to get adbd restarted with root permissions
    exec_iut_cmd("adb wait-for-device", True, False)
