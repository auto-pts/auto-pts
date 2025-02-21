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

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut,\
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.gap import __gap_current_settings_update
from autopts.pybtp.types import BTPError, addr2btp_ba

BAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_BAP,
                            defs.BTP_BAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_DISCOVER,
                 CONTROLLER_INDEX),
    'send': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_SEND, CONTROLLER_INDEX),
    'broadcast_source_setup': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SOURCE_SETUP,
                               CONTROLLER_INDEX),
    'broadcast_source_release': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SOURCE_RELEASE,
                                 CONTROLLER_INDEX),
    'broadcast_adv_start': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_ADV_START,
                            CONTROLLER_INDEX),
    'broadcast_adv_stop': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_ADV_STOP,
                           CONTROLLER_INDEX),
    'broadcast_source_start': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SOURCE_START,
                               CONTROLLER_INDEX),
    'broadcast_source_stop': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SOURCE_STOP,
                              CONTROLLER_INDEX),
    'broadcast_sink_setup': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SINK_SETUP,
                             CONTROLLER_INDEX, ""),
    'broadcast_sink_release': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SINK_RELEASE,
                               CONTROLLER_INDEX, ""),
    'broadcast_scan_start': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SCAN_START,
                             CONTROLLER_INDEX, ""),
    'broadcast_scan_stop': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SCAN_STOP,
                            CONTROLLER_INDEX, ""),
    'broadcast_sink_sync': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SINK_SYNC,
                            CONTROLLER_INDEX),
    'broadcast_sink_stop': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SINK_STOP,
                            CONTROLLER_INDEX),
    'broadcast_sink_bis_sync': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_BROADCAST_SINK_BIS_SYNC,
                                CONTROLLER_INDEX),
    'discover_scan_delegator': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_DISCOVER_SCAN_DELEGATOR,
                                CONTROLLER_INDEX),
    'broadcast_assistant_scan_start': (defs.BTP_SERVICE_ID_BAP,
                                       defs.BTP_BAP_CMD_BROADCAST_ASSISTANT_SCAN_START,
                                       CONTROLLER_INDEX),
    'broadcast_assistant_scan_stop': (defs.BTP_SERVICE_ID_BAP,
                                      defs.BTP_BAP_CMD_BROADCAST_ASSISTANT_SCAN_STOP,
                                      CONTROLLER_INDEX),
    'add_broadcast_src': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_ADD_BROADCAST_SRC,
                          CONTROLLER_INDEX),
    'remove_broadcast_src': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_REMOVE_BROADCAST_SRC,
                             CONTROLLER_INDEX),
    'modify_broadcast_src': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_MODIFY_BROADCAST_SRC,
                             CONTROLLER_INDEX),
    'set_broadcast_code': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_SET_BROADCAST_CODE,
                           CONTROLLER_INDEX),
    'bap_send_past': (defs.BTP_SERVICE_ID_BAP, defs.BTP_BAP_CMD_SEND_PAST, CONTROLLER_INDEX),
}


def bap_command_rsp_succ(timeout=20.0):
    logging.debug("%s", bap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_BAP)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def bap_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['discover'], data=data)

    bap_command_rsp_succ()


def bap_send(ase_id, data_ba, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_send.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', len(data_ba))
    data += data_ba

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['send'], data=data)

    tuple_data = bap_command_rsp_succ()
    buffered_data_len = int.from_bytes(tuple_data[0], byteorder='little')

    return buffered_data_len


def bap_broadcast_source_setup(
        streams_per_subgroup, subgroups, coding_format, vid, cid,
        codec_ltvs, sdu_interval, framing, max_sdu, retransmission_number,
        max_transport_latency, presentation_delay, broadcast_id=0x123456):

    logging.debug(f"{bap_broadcast_source_setup.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')
    data += struct.pack('B', streams_per_subgroup)
    data += struct.pack('B', subgroups)

    # QoS Config
    data += int.to_bytes(sdu_interval, 3, 'little')
    data += struct.pack('B', framing)
    data += struct.pack('<H', max_sdu)
    data += struct.pack('B', retransmission_number)
    data += struct.pack('<H', max_transport_latency)
    data += int.to_bytes(presentation_delay, 3, 'little')

    # Codec Config
    data += struct.pack('B', coding_format)
    data += struct.pack('<H', vid)
    data += struct.pack('<H', cid)
    codec_ltvs_len = len(codec_ltvs)
    data += struct.pack('B', codec_ltvs_len)
    if codec_ltvs_len:
        data += codec_ltvs


    iutctl.btp_socket.send(*BAP['broadcast_source_setup'], data=data)

    tuple_data = bap_command_rsp_succ()[0]
    gap_settings = int.from_bytes(tuple_data[:4], 'little')
    broadcast_id = int.from_bytes(tuple_data[4:7], 'little')
    __gap_current_settings_update(gap_settings)

    return broadcast_id


def bap_broadcast_source_release(broadcast_id):
    logging.debug(f"{bap_broadcast_source_release.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')

    iutctl.btp_socket.send(*BAP['broadcast_source_release'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_adv_start(broadcast_id):
    logging.debug(f"{bap_broadcast_adv_start.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')
    iutctl.btp_socket.send(*BAP['broadcast_adv_start'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_adv_stop(broadcast_id):
    logging.debug(f"{bap_broadcast_adv_stop.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')
    iutctl.btp_socket.send(*BAP['broadcast_adv_stop'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_source_start(broadcast_id):
    logging.debug(f"{bap_broadcast_source_start.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')
    iutctl.btp_socket.send(*BAP['broadcast_source_start'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_source_stop(broadcast_id):
    logging.debug(f"{bap_broadcast_source_stop.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += int.to_bytes(broadcast_id, 3, 'little')
    iutctl.btp_socket.send(*BAP['broadcast_source_stop'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_sink_setup():

    logging.debug(f"{bap_broadcast_sink_setup.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['broadcast_sink_setup'])

    bap_command_rsp_succ()


def bap_broadcast_sink_release():
    logging.debug(f"{bap_broadcast_sink_release.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['broadcast_sink_release'])

    bap_command_rsp_succ()


def bap_broadcast_scan_start():
    logging.debug(f"{bap_broadcast_scan_start.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['broadcast_scan_start'])

    bap_command_rsp_succ()


def bap_broadcast_scan_stop():
    logging.debug(f"{bap_broadcast_scan_stop.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAP['broadcast_scan_stop'])

    bap_command_rsp_succ()


def bap_broadcast_sink_sync(broadcast_id, advertiser_sid, skip, sync_timeout,
                            past_available, src_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_broadcast_sink_sync.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += int.to_bytes(broadcast_id, 3, 'little')
    data += struct.pack('B', advertiser_sid)
    data += struct.pack('<H', skip)
    data += struct.pack('<H', sync_timeout)
    data += struct.pack('?', past_available)
    data += struct.pack('B', src_id)

    iutctl.btp_socket.send(*BAP['broadcast_sink_sync'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_sink_stop(broadcast_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_broadcast_sink_stop.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += int.to_bytes(broadcast_id, 3, 'little')

    iutctl.btp_socket.send(*BAP['broadcast_sink_stop'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_sink_bis_sync(broadcast_id, requested_bis_sync,
                                bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_broadcast_sink_bis_sync.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += int.to_bytes(broadcast_id, 3, 'little')
    data += struct.pack('<I', requested_bis_sync)

    iutctl.btp_socket.send(*BAP['broadcast_sink_bis_sync'], data=data)

    bap_command_rsp_succ()


def bap_discover_scan_delegator(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_discover_scan_delegator.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl.btp_socket.send(*BAP['discover_scan_delegator'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_assistant_scan_start(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_broadcast_assistant_scan_start.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl.btp_socket.send(*BAP['broadcast_assistant_scan_start'], data=data)

    bap_command_rsp_succ()


def bap_broadcast_assistant_scan_stop(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_broadcast_assistant_scan_stop.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl.btp_socket.send(*BAP['broadcast_assistant_scan_stop'], data=data)

    bap_command_rsp_succ()


def bap_add_broadcast_src(advertiser_sid, broadcast_id, pa_sync,
                          pa_interval, num_subgroups, subgroups,
                          broadcaster_addr_type, broadcaster_addr,
                          bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_add_broadcast_src.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += address_to_ba(broadcaster_addr_type, broadcaster_addr)
    data += struct.pack('B', advertiser_sid)
    data += int.to_bytes(broadcast_id, 3, 'little')
    data += struct.pack('B', pa_sync)
    data += struct.pack('<H', pa_interval)
    data += struct.pack('B', num_subgroups)
    data += subgroups

    iutctl.btp_socket.send(*BAP['add_broadcast_src'], data=data)

    bap_command_rsp_succ()


def bap_remove_broadcast_src(src_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_remove_broadcast_src.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', src_id)

    iutctl.btp_socket.send(*BAP['remove_broadcast_src'], data=data)

    bap_command_rsp_succ()


def bap_modify_broadcast_src(src_id, pa_sync, pa_interval,
                             num_subgroups, subgroups,
                             bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_modify_broadcast_src.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', src_id)
    data += struct.pack('B', pa_sync)
    data += struct.pack('<H', pa_interval)
    data += struct.pack('B', num_subgroups)
    data += subgroups

    iutctl.btp_socket.send(*BAP['modify_broadcast_src'], data=data)

    bap_command_rsp_succ()


def bap_set_broadcast_code(src_id, broadcast_code,
                           bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_set_broadcast_code.__name__}")

    iutctl = get_iut()

    if isinstance(broadcast_code, str):
        # The default broadcast code string from PTS is in big endian
        broadcast_code = bytes.fromhex(broadcast_code)[::-1]

    if len(broadcast_code) != 16:
        raise Exception('Invalid Broadcast Code length')

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', src_id)
    data += broadcast_code

    iutctl.btp_socket.send(*BAP['set_broadcast_code'], data=data)

    bap_command_rsp_succ()


def bap_send_past(src_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{bap_send_past.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', src_id)

    iutctl.btp_socket.send(*BAP['bap_send_past'], data=data)

    bap_command_rsp_succ()


def bap_ev_discovery_completed_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_discovery_completed_.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'BAP Discovery completed: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    bap.event_received(defs.BTP_BAP_EV_DISCOVERY_COMPLETED, (addr_type, addr, status))


def bap_ev_codec_cap_found_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_codec_cap_found_.__name__, data)

    fmt = '<B6sBBHBIB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, pac_dir, coding_format, frequencies, frame_durations,\
        octets_per_frame, channel_counts = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'Found codec capabilities: addr {addr} addr_type '
                  f'{addr_type} pac_dir {pac_dir} coding {coding_format:#x} '
                  f'freq {frequencies:#b} duration {frame_durations:#b} '
                  f'frame_len {octets_per_frame:#x} channel_counts {channel_counts:#b}')

    bap.event_received(defs.BTP_BAP_EV_CODEC_CAP_FOUND,
                       (addr_type, addr, pac_dir, coding_format, frequencies,
                        frame_durations, octets_per_frame, channel_counts))


def bap_ev_ase_found_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_ase_found_.__name__, data)

    fmt = '<B6sBB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, ase_dir, ase_id = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'Found ASE: addr {addr} addr_type {addr_type}'
                  f' dir {ase_dir} ID {ase_id}')

    bap.event_received(defs.BTP_BAP_EV_ASE_FOUND, (addr_type, addr, ase_dir, ase_id))


def bap_ev_stream_received_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_stream_received_.__name__, data)

    fmt = '<B6sBB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, ase_id, iso_data_len = struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    iso_data = data[fmt_len:]

    logging.debug(f'Stream received: addr {addr} addr_type {addr_type}'
                  f' ID {ase_id} data {iso_data}')

    bap.event_received(defs.BTP_BAP_EV_STREAM_RECEIVED, (addr_type, addr, ase_id, iso_data))


def bap_ev_baa_found_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_baa_found_.__name__, data)

    fmt = '<B6s3sBH'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, broadcast_id, advertiser_sid, padv_interval = \
        struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")

    ev = {'addr_type': addr_type,
          'addr': addr,
          'broadcast_id': broadcast_id,
          'advertiser_sid': advertiser_sid,
          'padv_interval': padv_interval}

    logging.debug(f'Broadcast Audio Announcement received: {ev}')

    bap.event_received(defs.BTP_BAP_EV_BAA_FOUND, ev)


def bap_ev_bis_found_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_bis_found_.__name__, data)

    fmt = '<B6s3s3sBBBHHB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, broadcast_id, pd, subgroup_id, bis_id, coding_format, vid, cid, \
        ltvs_len = struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")
    pd = int.from_bytes(pd, "little")
    ltvs = data[fmt_len:]

    ev = {'addr_type': addr_type,
          'addr': addr,
          'broadcast_id': broadcast_id,
          'pd': pd,
          'subgroup_id': subgroup_id,
          'bis_id': bis_id,
          'coding_format': coding_format,
          'vid': vid,
          'cid': cid,
          'ltvs': ltvs}

    logging.debug(f'BIS found: {ev}')

    bap.event_received(defs.BTP_BAP_EV_BIS_FOUND, ev)


def bap_ev_bis_synced_received_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_bis_synced_received_.__name__, data)

    fmt = '<B6s3sB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, broadcast_id, bis_id = struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")

    ev = {'addr_type': addr_type,
          'addr': addr,
          'broadcast_id': broadcast_id,
          'bis_id': bis_id}

    logging.debug(f'BIS synced: {ev}')

    bap.event_received(defs.BTP_BAP_EV_BIS_SYNCED, ev)


def bap_ev_bis_stream_received_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_bis_stream_received_.__name__, data)

    fmt = '<B6s3sBB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, broadcast_id, bis_id, bis_data_len = \
        struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")
    bis_data = data[fmt_len:]

    ev = {'addr_type': addr_type,
          'addr': addr,
          'broadcast_id': broadcast_id,
          'bis_id': bis_id,
          'bid_data': bis_data}

    logging.debug(f'BIS data received: {ev}')

    bap.event_received(defs.BTP_BAP_EV_BIS_STREAM_RECEIVED, ev)


def bap_ev_scan_delegator_found_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_scan_delegator_found_.__name__, data)

    fmt = '<B6s'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr = struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    ev = {'addr_type': addr_type,
          'addr': addr}

    logging.debug(f'Scan Delegator found: {ev}')

    bap.event_received(defs.BTP_BAP_EV_SCAN_DELEGATOR_FOUND, ev)


def bap_ev_broadcast_receive_state_(bap, data, data_len):
    logging.debug('%s %r', bap_ev_broadcast_receive_state_.__name__, data)

    fmt = '<B6sBB6sB3sBBB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    (addr_type, addr, src_id, broadcaster_addr_type, broadcaster_addr,
        advertiser_sid, broadcast_id, pa_sync_state, big_encryption,
        num_subgroups) = struct.unpack_from(fmt, data[:fmt_len])

    subgroups = data[fmt_len:]

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcaster_addr = binascii.hexlify(broadcaster_addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")

    ev = {'addr_type': addr_type,
          'addr': addr,
          'src_id': src_id,
          'broadcaster_addr_type': broadcaster_addr_type,
          'broadcaster_addr': broadcaster_addr,
          'advertiser_sid': advertiser_sid,
          'broadcast_id': broadcast_id,
          'pa_sync_state': pa_sync_state,
          'big_encryption': big_encryption,
          'subgroups': subgroups,
          }

    logging.debug(f'Broadcast Receive State event: {ev}')

    bap.event_received(defs.BTP_BAP_EV_BROADCAST_RECEIVE_STATE, ev)


def bap_ev_pa_syn_req(bap, data, data_len):
    logging.debug('%s %r', bap_ev_pa_syn_req.__name__, data)

    fmt = '<B6sBB3sBH'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, src_id, advertiser_sid, broadcast_id, past_avail, \
        pa_interval = struct.unpack_from(fmt, data[:fmt_len])

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    broadcast_id = int.from_bytes(broadcast_id, "little")

    ev = {'addr_type': addr_type,
          'addr': addr,
          'src_id': src_id,
          'advertiser_sid': advertiser_sid,
          'broadcast_id': broadcast_id,
          'past_avail': past_avail,
          'pa_interval': pa_interval,
          }

    logging.debug(f'PA Sync Request event: {ev}')

    bap.event_received(defs.BTP_BAP_EV_PA_SYNC_REQ, ev)


BAP_EV = {
    defs.BTP_BAP_EV_DISCOVERY_COMPLETED: bap_ev_discovery_completed_,
    defs.BTP_BAP_EV_CODEC_CAP_FOUND: bap_ev_codec_cap_found_,
    defs.BTP_BAP_EV_ASE_FOUND: bap_ev_ase_found_,
    defs.BTP_BAP_EV_STREAM_RECEIVED: bap_ev_stream_received_,
    defs.BTP_BAP_EV_BAA_FOUND: bap_ev_baa_found_,
    defs.BTP_BAP_EV_BIS_FOUND: bap_ev_bis_found_,
    defs.BTP_BAP_EV_BIS_SYNCED: bap_ev_bis_synced_received_,
    defs.BTP_BAP_EV_BIS_STREAM_RECEIVED: bap_ev_bis_stream_received_,
    defs.BTP_BAP_EV_SCAN_DELEGATOR_FOUND: bap_ev_scan_delegator_found_,
    defs.BTP_BAP_EV_BROADCAST_RECEIVE_STATE: bap_ev_broadcast_receive_state_,
    defs.BTP_BAP_EV_PA_SYNC_REQ: bap_ev_pa_syn_req,
}
