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


class HAP:
    class Peer:
        def __init__(self):
            self.hearing_aid_features_handle = None
            self.hearing_aid_control_point_handle = None
            self.active_preset_index_handle = None
            self.discover_started = False
            self.discovery_completed = False

    def __init__(self):
        self.peers = {}
        self.event_queues = {
            defs.BTP_HAP_EV_IAC_DISCOVERY_COMPLETE: [],
            defs.BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE: [],
            defs.BTP_HAP_EV_PRESET_CHANGED: [],
        }
        self.event_handlers = {
            defs.BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE: self._ev_hauc_discovery_complete,
        }

    def get_peer(self, addr_type, addr):
        key = (addr_type, addr)
        try:
            return self.peers[key]
        except KeyError:
            self.peers[key] = self.Peer()
            return self.peers[key]

    def event_received(self, event_type, event_data_tuple):
        if event_type in self.event_handlers:
            self.event_handlers[event_type](*event_data_tuple)

        self.event_queues[event_type].append(event_data_tuple)

    def wait_iac_discovery_complete_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_HAP_EV_IAC_DISCOVERY_COMPLETE],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_hauc_discovery_complete_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def _ev_hauc_discovery_complete(self, addr_type, addr, status,
                                    hearing_aid_features_handle,
                                    hearing_aid_control_point_handle,
                                    active_preset_index_handle):
        if status != defs.BTP_STATUS_SUCCESS:
            return

        peer = self.get_peer(addr_type, addr)
        peer.hearing_aid_features_handle = hearing_aid_features_handle
        peer.hearing_aid_control_point_handle = hearing_aid_control_point_handle
        peer.active_preset_index_handle = active_preset_index_handle
        peer.discovery_completed = (status == defs.BTP_STATUS_SUCCESS)

    def wait_preset_changed_ev(self, addr_type, addr, timeout, change_id, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_HAP_EV_PRESET_CHANGED],
            lambda _addr_type, _addr, _change_id, *_:
                (addr_type, addr, change_id) == (_addr_type, _addr, _change_id),
            timeout, remove)
