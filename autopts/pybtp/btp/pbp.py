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
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, le_bytes_to_hex_str

log = logging.debug

PBP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_PBP,
                            defs.BTP_PBP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'set_public_broadcast_announcement': (defs.BTP_SERVICE_ID_PBP,
                                          defs.BTP_PBP_CMD_SET_PUBLIC_BROADCAST_ANNOUNCEMENT,
                                          CONTROLLER_INDEX),
    'set_broadcast_name': (defs.BTP_SERVICE_ID_PBP,
                           defs.BTP_PBP_CMD_SET_BROADCAST_NAME,
                           CONTROLLER_INDEX),
    'broadcast_scan_start': (defs.BTP_SERVICE_ID_PBP,
                             defs.BTP_PBP_CMD_BROADCAST_SCAN_START,
                             CONTROLLER_INDEX),
    'broadcast_scan_stop': (defs.BTP_SERVICE_ID_PBP,
                            defs.BTP_PBP_CMD_BROADCAST_SCAN_STOP,
                            CONTROLLER_INDEX),
}


def pbp_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_PBP)

    return tuple_data


def pbp_set_public_broadcast_announcement(features, metadata):
    logging.debug("")

    data = bytearray()
    metadata_len = len(metadata)
    data += struct.pack('BB', features, metadata_len)

    if metadata_len:
        data += metadata

    iutctl = get_iut()
    iutctl.btp_socket.send(*PBP['set_public_broadcast_announcement'], data=data)

    pbp_command_rsp_succ()


def pbp_set_broadcast_name(name):
    logging.debug("")

    name_data = name.encode('utf-8')
    data = bytearray()
    data += struct.pack('B', len(name_data))
    data += name_data

    iutctl = get_iut()
    iutctl.btp_socket.send(*PBP['set_broadcast_name'], data=data)

    pbp_command_rsp_succ()


def pbp_broadcast_scan_start():
    logging.debug("")

    data = bytearray()
    iutctl = get_iut()
    iutctl.btp_socket.send(*PBP['broadcast_scan_start'], data=data)

    pbp_command_rsp_succ()


def pbp_broadcast_scan_stop():
    logging.debug("")

    data = bytearray()
    iutctl = get_iut()
    iutctl.btp_socket.send(*PBP['broadcast_scan_stop'], data=data)

    pbp_command_rsp_succ()


def pbp_ev_public_broadcast_announcement_found(pbp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6s3sBHBB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    addr_type, addr, broadcast_id, advertiser_sid, padv_interval, pba_features, broadcast_name_len = \
        struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)
    broadcast_id = int.from_bytes(broadcast_id, "little")

    broadcast_name = data[fmt_len:].decode("utf-8")

    ev = {'addr_type': addr_type,
          'addr': addr,
          'broadcast_id': broadcast_id,
          'advertiser_sid': advertiser_sid,
          'padv_interval': padv_interval,
          'pba_features': pba_features,
          'broadcast_name': broadcast_name}

    logging.debug("Public Broadcast Announcement received: %r", ev)

    pbp.event_received(defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND, ev)


PBP_EV = {
    defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND: pbp_ev_public_broadcast_announcement_found,
}
