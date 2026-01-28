#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025-2026 NXP
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

from autopts.ptsprojects.stack.common import wait_for_event


class RfcommChannel:
    def __init__(self, chan_id, mtu):
        self.id = chan_id
        self.mtu = mtu
        self._rx_buffer = []

    def rx(self, data):
        self._rx_buffer.append(data)

    def read_rx(self):
        return self._rx_buffer

    def clear_rx(self):
        self._rx_buffer = []


class RfcommConn:
    def __init__(self, addr):
        self.addr = addr
        self.channels = {}

    def add_channel(self, chan_id, mtu):
        chan = RfcommChannel(chan_id, mtu)
        self.channels[chan_id] = chan

    def remove_channel(self, chan_id):
        if chan_id in self.channels:
            del self.channels[chan_id]

    def get_channel(self, chan_id):
        return self.channels.get(chan_id)

    def rx(self, chan_id, data):
        chan = self.get_channel(chan_id)
        if chan:
            chan.rx(data)

    def read_rx(self, chan_id, clear=True):
        chan = self.get_channel(chan_id)
        if chan:
            data = chan.read_rx()
            if clear:
                chan.clear_rx()
            return data
        return []

    def clear_rx(self, chan_id):
        chan = self.get_channel(chan_id)
        if chan:
            chan.clear_rx()


class RFCOMM:
    def __init__(self):
        self.connections = {}

    def add_channel(self, addr, channel, mtu):
        if addr not in self.connections:
            self.connections[addr] = RfcommConn(addr)
        self.connections[addr].add_channel(channel, mtu)

    def remove_channel(self, addr, chan_id):
        if addr not in self.connections:
            return
        self.connections[addr].remove_channel(chan_id)

    def is_channel_connected(self, addr, chan_id):
        if addr not in self.connections:
            return False
        chan = self.connections[addr].get_channel(chan_id)
        return chan is not None

    def wait_for_channel_connected(self, addr, chan_id, timeout=20):
        wait_for_event(timeout, lambda: self.is_channel_connected(addr, chan_id))
        return self.is_channel_connected(addr, chan_id)

    def rx(self, addr, chan_id, data):
        if addr not in self.connections:
            return
        self.connections[addr].rx(chan_id, data)

    def read_rx(self, addr, chan_id, clear=True):
        if addr not in self.connections:
            return []
        return self.connections[addr].read_rx(chan_id, clear=clear)

    def wait_for_rx_data(self, addr, chan_id, clear=True, timeout=20):
        def has_rx_data():
            return len(self.read_rx(addr, chan_id, clear=False)) > 0
        wait_for_event(timeout, has_rx_data)
        return self.read_rx(addr, chan_id, clear=clear)
