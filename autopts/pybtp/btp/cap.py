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

"""Wrapper around btp messages. The functions are added as needed."""
import binascii
import logging
import struct
from enum import IntEnum

from autopts.pybtp import defs, btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut,\
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.gap import __gap_current_settings_update
from autopts.pybtp.types import addr2btp_ba, BTPError, AdType

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853

CAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_CAP,
                            defs.BTP_CAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_CAP, defs.BTP_CAP_CMD_DISCOVER, CONTROLLER_INDEX),
    'unicast_setup_ase': (defs.BTP_SERVICE_ID_CAP, defs.BTP_CAP_CMD_UNICAST_SETUP_ASE, CONTROLLER_INDEX),
    'unicast_audio_start': (defs.BTP_SERVICE_ID_CAP, defs.BTP_CAP_CMD_UNICAST_AUDIO_START, CONTROLLER_INDEX),
    'unicast_audio_update': (defs.BTP_SERVICE_ID_CAP, defs.BTP_CAP_CMD_UNICAST_AUDIO_UPDATE, CONTROLLER_INDEX),
    'unicast_audio_stop': (defs.BTP_SERVICE_ID_CAP, defs.BTP_CAP_CMD_UNICAST_AUDIO_STOP, CONTROLLER_INDEX),
    'broadcast_source_setup_stream': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_SETUP_STREAM, CONTROLLER_INDEX),
    'broadcast_source_setup_subgroup': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_SETUP_SUBGROUP, CONTROLLER_INDEX),
    'broadcast_source_setup': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_SETUP, CONTROLLER_INDEX),
    'broadcast_source_release': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_RELEASE, CONTROLLER_INDEX),
    'broadcast_adv_start': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_ADV_START, CONTROLLER_INDEX),
    'broadcast_adv_stop': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_ADV_STOP, CONTROLLER_INDEX),
    'broadcast_source_start': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_START, CONTROLLER_INDEX),
    'broadcast_source_stop': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_STOP, CONTROLLER_INDEX),
    'broadcast_source_update': (defs.BTP_SERVICE_ID_CAP,
        defs.BTP_CAP_CMD_BROADCAST_SOURCE_UPDATE, CONTROLLER_INDEX),
}


def announcements(adv_data, rsp_data, targeted, sink_contexts, source_contexts):
    """Setup Announcements"""

    # CAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] = [struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]

    # BAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] += [struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, sink_contexts, source_contexts, 0) ]

    # Generate the Resolvable Set Identifier (RSI)
    rsi = btp.cas_get_member_rsi()
    adv_data[AdType.rsi] = struct.pack('<6B', *rsi)

    stack = get_stack()
    stack.gap.ad = adv_data


def cap_command_rsp_succ(timeout=20.0):
    logging.debug("%s", cap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CAP)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def cap_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{cap_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAP['discover'], data=data)

    cap_command_rsp_succ()


def cap_unicast_audio_start(cig_id, set_type):
    logging.debug(f"{cap_unicast_audio_start.__name__}")

    data = struct.pack('B', cig_id)
    data += struct.pack('B', set_type)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAP['unicast_audio_start'], data=data)

    cap_command_rsp_succ()


def cap_unicast_audio_update(metadata_tuple):
    logging.debug(f"{cap_unicast_audio_update.__name__}")

    data = bytearray()
    stream_count = len(metadata_tuple)
    data += struct.pack('B', stream_count)

    for addr_type, addr, ase_id, metadata in metadata_tuple:
        data += address_to_ba(addr_type, addr)
        data += struct.pack('B', ase_id)

        metadata_len = len(metadata)
        data += struct.pack('B', metadata_len)

        if metadata_len:
            data += metadata

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAP['unicast_audio_update'], data=data)

    cap_command_rsp_succ()


BTP_CAP_UNICAST_AUDIO_STOP_FLAG_RELEASE = 0b00000001

def cap_unicast_audio_stop(cig_id, release):
    logging.debug(f"{cap_unicast_audio_stop.__name__}")

    data = struct.pack('B', cig_id)

    flags = 0x00
    if release:
        flags |= BTP_CAP_UNICAST_AUDIO_STOP_FLAG_RELEASE

    data += struct.pack('?', flags)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAP['unicast_audio_stop'], data=data)

    cap_command_rsp_succ()


def cap_unicast_setup_ase(config, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{cap_unicast_setup_ase.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', config.ase_id)
    data += struct.pack('B', config.cis_id)
    data += struct.pack('B', config.cig_id)
    data += struct.pack('B', config.coding_format)
    data += struct.pack('<H', config.vid)
    data += struct.pack('<H', config.cid)

    data += int.to_bytes(config.sdu_interval, 3, 'little')
    data += struct.pack('B', config.framing)
    data += struct.pack('<H', config.max_sdu_size)
    data += struct.pack('B', config.retransmission_number)
    data += struct.pack('<H', config.max_transport_latency)
    data += int.to_bytes(config.presentation_delay, 3, 'little')

    codec_ltvs_len = len(config.codec_ltvs)
    metadata_ltvs_len = len(config.metadata_ltvs)
    data += struct.pack('B', codec_ltvs_len)
    data += struct.pack('B', metadata_ltvs_len)

    if codec_ltvs_len:
        data += config.codec_ltvs

    if metadata_ltvs_len:
        data += config.metadata_ltvs

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAP['unicast_setup_ase'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_source_setup_stream(source_id, subgroup_id, coding_format,
                                      vid, cid, codec_ltvs, metadata_ltvs):
    logging.debug(f"{cap_broadcast_source_setup_stream.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    data += struct.pack('B', subgroup_id)
    data += struct.pack('B', coding_format)
    data += struct.pack('<H', vid)
    data += struct.pack('<H', cid)

    codec_ltvs_len = len(codec_ltvs)
    metadata_ltvs_len = len(metadata_ltvs)
    data += struct.pack('B', codec_ltvs_len)
    data += struct.pack('B', metadata_ltvs_len)

    if codec_ltvs_len:
        data += codec_ltvs

    if metadata_ltvs_len:
        data += metadata_ltvs

    iutctl.btp_socket.send(*CAP['broadcast_source_setup_stream'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_source_setup_subgroup(source_id, subgroup_id, coding_format,
                                        vid, cid, codec_ltvs, metadata_ltvs):
    logging.debug(f"{cap_broadcast_source_setup_subgroup.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    data += struct.pack('B', subgroup_id)
    data += struct.pack('B', coding_format)
    data += struct.pack('<H', vid)
    data += struct.pack('<H', cid)

    codec_ltvs_len = len(codec_ltvs)
    metadata_ltvs_len = len(metadata_ltvs)
    data += struct.pack('B', codec_ltvs_len)
    data += struct.pack('B', metadata_ltvs_len)

    if codec_ltvs_len:
        data += codec_ltvs

    if metadata_ltvs_len:
        data += metadata_ltvs

    iutctl.btp_socket.send(*CAP['broadcast_source_setup_subgroup'], data=data)

    cap_command_rsp_succ()


BTP_CAP_BROADCAST_SOURCE_SETUP_FLAG_ENCRYPTION = 0x01
BTP_CAP_BROADCAST_SOURCE_SETUP_FLAG_SUBGROUP_CODEC = 0x02


def cap_broadcast_source_setup(source_id, broadcast_id, sdu_interval, framing, max_sdu,
                               retransmission_number, max_transport_latency,
                               presentation_delay, encryption, broadcast_code,
                               subgroup_codec_level):

    logging.debug(f"{cap_broadcast_source_setup.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    data += int.to_bytes(broadcast_id, 3, 'little')

    # QoS Config
    data += int.to_bytes(sdu_interval, 3, 'little')
    data += struct.pack('B', framing)
    data += struct.pack('<H', max_sdu)
    data += struct.pack('B', retransmission_number)
    data += struct.pack('<H', max_transport_latency)
    data += int.to_bytes(presentation_delay, 3, 'little')

    flags = 0x00
    if encryption:
        flags |= BTP_CAP_BROADCAST_SOURCE_SETUP_FLAG_ENCRYPTION

    if subgroup_codec_level:
        flags |= BTP_CAP_BROADCAST_SOURCE_SETUP_FLAG_SUBGROUP_CODEC

    if broadcast_code is None:
        broadcast_code = 16 * b'\x00'

    data += struct.pack('B', flags)
    data += struct.pack('<16s', broadcast_code)

    iutctl.btp_socket.send(*CAP['broadcast_source_setup'], data=data)

    tuple_data = cap_command_rsp_succ()[0]
    gap_settings = int.from_bytes(tuple_data[:4], 'little')
    broadcast_id = int.from_bytes(tuple_data[4:7], 'little')
    __gap_current_settings_update(gap_settings)

    return broadcast_id


def cap_broadcast_source_release(source_id):
    logging.debug(f"{cap_broadcast_source_release.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)

    iutctl.btp_socket.send(*CAP['broadcast_source_release'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_adv_start(source_id):
    logging.debug(f"{cap_broadcast_adv_start.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    iutctl.btp_socket.send(*CAP['broadcast_adv_start'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_adv_stop(source_id):
    logging.debug(f"{cap_broadcast_adv_stop.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    iutctl.btp_socket.send(*CAP['broadcast_adv_stop'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_source_start(source_id):
    logging.debug(f"{cap_broadcast_source_start.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    iutctl.btp_socket.send(*CAP['broadcast_source_start'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_source_stop(source_id):
    logging.debug(f"{cap_broadcast_source_stop.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)
    iutctl.btp_socket.send(*CAP['broadcast_source_stop'], data=data)

    cap_command_rsp_succ()


def cap_broadcast_source_update(source_id, metadata_ltvs):
    logging.debug(f"{cap_broadcast_source_update.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', source_id)

    metadata_ltvs_len = len(metadata_ltvs)
    data += struct.pack('B', metadata_ltvs_len)
    if metadata_ltvs_len:
        data += metadata_ltvs

    iutctl.btp_socket.send(*CAP['broadcast_source_update'], data=data)

    cap_command_rsp_succ()


def cap_ev_discovery_completed_(cap, data, data_len):
    logging.debug('%s %r', cap_ev_discovery_completed_.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'CAP Discovery completed: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    cap.event_received(defs.BTP_CAP_EV_DISCOVERY_COMPLETED, (addr_type, addr, status))


def cap_ev_unicast_start_completed_(cap, data, data_len):
    logging.debug('%s %r', cap_ev_unicast_start_completed_.__name__, data)

    fmt = 'BB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    cig_id, status = struct.unpack_from(fmt, data)

    logging.debug(f'CAP Unicast Start completed: cig_id {cig_id}, status {status}')

    cap.event_received(defs.BTP_CAP_EV_UNICAST_START_COMPLETED, (status,))


def cap_ev_unicast_stop_completed_(cap, data, data_len):
    logging.debug('%s %r', cap_ev_unicast_stop_completed_.__name__, data)

    fmt = 'BB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    cig_id, status = struct.unpack_from(fmt, data)

    logging.debug(f'CAP Unicast Stop completed: cig_id {cig_id}, status {status}')

    cap.event_received(defs.BTP_CAP_EV_UNICAST_STOP_COMPLETED, (cig_id, status))


CAP_EV = {
    defs.BTP_CAP_EV_DISCOVERY_COMPLETED: cap_ev_discovery_completed_,
    defs.BTP_CAP_EV_UNICAST_START_COMPLETED: cap_ev_unicast_start_completed_,
    defs.BTP_CAP_EV_UNICAST_STOP_COMPLETED: cap_ev_unicast_stop_completed_,
}
