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
from threading import Event


class GattAttribute:
    def __init__(self, handle, perm, uuid, att_rsp):
        self.handle = handle
        self.perm = perm
        self.uuid = uuid
        self.att_read_rsp = att_rsp


class GattService(GattAttribute):
    def __init__(self, handle, perm, uuid, att_rsp, end_handle=None):
        super().__init__(handle, perm, uuid, att_rsp)
        self.end_handle = end_handle


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


class Gatt:
    def __init__(self):
        self.server_db = GattDB()
        self.last_unique_uuid = 0
        self.verify_values = []
        self.notification_events = []
        self.notification_ev_received = Event()
        self.value_len = 0

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
