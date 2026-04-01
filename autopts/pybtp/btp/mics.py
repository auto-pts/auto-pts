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
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes

MICS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_MICS,
                            defs.BTP_MICS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'mute_disable':        (defs.BTP_SERVICE_ID_MICS,
                            defs.BTP_MICS_CMD_MUTE_DISABLE,
                            CONTROLLER_INDEX, ""),
    'mute_read':           (defs.BTP_SERVICE_ID_MICS,
                            defs.BTP_MICS_CMD_MUTE_READ,
                            CONTROLLER_INDEX, ""),
    'mute':                (defs.BTP_SERVICE_ID_MICS,
                            defs.BTP_MICS_CMD_MUTE,
                            CONTROLLER_INDEX, ""),
    'unmute':              (defs.BTP_SERVICE_ID_MICS,
                            defs.BTP_MICS_CMD_UNMUTE,
                            CONTROLLER_INDEX, ""),
}


def mics_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MICS)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def mics_mute_disable():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute_disable'])

    mics_command_rsp_succ()


def mics_mute_read():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute_read'])

    mics_command_rsp_succ()


def mics_mute():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute'])

    mics_command_rsp_succ()


def mics_unmute():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['unmute'])

    mics_command_rsp_succ()


def mics_mute_state_ev(mics, data, data_len):
    logging.debug('%r', data)

    fmt = '<b'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    mute = struct.unpack_from(fmt, data)

    logging.debug("MICS Mute state: %r", mute[0])

    mics.event_received(defs.BTP_MICS_EV_MUTE_STATE, mute)


MICS_EV = {
    defs.BTP_MICS_EV_MUTE_STATE: mics_mute_state_ev,
}
