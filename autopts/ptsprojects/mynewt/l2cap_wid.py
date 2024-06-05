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

import logging
import socket

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.wid import generic_wid_hdl
from autopts.pybtp.types import WIDParams

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log(f'{l2cap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.l2cap'])


def hdl_wid_255(_: WIDParams):
    """ description: Please send L2CAP Credit Based Connection REQ to PTS."""

    stack = get_stack()
    l2cap = stack.l2cap

    if l2cap.wid_cnt > 0:
        btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu, 1, 1, l2cap.hold_credits)
        l2cap.wait_for_connection(1)
        return True

    btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu, l2cap.num_channels, 1, l2cap.hold_credits)

    # Wait until all channels connected to avoid race condition between channel connection and new received wid
    for channel_id in range(l2cap.num_channels):
        l2cap.wait_for_connection(channel_id)

    l2cap.wid_cnt += 1

    return True
