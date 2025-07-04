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

from autopts.bot.common import check_call

supported_projects = ['zephyr']


def reset_cmd(iutctl):
    """Return reset command for nRF5x DUT

    Dependency: nRF5x command line tools
    """

    return f'nrfjprog -r -s {iutctl.debugger_snr}'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, project_repos=None,
                    env_cmd=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    :param project_repos: a list of repo paths
    :param env_cmd: a command to for environment activation, e.g. source /path/to/venv/activate
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)

    if env_cmd:
        env_cmd = env_cmd.split() + ['&&']
    else:
        env_cmd = []

    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    bttester_overlay = 'overlay-bt_ll_sw_split.conf'
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        bttester_overlay += f';{conf_file}'

    cmd = ['west', 'build', '-p', 'auto', '-b', board, '--', f'-DEXTRA_CONF_FILE=\'{bttester_overlay}\'']

    check_call(env_cmd + cmd, cwd=tester_dir)
    check_call(env_cmd + ['west', 'flash', '--skip-rebuild', '--recover', '-i', debugger_snr], cwd=tester_dir)
