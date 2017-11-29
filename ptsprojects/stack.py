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

from threading import Lock

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


class Gap():
    def __init__(self):
        # If disconnected - None
        # If connected - remote address tuple (addr, addr_type)
        self.connected = Property(None)


class Mesh():
    def __init__(self, dev_uuid):
        self.dev_uuid = dev_uuid

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
        self.health_test_id = '00'
        self.health_fault_array = 24 * 'FF'

        # vendor model data
        self.vendor_model_id = '0002'

        # IV update
        self.iv_update_timeout = Property(120)
        self.is_iv_test_mode_enabled = Property(False)


class Stack():
    def __init__(self):
        self.gap = None
        self.mesh = None

    def gap_init(self):
        self.gap = Gap()

    def mesh_init(self, dev_uuid):
        self.mesh = Mesh(dev_uuid)

    def cleanup(self):
        if self.gap:
            self.gap_init()

        if self.mesh:
            self.mesh_init(self.mesh.dev_uuid)

def init_stack():
    global STACK

    STACK = Stack()

def cleanup_stack():
    global STACK

    STACK = None

def get_stack():
    return STACK
