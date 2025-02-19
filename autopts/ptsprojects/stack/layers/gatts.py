#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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


class GATTS:
    def __init__(self):
        self.event_queues = {
            defs.BTP_GATTS_EV_ATTR_VALUE_CHANGED: [],
        }

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)

    def attr_value_changed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_GATTS_EV_ATTR_VALUE_CHANGED],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
