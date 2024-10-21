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
from argparse import Namespace

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import lt2_addr_get, lt2_addr_type_get, pts_addr_get, pts_addr_type_get
from autopts.pybtp.defs import AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, AUDIO_METADATA_CCID_LIST
from autopts.pybtp.types import WIDParams, AudioDir, ASCSState, CODEC_CONFIG_SETTINGS, create_lc3_ltvs_bytes, BTPError
from autopts.wid import generic_wid_hdl
from autopts.wid.bap import BAS_CONFIG_SETTINGS

log = logging.debug

gmap_audio_location_mapping = {
    "Not allocated" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT],
    "None" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT],
    "0b11" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT | defs.PACS_AUDIO_LOCATION_FRONT_RIGHT],
    "0b01 and 0b10" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT, defs.PACS_AUDIO_LOCATION_FRONT_RIGHT]
}


QOS_CONFIG_SETTINGS_GAMING = {
    # Set_Name: (Codec_Config, SDU_interval, Framing, Maximum_SDU_Size, Retransmission_Number, Max_Transport_Latency_ms, Presentation_Delay)

    # Unicast
    '16_1_gs': ("16_1",  7500, 0x00,  30, 1, 15, 60000),
    '16_2_gs': ("16_2", 10000, 0x00,  40, 1, 20, 60000),
    '32_1_gs': ("32_1", 7500,  0x00,  60, 1, 15, 60000),
    '32_2_gs': ("32_2", 10000, 0x00,  80, 1, 20, 60000),
    '48_1_gs': ("48_1",  7500, 0x00,  75, 1, 15, 60000),
    '48_2_gs': ("48_2", 10000, 0x00, 100, 1, 20, 60000),
    # Unicast
    '16_1_gr': ("16_1",  7500, 0x00,  30, 1, 15, 10000),
    '16_2_gr': ("16_2", 10000, 0x00,  40, 1, 20, 10000),
    '32_1_gr': ("32_1",  7500, 0x00,  60, 1, 15, 10000),
    '32_2_gr': ("32_2", 10000, 0x00,  80, 1, 20, 10000),
    '48_1_gr': ("48_1",  7500, 0x00,  75, 1, 15, 10000),
    '48_2_gr': ("48_2", 10000, 0x00, 100, 1, 20, 10000),
    '48_3_gr': ("48_3",  7500, 0x00,  90, 1, 15, 10000),
    '48_4_gr': ("48_4", 10000, 0x00, 120, 1, 20, 10000),
    # Broadcast
    '48_1_g': ("48_1", 7500, 0x00, 75, 1, 15, 10000),
    '48_2_g': ("48_2", 10000, 0x00, 100, 1, 20, 10000),
    '48_3_g': ("48_3", 7500, 0x00, 90, 1, 15, 10000),
    '48_4_g': ("48_4", 10000, 0x00, 120, 1, 20, 10000),
}


# Audio Configuration from BAP TS
# - Each configuration has number of servers and an array of server entries
# - Each server entry has an array of CIS entries
# - Each CIS entry specifies number of audio channels on local and remote sinks (matching the topology field)
# == local sink channel <-> remote source channels
audio_configurations_unicast = {
    "AC 1":      (1, [[(0, 1)]]),
    "AC 2":      (1, [[(1, 0)]]),
    "AC 3":      (1, [[(1, 1)]]),
    "AC 4":      (1, [[(0, 2)]]),
    "AC 5":      (1, [[(1, 2)]]),
    "AC 6(i)":   (1, [[(0, 1), (0, 1)]]),
    "AC 6(ii)":  (2, [[(0, 1)        ], [(0, 1)]]),
    "AC 7(i)":   (1, [[(0, 1), (1, 0)]]),
    "AC 7(ii)":  (2, [[(0, 1)        ], [(1, 0)]]),
    "AC 8(i)":   (1, [[(0, 1), (1, 1)]]),
    "AC 8(ii)":  (2, [[(0, 1)        ], [(1, 1)]]),
    "AC 9(i)":   (1, [[(1, 0), (1, 0)]]),
    "AC 9(ii)":  (2, [[(1, 0)        ], [(1, 0)]]),
    "AC 10":     (1, [[(2, 0)]]),
    "AC 11(i)":  (1, [[(1, 1), (1, 1)]]),
    "AC 11(ii)": (2, [[(1, 1)        ], [(1, 1)]]),
}


# Audio Configuration from BAP TS
# - num bis, num channels per bis
audio_configurations_broadcast = {
    "AC 12": (1, 1),
    "AC 13": (2, 1),
    "AC 14": (1, 2),
}

def gmap_wid_hdl(wid, description, test_case_name):
    log(f'{gmap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def create_default_config():
    return Namespace(addr=pts_addr_get(),
                     addr_type=pts_addr_type_get(),
                     vid=0x0000,
                     cid=0x0000,
                     coding_format=0x06,
                     frames_per_sdu=0x01,
                     audio_locations=0x01,
                     cig_id=0x00,
                     cis_id=0x00,
                     presentation_delay=40000,
                     qos_config=None,
                     codec_set_name=None,
                     codec_ltvs=None,
                     metadata_ltvs=None,
                     mono=None)


def config_for_qos_name(qos_name):
    config = create_default_config()
    config.qos_set_name = qos_name

    (config.codec_set_name,
     config.sdu_interval,
     config.framing,
     config.max_sdu_size,
     config.retransmission_number,
     config.max_transport_latency,
     config.presentation_delay) = QOS_CONFIG_SETTINGS_GAMING[config.qos_set_name]

    (config.sampling_freq,
     config.frame_duration,
     config.octets_per_frame) = CODEC_CONFIG_SETTINGS[config.codec_set_name]

    # streaming audio context = game
    config.metadata_ltvs = struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0008)
    return config


def gmap_discover():
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.gmap_discover(addr_type, addr)
    ev = stack.gmap.wait_discovery_completed_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True

# wid handlers section begin


test_cases_bgr_llb = {
    "GMAP/BGR/LLB/BV-13-C": ("AC 12", "48_1_g", "None", 1),
    "GMAP/BGR/LLB/BV-14-C": ("AC 12", "48_2_g", "None", 1),
    "GMAP/BGR/LLB/BV-15-C": ("AC 12", "48_3_g", "None", 1),
    "GMAP/BGR/LLB/BV-16-C": ("AC 12", "48_4_g", "None", 1),
    "GMAP/BGR/LLB/BV-01-C": ("AC 13", "48_1_g", "TSPX_IUT_Sink_Audio_Location", 2),
    "GMAP/BGR/LLB/BV-02-C": ("AC 13", "48_2_g", "TSPX_IUT_Sink_Audio_Location", 2),
    "GMAP/BGR/LLB/BV-03-C": ("AC 13", "48_3_g", "TSPX_IUT_Sink_Audio_Location", 2),
    "GMAP/BGR/LLB/BV-04-C": ("AC 13", "48_4_g", "TSPX_IUT_Sink_Audio_Location", 2),
    "GMAP/BGR/LLB/BV-09-C": ("AC 13", "48_1_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-10-C": ("AC 13", "48_2_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-11-C": ("AC 13", "48_3_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-12-C": ("AC 13", "48_4_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-17-C": ("AC 14", "48_1_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-18-C": ("AC 14", "48_2_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-19-C": ("AC 14", "48_3_g", "0b01 and 0b10", 1),
    "GMAP/BGR/LLB/BV-20-C": ("AC 14", "48_4_g", "0b01 and 0b10", 1)
}

test_cases_bgs_mxlt = {
    "GMAP/BGS/MXLT/BV-05-C": ("AC 12", "48_1_g"),
    "GMAP/BGS/MXLT/BV-06-C": ("AC 12", "48_2_g"),
    "GMAP/BGS/MXLT/BV-07-C": ("AC 12", "48_3_g"),
    "GMAP/BGS/MXLT/BV-08-C": ("AC 12", "48_4_g"),
    "GMAP/BGS/MXLT/BV-01-C": ("AC 13", "48_1_g"),
    "GMAP/BGS/MXLT/BV-02-C": ("AC 13", "48_2_g"),
    "GMAP/BGS/MXLT/BV-03-C": ("AC 13", "48_3_g"),
    "GMAP/BGS/MXLT/BV-04-C": ("AC 13", "48_4_g"),
    "GMAP/BGS/MXLT/BV-09-C": ("AC 14", "48_1_g"),
    "GMAP/BGS/MXLT/BV-10-C": ("AC 14", "48_2_g"),
    "GMAP/BGS/MXLT/BV-11-C": ("AC 14", "48_3_g"),
    "GMAP/BGS/MXLT/BV-12-C": ("AC 14", "48_4_g")
}

def hdl_wid_100(params: WIDParams):
    """
    Please synchronize with Broadcast ISO request
    """
    if params.test_case_name.endswith('LT2'):
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
    """Please send non connectable advertise with periodic info."""

    # Periodic adv started within cap_broadcast_adv_start at hdl_wid_114.

    return True


wid_114_settings = {
    # test_case_name: (audio configuration, qos setting, audio channel allocation)
    "GMAP/BGS/LLB/BV-05-C": ("AC 12", "48_1_g", "None"),
    "GMAP/BGS/LLB/BV-06-C": ("AC 12", "48_2_g", "None"),
    "GMAP/BGS/LLB/BV-07-C": ("AC 12", "48_3_g", "None"),
    "GMAP/BGS/LLB/BV-08-C": ("AC 12", "48_4_g", "None"),
    "GMAP/BGS/LLB/BV-01-C": ("AC 13", "48_1_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-02-C": ("AC 13", "48_2_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-03-C": ("AC 13", "48_3_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-04-C": ("AC 13", "48_4_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-09-C": ("AC 14", "48_1_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-10-C": ("AC 14", "48_2_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-11-C": ("AC 14", "48_3_g", "0b01 and 0b10"),
    "GMAP/BGS/LLB/BV-12-C": ("AC 14", "48_4_g", "0b01 and 0b10")
}


def hdl_wid_114(params: WIDParams):
    """Please advertise with Broadcast Audio Announcement (0x1852) service data"""


    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    presentation_delay = 10000

    audio_configuration, qos_setting, audio_channel_allocation = wid_114_settings[params.test_case_name]
    log(wid_114_settings[params.test_case_name])

    config = config_for_qos_name(qos_setting)
    log(config)
    num_bis, num_channels_per_bis = audio_configurations_broadcast[audio_configuration]

    audio_location_list = gmap_audio_location_mapping[audio_channel_allocation].copy()
    log(f"audio location list: {audio_location_list}")

    source_id = 0x00
    subgroup_id = 0x00
    subgroup_audio_location = 0

    for i in range(num_bis):
        audio_location = 0
        for j in range(num_channels_per_bis):
            audio_location = audio_location | audio_location_list.pop(0)
        subgroup_audio_location = subgroup_audio_location | audio_location
        logging.debug(f"Using Locations: {audio_location} for BIS {i}")
        config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                  config.frame_duration,
                                                  audio_location,
                                                  config.octets_per_frame * num_channels_per_bis,
                                                  config.frames_per_sdu)
        btp.cap_broadcast_source_setup_stream(source_id, subgroup_id, coding_format, vid, cid,
                                              config.codec_ltvs, config.metadata_ltvs)

    config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                              config.frame_duration,
                                              subgroup_audio_location,
                                              config.octets_per_frame * num_channels_per_bis,
                                              config.frames_per_sdu)
    btp.cap_broadcast_source_setup_subgroup(source_id, subgroup_id, coding_format, vid, cid,
                                            config.codec_ltvs, config.metadata_ltvs)

    # Zephyr stack generates Broadcast_ID itself
    broadcast_id = 0x123456
    btp.cap_broadcast_source_setup(source_id, broadcast_id, config.sdu_interval, config.framing, config.max_sdu_size,
                               config.retransmission_number, config.max_transport_latency, presentation_delay,
                                   encryption=False, broadcast_code=None,
                                   subgroup_codec_level=True)

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


gmap_ugg_unidirectional_settings = {
    # test_case_name: (audio configuration, qos name, audio channel allocation, LT_count)
    "GMAP/UGG/LLU/BV-63-C": ("AC 1",     "32_1_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-64-C": ("AC 1",     "32_2_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-51-C": ("AC 1",     "48_1_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-52-C": ("AC 1",     "48_2_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-53-C": ("AC 1",     "48_3_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-54-C": ("AC 1",     "48_4_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-87-C": ("AC 2",     "16_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-88-C": ("AC 2",     "16_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-55-C": ("AC 2",     "32_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-56-C": ("AC 2",     "32_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-57-C": ("AC 2",     "48_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-58-C": ("AC 2",     "48_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-69-C": ("AC 4",     "32_1_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-70-C": ("AC 4",     "32_2_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-59-C": ("AC 4",     "48_1_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-60-C": ("AC 4",     "48_2_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-61-C": ("AC 4",     "48_3_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-62-C": ("AC 4",     "48_4_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-73-C": ("AC 6(i)",  "32_1_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-74-C": ("AC 6(i)",  "32_2_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-01-C": ("AC 6(i)",  "48_1_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-02-C": ("AC 6(i)",  "48_2_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-03-C": ("AC 6(i)",  "48_3_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-04-C": ("AC 6(i)",  "48_4_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-75-C": ("AC 6(ii)", "32_1_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-76-C": ("AC 6(ii)", "32_2_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-05-C": ("AC 6(ii)", "48_1_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-06-C": ("AC 6(ii)", "48_2_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-07-C": ("AC 6(ii)", "48_3_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-08-C": ("AC 6(ii)", "48_4_gr", "0b01 and 0b10", 2),

    "GMAP/UGG/MXLT/BV-55-C": ("AC 1",     "32_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-56-C": ("AC 1",     "32_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-37-C": ("AC 1",     "48_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-38-C": ("AC 1",     "48_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-39-C": ("AC 1",     "48_3_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-40-C": ("AC 1",     "48_4_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-61-C": ("AC 4",     "32_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-62-C": ("AC 4",     "32_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-41-C": ("AC 4",     "48_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-42-C": ("AC 4",     "48_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-43-C": ("AC 4",     "48_3_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-44-C": ("AC 4",     "48_4_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-65-C": ("AC 6(i)",  "32_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-66-C": ("AC 6(i)",  "32_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-29-C": ("AC 6(i)",  "48_1_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-30-C": ("AC 6(i)",  "48_2_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-31-C": ("AC 6(i)",  "48_3_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-32-C": ("AC 6(i)",  "48_4_gr", "Not allocated", 1),
    "GMAP/UGG/MXLT/BV-67-C": ("AC 6(ii)", "32_1_gr", "Not allocated", 2),
    "GMAP/UGG/MXLT/BV-68-C": ("AC 6(ii)", "32_2_gr", "Not allocated", 2),
    "GMAP/UGG/MXLT/BV-33-C": ("AC 6(ii)", "48_1_gr", "Not allocated", 2),
    "GMAP/UGG/MXLT/BV-34-C": ("AC 6(ii)", "48_2_gr", "Not allocated", 2),
    "GMAP/UGG/MXLT/BV-35-C": ("AC 6(ii)", "48_3_gr", "Not allocated", 2),
    "GMAP/UGG/MXLT/BV-36-C": ("AC 6(ii)", "48_4_gr", "Not allocated", 2),
}

gmap_ugg_bidirectional_settings = {
    # test_case_name: (audio configuration, UGG to UGT QoS Setting, audio channel allocation, UGT to UGG QoS Setting, LT_count)
    "GMAP/UGG/LLU/BV-89-C":  ("AC 3",      "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-90-C":  ("AC 3",      "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-91-C":  ("AC 3",      "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-92-C":  ("AC 3",      "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-65-C":  ("AC 3",      "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-66-C":  ("AC 3",      "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-09-C":  ("AC 3",      "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-10-C":  ("AC 3",      "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-11-C":  ("AC 3",      "48_1_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-12-C":  ("AC 3",      "48_2_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-13-C":  ("AC 3",      "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-14-C":  ("AC 3",      "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-67-C":  ("AC 3",      "48_3_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-68-C":  ("AC 3",      "48_4_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-93-C":  ("AC 5",      "32_1_gr", "0b11",          "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-94-C":  ("AC 5",      "32_2_gr", "0b11",          "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-95-C":  ("AC 5",      "48_1_gr", "0b11",          "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-96-C":  ("AC 5",      "48_2_gr", "0b11",          "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-71-C":  ("AC 5",      "32_1_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-72-C":  ("AC 5",      "32_2_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-15-C":  ("AC 5",      "48_1_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-16-C":  ("AC 5",      "48_2_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-17-C":  ("AC 5",      "48_1_gr", "0b11",          "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-18-C":  ("AC 5",      "48_2_gr", "0b11",          "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-19-C":  ("AC 5",      "48_3_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-20-C":  ("AC 5",      "48_4_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-97-C":  ("AC 7(ii)",  "32_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-98-C":  ("AC 7(ii)",  "32_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-99-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-100-C": ("AC 7(ii)",  "48_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-41-C":  ("AC 7(ii)",  "32_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-42-C":  ("AC 7(ii)",  "32_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-21-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-22-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-23-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-24-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-25-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-26-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-77-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-78-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-101-C": ("AC 8(i)",   "32_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-102-C": ("AC 8(i)",   "32_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-103-C": ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-104-C": ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-79-C":  ("AC 8(i)",   "32_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-80-C":  ("AC 8(i)",   "32_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-27-C":  ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-28-C":  ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-29-C":  ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-30-C":  ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-31-C":  ("AC 8(i)",   "48_3_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-32-C":  ("AC 8(i)",   "48_4_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-105-C": ("AC 8(ii)",  "32_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-106-C": ("AC 8(ii)",  "32_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-107-C": ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-108-C": ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-81-C":  ("AC 8(ii)",  "32_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-82-C":  ("AC 8(ii)",  "32_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-33-C":  ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-34-C":  ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-35-C":  ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-36-C":  ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-37-C":  ("AC 8(ii)",  "48_3_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-38-C":  ("AC 8(ii)",  "48_4_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-109-C": ("AC 11(i)",  "32_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-110-C": ("AC 11(i)",  "32_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-111-C": ("AC 11(i)",  "48_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-112-C": ("AC 11(i)",  "48_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-83-C":  ("AC 11(i)",  "32_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-84-C":  ("AC 11(i)",  "32_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-39-C":  ("AC 11(i)",  "48_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-40-C":  ("AC 11(i)",  "48_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-43-C":  ("AC 11(i)",  "48_3_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-44-C":  ("AC 11(i)",  "48_4_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-113-C": ("AC 11(ii)", "32_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-114-C": ("AC 11(ii)", "32_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-115-C": ("AC 11(ii)", "48_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-116-C": ("AC 11(ii)", "48_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-85-C":  ("AC 11(ii)", "32_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-86-C":  ("AC 11(ii)", "32_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-45-C":  ("AC 11(ii)", "48_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-46-C":  ("AC 11(ii)", "48_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-49-C":  ("AC 11(ii)", "48_3_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-50-C":  ("AC 11(ii)", "48_4_gr", "0b01 and 0b10", "32_2_gs", 2),

    "GMAP/UGG/MXLT/BV-128-C": ("AC 3",      "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-129-C": ("AC 3",      "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-130-C": ("AC 3",      "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-131-C": ("AC 3",      "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-57-C":  ("AC 3",      "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-58-C":  ("AC 3",      "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-01-C":  ("AC 3",      "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-02-C":  ("AC 3",      "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-45-C":  ("AC 3",      "48_1_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/MXLT/BV-46-C":  ("AC 3",      "48_2_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/MXLT/BV-03-C":  ("AC 3",      "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-04-C":  ("AC 3",      "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-59-C":  ("AC 3",      "48_3_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/MXLT/BV-60-C":  ("AC 3",      "48_4_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/MXLT/BV-132-C": ("AC 5",      "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-133-C": ("AC 5",      "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-134-C": ("AC 5",      "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-135-C": ("AC 5",      "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-63-C":  ("AC 5",      "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-64-C":  ("AC 5",      "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-05-C":  ("AC 5",      "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-06-C":  ("AC 5",      "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-47-C":  ("AC 5",      "48_1_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/MXLT/BV-48-C":  ("AC 5",      "48_2_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/MXLT/BV-07-C":  ("AC 5",      "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-08-C":  ("AC 5",      "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-136-C": ("AC 7(ii)",  "32_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-137-C": ("AC 7(ii)",  "32_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-138-C": ("AC 7(ii)",  "48_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-139-C": ("AC 7(ii)",  "48_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-69-C":  ("AC 7(ii)",  "32_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-70-C":  ("AC 7(ii)",  "32_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-09-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-10-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-49-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/MXLT/BV-50-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/MXLT/BV-11-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-12-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-71-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/MXLT/BV-72-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/MXLT/BV-140-C": ("AC 8(i)",   "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-141-C": ("AC 8(i)",   "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-142-C": ("AC 8(i)",   "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-143-C": ("AC 8(i)",   "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-73-C":  ("AC 8(i)",   "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-74-C":  ("AC 8(i)",   "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-13-C":  ("AC 8(i)",   "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-14-C":  ("AC 8(i)",   "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-51-C":  ("AC 8(i)",   "48_1_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/MXLT/BV-52-C":  ("AC 8(i)",   "48_2_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/MXLT/BV-15-C":  ("AC 8(i)",   "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-16-C":  ("AC 8(i)",   "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-144-C": ("AC 8(ii)",  "32_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-145-C": ("AC 8(ii)",  "32_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-146-C": ("AC 8(ii)",  "48_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-147-C": ("AC 8(ii)",  "48_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-75-C":  ("AC 8(ii)",  "32_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-76-C":  ("AC 8(ii)",  "32_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-17-C":  ("AC 8(ii)",  "48_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-18-C":  ("AC 8(ii)",  "48_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-53-C":  ("AC 8(ii)",  "48_1_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/MXLT/BV-54-C":  ("AC 8(ii)",  "48_2_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/MXLT/BV-19-C":  ("AC 8(ii)",  "48_3_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-20-C":  ("AC 8(ii)",  "48_4_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-170-C": ("AC 11(i)",  "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-171-C": ("AC 11(i)",  "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-172-C": ("AC 11(i)",  "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/MXLT/BV-173-C": ("AC 11(i)",  "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/MXLT/BV-174-C": ("AC 11(i)",  "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-175-C": ("AC 11(i)",  "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-176-C": ("AC 11(i)",  "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-177-C": ("AC 11(i)",  "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-178-C": ("AC 11(i)",  "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/MXLT/BV-179-C": ("AC 11(i)",  "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/MXLT/BV-180-C": ("AC 11(ii)", "32_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-181-C": ("AC 11(ii)", "32_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-182-C": ("AC 11(ii)", "48_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/MXLT/BV-183-C": ("AC 11(ii)", "48_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/MXLT/BV-184-C": ("AC 11(ii)", "32_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-185-C": ("AC 11(ii)", "32_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-186-C": ("AC 11(ii)", "48_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-187-C": ("AC 11(ii)", "48_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/MXLT/BV-188-C": ("AC 11(ii)", "48_3_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/MXLT/BV-189-C": ("AC 11(ii)", "48_4_gr", "Not allocated", "32_2_gs", 2),
}


def hdl_wid_ugg_unidirectional(params: WIDParams):
    """
        Please configure 1 SINK ASE with Config Setting: .
    """

    lt1_test_name = params.test_case_name
    stack = get_stack()

    # get config
    audio_configuration, qos_name, audio_channel_allocation, lt_count = gmap_ugg_unidirectional_settings[lt1_test_name]
    log(gmap_ugg_unidirectional_settings[lt1_test_name])

    default_config = config_for_qos_name(qos_name)

    ases= []
    cig_id = 0x00
    cis_id = 0x00

    num_servers, server_entries = audio_configurations_unicast[audio_configuration]
    if num_servers != lt_count:
        log("Error: num servers incorrect")
        return False

    audio_location_list = gmap_audio_location_mapping[audio_channel_allocation].copy()
    log(f"audio location list: {audio_location_list}")

    lt_index = 0
    for cis_entries in server_entries:

        if lt_index == 0:
            addr = pts_addr_get()
            addr_type = pts_addr_type_get()
        else:
            addr = lt2_addr_get()
            addr_type = lt2_addr_type_get()

        for source_channels, sink_channels in cis_entries:
            if sink_channels > 0:

                audio_dir = AudioDir.SINK

                # Find ID of the ASE(s)
                ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
                if ev is None:
                    log(f"Could not find ASE for direction {audio_dir} on LT {lt_index+1}")
                    return False

                _, _, _, ase_id = ev

                audio_location = audio_location_list.pop()
                logging.debug(f"Using ASE_ID: {ase_id} for Location: {audio_location}")

                config = Namespace(**vars(default_config))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          sink_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            if source_channels > 0:

                audio_dir = AudioDir.SOURCE

                # Find ID of the ASE(s)
                ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
                if ev is None:
                    log(f"Could not find ASE for direction {audio_dir} on LT {lt_index + 1}")
                    return False

                _, _, _, ase_id = ev

                audio_location = audio_location_list.pop()
                logging.debug(f"Using ASE_ID: {ase_id} for Location: {audio_location}")

                config = Namespace(**vars(default_config))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          source_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            cis_id += 1

        lt_index += 1

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
            log('hdl_wid_ugg_unidirectional exit, not streaming')
            return False

    return True


def hdl_wid_ugg_bidirectional(params: WIDParams):
    """
    Please configure 1 SINK and 1 SOURCE ASE with Config Setting: .
    After that, configure both ASEes to streaming state.
    """

    lt1_test_name = params.test_case_name
    stack = get_stack()

    # get config
    audio_configuration, ugg_to_ugt_qos_name, audio_channel_allocation, ugt_to_ugg_qos_name, lt_count = gmap_ugg_bidirectional_settings[lt1_test_name]
    log(gmap_ugg_bidirectional_settings[lt1_test_name])

    default_config_ugg_to_ugt = config_for_qos_name(ugg_to_ugt_qos_name)
    default_config_ugt_to_ugg = config_for_qos_name(ugt_to_ugg_qos_name)

    num_servers, server_entries = audio_configurations_unicast[audio_configuration]
    if num_servers != lt_count:
        log("Error: num servers incorrect")
        return False

    audio_location_list = gmap_audio_location_mapping[audio_channel_allocation].copy()

    # get ASEs from BAP events and store in servers array
    servers = []
    for lt_index in range(lt_count):
        if lt_index == 0:
            addr = pts_addr_get()
            addr_type = pts_addr_type_get()
        else:
            addr = lt2_addr_get()
            addr_type = lt2_addr_type_get()

        # get Sink ASEs
        sink_ases = []
        while True:
            ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SINK, 1, remove=True)
            if ev is None:
                break
            _, _, _, ase_id = ev
            sink_ases.append(ase_id)

        # get Source ASEs
        source_ases = []
        while True:
            ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SOURCE, 1, remove=True)
            if ev is None:
                break
            _, _, _, ase_id = ev
            source_ases.append(ase_id)

        log(f"LT {lt_index+1} - {addr}({addr_type}): Sink ASEs {sink_ases}, Source ASEs {source_ases}")
        servers.append((lt_index, addr, addr_type, sink_ases, source_ases))
        lt_index += 1

    # calculate number of required sink and source ases per LT and select one
    assigned_servers = []
    total_sink_ases = 0
    for cis_entries in server_entries:
        num_sink_ases_required   = 0
        num_source_ases_required = 0
        for source_channels, sink_channels in cis_entries:
            if sink_channels > 0:
                num_sink_ases_required += 1
                total_sink_ases += 1
            if source_channels > 0:
                num_source_ases_required += 1

        # find suitable server
        found_lt = False
        for  server_info in servers:
            (lt_index, _, _, sink_ases, source_ases) = server_info
            if len(sink_ases) == num_sink_ases_required and len(source_ases) == num_source_ases_required:
                assigned_servers.append(server_info)
                found_lt = True

        if not found_lt:
                log(f"No LT with {num_sink_ases_required} Sink ASEs and {num_source_ases_required} Source ASEs available")
                return False

    # sanity check: no test has more than 2 Sink ASEs total
    if total_sink_ases > 2:
        log(f"Audio configuration {audio_configuration} requires more than 2 Sink ASEs")
        return False

    # setup ASEs
    ases= []
    cig_id = 0x00
    cis_id = 0x00
    for cis_entries in server_entries:

        (lt_index, addr, addr_type, sink_ases, source_ases) = assigned_servers.pop(0)

        for source_channels, sink_channels in cis_entries:

            if sink_channels > 0:

                ase_id = sink_ases.pop(0)
                audio_location = audio_location_list.pop()

                logging.debug(f"Using SINK ASE_ID: {ase_id} on LT {lt_index+1}")

                config = Namespace(**vars(default_config_ugg_to_ugt))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          sink_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            if source_channels > 0:

                ase_id = source_ases.pop(0)
                audio_location = 0

                logging.debug(f"Using Source ASE_ID: {ase_id} on LT {lt_index+1}")

                config = Namespace(**vars(default_config_ugt_to_ugg))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          source_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            cis_id += 1

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
            log('hdl_wid_ugg_bidirectional exit, not streaming')
            return False

    return True


def hdl_wid_311_and_313(params: WIDParams):
    # LT1 does all config
    if params.test_case_name.endswith('LT2'):
        return True

    tc_name = params.test_case_name
    if tc_name in gmap_ugg_unidirectional_settings:
        return hdl_wid_ugg_unidirectional(params)
    elif tc_name in gmap_ugg_bidirectional_settings:
        return hdl_wid_ugg_bidirectional(params)
    else:
        log("{tc_name} neither in hdl_wid_ugg_unidirectional nor hdl_wid_ugg_bidirectional")
        return False


def hdl_wid_311(params: WIDParams):
    """
        Please configure 1 SINK ASE with Config Setting: .
    """
    return hdl_wid_311_and_313(params)


def hdl_wid_313(params: WIDParams):
    """
    Please configure 1 SINK and 1 SOURCE ASE with Config Setting: .
    After that, configure both ASEes to streaming state.
    """
    return hdl_wid_311_and_313(params)


def hdl_wid_353(params: WIDParams):
    """
    Wait for Broadcast ISO request.
    """

    return True


def hdl_wid_364(_: WIDParams):
    """
    After processed audio stream data, please click OK.
    """

    return True


def hdl_wid_366(_: WIDParams):
    """
    Please click ok when IUT received and sent audio stream data.
    """

    return True

def hdl_wid_367(_: WIDParams):
    """
    Lower tester is streaming audio data.
    """

    return True


def hdl_wid_376(_: WIDParams):
    """
    Please confirm received streaming data...
    """

    return True


def hdl_wid_377(_: WIDParams):
    """Please confirm sent streaming data"""
    return True


def hdl_wid_387(_: WIDParams):
    """
    Please send valid streaming data.
    """

    return True


def hdl_wid_384(_: WIDParams):
    """
    Click OK will start transmitting audio streaming data.
    """

    return True

def hdl_wid_554(_: WIDParams):
    """
    Please click ok when the tester is ready to start CAP Unicast Audio Starting procedure.
    """

    return True


def hdl_wid_558(_: WIDParams):
    """
    Please click ok if the IUT is in streaming state.
    """

    return True


def hdl_wid_559(_: WIDParams):
    """
    Please advertise GMAP role characteristics in extended advertisement.
    """

    # Advertisement are started in project/gmap.py

    return True


def hdl_wid_2004(params: WIDParams):
    """
    Please confirm that 6 digit number is matched with [passkey].
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
    stack.gap.wait_for_connection(timeout=10, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30, addr=addr)

    return True


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """

    return True


def hdl_wid_20106(params: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor of ASE
        Control Point characteristic to enable notification.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    peer = stack.bap.get_peer(addr_type, addr)
    if peer.discovery_completed:
        log('Skip BAP discovery, discovery completed before')

        # Skip if discovery has been done already
        return True

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    return True


def hdl_wid_20103(_: WIDParams):
    """
    Please take action to discover the GMAP Role characteristic from the Gaming Audio. Discover the primary service if needed.
    """

    return gmap_discover()


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read X characteristic with handle = 0xXXXX.
    """

    logging.debug("description=%r", params.description)

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    MMI.reset()
    MMI.parse_description(params.description)
    handle = MMI.args[0]

    btp.gattc_read(addr_type, addr, handle)
    btp.gattc_read_rsp()

    return True



def hdl_wid_20116(_: WIDParams):
    """
    Please send command to the PTS to discover all mandatory characteristics of the Gaming Audio supported by the IUT.
    Discover primary service if needed.
    """

    return gmap_discover()


def hdl_wid_20206(_: WIDParams):
    """
    Please verify that for each supported characteristic, attribute handle/UUID pair(s) is returned to the upper tester.GMAP Role: Attribute Handle = 0x0281
    """

    # ToDo: verify values from dialog

    return True
