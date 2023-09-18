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

from time import sleep
from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams, ASCSState
from autopts.wid import generic_wid_hdl

log = logging.debug


def cap_wid_hdl(wid, description, test_case_name):
    log(f'{cap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin

def hdl_wid_202(_: WIDParams):
    """
        Please start audio streaming, and set to Audio Stream Endpoint to STREAMING state for ASE ID 1.
    """
    result = re.search(r'ASE ID (\d)', _.description)
    if result:
        ase_id = int(result.group(1), 16)
        addr_type, addr = btp.pts_addr_type_get(), btp.pts_addr_get()
        stack = get_stack()
        # Check whether streaming was strated
        ev = stack.ascs.wait_ascs_ase_state_changed_ev(addr_type, addr, ase_id, ASCSState.STREAMING, 200)
        return not ev is None

    return False


def hdl_wid_415(_: WIDParams):
    """
        Please stop broadcast, and wait for 10 seconds.
    """
    sleep(10)

    return True


def hdl_wid_416(_: WIDParams):
    """
        Please start broadcast.
    """
    return True

    
def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True
