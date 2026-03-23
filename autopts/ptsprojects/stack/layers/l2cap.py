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
import logging
from enum import Enum, auto

from autopts.ptsprojects.stack.common import wait_for_event


class L2capChanState(Enum):
    """ L2CAP Channel state """
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


class L2capChan:
    """ L2CAP Channel """
    def __init__(self, chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                 bd_addr_type, bd_addr):
        self.id = chan_id
        self.psm = psm
        self.peer_mtu = peer_mtu
        self.peer_mps = peer_mps
        self.our_mtu = our_mtu
        self.our_mps = our_mps
        self.peer_bd_addr_type = bd_addr_type
        self.peer_bd_addr = bd_addr
        self.disconn_reason = None
        self.data_tx = []
        self.data_rx = []
        self.state = L2capChanState.CONNECTING

    def is_connected(self):
        """ if channel is in connected state"""
        return self.state == L2capChanState.CONNECTED

    def is_connecting(self):
        """ if channel is in connecting state"""
        return self.state == L2capChanState.CONNECTING

    def connected(self, psm, peer_mtu, peer_mps, our_mtu, our_mps, bd_addr_type, bd_addr):
        """ set channel into connected state """
        self.psm = psm
        self.peer_mtu = peer_mtu
        self.peer_mps = peer_mps
        self.our_mtu = our_mtu
        self.our_mps = our_mps
        self.peer_bd_addr_type = bd_addr_type
        self.peer_bd_addr = bd_addr
        self.state = L2capChanState.CONNECTED

    def disconnected(self, psm, bd_addr_type, bd_addr, reason):
        """ set channel into disconnected state """
        self.psm = None
        self.peer_bd_addr_type = None
        self.peer_bd_addr = None
        self.disconn_reason = reason
        self.state = L2capChanState.DISCONNECTED

    def rx(self, data):
        self.data_rx.append(data)

    def tx(self, data):
        self.data_tx.append(data)

    def rx_data_get(self, timeout):
        if len(self.data_rx) != 0:
            return self.data_rx

        if wait_for_event(timeout, lambda: len(self.data_rx) != 0):
            return self.data_rx

        return None

    def tx_data_get(self):
        return self.data_tx


class L2cap:
    """L2CAP layer - manages L2CAP channels """
    connection_success = 0x0000
    unknown_le_psm = 0x0002
    no_resources = 0x0004
    insufficient_authen = 0x0005
    insufficient_author = 0x0006
    insufficient_key_sz = 0x0007
    insufficient_enc = 0x0008
    invalid_source_cid = 0x0009
    source_cid_already_used = 0x000a
    unacceptable_parameters = 0x000b
    invalid_parameters = 0x000c

    def __init__(self, psm, initial_mtu):
        # PSM used for testing for Client role
        self.psm = psm
        self.initial_mtu = initial_mtu
        self.channels = []
        self.hold_credits = 0
        self.num_channels = 2

    def chan_lookup_id(self, chan_id):
        """ lookup L2CAP channel with specified channel ID"""
        for chan in self.channels:
            if chan.id == chan_id:
                return chan
        return None

    def clear_data(self):
        """ clear data for all channels """
        for chan in self.channels:
            chan.data_tx = []
            chan.data_rx = []

    def reconfigured(self, chan_id, peer_mtu, peer_mps, our_mtu, our_mps):
        """ Called when specific channel was reconfigured """
        channel = self.chan_lookup_id(chan_id)
        channel.peer_mtu = peer_mtu
        channel.peer_mps = peer_mps
        channel.our_mtu = our_mtu
        channel.our_mps = our_mps

    def psm_set(self, psm):
        self.psm = psm

    def num_channels_set(self, num_channels):
        self.num_channels = num_channels

    def hold_credits_set(self, hold_credits):
        self.hold_credits = hold_credits

    def initial_mtu_set(self, initial_mtu):
        self.initial_mtu = initial_mtu

    def connect(self, chan_ids):
        """ Called when specified channels are pending connection """
        for chan_id in chan_ids:
            chan = self.chan_lookup_id(chan_id)
            if chan:
                raise Exception(f'Channel already exists {chan}')

            chan = L2capChan(chan_id, 0, 0, 0, 0, 0, None, None)
            self.channels.append(chan)

    def connected(self, chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                  bd_addr_type, bd_addr):
        """ Called when specified channel is connected """
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            # incoming connection
            chan = L2capChan(chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                             bd_addr_type, bd_addr)
            self.channels.append(chan)

        if chan.is_connected():
            logging.error(f'Channel already connected {chan}')
            return

        chan.connected(psm, peer_mtu, peer_mps, our_mtu, our_mps,
                       bd_addr_type, bd_addr)

    def disconnected(self, chan_id, psm, bd_addr_type, bd_addr, reason):
        """ Called when specified channel is disconnected """
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return

        if not chan.is_connected() and not chan.is_connecting():
            logging.error(f'Channel already disconnected {chan}')
            return

        chan.disconnected(psm, bd_addr_type, bd_addr, reason)

        # Remove channel from saved channels
        self.channels.remove(chan)

    def is_connected(self, chan_id):
        """ Check if channel is connected """
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            return False

        return chan.is_connected()

    def is_connecting(self, chan_id):
        """ Check if channel is connecting """
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            return False

        return chan.is_connecting()

    def wait_for_disconnection(self, chan_id, timeout):
        """ Wait for channel disconnection """
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            return True

        return wait_for_event(timeout, lambda: not self.is_connected(chan_id) and not self.is_connecting(chan_id))

    def wait_for_connection(self, chan_id, timeout=5):
        """ Wait for channel connection """
        if self.is_connected(chan_id):
            return True

        return wait_for_event(timeout, self.is_connected, chan_id)

    def rx(self, chan_id, data):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return

        chan.rx(data)

    def tx(self, chan_id, data):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return

        chan.tx(data)

    def rx_data_get(self, chan_id, timeout):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return None

        return chan.rx_data_get(timeout)

    def rx_data_get_all(self, timeout):
        return [chan.rx_data_get(timeout) for chan in self.channels]

    def tx_data_get(self, chan_id):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return None

        return chan.tx_data_get()

    def tx_data_get_all(self):
        return [chan.tx_data_get() for chan in self.channels]
