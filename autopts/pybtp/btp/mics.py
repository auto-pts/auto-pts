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

from .btpdefs import defs
from .btp import CONTROLLER_INDEX, get_iut_method as get_iut, btp_hdr_check
from .btpdefs.types import BTPError

MICS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_MICS,
                            defs.MICP_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'mute_disable':        (defs.BTP_SERVICE_ID_MICS,
                            defs.MICS_MUTE_DISABLE,
                            CONTROLLER_INDEX, ""),
    'mute_read':           (defs.BTP_SERVICE_ID_MICS,
                            defs.MICS_MUTE_READ,
                            CONTROLLER_INDEX, ""),
    'mute':                (defs.BTP_SERVICE_ID_MICS,
                            defs.MICS_MUTE,
                            CONTROLLER_INDEX, ""),
    'unmute':              (defs.BTP_SERVICE_ID_MICS,
                            defs.MICS_UNMUTE,
                            CONTROLLER_INDEX, ""),
}


def mics_command_rsp_succ(timeout=20.0):
    logging.debug("%s", mics_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MICS)
    return tuple_data


def mics_mute_disable():
    logging.debug(f"{mics_mute_disable.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute_disable'])

    mics_command_rsp_succ()


def mics_mute_read():
    logging.debug(f"{mics_mute_read.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute_read'])

    mics_command_rsp_succ()


def mics_mute():
    logging.debug(f"{mics_mute.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['mute'])

    mics_command_rsp_succ()


def mics_unmute():
    logging.debug(f"{mics_unmute.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*MICS['unmute'])

    mics_command_rsp_succ()


def mics_mute_state_ev(mics, data, data_len):
    logging.debug('%s %r', mics_mute_state_ev.__name__, data)

    fmt = '<b'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    mute = struct.unpack_from(fmt, data)

    logging.debug(f'MICS Mute state: {mute[0]}')

    mics.event_received(defs.MICS_MUTE_STATE_EV, mute)


MICS_EV = {
    defs.MICS_MUTE_STATE_EV: mics_mute_state_ev,
}