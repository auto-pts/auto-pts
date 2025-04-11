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
import copy

from autopts.ptsprojects.stack.common import wait_for_queue_event
from autopts.pybtp import defs


class CCP:
    def __init__(self):
        self.events = {
            defs.BTP_CCP_EV_DISCOVERED:  {'count': 0, 'status': 0, 'tbs_count': 0, 'gtbs': False},
            defs.BTP_CCP_EV_CALL_STATES: {'count': 0, 'status': 0, 'index': 0, 'call_count': 0, 'states': []},
            defs.BTP_CCP_EV_CHRC_HANDLES: [],
            defs.BTP_CCP_EV_CHRC_VAL: [],
            defs.BTP_CCP_EV_CHRC_STR: [],
            defs.BTP_CCP_EV_CP: [],
            defs.BTP_CCP_EV_CURRENT_CALLS: [],
        }

    def event_received(self, event_type, event_dict):
        count = self.events[event_type]['count']
        self.events[event_type] = copy.deepcopy(event_dict)
        self.events[event_type]['count'] = count + 1

    def event_received_2(self, event_type, event_data_tuple):
        self.events[event_type].append(event_data_tuple)

    def wait_characteristic_value_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.events[defs.BTP_CCP_EV_CHRC_VAL],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_characteristic_str_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.events[defs.BTP_CCP_EV_CHRC_STR],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_chrc_handles_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.events[defs.BTP_CCP_EV_CHRC_HANDLES],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_cp_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.events[defs.BTP_CCP_EV_CP],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_current_ev(self, addr_type, addr, timeout, remove=True):
        return wait_for_queue_event(
            self.events[defs.BTP_CCP_EV_CURRENT_CALLS],
            lambda _addr_type, _addr, *_:
            (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
