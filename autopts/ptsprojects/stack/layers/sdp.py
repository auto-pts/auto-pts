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

from autopts.ptsprojects.stack.common import wait_for_event


class SDP:
    def __init__(self):
        self.service_record_handles = {}

    def add_service_record_handles(self, addr, handle):
        handles = []
        if addr in self.service_record_handles.keys():
            handles.append(self.service_record_handles[addr])
        handles.append(handle)
        self.service_record_handles[addr] = handles

    def has_service_record_handle(self, addr=None):
        if addr and addr in self.service_record_handles.keys():
            if len(self.service_record_handles[addr]) > 0:
                handle = self.service_record_handles[addr][0]
                return handle
        else:
            if len(self.service_record_handles) > 0:
                addr = list(self.service_record_handles.keys())[0]
                if len(self.service_record_handles[addr]) > 0:
                    handle = self.service_record_handles[addr][0]
                    return handle
        return 0

    def get_service_record_handle(self, addr=None):
        if addr and addr in self.service_record_handles.keys():
            if len(self.service_record_handles[addr]) > 0:
                handle = self.service_record_handles[addr][0]
                del self.service_record_handles[addr][0]
                return handle
        else:
            if len(self.service_record_handles) > 0:
                addr = list(self.service_record_handles.keys())[0]
                if len(self.service_record_handles[addr]) > 0:
                    handle = self.service_record_handles[addr][0]
                    del self.service_record_handles[addr][0]
                    return handle
        return 0

    def sdp_wait_for_service_record_handle(self, timeout=5, addr=None):
        handle = self.get_service_record_handle(addr)
        if handle != 0:
            return handle

        wait_for_event(timeout, lambda: self.has_service_record_handle(addr) > 0)

        return self.get_service_record_handle(addr)
