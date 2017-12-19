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

from threading import Lock, Timer, Event

STACK = None


class Property(object):
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


class Gap():
    def __init__(self):
        # If disconnected - None
        # If connected - remote address tuple (addr, addr_type)
        self.connected = Property(None)
        self.current_settings = None
        # IUT address tuple (addr, addr_type)
        self.iut_bd_addr = Property(None)

    def wait_for_connection(self, timeout):
        if self.is_connected():
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if self.is_connected():
                t.cancel()
                return True

        return False

    def wait_for_disconnection(self, timeout):
        if not self.is_connected():
            return True

        flag = Event()
        flag.set()

        t = Timer(timeout, timeout_cb, [flag])
        t.start()

        while flag.is_set():
            if not self.is_connected():
                t.cancel()
                return True

        return False

    def is_connected(self):
        return False if (self.connected.data is None) else True


class Mesh():
    def __init__(self, uuid, oob, output_size, output_actions, input_size, input_actions):

        # init data
        self.dev_uuid = uuid
        self.static_auth = oob
        self.output_size = output_size
        self.output_actions = output_actions
        self.input_size = input_size
        self.input_actions = input_actions

        self.oob_action = Property(None)
        self.oob_data = Property(None)
        self.is_provisioned = Property(False)
        self.last_seen_prov_link_state = Property(None)

        # provision node data
        self.net_key = '0123456789abcdef0123456789abcdef'
        self.net_key_idx = 0x0000
        self.flags = 0x00
        self.iv_idx = 0x00000000
        self.seq_num = 0x00000000
        self.addr = 0x0b0c
        self.dev_key = '0123456789abcdef0123456789abcdef'

        # health model data
        self.health_test_id = Property(0x00)
        self.health_current_faults = Property(None)
        self.health_registered_faults = Property(None)

        # vendor model data
        self.vendor_model_id = '0002'

        # IV update
        self.iv_update_timeout = Property(120)
        self.is_iv_test_mode_enabled = Property(False)

        # Network
        self.net_recv_ev_store = Property(False)  # store data for further verification
        self.net_recv_ev_data = Property(None)  # event data tuple (ttl, ctl, src, dst, payload)


class Stack():
    def __init__(self):
        self.gap = None
        self.mesh = None

    def gap_init(self):
        self.gap = Gap()

    def mesh_init(self, uuid, oob, output_size, output_actions, input_size, input_actions):
        self.mesh = Mesh(uuid, oob, output_size, output_actions, input_size, input_actions)

    def cleanup(self):
        if self.gap:
            self.gap_init()

        if self.mesh:
            self.mesh_init(self.mesh.dev_uuid, self.mesh.static_auth,
                           self.mesh.output_size, self.mesh.output_actions,
                           self.mesh.input_size, self.mesh.input_actions)

def init_stack():
    global STACK

    STACK = Stack()

def cleanup_stack():
    global STACK

    STACK = None

def get_stack():
    return STACK
