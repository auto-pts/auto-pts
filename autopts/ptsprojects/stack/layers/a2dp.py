#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

from autopts.ptsprojects.stack.common import wait_event_with_condition, wait_for_event
from autopts.pybtp import defs


class A2DP:
    def __init__(self):
        self.connected = False
        self.addr = None
        self.audio_streaming = False

        # Same shape as the other layers that carry events a handler consumes
        # (mics, vcp, ascs and the rest): a queue per event type, appended by
        # event_received() and drained with wait_event_with_condition().
        self.event_queues = {
            defs.BTP_A2DP_EV_OPERATION_REQ: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def is_connected(self):
        return self.connected

    def wait_for_connection(self, timeout=20):
        wait_for_event(timeout, self.is_connected)
        return self.connected

    def wait_operation_req_ev(self, signal_id, timeout, remove=True):
        """Wait for the IUT to report that an AVDTP operation needs a decision.

        Returns None on timeout, which is the normal outcome for an IUT whose
        stack answers these operations itself, and is what makes the "if
        necessary" in the PTS prompts answerable.
        """
        return wait_event_with_condition(
            self.event_queues[defs.BTP_A2DP_EV_OPERATION_REQ],
            lambda sig, *_: sig == signal_id, timeout, remove)
