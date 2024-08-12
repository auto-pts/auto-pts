#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def gattc_wid_hdl(wid, description, test_case_name):
    log(f'{gattc_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    stack = get_stack()
    if stack.is_svc_supported('GATT_CL') and 'GATT/CL' in test_case_name:
        return generic_wid_hdl(wid, description, test_case_name,
                               [__name__, 'autopts.ptsprojects.mynewt.gatt_client_wid',
                                'autopts.wid.gatt_client'])

    return generic_wid_hdl(wid, description, test_case_name,
                           [__name__, 'autopts.ptsprojects.mynewt.gatt_wid',
                            'autopts.wid.gatt'])

def hdl_wid_142(_: WIDParams):
    """
    Please send an ATT_Write_Request to Client Support Features handle = '0015'O with 0x02 to enable Enhanced ATT.

    Discover all characteristics if needed.
    """

    btp.gap_pair()

    return True


def hdl_wid_400(_: WIDParams):

    return True


def hdl_wid_402(_: WIDParams):
    """Please initiate an L2CAP Credit Based Connection using LE signaling channel to the PTS."""

    return True
