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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.wid import generic_wid_hdl
from autopts.pybtp.types import *
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.ptsprojects.testcase import MMI

log = logging.debug


def tmap_wid_hdl(wid, description, test_case_name):
    log(f'{tmap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_100(params: WIDParams):
    """
    Please synchronize with Broadcast ISO request
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    stack = get_stack()

    btp.bap_broadcast_sink_setup()
    btp.bap_broadcast_scan_start()

    ev = stack.bap.wait_baa_found_ev(addr_type, addr, 30, False)
    if ev is None:
        log('BAA not found.')
        return False

    btp.bap_broadcast_scan_stop()

    log(f'Synchronizing to broadcast with ID {hex(ev["broadcast_id"])}')

    btp.bap_broadcast_sink_sync(ev['broadcast_id'], ev['advertiser_sid'],
                                5, 100, False, 0, ev['addr_type'], ev['addr'])

    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_found_ev(broadcast_id, 20, False)
    if ev is None:
        log(f'BIS not found, broadcast ID {broadcast_id}')
        return False

    # BIS_Sync bitfield uses bit 0 for BIS Index 1
    requested_bis_sync = 1
    bis_ids = [1]

    btp.bap_broadcast_sink_bis_sync(broadcast_id, requested_bis_sync)

    for bis_id in bis_ids:
        broadcast_id = ev['broadcast_id']
        ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 10, False)
        if ev is None:
            log(f'Failed to sync to BIS with ID {bis_id}, broadcast ID {broadcast_id}')
            return False

    return True


def hdl_wid_376(_: WIDParams):
    """
    Please confirm received streaming data.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    for ev in stack.bap.event_queues[defs.BAP_EV_ASE_FOUND]:
        _, _, ase_dir, ase_id = ev

        if ase_dir == AudioDir.SINK:
            ev = stack.bap.wait_stream_received_ev(addr_type, addr, ase_id, 10)
            if ev is None:
                return False

    return True


def hdl_wid_384(_: WIDParams):
    """
    Click OK will start transmitting audio streaming data.
    """

    return True


def hdl_wid_507(_: WIDParams):
    """
    Please confirm if the IUT read Front Left/Right Audio Location.
    """

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


def hdl_wid_20100(_: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    stack = get_stack()
    addr = btp.pts_addr_get()
    btp.gap_conn()
    stack.gap.wait_for_connection(timeout=5, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=50)

    return True


def hdl_wid_20103(_: WIDParams):
    """
        Please take action to discover the TMAP Role characteristic from the Telephony and Media Audio.
        Discover the primary service if needed.
        Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.tmap_discover(addr_type, addr)
    ev = stack.tmap.wait_discovery_completed_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True

def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read X characteristic with handle = 0xXXXX.
    """

    logging.debug("description=%r", params.description)

    MMI.reset()
    MMI.parse_description(params.description)
    handle = MMI.args[0]

    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(), handle)
    btp.gattc_read_rsp()

    return True

def hdl_wid_20116(_: WIDParams):
    """
        Please take action to discover the TMAP Role characteristic from the Telephony and Media Audio.
        Discover the primary service if needed.
        Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.tmap_discover(addr_type, addr)
    ev = stack.tmap.wait_discovery_completed_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True
