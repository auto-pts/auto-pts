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


class BAP:
    class Peer:
        def __init__(self):
            self.discovery_completed = False

    def __init__(self):
        self.peers = {}
        self.ase_configs = []
        self.broadcast_id = None
        self.broadcast_id_2 = None
        self.broadcast_code = ''
        self.hdl_wid_114_cnt = 0
        self.event_queues = {
            defs.BTP_BAP_EV_DISCOVERY_COMPLETED: [],
            defs.BTP_BAP_EV_CODEC_CAP_FOUND: [],
            defs.BTP_BAP_EV_ASE_FOUND: [],
            defs.BTP_BAP_EV_STREAM_RECEIVED: [],
            defs.BTP_BAP_EV_BAA_FOUND: [],
            defs.BTP_BAP_EV_BIS_FOUND: [],
            defs.BTP_BAP_EV_BIS_SYNCED: [],
            defs.BTP_BAP_EV_BIS_STREAM_RECEIVED: [],
            defs.BTP_BAP_EV_SCAN_DELEGATOR_FOUND: [],
            defs.BTP_BAP_EV_BROADCAST_RECEIVE_STATE: [],
            defs.BTP_BAP_EV_PA_SYNC_REQ: [],
        }
        self.event_handlers = {
            defs.BTP_BAP_EV_DISCOVERY_COMPLETED: self._ev_discovery_completed,
        }

    def get_peer(self, addr_type, addr):
        key = (addr_type, addr)
        try:
            return self.peers[key]
        except KeyError:
            self.peers[key] = self.Peer()
            return self.peers[key]

    def set_broadcast_code(self, broadcast_code):
        self.broadcast_code = broadcast_code

    def set_broadcast_id(self, broadcast_id):
        self.broadcast_id = broadcast_id

    def set_broadcast_id_2(self, broadcast_id):
        self.broadcast_id_2 = broadcast_id

    def event_received(self, event_type, event_data_tuple):
        if event_type in self.event_handlers:
            self.event_handlers[event_type](*event_data_tuple)

        self.event_queues[event_type].append(event_data_tuple)

    def wait_codec_cap_found_ev(self, addr_type, addr, pac_dir, timeout, remove=False):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_CODEC_CAP_FOUND],
            lambda _addr_type, _addr, _pac_dir, *_:
                (addr_type, addr, pac_dir) == (_addr_type, _addr, _pac_dir),
            timeout, remove)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_DISCOVERY_COMPLETED],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_ase_found_ev(self, addr_type, addr, ase_dir, timeout, remove=False):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_ASE_FOUND],
            lambda _addr_type, _addr, _ase_dir, *_:
                (addr_type, addr, ase_dir) == (_addr_type, _addr, _ase_dir),
            timeout, remove)

    def wait_stream_received_ev(self, addr_type, addr, ase_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_STREAM_RECEIVED],
            lambda _addr_type, _addr, _ase_id, *_:
                (addr_type, addr, ase_id) == (_addr_type, _addr, _ase_id),
            timeout, remove)

    def wait_baa_found_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_BAA_FOUND],
            lambda ev: (addr_type, addr) == (ev['addr_type'], ev['addr']),
            timeout, remove)

    def wait_bis_found_ev(self, broadcast_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_BIS_FOUND],
            lambda ev: broadcast_id == ev['broadcast_id'],
            timeout, remove)

    def wait_bis_synced_ev(self, broadcast_id, bis_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_BIS_SYNCED],
            lambda ev: (broadcast_id, bis_id) == (ev['broadcast_id'], ev['bis_id']),
            timeout, remove)

    def wait_bis_stream_received_ev(self, broadcast_id, bis_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_BIS_STREAM_RECEIVED],
            lambda ev: (broadcast_id, bis_id) == (ev['broadcast_id'], ev['bis_id']),
            timeout, remove)

    def wait_scan_delegator_found_ev(self, addr_type, addr, timeout, remove=False):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_SCAN_DELEGATOR_FOUND],
            lambda ev: (addr_type, addr) == (ev["addr_type"], ev["addr"]),
            timeout, remove)

    def wait_broadcast_receive_state_ev(self, broadcast_id, peer_addr_type, peer_addr,
                                        broadcaster_addr_type, broadcaster_addr,
                                        pa_sync_state, timeout, remove=False):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_BROADCAST_RECEIVE_STATE],
            lambda ev: (broadcast_id, peer_addr_type, peer_addr,
                        broadcaster_addr_type, broadcaster_addr,
                        pa_sync_state) ==
                       (ev["broadcast_id"], ev["addr_type"], ev["addr"],
                        ev["broadcaster_addr_type"], ev["broadcaster_addr"],
                        ev['pa_sync_state']),
            timeout, remove)

    def wait_pa_sync_req_ev(self, addr_type, addr, timeout, remove=False):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_BAP_EV_PA_SYNC_REQ],
            lambda ev: (addr_type, addr) == (ev["addr_type"], ev["addr"]),
            timeout, remove)

    def _ev_discovery_completed(self, addr_type, addr, status):
        peer = self.get_peer(addr_type, addr)
        peer.discovery_completed = (status == defs.BTP_STATUS_SUCCESS)
