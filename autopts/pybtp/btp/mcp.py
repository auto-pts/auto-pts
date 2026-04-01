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

MCP = {
    'read_supported_cmds':           (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_READ_SUPPORTED_COMMANDS,
                                      CONTROLLER_INDEX, ""),
    'discovery':                     (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_DISCOVERY,
                                      CONTROLLER_INDEX),
    'track_duration':                (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_TRACK_DURATION_READ,
                                      CONTROLLER_INDEX),
    'track_position_read':           (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_TRACK_POSITION_READ,
                                      CONTROLLER_INDEX),
    'track_position_set':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_TRACK_POSITION_SET,
                                      CONTROLLER_INDEX),
    'playback_speed_get':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PLAYBACK_SPEED_READ,
                                      CONTROLLER_INDEX),
    'playback_speed_set':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PLAYBACK_SPEED_SET,
                                      CONTROLLER_INDEX),
    'seeking_speed_get':             (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_SEEKING_SPEED_READ,
                                      CONTROLLER_INDEX),
    'icon_obj_id_read':              (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_ICON_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'next_track_obj_id_read':        (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_NEXT_TRACK_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'next_track_obj_id_set':         (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_NEXT_TRACK_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'parent_group_obj_id_read':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PARENT_GROUP_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_group_obj_id_read':     (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CURRENT_GROUP_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_group_obj_id_set':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CURRENT_GROUP_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'playing_order_read':            (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PLAYING_ORDER_READ,
                                      CONTROLLER_INDEX),
    'playing_order_set':             (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PLAYING_ORDER_SET,
                                      CONTROLLER_INDEX),
    'playing_orders_supported_read': (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_PLAYING_ORDERS_SUPPORTED_READ,
                                      CONTROLLER_INDEX),
    'media_state_read':              (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_MEDIA_STATE_READ,
                                      CONTROLLER_INDEX),
    'opcodes_supported_read':        (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_OPCODES_SUPPORTED_READ,
                                      CONTROLLER_INDEX),
    'content_control_id_read':       (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CONTENT_CONTROL_ID_READ,
                                      CONTROLLER_INDEX),
    'segments_obj_id_read':          (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_SEGMENTS_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_track_obj_id_read':     (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CURRENT_TRACK_OBJ_ID_READ,
                                      CONTROLLER_INDEX),
    'current_track_obj_id_set':      (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CURRENT_TRACK_OBJ_ID_SET,
                                      CONTROLLER_INDEX),
    'control_point_command':         (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_CMD_SEND,
                                      CONTROLLER_INDEX),
    'search_control_point_command':  (defs.BTP_SERVICE_ID_MCP,
                                      defs.BTP_MCP_CMD_SCP_SEND,
                                      CONTROLLER_INDEX),
}


def mcp_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MCP)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def mcp_discover(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['discovery'], data=data)

    mcp_command_rsp_succ()


def mcp_track_duration_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['track_duration'], data=data)

    mcp_command_rsp_succ()


def mcp_track_position_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['track_position_read'], data=data)

    mcp_command_rsp_succ()


def mcp_track_position_set(position, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("I", position))

    iutctl.btp_socket.send(*MCP['track_position_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playback_speed_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playback_speed_get'], data=data)

    mcp_command_rsp_succ()


def mcp_playback_speed_set(speed, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    iutctl = get_iut()

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", speed))

    iutctl.btp_socket.send(*MCP['playback_speed_set'], data=data)

    mcp_command_rsp_succ()


def mcp_seeking_speed_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['seeking_speed_get'], data=data)

    mcp_command_rsp_succ()


def mcp_icon_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['icon_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_next_track_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['next_track_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_next_track_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['next_track_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_parent_group_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['parent_group_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_group_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_group_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_group_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_group_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playing_order_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_order_read'], data=data)

    mcp_command_rsp_succ()


def mcp_playing_order_set(order, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", order))

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_order_set'], data=data)
    mcp_command_rsp_succ()


def mcp_playing_orders_supported_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['playing_orders_supported_read'], data=data)

    mcp_command_rsp_succ()


def mcp_media_state_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['media_state_read'], data=data)

    mcp_command_rsp_succ()


def mcp_content_control_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['content_control_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_segments_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['segments_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_track_obj_id_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_track_obj_id_read'], data=data)

    mcp_command_rsp_succ()


def mcp_current_track_obj_id_set(obj_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    obj_id_bytes = obj_id.to_bytes(6, 'little')
    data.extend(obj_id_bytes)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['current_track_obj_id_set'], data=data)
    mcp_command_rsp_succ()


def mcp_opcodes_supported_read(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['opcodes_supported_read'], data=data)

    mcp_command_rsp_succ()


def mcp_control_point_cmd(opcode, use_param, param, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("b", opcode))
    data.extend(struct.pack("b", use_param))
    data.extend(struct.pack("I", param))

    iutctl = get_iut()

    iutctl.btp_socket.send(*MCP['control_point_command'], data=data)
    mcp_command_rsp_succ()


def mcp_search_control_point_cmd(search_type, param, bd_addr_type=None, bd_addr=None):
    logging.debug("")

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
    logging.debug('%r', data)

    fmt = '<B6sbHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, player_name, icon_obj_id, icon_url, track_changed,\
        track_title, track_duration, track_position, playback_speed, seeking_speed,\
        segments_obj_id, current_track_obj_id, next_track_obj_id, current_group_obj_id, \
        parent_group_obj_id, playing_order, playing_orders_supported, media_state, cp, \
        opcodes_supported, scp, search_results_obj_id, content_control_id, feature, \
        obj_name, obj_type, obj_size, obj_prop, obj_created, obj_modified, obj_id, \
        oacp, olcp = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug(
        "MCP Discovery: MCS and OTS service characteristic handles:addr %r, addr_type %r, Status %r, Player Name %r,"
        "Icon Obj ID %r, Icon Url %r, Track Changed %r, Track Title %r,Track Duration %r, Track Position %r,"
        "Playback Speed %r, Seeking Speed %r, Segments Obj ID %r, Current Track Obj ID %r, Next Track Obj ID %r,"
        "Current Group Obj ID %r, Parent Group Obj ID %r, Playing Order %r, Playing Orders Supported %r, Media State %r,"
        "Control Point %r, Opcodes Supported %r, Search Control Point %r, Search Results Obj ID %r, Content Control ID %r,"
        "OTS Feature %r, Object Name %r, Object Type %r,Object Size %r, Object Properties %r, Object Created %r,"
        "Object Modified %r, Object ID %r, Object Action Control Point %r, Object List Control Point %r",
        addr, addr_type, status, player_name, icon_obj_id, icon_url, track_changed, track_title, track_duration,
        track_position, playback_speed, seeking_speed, segments_obj_id, current_track_obj_id, next_track_obj_id,
        current_group_obj_id, parent_group_obj_id, playing_order, playing_orders_supported, media_state, cp,
        opcodes_supported, scp, search_results_obj_id, content_control_id, feature, obj_name, obj_type, obj_size,
        obj_prop, obj_created, obj_modified, obj_id, oacp, olcp)

    mcp.event_received(defs.BTP_MCP_EV_DISCOVERED, (addr_type, addr, status, player_name,
                                                icon_obj_id, icon_url, track_changed,
                                                track_title, track_duration, track_position,
                                                playback_speed, seeking_speed, segments_obj_id,
                                                current_track_obj_id, next_track_obj_id,
                                                current_group_obj_id, parent_group_obj_id,
                                                playing_order, playing_orders_supported,
                                                media_state, cp, opcodes_supported, scp,
                                                search_results_obj_id, content_control_id, feature,
                                                obj_name, obj_type, obj_size, obj_prop, obj_created,
                                                obj_modified, obj_id, oacp, olcp))


def mcp_track_duration_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, duration = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Track Duration ev: addr %r, addr_type %r, Status %r, track duration %r",
                  addr, addr_type, status, duration)

    mcp.event_received(defs.BTP_MCP_EV_TRACK_DURATION, (addr_type, addr, status,
                                                    duration))


def mcp_track_position_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, position = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Track Position ev: addr %r, addr_type %r, Status %r, track position %r",
                  addr, addr_type, status, position)

    mcp.event_received(defs.BTP_MCP_EV_TRACK_POSITION, (addr_type, addr, status,
                                                    position))


def mcp_playback_speed_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, speed = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Playback speed: addr %r, addr_type %r, Status %r, playback speed %r",
                  addr, addr_type, status, speed)

    mcp.event_received(defs.BTP_MCP_EV_PLAYBACK_SPEED, (addr_type, addr, status,
                                                    speed))


def mcp_seeking_speed_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, speed = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Seeking speed: addr %r, addr_type %r, Status %r, seeking speed %r",
                  addr, addr_type, status, speed)

    mcp.event_received(defs.BTP_MCP_EV_SEEKING_SPEED, (addr_type, addr, status,
                                                   speed))


def mcp_icon_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Icon Object ID: addr %r, addr_type %r, Status %r, Icon Object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_ICON_OBJ_ID, (addr_type, addr, status,
                                                 obj_id))


def mcp_next_track_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Next Track Object ID: addr %r, addr_type %r, Status %r, Next Track object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_NEXT_TRACK_OBJ_ID, (addr_type, addr, status,
                                                       obj_id))


def mcp_parent_group_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Parent Group Object ID: addr %r, addr_type %r, Status %r, Parent Group Object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_PARENT_GROUP_OBJ_ID, (addr_type, addr, status,
                                                         obj_id))


def mcp_current_group_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Current Group Object ID: addr %r, addr_type %r, Status %r, Current Group Object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_CURRENT_GROUP_OBJ_ID, (addr_type, addr, status,
                                                          obj_id))


def mcp_playing_order_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, order = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Playing Order: addr %r, addr_type %r, Status %r, playing order %r",
                  addr, addr_type, status, order)

    mcp.event_received(defs.BTP_MCP_EV_PLAYING_ORDER, (addr_type, addr, status,
                                                   order))


def mcp_playing_orders_supported_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, orders = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Playing orders supported: addr %r, addr_type %r, Status %r, playing orders supported %r",
                  addr, addr_type, status, orders)

    mcp.event_received(defs.BTP_MCP_EV_PLAYING_ORDERS_SUPPORTED, (addr_type, addr,
                                                              status, orders))


def mcp_media_state_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, state = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Media State: addr %r, addr_type %r, Status %r, media state %r",
                  addr, addr_type, status, state)

    mcp.event_received(defs.BTP_MCP_EV_MEDIA_STATE, (addr_type, addr, status,
                                                 state))


def mcp_opcodes_supported_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, opcodes = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Opcodes Supported: addr %r, addr_type %r, Status %r, opcodes %r",
                  addr, addr_type, status, opcodes)

    mcp.event_received(defs.BTP_MCP_EV_OPCODES_SUPPORTED, (addr_type, addr,
                                                       status, opcodes))


def mcp_content_control_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, ccid = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Content Control ID: addr %r, addr_type %r, Status %r, content control ID %r",
                  addr, addr_type, status, ccid)

    mcp.event_received(defs.BTP_MCP_EV_CONTENT_CONTROL_ID, (addr_type, addr, status,
                                                        ccid))


def mcp_segments_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Track Segments Object ID: addr %r, addr_type %r, Status %r, Track Segments Object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_SEGMENTS_OBJ_ID, (addr_type, addr, status,
                                                     obj_id))


def mcp_current_track_obj_id_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    obj_id_bytes = data[-6:]
    obj_id = int.from_bytes(obj_id_bytes, byteorder='little', signed=False)

    logging.debug("MCP Current Track Object ID: addr %r, addr_type %r, Status %r, Current Track Object ID %r",
                  addr, addr_type, status, obj_id)

    mcp.event_received(defs.BTP_MCP_EV_CURRENT_TRACK_OBJ_ID, (addr_type, addr, status,
                                                          obj_id))


def mcp_control_point_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbbbI'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, opcode, use_param,\
        param = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Media Control Point: addr %r, addr_type %r, Status %r, Opcode %r, Param %r",
                  addr, addr_type, status, opcode, param)

    mcp.event_received(defs.BTP_MCP_EV_COMMAND, (addr_type, addr, status, opcode,
                                             use_param, param))


def mcp_search_control_point_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbbb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, status, param_len, search = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)

    param = struct.unpack_from(f'<{len(data) - fmt_size - 1}s',
                               data, offset=fmt_size)[0].decode('utf-8')

    logging.debug("MCP Search Control Point: addr %r, addr_type %r, Status %r, param_len %r, search type %r, param %r",
                  addr, addr_type, status, param_len, search, param)

    mcp.event_received(defs.BTP_MCP_EV_SEARCH, (addr_type, addr, status, param_len,
                                            search, param))


def mcp_cmd_ntf_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, requested_opcode,\
        result_code = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug(
        "MCP Media Control Point Notification: addr %r, addr_type %r, Status %r, Requested Opcode %r, Result Code %r",
        addr, addr_type, status, requested_opcode, result_code)

    mcp.event_received(defs.BTP_MCP_EV_CMD_NTF, (addr_type, addr, status,
                                             requested_opcode, result_code))


def mcp_search_ntf_ev(mcp, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, result_code = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("MCP Search Control Point Notification: addr %r, addr_type %r, Status %r, Result Code %r",
                  addr, addr_type, status, result_code)

    mcp.event_received(defs.BTP_MCP_EV_SEARCH_NTF, (addr_type, addr, status,
                                                result_code))


MCP_EV = {
    defs.BTP_MCP_EV_DISCOVERED: mcp_ev_discovery_completed,
    defs.BTP_MCP_EV_TRACK_DURATION: mcp_track_duration_ev,
    defs.BTP_MCP_EV_TRACK_POSITION: mcp_track_position_ev,
    defs.BTP_MCP_EV_PLAYBACK_SPEED: mcp_playback_speed_ev,
    defs.BTP_MCP_EV_SEEKING_SPEED: mcp_seeking_speed_ev,
    defs.BTP_MCP_EV_ICON_OBJ_ID: mcp_icon_obj_id_ev,
    defs.BTP_MCP_EV_NEXT_TRACK_OBJ_ID: mcp_next_track_obj_id_ev,
    defs.BTP_MCP_EV_PARENT_GROUP_OBJ_ID: mcp_parent_group_obj_id_ev,
    defs.BTP_MCP_EV_CURRENT_GROUP_OBJ_ID: mcp_current_group_obj_id_ev,
    defs.BTP_MCP_EV_PLAYING_ORDER: mcp_playing_order_ev,
    defs.BTP_MCP_EV_PLAYING_ORDERS_SUPPORTED: mcp_playing_orders_supported_ev,
    defs.BTP_MCP_EV_MEDIA_STATE: mcp_media_state_ev,
    defs.BTP_MCP_EV_OPCODES_SUPPORTED: mcp_opcodes_supported_ev,
    defs.BTP_MCP_EV_CONTENT_CONTROL_ID: mcp_content_control_id_ev,
    defs.BTP_MCP_EV_SEGMENTS_OBJ_ID: mcp_segments_obj_id_ev,
    defs.BTP_MCP_EV_CURRENT_TRACK_OBJ_ID: mcp_current_track_obj_id_ev,
    defs.BTP_MCP_EV_COMMAND: mcp_control_point_ev,
    defs.BTP_MCP_EV_SEARCH: mcp_search_control_point_ev,
    defs.BTP_MCP_EV_CMD_NTF: mcp_cmd_ntf_ev,
    defs.BTP_MCP_EV_SEARCH_NTF: mcp_search_ntf_ev
}
