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
            defs.BTP_ASCS_EV_CIS_CONNECTED: [],
            defs.BTP_ASCS_EV_CIS_DISCONNECTED: [],
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

    def wait_ascs_cis_connected_ev(self, addr_type, addr, ase_id, cis_id, timeout=10, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_ASCS_EV_CIS_CONNECTED],
            lambda _addr_type, _addr, _ase_id, _cis_id, *_: (addr_type, addr, ase_id, cis_id)
            == (_addr_type, _addr, _ase_id, _cis_id),
            timeout,
            remove,
        )

    def wait_ascs_cis_disconnected_ev(
        self, addr_type, addr, ase_id, cis_id, reason=None, timeout=10, remove=True
    ):
        def _matches(ev_addr_type, ev_addr, ev_ase_id, ev_cis_id, ev_reason, *_):
            return (
                ev_addr_type == addr_type
                and ev_addr == addr
                and ev_ase_id == ase_id
                and ev_cis_id == cis_id
                and (reason is None or ev_reason == reason)
            )

        return wait_event_with_condition(
            self.event_queues[defs.BTP_ASCS_EV_CIS_DISCONNECTED],
            _matches,
            timeout,
            remove,
        )
