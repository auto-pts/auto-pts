#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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

from autopts.ptsprojects.stack import WildCard, get_stack
from autopts.pybtp import btp
from autopts.pybtp.defs import AUDIO_METADATA_PROGRAM_INFO, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS
from autopts.pybtp.types import CODEC_CONFIG_SETTINGS, WIDParams, create_lc3_ltvs_bytes
from autopts.wid.bap import BAS_CONFIG_SETTINGS
from autopts.wid.common import _safe_bap_send

log = logging.debug


def hdl_wid_100(_: WIDParams):
    """Please synchronize with Broadcast ISO request."""

    stack = get_stack()

    btp.pbp.pbp_broadcast_scan_start()

    ev = stack.pbp.wait_public_broadcast_event_found_ev(WildCard(), WildCard(), WildCard(), 30, False)

    btp.pbp.pbp_broadcast_scan_stop()

    if ev is None:
        log('No advertisement with Public Broadcast Announcement and Broadcast Name found')
        return False

    log('Public Broadcast Announcement and Broadcast Name found')

    encrypted = (ev['pba_features'] & 1) != 0
    broadcast_id = ev['broadcast_id']
    addr_type = ev['addr_type']
    addr = ev['addr']

    if encrypted:
        stack = get_stack()
        broadcast_code = stack.bap.broadcast_code
        if isinstance(broadcast_code, str):
            # The default broadcast code string from PTS is in big endian
            broadcast_code = bytes.fromhex(broadcast_code)[::-1]

        # TODO set Broadcast code - BTstack BTP implementation uses default PTS broadcast code

    btp.bap_broadcast_sink_setup()

    btp.bap_broadcast_sink_sync(broadcast_id, ev['advertiser_sid'],
                                5, 100, False, 0, addr_type, addr)

    ev = stack.bap.wait_bis_found_ev(broadcast_id, 20, False)
    if ev is None:
        log(f'BIS not found for broadcast ID {broadcast_id}')
        return False

    log('BIS found')

    return True


def hdl_wid_104(_: WIDParams):
    """Please send non connectable advertise with periodic info."""

    # Periodic adv started within cap_broadcast_adv_start at hdl_wid_552.

    return True


def hdl_wid_353(_: WIDParams):
    """
    Wait for Broadcast ISO request.
    """

    return True


def hdl_wid_376(_: WIDParams):
    """
    Please confirm received streaming data..
    """

    # get Broadcast ID from Public Broadcast Announcement in WID 100
    stack = get_stack()
    ev = stack.pbp.wait_public_broadcast_event_found_ev(WildCard(), WildCard(), WildCard(), 30, False)
    broadcast_id = ev['broadcast_id']
    bis_id = 1

    ev = stack.bap.wait_bis_stream_received_ev(broadcast_id, bis_id, 20, False)
    if ev is None:
        log(f'BIS Stream receive failed for broadcast ID {broadcast_id}')
        return False

    return True


def hdl_wid_377(_: WIDParams):
    """
    Please confirm sent streaming data...
    """

    return True


def hdl_wid_551(params: WIDParams):
    """Please confirm that IUT received PBP Features value as 0x02"""

    # Search for the pattern in the input string
    match = re.search(r'0x[0-9A-Fa-f]+', params.description)

    # Extract and print the hex value
    if match:
        pba_features = int(match.group(), 16)
    else:
        log('Cannot find expected PBP Features')
        return False

    stack = get_stack()

    btp.pbp.pbp_broadcast_scan_start()

    ev = stack.pbp.wait_public_broadcast_event_found_ev(WildCard(), WildCard(), WildCard(), 30, False)

    btp.pbp.pbp_broadcast_scan_stop()

    if ev is None:
        log('No advertisement with Public Broadcast Announcement and Broadcast Name found')
        return False

    log(f"Public Broadcast Announcement with feature {ev['pba_features']} and Broadcast Name found")

    return ev['pba_features'] == pba_features


def hdl_wid_378(_: WIDParams):
    """
    Please confirm received BASE entry
    """

    # get Broadcast ID and Address from Public Broadcast Announcement in WID 100
    stack = get_stack()
    ev = stack.pbp.wait_public_broadcast_event_found_ev(WildCard(), WildCard(), WildCard(), 30, False)

    broadcast_id = ev['broadcast_id']
    addr_type = ev['addr_type']
    addr = ev['addr']

    bis_id = 1
    requested_bis_sync = 1
    btp.bap_broadcast_sink_bis_sync(broadcast_id, requested_bis_sync, addr_type, addr)

    ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 20, False)
    if ev is None:
        log(f'BIS Sync failed for broadcast ID {broadcast_id}, bis-id {bis_id}')
        return False

    log('BIS Synced')
    return True


wid_552_settings = {
    # test_case_name: features (1 - encrypted, 2 - std quality, 4 - high quality), bis, qos_name
    'PBP/PBS/STR/BV-01-C': (2, 1, '16_2_1'),
    'PBP/PBS/STR/BV-02-C': (4, 1, '48_1_1'),
    'PBP/PBS/STR/BV-03-C': (3, 1, '16_2_1'),
    'PBP/PBS/STR/BV-04-C': (5, 1, '48_1_1'),
    'PBP/PBS/STR/BV-05-C': (2, 2, '16_2_2'),
    'PBP/PBS/STR/BV-06-C': (2, 1, '24_2_1'),
    'PBP/PBS/STR/BV-07-C': (2, 2, '24_2_2'),
    'PBP/PBS/PBM/BV-01-C': (2, 1, '16_2_1'),
}


def hdl_wid_552(params: WIDParams):
    """
    Please advertise with Public Broadcast Announcement (0x1856) service data
    """

    features, bis_count, qos_set_name = wid_552_settings[params.test_case_name]

    # default PTS program info, see TSPX_Program_Info
    stack = get_stack()
    program_info = bytes.fromhex(stack.pbp.program_info)
    program_info_len = len(program_info)
    metadata = struct.pack('<BB', program_info_len + 1, AUDIO_METADATA_PROGRAM_INFO) + program_info

    btp.pbp.pbp_set_public_broadcast_announcement(features, metadata)
    btp.pbp.pbp_set_broadcast_name(stack.pbp.broadcast_name)

    metadata += struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)

    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    codec_set_name, *qos_config = BAS_CONFIG_SETTINGS[qos_set_name]

    (sampling_freq, frame_duration, octets_per_frame) = \
        CODEC_CONFIG_SETTINGS[codec_set_name]
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)

    source_id = 0x00
    subgroup_id = 0x00
    presentation_delay = 40000

    for _i in range(bis_count):
        btp.cap_broadcast_source_setup_stream(source_id, subgroup_id, coding_format, vid, cid,
                                              codec_ltvs_bytes, metadata)

    btp.cap_broadcast_source_setup_subgroup(source_id, subgroup_id, coding_format, vid, cid,
                                            codec_ltvs_bytes, metadata)

    # Due to no broadcast ID in the IXIT for PBP, any broadcast ID will work
    broadcast_id = 0x123456
    encrypted = False
    broadcast_code = None
    if (features & 1) != 0:
        encrypted = True
        broadcast_code = stack.bap.broadcast_code
        if isinstance(broadcast_code, str):
            # The default broadcast code string from PTS is in big endian
            broadcast_code = bytes.fromhex(broadcast_code)[::-1]

    btp.cap_broadcast_source_setup(source_id, broadcast_id, *qos_config, presentation_delay,
                                   encryption=encrypted, broadcast_code=broadcast_code,
                                   subgroup_codec_level=True)

    btp.cap_broadcast_adv_start(source_id)

    btp.cap_broadcast_source_start(source_id)

    data = bytearray([j for j in range(0, 41)])

    # PTS does not send an explicit message, but for each
    # configured SINK it expects to receive any ISO data.
    for _ in range(1, 10):
        _safe_bap_send(0, data)

    return True
