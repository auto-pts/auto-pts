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


class PACS:
    def __init__(self):
        self.event_queues = {
            defs.BTP_PACS_EV_CHARACTERISTIC_SUBSCRIBED: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_pacs_characteristic_subscribed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_PACS_EV_CHARACTERISTIC_SUBSCRIBED],
            lambda _addr_type, _addr, *_: (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
