#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

from .nrf5x import *
from autopts.bot.common import check_call

board_type = 'nrf5340dk_nrf5340_cpuapp'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, repos=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    :param repos: project repos
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)

    tester_dir = os.path.join(zephyr_wd, 'tests', 'bluetooth', 'tester')

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    autopts_overlay = 'autopts_audio_overlay.conf'
    check_call(['printf', r'CONFIG_BT_ATT_ENFORCE_FLOW=n\nCONFIG_BT_HCI_VS_EXT=n', '>', autopts_overlay], cwd=tester_dir)

    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        autopts_overlay += f';{conf_file}'

    cmd = ['west', 'build', '-p', 'auto', '-b', board, '--', f'-DOVERLAY_CONFIG={autopts_overlay}']
    check_call(cmd, cwd=tester_dir)
    check_call(['west', 'flash', '--skip-rebuild', '--recover', '-i', debugger_snr], cwd=tester_dir)

    sdk_nrf_repo = os.path.join(repos['sdk-nrf']['path'], 'applications', 'nrf5340_audio', 'bin')

    # Find the hex file, because *.hex does not work in Windows shell
    for file in os.listdir(sdk_nrf_repo):
        if file.endswith(".hex"):
            hex_file = file
            break

    # Flashing LE Audio Controller Subsystem for nRF53 on the network core
    cmd = ['nrfjprog', '--program', hex_file, '--chiperase', '--coprocessor', 'CP_NETWORK', '-r']
    check_call(cmd, cwd=sdk_nrf_repo)
