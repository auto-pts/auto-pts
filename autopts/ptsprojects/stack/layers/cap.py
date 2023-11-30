#
# auto-pts - The Bluetooth PTS Automation Framework
#
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


class CAP:
    def __init__(self):
        self.event_queues = {
            defs.CAP_EV_DISCOVERY_COMPLETED: [],
            defs.CAP_EV_UNICAST_START_COMPLETED: [],
            defs.CAP_EV_UNICAST_STOP_COMPLETED: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.CAP_EV_DISCOVERY_COMPLETED],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_unicast_start_completed_ev(self, cig_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.CAP_EV_UNICAST_START_COMPLETED],
            lambda _cig_id: cig_id == _cig_id,
            timeout, remove)

    def wait_unicast_stop_completed_ev(self, cig_id, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.CAP_EV_UNICAST_STOP_COMPLETED],
            lambda _cig_id, *_: cig_id == _cig_id,
            timeout, remove)
