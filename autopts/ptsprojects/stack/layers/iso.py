#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Demant A/S.
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


class ISO:
    def __init__(self):
        self.event_queues = {
            defs.BTP_ISO_EV_CONNECTED: [],
            defs.BTP_ISO_EV_DISCONNECTED: [],
            defs.BTP_ISO_EV_RECV: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_connected_ev(self, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ISO_EV_CONNECTED],
            lambda ev: True,
            timeout, remove)

    def wait_disconnected_ev(self, reason, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ISO_EV_DISCONNECTED],
            lambda ev: reason == ev['reason'],
            timeout, remove)

    def wait_recv_ev(self, handle, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ISO_EV_RECV],
            lambda ev: handle == ev['handle'],
            timeout, remove)
