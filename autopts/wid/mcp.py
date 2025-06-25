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

import logging
import re

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


class SearchTypes:
    TRACK_NAME = 0x01
    ARTIST_NAME = 0x02
    ALBUM_NAME = 0x03
    GROUP_NAME = 0x04
    EARLIEST_YEAR = 0x05
    LATEST_YEAR = 0x06
    GENRE = 0x07
    ONLY_TRACKS = 0x08
    ONLY_GORUPS = 0x09


def hdl_wid_15(params: WIDParams):
    """Please confirm IUT received all error Result Codes -
    OPCODE NOT SUPPORTED(0x02), MEDIA PLAYER INACTIVE(0x03)
    and COMMAND CANNOT BE COMPLETED(0x04) on Media Control Point Notification"""

    stack = get_stack()

    if stack.mcp.error_opcodes != [2, 3, 4]:
        return False

    return True


def hdl_wid_16(params: WIDParams):
    """Please confirm IUT received Result Code 0x02(FAILURE) on Search Result
       Control Point Notification."""

    stack = get_stack()

    if stack.mcp.error_opcodes != [2]:
        return False

    return True


def hdl_wid_33(params: WIDParams):
    """Please write Search Control Point with Track Name."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.TRACK_NAME, 'Track Name',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_34(params: WIDParams):
    """Please write Search Control Point with Artist Name."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.ARTIST_NAME, 'Artist Name',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_35(params: WIDParams):
    """Please write Search Control Point with Album Name."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.ALBUM_NAME, 'Album name',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_36(params: WIDParams):
    """Please write Search Control Point with Group Name."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.GROUP_NAME, 'Group Name',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_37(params: WIDParams):
    """Please write Search Control Point with Earliest Year."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.EARLIEST_YEAR, '1999',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_38(params: WIDParams):
    """Please write Search Control Point with Latest Year."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.LATEST_YEAR, '2999',
                                     addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_39(params: WIDParams):
    """Please write Search Control Point with Genre."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.GENRE, 'Genre', addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_40(params: WIDParams):
    """Please write Search Control Point with Only Tracks."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.ONLY_TRACKS, "0", addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_41(params: WIDParams):
    """Please write Search Control Point with Only Groups."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.mcp_search_control_point_cmd(SearchTypes.ONLY_GORUPS, "0", addr_type, addr)
    ev = stack.mcp.wait_search_control_point_ev(addr_type, addr, 10)
    if ev is None:
        return False

    return True


def hdl_wid_20001(_: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(params: WIDParams):
    """
    Please initiate a GATT connection to the PTS. Verify that the Implementation
    Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.gap_conn()
    stack.gap.wait_for_connection(timeout=5, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30)

    return True


def hdl_wid_20103(params: WIDParams):
    """
    Please take action to discover the xxxx from the xxxx.
    Discover the primary service if needed. Verify that the Implementation Under
    Test (IUT) can send Discover All Characteristics command.
    """

    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.mcp_discover(addr_type, addr)
    ev = stack.mcp.wait_discovery_completed_ev(addr_type, addr, 20, remove=False)
    if ev is None:
        return False

    return True


def hdl_wid_20106(params: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of Audio Input State
    characteristic to enable notification.Descriptor handle value: 0x00B3
    """

    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.mcp_discover(addr_type, addr)
    ev = stack.mcp.wait_discovery_completed_ev(addr_type, addr, 20, remove=True)
    if ev is None:
        return False

    return True


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read xxxx characteristic with handle = 0xXXXX.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    stack.mcp.object_id = None

    if "Track Duration" in params.description:
        btp.mcp_track_duration_get(addr_type, addr)
        ev = stack.mcp.wait_track_duration_ev(addr_type, addr, 10)

    elif "Track Position" in params.description:
        btp.mcp_track_position_get(addr_type, addr)
        ev = stack.mcp.wait_track_position_ev(addr_type, addr, 10)

    elif "Playback Speed" in params.description:
        btp.mcp_playback_speed_get(addr_type, addr)
        ev = stack.mcp.wait_playback_speed_ev(addr_type, addr, 10)

    elif "Seeking Speed" in params.description:
        btp.mcp_seeking_speed_get(addr_type, addr)
        ev = stack.mcp.wait_seeking_speed_ev(addr_type, addr, 10)

    elif "Icon Object" in params.description:
        btp.mcp_icon_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_icon_obj_id_ev(addr_type, addr, 10)

    elif "Next Track Object" in params.description:
        btp.mcp_next_track_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_next_track_obj_id_ev(addr_type, addr, 10)
        if ev is not None:
            stack.mcp.object_id = ev[3]

    elif "Current Track Object" in params.description:
        btp.mcp_current_track_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_current_track_obj_id_ev(addr_type, addr, 10)
        if ev is not None:
            stack.mcp.object_id = ev[3]

    elif "Parent Group" in params.description:
        btp.mcp_parent_group_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_parent_group_obj_id_ev(addr_type, addr, 10)

    elif "Current Track Segments" in params.description:
        btp.mcp_segments_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_segments_obj_id_ev(addr_type, addr, 10)

    elif "Current Group Object" in params.description:
        btp.mcp_current_group_obj_id_read(addr_type, addr)
        ev = stack.mcp.wait_current_group_obj_id_ev(addr_type, addr, 10)
        if ev is not None:
            stack.mcp.object_id = ev[3]

    elif "Playing Order Supported" in params.description:
        btp.mcp_playing_orders_supported_read(addr_type, addr)
        ev = stack.mcp.wait_playing_orders_supported_ev(addr_type, addr, 10)

    elif "Playing Order" in params. description:
        btp.mcp_playing_order_read(addr_type, addr)
        ev = stack.mcp.wait_playing_order_ev(addr_type, addr, 10)

    elif "Media State" in params.description:
        btp.mcp_media_state_read(addr_type, addr)
        ev = stack.mcp.wait_media_state_ev(addr_type, addr, 10)

    elif "Opcodes Supported" in params.description:
        btp.mcp_opcodes_supported_read(addr_type, addr)
        ev = stack.mcp.wait_opcodes_supported_ev(addr_type, addr, 10)

    elif "Content Control" in params.description:
        btp.mcp_content_control_id_read(addr_type, addr)
        ev = stack.mcp.wait_content_control_id_ev(addr_type, addr, 10)

    if ev is None:
        return False

    return True


def hdl_wid_20109(_: WIDParams):
    """
    Please send indications for Characteristic 'Object List Control Point' to the PTS.
    """

    return True


def hdl_wid_20110(params: WIDParams):
    """
    Please send write request to handle 0xXXXX with following value.
    Any attribute value
    """

    # This WID appears randomly instead of hdl_wid_20121

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    """ PTS is providing handle value instead of expected action so we map it here based on
    test case name
    """
    if 'MCP/CL/CGGIT/CHA/BV-07-C' == params.test_case_name:
        btp.mcp_track_position_set(100, addr_type, addr)
        ev = stack.mcp.wait_track_position_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-08-C' == params.test_case_name:
        btp.mcp_playback_speed_set(64, addr_type, addr)
        ev = stack.mcp.wait_playback_speed_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-11-C' == params.test_case_name:
        btp.mcp_current_track_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_current_track_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-12-C' == params.test_case_name:
        btp.mcp_next_track_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_next_track_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-14-C' == params.test_case_name:
        btp.mcp_current_group_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_current_group_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-15-C' == params.test_case_name:
        btp.mcp_playing_order_set(2, addr_type, addr)
        ev = stack.mcp.wait_playing_order_ev(addr_type, addr, 10)
    else:
        ev = None

    if ev is None:
        return False

    return True


def hdl_wid_20116(params: WIDParams):
    """Please send command to the PTS to discover all mandatory characteristics
     of the Microphone Control supported by the IUT. Discover primary service if needed.
     """

    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.mcp_discover(addr_type, addr)
    ev = stack.mcp.wait_discovery_completed_ev(addr_type, addr, 20, remove=False)
    if ev is None:
        return False

    return True


def hdl_wid_20121(params: WIDParams):
    """Please write value with write command (without response) to handle 0x00F3
     with following value. Any attribute value"""

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    """ PTS is providing handle value instead of expected action so we map it here based on
    test case name
    """
    if 'MCP/CL/CGGIT/CHA/BV-07-C' == params.test_case_name:
        btp.mcp_track_position_set(100, addr_type, addr)
        ev = stack.mcp.wait_track_position_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-08-C' == params.test_case_name:
        btp.mcp_playback_speed_set(64, addr_type, addr)
        ev = stack.mcp.wait_playback_speed_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-11-C' == params.test_case_name:
        btp.mcp_current_track_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_current_track_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-12-C' == params.test_case_name:
        btp.mcp_next_track_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_next_track_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-14-C' == params.test_case_name:
        btp.mcp_current_group_obj_id_set(stack.mcp.object_id, addr_type, addr)
        ev = stack.mcp.wait_current_group_obj_id_ev(addr_type, addr, 10)
    elif 'MCP/CL/CGGIT/CHA/BV-15-C' == params.test_case_name:
        btp.mcp_playing_order_set(2, addr_type, addr)
        ev = stack.mcp.wait_playing_order_ev(addr_type, addr, 10)
    else:
        ev = None

    if ev is None:
        return False

    return True


def hdl_wid_20136(params: WIDParams):
    """Please write value with Write Request or Write Without Response to handle
       0x010F with following value.
       Media Control Point:
       Opcode: [1 (0x01)] Play"""

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    pattern = r'\[(\d+)'
    if 'MCP/CL/SPE' in params.test_case_name:
        # Error handling tests
        if "Search Control Point" in params.description:
            btp.mcp_search_control_point_cmd(1, 'WildCard', addr_type, addr)
            ev = stack.mcp.wait_search_notification_ev(addr_type, addr, 10)
            stack.mcp.error_opcodes.append(ev[3])
            if ev is None:
                return False
            return True
        if "Media Control Point" in params.description:
            btp.mcp_control_point_cmd(1, 0, 0, addr_type, addr)
            ev = stack.mcp.wait_cmd_notification_ev(addr_type, addr, 10)
            stack.mcp.error_opcodes.append(ev[4])
            if ev is None:
                return False
            return True

    opcode = int(re.search(pattern, params.description).group(1))
    if 'Parameter' in params.description:
        use_param, param = 1, 100
    else:
        use_param, param = 0, 0

    btp.mcp_control_point_cmd(opcode, use_param, param, addr_type, addr)

    ev = stack.mcp.wait_control_point_ev(addr_type, addr, 10)

    if ev is None:
        return False

    return True


def hdl_wid_20206(params: WIDParams):
    """Please verify that for each supported characteristic, attribute handle/UUID
     pair(s) is returned to the upper tester.
     Media Player Name: Attribute Handle = 0x00E2
     Characteristic Properties = 0x12
     Handle = 0x00E3
     UUID = 0x2B93

     Media Player Icon Object: Attribute Handle = 0x00E5
     Characteristic Properties = 0x02
     Handle = 0x00E6
     UUID = 0x2B94
     ...
     """

    stack = get_stack()

    if params.test_case_name == "MCP/CL/CGGIT/SER/BV-02-C":
        chars = stack.mcp.event_queues[defs.BTP_MCP_EV_DISCOVERED][0][3:25]
        chrc_list = [f'{chrc:04X}' for chrc in chars]
    elif params.test_case_name == "MCP/CL/CGGIT/SER/BV-03-C":
        chars = stack.mcp.event_queues[defs.BTP_MCP_EV_DISCOVERED][0][25:]
        chrc_list = [f'{chrc:04X}' for chrc in chars]
        # Object First-Created and Object Last-Modified Characteristic are omitted
        # because Server doest not have access to real time clock (data is set to 0)
        while '0000' in chrc_list:
            chrc_list.remove('0000')

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    desc_params = pattern.findall(params.description)
    if not desc_params:
        logging.error("parsing error")
        return False

    desc_params_list = desc_params[2::4]

    if params.test_case_name == "MCP/CL/CGGIT/SER/BV-03-C":
        # Also Object List Filter characteristic isn't supported.
        unsupported_chrc = ['012A', '012C', '0138', '013D', '013F', '013A']
        for handle in unsupported_chrc:
            while handle in desc_params_list:
                desc_params_list.remove(handle)

    if desc_params_list == chrc_list:
        return True

    return False


def hdl_wid_20144(params: WIDParams):
    """Please click Yes if IUT support Write Command(without response), otherwise click No."""

    return False


def hdl_wid_20145(params: WIDParams):
    """
    Please click Yes if IUT support Write Request, otherwise click No.
    """

    return True


def hdl_wid_20146(params: WIDParams):
    """Please click Yes if IUT support Write Long characteristic
       (Prepare Write and Execute Write), otherwise click No."""

    return False
