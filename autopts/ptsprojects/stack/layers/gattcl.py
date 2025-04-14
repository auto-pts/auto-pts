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
from autopts.ptsprojects.stack.common import wait_for_event
from autopts.ptsprojects.stack.layers import Property


def is_procedure_done(lst, cnt):
    if cnt is None:
        return False

    if cnt <= 0:
        return True

    return len(lst) == cnt


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
        self.event_to_await = None

    def set_event_to_await(self, event):
        self.event_to_await = event

    def wait_for_rsp_event(self, timeout=30):
        return wait_for_event(timeout, self.event_to_await)

    def is_mtu_exchanged(self, *args):
        return self.mtu_exchanged.data

    def wait_for_mtu_exchange(self, timeout=30):
        return wait_for_event(timeout, self.is_mtu_exchanged)

    def is_prim_disc_complete(self, *args):
        return is_procedure_done(self.prim_svcs, self.prim_svcs_cnt)

    def wait_for_prim_svcs(self, timeout=30):
        return wait_for_event(timeout, self.is_prim_disc_complete)

    def is_incl_disc_complete(self, *args):
        return is_procedure_done(self.incl_svcs, self.incl_svcs_cnt)

    def wait_for_incl_svcs(self, timeout=30):
        return wait_for_event(timeout, self.is_incl_disc_complete)

    def is_chrcs_disc_complete(self, *args):
        return is_procedure_done(self.chrcs, self.chrcs_cnt)

    def wait_for_chrcs(self, timeout=30):
        return wait_for_event(timeout, self.is_chrcs_disc_complete)

    def is_dscs_disc_complete(self, *args):
        return is_procedure_done(self.dscs, self.dscs_cnt)

    def wait_for_descs(self, timeout=30):
        return wait_for_event(timeout, self.is_dscs_disc_complete)

    def is_read_complete(self, *args):
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

    def is_write_completed(self, *args):
        return self.write_status is not None

    def wait_for_write_rsp(self, timeout=30):
        return wait_for_event(timeout, self.is_write_completed)

    def is_verified_val_rxed(self, expected_count):
        if expected_count > 0:
            return len(self.verify_values) == expected_count
        return len(self.verify_values) > 0

    def wait_for_verify_values(self, timeout=30, expected_count=0):
        return wait_for_event(timeout, self.is_verified_val_rxed, expected_count)
