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


HAS = {
    'read_supported_cmds': ( defs.BTP_SERVICE_ID_HAS,
                             defs.BTP_HAS_CMD_READ_SUPPORTED_COMMANDS,
                             CONTROLLER_INDEX),
    'set_active_index':    ( defs.BTP_SERVICE_ID_HAS, 
                             defs.BTP_HAS_CMD_SET_ACTIVE_INDEX,
                             CONTROLLER_INDEX),
    'set_preset_name':     ( defs.BTP_SERVICE_ID_HAS, 
                             defs.BTP_HAS_CMD_SET_PRESET_NAME,
                             CONTROLLER_INDEX),
    'remove_preset':       ( defs.BTP_SERVICE_ID_HAS, 
                             defs.BTP_HAS_CMD_REMOVE_PRESET,
                             CONTROLLER_INDEX),
    'add_preset':          ( defs.BTP_SERVICE_ID_HAS, 
                             defs.BTP_HAS_CMD_ADD_PRESET,
                             CONTROLLER_INDEX),
    'set_properties':      ( defs.BTP_SERVICE_ID_HAS, 
                             defs.BTP_HAS_CMD_SET_PROPERTIES,
                             CONTROLLER_INDEX)
}


def has_command_rsp_succ(timeout=20.0):
    logging.debug("%s", has_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_HAS)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def has_set_active_index(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{has_set_active_index.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAS['set_active_index'], data=data)

    has_command_rsp_succ()


def has_set_preset_name(index, name, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{has_set_preset_name.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    size = len(name.encode())
    data += struct.pack('BB' + str(size) + 's', index, size, name.encode())

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAS['set_preset_name'], data=data)

    has_command_rsp_succ()


def has_remove_preset(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{has_remove_preset.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAS['remove_preset'], data=data)

    has_command_rsp_succ()


def has_add_preset(index, properties, name, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{has_add_preset.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    size = len(name.encode())
    data += struct.pack('BBB' + str(size) + 's', index, properties, size, name.encode())

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAS['add_preset'], data=data)

    has_command_rsp_succ()


def has_set_properties(index, properties, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{has_add_preset.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('BB', index, properties)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAS['set_properties'], data=data)

    has_command_rsp_succ()
