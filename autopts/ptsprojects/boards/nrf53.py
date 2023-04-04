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

from .nrf5x import *
from autopts.bot.common import check_call

board_type = 'nrf5340dk_nrf5340_cpuapp'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)

    tester_dir = os.path.join(zephyr_wd, 'tests', 'bluetooth', 'tester')
    controller_dir = os.path.join(zephyr_wd, 'samples', 'bluetooth', 'hci_rpmsg')

    check_call('rm -rf build/'.split(), cwd=tester_dir)
    check_call('rm -rf build/'.split(), cwd=controller_dir)

    bttester_overlay = 'nrf5340_hci_rpmsg.conf;./overlay-debug.conf'

    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        bttester_overlay += f';{conf_file}'

    cmd = ['west', 'build', '-b', board, '--', f'-DOVERLAY_CONFIG={bttester_overlay}']
    check_call(cmd, cwd=tester_dir)
    check_call(['west', 'flash', '--skip-rebuild', '--recover', '-i', debugger_snr], cwd=tester_dir)

    controller_overlay = 'bttester_hci_rpmsg_overlay.conf'
    check_call(f'echo CONFIG_BT_CTLR_CONN_ISO_LOW_LATENCY_POLICY=y > {controller_overlay}'.split(),
               cwd=controller_dir)

    cmd = ['west', 'build', '-b', 'nrf5340dk_nrf5340_cpunet', '--',
           f'-DOVERLAY_CONFIG=nrf5340_cpunet_iso-bt_ll_sw_split.conf;{controller_overlay}']
    check_call(cmd, cwd=controller_dir)
    check_call(['west', 'flash', '--skip-rebuild', '-i', debugger_snr], cwd=controller_dir)
