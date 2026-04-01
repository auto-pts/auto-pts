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

VCP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'discovery':           (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_DISCOVERY,
                            CONTROLLER_INDEX),
    'state_read':          (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_STATE_READ,
                            CONTROLLER_INDEX),
    'flags_read':          (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_FLAGS_READ,
                            CONTROLLER_INDEX),
    'vcp_vol_down':        (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_VOL_DOWN,
                            CONTROLLER_INDEX),
    'vcp_vol_up':          (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_VOL_UP,
                            CONTROLLER_INDEX),
    'vcp_unmute_vol_down': (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_UNMUTE_VOL_DOWN,
                            CONTROLLER_INDEX),
    'vcp_unmute_vol_up':   (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_UNMUTE_VOL_UP,
                            CONTROLLER_INDEX),
    'vcp_set_vol':         (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_SET_VOL,
                            CONTROLLER_INDEX),
    'vcp_unmute':          (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_UNMUTE,
                            CONTROLLER_INDEX),
    'vcp_mute':            (defs.BTP_SERVICE_ID_VCP,
                            defs.BTP_VCP_CMD_MUTE,
                            CONTROLLER_INDEX),
}


def vcp_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_VCP)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def vcp_discover(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['discovery'], data=data)

    vcp_command_rsp_succ()


def vcp_state_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['state_read'], data=data)

    vcp_command_rsp_succ()


def vcp_volume_flags_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['flags_read'], data=data)

    vcp_command_rsp_succ()


def vcp_volume_down(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_vol_down'], data=data)

    vcp_command_rsp_succ()


def vcp_volume_up(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_vol_up'], data=data)

    vcp_command_rsp_succ()


def vcp_unmute_vol_down(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_unmute_vol_down'], data=data)

    vcp_command_rsp_succ()


def vcp_unmute_vol_up(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_unmute_vol_up'], data=data)

    vcp_command_rsp_succ()


def vcp_set_vol(volume, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    iutctl = get_iut()

    if isinstance(volume, str):
        volume = int(volume)
    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("<B", volume))

    iutctl.btp_socket.send(*VCP['vcp_set_vol'], data=data)

    vcp_command_rsp_succ()


def vcp_unmute(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_unmute'], data=data)

    vcp_command_rsp_succ()


def vcp_mute(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*VCP['vcp_mute'], data=data)

    vcp_command_rsp_succ()


def vcp_ev_discovery_completed_(vcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbHHHHHHHHHHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, control_handle, flag_handle, state_handle, vocs_state,\
        vocs_location, vocs_control, vocs_desc, aics_state, aics_gain, aics_type,\
        aics_status, aics_control, aics_desc = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug(
        "VCP Discovery completed: addr %r, addr_type %r, ATT Status %r, Volume Control Point handle %r,"
        "Volume Flags handle %r, Volume State handle %r, VOCS State handle %r, VOCS Location handle %r,"
        "VOCS Control handle %r, VOCS Description handle %r, AICS State handle %r, AICS Gain handle %r,"
        "AICS Type handle %r, AICS Status handle %r, AICS Control Point %r, AICS Description %r",
        addr, addr_type, att_status, control_handle, flag_handle, state_handle, vocs_state, vocs_location,
        vocs_control, vocs_desc, aics_state, aics_gain, aics_type, aics_status, aics_control, aics_desc)

    vcp.event_received(defs.BTP_VCP_EV_DISCOVERED, (addr_type, addr, att_status, control_handle,
                                                flag_handle, state_handle, vocs_state,
                                                vocs_location, vocs_control,
                                                vocs_desc, aics_state, aics_gain,
                                                aics_type, aics_status, aics_control,
                                                aics_desc))


def vcp_state_ev(vcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, volume, mute = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("VCP State: addr %r, addr_type %r, ATT Status %r, volume %r, mute %r",
                  addr, addr_type, att_status, volume, mute)

    vcp.event_received(defs.BTP_VCP_EV_STATE, (addr_type, addr, att_status, volume, mute))


def vcp_flags_ev(vcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, flags = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("VCP Volume Flags: addr %r, addr_type %r,ATT Status %r, flags %r",
                  addr, addr_type, att_status, flags)

    vcp.event_received(defs.BTP_VCP_EV_FLAGS, (addr_type, addr, att_status, flags))


def vcp_procedure_ev(vcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, opcode = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("VCP Procedure Event: addr %r, addr_type %r, ATT status %r, opcode %r",
                  addr, addr_type, att_status, opcode)

    vcp.event_received(defs.BTP_VCP_EV_PROCEDURE, (addr_type, addr, att_status, opcode))


VCP_EV = {
    defs.BTP_VCP_EV_DISCOVERED: vcp_ev_discovery_completed_,
    defs.BTP_VCP_EV_STATE: vcp_state_ev,
    defs.BTP_VCP_EV_FLAGS: vcp_flags_ev,
    defs.BTP_VCP_EV_PROCEDURE: vcp_procedure_ev
}
