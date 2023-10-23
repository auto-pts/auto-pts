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

"""Script for printing test cases enabled in workspace

Usage:
$ python3 testplan_vs_workspace.py path/to/workspace.pqw6
"""
import sys
import os
import win32com.client


if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.exit(f'Usage:\n$ python3 {sys.argv[0]} path/to/workspace.pqw6')

    workspace_path = sys.argv[1]

    if not os.path.isfile(workspace_path) or not workspace_path.endswith('.pqw6'):
        sys.exit('{} is not a file or workspace (*.pqw6)!'.format(workspace_path))

    pts = win32com.client.Dispatch('ProfileTuningSuite_6.PTSControlServer')
    pts.OpenWorkspace(workspace_path)

    for i in range(0, pts.GetProjectCount()):
        project_name = pts.GetProjectName(i)

        for j in range(0, pts.GetTestCaseCount(project_name)):
            test_case_name = pts.GetTestCaseName(project_name, j)
            print(test_case_name)
