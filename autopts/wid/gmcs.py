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
from enum import IntEnum

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


class MediaProxyOp(IntEnum):
    """Media Control Point opcodes from the Media Control Service specification.

    Passed as the ``opcode`` argument of ``btp.gmcs_control_point_cmd()``.
    """

    PLAY = 0x01
    PAUSE = 0x02
    FAST_REWIND = 0x03
    FAST_FORWARD = 0x04
    STOP = 0x05
    MOVE_RELATIVE = 0x10
    PREV_SEGMENT = 0x20
    NEXT_SEGMENT = 0x21
    FIRST_SEGMENT = 0x22
    LAST_SEGMENT = 0x23
    GOTO_SEGMENT = 0x24
    PREV_TRACK = 0x30
    NEXT_TRACK = 0x31
    FIRST_TRACK = 0x32
    LAST_TRACK = 0x33
    GOTO_TRACK = 0x34
    PREV_GROUP = 0x40
    NEXT_GROUP = 0x41
    FIRST_GROUP = 0x42
    LAST_GROUP = 0x43
    GOTO_GROUP = 0x44


# wid handlers section begin
def hdl_wid_4(params: WIDParams):
    """Please configure an initial state to Inactive state"""
    stack = get_stack()

    media_pl_state = btp.gmcs_inactive_state_set()

    if media_pl_state != 0:
        return False
    elif params.test_case_name == 'GMCS/SR/MCP/BV-37-C':
        next_track_id = btp.gmcs_next_track_obj_id_get()
        stack.gmcs.track_obj_id = next_track_id
        # This is validated in hdl_wid_32
    elif params.test_case_name == 'GMCS/SR/MCP/BV-33-C':
        # This is validated in hdl_wid_32
        current_track_id = btp.gmcs_current_track_obj_id_get()
        stack.gmcs.current_track_obj_id = current_track_id
        # Initial condition from Test Spec
        btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_TRACK, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-53-C':
        # Initial condition from Test Spec
        btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_GROUP, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-61-C':
        # Initial condition from Test Spec
        btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_GROUP, 0)

    return True


def hdl_wid_7(params: WIDParams):
    """Please configure that current track position set to a position outside
       the First Segment."""

    btp.gmcs_control_point_cmd(MediaProxyOp.LAST_SEGMENT, 0)

    return True


def hdl_wid_8(params: WIDParams):
    """Please configure that current track position set to a position outside
       the Last Segment"""

    btp.gmcs_control_point_cmd(MediaProxyOp.FIRST_SEGMENT, 0)

    return True


def hdl_wid_9(params: WIDParams):
    """Please configure that current track set to NOT the First Track"""

    btp.gmcs_control_point_cmd(MediaProxyOp.LAST_TRACK, 0)

    return True


def hdl_wid_10(params: WIDParams):
    """Please configure that current track set to NOT the Last Track"""

    btp.gmcs_control_point_cmd(MediaProxyOp.PREV_TRACK, 0)

    return True


def hdl_wid_11(params: WIDParams):
    """Please configure that current track set to the Second Track"""

    btp.gmcs_control_point_cmd(MediaProxyOp.FIRST_TRACK, 0)

    btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_TRACK, 0)

    return True


def hdl_wid_12(params: WIDParams):
    """Please configure that current track set to the next to the Last Track"""

    btp.gmcs_control_point_cmd(MediaProxyOp.LAST_TRACK, 0)
    btp.gmcs_control_point_cmd(MediaProxyOp.PREV_TRACK, 0)
    btp.gmcs_control_point_cmd(MediaProxyOp.PREV_TRACK, 0)

    # Setting current track to last_track - 2 works.

    return True


def hdl_wid_13(params: WIDParams):
    """Please configure that current group set to the Second Group"""

    btp.gmcs_control_point_cmd(MediaProxyOp.FIRST_GROUP, 0)
    btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_GROUP, 0)

    return True


def hdl_wid_14(params: WIDParams):
    """Please configure that current group set to the next to the Last Group"""

    btp.gmcs_control_point_cmd(MediaProxyOp.LAST_GROUP, 0)
    btp.gmcs_control_point_cmd(MediaProxyOp.PREV_GROUP, 0)

    return True


def hdl_wid_32(params: WIDParams):
    """Please confirm that Current Track has been moved to a Valid Track."""

    stack = get_stack()

    current_track_obj_id = btp.gmcs_current_track_obj_id_get()

    if params.test_case_name == 'GMCS/SR/MCP/BV-33-C':
        if stack.gmcs.current_track_obj_id != current_track_obj_id:
            return False
    elif params.test_case_name == 'GMCS/SR/MCP/BV-37-C':
        if current_track_obj_id != stack.gmcs.track_obj_id:
            return False

    return True


def hdl_wid_44(params: WIDParams):
    """If the IUT supports transitioning to an active state, please set the
       current track to a track other than the first or last within a group
       of tracks."""

    btp.gmcs_control_point_cmd(MediaProxyOp.GOTO_TRACK, 1, 2)

    return True


def hdl_wid_45(params: WIDParams):
    """Please configure that current track position is greater than 0 and less than
    the duration of the track."""

    btp.gmcs_control_point_cmd(MediaProxyOp.STOP, 0)
    btp.gmcs_control_point_cmd(MediaProxyOp.MOVE_RELATIVE, 1, 1)

    # PTS seems to also expect IUT to set initial state in this WID
    # (although in test spec this is separate step)
    if params.test_case_name == 'GMCS/SR/MCP/BV-12-C ':
        btp.gmcs_control_point_cmd(MediaProxyOp.PLAY, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-14-C':
        btp.gmcs_control_point_cmd(MediaProxyOp.FAST_FORWARD, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-75-C':
        btp.gmcs_inactive_state_set()

    return True


def hdl_wid_20001(params: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""

    stack = get_stack()

    if params.test_case_name in ['GMCS/SR/MCP/BV-05-C', 'GMCS/SR/MCP/BV-06-C']:
        btp.gmcs_control_point_cmd(MediaProxyOp.NEXT_SEGMENT, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-09-C':
        btp.gmcs_control_point_cmd(MediaProxyOp.PLAY, 0)

    btp.gap_set_connectable()
    btp.gap_start_advertising(ad=stack.gap.ad)

    if params.test_case_name == "GMCS/SR/SP/BV-01-C":
        btp.gmcs_parent_group_set()

    return True


def hdl_wid_20109(_: WIDParams):
    """
    Please send indications for Characteristic 'Object List Control Point' to the PTS.
    """

    return True


def hdl_wid_20141(params: WIDParams):
    """Please update Media Player Name/Track Title characteristic with value
       whose length is greater than the (ATT_MTU-3). Click OK when it is ready."""

    if params.test_case_name == 'GMCS/SR/SPN/BV-01-C':
        btp.gmcs_player_name_set("Player Name Initial Value")
        return True

    return False


def hdl_wid_20142(params: WIDParams):
    """Please update Media Player Name/Track Title characteristic and send a
       notification containing the updated value of the characteristic with
       a different value whose length is greater than the (ATT_MTU-3)."""

    if params.test_case_name == 'GMCS/SR/SPN/BV-01-C':
        btp.gmcs_player_name_set("Player Name Updated Value")
        return True

    return False
