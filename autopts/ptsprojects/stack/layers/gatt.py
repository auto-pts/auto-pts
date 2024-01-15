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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btpdefs.gatt import GattCharacteristicDescriptor


def clear_verify_values():
    stack = get_stack()
    stack.gatt_cl.verify_values = []


def add_to_verify_values(item):
    stack = get_stack()
    stack.gatt_cl.verify_values.append(item)


def get_verify_values():
    stack = get_stack()
    return stack.gatt_cl.verify_values


def extend_verify_values(item):
    stack = get_stack()
    stack.gatt_cl.verify_values.extend(item)


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
        self.signed_write_handle = 0

    def clear_verify_values(self):
        self.verify_values = []

    def add_to_verify_values(self, item):
        self.verify_values.append(item)

    def get_verify_values(self):
        return self.verify_values

    def extend_verify_values(self, item):
        self.verify_values.extend(item)

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
