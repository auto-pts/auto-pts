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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug

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
        MEDIA_PROXY_OP_NEXT_TRACK = 0x31
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_TRACK, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-53-C':
        # Initial condition from Test Spec
        MEDIA_PROXY_OP_NEXT_GROUP = 0x41
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_GROUP, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-61-C':
        # Initial condition from Test Spec
        MEDIA_PROXY_OP_NEXT_GROUP = 0x41
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_GROUP, 0)

    return True


def hdl_wid_7(params: WIDParams):
    """Please configure that current track position set to a position outside
       the First Segment."""

    MEDIA_PROXY_OP_LAST_SEGMENT = 0x23

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_LAST_SEGMENT, 0)

    return True


def hdl_wid_8(params: WIDParams):
    """Please configure that current track position set to a position outside
       the Last Segment"""

    MEDIA_PROXY_OP_FIRST_SEGMENT = 0x22

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_FIRST_SEGMENT, 0)

    return True


def hdl_wid_9(params: WIDParams):
    """Please configure that current track set to NOT the First Track"""

    MEDIA_PROXY_OP_LAST_TRACK = 0x33

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_LAST_TRACK, 0)

    return True


def hdl_wid_10(params: WIDParams):
    """Please configure that current track set to NOT the Last Track"""

    MEDIA_PROXY_OP_PREV_TRACK = 0x30

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PREV_TRACK, 0)

    return True


def hdl_wid_11(params: WIDParams):
    """Please configure that current track set to the Second Track"""

    MEDIA_PROXY_OP_NEXT_TRACK = 0x31
    MEDIA_PROXY_OP_FIRST_TRACK = 0x32

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_FIRST_TRACK, 0)

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_TRACK, 0)

    return True


def hdl_wid_12(params: WIDParams):
    """Please configure that current track set to the next to the Last Track"""

    MEDIA_PROXY_OP_PREV_TRACK = 0x30
    MEDIA_PROXY_OP_LAST_TRACK = 0x33

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_LAST_TRACK, 0)
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PREV_TRACK, 0)
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PREV_TRACK, 0)

    # Setting current track to last_track - 2 works.

    return True


def hdl_wid_13(params: WIDParams):
    """Please configure that current group set to the Second Group"""

    MEDIA_PROXY_OP_NEXT_GROUP = 0x41
    MEDIA_PROXY_OP_FIRST_GROUP = 0x42

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_FIRST_GROUP, 0)
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_GROUP, 0)

    return True


def hdl_wid_14(params: WIDParams):
    """Please configure that current group set to the next to the Last Group"""

    MEDIA_PROXY_OP_PREV_GROUP = 0x40
    MEDIA_PROXY_OP_LAST_GROUP = 0x43

    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_LAST_GROUP, 0)
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PREV_GROUP, 0)

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

    if params.test_case_name in ['GMCS/SR/MCP/BV-41-C', 'GMCS/SR/MCP/BV-45-C']:
        # This applies only for testcases where media player is initially
        # in inactive state
        MEDIA_PROXY_OP_NEXT_TRACK = 0x31
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_TRACK, 0)

    return True


def hdl_wid_45(params: WIDParams):
    """Please configure that current track position is greater than 0 and less than
    the duration of the track."""

    MEDIA_PROXY_OP_STOP = 0x05
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_STOP, 0)
    MEDIA_PROXY_OP_MOVE_RELATIVE = 0x10
    btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_MOVE_RELATIVE, 1, 1)

    # PTS seems to also expect IUT to set initial state in this WID
    # (although in test spec this is separate step)
    if params.test_case_name == 'GMCS/SR/MCP/BV-12-C ':
        MEDIA_PROXY_OP_PLAY = 0x01
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PLAY, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-14-C':
        MEDIA_PROXY_OP_FAST_FORWARD = 0x04
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_FAST_FORWARD, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-75-C':
        btp.gmcs_inactive_state_set()

    return True


def hdl_wid_20001(params: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""

    stack = get_stack()

    if params.test_case_name in ['GMCS/SR/MCP/BV-05-C', 'GMCS/SR/MCP/BV-06-C']:
        MEDIA_PROXY_OP_NEXT_SEGMENT = 0x21
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_NEXT_SEGMENT, 0)
    elif params.test_case_name == 'GMCS/SR/MCP/BV-09-C':
        MEDIA_PROXY_OP_PLAY = 0x01
        btp.gmcs_control_point_cmd(MEDIA_PROXY_OP_PLAY, 0)

    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

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

    # TODO: GMCS/SR/SPN/BV-01-C, GMCS/SR/SPN/BV-02-C
    #  There is no way to do that with current API.

    return False


def hdl_wid_20142(params: WIDParams):
    """Please update Track Title characteristic(Handle = 0x005E) and send a
       notification containing the updated value of the characteristic with
       a different value whose length is greater than the (ATT_MTU-3)."""

    # TODO: GMCS/SR/SPN/BV-01-C, GMCS/SR/SPN/BV-02-C
    #  There is no way to do that with current API.

    return False
