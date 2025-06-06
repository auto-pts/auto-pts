#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup.
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

"""Script for printing old overlays

Run under Windows.

Usage:
$ python3 zephyr path\to\auto-pts\\workspaces\\zephyr\\zephyr-master\\zephyr-master.pqw6
$ python3 mynewt "path\to\auto-pts\\workspaces\nimble-master\nimble-master.pqw6"
"""

import importlib
import os
import sys

import win32com
import wmi

from autopts.ptscontrol import PyPTS


class PyPTSControl(PyPTS):
    """PTS control interface.
    This class contains cherry picked functionality from ptscontrol.PyPTS
    """

    def start_pts(self):
        """Overwrite to enable running without dongle"""
        # Get PTS process list before running new PTS daemon
        c = wmi.WMI()

        pts_ps_list_pre = list(c.Win32_Process(name="PTS.exe"))

        self._pts = win32com.client.Dispatch('ProfileTuningSuite_6.PTSControlServer')

        # Get PTS process list after running new PTS daemon to get PID of
        # new instance
        pts_ps_list_post = list(c.Win32_Process(name="PTS.exe"))

        pts_ps_list = list(set(pts_ps_list_post) - set(pts_ps_list_pre))
        if not pts_ps_list:
            print("Error during pts startup!")
            return

        self._pts_proc = pts_ps_list[0]

        print(f"Started new PTS daemon with pid: {self._pts_proc.ProcessId}")

    def get_bluetooth_address(self):
        return '123445567890'


if __name__ == '__main__':

    if len(sys.argv) < 3:
        sys.exit(f'Usage:\n$ python3 {sys.argv[0]} <project_name> path/to/workspace.pqw6')

    project = sys.argv[1]
    mod = importlib.import_module('autopts.bot.iut_config.' + project)
    iut_config = mod.iut_config
    test_case_prefixes = []

    for _config, value in list(iut_config.items()):
        if 'test_cases' not in value:
            continue
        test_case_prefixes.extend(value['test_cases'])

    workspace_path = sys.argv[2]

    if not os.path.isfile(workspace_path) or not workspace_path.endswith('.pqw6'):
        sys.exit(f'{workspace_path} is not a file or workspace (*.pqw6)!')

    print('Starting PTS needed to workspace parsing ...')
    pts = PyPTSControl()
    pts.open_workspace(workspace_path)

    profiles = []
    workspace_test_cases = []

    for profile in pts.get_project_list():
        profiles.append(profile)
        workspace_test_cases.extend(pts.get_test_case_list(profile))

    print('Old overlays:')
    for tc_prefix in test_case_prefixes:
        valid = False
        for tc in workspace_test_cases:
            if tc.startswith(tc_prefix):
                valid = True
                break
        if not valid:
            print(tc_prefix)
