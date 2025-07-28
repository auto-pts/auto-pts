#!/usr/bin/env python3

# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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

from autopts.utils import extract_wid_testcases_to_csv

# USE: Simply  run python3 -m tools.wid_usage in auto-pts directory

if __name__ == '__main__':
    extract_wid_testcases_to_csv()
