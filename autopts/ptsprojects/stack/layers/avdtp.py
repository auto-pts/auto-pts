#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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

from autopts.pybtp import defs


class AVDTP:
    def __init__(self):
        self.event_queues = {
            defs.BTP_AVDTP_EV_DUMMY_COMPLETED: [],
        }

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)
