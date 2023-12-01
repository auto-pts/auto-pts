#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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
import struct

from autopts.pybtp import btp, defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import AdType, OwnAddrType, WIDParams, gap_settings_btp2txt
from autopts.wid import generic_wid_hdl

log = logging.debug


def csip_wid_hdl(wid, description, test_case_name):
    log(f'{csip_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def hdl_wid_5(_: WIDParams):
    """
        Please have IUT enter GAP Discoverable Mode and generate Advertising Packets.
    """
    rsi = btp.csis_get_member_rsi()
    if not rsi:
        return False

    advdata = {}
    advdata[AdType.rsi] = struct.pack('<6B', *rsi)

    stack = get_stack()

    key = gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]
    if stack.gap.current_settings_get(key):
        btp.gap_adv_off()

    btp.gap_adv_ind_on(ad=advdata, own_addr_type=OwnAddrType.le_resolvable_private_address)
    return True


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad, own_addr_type=OwnAddrType.le_resolvable_private_address)
    return True


def hdl_wid_20108(_: WIDParams):
    """
        Please send notifications for Characteristic 'Set Member Lock' to the PTS.
        Expected Value: Any value
    """
    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True
