#
# auto-pts - The Bluetooth PTS Automation Framework
#
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

"""Script for printing diff between testplan.xlsx and active test cases in workspace

Usage:
$ python3 testplan_vs_workspace.py path/to/workspace path/to/test_plan.xlsx
"""
import sys
import os
import pandas as pd
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
        pts_ps_list_pre = []
        pts_ps_list_post = []

        for ps in c.Win32_Process(name="PTS.exe"):
            pts_ps_list_pre.append(ps)

        self._pts = win32com.client.Dispatch('ProfileTuningSuite_6.PTSControlServer')

        # Get PTS process list after running new PTS daemon to get PID of
        # new instance
        for ps in c.Win32_Process(name="PTS.exe"):
            pts_ps_list_post.append(ps)

        pts_ps_list = list(set(pts_ps_list_post) - set(pts_ps_list_pre))
        if not pts_ps_list:
            print("Error during pts startup!")
            return

        self._pts_proc = pts_ps_list[0]

        print("Started new PTS daemon with pid: %d" % self._pts_proc.ProcessId)

    def get_bluetooth_address(self):
        return '123445567890'


if __name__ == '__main__':

    if len(sys.argv) < 3:
        sys.exit('Usage:\n$ python3 {} path/to/workspace path/to/test_plan.xlsx'.format(sys.argv[0]))

    workspace_path = sys.argv[1]
    testplan_path = sys.argv[2]

    if not os.path.isfile(workspace_path) or not workspace_path.endswith('.pqw6'):
        sys.exit('{} is not a file or workspace (*.pqw6)!'.format(workspace_path))

    if not os.path.isfile(testplan_path) or not testplan_path.endswith('.xlsx'):
        sys.exit('{} is not a file or test plan (*.xlsx)!'.format(testplan_path))

    print('Starting PTS needed to workspace parsing ...')
    pts = PyPTSControl()
    pts.open_workspace(workspace_path)

    profiles = []
    workspace_test_cases = []

    for profile in pts.get_project_list():
        profiles.append(profile)

        for test_case in pts.get_test_case_list(profile):
            workspace_test_cases.append(test_case)

    test_plan_test_cases = []
    test_plan = pd.read_excel(testplan_path, sheet_name='TestPlan')
    test_plan_column_0 = test_plan.iloc[:, 0]

    in_test_case_table = False

    prev_row = None

    for row in test_plan_column_0:
        if pd.isna(row):
            in_test_case_table = False
        elif not in_test_case_table:
            if row == 'Test Case ID' and '.TS.' in prev_row:
                in_test_case_table = True
        else:
            test_plan_test_cases.append(row)

        prev_row = row

    workspace_test_cases = set(workspace_test_cases)
    test_plan_test_cases = set(test_plan_test_cases)

    print('Test cases which are in workspace, but not in test plan')
    [print(i) for i in sorted(workspace_test_cases - test_plan_test_cases)]

    print('Test cases which are in test plan, but not in workspace')
    [print(i) for i in sorted(test_plan_test_cases - workspace_test_cases)]
