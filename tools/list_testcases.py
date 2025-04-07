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
import os
import sys
from os.path import abspath, dirname

from autopts.client import get_test_cases
from autopts.ptscontrol import PyPTS

AUTOPTS_REPO = dirname(dirname(abspath(__file__)))
sys.path.insert(0, AUTOPTS_REPO)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.exit(f'Usage:\n$ python3 {sys.argv[0]} path/to/workspace.pqw6')

    workspace_path = sys.argv[1]

    if not os.path.isfile(workspace_path) or not workspace_path.endswith('.pqw6'):
        sys.exit(f'{workspace_path} is not a file or workspace (*.pqw6)!')

    pts = PyPTS(lite_start=True)
    pts.start_pts()
    pts.open_workspace(workspace_path)
    test_cases = get_test_cases(pts, [], [])

    for test_case_name in test_cases:
        print(test_case_name)
