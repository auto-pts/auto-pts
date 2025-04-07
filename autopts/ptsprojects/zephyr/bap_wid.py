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

import logging

from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl


log = logging.debug


def bap_wid_hdl(wid, description, test_case_name):
    log(f'{bap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.bap'])


def hdl_wid_20107(_: WIDParams):
    """
    Please send Read Request to read X characteristic with handle = 0xXXXX.
    """

    # Zephyr API reads the characteristics at discovery and
    # the PTS disconnects immediately after that.

    return True
