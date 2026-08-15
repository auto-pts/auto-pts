#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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

from autopts.wid import generic_wid_hdl

log = logging.debug


def opp_wid_hdl(wid, description, test_case_name):
    """WID dispatcher for OPP test cases on Zephyr.

    Looks up handlers first in this module, then falls back to the
    generic autopts.wid.opp module.

    Args:
        wid: WID (Wireless ID) number from PTS.
        description: params.description string (PTS-defined, not hardcoded).
        test_case_name: Name of the active test case.
    """
    log(f'{opp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name,
                           [__name__, 'autopts.wid.opp'])
