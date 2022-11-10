#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2022, NXP.
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
import os
import sys

supported_projects = ['zephyr']


def reset_cmd(iutctl):
    if sys.platform == "win32":
        jlink = 'JLink'
    else:
        jlink = 'JLinkExe'

    if iutctl.debugger_snr is None:
        return f'{jlink} -device MIMXRT1062XXX6A -CommandFile {generate_reset_file()}'
    else:
        return f'{jlink} -usb {iutctl.debugger_snr} -device MIMXRT1062XXX6A -CommandFile {generate_reset_file()}'


def generate_reset_file():
    reset_command = "si 1\n" \
                    "speed 4000\n" \
                    "h\n" \
                    "RSetType 2\n" \
                    "r\n" \
                    "g\n" \
                    "q\n"
    file_path = "reset.jlink"
    if not os.path.exists(file_path):
        with open(file_path, 'x') as f:
            f.write(reset_command)
            f.close()
    return file_path
