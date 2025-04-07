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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba


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
    logging.debug("%s", micp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MICP)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def micp_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{micp_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['discovery'], data=data)

    micp_command_rsp_succ()


def micp_mute(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{micp_mute.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['mute'], data=data)

    micp_command_rsp_succ()


def micp_mute_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{micp_mute_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MICP['mute_state'], data=data)

    micp_command_rsp_succ()


def micp_ev_discovery_completed_(micp, data, data_len):
    logging.debug('%s %r', micp_ev_discovery_completed_.__name__, data)

    fmt = '<B6sbHHHHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, mute_handle, state_handle, gain_handle, type_handle, \
        status_handle, control_handle, desc_handle = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MICP Discovery completed: addr {addr}, addr_type {addr_type}, '
                  f'att_status {att_status} mute handle {mute_handle},'
                  f' state handle {state_handle}, gain handle {gain_handle},'
                  f' type handle {type_handle}, status handle {status_handle},'
                  f' control handle {control_handle}, description handle {desc_handle}')

    micp.event_received(defs.BTP_MICP_EV_DISCOVERED, (addr_type, addr, att_status, mute_handle,
                                                  state_handle, gain_handle, type_handle,
                                                  status_handle, control_handle, desc_handle))


def micp_mute_state_ev(micp, data, data_len):
    logging.debug('%s %r', micp_mute_state_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, mute = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MICP Mute Read: addr {addr} addr_type '
                  f'{addr_type}, att_status {att_status} mute {mute}')

    micp.event_received(defs.BTP_MICP_EV_MUTE_STATE, (addr_type, addr, att_status, mute))


MICP_EV = {
    defs.BTP_MICP_EV_DISCOVERED: micp_ev_discovery_completed_,
    defs.BTP_MICP_EV_MUTE_STATE: micp_mute_state_ev,
}