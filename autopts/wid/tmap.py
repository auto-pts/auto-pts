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
import re
import struct
from argparse import Namespace

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp, defs
from autopts.pybtp.btp.btp import lt2_addr_get, lt2_addr_type_get, pts_addr_get, pts_addr_type_get
from autopts.pybtp.defs import AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS
from autopts.pybtp.types import (
    CODEC_CONFIG_SETTINGS,
    QOS_CONFIG_SETTINGS,
    ASCSState,
    AudioDir,
    WIDParams,
    create_lc3_ltvs_bytes,
)
from autopts.wid.bap import BAS_CONFIG_SETTINGS, create_default_config, get_audio_locations_from_pac
from autopts.wid.ccp import BT_TBS_GTBS_INDEX
from autopts.wid.common import _safe_bap_send

log = logging.debug


def trigger_discovery_if_needed(params):
    # get peer addr
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    peer = stack.bap.get_peer(addr_type, addr)
    if not peer.discovery_completed:
        # CAP discover includes CSIP
        btp.cap_discover(addr_type, addr)
        stack.cap.wait_discovery_completed_ev(addr_type, addr, 30)

        btp.bap_discover(addr_type, addr)
        stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

        btp.vcp_discover(addr_type, addr)
        stack.vcp.wait_discovery_completed_ev(addr_type, addr, 10)


def tmap_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
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


def hdl_wid_104(_: WIDParams):
    """Please send non-connectable advertise with periodic info."""

    # Periodic adv started within cap_broadcast_adv_start at hdl_wid_114.

    return True


def hdl_wid_114(params: WIDParams):
    """Please advertise with Broadcast Audio Announcement (0x1852) service data"""

    # advertisement started in hdl_wid_506

    return True


wid_311_settings = {
    # lt_count, num sink ASEs, sink locations (0 - don't care), num source ASEs, QoS Set Name
    'TMAP/UMS/VRC/BV-01-I':     (1, 2, 0, 0, '48_2_1'),
    'TMAP/UMS/VRC/BV-02-I':     (2, 1, 0, 0, '48_2_1'),
    'TMAP/UMS/VRC/BV-02-I_LT2': (2, 1, 0, 0, '48_2_1'),
    'TMAP/UMS/VRC/BV-03-I':     (1, 2, 0, 0, '48_2_1'),
    'TMAP/UMS/ASC/BV-01-I':     (1, 1, 1, 0, '48_2_1'),
    'TMAP/UMS/ASC/BV-02-I':     (1, 1, 2, 0, '48_2_1'),
    'TMAP/UMS/ASC/BV-03-I':     (1, 1, 3, 0, '48_2_1'),
}


def hdl_wid_311(params: WIDParams):
    """Please configure 2 SINK ASE with Config Setting: 48_2_1."""

    # Based on cap/wid_400
    stack = get_stack()
    if params.test_case_name.endswith('LT2'):
        log('hdl_wid_311 started for LT2')
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
        settings_name = params.test_case_name
        # This WID for LT2 is synchronized to arrived as a second one.
        # All CISes in a CIG shall have different CIS_ID, so let's keep
        # the increasing order to assure this.
        cis_id = stack.bap.ase_configs[-1].cis_id + 1
    else:
        log('hdl_wid_311 started for LT1')
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()
        settings_name = params.test_case_name
        cis_id = 0x00

    lt_count, num_sink_ases, sink_locations, num_source_ases, qos_set_name = \
        wid_311_settings[settings_name]

    log(
        f"Looking for {lt_count} LTs, num Sink ASEs {num_sink_ases}, Sink locations {sink_locations}, "
        f"num Source ASEs {num_source_ases}, QoS Config {qos_set_name}"
    )

    metadata = b''
    default_config = create_default_config()
    default_config.qos_set_name = qos_set_name

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
    for i in range(0, num_sink_ases):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SINK
        config.max_sdu_size = default_config.max_sdu_size

        if sink_locations != 0:
            config.audio_locations = sink_locations
            log("Use Sink Locations %u from Test Specification", config.audio_locations)
        else:
            config.audio_locations = get_audio_locations_from_pac(
                default_config.addr_type, default_config.addr, config.audio_dir)
            log("Use Sink Locations %u from PACS Sink Record", config.audio_locations)

        if not config.audio_locations:
            log('hdl_wid_311 exit, no suitable sink audio locations')
            return False

        sinks.append(config)

    sources = []
    for i in range(0, num_source_ases):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SOURCE
        config.max_sdu_size = default_config.max_sdu_size
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)

        if not config.audio_locations:
            log('hdl_wid_311 exit, no suitable source audio locations')
            return False

        sources.append(config)

    ase_found_ev_cache = []
    ases = sinks + sources
    for config in ases:
        ev = stack.bap.wait_ase_found_ev(default_config.addr_type,
                                         default_config.addr,
                                         config.audio_dir, 30, remove=True)
        if ev is None:
            log('hdl_wid_311 exit, no suitable ase found')
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
                log('hdl_wid_311 exit, not streaming')
                return False

    return True


def hdl_wid_364(_: WIDParams):
    """
    After processed audio stream data, please click OK.
    """

    return True


def hdl_wid_367(_: WIDParams):
    """
    Lower tester is streaming audio data.
    """
    return True


def hdl_wid_376(_: WIDParams):
    """
    Please confirm received streaming data.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    for ev in stack.bap.event_queues[defs.BTP_BAP_EV_ASE_FOUND]:
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


def hdl_wid_500(_: WIDParams):
    """Please click ok when the tester is ready to
    discover Generic Telephone Bearer Service"""
    return True


def hdl_wid_501(params: WIDParams):
    """Please discover Generic Telephone Bearer Service and
    click ok when the tester is ready to start CAP
    Unicast Audio Starting procedure"""

    # get peer addr
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.ccp_discover_tbs(addr_type, addr)
    btp.ccp.ccp_await_discovered(30000)

    return True


def hdl_wid_502(params: WIDParams):
    """
        Please order IUT to receive an incoming call, accepts and establishes the call with
        confirmation from the Upper Tester
    """

    if params.test_case_name.endswith('LT2'):
        return True

    btp.tbs_remote_incoming(0, 'tel:+19991111234', 'tel:+19991111235',
                            'tel:+19991110011')

    return True


def hdl_wid_503(params: WIDParams):
    """
        Please order IUT to hang up the call
    """

    if params.test_case_name.endswith('LT2'):
        return True

    btp.tbs_terminate_call(1)

    return True


wid_504_settings = {
    # test_case_name: (lt count, iut as audio source: streams + channels,
    # sink locations (0 - don't care), iut as audio sink streams, metadata)
    'TMAP/CG/VRC/BV-01-C': (1, 1, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-05-C': (1, 2, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-06-C': (1, 1, 2, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-07-C': (1, 1, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-08-C': (1, 2, 1, 0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-11-C': (1, 2, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-12-C': (1, 2, 1, 0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/ASC/BV-01-C': (1, 1, 1, 1, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/ASC/BV-02-C': (1, 1, 1, 2, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/ASC/BV-03-C': (1, 1, 1, 3, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),

    # According to TMAP.TS.p1 LT1 provides audio source and
    # LT2 provides audio sink, however, PTS 8.5.3 seem to have this the other way round
    'TMAP/CG/VRC/BV-02-C':     (2, 1, 1, 0, 0, 0, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-02-C_LT2': (2, 0, 0, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-03-C':     (2, 1, 1, 0, 0, 0, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-03-C_LT2': (2, 1, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-09-C':     (2, 1, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'TMAP/CG/VRC/BV-09-C_LT2': (2, 1, 1, 0, 1, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),

}


def hdl_wid_504(params: WIDParams):
    """
        Please configure to Streaming state by starting the CAP Unicast Audio Start Procedure.
        In order to start the CAP Unicast Audio Start Procedure, the IUT may simulate/receive an incoming call,
        accepts and establishes the call with confirmation from the Upper Tester.
    """

    # Based on cap/wid_400
    stack = get_stack()
    if params.test_case_name.endswith('LT2'):
        log('hdl_wid_504 started for LT2')
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
        settings_name = params.test_case_name
        # This WID for LT2 is synchronized to arrived as a second one.
        # All CISes in a CIG shall have different CIS_ID, so let's keep
        # the increasing order to assure this.
        cis_id = stack.bap.ase_configs[-1].cis_id + 1
    else:
        log('hdl_wid_504 started for LT1')
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()
        settings_name = params.test_case_name
        cis_id = 0x00

    default_config = create_default_config()
    default_config.qos_set_name = '16_2_1'

    lt_count, iut_source_streams, iut_source_channels, pts_sink_locations, \
        iut_sink_streams, iut_sink_channels, metadata = wid_504_settings[settings_name]

    log(
        f"Look for {iut_sink_streams} Source ASEs ({iut_sink_channels} channels) and "
        f"{iut_source_streams} Sink ASEs ({iut_source_channels} channels) on Lower Tester"
    )

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
    for i in range(0, iut_source_streams):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SINK
        config.max_sdu_size = default_config.max_sdu_size * iut_source_channels

        if pts_sink_locations != 0:
            config.audio_locations = pts_sink_locations
            log("Use Sink Locations %u from Test Specification", config.audio_locations)
        else:
            config.audio_locations = get_audio_locations_from_pac(
                default_config.addr_type, default_config.addr, config.audio_dir)
            log("Use Sink Locations %u from PACS Sink Record", config.audio_locations)

        if not config.audio_locations:
            log('hdl_wid_504 exit, no suitable sink audio locations')
            return False

        sinks.append(config)

    sources = []
    for i in range(0, iut_sink_streams):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SOURCE
        config.max_sdu_size = default_config.max_sdu_size * iut_sink_channels
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)

        if not config.audio_locations:
            log('hdl_wid_504 exit, no suitable source audio locations')
            return False

        sources.append(config)

    ase_found_ev_cache = []
    ases = sinks + sources
    for config in ases:
        ev = stack.bap.wait_ase_found_ev(default_config.addr_type,
                                         default_config.addr,
                                         config.audio_dir, 30, remove=True)
        if ev is None:
            log('hdl_wid_504 exit, no suitable ase found')
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
                log('hdl_wid_504 exit, not streaming')
                return False

    return True


def hdl_wid_506(params: WIDParams):
    """
    Please click OK when the IUT is ready to broadcast Basic Audio Announcements with Audio Location Front xxx
    """

    # There's no explicit 'stop broadcast / advertising' dialog for TMAP/BMS/ASC/BV-01-I in PTS, therefore,
    # we first stop a potential ongoing advertising + broadcast before starting the new one

    # TODO: store Broadcast/Advertising state and only disable adv + broadcast if it has been started

    source_id = 0x00
    btp.cap_broadcast_adv_stop(source_id)
    btp.cap_broadcast_source_stop(source_id)
    btp.cap_broadcast_source_release(source_id)

    # Get Audio Locations from description
    audio_locations = 0
    if 'Left' in params.description:
        audio_locations |= 1
    if 'Right' in params.description:
        audio_locations |= 2

    # based on cap/hdl_wid_114 using fixed configuration

    source_num = 1
    metadata = struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)
    qos_set_name = '48_2_1'
    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    codec_set_name, *qos_config = BAS_CONFIG_SETTINGS[qos_set_name]

    (sampling_freq, frame_duration, octets_per_frame) = \
        CODEC_CONFIG_SETTINGS[codec_set_name]
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)

    subgroup_id = 0x00
    presentation_delay = 40000

    for i in range(source_num):
        btp.cap_broadcast_source_setup_stream(source_id, subgroup_id, coding_format, vid, cid,
                                              codec_ltvs_bytes, metadata)

    btp.cap_broadcast_source_setup_subgroup(source_id, subgroup_id, coding_format, vid, cid,
                                            codec_ltvs_bytes, metadata)

    # Zephyr stack generates Broadcast_ID itself
    broadcast_id = 0x123456
    btp.cap_broadcast_source_setup(source_id, broadcast_id, *qos_config, presentation_delay,
                                   encryption=False, broadcast_code=None,
                                   subgroup_codec_level=False)

    btp.cap_broadcast_adv_start(source_id)

    btp.cap_broadcast_source_start(source_id)

    data = bytearray([j for j in range(0, 41)])

    # PTS does not send an explicit message, but for each
    # configured SINK it expects to receive any ISO data.
    for _ in range(1, 10):
        _safe_bap_send(0, data)

    return True


def hdl_wid_507(_: WIDParams):
    """
    Please confirm if the IUT read Front Left/Right Audio Location.
    """

    return True


def hdl_wid_511(params: WIDParams):
    """
    Please place a call using CCP Originate Call.
    """

    # get peer addr
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    btp.ccp_originate_call(BT_TBS_GTBS_INDEX, 'tel:+123456789', addr_type, addr)

    return True


def hdl_wid_512(params: WIDParams):
    """
    Please terminate the call using CCP Terminate Call
    """

    # get peer addr
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    # TODO: call_id should be retrieved somehow, e.g from control pointer operation event, or
    #       by explicitly reading call states
    call_id = 0
    btp.ccp_terminate_call(BT_TBS_GTBS_INDEX, call_id, addr_type, addr)

    return True


def hdl_wid_514(params: WIDParams):
    """
    Please read lock characteristic.
    """

    # copy from wid/cap.py, hdl_wid_405
    if params.test_case_name.endswith('LT2'):
        # Ordered Access Operation reads locks of all members
        return True

    btp.csip_start_ordered_access()

    return True


def hdl_wid_516(params: WIDParams):
    """
    Please confirm the IUT has a single channel of audio with no location
    """

    return True


def hdl_wid_517(params: WIDParams):
    """
    Click OK will send CCP Originate Call.
    """

    return True


def hdl_wid_521(params: WIDParams):
    """
    Please click Ok when IUT is ready to start the CAP Unicast Audio Start Procedure
    """

    # implemented in hdl_311
    hdl_wid_311(params)

    return True


def hdl_wid_522(params: WIDParams):
    """
    Please advertise TMAP role characteristics in extended advertisement.
    """

    # Advertisement configured by test case in ptsproject/$PROJECT/tmap.py

    return True


# Copy & paste from wid/gap.py
def hdl_wid_2004(params: WIDParams):
    """
    Please confirm that 6-digit number is matched with [passkey].
    """
    pattern = r'[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if stack.gap.get_passkey() is None:
        return False

    btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
    match = stack.gap.passkey.data == passkey

    # clear passkey for repeated pairing attempts
    stack.gap.passkey.data = None

    return match


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(params: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
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

    # race condition: connect will cause pairing, which might trigger numeric comparison, but
    # PTS will show WID2004 to let us confirm, which we cannot if we're still in this function
    # => only connect here and trigger CAP, BAP, CSIP discovery later
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


def hdl_wid_20106(params: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor
        of ASE Control Point characteristic to enable notification.
    """

    trigger_discovery_if_needed(params)

    return True


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read X characteristic with handle = 0xXXXX.
    """

    stack = get_stack()

    logging.debug("description=%r", params.description)

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    if "Volume State" in params.description:
        btp.vcp_state_read(addr_type, addr)
        ev = stack.vcp.wait_vcp_procedure_ev(addr_type, addr, 10)
        if ev is not None:
            return True

    MMI.reset()
    MMI.parse_description(params.description)
    handle = MMI.args[0]

    btp.gattc_read(addr_type, addr, handle)
    btp.gattc_read_rsp()

    return True


def hdl_wid_20110(params: WIDParams):
    """
        Please send write request to handle 0x024A with following value.
        Volume Control Point:
        Op Code: [4 (0x04)] Set Absolute Volume
        Change Counter: <WildCard: Exists>
        Volume Setting: [255 (0xFF)]
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    # Get volume from description
    volume_pattern = r"Volume Setting: \[(\d+) \(0x[0-9A-Fa-f]+\)\]"
    match = re.search(volume_pattern, params.description)
    if match:
        volume_setting = match.group(1)
        btp.vcp_set_vol(volume_setting, addr_type, addr)

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


def hdl_wid_20206(_: WIDParams):
    """
    Please verify that for each supported characteristic,
    attribute handle/UUID pair(s) is returned to the upper tester.
    TMAP Role: Attribute Handle = 0x0321
    """

    # BTstack uses GATT Read Value by Type without first searching for TMAP Service and finding TMAP Characteristics

    return True
