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
        self.blob_lost_target = False

        # network data
        self.lt1_addr = 0x0001

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
        # model_recv_ev_store - store data for further verification
        self.model_recv_ev_store = Property(False)
        # model_recv_ev_data (src, dst, payload)
        self.model_recv_ev_data = Property(None)
        self.incomp_timer_exp = Property(False)
        self.friendship = Property(False)
        self.lpn = Property(False)

        # Lower tester composition data
        self.tester_comp_data = Property({})

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

        # SAR
        self.sar_transmitter_state = Property((0x01, 0x07, 0x01, 0x07, 0x01, 0x02, 0x03))
        self.sar_receiver_state = Property((0x04, 0x02, 0x01, 0x01, 0x01))

        # Large Composition Data models
        self.large_comp_data = Property(None)
        self.models_metadata = Property(None)

        # MMDL Blob transfer timeout
        self.timeout = 0

        # MMDL Blob transfer TTL
        self.transfer_ttl = 2

        # MMDL Blob transfer server rxed data size
        self.blob_rxed_bytes = 0

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

    def reset_state(self):
        '''Used to set MESH status to uninitialised. It's used after
        IUT restart when mesh was set to initialised before it'''
        self.is_initialized = False

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

        return wait_for_event(timeout, lambda: uuid in self.nodes_added.data)

    def wait_for_model_added_op(self, timeout, op):
        if self.model_recv_ev_data.data is not None and \
               self.model_recv_ev_data.data[2][0:4] == op:
            self.model_recv_ev_data.data = (0, 0, b'')
            return True

        if wait_for_event(timeout,
                          lambda: self.model_recv_ev_data.data is not None and
                          self.model_recv_ev_data.data[2][0:4] == op):
            self.model_recv_ev_data.data = (0, 0, b'')
            return True

        return False

    def set_iut_provisioner(self, _is_prov):
        self.iut_is_provisioner = _is_prov

    def set_iut_addr(self, _addr):
        self.address_iut = _addr

    def timeout_base_set(self, timeout):
        self.timeout_base = timeout

    def timeout_base_get(self):
        return self.timeout_base

    def transfer_ttl_set(self, ttl):
        self.transfer_ttl = ttl

    def transfer_ttl_get(self):
        return self.transfer_ttl

    def set_tester_comp_data(self, page, comp):
        self.tester_comp_data.data[page] = comp

    def get_tester_comp_data(self, page):
        if page in self.tester_comp_data.data:
            return self.tester_comp_data.data[page]

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

        if wait_for_event(timeout, lambda: self.incomp_timer_exp.data):
            return True

        return False

    def wait_for_prov_link_close(self, timeout):
        if not self.last_seen_prov_link_state.data:
            self.last_seen_prov_link_state.data = ('uninitialized', None)

        state, _ = self.last_seen_prov_link_state.data
        if state == 'closed':
            return True

        if wait_for_event(timeout, lambda: 'closed' == self.last_seen_prov_link_state.data[0]):
            return True

        return False

    def wait_for_lpn_established(self, timeout):
        if self.lpn.data:
            return True

        if wait_for_event(timeout, lambda: self.lpn.data):
            return True

        return False

    def wait_for_lpn_terminated(self, timeout):
        if not self.lpn.data:
            return True

        if wait_for_event(timeout, lambda: not self.lpn.data):
            return True

        return False

    def wait_for_blob_target_lost(self, timeout):
        if self.blob_lost_target:
            return True

        if wait_for_event(timeout, lambda: self.blob_lost_target):
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
