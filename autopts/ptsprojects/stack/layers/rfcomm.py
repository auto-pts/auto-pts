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

from autopts.ptsprojects.stack.common import wait_for_queue_event
from autopts.pybtp import defs
import logging

class RfcommChan:
    def __init__(self, chan_id, mtu):
        self.id = chan_id
        self.mtu = mtu

class RFCOMM:
    def __init__(self):
        self.channels = []

    def chan_lookup_id(self, chan_id):
        for chan in self.channels:
            if chan.id == chan_id:
                return chan
        return None

    def connected(self, channel, mtu):
        chan = self.chan_lookup_id(channel)
        if chan is None:
            chan = RfcommChan(channel, mtu)
            self.channels.append(chan)

    def disconnected(self, chan_id):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return
        self.channels.remove(chan)
