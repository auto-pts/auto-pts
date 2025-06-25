#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
# Copyright (c) 2025, Nordic Semiconductor ASA.
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
import struct
from argparse import Namespace

from autopts.ptsprojects.stack import WildCard, get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import (
    lt2_addr_get,
    lt2_addr_type_get,
    lt3_addr_get,
    lt3_addr_type_get,
    pts_addr_get,
    pts_addr_type_get,
)
from autopts.pybtp.btp.audio import pack_metadata
from autopts.pybtp.btp.cap import announcements
from autopts.pybtp.btp.gap import gap_set_uuid16_svc_data
from autopts.pybtp.btp.pacs import pacs_set_available_contexts
from autopts.pybtp.types import BASS_PA_INTERVAL_UNKNOWN, UUID, Addr, ASCSState, BAPAnnouncement, CAPAnnouncement, WIDParams
from autopts.wid.bap import (
    BAS_CONFIG_SETTINGS,
    CODEC_CONFIG_SETTINGS,
    QOS_CONFIG_SETTINGS,
    AudioDir,
    create_default_config,
    create_lc3_ltvs_bytes,
    get_audio_locations_from_pac,
)
from autopts.wid.common import _safe_bap_send

log = logging.debug


def hdl_wid_100(params: WIDParams):
    """
    Please synchronize with Broadcast ISO request
    """
    if params.test_case_name.endswith('LT3'):
        addr = lt3_addr_get()
        addr_type = lt3_addr_type_get()
    elif params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
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

    return True


def hdl_wid_104(_: WIDParams):
    """Please send non-connectable advertise with periodic info."""

    # Periodic adv started within cap_broadcast_adv_start at hdl_wid_114.

    return True


wid_114_settings = {
    # test_case_name: (source_num, metadata)
    "CAP/INI/BST/BV-01-C": (1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-02-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-03-C": (1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-04-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-05-C": (1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-06-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-07-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/BST/BV-08-C": (1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-09-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-10-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/BST/BV-11-C": (1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-12-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-13-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-14-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-15-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/BST/BV-16-C": (1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BST/BV-17-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UTB/BV-01-C": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UTB/BV-01-C_LT2": (2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UTB/BV-02-C": (2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-02-C_LT2": (2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-03-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-03-C_LT2": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-04-C": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UTB/BV-04-C_LT2": (2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/BTU/BV-01-C": (1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BTU/BV-02-C": (1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
}


def hdl_wid_114(params: WIDParams):
    """Please advertise with Broadcast Audio Announcement (0x1852) service data"""

    stack = get_stack()

    source_num, metadata = wid_114_settings[params.test_case_name]
    qos_set_name = "16_2_1"
    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    codec_set_name, *qos_config = BAS_CONFIG_SETTINGS[qos_set_name]

    (sampling_freq, frame_duration, octets_per_frame) = CODEC_CONFIG_SETTINGS[codec_set_name]
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration, audio_locations, octets_per_frame, frames_per_sdu)

    source_id = 0x00
    subgroup_id = 0x00
    presentation_delay = 40000

    for _i in range(source_num):
        btp.cap_broadcast_source_setup_stream(source_id, subgroup_id, coding_format, vid, cid, codec_ltvs_bytes, metadata)

    btp.cap_broadcast_source_setup_subgroup(source_id, subgroup_id, coding_format, vid, cid, codec_ltvs_bytes, metadata)

    btp.cap_broadcast_source_setup(
        source_id,
        stack.cap.local_broadcast_id,
        *qos_config,
        presentation_delay,
        encryption=False,
        broadcast_code=None,
        subgroup_codec_level=False,
    )

    btp.cap_broadcast_adv_start(source_id)

    btp.cap_broadcast_source_start(source_id)

    data = bytearray([j for j in range(0, 41)])

    # PTS does not send an explicit message, but for each
    # configured SINK it expects to receive any ISO data.
    for _ in range(1, 10):
        _safe_bap_send(0, data)

    return True


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
        return ev is not None

    return False


wid_310_settings = {
    "CAP/INI/UST/BV-32-C": pack_metadata(stream_context=0x0200),
    "CAP/INI/UST/BV-33-C": pack_metadata(stream_context=0x0200),
    "CAP/INI/UST/BV-34-C": pack_metadata(stream_context=0x0200, ccid_list=[0x00]),
    "CAP/INI/UST/BV-35-C": pack_metadata(stream_context=0x0200, ccid_list=[0x00]),
    "CAP/INI/UST/BV-36-C": pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01]),
    "CAP/INI/UST/BV-37-C": pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01]),
}


def hdl_wid_309(params: WIDParams):
    """ Please configure ASE state to Releasing state. """
    if params.test_case_name.endswith('LT2'):
        return True

    cig_id = 0x00
    btp.cap_unicast_audio_stop(cig_id, True)

    stack = get_stack()
    ev = stack.cap.wait_unicast_stop_completed_ev(cig_id, 20)
    if ev is None:
        return False

    return True


def hdl_wid_310(params: WIDParams):
    """Please send Update Metadata Opcode with valid data."""

    if params.test_case_name.endswith('LT2'):
        return True

    stack = get_stack()
    metadata = wid_310_settings[params.test_case_name]
    update_metadata = [
        (config.addr_type, config.addr, config.ase_id, metadata)
        for config in stack.bap.ase_configs
    ]

    btp.cap_unicast_audio_update(update_metadata)

    return True


def hdl_wid_312(params: WIDParams):
    """Please configure ASE state to Disable"""
    if params.test_case_name.endswith('LT2'):
        return True

    cig_id = 0x00
    btp.cap_unicast_audio_stop(cig_id, False)

    stack = get_stack()
    ev = stack.cap.wait_unicast_stop_completed_ev(cig_id, 20)
    if ev is None:
        return False

    return True


def hdl_wid_345(params: WIDParams):
    """Please ADD Broadcast Source to Lower Tester with PA SYNC with PAST(01) or No PAST(02), BIS INDEX: 0x00000001"""
    stack = get_stack()

    # get pts address and lt1 test name
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    test_name = params.test_case_name.removesuffix("_LT2")

    # get broadcaster address
    if test_name.startswith("CAP/INI/UTB/BV-") or test_name.startswith("CAP/INI/BTU/BV-"):
        if not params.test_case_name.endswith("LT2"):
            # Use hdl_wid_114 to setup broadcast source. hdl_wid_345 will be called later to handle transferring the
            # broadcast information to the lower testers.
            hdl_wid_114(params)

        # IUT is Broadcaster
        broadcaster_addr = stack.gap.iut_addr_get_str()
        broadcaster_addr_type = Addr.le_random if stack.gap.iut_addr_is_random() else Addr.le_public
        # TODO: hard-coded in BTstack BTP Client - There is no way with existing commands and events to know or control this.
        advertiser_sid = 0
        # Since we don't know the interval used by the IUT we need to use this.
        # The IUT may determine to replace this value with the actual value when sending the request to the lower testers
        padv_interval = BASS_PA_INTERVAL_UNKNOWN
        broadcast_id = stack.cap.local_broadcast_id
    else:
        # A Lower Tester is Broadcaster
        if test_name in ["CAP/COM/BST/BV-01-C", "CAP/COM/BST/BV-02-C", "CAP/COM/BST/BV-06-C"]:
            broadcaster_addr = lt3_addr_get()
            broadcaster_addr_type = lt3_addr_type_get()
        else:
            broadcaster_addr = lt2_addr_get()
            broadcaster_addr_type = lt2_addr_type_get()

        log(f"Wait for BAA for {broadcaster_addr}")
        ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
        if ev is None:
            log('No BAA found')
            return False

        base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
        if base_found_ev is None:
            log('No base found')
            return False

        advertiser_sid = ev['advertiser_sid']
        broadcast_id = ev['broadcast_id']
        padv_interval = ev['padv_interval']

    padv_sync = 0x02
    num_subgroups = 1
    bis_sync = 1
    result = re.search(r'BIS INDEX: 0x(\d+)', params.description)
    if result:
        bis_sync = int(result.group(1), 16)
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), timeout=10, remove=True)

    if ev is None:
        log('No broadcast receive state event 1')
        return False

    # We get 2 Broadcast Receive State updates: one to ack the sync process and one that sync was achieved.

    # Issue: On PTS 8.5.3, if we send a new command before the second was received, it will be ignored
    # Fix: Wait for second update
    # note: it would be better to wait for PA SYNC == 0x02 with BIS SYNC = 1
    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), timeout=10, remove=True)

    if ev is None:
        log('No broadcast receive state event 2')
        return False

    # handle BIG Encryption
    if ev['big_encryption'] == 1:
        log("BIG Encryption, set Broadcast code")
        source_id = (ev['src_id'])
        # broadcast code from TSPX_broadcast_code in ptsproject/x/cap.py
        broadcast_code = "0102680553F1415AA265BBAFC6EA03B8"
        btp.bap_set_broadcast_code(source_id, broadcast_code, addr_type, addr)

        # wait for BIS sync
        stack.bap.wait_broadcast_receive_state_ev(
            broadcast_id, addr_type, addr, broadcaster_addr_type,
            broadcaster_addr, WildCard(), timeout=10, remove=True)

    return True


def hdl_wid_347(params: WIDParams):
    """1. Please ADD Broadcast Source from Lower Tester 2 to
          Lower Tester 1 with PA SYNC: 0x00, BIS INDEX: 0x00000000
       2. After that, please REMOVE Broadcast Source.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    broadcaster_addr = lt2_addr_get()
    broadcaster_addr_type = lt2_addr_type_get()

    ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
    if ev is None:
        log('No BAA found')
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        log('No base found')
        return False

    broadcast_id = ev['broadcast_id']

    # stop sync to free resources on Controller
    btp.bap_broadcast_sink_stop(broadcast_id, addr_type, addr)

    advertiser_sid = ev['advertiser_sid']
    padv_interval = ev['padv_interval']
    num_subgroups = 1
    padv_sync = 0x02
    bis_sync = 1
    result = re.search(r'BIS INDEX: 0x(\d+)', params.description)
    if result:
        bis_sync = int(result.group(1), 16)
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), timeout=10, remove=True)

    if ev is None:
        log('No broadcast receive state event 1')
        return False

    # We get 2 Broadcast Receive State updates: one to ack the sync process and one that sync was achieved.

    # Issue: On PTS 8.5.3, if we send a new command before the second was received, it will be ignored
    # Fix: Wait for second update
    # note: it would be better to wait for PA SYNC == 0x02 with BIS SYNC = 1
    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), timeout=10, remove=True)

    # stop sync with Modify Source
    padv_sync = 0x0
    bis_sync = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    source_id = (ev['src_id'])
    btp.bap_modify_broadcast_src(source_id, padv_sync, padv_interval, num_subgroups, subgroups, addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, padv_sync, timeout=10, remove=False)

    if ev is None:
        log('No broadcast receive state event 3')
        return False

    # then remove it with Remove Source
    btp.bap_remove_broadcast_src(ev['src_id'], addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, padv_sync, timeout=10, remove=False)

    if ev is None:
        log('No broadcast receive state event 4')
        return False

    return True


def hdl_wid_353(params: WIDParams):
    """Wait for Broadcast ISO request."""

    return True


def hdl_wid_357(_: WIDParams):
    """Please terminate BIG."""
    # Only one source supported for now
    source_id = 0x00
    btp.cap_broadcast_adv_stop(source_id)
    btp.cap_broadcast_source_stop(source_id)

    return True


def hdl_wid_376(params: WIDParams):
    """
    Please confirm received streaming data.
    """

    stack = get_stack()

    if params.test_case_name in ['CAP/COM/BST/BV-01-C_LT3',
                                 'CAP/COM/BST/BV-02-C_LT3',
                                 'CAP/COM/BST/BV-03-C_LT2',
                                 'CAP/COM/BST/BV-04-C_LT2',
                                 'CAP/COM/BST/BV-06-C_LT3'
                                 ]:
        # Confirm that LT1 & LT2 received stream from LT3 ...
        # Pending errata.

        return True

    return False


def hdl_wid_377(_: WIDParams):
    """Please confirm sent streaming data"""
    return True


def hdl_wid_384(_: WIDParams):
    """
    Click OK will start transmitting audio streaming data.
    """

    return True


wid_400_settings = {
    # test_case_name: (sink_num, source_num, LT_count, metadata)
    # Two Lower Testers, unidirectional
    "CAP/INI/UST/BV-01-C": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-02-C": (0, 1, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-03-C": (1, 0, 2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UST/BV-04-C": (0, 1, 2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UST/BV-05-C": (1, 0, 2, pack_metadata(stream_context=0x0002, ccid_list=[0x00])),
    "CAP/INI/UST/BV-06-C": (0, 1, 2, pack_metadata(stream_context=0x0002, ccid_list=[0x00])),
    "CAP/INI/UST/BV-07-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-08-C": (0, 1, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-09-C": (1, 0, 2, pack_metadata(stream_context=0x0080, ccid_list=[0x00])),
    "CAP/INI/UST/BV-10-C": (0, 1, 2, pack_metadata(stream_context=0x0080, ccid_list=[0x00])),
    "CAP/INI/UST/BV-11-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-12-C": (0, 1, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-13-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UST/BV-14-C": (0, 1, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    # Single LT, unidirectional
    "CAP/INI/UST/BV-15-C": (2, 0, 1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-16-C": (0, 2, 1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-17-C": (2, 0, 1, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UST/BV-18-C": (0, 2, 1, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UST/BV-19-C": (2, 0, 1, pack_metadata(stream_context=0x0002, ccid_list=[0x00])),
    "CAP/INI/UST/BV-20-C": (0, 2, 1, pack_metadata(stream_context=0x0002, ccid_list=[0x00])),
    "CAP/INI/UST/BV-21-C": (2, 0, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-22-C": (0, 2, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-23-C": (2, 0, 1, pack_metadata(stream_context=0x0080, ccid_list=[0x00])),
    "CAP/INI/UST/BV-24-C": (0, 2, 1, pack_metadata(stream_context=0x0080, ccid_list=[0x00])),
    "CAP/INI/UST/BV-25-C": (2, 0, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-26-C": (0, 2, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-27-C": (2, 0, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UST/BV-28-C": (0, 2, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    # Two LTs, one CIS bidirectional, the other CIS unidirectional
    "CAP/INI/UST/BV-29-C": (1, 1, 2, pack_metadata(stream_context=0x0007)),
    "CAP/INI/UST/BV-29-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0007)),
    "CAP/INI/UST/BV-30-C": (1, 1, 2, pack_metadata(stream_context=0x0007, ccid_list=[0x00])),
    "CAP/INI/UST/BV-30-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0007, ccid_list=[0x00])),
    "CAP/INI/UST/BV-31-C": (1, 1, 2, pack_metadata(stream_context=0x0007, ccid_list=[0x00, 0x01])),
    "CAP/INI/UST/BV-31-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0007, ccid_list=[0x00, 0x01])),
    # Two LTs, unidirectional
    "CAP/INI/UST/BV-32-C": (0, 1, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-33-C": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-34-C": (0, 1, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-35-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UST/BV-36-C": (0, 1, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UST/BV-37-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UST/BV-40-C": (0, 1, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-41-C": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-42-C": (1, 1, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UST/BV-42-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    # Two Lower Testers, unidirectional
    "CAP/INI/UTB/BV-01-C": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UTB/BV-01-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0200)),
    "CAP/INI/UTB/BV-02-C": (1, 0, 2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-02-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0004, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-03-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-03-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
    "CAP/INI/UTB/BV-04-C": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    "CAP/INI/UTB/BV-04-C_LT2": (1, 0, 2, pack_metadata(stream_context=0x0200, ccid_list=[0x00, 0x01])),
    # Single LT, unidirectional
    "CAP/INI/BTU/BV-01-C": (1, 0, 1, pack_metadata(stream_context=0x0200)),
    "CAP/INI/BTU/BV-02-C": (1, 0, 1, pack_metadata(stream_context=0x0200, ccid_list=[0x00])),
}


def hdl_wid_400(params: WIDParams):
    """
        Please configure to Enabling or Streaming state.
    """
    stack = get_stack()

    if params.test_case_name.endswith('LT2'):
        log('hdl_wid_400 started for LT2')
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
        if params.test_case_name in wid_400_settings:
            settings_name = params.test_case_name
        else:
            settings_name = params.test_case_name[:-len('_LT2')]

        # This WID for LT2 is synchronized to arrived as a second one.
        # All CISes in a CIG shall have different CIS_ID, so let's keep
        # the increasing order to assure this.
        cis_id = stack.bap.ase_configs[-1].cis_id + 1
    else:
        log('hdl_wid_400 started for LT1')
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()
        settings_name = params.test_case_name
        cis_id = 0x00

    default_config = create_default_config()
    default_config.qos_set_name = '16_2_1'

    sink_num, source_num, lt_count, metadata = wid_400_settings[settings_name]

    default_config.codec_set_name = '_'.join(default_config.qos_set_name.split('_')[:-1])
    default_config.addr = addr
    default_config.addr_type = addr_type
    default_config.metadata_ltvs = metadata

    (default_config.sampling_freq,
     default_config.frame_duration,
     default_config.octets_per_frame) = CODEC_CONFIG_SETTINGS[default_config.codec_set_name]

    (default_config.sdu_interval,
     default_config.framing,
     default_config.max_sdu_size,
     default_config.retransmission_number,
     default_config.max_transport_latency) = QOS_CONFIG_SETTINGS[default_config.qos_set_name]

    sinks = []
    for _i in range(0, sink_num):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SINK
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)

        if not config.audio_locations:
            log('hdl_wid_400 exit, no suitable sink audio locations')
            return False

        sinks.append(config)

    sources = []
    for _i in range(0, source_num):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SOURCE
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)

        if not config.audio_locations:
            log('hdl_wid_400 exit, no suitable source audio locations')
            return False

        sources.append(config)

    ase_found_ev_cache = []
    ases = sinks + sources
    for config in ases:
        ev = stack.bap.wait_ase_found_ev(default_config.addr_type,
                                         default_config.addr,
                                         config.audio_dir, 30, remove=True)
        if ev is None:
            log('hdl_wid_400 exit, no suitable ase found')
            return False

        ase_found_ev_cache.append(ev)

        _, _, audio_dir, ase_id = ev
        config.ase_id = ase_id
        config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                  config.frame_duration,
                                                  config.audio_locations,
                                                  config.octets_per_frame,
                                                  config.frames_per_sdu)

    bidir_cises = list(zip(sinks, sources))
    bidir_cises_num = len(bidir_cises)

    for sink_config, source_config in bidir_cises:
        sink_config.cis_id = cis_id
        source_config.cis_id = cis_id
        cis_id += 1

    unidir_cises = []
    for sink_config in sinks[bidir_cises_num:]:
        sink_config.cis_id = cis_id
        unidir_cises.append((sink_config, None))
        cis_id += 1

    for source_config in sources[bidir_cises_num:]:
        source_config.cis_id = cis_id
        unidir_cises.append((None, source_config))
        cis_id += 1

    cig_id = 0x00
    for config in ases:
        config.cig_id = cig_id
        btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
        stack.bap.ase_configs.append(config)

    if lt_count == 1 or (lt_count == 2 and params.test_case_name.endswith('LT2')) or \
                        (lt_count == 3 and params.test_case_name.endswith('LT3')):
        # Zephyr CAP API starts all streams in group at once
        btp.cap_unicast_audio_start(cig_id, defs.CAP_UNICAST_AUDIO_START_SET_TYPE_AD_HOC)
        ev = stack.cap.wait_unicast_start_completed_ev(cig_id, 10)
        if ev is None:
            return False

        # We could wait for this, but Zephyr controller has issue with the second CIS,
        # so PTS does not send Streaming notification.
        for config in ases:
            # Wait for the ASE states to be changed to streaming
            ev = stack.ascs.wait_ascs_ase_state_changed_ev(config.addr_type,
                                                           config.addr,
                                                           config.ase_id,
                                                           ASCSState.STREAMING,
                                                           20)
            if ev is None:
                log('hdl_wid_400 exit, not streaming')
                return False

    return True


def hdl_wid_402(_: WIDParams):
    """
        Click OK will initiate release operation
    """

    return True


def hdl_wid_404(_: WIDParams):
    """
        Please wait to establish 2 connections. After that, Click OK to send notification.
    """

    return True


def hdl_wid_405(params: WIDParams):
    """
        Please read lock characteristic.
    """
    if params.test_case_name.endswith('LT2'):
        # Ordered Access Operation reads locks of all members
        return True

    btp.csip_start_ordered_access()

    return True


def hdl_wid_406(params: WIDParams):
    """
        Please perform Unicast Audio Ending procedure,
        and initiate Broadcast Audio Reception Start
        procedure for Unicast Handover procedure.
    """

    # Stop Unicast

    if params.test_case_name.endswith('LT2'):
        return True

    cig_id = 0x00
    btp.cap_unicast_audio_stop(cig_id, True)

    stack = get_stack()
    ev = stack.cap.wait_unicast_stop_completed_ev(cig_id, 20)
    if ev is None:
        log("hdl_wid_406 exit, unicast stop event not received")
        return False

    # hdl_wid_345 will be used to start the broadcast source and broadcast audio reception

    return True


def hdl_wid_408(params: WIDParams):
    """Please write Mute Characteristic."""

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
        lt1_test_name = params.test_case_name.replace('_LT2', '')
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()
        lt1_test_name = params.test_case_name

    btp.micp_mute(addr_type, addr)

    return True


def hdl_wid_409(_: WIDParams):
    """Please update metadata in BASE. Then click OK when IUT is ready
       to advertise with new BASE information"""

    source_id = 0x00
    metadata = pack_metadata(stream_context=0x0004, ccid_list=[0x00])

    btp.cap_broadcast_adv_stop(source_id)

    btp.cap_broadcast_source_update(source_id, metadata)

    btp.cap_broadcast_adv_start(source_id)

    return True


update_settings = {
    "CAP/INI/BST/BV-13-C": pack_metadata(stream_context=0x0200, ccid_list=[0x00]),
    "CAP/INI/BST/BV-14-C": pack_metadata(stream_context=0x0200, ccid_list=[0x01]),
    "CAP/INI/BST/BV-15-C": pack_metadata(stream_context=0x0200),
}


def hdl_wid_410(params: WIDParams):
    """Please add CCID in BASE. Then click OK when IUT is ready to advertise with new BASE information"""
    source_id = 0x00
    metadata = update_settings[params.test_case_name]

    btp.cap_broadcast_adv_stop(source_id)

    btp.cap_broadcast_source_update(source_id, metadata)

    btp.cap_broadcast_adv_start(source_id)

    return True


def hdl_wid_411(params: WIDParams):
    """Please remove CCID in BASE. Then click OK when IUT is ready to advertise with new BASE information"""

    return hdl_wid_410(params)


def hdl_wid_412(params: WIDParams):
    """Please change CCID values in BASE. Then click OK when IUT is ready to advertise with new BASE information"""

    return hdl_wid_410(params)


def hdl_wid_413(params: WIDParams):
    """Please remove source."""

    stack = get_stack()

    # IUT is Broadcaster
    broadcaster_addr = stack.gap.iut_addr_get_str()
    broadcaster_addr_type = Addr.le_random if stack.gap.iut_addr_is_random() else Addr.le_public
    broadcast_id = stack.cap.local_broadcast_id

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    # first stop sync with Modify Source
    pa_sync = 0x0
    bis_sync = 0
    metadata_len = 0
    num_subgroups = 1
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    # TODO: get src_id from Broadcast Add Source
    source_id = 1
    # Since we don't know the interval used by the IUT we need to use this.
    # The IUT may determine to replace this value with the actual value when sending the request to the lower testers
    padv_interval = BASS_PA_INTERVAL_UNKNOWN
    btp.bap_modify_broadcast_src(source_id, pa_sync, padv_interval, num_subgroups, subgroups, addr_type, addr)

    pa_sync_state = 0x0
    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, pa_sync_state, timeout=10, remove=True)

    if ev is None:
        log('No broadcast receive state event 1')
        return False

    # then remove it with Remove Source
    btp.bap_remove_broadcast_src(source_id, addr_type, addr)

    # stop IUT Broadcaster
    source_id = 0
    btp.cap_broadcast_adv_stop(source_id)
    btp.cap_broadcast_source_stop(source_id)

    return True


def hdl_wid_414(params: WIDParams):
    """Please click OK when IUT received notification."""
    stack = get_stack()

    # get pts address and lt1 test name
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    # IUT is Broadcaster
    broadcaster_addr = stack.gap.iut_addr_get_str()
    broadcaster_addr_type = Addr.le_random if stack.gap.iut_addr_is_random() else Addr.le_public
    broadcast_id = stack.cap.local_broadcast_id

    padv_sync = 0x02
    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, padv_sync, timeout=10, remove=False)

    if ev is None:
        log('No broadcast receive state event 4')
        return False

    return True


def hdl_wid_415(_: WIDParams):
    """
        Please stop broadcast, and wait for 10 seconds.
    """
    btp.gap_adv_off()

    # PTS waits 10 seconds on its own before sending next wid 416.

    return True


def hdl_wid_416(_: WIDParams):
    """
        Please start broadcast.
    """
    stack = get_stack()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_418(_: WIDParams):
    """
       Please confirm the other tester successfully added broadcast source.
    """
    return True


def hdl_wid_419(params: WIDParams):
    """
        Please configure to Streaming state.
    """
    return hdl_wid_400(params)


def hdl_wid_420(params: WIDParams):
    """
        Please put the IUT in Non-Bondable mode.
    """
    btp.gap_set_bondable_off()

    return True


def hdl_wid_421(params: WIDParams):
    """
        Please make sure the IUT is a BAP Unicast Server that is in an Idle state
    """
    adv_data, rsp_data = {}, {}

    # Set available contexts to 0
    gap_set_uuid16_svc_data(adv_data, UUID.CAS, struct.pack('<B', CAPAnnouncement.TARGETED))
    gap_set_uuid16_svc_data(adv_data, UUID.ASCS, struct.pack('<BHHB', BAPAnnouncement.TARGETED, 0, 0, 0))

    announcements(adv_data)
    btp.gap_adv_ind_on(ad=adv_data, sd=rsp_data)

    # Set available contexts to 0
    pacs_set_available_contexts(0, 0)

    return True


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    return True


def hdl_wid_20100(params: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    btp.gap_conn(addr, addr_type)
    stack.gap.wait_for_connection(timeout=5, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30, addr=addr)

    btp.cap_discover(addr_type, addr)
    stack.cap.wait_discovery_completed_ev(addr_type, addr, 30)

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    if params.test_case_name.removesuffix("_LT2") in ["CAP/COM/CRC/BV-07-C", "CAP/COM/CRC/BV-08-C", "CAP/COM/CRC/BV-09-C"]:
        btp.micp_discover(addr_type, addr)
        stack.micp.wait_discovery_completed_ev(addr_type, addr, 10)

    if params.test_case_name.removesuffix("_LT2") in [
        "CAP/COM/CRC/BV-01-C",
        "CAP/COM/CRC/BV-03-C",
        "CAP/COM/CRC/BV-04-C",
        "CAP/COM/CRC/BV-05-C",
        "CAP/COM/CRC/BV-06-C",
    ]:
        btp.vcp_discover(addr_type, addr)
        stack.vcp.wait_discovery_completed_ev(addr_type, addr, 10)

    # Discover BASS on CAP tests that need it (CAP Commander for broadcast and CAP Handover)
    if (
        params.test_case_name.startswith("CAP/INI/UTB")
        or params.test_case_name.startswith("CAP/INI/BTU")
        or params.test_case_name.startswith("CAP/COM/BST")
    ):
        btp.bap_discover_scan_delegator(addr_type, addr)
        ev = stack.bap.wait_scan_delegator_found_ev(addr_type, addr, 10)
        if ev is None:
            return False

    return True


def hdl_wid_20101(_: WIDParams):
    """
        Please send discover primary services command to the PTS.
    """
    return True


def hdl_wid_20106(_: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor
    of ASE Control Point characteristic to enable notification.

    or

    Please write to Client Characteristic Configuration Descriptor
    of Broadcast Receive State characteristic to enable notification.
    """

    # IUTs are expected to subscribe to notifications when discovering in hdl_wid_20100

    return True


def hdl_wid_20110(params: WIDParams):
    """
        Please send write request to handle 0x016A with following value.
        Volume Control Point:
            Op Code: [? (0x0?)] ?
            Change Counter: <WildCard: Exists
        """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
        lt1_test_name = params.test_case_name.replace('_LT2', '')
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()
        lt1_test_name = params.test_case_name

    stack = get_stack()

    if lt1_test_name == 'CAP/COM/CRC/BV-01-C':
        btp.vcp_set_vol(50, addr_type, addr)
        stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
    if lt1_test_name == 'CAP/COM/CRC/BV-03-C':
        btp.vcp_unmute(addr_type, addr)
        stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
    if lt1_test_name == 'CAP/COM/CRC/BV-04-C':
        btp.vcp_mute(addr_type, addr)
        stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
    if lt1_test_name == 'CAP/COM/CRC/BV-05-C':
        btp.vcp_set_vol(13, addr_type, addr)
        stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
    if lt1_test_name == 'CAP/COM/CRC/BV-06-C':
        btp.vcp_mute(addr_type, addr)
        stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
    if lt1_test_name == 'CAP/COM/CRC/BV-09-C':
        btp.aics_set_gain(42, addr_type, addr)
        stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True


def hdl_wid_20115(params: WIDParams):
    """
        Please initiate a GATT disconnection to the PTS.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.gap_disconn(addr, addr_type)

    return True


def hdl_wid_20200(_: WIDParams):
    """
        Please confirm the following handles for Common Audio.
        Start Handle: 0x0190	 End Handle: 0x0191
    """

    return True
