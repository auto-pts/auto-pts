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
import re
from enum import IntFlag

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams


class PresetProperty(IntFlag):
    BT_HAS_PROP_NONE = 0
    BT_HAS_PROP_WRITABLE = 1 << 0
    BT_HAS_PROP_AVAILABLE = 1 << 1


log = logging.debug


# wid handlers section begin

def hdl_wid_450(_: WIDParams):
    """
        Please add a new Preset Record.
    """
    n, properties = 5, PresetProperty.BT_HAS_PROP_AVAILABLE | PresetProperty.BT_HAS_PROP_WRITABLE
    btp.has_add_preset(n, properties, 'PRESET_' + str(n))
    return True


def hdl_wid_451(_: WIDParams):
    """
        Please remove the Preset Record with index n.
    """
    n = int(re.findall(r'\d', _.description)[0])
    btp.has_remove_preset(n)
    return True


def hdl_wid_452(_: WIDParams):
    """
        Please update preset name with index n
    """
    n = int(re.findall(r'\d', _.description)[0])
    btp.has_set_preset_name(n, 'CHANGED_' + str(n))
    return True


def hdl_wid_453(_: WIDParams):
    """
        Please set the Preset record with Index n as available.
    """
    n = int(re.findall(r'\d', _.description)[0])
    properties = PresetProperty.BT_HAS_PROP_WRITABLE | PresetProperty.BT_HAS_PROP_AVAILABLE
    btp.has_set_properties(n, properties)
    return True


def hdl_wid_454(_: WIDParams):
    """
        Please sets the Preset record with Index n as unavailable.
    """
    n = int(re.findall(r'\d', _.description)[0])
    properties = PresetProperty.BT_HAS_PROP_WRITABLE
    btp.has_set_properties(n, properties)
    return True


def hdl_wid_457(_: WIDParams):
    """
        Please set Active Index to n
    """
    n = int(re.findall(r'\d', _.description)[0])
    btp.has_set_active_index(n)
    return True


def hdl_wid_492(_: WIDParams):
    """
        Please remove all preset records from IUT.
    """
    btp.has_set_active_index(0)
    btp.has_remove_preset(0)
    return True


def hdl_wid_494(_: WIDParams):
    """
        Please do the followings:
            1. change the Preset Name of TSPX_writable_preset_index[0] to a random name.
            2. add a new Preset record
            3. add a new Preset record
            4. Set the Active Preset to the record added in Step 2.
            5. Change the name of TSPX_writable_preset_index[1] to "New Name item"
            6. Remove Preset Record 4.
    """
    n = defs.HAS_TSPX_writable_preset_indices[0]
    btp.has_set_preset_name(n, 'RANDOM_' + str(n))
    properties = PresetProperty.BT_HAS_PROP_AVAILABLE | PresetProperty.BT_HAS_PROP_WRITABLE
    btp.has_add_preset(8, properties, 'PRESET_8')
    btp.has_add_preset(6, properties, 'PRESET_6')
    btp.has_set_active_index(8)
    btp.has_set_preset_name(defs.HAS_TSPX_writable_preset_indices[1], 'New Name Item')
    btp.has_remove_preset(4)
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


def hdl_wid_20002(_: WIDParams):
    """
        Please prepare IUT into an L2CAP Credit Based Connection connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept L2CAP_CREDIT_BASED_CONNECTION_REQ from PTS.
    """
    return True


def hdl_wid_20108(_: WIDParams):
    """
        Please send notifications for Characteristic 'Active Preset Index' to the PTS.
        Expected Value: Any value
    """
    return True


def hdl_wid_20109(_: WIDParams):
    """
        Please send indications for Characteristic 'Hearing Aid Preset Control Point' to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can send indication.
        Expected Value: Any value"
    """
    return True
