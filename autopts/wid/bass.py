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
import struct

from autopts.ptsprojects.stack import WildCard, get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import UUID, AdFlags, AdType, BASSPASyncState, BIGEncryption, WIDParams, gap_settings_btp2txt

log = logging.debug


def hdl_wid_100(param: WIDParams):
    """
    Please synchronize with Broadcast ISO request.
    """
    stack = get_stack()

    ev = stack.bap.wait_pa_sync_req_ev(WildCard(), WildCard(), 30, False)
    if ev is None:
        log('PA sync request not received.')
        return False

    log(f'Synchronizing to broadcast with ID {hex(ev["broadcast_id"])}')

    btp.bap_broadcast_sink_sync(ev['broadcast_id'], ev['advertiser_sid'],
                                5, 1000, ev['past_avail'], ev['src_id'],
                                ev['addr_type'], ev['addr'])

    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_found_ev(broadcast_id, 20, False)
    if ev is None:
        log(f'BIS not found, broadcast ID {broadcast_id}')
        return False

    # Workaround for BASS/SR/SPE/BI-06-C: This test case validates invalid length handling
    # and doesn't require PA or BIS sync. However, PTS sends Add Source requesting only PA sync,
    # then sends WID 100 (which expects BIS sync per its description "synchronize with Broadcast
    # ISO"). This mismatch causes the BIS sync wait to timeout. Skip BIS sync wait for this test
    # case until PTS is fixed (e.g., by using a different WID, requesting BIS sync in Add Source,
    # or not sending WID 100 for this test).
    if param.test_case_name in ['BASS/SR/SPE/BI-06-C']:
        return True

    bis_id = ev['bis_id']
    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 10, False)
    if ev is None:
        log(f'Failed to sync to BIS with ID {bis_id}, broadcast ID {broadcast_id}')
        return False

    return True


def hdl_wid_101(param: WIDParams):
    """
    Wait for the Broadcast Receive State Characteristic to get the state of PA Sync.
    """

    if param.test_case_name in ['BASS/SR/CP/BV-16-C']:
        stack = get_stack()
        ev = stack.bap.wait_pa_sync_req_ev(WildCard(), WildCard(), 30, False)
        if ev is None:
            log('PA sync request not received.')
            return False

        log(f'Synchronizing to broadcast with ID {hex(ev["broadcast_id"])}')

        btp.bap_broadcast_sink_sync(ev['broadcast_id'], ev['advertiser_sid'],
                                    5, 1000, ev['past_avail'], ev['src_id'],
                                    ev['addr_type'], ev['addr'])

    return True


def hdl_wid_102(_: WIDParams):
    """
    Please click OK when IUT establishes BIG sync. Lower tester will terminate BIG.
    """
    stack = get_stack()
    ev_queue = stack.bap.event_queues[defs.BTP_BAP_EV_PA_SYNC_REQ]
    if len(ev_queue) == 0:
        log('PA sync request not received.')
        return False

    ev = ev_queue[0]
    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_found_ev(broadcast_id, 10, False)
    if ev is None:
        log('BIS not found')
        return False

    bis_id = ev['bis_id']
    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 10, False)
    if ev is None:
        log(f'Failed to sync to BIS with ID {bis_id}, broadcast ID {broadcast_id}')
        return False
    return True


def hdl_wid_103(_: WIDParams):
    """
    Please Send Broadcast Receive State notification.
    """
    return True


def hdl_wid_104(_: WIDParams):
    """
    Please send non connectable advertise with periodic info.
    """
    return True


def hdl_wid_110(_: WIDParams):
    """
    Please stop the synchronization with the broadcast source then send Broadcast Receive State notification.
    """
    stack = get_stack()

    ev_queue = stack.bap.event_queues[defs.BTP_BAP_EV_BIS_FOUND]
    if len(ev_queue) == 0:
        return False

    ev = ev_queue[0]
    broadcast_id = ev['broadcast_id']
    btp.bap_broadcast_sink_stop(broadcast_id)

    return True


def hdl_wid_111(_: WIDParams):
    """
    Lower tester doesn't expect to receive Broadcast Receive State Characteric.
    """
    return True


def hdl_wid_113(_: WIDParams):
    """
    Please synchronize (server initiated) to public address of xxxxxxxxxxxx.
    """
    stack = get_stack()
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    btp.bap_broadcast_scan_start()

    ev = stack.bap.wait_baa_found_ev(addr_type, addr, 10, False)
    if ev is None:
        log('BAA not found.')
        return False

    btp.bap_broadcast_scan_stop()

    log(f'Synchronizing to broadcast with ID {hex(ev["broadcast_id"])}')

    btp.bap_broadcast_sink_sync(ev['broadcast_id'], ev['advertiser_sid'],
                                5, 1000, False, 0,
                                ev['addr_type'], ev['addr'])

    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_found_ev(broadcast_id, 20, False)
    if ev is None:
        log(f'BIS not found, broadcast ID {broadcast_id}')
        return False

    # BIS_Sync bitfield uses bit 0 for BIS Index 1
    requested_bis_sync = 1 << (ev['bis_id'] - 1)
    btp.bap_broadcast_sink_bis_sync(ev['broadcast_id'], requested_bis_sync)

    bis_id = ev['bis_id']
    broadcast_id = ev['broadcast_id']
    ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 10, False)
    if ev is None:
        log(f'Failed to sync to BIS with ID {bis_id}, broadcast ID {broadcast_id}')
        return False

    return True


def hdl_wid_115(_: WIDParams):
    """
    Please verify the metadata:
    BASC Subgroup:
        BIS Sync: [0x00000000]
        Metadata Length: [0 (0x00)]
    """
    return True


def hdl_wid_116(_: WIDParams):
    """
    Please expose a Broadcast Receive State with BIG_Encryption
    field indicating Broadcast_Code required.
    """

    stack = get_stack()

    # Add a Broadcast Receive State with BIG_Encryption field set to indicate
    # Broadcast_Code required, other fields are arbitrary valid values
    broadcaster_addr_type = 0x00  # Public address
    broadcaster_addr = '001122334455'
    advertiser_sid = 0x01
    broadcast_id = 0x123456
    bis_sync = 0
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    big_encryption = BIGEncryption.BROADCAST_CODE_REQUIRED

    btp.bap_scan_delegator_add_src(
        broadcaster_addr_type, broadcaster_addr,
        advertiser_sid, broadcast_id,
        BASSPASyncState.NOT_SYNCED, big_encryption, 1, subgroups)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, WildCard(), WildCard(),
        broadcaster_addr_type, broadcaster_addr, WildCard(),
        advertiser_sid=advertiser_sid,
        big_encryption=big_encryption,
        subgroups=subgroups,
        timeout=10, remove=False)

    if ev is None:
        log('Broadcast Receive State notification with expected fields not received.')
        return False

    log(f'Received Broadcast Receive State with Broadcast_Code required: {ev}')
    return True


def hdl_wid_20001(_: WIDParams):
    """Please prepare IUT into a connectable mode. Description: Verify
       that the Implementation Under Test (IUT) can accept GATT connect
        request from PTS.
    """
    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return True

    # The Unicast Server shall transmit connectable extended advertising PDUs
    # that contain the Service Data AD data type, including additional
    # service data defined in BAP_v1.0.1, 3.5.3, Table 3.7.
    ad = {
        AdType.name_full: stack.gap.name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: bytes.fromhex(UUID.ASCS)[::-1].hex(),
        AdType.uuid16_svc_data: '4e1801ff0fff0f00',
    }

    btp.gap_set_extended_advertising_on()
    btp.gap_adv_ind_on(ad=ad)

    return True
