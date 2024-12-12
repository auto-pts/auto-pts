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


class VCP:
    def __init__(self):
        self.wid_counter = 0
        self.event_queues = {
            defs.BTP_VCP_EV_DISCOVERED: [],
            defs.BTP_VCP_EV_STATE: [],
            defs.BTP_VCP_EV_FLAGS: [],
            defs.BTP_VCP_EV_PROCEDURE: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_VCP_EV_DISCOVERED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_vcp_state_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_VCP_EV_STATE],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_vcp_flags_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_VCP_EV_FLAGS],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_vcp_procedure_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_VCP_EV_PROCEDURE],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
