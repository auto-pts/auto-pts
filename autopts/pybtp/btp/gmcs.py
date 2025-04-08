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
from autopts.pybtp.types import BTPError, addr2btp_ba

GMCS = {
    'read_supported_cmds':      (defs.BTP_SERVICE_ID_GMCS,
                                 defs.BTP_GMCS_CMD_READ_SUPPORTED_COMMANDS,
                                 CONTROLLER_INDEX, ""),
    'control_point_command':    (defs.BTP_SERVICE_ID_GMCS,
                                 defs.BTP_GMCS_CMD_COMMAND_SEND,
                                 CONTROLLER_INDEX),
    'current_track_obj_id_get': (defs.BTP_SERVICE_ID_GMCS,
                                 defs.BTP_GMCS_CMD_CURRENT_TRACK_OBJ_ID_GET,
                                 CONTROLLER_INDEX, ""),
    'next_track_obj_id_get':     (defs.BTP_SERVICE_ID_GMCS,
                                  defs.BTP_GMCS_CMD_NEXT_TRACK_OBJ_ID_GET,
                                  CONTROLLER_INDEX, ""),
    'inactive_state_set':        (defs.BTP_SERVICE_ID_GMCS,
                                  defs.BTP_GMCS_CMD_INACTIVE_STATE_SET,
                                  CONTROLLER_INDEX, ""),
    'parent_group_set':          (defs.BTP_SERVICE_ID_GMCS,
                                  defs.BTP_GMCS_CMD_PARENT_GROUP_SET,
                                  CONTROLLER_INDEX, ""),
}


def gmcs_command_rsp_succ(timeout=20.0):
    logging.debug("%s", gmcs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GMCS)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def gmcs_control_point_cmd(opcode, use_param, param=None):
    logging.debug(f"{gmcs_control_point_cmd.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", opcode))
    data.extend(struct.pack("b", use_param))

    if use_param > 0 and param is not None:
        data.extend(struct.pack("I", param))

    iutctl = get_iut()

    iutctl.btp_socket.send(*GMCS['control_point_command'], data=data)

    gmcs_command_rsp_succ()


def gmcs_current_track_obj_id_get():
    logging.debug(f"{gmcs_current_track_obj_id_get.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*GMCS['current_track_obj_id_get'])

    fmt = '<6s'
    data = gmcs_command_rsp_succ()[0]

    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    obj_id_bytes = struct.unpack_from(fmt, data)
    obj_id = int.from_bytes(obj_id_bytes[0], byteorder='little', signed=False)

    return obj_id


def gmcs_next_track_obj_id_get():
    logging.debug(f"{gmcs_next_track_obj_id_get.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*GMCS['next_track_obj_id_get'])

    fmt = '<6s'
    data = gmcs_command_rsp_succ()[0]

    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    obj_id_bytes = struct.unpack_from(fmt, data)
    obj_id = int.from_bytes(obj_id_bytes[0], byteorder='little', signed=False)

    return obj_id


def gmcs_inactive_state_set():
    logging.debug(f"{gmcs_inactive_state_set.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*GMCS['inactive_state_set'])

    fmt = '<b'
    data = gmcs_command_rsp_succ()[0]

    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    state = struct.unpack_from(fmt, data)[0]

    return state


def gmcs_parent_group_set():
    logging.debug(f"{gmcs_parent_group_set.__name__}")

    iutctl = get_iut()

    iutctl.btp_socket.send(*GMCS['parent_group_set'])

    return gmcs_command_rsp_succ()


GMCS_EV = {
}
