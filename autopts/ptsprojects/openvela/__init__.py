#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""openvela auto PTS project (A2DP only)

The autopts framework accesses profile modules via:
    getattr(autoprojects, 'a2dp', None)  -> openvela.a2dp module

Each profile module must export: set_pixits(), test_cases()
"""

# Import profile modules so they are accessible via getattr
from autopts.ptsprojects.openvela import a2dp as a2dp
from autopts.ptsprojects.openvela import iutctl as iutctl
