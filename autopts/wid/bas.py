#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant A/S.
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

log = logging.debug

_step = 0


def bas_wid_hdl(wid, description, test_case_name):
    log(f'{bas_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])    


# wid handlers section begin


def hdl_wid_5(_: WIDParams):
    """
        Please Change the Battery Level field of Battery Level Status characteristic.
    """
    btp.bas_set_battery_level();
    return True

def hdl_wid_7(_: WIDParams):
    """
        Please Change the Power State field of Battery Level Status characteristic.
    """
    btp.bas_set_battery_present();
    return True

def hdl_wid_18(_: WIDParams):
    """
        Please performs an action on the IUT that the battery does not present.
    
        Values that will be checked:
            "Battery present":       "No",
            "Battery charge State":  "Unknown",
            "Battery charge level":  "Unknown",
            "Charging Type":         "Unknown" OR "Not charging",
            "Charging fault reason": "Battery"
    """
    btp.bas_set_battery_present(battery_present=0);
    return True

def hdl_wid_21(_: WIDParams):
    """
        Please change the value of Battery Level Status characteristic.
    """
    btp.bas_set_battery_level();
    return True

def hdl_wid_34(_: WIDParams):
    """
        Please change the value of Battery Level characteristic.
    """
    btp.bas_set_battery_level();
    return True

def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True

def hdl_wid_20108(_: WIDParams):
    """
        Please send notifications for Characteristic 'Battery Level Status' to the PTS.
    """
    global _step
    _step = 1 if not _step else _step + 1

    if _step == 1:
        btp.bas_set_battery_present(battery_present=1)
    elif _step == 2:
        btp.bas_set_battery_level(battery_level=69)
    else:
        logging.exception("Error encountered during execution of operations.")

    return True
