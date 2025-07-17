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

from autopts.ptsprojects.stack.common import wait_event_with_condition
from autopts.pybtp import defs


class CSIP:
    def __init__(self):
        self.member_cnt = 0
        self.wid_cnt = 0
        self.event_queues = {
            defs.BTP_CSIP_EV_DISCOVERED: [],
            defs.BTP_CSIP_EV_SIRK: [],
            defs.BTP_CSIP_EV_LOCK: []
        }

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)

    def wait_discovery_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_CSIP_EV_DISCOVERED],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_sirk_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_CSIP_EV_SIRK],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_lock_ev(self, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_CSIP_EV_LOCK],
            lambda *_: True, timeout, remove)
