#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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


CAS = {
    'read_supported_cmds': ( defs.BTP_SERVICE_ID_CAS,
                             defs.BTP_CAS_CMD_READ_SUPPORTED_COMMANDS,
                             CONTROLLER_INDEX),
    'set_member_lock':     ( defs.BTP_SERVICE_ID_CAS,
                             defs.BTP_CAS_CMD_SET_MEMBER_LOCK,
                             CONTROLLER_INDEX),
    'get_member_rsi':      ( defs.BTP_SERVICE_ID_CAS,
                             defs.BTP_CAS_CMD_GET_MEMBER_RSI,
                             CONTROLLER_INDEX)
}


def cas_command_rsp_succ(timeout=20.0):
    logging.debug("%s", cas_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CAS)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def cas_set_member_lock(lock, force, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{cas_set_member_lock.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('BB', lock, force)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CAS['set_member_lock'], data=data)

    cas_command_rsp_succ()


def cas_get_member_rsi(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{cas_get_member_rsi.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    rsp = iutctl.btp_socket.send_wait_rsp(*CAS['get_member_rsi'], data=data)[0]

    rsi = struct.unpack('<6B', rsp)
    return rsi
