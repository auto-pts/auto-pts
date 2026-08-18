#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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

from autopts.ptsprojects.stack.common import wait_for_event


class AvrcpConnection:
    def __init__(self, addr):
        self.addr = addr
        self.conn_type = []  # list()
        self.data_rx = {}  # defaultdict(list)
        self.data_tx = {}  # defaultdict(list)

    def connected(self, conn_type):
        self.conn_type.append(conn_type)

    def disconnected(self, conn_type):
        self.conn_type.remove(conn_type)
        if not self.conn_type:
            self.addr = None

    def rx(self, ev, data):
        self.data_rx.setdefault(ev, []).append(data)

    def rx_data_get(self, ev, timeout, clear):
        if ev in self.data_rx and len(self.data_rx[ev]) != 0:
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        if wait_for_event(timeout, lambda: ev in self.data_rx and len(self.data_rx[ev]) != 0):
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        return None

    def rx_data_clear(self, ev, data):
        self.data_rx[ev].remove(data)


class AVRCP:
    def __init__(self):
        self.connections = []
        self.media_player_items = []
        self.virtual_filesystem_items = []
        self.search_items = []
        self.now_playing_items = []
        self.discovered_uids = []
        self.uid_counter = 0

    def conn_lookup_addr(self, addr):
        for conn in self.connections:
            if conn.addr == addr:
                return conn
        return None

    def add_connection(self, addr, conn_type):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            conn = AvrcpConnection(addr)
            self.connections.append(conn)
        conn.connected(conn_type)

    def remove_connection(self, addr, conn_type):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            logging.error("unknown AVRCP connection")
            return
        if conn_type not in conn.conn_type:
            logging.warning("connection already disconnected")
            return
        conn.disconnected(conn_type)
        if not conn.conn_type:
            self.connections.remove(conn)

    def is_connected(self, addr, conn_type):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            return False
        if conn_type not in conn.conn_type:
            return False
        return True

    def wait_for_connection(self, addr, conn_type, timeout):
        if self.is_connected(addr=addr, conn_type=conn_type):
            return True
        return wait_for_event(timeout, self.is_connected, addr=addr, conn_type=conn_type)

    def wait_for_disconnection(self, addr, conn_type, timeout):
        if not self.is_connected(addr=addr, conn_type=conn_type):
            return True
        return wait_for_event(timeout, lambda: not self.is_connected(addr=addr, conn_type=conn_type))

    def rx(self, addr, ev, data):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            logging.error("unknown AVRCP connection")
            return

        conn.rx(ev, data)

    def rx_data_get(self, addr, ev, timeout, clear=True):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            logging.error("unknown AVRCP connection")
            return None

        return conn.rx_data_get(ev, timeout, clear)

    def rx_data_clear(self, addr, ev, data):
        conn = self.conn_lookup_addr(addr)
        if conn is None:
            logging.error("unknown AVRCP connection")
            return None

        conn.rx_data_clear(ev, data)
