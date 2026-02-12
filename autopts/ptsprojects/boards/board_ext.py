#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Nordic Semiconductor ASA.
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

supported_projects = ["zephyr"]


def reset_cmd(iutctl):
    """Return reset command for DUT
    """

    get_reset_cmd = os.getenv("AUTOPTS_RESET_CMD")
    if get_reset_cmd is None:
        raise Exception("AUTOPTS_RESET_CMD env variable is not set")

    cmd = subprocess.run(
        [get_reset_cmd, "--snr", f"{iutctl.debugger_snr}"],
        check=True,
        stdout=subprocess.PIPE,
    )

    return cmd.stdout.decode()


def build_and_flash(zephyr_wd, tester_app_dir, board, debugger_snr, conf_file=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param tester_app_dir: path to tester application relative to zephyr_wd
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """

    build_and_flash_cmd = os.getenv("AUTOPTS_BUILD_FLASH_CMD")
    if build_and_flash_cmd is None:
        raise Exception("AUTOPTS_BUILD_FLASH_CMD env variable is not set")

    logging.debug("%s: %s %s %s %s", build_and_flash.__name__, zephyr_wd, tester_app_dir, board, conf_file)

    tester_dir = os.path.join(zephyr_wd, tester_app_dir)

    # board is not send to program as it's not set and this file may be used for different boards
    # the program is expected to retrieve board information from SNR
    subprocess.run(
        [
            build_and_flash_cmd,
            "--snr",
            f"{debugger_snr}",
            "--config",
            f"{conf_file}",
        ],
        check=True,
        cwd=tester_dir,
    )
