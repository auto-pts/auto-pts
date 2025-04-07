#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
$ python3 cache_testcases.py path/to/workspace.pqw6 path/to/cached_testcases.yaml
"""
import sys
from os.path import abspath, dirname

import yaml

if __name__ == '__main__':
    AUTOPTS_REPO = dirname(dirname(dirname(abspath(__file__))))
    sys.path.insert(0, AUTOPTS_REPO)


from autopts.ptscontrol import PyPTS


def cache_test_cases(workspace_path, cache_file_path):
    pts = PyPTS(lite_start=True)
    pts.start_pts()
    pts.open_workspace(workspace_path)
    projects = pts.get_project_list()

    test_cases = {}
    for project in projects:
        test_cases[project] = list(pts.get_test_case_list(project))

    with open(cache_file_path, 'w') as stream:
        yaml.dump(test_cases, stream)


def main():
    if len(sys.argv) < 3:
        sys.exit(f'Usage:\n$ python3 {sys.argv[0]} path/to/workspace.pqw6 path/to/cached_test_cases.txt')

    workspace_path = sys.argv[1]
    cache_file_path = sys.argv[2]
    cache_test_cases(workspace_path, cache_file_path)


if __name__ == '__main__':
    main()
