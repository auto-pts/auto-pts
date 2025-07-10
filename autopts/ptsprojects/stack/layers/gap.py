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
from dataclasses import dataclass

from autopts.ptsprojects.stack.common import Property, wait_for_event
from autopts.pybtp.types import Addr, AdType, IOCap


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


@dataclass(frozen=True)
class PeriodicBiginfo:
    '''
    Class that stores information about a BIG (Broadcast Isochronous Group) advertisement
    received during periodic advertising.

    This class represents a single entry containing information about a BIG advertisement
    that was discovered during periodic advertising scanning. It stores the advertiser's
    address and type, synchronization handle, advertising set ID, number of BIS streams
    in the group, and encryption status.

    Attributes:
        addr (str): Advertiser's Bluetooth address
        addr_type (int): Advertiser's address type (public or random)
        sync_handle (int): Synchronization handle for the periodic advertising train
        sid (int): Advertising Set ID that identifies the advertising set
        num_bis (int): Number of Broadcast Isochronous Streams in the BIG
        iso_interval (int): ISO interval for the BIG in units of 1.25ms
        max_pdu (int): Maximum size of the PDU (Protocol Data Unit) in octets
        sdu_interval (int): SDU (Service Data Unit) interval in microseconds
        max_sdu (int): Maximum size of the SDU in octets
        phy (int): PHY (Physical Layer) used for transmission (1 = 1M, 2 = 2M, or 3 = Coded)
        framing (int): Framing mode (0 = unframed, 1 = framed, Segment, or 2 = framed, Unsegmented)
        encryption (bool): Whether the BIG is encrypted
    '''
    addr: str
    addr_type: int
    sync_handle: int
    sid: int
    num_bis: int
    iso_interval: int
    max_pdu: int
    sdu_interval: int
    max_sdu: int
    phy: int
    framing: int
    encryption: bool


@dataclass(frozen=True)
class BisRx:
    '''
    Class that represents received data from a Broadcast Isochronous Stream (BIS).

    This class encapsulates data packets received from a specific BIS within a
    Broadcast Isochronous Group (BIG). It stores metadata about the received packet
    including control flags, timestamp, sequence number, and the actual payload data.

    Attributes:
        flags (int): Control flags for the BIS data packet
        timestamp (int): Timestamp indicating when the data was received
        seq_num (int): Sequence number for ordering packets in the stream
        stream_data (tuple): The actual payload data received in the BIS packet
    '''
    flags: int
    ts: int
    seq_num: int
    stream_data: tuple


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
        self.encryption_change_rcvd = Property(None)

        # bond_lost data (addr_type, addr)
        self.bond_lost_ev_data = Property(None)
        # if no io_cap was set it means we use no_input_output
        self.io_cap = IOCap.no_input_output

        # if IUT doesn't support it, it should be disabled in preconditions
        self.pair_user_interaction = True
        self.periodic_report_rxed = False
        self.periodic_sync_established_rxed = False
        self.periodic_transfer_received = False
        self.periodic_biginfo = []
        self.big_sync_established = False
        self.big_bis_data_path_setup = []
        self.big_bis_stream_rx = {}
        self.big_broadcast_code = None

        # Used for MMI handling
        self.delay_mmi = False
        self.mmi_round = {}

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

    def wait_big_established(self, timeout=10):
        if self.big_sync_established:
            return True

        if wait_for_event(timeout, lambda: self.big_sync_established):
            self.big_sync_established = False
            return True

        return False

    def read_periodic_biginfo(self, timeout=10):
        if len(self.periodic_biginfo):
            return self.periodic_biginfo.pop(0)

        if wait_for_event(timeout, lambda: len(self.periodic_biginfo) > 0):
            return self.periodic_biginfo.pop(0)

        return None

    def write_periodic_biginfo(self, addr, addr_type, sync_handle, sid, num_bis, iso_interval,
                               max_pdu, sdu_interval, max_sdu, phy, framing, encryption):
        if isinstance(encryption, int):
            encryption = bool(encryption)
        self.periodic_biginfo.append(PeriodicBiginfo(addr, addr_type, sync_handle, sid, num_bis,
                                                     iso_interval, max_pdu, sdu_interval, max_sdu,
                                                     phy, framing, encryption))

    def wait_bis_data_path_setup(self, bis_id=None, timeout=10):
        if bis_id is None:
            if len(self.big_bis_data_path_setup) > 0:
                return True

            if wait_for_event(timeout, lambda: len(self.big_bis_data_path_setup) > 0):
                return True
        else:
            if bis_id in self.big_bis_data_path_setup:
                return True

            if wait_for_event(timeout, lambda: bis_id in self.big_bis_data_path_setup):
                return True

        return False

    def read_bis_stream_received_data(self, bis_id=None, timeout=10):
        '''
        Retrieves and consumes received data from Broadcast Isochronous Streams (BIS).

        This method extracts the oldest data packet from the specified BIS stream or from
        any available stream if no specific BIS ID is provided. It removes the returned
        data from the internal buffer to prevent duplicate processing.

        Args:
            bis_id (int, optional): The specific BIS ID to read data from. If None,
                                   data from the first available stream will be returned.
            timeout (int, optional): Maximum time in seconds to wait for data if none
                                    is immediately available. Defaults to 10 seconds.

        Returns:
            BisRx or None:
                A BisRx object containing the packet metadata and payload if data is
                available, with attributes:
                    - flags: Control flags for the BIS data
                    - ts: Timestamp of when the data was received
                    - seq_num: Sequence number for ordering packets
                    - stream_data: The actual payload data
                Returns None if no data is available within the timeout period.

        Example:
            # Read data from a specific BIS stream
            packet = gap.read_bis_stream_received_data(bis_id=1)

            # Read data from any available BIS stream with a 5 second timeout
            packet = gap.read_bis_stream_received_data(timeout=5)
        '''
        if bis_id is None:
            if len(self.big_bis_stream_rx) > 0:
                return self.big_bis_stream_rx[list(self.big_bis_stream_rx.keys())[0]].pop(0)

            if wait_for_event(timeout, lambda: len(self.big_bis_stream_rx) > 0):
                return self.big_bis_stream_rx[list(self.big_bis_stream_rx.keys())[0]].pop(0)
        else:
            if bis_id in self.big_bis_stream_rx.keys():
                return self.big_bis_stream_rx[bis_id].pop(0)

            if wait_for_event(timeout, lambda: bis_id in self.big_bis_stream_rx.keys()):
                return self.big_bis_stream_rx[bis_id].pop(0)

        return None

    def write_bis_stream_received_data(self, bis_id, flags, ts, seq_num, stream_data):
        if bis_id in self.big_bis_stream_rx.keys():
            streams = self.big_bis_stream_rx[bis_id]
        else:
            streams = []
        streams.append(BisRx(flags, ts, seq_num, stream_data))
        self.big_bis_stream_rx[bis_id] = streams

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

    def get_mmi_round(self, mmi):
        if mmi in self.mmi_round.keys():
            return self.mmi_round[mmi]
        return 0

    def increase_mmi_round(self, mmi):
        if mmi in self.mmi_round.keys():
            self.mmi_round[mmi] += 1
        else:
            self.mmi_round[mmi] = 1

    def gap_wait_for_pairing_fail(self, timeout=5):
        if self.pairing_failed_rcvd.data is None:
            wait_for_event(timeout, lambda: self.pairing_failed_rcvd.data)

        return self.pairing_failed_rcvd.data

    def gap_wait_for_encryption_change(self, timeout=5):
        if self.encryption_change_rcvd.data is None:
            wait_for_event(timeout, lambda: self.encryption_change_rcvd.data)

        return self.encryption_change_rcvd.data

    def gap_wait_for_encrypted(self, timeout=5):
        if self.encryption_change_rcvd.data is None:
            wait_for_event(timeout, lambda: self.encryption_change_rcvd.data)

        if self.encryption_change_rcvd.data is None:
            return False

        (_, _, enabled, _) = self.encryption_change_rcvd.data

        if enabled == 0:
            return False
        else:
            return True

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
