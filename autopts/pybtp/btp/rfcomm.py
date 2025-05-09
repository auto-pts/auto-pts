#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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

import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, \
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba
log = logging.debug


RFCOMM = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_RFCOMM,
                            defs.BTP_RFCOMM_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'conn': (defs.BTP_SERVICE_ID_RFCOMM,
            defs.BTP_RFCOMM_CMD_CONNECT,
            CONTROLLER_INDEX),
    'register_server': (defs.BTP_SERVICE_ID_RFCOMM,
                    defs.BTP_RFCOMM_CMD_REGISTER_SERVER,
                    CONTROLLER_INDEX),
    'send_data': (defs.BTP_SERVICE_ID_RFCOMM,
                defs.BTP_RFCOMM_CMD_SEND_DATA,
                CONTROLLER_INDEX),
}


def rfcomm_conn(bd_addr=None, bd_addr_type=None, channel=None):
    logging.debug("%s %r %r", rfcomm_conn.__name__, bd_addr, channel)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['conn'], data=data_ba)

def rfcomm_register_server(channel=None):
    logging.debug("%s %r", rfcomm_register_server.__name__, channel)
    iutctl = get_iut()

    data_ba = bytearray()

    # Add channel
    if channel is None:
        channel = 9  # Default channel if not specified
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['register_server'], data=data_ba)

def rfcomm_send_data(data):
    """
    Send data over an established RFCOMM connection.
    
    Args:
        data: The data to be sent (bytes or bytearray)
        dlci: The DLCI to use (optional, depends on implementation)
    """
    logging.debug("%s %r", rfcomm_send_data.__name__, data)
    iutctl = get_iut()

    if isinstance(data, bytes):
        data_ba = bytearray(data)
    elif isinstance(data, bytearray):
        data_ba = data
    else:
        data_ba = bytearray(data)

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['send_data'], data=data_ba)


def rfcomm_disconnect():
    """
    Initiate a disconnection of an established RFCOMM connection.

    Args:
        dlci: The DLCI to disconnect (optional, depends on implementation)
    """
    logging.debug("%s", rfcomm_disconnect.__name__)
    iutctl = get_iut()

    data_ba = bytearray()

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['disconnect'], data=data_ba)

RFCOMM = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_RFCOMM,
                            defs.BTP_RFCOMM_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'conn': (defs.BTP_SERVICE_ID_RFCOMM,
            defs.BTP_RFCOMM_CMD_CONNECT,
            CONTROLLER_INDEX),
    'register_server': (defs.BTP_SERVICE_ID_RFCOMM,
                    defs.BTP_RFCOMM_CMD_REGISTER_SERVER,
                    CONTROLLER_INDEX),
    'send_data': (defs.BTP_SERVICE_ID_RFCOMM,
                defs.BTP_RFCOMM_CMD_SEND_DATA,
                CONTROLLER_INDEX),
    'disconnect': (defs.BTP_SERVICE_ID_RFCOMM,
                  defs.BTP_RFCOMM_CMD_DISCONNECT,
                  CONTROLLER_INDEX),
}


def rfcomm_command_rsp_succ(timeout=20.0):
    logging.debug("%s", rfcomm_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_RFCOMM)

    return tuple_data

# An example event, to be changed or deleted
def rfcomm_ev_dummy_completed(rfcomm, data, data_len):
    logging.debug('%s %r', rfcomm_ev_dummy_completed.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'RFCOMM Dummy event completed: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    rfcomm.event_received(defs.BTP_RFCOMM_EV_DUMMY_COMPLETED, (addr_type, addr, status))


RFCOMM_EV = {
    defs.BTP_RFCOMM_EV_DUMMY_COMPLETED: rfcomm_ev_dummy_completed,
}
