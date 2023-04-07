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

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    # if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
    #     cmd.extend(('--', '-DOVERLAY_CONFIG={}'.format(conf_file)))

    # Hot Fix: The behavior of CONFIG_LOG_DEFAULT_LEVEL was changed,
    # which results in a stack overflow
    tmp_overlay = 'tmp_workaround_overlay.conf'
    check_call(f'echo CONFIG_LOG_DEFAULT_LEVEL=2 > {tmp_overlay}'.split(), cwd=tester_dir)
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        tmp_overlay += f';{conf_file}'

    # Hot Fix for LE Audio: some configs are missing in tester
    if conf_file and 'audio' in conf_file:
        config = """CONFIG_BT_CTLR_ADV_DATA_LEN_MAX=191
CONFIG_BT_KEYS_OVERWRITE_OLDEST=y
CONFIG_BT_CTLR_PERIPHERAL_ISO=y
CONFIG_BT_CTLR_CENTRAL_ISO=y
# Supports the highest SDU size required by any BAP LC3 presets (155)
CONFIG_BT_CTLR_ISO_TX_BUFFER_SIZE=155
# Supports the highest SDU size required by any BAP LC3 presets (155)
CONFIG_BT_CTLR_ISO_TX_BUFFER_SIZE=155
CONFIG_BT_ISO_TX_BUF_COUNT=4
CONFIG_BT_BAP_UNICAST_CLIENT_GROUP_STREAM_COUNT=4
"""

        nrf52_leaudio_hotfix_overlay = 'nrf52_leaudio_hotfix_overlay.conf'
        conf_file = open(os.path.join(tester_dir, nrf52_leaudio_hotfix_overlay), "w")
        conf_file.write(config)
        conf_file.close()
        tmp_overlay += f';{nrf52_leaudio_hotfix_overlay}'

    cmd.extend(('--', '-DOVERLAY_CONFIG={}'.format(tmp_overlay)))

    check_call(cmd, cwd=tester_dir)
    check_call(['west', 'flash', '--skip-rebuild', '--recover',
                '-i', debugger_snr], cwd=tester_dir)
