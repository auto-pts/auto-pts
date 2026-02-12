#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2023, NXP.
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
from autopts.ptsprojects.boards import Jlink

log = logging.debug

supported_projects = ['zephyr']
board_type = 'frdm_mcxw71'


def reset_cmd(iutctl):
    return Jlink(iutctl.debugger_snr, iutctl.device_core).reset_command


def build_and_flash(zephyr_wd, tester_app_dir, board, debugger_snr, conf_file=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param tester_app_dir: path to tester application relative to zephyr_wd
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)
    tester_dir = os.path.join(zephyr_wd, tester_app_dir)

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    if conf_file and conf_file not in ["default", "prj.conf"]:
        cmd.extend(('--', f'-DOVERLAY_CONFIG=\'{conf_file}\''))
    logging.info(f'cmd:{cmd}, tester_dir:{tester_dir}')
    check_call(cmd, cwd=tester_dir)
    check_call(['west', 'flash', '--skip-rebuild',
                '-i', debugger_snr], cwd=tester_dir)
