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

from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl
from autopts.wid.gmcs import hdl_wid_20141 as _generic_hdl_wid_20141
from autopts.wid.gmcs import hdl_wid_20142 as _generic_hdl_wid_20142

log = logging.debug


def gmcs_wid_hdl(wid, description, test_case_name):
    log(f'{gmcs_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.gmcs'])


def hdl_wid_20141(params: WIDParams):
    """Please update Media Player Name/Track Title characteristic with value
       whose length is greater than the (ATT_MTU-3). Click OK when it is ready."""

    if params.test_case_name == 'GMCS/SR/SPN/BV-02-C':
        # This relies on the Zephyr Media Player sample: its initial track
        # title ("Track 1.1 with a very long name") is already longer than
        # ATT_MTU-3 with the default ATT_MTU of 23, so nothing to do.
        return True

    return _generic_hdl_wid_20141(params)


def hdl_wid_20142(params: WIDParams):
    """Please update Media Player Name/Track Title characteristic and send a
       notification containing the updated value of the characteristic with
       a different value whose length is greater than the (ATT_MTU-3)."""

    if params.test_case_name == 'GMCS/SR/SPN/BV-02-C':
        # This relies on the Zephyr Media Player sample: moves to
        # "Track 1.2 with a very long name", which notifies the Track Title.
        MEDIA_PROXY_OP_NEXT_TRACK = 0x31
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_TRACK, 0)
        return True

    return _generic_hdl_wid_20142(params)
