#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup.
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr2btp_ba

VOCS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VOCS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'audio_desc':          (defs.BTP_SERVICE_ID_VOCS, defs.BTP_VOCS_CMD_UPDATE_OUT_DESC,
                            CONTROLLER_INDEX),
    "audio_loc":           (defs.BTP_SERVICE_ID_VOCS, defs.BTP_VOCS_CMD_UPDATE_AUDIO_LOC,
                            CONTROLLER_INDEX),
    'state_read':          (defs.BTP_SERVICE_ID_VOCS,
                            defs.BTP_VOCS_CMD_OFFSET_STATE_GET,
                            CONTROLLER_INDEX),
    'audio_loc_get':       (defs.BTP_SERVICE_ID_VOCS,
                            defs.BTP_VOCS_CMD_AUDIO_LOC_GET,
                            CONTROLLER_INDEX),
    'state_set':           (defs.BTP_SERVICE_ID_VOCS,
                            defs.BTP_VOCS_CMD_OFFSET_STATE_SET,
                            CONTROLLER_INDEX),
}


def vocs_command_rsp_succ(op=None):
    logging.debug("%s", vocs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_VOCS, op)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def vocs_audio_desc(string):
    logging.debug("%s", vocs_audio_desc.__name__)

    iutctl = get_iut()
    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

    iutctl.btp_socket.send(*VOCS['audio_desc'], data = data)
    vocs_command_rsp_succ()


def vocs_audio_loc(location, bd_addr_type=None, bd_addr=None):
    logging.debug("%s", vocs_audio_loc.__name__)

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(bytearray(struct.pack("I", location)))

    iutctl.btp_socket.send(*VOCS['audio_loc'], data=data)
    vocs_command_rsp_succ()


def vocs_offset_state_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{vocs_offset_state_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VOCS['state_read'], data=data)

    vocs_command_rsp_succ()


def vocs_offset_state_set(offset, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{vocs_offset_state_set.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(bytearray(struct.pack("h", offset)))

    iutctl.btp_socket.send(*VOCS['state_set'], data=data)
    vocs_command_rsp_succ()


def vocs_audio_location_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{vocs_audio_location_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VOCS['audio_loc_get'], data=data)

    vocs_command_rsp_succ()


def vocs_state_ev(vocs, data, data_len):
    logging.debug('%s %r', vocs_state_ev.__name__, data)

    fmt = '<B6sbh'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, offset = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'VOCS Offset State: addr {addr} addr_type {addr_type},'
                  f'ATT status {att_status}, offset {offset}')

    vocs.event_received(defs.BTP_VOCS_EV_OFFSET, (addr_type, addr, att_status, offset))


def vocs_audio_loc_ev(vocs, data, data_len):
    logging.debug('%s %r', vocs_audio_loc_ev.__name__, data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, location = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'VOCS Audio Location: addr {addr} addr_type {addr_type},'
                  f' ATT Status {att_status}, Audio Location {location}')

    vocs.event_received(defs.BTP_VOCS_EV_AUDIO_LOC, (addr_type, addr, att_status,
                                                 location))


def vocs_procedure_ev(vocs, data, data_len):
    logging.debug('%s %r', vocs_procedure_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, opcode = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'VOCS Procedure Event: addr {addr} addr_type {addr_type},'
                  f' ATT status {att_status}, opcode {opcode}')

    vocs.event_received(defs.BTP_VOCS_EV_PROCEDURE, (addr_type, addr, att_status, opcode))


VOCS_EV = {
    defs.BTP_VOCS_EV_OFFSET: vocs_state_ev,
    defs.BTP_VOCS_EV_AUDIO_LOC: vocs_audio_loc_ev,
    defs.BTP_VOCS_EV_PROCEDURE: vocs_procedure_ev
}
