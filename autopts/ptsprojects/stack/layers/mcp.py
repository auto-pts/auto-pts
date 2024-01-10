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
from autopts.ptsprojects.stack.common import wait_for_queue_event
from autopts.pybtp import defs


class MCP:
    def __init__(self):
        self.event_queues = {
            defs.MCP_DISCOVERED_EV: [],
            defs.MCP_TRACK_DURATION_EV: [],
            defs.MCP_TRACK_POSITION_EV: [],
            defs.MCP_PLAYBACK_SPEED_EV: [],
            defs.MCP_SEEKING_SPEED_EV: [],
            defs.MCP_ICON_OBJ_ID_EV: [],
            defs.MCP_NEXT_TRACK_OBJ_ID_EV: [],
            defs.MCP_PARENT_GROUP_OBJ_ID_EV: [],
            defs.MCP_CURRENT_GROUP_OBJ_ID_EV: [],
            defs.MCP_PLAYING_ORDER_EV: [],
            defs.MCP_PLAYING_ORDERS_SUPPORTED_EV: [],
            defs.MCP_MEDIA_STATE_EV: [],
            defs.MCP_OPCODES_SUPPORTED_EV: [],
            defs.MCP_CONTENT_CONTROL_ID_EV: [],
            defs.MCP_SEGMENTS_OBJ_ID_EV: [],
            defs.MCP_CURRENT_TRACK_OBJ_ID_EV: [],
            defs.MCP_COMMAND_EV: [],
            defs.MCP_SEARCH_EV: [],
            defs.MCP_CMD_NTF_EV: [],
            defs.MCP_SEARCH_NTF_EV: []
        }
        self.error_opcodes = []

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_DISCOVERED_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_track_duration_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_TRACK_DURATION_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_track_position_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_TRACK_POSITION_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playback_speed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_PLAYBACK_SPEED_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_seeking_speed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_SEEKING_SPEED_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_icon_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_ICON_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_next_track_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_NEXT_TRACK_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_parent_group_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_PARENT_GROUP_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_current_group_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_CURRENT_GROUP_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playing_order_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_PLAYING_ORDER_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_playing_orders_supported_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_PLAYING_ORDERS_SUPPORTED_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_media_state_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_MEDIA_STATE_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_opcodes_supported_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_OPCODES_SUPPORTED_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_content_control_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_CONTENT_CONTROL_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_segments_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_SEGMENTS_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_current_track_obj_id_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_CURRENT_TRACK_OBJ_ID_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_control_point_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_COMMAND_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_search_control_point_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_SEARCH_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_cmd_notification_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_CMD_NTF_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_search_notification_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.MCP_SEARCH_NTF_EV],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
