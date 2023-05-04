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
import os
import sys
import logging

log = logging.debug

supported_projects = ['zephyr']


def reset_cmd(iutctl):

    def _generate_reset_file():
        reset_command = "si 1\n" \
                        "speed 4000\n" \
                        "h\n" \
                        "r\n" \
                        "g\n" \
                        "q\n"
        file_path = "reset.jlink"
        if not os.path.exists(file_path):
            with open(file_path, 'x') as f:
                f.write(reset_command)
                f.close()
        return file_path

    jlink = 'JLink' if sys.platform == "win32" else 'JLinkExe'

    jlink_cmd = [jlink, '-CommandFile', _generate_reset_file()]
    device_option = ['-device', iutctl.device_core]
    debugger_option = ['-usb', iutctl.debugger_snr] if iutctl.debugger_snr else []
    jlink_cmd += debugger_option + device_option

    return ' '.join(jlink_cmd)
