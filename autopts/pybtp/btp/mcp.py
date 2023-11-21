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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, btp_hdr_check, pts_addr_get, \
    pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba

MCP = {
    'read_supported_cmds':           (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_READ_SUPPORTED_COMMANDS,
                                      CONTROLLER_INDEX, ""),
    'discovery':                     (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_DISCOVERY,
                                      CONTROLLER_INDEX),
    'track_duration':                (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_TRACK_DURATION_READ,
                                      CONTROLLER_INDEX),
    'track_position_read':           (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_TRACK_POSITION_READ,
                                      CONTROLLER_INDEX),
    'track_position_set':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_TRACK_POSITION_SET,
                                      CONTROLLER_INDEX),
    'playback_speed_get':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PLAYBACK_SPEED_READ,
                                      CONTROLLER_INDEX),
    'playback_speed_set':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PLAYBACK_SPEED_SET,
                                      CONTROLLER_INDEX),
    'seeking_speed_get':             (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_SEEKING_SPEED_READ,
                                      CONTROLLER_INDEX),
    'icon_obj_id_read':              (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_ICON_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'next_track_obj_id_read':        (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_NEXT_TRACK_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'next_track_obj_id_set':         (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_NEXT_TRACK_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'parent_group_obj_id_read':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PARENT_GROUP_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_group_obj_id_read':     (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CURRENT_GROUP_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_group_obj_id_set':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CURRENT_GROUP_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'playing_order_read':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PLAYING_ORDER_READ,
                                      CONTROLLER_INDEX),
    'playing_order_set':             (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PLAYING_ORDER_SET,
                                      CONTROLLER_INDEX),
    'playing_orders_supported_read': (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_PLAYING_ORDERS_SUPPORTED_READ,
                                      CONTROLLER_INDEX),
    'media_state_read':              (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_MEDIA_STATE_READ,
                                      CONTROLLER_INDEX),
    'opcodes_supported_read':        (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_OPCODES_SUPPORTED_READ,
                                      CONTROLLER_INDEX),
    'content_control_id_read':       (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CONTENT_CONTROL_ID_READ,
                                      CONTROLLER_INDEX),
    'segments_obj_id_read':          (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_SEGMENTS_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_track_obj_id_read':     (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CURRENT_TRACK_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_track_obj_id_set':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CURRENT_TRACK_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'control_point_command':         (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_CMD_SEND,
                                      CONTROLLER_INDEX),
    'search_control_point_command':  (defs.BTP_SERVICE_ID_MCP,
                                      defs.MCP_SCP_SEND,
                                      CONTROLLER_INDEX),
}


def mcp_command_rsp_succ(timeout=20.0):
    logging.debug("%s", mcp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MCP)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def mcp_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['discovery'], data=data)

    mcp_command_rsp_succ()


def mcp_track_duration_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_track_duration_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['track_duration'], data=data)

    mcp_command_rsp_succ()


def mcp_track_position_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_track_position_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['track_position_read'], data=data)

    mcp_command_rsp_succ()


def mcp_track_position_set(position, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_track_position_set.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("I", position))

    iutctl.btp_socket.send(*MCP['track_position_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playback_speed_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_playback_speed_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playback_speed_get'], data=data)

    mcp_command_rsp_succ()


def mcp_playback_speed_set(speed, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_playback_speed_set.__name__}")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", speed))

    iutctl.btp_socket.send(*MCP['playback_speed_set'], data=data)

    mcp_command_rsp_succ()


def mcp_seeking_speed_get(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_seeking_speed_get.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['seeking_speed_get'], data=data)

    mcp_command_rsp_succ()


def mcp_icon_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_icon_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['icon_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_next_track_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_next_track_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['next_track_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_next_track_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_next_track_obj_id_set.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['next_track_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_parent_group_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_parent_group_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['parent_group_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_group_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_current_group_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_group_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_group_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_current_group_obj_id_set.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_group_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playing_order_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_playing_order_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_order_read'], data=data)

    mcp_command_rsp_succ()


def mcp_playing_order_set(order, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_playing_order_set.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", order))

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_order_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playing_orders_supported_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_playing_orders_supported_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_orders_supported_read'], data=data)

    mcp_command_rsp_succ()


def mcp_media_state_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_media_state_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['media_state_read'], data=data)

    mcp_command_rsp_succ()


def mcp_content_control_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_content_control_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['content_control_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_segments_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_segments_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['segments_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_track_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_current_track_obj_id_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_track_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_track_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_current_track_obj_id_set.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_track_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_opcodes_supported_read(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_opcodes_supported_read.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['opcodes_supported_read'], data=data)

    mcp_command_rsp_succ()


def mcp_control_point_cmd(opcode, use_param, param, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_control_point_cmd.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", opcode))
    data.extend(struct.pack("b", use_param))
    data.extend(struct.pack("I", param))

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['control_point_command'], data=data)
    mcp_command_rsp_succ()


def mcp_search_control_point_cmd(search_type, param, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{mcp_search_control_point_cmd.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", search_type))
    param_len = len(param)
    data.extend(struct.pack("b", param_len))
    encoded_string = param.encode("utf-8")
    param_fmt = str(param_len) + "s"
    data.extend(struct.pack(param_fmt, encoded_string))

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['search_control_point_command'], data=data)
    mcp_command_rsp_succ()


def mcp_ev_discovery_completed(mcp, data, data_len):
    logging.debug('%s %r', mcp_ev_discovery_completed.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Discovery: addr {addr} addr_type {addr_type},'
                  f' Status {status}')

    mcp.event_received(defs.MCP_DISCOVERED_EV, (addr_type, addr, status))


def mcp_track_duration_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_track_duration_ev.__name__, data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, duration = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Track Duration ev: addr {addr} addr_type {addr_type},'
                  f' Status {status}, track duration {duration}')

    mcp.event_received(defs.MCP_TRACK_DURATION_EV, (addr_type, addr, status,
                                                    duration))


def mcp_track_position_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_track_position_ev.__name__, data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, position = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Track Position ev: addr {addr} addr_type {addr_type},'
                  f' Status {status}, track position {position}')

    mcp.event_received(defs.MCP_TRACK_POSITION_EV, (addr_type, addr, status,
                                                    position))


def mcp_playback_speed_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_playback_speed_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, speed = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Playback speed: addr {addr} addr_type {addr_type},'
                  f' Status {status}, playback speed {speed}')

    mcp.event_received(defs.MCP_PLAYBACK_SPEED_EV, (addr_type, addr, status,
                                                    speed))


def mcp_seeking_speed_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_seeking_speed_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, speed = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Seeking speed: addr {addr} addr_type {addr_type},'
                  f' Status {status}, seeking speed {speed}')

    mcp.event_received(defs.MCP_SEEKING_SPEED_EV, (addr_type, addr, status,
                                                   speed))


def mcp_icon_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_icon_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Icon Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Icon Object ID {obj_id}')

    mcp.event_received(defs.MCP_ICON_OBJ_ID_EV, (addr_type, addr, status,
                                                 obj_id))


def mcp_next_track_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_next_track_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Next Track Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Next Track object ID {obj_id}')

    mcp.event_received(defs.MCP_NEXT_TRACK_OBJ_ID_EV, (addr_type, addr, status,
                                                       obj_id))


def mcp_parent_group_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_parent_group_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Parent Group Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Parent Group Object ID {obj_id}')

    mcp.event_received(defs.MCP_PARENT_GROUP_OBJ_ID_EV, (addr_type, addr, status,
                                                         obj_id))


def mcp_current_group_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_current_group_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Current Group Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Current Group Object ID {obj_id}')

    mcp.event_received(defs.MCP_CURRENT_GROUP_OBJ_ID_EV, (addr_type, addr, status,
                                                          obj_id))


def mcp_playing_order_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_playing_order_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, order = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Playing Order: addr {addr} addr_type {addr_type},'
                  f' Status {status}, playing order {order}')

    mcp.event_received(defs.MCP_PLAYING_ORDER_EV, (addr_type, addr, status,
                                                   order))


def mcp_playing_orders_supported_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_playing_orders_supported_ev.__name__, data)

    fmt = '<B6sbB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, orders = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Playing orders supported: addr {addr} addr_type {addr_type},'
                  f' Status {status}, playing orders supported {orders}')

    mcp.event_received(defs.MCP_PLAYING_ORDERS_SUPPORTED_EV, (addr_type, addr,
                                                              status, orders))


def mcp_media_state_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_media_state_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, state = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Media State: addr {addr} addr_type {addr_type},'
                  f' Status {status}, media state {state}')

    mcp.event_received(defs.MCP_MEDIA_STATE_EV, (addr_type, addr, status,
                                                 state))


def mcp_opcodes_supported_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_opcodes_supported_ev.__name__, data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, opcodes = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Opcodes Supported: addr {addr} addr_type {addr_type},'
                  f' Status {status}, opcodes {opcodes}')

    mcp.event_received(defs.MCP_OPCODES_SUPPORTED_EV, (addr_type, addr,
                                                       status, opcodes))


def mcp_content_control_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_content_control_id_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, ccid = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Content Control ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, content control ID {ccid}')

    mcp.event_received(defs.MCP_CONTENT_CONTROL_ID_EV, (addr_type, addr, status,
                                                        ccid))


def mcp_segments_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_segments_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Track Segments Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Track Segments Object ID {obj_id}')

    mcp.event_received(defs.MCP_SEGMENTS_OBJ_ID_EV, (addr_type, addr, status,
                                                     obj_id))


def mcp_current_track_obj_id_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_current_track_obj_id_ev.__name__, data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug(f'MCP Current Track Object ID: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Current Track Object ID {obj_id}')

    mcp.event_received(defs.MCP_CURRENT_TRACK_OBJ_ID_EV, (addr_type, addr, status,
                                                          obj_id))


def mcp_control_point_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_control_point_ev.__name__, data)

    fmt = '<B6sbbbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, opcode, use_param,\
        param = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Media Control Point: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Opcode {opcode}, Param {param}')

    mcp.event_received(defs.MCP_COMMAND_EV, (addr_type, addr, status, opcode,
                                             use_param, param))


def mcp_search_control_point_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_search_control_point_ev.__name__, data)

    fmt = '<B6sbbb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, status, param_len, search = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    param = struct.unpack_from(f'<{len(data) - fmt_size - 1}s',
                               data, offset=fmt_size)[0].decode('utf-8')

    logging.debug(f'MCP Search Control Point: addr {addr} addr_type {addr_type},'
                  f' Status {status}, param_len {param_len},'
                  f'search type {search}, param {param}')

    mcp.event_received(defs.MCP_SEARCH_EV, (addr_type, addr, status, param_len,
                                            search, param))


def mcp_cmd_ntf_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_cmd_ntf_ev.__name__, data)

    fmt = '<B6sbbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, requested_opcode,\
        result_code = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Media Control Point Notification: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Requested Opcode {requested_opcode},'
                  f' Result Code {result_code}')

    mcp.event_received(defs.MCP_CMD_NTF_EV, (addr_type, addr, status,
                                             requested_opcode, result_code))


def mcp_search_ntf_ev(mcp, data, data_len):
    logging.debug('%s %r', mcp_search_ntf_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, result_code = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'MCP Search Control Point Notification: addr {addr} addr_type {addr_type},'
                  f' Status {status}, Result Code {result_code}')

    mcp.event_received(defs.MCP_SEARCH_NTF_EV, (addr_type, addr, status,
                                                result_code))


MCP_EV = {
    defs.MCP_DISCOVERED_EV: mcp_ev_discovery_completed,
    defs.MCP_TRACK_DURATION_EV: mcp_track_duration_ev,
    defs.MCP_TRACK_POSITION_EV: mcp_track_position_ev,
    defs.MCP_PLAYBACK_SPEED_EV: mcp_playback_speed_ev,
    defs.MCP_SEEKING_SPEED_EV: mcp_seeking_speed_ev,
    defs.MCP_ICON_OBJ_ID_EV: mcp_icon_obj_id_ev,
    defs.MCP_NEXT_TRACK_OBJ_ID_EV: mcp_next_track_obj_id_ev,
    defs.MCP_PARENT_GROUP_OBJ_ID_EV: mcp_parent_group_obj_id_ev,
    defs.MCP_CURRENT_GROUP_OBJ_ID_EV: mcp_current_group_obj_id_ev,
    defs.MCP_PLAYING_ORDER_EV: mcp_playing_order_ev,
    defs.MCP_PLAYING_ORDERS_SUPPORTED_EV: mcp_playing_orders_supported_ev,
    defs.MCP_MEDIA_STATE_EV: mcp_media_state_ev,
    defs.MCP_OPCODES_SUPPORTED_EV: mcp_opcodes_supported_ev,
    defs.MCP_CONTENT_CONTROL_ID_EV: mcp_content_control_id_ev,
    defs.MCP_SEGMENTS_OBJ_ID_EV: mcp_segments_obj_id_ev,
    defs.MCP_CURRENT_TRACK_OBJ_ID_EV: mcp_current_track_obj_id_ev,
    defs.MCP_COMMAND_EV: mcp_control_point_ev,
    defs.MCP_SEARCH_EV: mcp_search_control_point_ev,
    defs.MCP_CMD_NTF_EV: mcp_cmd_ntf_ev,
    defs.MCP_SEARCH_NTF_EV: mcp_search_ntf_ev
}