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
import subprocess
import sys
from pathlib import PurePosixPath

from autopts.bot.common import check_call

supported_projects = ['zephyr']


board_type = 'nrf52840dk/nrf52840'


def reset_cmd(iutctl):
    """Return reset command for nRF5x DUT

    Dependency: nRF5x command line tools
    """

    return f'nrfjprog -r -s {iutctl.debugger_snr}'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, env_cmd=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    :param env_cmd: a command to for environment activation, e.g. source /path/to/venv/activate
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)

    if env_cmd:
        env_cmd = env_cmd.split() + ['&&']
    else:
        env_cmd = []

    tester_dir = PurePosixPath(zephyr_wd, 'tests', 'bluetooth', 'tester').as_posix()

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    if conf_file and conf_file not in ["default", "prj.conf"]:
        cmd.extend(('--', f'-DEXTRA_CONF_FILE=\'{conf_file}\''))

    check_call(env_cmd + cmd, cwd=tester_dir)

    shell = True
    if sys.platform == 'win32':
        shell = False
        cmd = ['west', 'flash', '--skip-rebuild', '--recover', '--snr',
               debugger_snr]
        cmd = subprocess.list2cmdline(cmd)
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl

    check_call(env_cmd + cmd, cwd=tester_dir, shell=shell)
