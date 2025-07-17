#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Demant.
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError


def flogger(f):
    def inner(*args, **kwargs):
        logging.debug(f'{f.__name__}')
        ret = f(*args, **kwargs)
        return ret
    return inner


ISO = {
    "BTP_ISO_CMD_SYNC": (defs.BTP_SERVICE_ID_ISO, defs.BTP_ISO_CMD_SYNC, CONTROLLER_INDEX),
}


@flogger
def iso_command_rsp_succ(timeout=20.0):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_ISO)

    return tuple_data


@flogger
def BTP_ISO_CMD_SYNC(bis_bitfield, mse, sync_timeout, broadcast_code=None):
    iutctl = get_iut()

    encryption = broadcast_code is not None

    if broadcast_code is None:
        # Still need to send a broadcast code
        broadcast_code = bytearray([0] * 16)
    elif isinstance(broadcast_code, str):
        # The default broadcast code string from PTS is in big endian
        broadcast_code = bytes.fromhex(broadcast_code)[::-1]

    if len(broadcast_code) != 16:
        raise Exception('Invalid Broadcast Code length')

    data = bytearray()
    data += struct.pack('<L', bis_bitfield)
    data += struct.pack('<L', mse)
    data += struct.pack('<H', sync_timeout)
    data += struct.pack('B', encryption)
    data += broadcast_code

    iutctl.btp_socket.send(*ISO['BTP_ISO_CMD_SYNC'], data=data)

    iso_command_rsp_succ()


@flogger
def BTP_ISO_EV_CONNECTED_(iso, data, data_len):

    fmt = '<H'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    handle = struct.unpack_from(fmt, data[:fmt_len])[0]

    ev = {'handle': handle}

    logging.debug(f'BTP_ISO_EV_CONNECTED_ {handle}')

    iso.event_received(defs.BTP_ISO_EV_CONNECTED, ev)


@flogger
def BTP_ISO_EV_DISCONNECTED_(iso, data, data_len):

    fmt = '<HB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    handle, reason = struct.unpack_from(fmt, data[:fmt_len])

    ev = {'handle': handle, 'reason': reason}

    iso.event_received(defs.BTP_ISO_EV_DISCONNECTED, ev)


@flogger
def BTP_ISO_EV_RECV_(iso, data, data_len):

    fmt = '<HLHB'
    fmt_len = struct.calcsize(fmt)
    if len(data) < fmt_len:
        raise BTPError('Invalid data length')

    handle, ts, seq_num, flags = struct.unpack_from(fmt, data[:fmt_len])

    ev = {'handle': handle, 'ts': ts, 'seq_num': seq_num, 'flags': flags}

    logging.debug(f'BTP_ISO_EV_RECV_ {handle}')

    iso.event_received(defs.BTP_ISO_EV_RECV, ev)


ISO_EV = {
    defs.BTP_ISO_EV_CONNECTED: BTP_ISO_EV_CONNECTED_,
    defs.BTP_ISO_EV_DISCONNECTED: BTP_ISO_EV_DISCONNECTED_,
    defs.BTP_ISO_EV_RECV: BTP_ISO_EV_RECV_,
}
