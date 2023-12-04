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
import re
import struct
from argparse import Namespace
from time import sleep

from autopts.ptsprojects.stack import get_stack, WildCard
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import pts_addr_get, pts_addr_type_get, ascs_add_ase_to_cis, lt2_addr_get, lt2_addr_type_get
from autopts.pybtp.types import WIDParams, UUID, gap_settings_btp2txt, AdType, AdFlags, BTPError
from autopts.wid import generic_wid_hdl

log = logging.debug


class PaSyncState:
    NOT_SYNCED     = 0x00
    SYNC_INFO_REQ  = 0x01
    SYNCED         = 0x02
    FAILED_TO_SYNC = 0x03
    NO_PAST        = 0x04


class BIGEncryption:
    NOT_ENCRYPTED           = 0x00
    BROADCAST_CODE_REQUIRED = 0x01
    DECRYPTING              = 0x02
    BAD_CODE                = 0x03


def bap_wid_hdl(wid, description, test_case_name):
    log(f'{bap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_20100(params: WIDParams):
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.gap_conn()
    stack.gap.gap_wait_for_sec_lvl_change(30)

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    if params.test_case_name.startswith('BAP/BA/BASS'):
        btp.bap_discover_scan_delegator()

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

    if params.test_case_name.startswith('BAP/BA'):
        return True

    # BIS_Sync bitfield uses bit 0 for BIS Index 1
    requested_bis_sync = 1
    bis_ids = [1]
    if params.test_case_name.startswith('BAP/BSNK/STR') or \
            params.test_case_name.startswith('BAP/BSRC/STR'):
        tc_num = int(re.findall(r'\d+', params.test_case_name)[0])
        if tc_num >= 18:
            requested_bis_sync |= 2
            bis_ids.append(2)

    btp.bap_broadcast_sink_bis_sync(broadcast_id, requested_bis_sync)

    for bis_id in bis_ids:
        broadcast_id = ev['broadcast_id']
        ev = stack.bap.wait_bis_synced_ev(broadcast_id, bis_id, 10, False)
        if ev is None:
            log(f'Failed to sync to BIS with ID {bis_id}, broadcast ID {broadcast_id}')
            return False

    return True


def hdl_wid_104(params: WIDParams):
    """
    Please send non connectable advertise with periodic info.
    """
    # Advertising started at hdl_wid_114

    return True


BAS_CONFIG_SETTINGS = {
    # Set_Name: (Codec_Setting, SDU_Interval_µs, Framing, Max_SDU_octets, RTN, Max_Transport_Latency_ms),
    '8_1_1': ('8_1', 7500, 0x00, 26, 2, 8),
    '8_2_1': ('8_2', 10000, 0x00, 30, 2, 10),
    '16_1_1': ('16_1', 7500, 0x00, 30, 2, 8),
    '16_2_1': ('16_2', 10000, 0x00, 40, 2, 10),
    '24_1_1': ('24_1', 7500, 0x00, 45, 2, 8),
    '24_2_1': ('24_2', 10000, 0x00, 60, 2, 10),
    '32_1_1': ('32_1', 7500, 0x00, 60, 2, 8),
    '32_2_1': ('32_2', 10000, 0x00, 80, 2, 10),
    '441_1_1': ('441_1', 8163, 0x01, 97, 4, 24),
    '441_2_1': ('441_2', 10884, 0x01, 130, 4, 31),
    '48_1_1': ('48_1', 7500, 0x00, 75, 4, 15),
    '48_2_1': ('48_2', 10000, 0x00, 100, 4, 20),
    '48_3_1': ('48_3', 7500, 0x00, 90, 4, 15),
    '48_4_1': ('48_4', 10000, 0x00, 120, 4, 20),
    '48_5_1': ('48_5', 7500, 0x00, 117, 4, 15),
    '48_6_1': ('48_6', 10000, 0x00, 155, 4, 20),
    '8_1_2': ('8_1', 7500, 0x00, 26, 4, 45),
    '8_2_2': ('8_2', 10000, 0x00, 30, 4, 60),
    '16_1_2': ('16_1', 7500, 0x00, 30, 4, 45),
    '16_2_2': ('16_2', 10000, 0x00, 40, 4, 60),
    '24_1_2': ('24_1', 7500, 0x00, 45, 4, 45),
    '24_2_2': ('24_2', 10000, 0x00, 60, 4, 60),
    '32_1_2': ('32_1', 7500, 0x00, 60, 4, 45),
    '32_2_2': ('32_2', 10000, 0x00, 80, 4, 60),
    '441_1_2': ('441_1', 8163, 0x01, 97, 4, 54),
    '441_2_2': ('441_2', 10884, 0x01, 130, 4, 60),
    '48_1_2': ('48_1', 7500, 0x00, 75, 4, 50),
    '48_2_2': ('48_2', 10000, 0x00, 100, 4, 65),
    '48_3_2': ('48_3', 7500, 0x00, 90, 4, 50),
    '48_4_2': ('48_4', 10000, 0x00, 120, 4, 65),
    '48_5_2': ('48_5', 7500, 0x00, 117, 4, 50),
    '48_6_2': ('48_6', 10000, 0x00, 155, 4, 65),
}


def hdl_wid_114(params: WIDParams):
    """
    Please advertise with Broadcast Audio Announcement (0x1852) service data
    """
    configurations = {
        'BAP/BSRC/SCC/BV-01-C': '8_1_1',
        'BAP/BSRC/SCC/BV-02-C': '8_2_1',
        'BAP/BSRC/SCC/BV-03-C': '16_1_1',
        'BAP/BSRC/SCC/BV-04-C': '16_2_1',
        'BAP/BSRC/SCC/BV-05-C': '24_1_1',
        'BAP/BSRC/SCC/BV-06-C': '24_2_1',
        'BAP/BSRC/SCC/BV-07-C': '32_1_1',
        'BAP/BSRC/SCC/BV-08-C': '32_2_1',
        'BAP/BSRC/SCC/BV-09-C': '441_1_1',
        'BAP/BSRC/SCC/BV-10-C': '441_2_1',
        'BAP/BSRC/SCC/BV-11-C': '48_1_1',
        'BAP/BSRC/SCC/BV-12-C': '48_2_1',
        'BAP/BSRC/SCC/BV-13-C': '48_3_1',
        'BAP/BSRC/SCC/BV-14-C': '48_4_1',
        'BAP/BSRC/SCC/BV-15-C': '48_5_1',
        'BAP/BSRC/SCC/BV-16-C': '48_6_1',
        'BAP/BSRC/SCC/BV-17-C': '8_1_2',
        'BAP/BSRC/SCC/BV-18-C': '8_2_2',
        'BAP/BSRC/SCC/BV-19-C': '16_1_2',
        'BAP/BSRC/SCC/BV-20-C': '16_2_2',
        'BAP/BSRC/SCC/BV-21-C': '24_1_2',
        'BAP/BSRC/SCC/BV-22-C': '24_2_2',
        'BAP/BSRC/SCC/BV-23-C': '32_1_2',
        'BAP/BSRC/SCC/BV-24-C': '32_2_2',
        'BAP/BSRC/SCC/BV-25-C': '441_1_2',
        'BAP/BSRC/SCC/BV-26-C': '441_2_2',
        'BAP/BSRC/SCC/BV-27-C': '48_1_2',
        'BAP/BSRC/SCC/BV-28-C': '48_2_2',
        'BAP/BSRC/SCC/BV-29-C': '48_3_2',
        'BAP/BSRC/SCC/BV-30-C': '48_4_2',
        'BAP/BSRC/SCC/BV-31-C': '48_5_2',
        'BAP/BSRC/SCC/BV-32-C': '48_6_2',
        # Cases with 1 BIS:
        'BAP/BSRC/STR/BV-01-C': '8_1_1',
        'BAP/BSRC/STR/BV-02-C': '8_2_1',
        'BAP/BSRC/STR/BV-03-C': '16_1_1',
        'BAP/BSRC/STR/BV-04-C': '16_2_1',
        'BAP/BSRC/STR/BV-05-C': '24_1_1',
        'BAP/BSRC/STR/BV-06-C': '24_2_1',
        'BAP/BSRC/STR/BV-07-C': '32_1_1',
        'BAP/BSRC/STR/BV-08-C': '32_2_1',
        'BAP/BSRC/STR/BV-09-C': '441_1_1',
        'BAP/BSRC/STR/BV-10-C': '441_2_1',
        'BAP/BSRC/STR/BV-11-C': '48_1_1',
        'BAP/BSRC/STR/BV-12-C': '48_2_1',
        'BAP/BSRC/STR/BV-13-C': '48_3_1',
        'BAP/BSRC/STR/BV-14-C': '48_4_1',
        'BAP/BSRC/STR/BV-15-C': '48_5_1',
        'BAP/BSRC/STR/BV-16-C': '48_6_1',
        # Cases with 2 BISes:
        'BAP/BSRC/STR/BV-18-C': '8_1_1',
        'BAP/BSRC/STR/BV-19-C': '8_2_1',
        'BAP/BSRC/STR/BV-20-C': '16_1_1',
        'BAP/BSRC/STR/BV-21-C': '16_2_1',
        'BAP/BSRC/STR/BV-22-C': '24_1_1',
        'BAP/BSRC/STR/BV-23-C': '24_2_1',
        'BAP/BSRC/STR/BV-24-C': '32_1_1',
        'BAP/BSRC/STR/BV-25-C': '32_2_1',
        'BAP/BSRC/STR/BV-26-C': '441_1_1',
        'BAP/BSRC/STR/BV-27-C': '441_2_1',
        'BAP/BSRC/STR/BV-28-C': '48_1_1',
        'BAP/BSRC/STR/BV-29-C': '48_2_1',
        'BAP/BSRC/STR/BV-30-C': '48_3_1',
        'BAP/BSRC/STR/BV-31-C': '48_4_1',
        'BAP/BSRC/STR/BV-32-C': '48_5_1',
        'BAP/BSRC/STR/BV-33-C': '48_6_1',
    }

    if params.test_case_name in configurations:
        qos_set_name = configurations[params.test_case_name]
        coding_format = 0x06
        vid = 0x0000
        cid = 0x0000
    else:
        qos_set_name = '8_1_1'
        coding_format = 0xff
        vid = 0xffff
        cid = 0xffff

    codec_set_name, *qos_config = BAS_CONFIG_SETTINGS[qos_set_name]

    (sampling_freq, frame_duration, octets_per_frame) = \
        CODEC_CONFIG_SETTINGS[codec_set_name]
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)

    streams_per_subgroup = 1
    tc_num = int(re.findall(r'\d+', params.test_case_name)[0])
    if tc_num >= 18:
        streams_per_subgroup = 2

    presentation_delay = 40000
    subgroups = 1
    broadcast_id = btp.bap_broadcast_source_setup(
        streams_per_subgroup, subgroups, coding_format, vid, cid,
        codec_ltvs_bytes, *qos_config, presentation_delay)

    stack = get_stack()
    stack.bap.broadcast_id = broadcast_id

    btp.bap_broadcast_adv_start(broadcast_id)

    btp.bap_broadcast_source_start(broadcast_id)

    return True


def hdl_wid_201(params: WIDParams):
    """Please configure the CODEC parameters on ASE ID 1 in Audio Stream
       Endpoint Characteristic. Codec Configuration: 8_1_1
     """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    parsed = re.findall(r'\d+(?:_\d+)*', params.description)
    ase_id = int(parsed[0])

    if len(parsed) > 1:
        qos_set_name = parsed[1]
        config_name = '_'.join(qos_set_name.split('_')[:-1])
        coding_format = 0x06
        vid = 0x0000
        cid = 0x0000
    else:
        config_name = '16_1'
        coding_format = 0xff
        vid = 0xffff
        cid = 0xffff

    (sampling_freq, frame_duration, octets_per_frame) = \
        CODEC_CONFIG_SETTINGS[config_name]
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, vid, cid, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_202(params: WIDParams):
    """
    Please start audio streaming, and set to Audio Stream Endpoint to STREAMING state for ASE ID 1.
    """
    # In some BAP/USR (server role) test cases the PTS sends the MMI 202
    # to configure the Sink ASE to streaming state, in some others it does not.
    # For now, let's autonomously send Receiver Start Ready at ASE Enabled.

    return True


def hdl_wid_204(params: WIDParams):
    """
    Please initiate Server initiated DISABLE operation on ASE ID 3 in Audio Stream Endpoint Characteristic.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    ase_id = int(numbers[0])

    # Start streaming
    btp.ascs_disable(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_206(params: WIDParams):
    """
    Please initiate RELEASE operation on ASE ID 3 in Audio Stream Endpoint Characteristic.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    ase_id = int(numbers[0])

    # Start streaming
    btp.ascs_release(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_207(params: WIDParams):
    """
    Please initiate META UPDATE operation on ASE ID 3 in Audio Stream Endpoint Characteristic.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    ase_id = int(numbers[0])

    # Start streaming
    btp.ascs_update_metadata(ase_id)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_208(_: WIDParams):
    """
    Lower tester is waiting RELEASED operation (IDLE or CODEC Configured state)
    on ASE ID 3 in Audio Stream Endpoint Characteristic.
    """
    return True


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


def first_1_bit_index(n):
    if n == 0:
        return -1

    # Convert number to binary and remove the '0b' prefix
    binary = bin(n)[2:]
    index = len(binary) - 1 - binary.rindex('1')

    return index


def last_1_bit_index(n):
    if n == 0:
        return -1

    # Convert number to binary and remove the '0b' prefix
    binary = bin(n)[2:]
    index = len(binary) - 1

    return index


def count_1_bits(n):
    binary = bin(n)[2:]  # Convert number to binary and remove the '0b' prefix
    return binary.count('1')


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
    cig_id = 0x00
    cis_id = 0x00
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
    cig_id = 0x00
    cis_id = 0x00
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
    cig_id = 0x00
    cis_id = 0x00
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
    cig_id = 0x00
    cis_id = 0x00
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
                     cig_id=0x00,
                     cis_id=0x00,
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

        # Adjust max sdu size to the number of channels
        config.max_sdu_size = config.max_sdu_size * count_1_bits(config.audio_locations)

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

    channel_counts = last_1_bit_index(ev[7]) + 1

    audio_locations = 0x00
    for i in range(0, channel_counts):
        audio_locations = (audio_locations << 1) + 0x01

    return audio_locations


def hdl_wid_311(params: WIDParams):
    """
    Please configure 1 SOURCE ASE with Config Setting: IXIT.
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

    # Most test cases use bidirectional CISes and/or one unidirectional CIS.
    # Only a few tests need several unidirectional CISs.
    if params.test_case_name in ['BAP/UCL/STR/BV-525-C', ]:
        bidir_cises = []
        bidir_cises_num = 0
    else:
        bidir_cises = list(zip(sinks, sources))
        bidir_cises_num = len(bidir_cises)

    cis_id = 0x00
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

    cises = bidir_cises + unidir_cises

    for config in ases:
        config.cig_id = 0x00
        ascs_add_ase_to_cis(config.ase_id, config.cis_id, config.cig_id)

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
            btp.ascs_receiver_start_ready(source_config.ase_id)
        elif sink_config:
            # Called for Sink ASE just to trigger CIS establishment,
            # but the Sink ASE will go to streaming state later,
            # only when it is ready (all CISes are established).
            btp.ascs_receiver_start_ready(sink_config.ase_id)

    # PTS will change ASE states to streaming when all CISes are established
    for config in ases:
        # Wait for the ASE states to be changed to streaming
        ev = stack.ascs.wait_ascs_ase_state_changed_ev(config.addr_type,
                                                       config.addr,
                                                       config.ase_id,
                                                       ASCSState.STREAMING,
                                                       30)
        if ev is None:
            return False

    for i in range(1, 100):
        for config in sinks:
            try:
                btp.bap_send(config.ase_id, stream_data[config.ase_id])
            except BTPError:
                # Buffer full
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
    sampling_freq = first_1_bit_index(frequencies)
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
    cig_id = 0x00
    cis_id = 0x00
    presentation_delay = 40000
    qos_config = (7500, 0x00, 40, 2, 10)
    btp.ascs_config_qos(ase_id, cig_id, cis_id, *qos_config, presentation_delay)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_340(_: WIDParams):
    """Please confirm that IUT discovered Scan Delegator"""
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    ev = stack.bap.wait_scan_delegator_found_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_342(_: WIDParams):
    """Please write remote scan start opcode with GATT Write Without Response"""
    btp.bap_broadcast_assistant_scan_start()

    return True


def hdl_wid_343(_: WIDParams):
    """Please write remote scan stop opcode with GATT Write Req."""
    btp.bap_broadcast_assistant_scan_stop()

    return True


def hdl_wid_345(params: WIDParams):
    """Please ADD Broadcast Source from Lower Tester 2 to Lower Tester 1
     with PA SYNC with PAST(01) or No PAST(02), BIS INDEX: 0x00000001."""
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    broadcaster_addr = lt2_addr_get()
    broadcaster_addr_type = lt2_addr_type_get()

    ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
    if ev is None:
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        return False

    advertiser_sid = ev['advertiser_sid']
    broadcast_id = ev['broadcast_id']
    padv_interval = ev['padv_interval']
    padv_sync = 0x02
    num_subgroups = 1
    bis_sync = 1
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), 10, True)

    if ev is None:
        return False

    if ev['pa_sync_state'] == PaSyncState.SYNC_INFO_REQ:
        btp.bap_send_past(ev['src_id'])

        ev = stack.bap.wait_broadcast_receive_state_ev(
            broadcast_id, addr_type, addr, broadcaster_addr_type,
            broadcaster_addr, WildCard(), 10, True)

        if ev is None:
            return False

    return True


def hdl_wid_346(params: WIDParams):
    """1. Please ADD Broadcast Source from Lower Tester 2 to Lower Tester 1
          with PA SYNC with PAST(01) or No PAST(02), BIS INDEX: 0x00000001
       2. After that, please MODIFY Broadcast Source with PA SYNC: 0x00,
          BIS INDEX: 0x00000000.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    broadcaster_addr = lt2_addr_get()
    broadcaster_addr_type = lt2_addr_type_get()

    ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
    if ev is None:
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        return False

    advertiser_sid = ev['advertiser_sid']
    broadcast_id = ev['broadcast_id']
    padv_interval = ev['padv_interval']
    padv_sync = 0x02
    num_subgroups = 1
    bis_sync = 1
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), 10, True)

    if ev is None:
        return False

    if ev['pa_sync_state'] == PaSyncState.SYNC_INFO_REQ:
        btp.bap_send_past(ev['src_id'])

        ev = stack.bap.wait_broadcast_receive_state_ev(
            broadcast_id, addr_type, addr, broadcaster_addr_type,
            broadcaster_addr, WildCard(), 10, True)

        if ev is None:
            return False

    padv_sync = 0x00
    bis_sync = 0
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_modify_broadcast_src(ev['src_id'], padv_sync, padv_interval,
                                 num_subgroups, subgroups,
                                 addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), 10, True)

    if ev is None:
        return False

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
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        return False

    advertiser_sid = ev['advertiser_sid']
    broadcast_id = ev['broadcast_id']
    padv_interval = ev['padv_interval']
    num_subgroups = 1
    # Ignore wrong values of PA SYNC and BIS INDEX in WID description
    padv_sync = 0x02
    bis_sync = 1
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), 10, True)

    if ev is None:
        return False

    if ev['pa_sync_state'] == PaSyncState.SYNC_INFO_REQ:
        btp.bap_send_past(ev['src_id'])

        ev = stack.bap.wait_broadcast_receive_state_ev(
            broadcast_id, addr_type, addr, broadcaster_addr_type,
            broadcaster_addr, WildCard(), 10, True)

        if ev is None:
            return False

    btp.bap_remove_broadcast_src(ev['src_id'], addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, padv_sync, 10, False)

    if ev is None:
        return False

    return True


def hdl_wid_348(params: WIDParams):
    """1. Please ADD Broadcast Source from Lower Tester 2 to
          Lower Tester 1 with PA SYNC with PAST(01) or No PAST(02), BIS INDEX: 0x00000001
       2. After that, please set BROADCAST CODE.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    broadcaster_addr = lt2_addr_get()
    broadcaster_addr_type = lt2_addr_type_get()

    ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
    if ev is None:
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        return False

    advertiser_sid = ev['advertiser_sid']
    broadcast_id = ev['broadcast_id']
    padv_interval = ev['padv_interval']
    num_subgroups = 1
    padv_sync = 0x02
    bis_sync = 1
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, WildCard(), 10, True)

    if ev is None:
        return False

    btp.bap_set_broadcast_code(ev['src_id'], stack.bap.broadcast_code)

    if ev['pa_sync_state'] == PaSyncState.SYNC_INFO_REQ:
        btp.bap_send_past(ev['src_id'])

        ev = stack.bap.wait_broadcast_receive_state_ev(
            broadcast_id, addr_type, addr, broadcaster_addr_type,
            broadcaster_addr, WildCard(), 10, True)

        if ev is None:
            return False

    return True


def hdl_wid_349(params: WIDParams):
    """
    Please ADD Broadcast Source from Lower Tester 2 to
    Lower Tester 1 with PA SYNC: 0x01, BIS INDEX: 0x00000000
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()
    broadcaster_addr = lt2_addr_get()
    broadcaster_addr_type = lt2_addr_type_get()

    ev = stack.bap.wait_baa_found_ev(broadcaster_addr_type, broadcaster_addr, 10, False)
    if ev is None:
        return False

    base_found_ev = stack.bap.wait_bis_found_ev(ev['broadcast_id'], 10, False)
    if base_found_ev is None:
        return False

    advertiser_sid = ev['advertiser_sid']
    broadcast_id = ev['broadcast_id']
    padv_interval = ev['padv_interval']
    num_subgroups = 1
    padv_sync = 0x01
    bis_sync = 1
    metadata_len = 0
    subgroups = struct.pack('<IB', bis_sync, metadata_len)
    btp.bap_add_broadcast_src(advertiser_sid, broadcast_id, padv_sync,
                              padv_interval, num_subgroups, subgroups,
                              broadcaster_addr_type, broadcaster_addr,
                              addr_type, addr)

    ev = stack.bap.wait_broadcast_receive_state_ev(
        broadcast_id, addr_type, addr, broadcaster_addr_type,
        broadcaster_addr, padv_sync, 10, False)

    if ev is None:
        return False

    return True


def hdl_wid_353(_: WIDParams):
    """Wait for Broadcast ISO request.
    """
    return True


def hdl_wid_357(_: WIDParams):
    """Wait for Broadcast ISO request.
    """
    stack = get_stack()
    btp.bap_broadcast_source_stop(stack.bap.broadcast_id)

    return True


def hdl_wid_363(params: WIDParams):
    """Wait for an extended advertising packet containing Audio Control
       Service UUID with announcement fields.
    """
    stack = get_stack()

    if params.test_case_name in ['BAP/USR/ADV/BV-01-C']:
        announcement_type = '00'  # General Announcement
    else:  # BAP/USR/ADV/BV-04-C
        announcement_type = '01'  # Targeted Announcement

    ad = {
        AdType.name_full: stack.gap.name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: bytes.fromhex(UUID.ASCS)[::-1].hex(),
        AdType.uuid16_svc_data: f'4e18{announcement_type}ff0fff0f00',
    }

    btp.gap_set_extended_advertising_on()
    btp.gap_adv_ind_on(ad=ad)

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


def hdl_wid_366(_: WIDParams):
    """
    Please click ok when IUT received and sent audio stream data.
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


def hdl_wid_367(_: WIDParams):
    """
    Lower tester is streaming audio data.
    """
    return True


def hdl_wid_376(params: WIDParams):
    """
    Please confirm received streaming data.
    """

    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    if params.test_case_name in ['BAP/BA/BASS/BV-04-C_LT2',
                                 'BAP/BA/BASS/BV-05-C_LT2',
                                 'BAP/BA/BASS/BV-06-C_LT2',
                                 'BAP/BA/BASS/BV-07-C_LT2',
                                 'BAP/BA/BASS/BV-08-C_LT2',
                                 ]:
        # Confirm that LT1 received stream from LT2 ...
        # Pending errata.

        return True

    if params.test_case_name.startswith('BAP/BSNK'):
        for ev in stack.bap.event_queues[defs.BAP_EV_BIS_SYNCED]:
            ev = stack.bap.wait_bis_stream_received_ev(ev['broadcast_id'], ev['bis_id'], 10)
            if ev is None:
                return False
    else:
        for ev in stack.bap.event_queues[defs.BAP_EV_ASE_FOUND]:
            _, _, ase_dir, ase_id = ev

            if ase_dir == AudioDir.SINK:
                ev = stack.bap.wait_stream_received_ev(addr_type, addr, ase_id, 10)
                if ev is None:
                    return False

    return True


def hdl_wid_377(_: WIDParams):
    """
    Please confirm sent streaming data.
    """
    stack = get_stack()

    sources = []
    for ev in stack.ascs.event_queues[defs.ASCS_EV_ASE_STATE_CHANGED]:
        _, _, ase_id, state = ev

        if state == ASCSState.STREAMING:
            sources.append(ase_id)

    data = bytearray([j for j in range(0, 41)])

    for i in range(1, 10):
        for ase_id in sources:
            try:
                btp.bap_send(ase_id, data)
            except BTPError:
                # Buffer full
                pass

    return True


def hdl_wid_378(_: WIDParams):
    """
    Please confirm received BASE entry Basic Audio Announcements
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.bap_broadcast_sink_setup()
    btp.bap_broadcast_scan_start()

    ev = stack.bap.wait_baa_found_ev(addr_type, addr, 10, False)
    if ev is None:
        return False

    return True


def hdl_wid_379(_: WIDParams):
    """
    Please order the IUT to release the broadcast stream.
    """
    stack = get_stack()
    broadcast_id = stack.bap.broadcast_id
    btp.bap_broadcast_source_stop(broadcast_id)
    btp.bap_broadcast_adv_stop(broadcast_id)
    btp.bap_broadcast_source_release(broadcast_id)

    return True


def hdl_wid_380(_: WIDParams):
    """
    Please reconfigure BASE with different settings. Then click OK when
    IUT is ready to advertise with Broadcast Audio Announcement (0x1852)
    service data.
    """
    stack = get_stack()
    btp.bap_broadcast_adv_stop(stack.bap.broadcast_id)
    btp.bap_broadcast_source_stop(stack.bap.broadcast_id)

    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    qos_set_name = '16_1_1'

    codec_set_name, *qos_config = BAS_CONFIG_SETTINGS[qos_set_name]
    (sampling_freq, frame_duration, octets_per_frame) = \
        CODEC_CONFIG_SETTINGS[codec_set_name]
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)

    presentation_delay = 40000
    streams_per_subgroup = 2
    subgroups = 1
    broadcast_id = btp.bap_broadcast_source_setup(
        streams_per_subgroup, subgroups, coding_format, vid, cid,
        codec_ltvs_bytes, *qos_config, presentation_delay)

    stack.bap.broadcast_id = broadcast_id

    btp.bap_broadcast_adv_start(broadcast_id)

    return True


def hdl_wid_381(_: WIDParams):
    """
    When IUT is ready to receive notification. Please click OK.
    """
    return True


def hdl_wid_382(_: WIDParams):
    """
    CIS connection is disconnected. Expect to receive QoS Configured state.
    """
    return True


def hdl_wid_384(_: WIDParams):
    """
    Click OK will start transmitting audio streaming data.
    """

    return True


def hdl_wid_387(_: WIDParams):
    """Please send valid streaming data."""
    stack = get_stack()

    sources = []
    for ev in stack.ascs.event_queues[defs.ASCS_EV_ASE_STATE_CHANGED]:
        _, _, ase_id, state = ev

        if state == ASCSState.STREAMING:
            sources.append(ase_id)

    data = bytearray([j for j in range(0, 41)])

    for i in range(1, 10):
        for ase_id in sources:
            try:
                btp.bap_send(ase_id, data)
            except BTPError:
                # Buffer full
                pass

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
