#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
from threading import Lock, Timer, Event
from autopts.pybtp.types import AdType, Addr, IOCap

STACK = None


class GattAttribute:
    def __init__(self, handle, perm, uuid, att_rsp):
        self.handle = handle
        self.perm = perm
        self.uuid = uuid
        self.att_read_rsp = att_rsp


class GattService(GattAttribute):
    pass


class GattPrimary(GattService):
    pass


class GattSecondary(GattService):
    pass


class GattServiceIncluded(GattAttribute):
    def __init__(self, handle, perm, uuid, att_rsp, incl_svc_hdl, end_grp_hdl):
        GattAttribute.__init__(self, handle, perm, uuid, att_rsp)
        self.incl_svc_hdl = incl_svc_hdl
        self.end_grp_hdl = end_grp_hdl


class GattCharacteristic(GattAttribute):
    def __init__(self, handle, perm, uuid, att_rsp, prop, value_handle):
        GattAttribute.__init__(self, handle, perm, uuid, att_rsp)
        self.prop = prop
        self.value_handle = value_handle


class GattCharacteristicDescriptor(GattAttribute):
    def __init__(self, handle, perm, uuid, att_rsp, value):
        GattAttribute.__init__(self, handle, perm, uuid, att_rsp)
        self.value = value
        self.has_changed_cnt = 0
        self.has_changed = Event()


class GattDB:
    def __init__(self):
        self.db = dict()

    def attr_add(self, handle, attr):
        self.db[handle] = attr

    def attr_lookup_handle(self, handle):
        if handle in self.db:
            return self.db[handle]
        return None


class Property:
    def __init__(self, data):
        self._lock = Lock()
        self.data = data

    def __get__(self, instance, owner):
        with self._lock:
            return getattr(instance, self.data)

    def __set__(self, instance, value):
        with self._lock:
            setattr(instance, self.data, value)


def timeout_cb(flag):
    flag.clear()


class ConnParams:
    def __init__(self, conn_itvl_min, conn_itvl_max, conn_latency, supervision_timeout):
        self.conn_itvl_min = conn_itvl_min
        self.conn_itvl_max = conn_itvl_max
        self.conn_latency = conn_latency
        self.supervision_timeout = supervision_timeout


class Gap:
    def __init__(self, name, manufacturer_data, appearance, svc_data, flags,
                 svcs, uri=None):

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
        self.oob_legacy = "0000000000000000FE12036E5A889F4D"

        # If disconnected - None
        # If connected - remote address tuple (addr, addr_type)
        self.connected = Property(None)
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
        })
        self.iut_bd_addr = Property({
            "address": None,
            "type": None,
        })
        self.discoverying = Property(False)
        self.found_devices = Property([])  # List of found devices

        self.peripheral = Property(False) # IUT role in test

        self.passkey = Property(None)
        self.conn_params = Property(None)
        self.pairing_failed_rcvd = Property(None)

        # bond_lost data (addr_type, addr)
        self.bond_lost_ev_data = Property(None)
        # if no io_cap was set it means we use no_input_output
        self.io_cap = IOCap.no_input_output
        self.sec_level = Property(None)

    def wait_for_connection(self, timeout, conn_count=0):
        if self.is_connected(conn_count):
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.is_connected(conn_count):
                t.cancel()
                return True

        return False

    def wait_for_disconnection(self, timeout):
        if not self.is_connected(0):
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if not self.is_connected(0):
                t.cancel()
                return True

        return False

    def is_connected(self, conn_count):
        if conn_count > 0:
            if self.connected.data is not None:
                return len(self.connected.data) >= conn_count
            return False
        return self.connected.data

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
            flag = Event()
            flag.set()

            t = Timer(timeout, timeout_cb, [flag])
            t.start()

            while flag.is_set():
                if self.passkey.data:
                    t.cancel()
                    break

        return self.passkey.data

    def gap_wait_for_pairing_fail(self, timeout=5):
        if self.pairing_failed_rcvd.data is None:
            flag = Event()
            flag.set()

            t = Timer(timeout, timeout_cb, [flag])
            t.start()

            while flag.is_set():
                if self.pairing_failed_rcvd.data:
                    t.cancel()
                    break

        return self.pairing_failed_rcvd.data

    def gap_wait_for_lost_bond(self, timeout=5):
        if self.bond_lost_ev_data.data is None:
            flag = Event()
            flag.set()

            t = Timer(timeout, timeout_cb, [flag])
            t.start()

            while flag.is_set():
                if self.bond_lost_ev_data.data:
                    t.cancel()
                    break

        return self.bond_lost_ev_data.data

    def gap_wait_for_sec_lvl_change(self, level, timeout=5):
        if self.sec_level != level:
            flag = Event()
            flag.set()

            t = Timer(timeout, timeout_cb, [flag])
            t.start()

            while flag.is_set():
                if self.sec_level == level:
                    t.cancel()
                    break

        return self.sec_level


class Mesh:
    def __init__(self, uuid, uuid_lt2=None):

        # init data
        self.dev_uuid = uuid
        self.dev_uuid_lt2 = uuid_lt2
        self.static_auth = None
        self.output_size = 0
        self.output_actions = None
        self.input_size = 0
        self.input_actions = None
        self.crpl_size = 0
        self.auth_metod = 0

        self.oob_action = Property(None)
        self.oob_data = Property(None)
        self.is_provisioned = Property(False)
        self.is_initialized = False
        self.last_seen_prov_link_state = Property(None)
        self.prov_invalid_bearer_rcv = Property(False)

        # provision node data
        self.net_key = '0123456789abcdef0123456789abcdef'
        self.net_key_idx = 0x0000
        self.flags = 0x00
        self.iv_idx = 0x00000000
        self.seq_num = 0x00000000
        self.address_iut = 0x0003
        self.dev_key = '0123456789abcdef0123456789abcdef'
        self.iut_is_provisioner = False
        self.pub_key = Property(None)
        self.priv_key = Property(None)

        # health model data
        self.health_test_id = Property(0x00)
        self.health_current_faults = Property(None)
        self.health_registered_faults = Property(None)

        # vendor model data
        self.vendor_model_id = '0002'

        # IV update
        self.iv_update_timeout = Property(120)
        self.is_iv_test_mode_enabled = Property(False)
        self.iv_test_mode_autoinit = False

        # Network
        # net_recv_ev_store - store data for further verification
        self.net_recv_ev_store = Property(False)
        # net_recv_ev_data (ttl, ctl, src, dst, payload)
        self.net_recv_ev_data = Property(None)
        self.incomp_timer_exp = Property(False)
        self.friendship = Property(False)
        self.lpn = Property(False)

        # LPN
        self.lpn_subscriptions = []

        # Node Identity
        self.proxy_identity = False

        # Config Client
        self.net_idx = 0x0000
        self.address_lt1 = 0x0001
        self.address_lt2 = None
        self.net_key_index = 0x0000
        self.el_address = 0x0001
        self.status = Property(None)
        self.model_data = Property(None)
        self.app_idx = 0x0000
        self.provisioning_in_progress = Property(None)
        self.nodes_added = Property({})
        self.nodes_expected = Property([])

        # MMDL expected status data
        self.expect_status_data = Property({
            "Ack": True,
            'Status': [],
            'Remaining Time': 0,
        })

        # MMDL received status data
        self.recv_status_data = Property({
            "Ack": True,
            'Status': [],
            'Remaining Time': 0,
        })

    def get_dev_uuid(self):
        return self.dev_uuid

    def get_dev_uuid_lt2(self):
        return self.dev_uuid_lt2

    def set_prov_data(self, oob, output_size, output_actions, input_size,
                      input_actions, crpl_size, auth_method):
        self.static_auth = oob
        self.output_size = output_size
        self.output_actions = output_actions
        self.input_size = input_size
        self.input_actions = input_actions
        self.crpl_size = crpl_size
        self.auth_metod = auth_method

    def node_added(self, net_idx, addr, uuid, num_elems):
        self.nodes_added.data[uuid] = (net_idx, addr, uuid, num_elems)

    def expect_node(self, uuid):
        self.nodes_expected.data.append(uuid)

    def wait_for_node_added_uuid(self, timeout, uuid):
        if uuid in self.nodes_added.data:
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if uuid in self.nodes_added.data:
                t.cancel()
                return True

        return False

    def set_iut_provisioner(self, _is_prov):
        self.iut_is_provisioner = _is_prov

    def recv_status_data_set(self, key, data):
        if key in self.recv_status_data.data:
            self.recv_status_data.data[key] = data
        else:
            logging.error("%s %s not in store data",
                          self.recv_status_data_set.__name__, key)

    def recv_status_data_get(self, key):
        if key in self.recv_status_data.data:
            return self.recv_status_data.data[key]
        logging.error("%s %s not in store data",
                      self.recv_status_data_get.__name__, key)
        return False

    def expect_status_data_set(self, key, data):
        if key in self.expect_status_data.data:
            self.expect_status_data.data[key] = data
        else:
            logging.error("%s %s not in store data",
                          self.expect_status_data_set.__name__, key)

    def expect_status_data_get(self, key):
        if key in self.expect_status_data.data:
            return self.expect_status_data.data[key]
        logging.error("%s %s not in store data",
                      self.expect_status_data_get.__name__, key)
        return False

    def proxy_identity_enable(self):
        self.proxy_identity = True

    def wait_for_incomp_timer_exp(self, timeout):
        if self.incomp_timer_exp.data:
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.incomp_timer_exp.data:
                t.cancel()
                return True

        return False

    def wait_for_prov_link_close(self, timeout):
        if not self.last_seen_prov_link_state.data:
            self.last_seen_prov_link_state.data = ('uninitialized', None)

        state, _ = self.last_seen_prov_link_state.data
        if state == 'closed':
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            state, _ = self.last_seen_prov_link_state.data
            if state == 'closed':
                t.cancel()
                return True

        return False

    def wait_for_lpn_established(self, timeout):
        if self.lpn.data:
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.lpn.data:
                t.cancel()
                return True

        return False

    def wait_for_lpn_terminated(self, timeout):
        if not self.lpn.data:
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if not self.lpn.data:
                t.cancel()
                return True

        return False

    def pub_key_set(self, pub_key):
        self.pub_key.data = pub_key

    def pub_key_get(self):
        return self.pub_key.data

    def priv_key_set(self, priv_key):
        self.priv_key.data = priv_key

    def priv_key_get(self):
        return self.priv_key.data


class L2capChan:
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
        self.state = "init"  # "connected" / "disconnected"

    def _get_state(self, timeout):
        if self.state and self.state != "init":
            return self.state

        #  In case of self initiated connection, wait a while
        #  for connected/disconnected event
        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.state and self.state != "init":
                t.cancel()
                break

        return self.state

    def is_connected(self, timeout):
        state = self._get_state(timeout)
        if state == "connected":
            return True
        return False

    def connected(self, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                  bd_addr_type, bd_addr):
        self.psm = psm
        self.peer_mtu = peer_mtu
        self.peer_mps = peer_mps
        self.our_mtu = our_mtu
        self.our_mps = our_mps
        self.peer_bd_addr_type = bd_addr_type
        self.peer_bd_addr = bd_addr
        self.state = "connected"

    def disconnected(self, psm, bd_addr_type, bd_addr, reason):
        self.psm = None
        self.peer_bd_addr_type = None
        self.peer_bd_addr = None
        self.disconn_reason = reason
        self.state = "disconnected"

    def rx(self, data):
        self.data_rx.append(data)

    def tx(self, data):
        self.data_tx.append(data)

    def rx_data_get(self, timeout):
        if len(self.data_rx) != 0:
            return self.data_rx

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if len(self.data_rx) != 0:
                t.cancel()
                return self.data_rx

        return None

    def tx_data_get(self):
        return self.data_tx


class L2cap:
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
        for chan in self.channels:
            if chan.id == chan_id:
                return chan
        return None

    def clear_data(self):
        for chan in self.channels:
            chan.data_tx = []
            chan.data_rx = []

    def reconfigured(self, chan_id, peer_mtu, peer_mps, our_mtu, our_mps):
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

    def connected(self, chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                  bd_addr_type, bd_addr):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            chan = L2capChan(chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                             bd_addr_type, bd_addr)
            self.channels.append(chan)

        chan.connected(psm, peer_mtu, peer_mps, our_mtu, our_mps,
                       bd_addr_type, bd_addr)

    def disconnected(self, chan_id, psm, bd_addr_type, bd_addr, reason):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return
        # Remove channel from saved channels
        self.channels.remove(chan)

        chan.disconnected(psm, bd_addr_type, bd_addr, reason)

    def is_connected(self, chan_id):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            return False

        return chan.is_connected(10)

    def wait_for_disconnection(self, chan_id, timeout):
        if not self.is_connected(chan_id):
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if not self.is_connected(chan_id):
                t.cancel()
                return True

        return False

    def wait_for_connection(self, chan_id, timeout=5):
        if self.is_connected(chan_id):
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.is_connected(chan_id):
                t.cancel()
                return True

        return False

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
        data = []

        for chan in self.channels:
            data.append(chan.rx_data_get(timeout))

        return data

    def tx_data_get(self, chan_id):
        chan = self.chan_lookup_id(chan_id)
        if chan is None:
            logging.error("unknown channel")
            return None

        return chan.tx_data_get()

    def tx_data_get_all(self):
        data = []

        for chan in self.channels:
            data.append(chan.tx_data_get())

        return data


class SynchPoint:
    def __init__(self, test_case, wid, delay=None):
        self.test_case = test_case
        self.wid = wid
        self.delay = delay
        self.description = None

    def is_waiting(self):
        return self.description is not None

    def set_waiting(self, description):
        self.description = description

    def clear_waiting(self):
        self.description = None


class SynchElem:
    def __init__(self, sync_points):
        self.sync_points = sync_points

    def find_matching(self, test_case, wid):
        matching_items = [item for item in self.sync_points if
                          item.test_case == test_case and item.wid == wid]
        if matching_items:
            return matching_items[0]
        return None

    def is_ready(self):
        return all([item.is_waiting() for item in self.sync_points])

    def clear(self, clear_element):
        for clear_item in clear_element.sync_points:
            match = self.find_matching(clear_item.test_case,
                                       clear_item.wid)
            if match:
                match.clear_waiting()


class Synch:
    def __init__(self, sync_callbacks):
        self._synch_table = []
        self._pending_responses = []
        self._sync_callbacks = sync_callbacks

    def reinit(self, sync_callbacks):
        self._synch_table.clear()
        self._pending_responses.clear()
        self._sync_callbacks.clear()
        for cb in sync_callbacks:
            self._sync_callbacks.append(cb)

    def add_synch_element(self, elem):
        self._synch_table.append(SynchElem(elem))

    def perform_synch(self, wid, tc_name, description):
        found_element = None
        # Clean the remaining element descriptions with the same e_wid

        for i, elem in enumerate(self._synch_table):
            tc_item = elem.find_matching(tc_name, wid)
            if not tc_item:
                continue

            tc_item.set_waiting(description)
            if not elem.is_ready():
                # Wait for other wids
                return None

            found_element = i
            break

        synch_element = self._synch_table.pop(found_element)

        # Clean the remaining element descriptions with the same e_wid
        for element in self._synch_table:
            element.clear(synch_element)

        return synch_element.sync_points

    def is_required_synch(self, tc_name, wid):
        for elem in self._synch_table:
            if elem.find_matching(tc_name, wid):
                return True
        return False

    def prepare_pending_response(self, test_case_name, response, delay):
        self._pending_responses.append((test_case_name, response, delay))

    def set_pending_responses_if_any(self):
        for name, rsp, delay in self._pending_responses:
            for cb in self._sync_callbacks:
                if cb.get_current_test_case() == name:
                    cb.set_pending_response((name, rsp, delay))

        self._pending_responses = []

    def cancel_synch(self):
        self._synch_table = []
        self._pending_responses = []
        for cb in self._sync_callbacks:
            cb.clear_pending_responses()


class Gatt:
    def __init__(self):
        self.server_db = GattDB()
        self.last_unique_uuid = 0
        self.verify_values = []
        self.notification_events = []
        self.notification_ev_received = Event()
        self.signed_write_handle = 0

    def attr_value_set(self, handle, value):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr:
            attr.value = value
            return

        attr = GattCharacteristicDescriptor(handle, None, None, None, value)
        self.server_db.attr_add(handle, attr)

    def attr_value_get(self, handle):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr:
            return attr.value

        return None

    def attr_value_set_changed(self, handle):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr is None:
            logging.error("No attribute with %r handle", handle)
            return

        attr.has_changed_cnt += 1
        attr.has_changed.set()

    def attr_value_clr_changed(self, handle):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr is None:
            logging.error("No attribute with %r handle", handle)
            return

        attr.has_changed_cnt = 0
        attr.has_changed.clear()

    def attr_value_get_changed_cnt(self, handle):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr is None:
            logging.error("No attribute with %r handle", handle)
            return 0

        return attr.has_changed_cnt

    def wait_attr_value_changed(self, handle, timeout=None):
        attr = self.server_db.attr_lookup_handle(handle)
        if attr is None:
            attr = GattCharacteristicDescriptor(handle, None, None, None, None)
            self.server_db.attr_add(handle, attr)

        if attr.has_changed.wait(timeout=timeout):
            return attr.value

        logging.debug("timed out")
        return None

    def notification_ev_recv(self, addr_type, addr, notif_type, handle, data):
        self.notification_events.append((addr_type, addr, notif_type, handle, data))
        self.notification_ev_received.set()

    def wait_notification_ev(self, timeout=None):
        self.notification_ev_received.wait(timeout)
        self.notification_ev_received.clear()


def wait_for_event(timeout, test, args=None):
    if test(args):
        return True

    flag = Event()
    flag.set()

    t = Timer(timeout, timeout_cb, [flag])
    t.start()

    while flag.is_set():
        if test(args):
            t.cancel()
            return True

    return False


def is_procedure_done(list, cnt):
    if cnt is None:
        return False

    if cnt <= 0:
        return True

    return len(list) == cnt


class GattCl:
    def __init__(self):
        # if MTU exchanged tuple (addr, addr_type, status)
        self.mtu_exchanged = Property(None)
        self.verify_values = []
        self.prim_svcs_cnt = None
        self.prim_svcs = []
        self.incl_svcs_cnt = None
        self.incl_svcs = []
        self.chrcs_cnt = None
        self.chrcs = []
        self.dscs_cnt = None
        self.dscs = []
        self.notifications = []
        self.write_status = None

    def is_mtu_exchanged(self, args):
        return self.mtu_exchanged.data

    def wait_for_mtu_exchange(self, timeout=30):
        return wait_for_event(timeout, self.is_mtu_exchanged)

    def is_prim_disc_complete(self, args):
        return is_procedure_done(self.prim_svcs, self.prim_svcs_cnt)

    def wait_for_prim_svcs(self, timeout=30):
        return wait_for_event(timeout, self.is_prim_disc_complete)

    def is_incl_disc_complete(self, args):
        return is_procedure_done(self.incl_svcs, self.incl_svcs_cnt)

    def wait_for_incl_svcs(self, timeout=30):
        return wait_for_event(timeout, self.is_incl_disc_complete)

    def is_chrcs_disc_complete(self, args):
        return is_procedure_done(self.chrcs, self.chrcs_cnt)

    def wait_for_chrcs(self, timeout=30):
        return wait_for_event(timeout, self.is_chrcs_disc_complete)

    def is_dscs_disc_complete(self, args):
        return is_procedure_done(self.dscs, self.dscs_cnt)

    def wait_for_descs(self, timeout=30):
        return wait_for_event(timeout, self.is_dscs_disc_complete)

    def is_read_complete(self, args):
        return self.verify_values != []

    def wait_for_read(self, timeout=30):
        return wait_for_event(timeout, self.is_read_complete)

    def is_notification_rxed(self, expected_count):
        if expected_count > 0:
            return len(self.notifications) == expected_count
        return len(self.notifications) > 0

    def wait_for_notifications(self, timeout=30, expected_count=0):
        return wait_for_event(timeout,
                              self.is_notification_rxed, expected_count)

    def is_write_completed(self, args):
        return self.write_status is not None

    def wait_for_write_rsp(self, timeout=30):
        return wait_for_event(timeout, self.is_write_completed)


class Stack:
    def __init__(self):
        self.gap = None
        self.mesh = None
        self.l2cap = None
        self.synch = None
        self.gatt = None
        self.gatt_cl = None
        self.supported_svcs = 0

    def is_svc_supported(self, svc):
        # these are in little endian
        services = {
            "CORE":         0b0000001,
            "GAP":          0b0000010,
            "GATT":         0b0000100,
            "L2CAP":        0b0001000,
            "MESH":         0b0010000,
            "MESH_MMDL":    0b0100000,
            "GATT_CL":      0b1000000,
        }
        return self.supported_svcs & services[svc] > 0

    def gap_init(self, name=None, manufacturer_data=None, appearance=None,
                 svc_data=None, flags=None, svcs=None, uri=None):
        self.gap = Gap(name, manufacturer_data, appearance, svc_data, flags,
                       svcs, uri)

    def mesh_init(self, uuid, uuid_lt2=None):
        if self.mesh:
            return

        self.mesh = Mesh(uuid, uuid_lt2)

    def l2cap_init(self, psm, initial_mtu):
        self.l2cap = L2cap(psm, initial_mtu)

    def gatt_init(self):
        self.gatt = Gatt()
        self.gatt_cl = self.gatt

    def gatt_cl_init(self):
        self.gatt_cl = GattCl()

    def synch_init(self, sync_callbacks):
        if not self.synch:
            self.synch = Synch(sync_callbacks)
        else:
            self.synch.reinit(sync_callbacks)

    def cleanup(self):
        if self.gap:
            self.gap = Gap(self.gap.name, self.gap.manufacturer_data, None, None, None, None, None)

        if self.mesh:
            self.mesh = Mesh(self.mesh.get_dev_uuid(), self.mesh.get_dev_uuid_lt2())

        if self.gatt:
            self.gatt_init()

        if self.gatt_cl:
            self.gatt_cl_init()

        if self.synch:
            self.synch.cancel_synch()


def init_stack():
    global STACK

    STACK = Stack()


def cleanup_stack():
    global STACK

    STACK = None


def get_stack():
    return STACK
