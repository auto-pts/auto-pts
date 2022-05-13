#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2021, Nordic Semiconductor ASA.
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
import os
import subprocess
import sys

from autopts.bot.common import check_call

supported_projects = ['zephyr']


board_type = 'nrf52840dk_nrf52840'


def reset_cmd(iutctl):
    """Return reset command for nRF5x DUT

    Dependency: nRF5x command line tools
    """

    return f'nrfjprog -r -s {iutctl.debugger_snr}'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)
    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        cmd.extend(('--', '-DOVERLAY_CONFIG={}'.format(conf_file)))

    shell = True
    if sys.platform == 'win32':
        shell = False
        cmd = subprocess.list2cmdline(cmd)
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl

    check_call(cmd, cwd=tester_dir, shell=shell)
    check_call(['west', 'flash', '--skip-rebuild', '--recover',
                '--snr', debugger_snr], cwd=tester_dir)
