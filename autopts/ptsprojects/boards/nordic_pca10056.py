#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

from autopts.bot.mynewt import check_call

supported_projects = ['mynewt']
board_type = 'nordic_pca10056'


def reset_cmd(iutctl):
    """Return reset command for nRF52 DUT

    Dependency: nRF5x command line tools
    """
    with_srn = ''

    if iutctl.debugger_snr:
        with_srn = f' -s {iutctl.debugger_snr}'

    return f'nrfjprog -f nrf52 -r {with_srn}'


def build_and_flash(project_path, board, overlay=None, debugger_snr=None):
    """Build and flash Mynewt binary
    :param project_path: Mynewt source path
    :param board: IUT
    :param overlay: configuration map to be used
    :param debugger_snr: JLink serial number
    :return: TTY path
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, project_path,
                  board, overlay)

    check_call('rm -rf bin/'.split(), cwd=project_path)
    check_call(f'rm -rf targets/{board}_boot/'.split(),
               cwd=project_path)
    check_call('rm -rf targets/bttester/'.split(), cwd=project_path)

    check_call(f'newt target create {board}_boot'.split(),
               cwd=project_path)
    check_call('newt target create bttester'.split(), cwd=project_path)

    check_call(
        f'newt target set {board}_boot bsp=@apache-mynewt-core/hw/bsp/{board}'.split(), cwd=project_path)
    check_call(
        f'newt target set {board}_boot app=@mcuboot/boot/mynewt'.split(), cwd=project_path)
    check_call(f'newt target set {board}_boot syscfg=MYNEWT_DOWNLOADER=nrfjprog'.split(),
               cwd=project_path)

    check_call(
        f'newt target set bttester bsp=@apache-mynewt-core/hw/bsp/{board}'.split(), cwd=project_path)
    check_call(
        'newt target set bttester app=@apache-mynewt-nimble/apps/bttester'.split(),
        cwd=project_path)

    config = 'MYNEWT_DOWNLOADER=nrfjprog'
    if overlay:
        config += ':' + ':'.join([f'{k}={v}' for k, v in list(overlay.items())])

    check_call(f'newt target set bttester syscfg={config}'.split(), cwd=project_path)

    check_call(f'newt build {board}_boot'.split(), cwd=project_path)
    check_call('newt build bttester'.split(), cwd=project_path)

    check_call(f'newt create-image -2 {board}_boot timestamp'.split(),
               cwd=project_path)
    check_call('newt create-image -2 bttester timestamp'.split(), cwd=project_path)

    load_boot_cmd = f'newt load {board}_boot'.split()
    load_app_cmd = 'newt load bttester'.split()
    if debugger_snr:
        snr = f'JLINK_SN={debugger_snr}'
        load_boot_cmd.insert(0, snr)
        load_app_cmd.insert(0, snr)

    check_call(load_boot_cmd, cwd=project_path)
    check_call(load_app_cmd, cwd=project_path)
