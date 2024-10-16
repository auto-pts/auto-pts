#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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


class PBP:
    def __init__(self):
        self.event_queues = {
            defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND: [],
        }

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)

    def wait_public_broadcast_event_found_ev(self, addr_type, addr, broadcast_name, timeout, remove=True):
        return wait_for_queue_event(
            self.event_queues[defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND],
            lambda ev: (addr_type, addr, broadcast_name) == (ev['addr_type'], ev['addr'], ev['broadcast_name']),
            timeout, remove)
