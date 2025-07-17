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
from autopts.ptsprojects.stack.common import wait_event_with_condition
from autopts.pybtp import defs


class ASCS:
    def __init__(self):
        self.event_queues = {
            defs.BTP_ASCS_EV_OPERATION_COMPLETED: [],
            defs.BTP_ASCS_EV_CHARACTERISTIC_SUBSCRIBED: [],
            defs.BTP_ASCS_EV_ASE_STATE_CHANGED: [],
        }

    def event_received(self, event_type, event_data_tuple):
        self.event_queues[event_type].append(event_data_tuple)

    def wait_ascs_operation_complete_ev(self, addr_type, addr, ase_id, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ASCS_EV_OPERATION_COMPLETED],
            lambda _addr_type, _addr, _ase_id, *_: (addr_type, addr, ase_id) == (_addr_type, _addr, _ase_id),
            timeout, remove)

    def wait_ascs_characteristic_subscribed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ASCS_EV_CHARACTERISTIC_SUBSCRIBED],
            lambda _addr_type, _addr, *_: (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)

    def wait_ascs_ase_state_changed_ev(self, addr_type, addr, ase_id, state, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ASCS_EV_ASE_STATE_CHANGED],
            lambda _addr_type, _addr, _ase_id, _state, *_:
            (addr_type, addr, ase_id, state) == (_addr_type, _addr, _ase_id, _state),
            timeout, remove)
