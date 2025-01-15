#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Nordic Semiconductor ASA.
# Copyright (c) 2024, Codecoup.
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

from subprocess import CalledProcessError
from autopts.bot.common import check_call

supported_projects = ['zephyr']

board_type = 'nrf54h20dk/nrf54h20/cpuapp'


def reset_cmd(iutctl):
    """Return reset command for nRF54H DUT

    Dependency: nRF54H command line tools
    """
    return f'nrfutil device reset --reset-kind RESET_PIN --serial-number {iutctl.debugger_snr}'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)
    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    cmd = ['west', 'build', '--sysbuild', '-p', 'auto', '-b', board]
    if conf_file and conf_file not in ['default', 'prj.conf']:
        if 'audio' in conf_file:
            conf_file += ';overlay-le-audio-ctlr.conf'
        cmd.extend(('--', f'-DEXTRA_CONF_FILE=\'{conf_file}\''))

    check_call(cmd, cwd=tester_dir)
    try:
        check_call(['west', 'flash', '--skip-rebuild',
                    '-i', debugger_snr], cwd=tester_dir)
    except CalledProcessError:
        check_call(['west', 'flash', '--skip-rebuild', '--recover',
                    '-i', debugger_snr], cwd=tester_dir)
