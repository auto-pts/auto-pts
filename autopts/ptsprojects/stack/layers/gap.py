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

from autopts.ptsprojects.stack.common import Property, wait_for_event
from autopts.pybtp.types import AdType, IOCap, Addr


class ConnParams:
    def __init__(self, conn_itvl_min, conn_itvl_max, conn_latency, supervision_timeout):
        self.conn_itvl_min = conn_itvl_min
        self.conn_itvl_max = conn_itvl_max
        self.conn_latency = conn_latency
        self.supervision_timeout = supervision_timeout


class GapConnection:
    def __init__(self, addr, addr_type):
        self.addr = addr
        self.addr_type = addr_type
        self.sec_level = 0


class Gap:
    def __init__(self, name, manufacturer_data, appearance, svc_data, flags,
                 svcs, uri=None, periodic_data=None, le_supp_feat=None):

        self.ad = {}
        self.sd = {}

        if name:
            if isinstance(name, bytes):
                self.ad[AdType.name_full] = name
            else:
                self.ad[AdType.name_full] = name.encode('utf-8')

        if manufacturer_data:
            self.sd[AdType.manufacturer_data] = manufacturer_data

        self.name = name
        self.manufacturer_data = manufacturer_data
        self.appearance = appearance
        self.svc_data = svc_data
        self.flags = flags
        self.svcs = svcs
        self.uri = uri
        self.le_supp_feat = le_supp_feat
        self.periodic_data = periodic_data
        self.oob_legacy = "0000000000000000FE12036E5A889F4D"

        # If disconnected - None
        # If connected - remote address tuple (addr, addr_type)
        # GapConnection
        self.connections = {}
        self.current_settings = Property({
            "Powered": False,
            "Connectable": False,
            "Fast Connectable": False,
            "Discoverable": False,
            "Bondable": False,
            "Link Level Security": False,  # Link Level Security (Sec. mode 3)
            "SSP": False,  # Secure Simple Pairing
            "BREDR": False,  # Basic Rate/Enhanced Data Rate
            "HS": False,  # High Speed
            "LE": False,  # Low Energy
            "Advertising": False,
            "SC": False,  # Secure Connections
            "Debug Keys": False,
            "Privacy": False,
            "Controller Configuration": False,
            "Static Address": False,
            "Extended Advertising": False,
            "SC Only": False,
        })
        self.iut_bd_addr = Property({
            "address": None,
            "type": None,
        })
        self.discoverying = Property(False)
        self.found_devices = Property([])  # List of found devices

        self.passkey = Property(None)
        self.conn_params = Property(None)
        self.pairing_failed_rcvd = Property(None)
        self.encryption_failed_rcvd = Property(None)

        # bond_lost data (addr_type, addr)
        self.bond_lost_ev_data = Property(None)
        # if no io_cap was set it means we use no_input_output
        self.io_cap = IOCap.no_input_output

        # if IUT doesn't support it, it should be disabled in preconditions
        self.pair_user_interaction = True
        self.periodic_report_rxed = False
        self.periodic_sync_established_rxed = False
        self.periodic_transfer_received = False

        # Used for MMI handling
        self.delay_mmi = False

    def add_connection(self, addr, addr_type):
        self.connections[addr] = GapConnection(addr=addr,
                                               addr_type=addr_type)

    def remove_connection(self, addr):
        return self.connections.pop(addr)

    def wait_for_connection(self, timeout, conn_count=1, addr=None):
        if self.is_connected(conn_count=conn_count, addr=addr):
            return True

        return wait_for_event(timeout, self.is_connected, conn_count=conn_count, addr=addr)

    def wait_for_disconnection(self, timeout, addr=None):
        if not self.is_connected(addr=addr):
            return True

        return wait_for_event(timeout, lambda: not self.is_connected(addr=addr))

    def is_connected(self, conn_count=1, addr=None):
        if addr:
            return addr in self.connections

        return len(self.connections) >= conn_count

    def wait_periodic_report(self, timeout):
        if self.periodic_report_rxed:
            return True

        if wait_for_event(timeout, lambda: self.periodic_report_rxed):
            self.periodic_report_rxed = False
            return True

        return False

    def wait_periodic_established(self, timeout):
        if self.periodic_sync_established_rxed:
            return True

        if wait_for_event(timeout, lambda: self.periodic_sync_established_rxed):
            self.periodic_sync_established_rxed = False
            return True

        return False

    def wait_periodic_transfer_received(self, timeout):
        if self.periodic_transfer_received:
            return True

        if wait_for_event(timeout, lambda: self.periodic_transfer_received):
            self.periodic_transfer_received = False
            return True

        return False

    def current_settings_set(self, key):
        if key in self.current_settings.data:
            self.current_settings.data[key] = True
        else:
            logging.error("%s %s not in current_settings",
                          self.current_settings_set.__name__, key)

    def current_settings_clear(self, key):
        if key in self.current_settings.data:
            self.current_settings.data[key] = False
        else:
            logging.error("%s %s not in current_settings",
                          self.current_settings_clear.__name__, key)

    def current_settings_get(self, key):
        if key in self.current_settings.data:
            return self.current_settings.data[key]
        logging.error("%s %s not in current_settings",
                      self.current_settings_get.__name__, key)
        return False

    def iut_addr_get_str(self):
        addr = self.iut_bd_addr.data["address"]
        if addr:
            return addr.decode("utf-8")
        return "000000000000"

    def iut_addr_set(self, addr, addr_type):
        self.iut_bd_addr.data["address"] = addr
        self.iut_bd_addr.data["type"] = addr_type

    def iut_addr_is_random(self):
        return self.iut_bd_addr.data["type"] == Addr.le_random

    def iut_has_privacy(self):
        return self.current_settings_get("Privacy")

    def set_conn_params(self, params):
        self.conn_params.data = params

    def reset_discovery(self):
        self.discoverying.data = True
        self.found_devices.data = []

    def set_passkey(self, passkey):
        self.passkey.data = passkey

    def get_passkey(self, timeout=5):
        if self.passkey.data is None:
            wait_for_event(timeout, lambda: self.passkey.data)

        return self.passkey.data

    def gap_wait_for_pairing_fail(self, timeout=5):
        if self.pairing_failed_rcvd.data is None:
            wait_for_event(timeout, lambda: self.pairing_failed_rcvd.data)

        return self.pairing_failed_rcvd.data

    def gap_wait_for_encryption_fail(self, timeout=5):
        if self.encryption_failed_rcvd.data is None:
            wait_for_event(timeout, lambda: self.encryption_failed_rcvd.data)

        return self.encryption_failed_rcvd.data

    def gap_wait_for_lost_bond(self, timeout=5):
        if self.bond_lost_ev_data.data is None:
            wait_for_event(timeout, lambda: self.bond_lost_ev_data.data)

        return self.bond_lost_ev_data.data

    def set_connection_sec_level(self, addr, level):
        self.connections[addr].sec_level = level

    def gap_wait_for_sec_lvl_change(self, level, timeout=5, addr=None):
        if not self.is_connected(addr=addr):
            raise Exception("Not connected")

        if addr:
            conn = self.connections[addr]
        else:
            addr, conn = list(self.connections.items())[0]

        if conn.sec_level != level:
            wait_for_event(timeout, lambda: conn.sec_level == level)

        return conn.sec_level

    def gap_set_pair_user_interaction(self, user_interaction):
        self.pair_user_interaction = user_interaction
