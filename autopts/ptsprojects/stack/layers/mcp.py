#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2024, Codecoup.
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
from autopts.ptsprojects.stack.common import wait_event_with_condition
from autopts.pybtp import defs


class MCP:
    def __init__(self):
        self.event_queues = {
            defs.BTP_MCP_EV_DISCOVERED: [],
            defs.BTP_MCP_EV_TRACK_DURATION: [],
            defs.BTP_MCP_EV_TRACK_POSITION: [],
            defs.BTP_MCP_EV_PLAYBACK_SPEED: [],
            defs.BTP_MCP_EV_SEEKING_SPEED: [],
            defs.BTP_MCP_EV_ICON_OBJ_ID: [],
            defs.BTP_MCP_EV_NEXT_TRACK_OBJ_ID: [],
            defs.BTP_MCP_EV_PARENT_GROUP_OBJ_ID: [],
            defs.BTP_MCP_EV_CURRENT_GROUP_OBJ_ID: [],
            defs.BTP_MCP_EV_PLAYING_ORDER: [],
            defs.BTP_MCP_EV_PLAYING_ORDERS_SUPPORTED: [],
            defs.BTP_MCP_EV_MEDIA_STATE: [],
            defs.BTP_MCP_EV_OPCODES_SUPPORTED: [],
            defs.BTP_MCP_EV_CONTENT_CONTROL_ID: [],
            defs.BTP_MCP_EV_SEGMENTS_OBJ_ID: [],
            defs.BTP_MCP_EV_CURRENT_TRACK_OBJ_ID: [],
            defs.BTP_MCP_EV_COMMAND: [],
            defs.BTP_MCP_EV_SEARCH: [],
            defs.BTP_MCP_EV_CMD_NTF: [],
            defs.BTP_MCP_EV_SEARCH_NTF: []
        }
        self.error_opcodes = []
        self.object_id = None

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_DISCOVERED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_track_duration_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_TRACK_DURATION],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_track_position_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_TRACK_POSITION],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playback_speed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_PLAYBACK_SPEED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_seeking_speed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_SEEKING_SPEED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_icon_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_ICON_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_next_track_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_NEXT_TRACK_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_parent_group_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_PARENT_GROUP_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_current_group_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_CURRENT_GROUP_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playing_order_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_PLAYING_ORDER],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playing_orders_supported_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_PLAYING_ORDERS_SUPPORTED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_media_state_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_MEDIA_STATE],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_opcodes_supported_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_OPCODES_SUPPORTED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_content_control_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_CONTENT_CONTROL_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_segments_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_SEGMENTS_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_current_track_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_CURRENT_TRACK_OBJ_ID],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_control_point_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_COMMAND],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_search_control_point_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_SEARCH],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_cmd_notification_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_CMD_NTF],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_search_notification_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_MCP_EV_SEARCH_NTF],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
