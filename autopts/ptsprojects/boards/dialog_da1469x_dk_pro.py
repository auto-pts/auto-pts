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
import os
import sys
from autopts.bot.common import check_call

supported_projects = ['mynewt']


def reset_cmd(iutctl):
    """Return reset command for Dialog da1469x dk pro

    Dependency: nRF5x command line tools
    """

    if sys.platform == "win32":
        jlink = 'JLink'
    else:
        jlink = 'JLinkExe'

    reset_jlink = 'reset.jlink'

    if not os.path.exists(reset_jlink):
        with open(reset_jlink, 'x') as f:
            f.write('r\nq')

    return '{} -nogui 1 -if swd -speed 4000 -device CORTEX-M33 -commanderscript {}' \
        .format(jlink, reset_jlink)


def build_and_flash(project_path, board, overlay=None):
    """Build and flash Mynewt binary
    :param project_path: Mynewt source path
    :param board: IUT
    :param overlay: configuration map to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, project_path,
                  board, overlay)

    board = 'dialog_da1469x-dk-pro'
    check_call('rm -rf bin/'.split(), cwd=project_path)
    check_call('rm -rf targets/da1469x_boot/'.split(),
               cwd=project_path)
    check_call('rm -rf targets/da1469x_flash_loader/'.split(), cwd=project_path)
    check_call('rm -rf targets/dialog_cmac/'.split(), cwd=project_path)
    check_call('rm -rf targets/da1469x_bttester/'.split(), cwd=project_path)

    check_call('newt target create da1469x_boot'.split(),
               cwd=project_path)
    check_call('newt target create da1469x_flash_loader'.split(),
               cwd=project_path)
    check_call('newt target create dialog_cmac'.split(), cwd=project_path)
    check_call('newt target create da1469x_bttester'.split(), cwd=project_path)

    check_call(
        'newt target set da1469x_boot bsp=@apache-mynewt-core/hw/bsp/{0}'.format(
            board).split(), cwd=project_path)
    check_call(
        'newt target set da1469x_boot app=@mcuboot/boot/mynewt'.split(), cwd=project_path)

    check_call(
        'newt target set da1469x_flash_loader bsp=@apache-mynewt-core/hw/bsp/{}'.format(board).split(),
        cwd=project_path)
    check_call(
        'newt target set da1469x_flash_loader app=@apache-mynewt-core/apps/flash_loader'.split(), cwd=project_path)
    check_call(
        'newt target set da1469x_flash_loader syscfg=FLASH_LOADER_DL_SZ=0x10000:RAM_RESIDENT=1'.split(),
        cwd=project_path)

    check_call(
        'newt target set dialog_cmac bsp=@apache-mynewt-core/hw/bsp/dialog_cmac'.split(), cwd=project_path)
    check_call(
        'newt target set dialog_cmac app=@apache-mynewt-nimble/apps/blehci'.split(), cwd=project_path)
    check_call('newt target set dialog_cmac build_profile=speed'.split(), cwd=project_path)

    with open(os.path.join(project_path, 'targets/dialog_cmac/syscfg.yml'), 'w') as f:
        f.write('''syscfg.vals:
  MCU_DEEP_SLEEP: 1
  MCU_SLP_TIMER: 1
  MCU_SLP_TIMER_32K_ONLY: 1

  BLE_HCI_TRANSPORT: dialog_cmac

  # LL recommended settings (decreasing timing values is not recommended)
  BLE_LL_CFG_FEAT_CTRL_TO_HOST_FLOW_CONTROL: 1
  BLE_LL_CONN_INIT_MIN_WIN_OFFSET: 2
  BLE_LL_RFMGMT_ENABLE_TIME: 20
  BLE_LL_SCHED_AUX_MAFS_DELAY: 150
  BLE_LL_SCHED_AUX_CHAIN_MAFS_DELAY: 150

  # NOTE: set public address in target settings
  BLE_PUBLIC_DEV_ADDR: "(uint8_t[6]){0xff, 0xff, 0xff, 0xff, 0xff, 0xff}"

  BLE_EXT_ADV: 1
  BLE_PERIODIC_ADV: 1
  BLE_LL_CFG_FEAT_LE_2M_PHY: 1
  BLE_LL_NUM_SCAN_DUP_ADVS: 256
''')

    check_call(
        'newt target set da1469x_bttester bsp=@apache-mynewt-core/hw/bsp/{}'.format(board).split(), cwd=project_path)
    check_call(
        'newt target set da1469x_bttester app=@apache-mynewt-nimble/apps/bttester'.split(),
        cwd=project_path)
    check_call('newt target set da1469x_bttester build_profile=debug'.split(), cwd=project_path)
    check_call('newt target set da1469x_bttester syscfg='
               'BLE_HCI_TRANSPORT=dialog_cmac:'
               'CMAC_IMAGE_TARGET_NAME=dialog_cmac'.split(), cwd=project_path)

    if overlay is not None:
        config = ':'.join(['{}={}'.format(k, v) for k, v in list(overlay.items())])
        check_call('newt target set da1469x_bttester syscfg={}'.format(config).split(),
                   cwd=project_path)

    check_call('newt build dialog_cmac'.split(), cwd=project_path)
    check_call('newt build da1469x_flash_loader'.split(), cwd=project_path)
    check_call('newt build da1469x_boot'.split(), cwd=project_path)
    check_call('newt build da1469x_bttester'.split(), cwd=project_path)

    check_call('newt create-image -2 da1469x_flash_loader timestamp'.split(),
               cwd=project_path)
    check_call('newt create-image -2 da1469x_boot timestamp'.split(),
               cwd=project_path)
    check_call('newt create-image -2 da1469x_bttester timestamp'.split(), cwd=project_path)

    check_call('newt load da1469x_flash_loader'.split(), cwd=project_path)
    check_call('newt load da1469x_boot'.split(), cwd=project_path)
    check_call('newt load da1469x_bttester'.split(), cwd=project_path)
