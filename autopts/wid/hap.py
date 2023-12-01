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

from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def hap_wid_hdl(wid, description, test_case_name):
    log(f'{hap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin

def hdl_wid_489(_: WIDParams):
    """
        Please click OK after IUT sync to BIS.
    """
    addr, addr_type = btp.pts_addr_get(), btp.pts_addr_type_get()
    stack = get_stack()

    btp.bap_broadcast_sink_setup()
    btp.bap_broadcast_scan_start()
    ev = stack.bap.wait_baa_found_ev(addr_type, addr, 30)
    btp.bap_broadcast_scan_stop()
    if ev:
        id, sid, addr_type, addr = ev['broadcast_id'], ev['advertiser_sid'], ev['addr_type'], ev['addr']
        btp.bap_broadcast_sink_sync(id, sid, 5, 600, False, 0, addr_type, addr)
        ev = stack.bap.wait_bis_found_ev(id, 50)

    return not ev is None


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True
