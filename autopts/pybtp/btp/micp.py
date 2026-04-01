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
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes, le_bytes_to_hex_str

MICP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_MICP,
                            defs.BTP_MICP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'discovery':           (defs.BTP_SERVICE_ID_MICP,
                            defs.BTP_MICP_CMD_DISCOVERY,
                            CONTROLLER_INDEX),
    'mute_state':          (defs.BTP_SERVICE_ID_MICP,
                            defs.BTP_MICP_CMD_MUTE_STATE,
                            CONTROLLER_INDEX),
    'mute':                (defs.BTP_SERVICE_ID_MICP,
                            defs.BTP_MICP_CMD_MUTE,
                            CONTROLLER_INDEX),
}


def micp_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MICP)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def micp_discover(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['discovery'], data=data)

    micp_command_rsp_succ()


def micp_mute(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['mute'], data=data)

    micp_command_rsp_succ()


def micp_mute_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['mute_state'], data=data)

    micp_command_rsp_succ()


def micp_ev_discovery_completed_(micp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbHHHHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, mute_handle, state_handle, gain_handle, type_handle, \
        status_handle, control_handle, desc_handle = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MICP Discovery completed: addr %r, addr_type %r, att_status %r, mute handle %r, state handle %r,"
                  "gain handle %r, type handle %r, status handle %r, control handle %r, description handle %r",
                  addr, addr_type, att_status, mute_handle, state_handle, gain_handle, type_handle, status_handle,
                  control_handle, desc_handle)

    micp.event_received(defs.BTP_MICP_EV_DISCOVERED, (addr_type, addr, att_status, mute_handle,
                                                  state_handle, gain_handle, type_handle,
                                                  status_handle, control_handle, desc_handle))


def micp_mute_state_ev(micp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, mute = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MICP Mute Read: addr %r, addr_type %r, att_status %r, mute %r",
                  addr, addr_type, att_status, mute)

    micp.event_received(defs.BTP_MICP_EV_MUTE_STATE, (addr_type, addr, att_status, mute))


MICP_EV = {
    defs.BTP_MICP_EV_DISCOVERED: micp_ev_discovery_completed_,
    defs.BTP_MICP_EV_MUTE_STATE: micp_mute_state_ev,
}
