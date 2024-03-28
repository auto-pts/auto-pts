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
import struct
from argparse import Namespace

from autopts.pybtp import btp, defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp import pts_addr_get, pts_addr_type_get, lt2_addr_get, lt2_addr_type_get
from autopts.pybtp.defs import AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, AUDIO_METADATA_CCID_LIST
from autopts.pybtp.types import WIDParams, ASCSState, BTPError
from autopts.wid import generic_wid_hdl
from autopts.wid.bap import (create_default_config, AudioDir, get_audio_locations_from_pac,
                             create_lc3_ltvs_bytes, CODEC_CONFIG_SETTINGS, QOS_CONFIG_SETTINGS,
                             BAS_CONFIG_SETTINGS)

log = logging.debug


def cap_wid_hdl(wid, description, test_case_name):
    log(f'{cap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin

def hdl_wid_104(_: WIDParams):
    """Please send non connectable advertise with periodic info."""

    # Periodic adv started within cap_broadcast_adv_start at hdl_wid_114.

    return True


wid_114_settings = {
    # test_case_name: (source_num, metadata)
    'CAP/INI/BST/BV-01-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-02-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-03-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-04-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-05-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-06-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-07-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/BST/BV-08-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-09-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-10-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/BST/BV-11-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-12-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-13-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-14-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-15-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/BST/BV-16-C': (1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/BST/BV-17-C': (2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
}


def hdl_wid_114(params: WIDParams):
    """Please advertise with Broadcast Audio Announcement (0x1852) service data"""

    # btp.gap_adv_off()

    source_num, metadata = wid_114_settings[params.test_case_name]
    qos_set_name = '8_1_1'
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
    for i in range(1, 10):
        try:
            btp.bap_send(0, data)
        except BTPError:
            # Buffer full
            pass

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
        return not ev is None

    return False


wid_310_settings = {
    'CAP/INI/UST/BV-32-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200),
    'CAP/INI/UST/BV-33-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200),
    'CAP/INI/UST/BV-34-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00),
    'CAP/INI/UST/BV-35-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00),
    'CAP/INI/UST/BV-36-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01),
    'CAP/INI/UST/BV-37-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01),
}


def hdl_wid_309(params: WIDParams):
    if params.test_case_name.endswith('LT2'):
        return True

    cig_id = 0x00
    btp.cap_unicast_audio_stop(cig_id)

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
    update_metadata = []

    for config in stack.bap.ase_configs:
        update_metadata.append((config.addr_type, config.addr, config.ase_id, metadata))

    btp.cap_unicast_audio_update(update_metadata)

    return True


def hdl_wid_312(params: WIDParams):
    """Please configure ASE state to Disable"""
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    configs = []
    stack = get_stack()
    for ase in stack.bap.ase_configs:
        if ase.addr == addr:
            configs.append(ase)

    if not configs:
        log('No ASE ID found in configs')
        return False

    stack.ascs.event_queues[defs.ASCS_EV_OPERATION_COMPLETED].clear()
    for config in configs:
        btp.ascs_disable(config.ase_id, addr_type, addr)
        ev = stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, config.ase_id, 10)
        if ev is None:
            raise Exception("Disable command failed")

    for config in configs:
        if config.audio_dir == AudioDir.SOURCE:
            # Initiate receiver Stop Ready
            btp.ascs_receiver_stop_ready(config.ase_id, addr_type, addr)
            ev = stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, config.ase_id, 10)
            if ev is None:
                raise Exception("Receiver Stop Ready command failed")

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


def hdl_wid_377(_: WIDParams):
    """Please confirm sent streaming data"""
    return True


wid_400_settings = {
    # test_case_name: (sink_num, source_num, LT_count, metadata)
    # Two Lower Testers, unidirectional
    'CAP/INI/UST/BV-01-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-02-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-03-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0004) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-04-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0004) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-05-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0002) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-06-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0002) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-07-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-08-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-09-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0080) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-10-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0080) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-11-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-12-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-13-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/UST/BV-14-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    # Single LT, unidirectional
    'CAP/INI/UST/BV-15-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-16-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-17-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0004) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-18-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0004) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-19-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0002) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-20-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0002) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-21-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-22-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-23-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0080) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-24-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0080) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-25-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-26-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-27-C': (2, 0, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/UST/BV-28-C': (0, 2, 1, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    # Two LTs, one CIS bidirectional, the other CIS unidirectional
    'CAP/INI/UST/BV-29-C': (1, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007)),
    'CAP/INI/UST/BV-29-C_LT2': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007)),
    'CAP/INI/UST/BV-30-C': (1, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-30-C_LT2': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007) +
                                struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-31-C': (1, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/UST/BV-31-C_LT2': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0007) +
                                struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),

    # Two LTs, unidirectional
    'CAP/INI/UST/BV-32-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-33-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-34-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-35-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)),
    'CAP/INI/UST/BV-36-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/UST/BV-37-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                            struct.pack('<BBBB', 3, AUDIO_METADATA_CCID_LIST, 0x00, 0x01)),
    'CAP/INI/UST/BV-40-C': (0, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-41-C': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),

    'CAP/INI/UST/BV-42-C': (1, 1, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
    'CAP/INI/UST/BV-42-C_LT2': (1, 0, 2, struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)),
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
    for i in range(0, sink_num):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SINK
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)

        if not config.audio_locations:
            log('hdl_wid_400 exit, no suitable sink audio locations')
            return False

        sinks.append(config)

    sources = []
    for i in range(0, source_num):
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
                                                           10)
            if ev is None:
                return False

    return True


def hdl_wid_402(_: WIDParams):
    """
        Click OK will initiate release operation
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


def hdl_wid_409(_: WIDParams):
    """Please update metadata in BASE. Then click OK when IUT is ready
       to advertise with new BASE information"""

    source_id = 0x00
    metadata = struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0004) + \
               struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00)

    btp.cap_broadcast_adv_stop(source_id)

    btp.cap_broadcast_source_update(source_id, metadata)

    btp.cap_broadcast_adv_start(source_id)

    return True


update_settings = {
    'CAP/INI/BST/BV-13-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x00),
    'CAP/INI/BST/BV-14-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200) +
                           struct.pack('<BBB', 2, AUDIO_METADATA_CCID_LIST, 0x01),
    'CAP/INI/BST/BV-15-C': struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200),
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


def hdl_wid_419(params: WIDParams):
    """
        Please configure to Streaming state.
    """
    return hdl_wid_400(params)


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
    """
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
