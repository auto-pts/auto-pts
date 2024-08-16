#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant.
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
import re
import sys

from enum import IntFlag
from autopts.pybtp import btp, defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

class PresetProperty(IntFlag):
    BT_BAS_PROP_NONE      = 0
    BT_BAS_PROP_WRITABLE  = 1<<0
    BT_BAS_PROP_AVAILABLE = 1<<1

log = logging.debug


def bas_wid_hdl(wid, description, test_case_name):
    log(f'{bas_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])    


# wid handlers section begin



def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True

def hdl_wid_20002(_: WIDParams):
    """
        Please prepare IUT into an L2CAP Credit Based Connection connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept L2CAP_CREDIT_BASED_CONNECTION_REQ from PTS.
    """
    return True

def hdl_wid_20100(_: WIDParams): ## TODO: test remove
    btp.gap_conn()
    return True

def hdl_wid_20101(_: WIDParams):
    """
    description: Please send discover primary services command to the PTS.
                 Description: Verify that the Implementation Under Test (IUT)
                 can send Discover All Primary Services or
                 Discovery Primary Services by Service UUID command.
    """
    stack = get_stack()

    btp.gattc_disc_all_prim(btp.pts_addr_type_get(),
                            btp.pts_addr_get())
    svcs = btp.gattc_disc_all_prim_rsp()

    stack.gatt.verify_values = svcs

    return True

def hdl_wid_20103(_: WIDParams):
    """
        Please take action to discover the Battery Level Status characteristic from the Battery Service.
        Discover the primary service if needed.
        Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    try:
        btp.gattc_disc_all_chrc(bd_addr_type, bd_addr, 0x0001, 0xffff)
        attrs = btp.gattc_disc_all_chrc_rsp()

        stack.gatt.verify_values = attrs
        return True
    
    except:
        return False

# def hdl_wid_20108(_: WIDParams):
#     """
#         Please send notifications for Characteristic 'Battery Level Status' to the PTS.
#         Expected Value: Any value
#     """
#     return True