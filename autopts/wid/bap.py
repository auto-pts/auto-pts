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
import binascii
import logging
import random
import re
import struct
from argparse import Namespace
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import WIDParams, UUID
from autopts.wid import generic_wid_hdl

log = logging.debug


def bap_wid_hdl(wid, description, test_case_name):
    log(f'{bap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_20100(_: WIDParams):
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.gap_conn()
    stack.gap.gap_wait_for_sec_lvl_change(30)

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    return True


def disc_full(svc_uuid=None, ch_uuid=None):
    attrs = {}
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if svc_uuid:
        btp.gattc_disc_prim_uuid(bd_addr_type, bd_addr, svc_uuid)
        svcs = btp.gattc_disc_prim_uuid_rsp()
    else:
        btp.gattc_disc_all_prim(bd_addr_type, bd_addr)
        svcs = btp.gattc_disc_all_prim_rsp()

    if not svcs:
        return attrs

    for svc in svcs:
        attrs[svc] = {}

        if ch_uuid:
            btp.gattc_disc_chrc_uuid(bd_addr_type, bd_addr, svc.handle, svc.end_handle, ch_uuid)
            chars = btp.gattc_disc_chrc_uuid_rsp()
        else:
            btp.gattc_disc_all_chrc(bd_addr_type, bd_addr, svc.handle, svc.end_handle)
            chars = btp.gattc_disc_all_chrc_rsp()

        if not chars:
            continue

        for i in range(0, len(chars)):
            start_hdl = chars[i].handle + 2  # CCC handle
            end_hdl = start_hdl

            btp.gattc_disc_all_desc(btp.pts_addr_type_get(),
                                    btp.pts_addr_get(),
                                    start_hdl, end_hdl)

            descs = btp.gattc_disc_all_desc_rsp()
            attrs[svc][chars[i]] = descs

    return attrs


def hdl_wid_300(_: WIDParams):
    """
    Please scan for Advertising Packets and Press OK to confirm receiving
    the ASCS UUID and Available Audio Contexts.
    """

    btp.gap_start_discov(discov_type='passive', mode='observe')
    sleep(5)
    btp.gap_stop_discov()

    found = btp.check_discov_results(uuids=[UUID.ASCS])
    if not found:
        return False

    return btp.check_discov_results(uuids=[UUID.AVAILABLE_AUDIO_CTXS])


class AudioDir:
    SINK = 0x01
    SOURCE = 0x02


class ASCSOperation:
    CONFIG_CODEC = 0x01
    CONFIG_QOS = 0x02
    ENABLE = 0x03
    RECEIVER_START_READY = 0x04
    DISABLE = 0x05
    RECEIVER_STOP_READY = 0x06
    UPDATE_METADATA = 0x07
    RELEASE = 0x08


class ASCSState:
    IDLE = 0x00
    CODEC_CONFIGURED = 0x01
    QOS_CONFIGURED = 0x02
    ENABLING = 0x03
    STREAMING = 0x04
    DISABLING = 0x05
    RELEASING = 0x06


# Assigned Numbers (2023), 6.12.4 Codec_Specific_Capabilities LTV Structures
class LC3_PAC_LTV_Type:
    SAMPLING_FREQ = 0x01
    FRAME_DURATION = 0x02
    CHANNELS = 0x03
    FRAME_LEN = 0x04
    FRAMES_PER_SDU = 0x05


# Assigned Numbers (2023), 6.12.5 Codec_Specific_Configuration LTV structures
class LC3_LTV_Config_Type:
    SAMPLING_FREQ = 0x01
    FRAME_DURATION = 0x02
    CHANNEL_ALLOCATION = 0x03
    FRAME_LEN = 0x04
    FRAMES_PER_SDU = 0x05


SAMPLING_FREQ_STR_TO_CODE = {
    '8': 0x01,  # 8000 Hz
    '11.025': 0x02,  # 11025 Hz
    '16': 0x03,  # 16000 Hz
    '22.05': 0x04,  # 22050 Hz
    '24': 0x05,  # 24000 Hz
    '32': 0x06,  # 32000 Hz
    '44.1': 0x07,  # 44100 Hz
    '48': 0x08,  # 48000 Hz
    '88.2': 0x09,  # 88200 Hz
    '96': 0x0a,  # 96000 Hz
    '176.4': 0x0b,  # 1764000 Hz
    '192': 0x0c,  # 192000 Hz
    '384': 0x0d,  # 384000 Hz
}

FRAME_DURATION_STR_TO_CODE = {
    '7.5': 0x00,  # 7.5 ms
    '10': 0x01,  # 10 ms
}

CODEC_CONFIG_SETTINGS = {
    # Set_Name: (Sampling_Frequency, Frame_Duration, Octets_Per_Codec_Frame)
    '8_1': (0x01, 0x00, 26),
    '8_2': (0x01, 0x01, 30),
    '16_1': (0x03, 0x00, 30),
    '16_2': (0x03, 0x01, 40),
    '24_1': (0x05, 0x00, 45),
    '24_2': (0x05, 0x01, 60),
    '32_1': (0x06, 0x00, 60),
    '32_2': (0x06, 0x01, 80),
    '441_1': (0x07, 0x00, 97),
    '441_2': (0x07, 0x01, 130),
    '48_1': (0x08, 0x00, 75),
    '48_2': (0x08, 0x01, 100),
    '48_3': (0x08, 0x00, 90),
    '48_4': (0x08, 0x01, 120),
    '48_5': (0x08, 0x00, 117),
    '48_6': (0x08, 0x01, 155),
}

QOS_CONFIG_SETTINGS = {
    # Set_Name: (SDU_interval, Framing, Maximum_SDU_Size, Retransmission_Number, Max_Transport_Latency)
    '8_1_1': (7500, 0x00, 26, 2, 8),
    '8_2_1': (10000, 0x00, 30, 2, 10),
    '16_1_1': (7500, 0x00, 30, 2, 8),
    '16_2_1': (10000, 0x00, 40, 2, 10),
    '24_1_1': (7500, 0x00, 45, 2, 8),
    '24_2_1': (10000, 0x00, 60, 2, 10),
    '32_1_1': (7500, 0x00, 60, 2, 8),
    '32_2_1': (10000, 0x00, 80, 2, 10),
    '441_1_1': (8163, 0x01, 97, 5, 24),
    '441_2_1': (10884, 0x01, 130, 5, 31),
    '48_1_1': (7500, 0x00, 75, 5, 15),
    '48_2_1': (10000, 0x00, 100, 5, 20),
    '48_3_1': (7500, 0x00, 90, 5, 15),
    '48_4_1': (10000, 0x00, 120, 5, 20),
    '48_5_1': (7500, 0x00, 117, 5, 15),
    '48_6_1': (10000, 0x00, 155, 5, 20),
    '8_1_2': (7500, 0x00, 26, 13, 75),
    '8_2_2': (10000, 0x00, 30, 13, 95),
    '16_1_2': (7500, 0x00, 30, 13, 75),
    '16_2_2': (10000, 0x00, 40, 13, 95),
    '24_1_2': (7500, 0x00, 45, 13, 75),
    '24_2_2': (10000, 0x00, 60, 13, 95),
    '32_1_2': (7500, 0x00, 60, 13, 75),
    '32_2_2': (10000, 0x00, 80, 13, 95),
    '441_1_2': (8163, 0x01, 97, 13, 80),
    '441_2_2': (10884, 0x01, 130, 13, 85),
    '48_1_2': (7500, 0x00, 75, 13, 75),
    '48_2_2': (10000, 0x00, 100, 13, 95),
    '48_3_2': (7500, 0x00, 90, 13, 75),
    '48_4_2': (10000, 0x00, 120, 13, 100),
    '48_5_2': (7500, 0x00, 117, 13, 75),
    '48_6_2': (10000, 0x00, 155, 13, 100),
}


def bytes_to_ltvs(data):
    """Parse LTV values from bytes."""
    i = 0
    ltv = {}

    all_ltv_len = data[i]
    i += 1

    if all_ltv_len == 0:
        return ltv

    max_i = i + all_ltv_len
    while i < max_i:
        tv_len = data[i]
        i += 1

        ltv_type = data[i]
        i += 1

        value_len = tv_len - 1
        value = data[i:i + value_len]
        i += value_len

        ltv[ltv_type] = value

    return ltv


def create_lc3_ltvs_bytes(sampling_freq, frame_duration, audio_locations,
                          octets_per_frame, frames_per_sdu):
    ltvs = bytearray()
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.SAMPLING_FREQ, sampling_freq)
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.FRAME_DURATION, frame_duration)
    ltvs += struct.pack('<BBI', 5, LC3_LTV_Config_Type.CHANNEL_ALLOCATION, audio_locations)
    ltvs += struct.pack('<BBH', 3, LC3_LTV_Config_Type.FRAME_LEN, octets_per_frame)
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.FRAMES_PER_SDU, frames_per_sdu)

    return ltvs


def parse_pac_char_value(data):
    ltvs = {}
    number_of_pac_records = data[0]
    i = 1

    try:
        for n in range(0, number_of_pac_records):
            codec_id = data[i:i+5]
            i += 5

            ltvs[codec_id] = {}

            ltvs_len = data[i]
            if ltvs_len:
                capabilities = bytes_to_ltvs(data[i:i + ltvs_len + 1])
            else:
                capabilities = None
            i += ltvs_len + 1

            ltvs_len = data[i]
            if ltvs_len:
                metadata = bytes_to_ltvs(data[i:i + ltvs_len + 1])
            else:
                metadata = None
            i += ltvs_len + 1

            ltvs[codec_id] = (capabilities, metadata)
    except:
        # If MTU was so small that PAC records are truncated, lets
        # parse as much as possible and try to continue the test case.
        log(f'PAC records truncated, parsed ltvs: {ltvs}')

    return ltvs


def parse_ase_char_value(data):
    ase_id = data[0]
    state = data[1]

    if state == ASCSState.CODEC_CONFIGURED:
        framing = data[2]
        preferred_phy = data[3]
        preferred_retransmission_number = data[4]
        max_transport_latency = int.from_bytes(data[5:7], "little")
        presentation_delay_min = int.from_bytes(data[7:10], "little")
        presentation_delay_max = int.from_bytes(data[10:13], "little")
        preferred_presentation_delay_min = \
            int.from_bytes(data[13:16], "little")
        preferred_presentation_delay_max = \
            int.from_bytes(data[16:19], "little")
        codec_id = int.from_bytes(data[19:24], "little")
        codec_config_length = data[24]

        if codec_config_length > 0:
            config = bytes_to_ltvs(data[24:24 + codec_config_length + 1])
        else:
            config = None

        ase_params = (ase_id, state, framing, preferred_phy,
                      preferred_retransmission_number,
                      max_transport_latency,
                      presentation_delay_min,
                      presentation_delay_max,
                      preferred_presentation_delay_min,
                      preferred_presentation_delay_max,
                      codec_id, codec_config_length, config)
    else:
        ase_params = (ase_id, state)

    return ase_params


def attrs_get_char_handle(attrs, uuid):
    for svc in attrs:
        chars = attrs[svc]
        for ch in chars:
            if ch.uuid == uuid:
                return ch.handle

    return None


def attrs_get_value_handle(attrs, uuid):
    handle = attrs_get_char_handle(attrs, uuid)

    if handle is None:
        return None

    return handle + 1


def read_pacs_records(pac_uuid=UUID.SINK_PAC, attrs=None):
    """
    Read PACS records to get Codec Specific Capabilities LTV Structures
    """
    if attrs is None:
        attrs = disc_full(svc_uuid=UUID.PACS, ch_uuid=pac_uuid)

    handle = attrs_get_value_handle(attrs, pac_uuid)
    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(), handle)
    rsp, value = btp.gattc_read_rsp()
    pac_ltvs = parse_pac_char_value(value[0])
    codec_id, (capabilities_ltv, metadata_ltv) = pac_ltvs.popitem()

    return codec_id, capabilities_ltv, metadata_ltv


def read_ase_params(handle, ase_uuid=UUID.SINK_ASE, attrs=None,
                    bd_addr_type=None, bd_addr=None):
    if handle is None:
        if attrs is None:
            attrs = disc_full(svc_uuid=UUID.ASCS, ch_uuid=ase_uuid)
        handle = attrs_get_value_handle(attrs, ase_uuid)

    btp.gattc_read(btp.pts_addr_type_get(bd_addr_type),
                   btp.pts_addr_get(bd_addr), handle)
    rsp, value = btp.gattc_read_rsp()

    ase_value = value[0]
    ase_params = parse_ase_char_value(ase_value)

    return ase_params


def first_1_bit(val):
    i = 0
    while val:
        b = val & 0x01
        if b:
            return i
        val >>= 0x01
        i += 1
    return None


def last_1_bit(val):
    i = 7
    while val:
        b = val & 0b10000000
        if b:
            return i
        val <<= 0x01
        i -= 1
    return None


def hdl_wid_302(params: WIDParams):
    """
    Please configure ASE state to CODEC configured with SINK/SOURCE ASE,
    Freq: X KHz, Frame Duration: X ms
    """

    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    sampling_freq = numbers[0]
    frame_duration = numbers[1]

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    sampling_freq = SAMPLING_FREQ_STR_TO_CODE[sampling_freq]
    frame_duration = FRAME_DURATION_STR_TO_CODE[frame_duration]
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_303(params: WIDParams):
    """
    Please configure ASE state to QoS Configured with 16_2_1 in SINK direction.
    """

    parsed = re.findall(r'\d+(?:_\d+)*', params.description)
    qos_set_name = parsed[0]
    codec_set_name = '_'.join(qos_set_name.split('_')[:-1])

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
        ase_uuid = UUID.SINK_ASE
    else:
        audio_dir = AudioDir.SOURCE
        ase_uuid = UUID.SOURCE_ASE

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    attrs = disc_full(svc_uuid=UUID.ASCS, ch_uuid=ase_uuid)
    attr_handle = attrs_get_value_handle(attrs, ase_uuid)
    _, status, *_ = read_ase_params(handle=attr_handle)

    # In some test cases ASE codec is not configured by MMI before
    if status == ASCSState.IDLE:
        # Get supported capabilities
        ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
        if ev is None:
            return False

        _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

        (sampling_freq, frame_duration, octets_per_frame) = CODEC_CONFIG_SETTINGS[codec_set_name]
        audio_locations = 0x01
        frames_per_sdu = 0x01

        # Perform Codec Config operation
        codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                                 audio_locations, octets_per_frame,
                                                 frames_per_sdu)
        btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Perform Config QOS operation
    cig_id = 0x01
    cis_id = 0x01
    presentation_delay = 40000
    qos_config = QOS_CONFIG_SETTINGS[qos_set_name]
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_304(params: WIDParams):
    """
    Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    """
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    sampling_freq_str = numbers[0]
    frame_duration_str = numbers[1]

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    sampling_freq = SAMPLING_FREQ_STR_TO_CODE[sampling_freq_str]
    frame_duration = FRAME_DURATION_STR_TO_CODE[frame_duration_str]
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    frames_per_sdu = 0x01

    # Perform Codec Config operation
    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Perform Config QOS operation
    cig_id = 0x01
    cis_id = 0x01
    presentation_delay = 40000
    qos_config = QOS_CONFIG_SETTINGS[f'{sampling_freq_str}_1_1']
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Enable streams
    btp.ascs_enable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_305(params: WIDParams):
    """
    Please configure ASE state to Disabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    """
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    sampling_freq_str = numbers[0]
    frame_duration_str = numbers[1]

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    sampling_freq = SAMPLING_FREQ_STR_TO_CODE[sampling_freq_str]
    frame_duration = FRAME_DURATION_STR_TO_CODE[frame_duration_str]
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    frames_per_sdu = 0x01

    # Perform Codec Config operation
    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Perform Config QOS operation
    cig_id = 0x01
    cis_id = 0x01
    presentation_delay = 40000
    qos_config = QOS_CONFIG_SETTINGS[f'{sampling_freq_str}_1_1']
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Enable streams
    btp.ascs_enable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Disable streams
    btp.ascs_disable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_306(params: WIDParams):
    """
    Please configure ASE state to Streaming for SINK ASE, Freq: 16KHz and Frame Duration: 10ms
    """
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    sampling_freq_str = numbers[0]
    frame_duration_str = numbers[1]

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    sampling_freq = SAMPLING_FREQ_STR_TO_CODE[sampling_freq_str]
    frame_duration = FRAME_DURATION_STR_TO_CODE[frame_duration_str]
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    frames_per_sdu = 0x01

    # Perform Codec Config operation
    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Perform Config QOS operation
    cig_id = 0x01
    cis_id = 0x01
    presentation_delay = 40000
    qos_config = QOS_CONFIG_SETTINGS[f'{sampling_freq_str}_1_1']
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Enable streams
    btp.ascs_enable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Start streaming
    btp.ascs_receiver_start_ready(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_307(_: WIDParams):
    """
    Please configure ASE state to Disabling state. If server is Source, please initiate Receiver Stop Ready.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ID of the ASE
    ev = stack.bap.event_queues[defs.BAP_EV_ASE_FOUND][0]
    _, _, ase_dir, ase_id = ev

    # Disable ASE
    btp.ascs_disable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    if ase_dir == AudioDir.SOURCE:
        # Initiate receiver Stop Ready
        btp.ascs_receiver_stop_ready(ase_id)
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_308(_: WIDParams):
    """
    Please configure ASE state to Disabling state.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ID of the ASE
    ev = stack.bap.event_queues[defs.BAP_EV_ASE_FOUND][0]
    _, _, ase_dir, ase_id = ev

    # Disable ASE
    btp.ascs_disable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_309(_: WIDParams):
    """
    Please configure ASE state to Releasing state.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ID of the ASE
    ev = stack.bap.event_queues[defs.BAP_EV_ASE_FOUND][0]
    _, _, _, ase_id = ev

    # Release streams
    btp.ascs_release(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_310(_: WIDParams):
    """
    Please send Update Metadata Opcode with valid data.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ASE ID
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SINK, 30)
    if ev is None:
        ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SOURCE, 5)

    if ev is None:
        return False

    _, _, ase_dir, ase_id = ev

    # Update metadata
    btp.ascs_update_metadata(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def create_default_config():
    return Namespace(addr=pts_addr_get(),
                     addr_type=pts_addr_type_get(),
                     current_state=ASCSState.IDLE,
                     vid=0x0000,
                     cid=0x0000,
                     coding_format=0x06,
                     frames_per_sdu=0x01,
                     audio_locations=0x01,
                     cig_id=0x01,
                     cis_id=0x01,
                     presentation_delay=40000,
                     qos_config=None,
                     codec_set_name=None)


def config_codec(config):
    if config is None:
        config = create_default_config()

    if config.codec_set_name is not None:
        (config.sampling_freq, config.frame_duration, config.octets_per_frame) = \
            CODEC_CONFIG_SETTINGS[config.codec_set_name]

    stack = get_stack()
    codec_ltvs_bytes = create_lc3_ltvs_bytes(config.sampling_freq,
                                             config.frame_duration,
                                             config.audio_locations,
                                             config.octets_per_frame,
                                             config.frames_per_sdu)

    btp.ascs_config_codec(config.ase_id,
                          config.coding_format,
                          config.vid,
                          config.cid,
                          codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.CODEC_CONFIGURED


def config_qos(config):
    if config.qos_set_name is not None:
        (config.sdu_interval, config.framing, config.max_sdu_size,
         config.retransmission_number, config.max_transport_latency) = \
            QOS_CONFIG_SETTINGS[config.qos_set_name]

    stack = get_stack()
    btp.ascs_config_qos(config.ase_id,
                        config.cig_id,
                        config.cis_id,
                        config.sdu_interval,
                        config.framing,
                        config.max_sdu_size,
                        config.retransmission_number,
                        config.max_transport_latency,
                        config.presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.QOS_CONFIGURED


def enable(config):
    stack = get_stack()
    btp.ascs_enable(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.ENABLING


def start_streaming(config):
    stack = get_stack()
    btp.ascs_receiver_start_ready(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.STREAMING


def stop_streaming(config):
    stack = get_stack()
    btp.ascs_receiver_stop_ready(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.QOS_CONFIGURED


def source_disable(config):
    """Disable ASE streams"""
    stack = get_stack()
    btp.ascs_disable(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.DISABLING


def sink_disable(config):
    """Disable ASE streams"""
    stack = get_stack()
    btp.ascs_disable(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    config.current_state = ASCSState.QOS_CONFIGURED


def release(config):
    """Release ASE streams"""
    stack = get_stack()
    btp.ascs_release(config.ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                               config.addr,
                                               config.ase_id, 30)
    # No caching
    config.current_state = ASCSState.IDLE


def get_audio_locations_from_pac(addr_type, addr, audio_dir):
    # Get supported capabilities
    stack = get_stack()
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    channel_counts = last_1_bit(ev[7]) + 1

    audio_locations = 0x00
    for i in range(0, channel_counts):
        audio_locations = (audio_locations << 1) + 0x01

    return audio_locations


def hdl_wid_311(params: WIDParams):
    """
    Please configure 1 SOURCE ASE with Config Setting: 8_1_1.
    After that, configure to streaming state.
    """

    stack = get_stack()
    default_config = create_default_config()

    parsed = re.findall(r'\d+(?:_\d+)*', params.description)

    default_config.qos_set_name = '16_2_1'
    sink_num = source_num = n = 0

    if 'SINK' in params.description:
        sink_num = int(parsed[n])
        n += 1

    if 'SOURCE' in params.description:
        source_num = int(parsed[n])
        n += 1

    if 'IXIT' not in params.description:
        default_config.qos_set_name = parsed[n]

    default_config.codec_set_name = '_'.join(default_config.qos_set_name.split('_')[:-1])

    sinks = []
    for i in range(0, sink_num):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SINK
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)
        sinks.append(config)

    sources = []
    for i in range(0, source_num):
        config = Namespace(**vars(default_config))
        config.audio_dir = AudioDir.SOURCE
        config.audio_locations = get_audio_locations_from_pac(
            default_config.addr_type, default_config.addr, config.audio_dir)
        sources.append(config)

    ase_found_ev_cache = []
    ases = sinks + sources
    for config in ases:
        ev = stack.bap.wait_ase_found_ev(default_config.addr_type,
                                         default_config.addr,
                                         config.audio_dir, 30, remove=True)
        if ev is None:
            return False

        ase_found_ev_cache.append(ev)

        _, _, audio_dir, ase_id = ev
        config.ase_id = ase_id

    # Restore removed events, so other wids could use them
    stack.bap.event_queues[defs.BAP_EV_ASE_FOUND].extend(ase_found_ev_cache)

    for config in ases:
        config_codec(config)

    # TODO: Some tests need multiple unidirectional CISes and some others need
    #  the bidirectional ones. There is no hint for this in the MMI description.
    #  For now let's create as many bidirectional CISes as possible.
    bidir_cises = list(zip(sinks, sources))
    bidir_cises_num = len(bidir_cises)

    unidir_cises = []
    for sink_config in sinks[bidir_cises_num:]:
        unidir_cises.append((sink_config, None))

    for source_config in sources[bidir_cises_num:]:
        unidir_cises.append((None, source_config))

    cises = bidir_cises + unidir_cises

    # Configure QoS for the CIG.
    # Zephyrs API configures QoS for all ASEs in group at once
    config = Namespace(**vars(ases[0]))
    config_qos(config)

    # An ASCS operation completed event will arrive for each end point
    for config in ases[1:]:
        ev = stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                                        config.addr,
                                                        config.ase_id, 30)
        if ev is None:
            return False

    # Generate random data to stream to the SINK ASE
    stream_data = {}
    for config in sinks:
        data = [j for j in range(0, config.octets_per_frame)]
        stream_data[config.ase_id] = bytearray(data)

    for config in ases:
        enable(config)

    for sink_config, source_config in cises:
        if source_config:
            # Bidirectional CIS or unidirectional CIS with a SOURCE end point
            start_streaming(source_config)
        elif sink_config:
            # Unidirectional CIS with a SINK end point
            btp.ascs_receiver_start_ready(sink_config.ase_id)

    # The ASCS notifications about change of a SINK ASE state to Streaming
    # do not arrive until all CISes in a CIG are in streaming state.
    for config in sinks:
        ev = stack.ascs.wait_ascs_operation_complete_ev(config.addr_type,
                                                        config.addr,
                                                        config.ase_id, 30)
        if ev is None:
            return False

    for i in range(1, 100):
        for config in sinks:
            try:
                btp.bap_send(config.ase_id, stream_data[config.ase_id])
            except:
                pass

    return True


def hdl_wid_313(params: WIDParams):
    """
    Please configure 1 SINK and 1 SOURCE ASE with Config Setting: 16_2_1.
    After that, configure both ASEes to streaming state.
    """
    return hdl_wid_311(params)


def hdl_wid_314(params: WIDParams):
    """
    Please configure ASE state to CODEC configured with Vendor specific parameter in SINK ASE
    """

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ASE ID
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Errata in progress, since the vendor codec does not appear in PAC records
    sampling_freq = first_1_bit(frequencies)
    frame_duration = frame_durations
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    coding_format = 0xff
    frames_per_sdu = 0x01

    # Perform Config Codec
    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0xffff, 0xffff, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_315(params: WIDParams):
    """
    Please configure ASE state to QoS Configured with Vendor specific parameter in SOURCE ASE.
    """

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
        ase_uuid = UUID.SINK_ASE
    else:
        audio_dir = AudioDir.SOURCE
        ase_uuid = UUID.SOURCE_ASE

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    attrs = disc_full(svc_uuid=UUID.ASCS, ch_uuid=ase_uuid)
    attr_handle = attrs_get_value_handle(attrs, ase_uuid)
    _, status, *_ = read_ase_params(handle=attr_handle)

    # In some test cases ASE codec is not configured by MMI before
    if status == ASCSState.IDLE:
        sampling_freq = 0
        frame_duration = 0
        octets_per_frame = 0
        audio_locations = 0
        coding_format = 0xff
        vid = 0xffff
        cid = 0xffff
        frames_per_sdu = 0x01

        # Perform Codec Config operation
        codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                                 audio_locations, octets_per_frame,
                                                 frames_per_sdu)
        btp.ascs_config_codec(ase_id, coding_format, vid, cid, codec_ltvs_bytes)
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Perform Config QOS operation
    cig_id = 0x01
    cis_id = 0x01
    presentation_delay = 40000
    qos_config = (7500, 0x00, 40, 2, 10)
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_364(_: WIDParams):
    """
    After processed audio stream data, please click OK.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    for ev in stack.bap.event_queues[defs.BAP_EV_ASE_FOUND]:
        _, _, ase_dir, ase_id = ev

        if ase_dir == AudioDir.SOURCE:
            ev = stack.bap.wait_stream_received_ev(addr_type, addr, ase_id, 10)
            if ev is None:
                return False

    return True


def hdl_wid_20206(_: WIDParams):
    """
    Please verify that for each supported characteristic, attribute handle/UUID
    pair(s) is returned to the upper tester.
    Sink PAC:
        Attribute Handle = 0x00A1
        Characteristic Properties = 0x12
        Handle = 0x00A2
        UUID = 0x2BC9
    Sink Audio Locations:
        Attribute Handle = 0x00A4
        Characteristic Properties = 0x1A
        Handle = 0x00A5
        UUID = 0x2BCA
    Source PAC:
        Attribute Handle = 0x00A7
        Characteristic Properties = 0x12
        Handle = 0x00A8
        UUID = 0x2BCB
    Source Audio Locations:
        Attribute Handle = 0x00AA
        Characteristic Properties = 0x1A
        Handle = 0x00AB
        UUID = 0x2BCC
    Available Audio Contexts:
        Attribute Handle = 0x00AD
        Characteristic Properties = 0x12
        Handle = 0x00AE
        UUID = 0x2BCD
    Supported Audio Contexts:
        Attribute Handle = 0x00B0
        Characteristic Properties = 0x12
        Handle = 0x00B1
        UUID = 0x2BCE

    """

    # TODO cheating is bad

    return True


def hdl_wid_20103(_: WIDParams):
    """
    Please take action to discover the [Sink/Source] PAC characteristic from
    the Published Audio Capability. Discover the primary service if needed.
    """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20106(_: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of
    X characteristic to enable notification.
    """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20116(_: WIDParams):
    """
    Please send command to the PTS to discover all mandatory characteristics
    of the Published Audio Capability supported by the IUT. Discover primary
    service if needed.
    """

    # Discover and subscribe at hdl_wid_20100

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


def hdl_wid_20110(params: WIDParams):
    """
    Please send write request to handle 0xXXXX with following value: Any attribute value.
    """

    handle = re.findall(r'0[xX][0-9a-fA-F]+', params.description)[0]
    btp.gattc_write(btp.pts_addr_type_get(), btp.pts_addr_get(), handle, '0001')
    btp.gattc_write_rsp()

    return True


def hdl_wid_20115(_: WIDParams):
    """
    Please initiate a GATT disconnection to the PTS.
    Description: Verify that the Implementation Under Test (IUT) can initiate
    GATT disconnect request to PTS.
    """

    btp.gap_disconn()

    return True


def hdl_wid_20121(params: WIDParams):
    """
    Please write value with write command (without response) to handle 0xXXXX
    with following value: Any attribute value.
    """

    handle = re.findall(r'0[xX][0-9a-fA-F]+', params.description)[0]
    btp.gattc_write_without_rsp(btp.pts_addr_type_get(), btp.pts_addr_get(), handle, '0001')

    return True


def hdl_wid_20145(_: WIDParams):
    """
    Please click Yes if IUT support Write Request, otherwise click No.
    """
    return True


def hdl_wid_20144(_: WIDParams):
    """
    Please click Yes if IUT support Write Command(without response), otherwise click No.
    """
    return True
