#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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

from dataclasses import dataclass
from threading import Timer

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import defs


@dataclass(frozen=True)
class HFP_AG_CALL:
    index: int
    direction: int
    state: int
    number: str
    type: int
    mpty: int


class HFP_AG_CONNECTION:
    def __init__(self, addr):
        self.addr = addr
        self.sco_connect = False
        self.calls = []
        self.ecnr = True
        self.vgs = None
        self.vgm = None
        self.ready_accept_audio = False
        self.ready_accept_audio_callback = None

    def sco_is_connected(self):
        return self.sco_connect

    def wait_for_sco_connection(self, timeout=10):
        if self.sco_connect:
            return True

        wait_for_event(timeout, lambda: self.sco_connect)
        return self.sco_connect

    def sco_connected(self):
        self.sco_connect = True

    def sco_disconnected(self):
        self.sco_connect = False

    def add_call(self, index, direction, number: str = ""):
        state = (
            defs.BTP_HFP_AG_CALL_STATUS_INCOMING
            if direction is defs.BTP_HFP_AG_CALL_DIR_INCOMING
            else defs.BTP_HFP_AG_CALL_STATUS_DIALING
        )
        if not any(call.index == index for call in self.calls):
            call = HFP_AG_CALL(index=index, direction=direction, state=state, number=number,
                               type=0, mpty=0)
            self.calls.append(call)

    def remove_call(self, index):
        self.calls = [call for call in self.calls if call.index != index]

    def get_calls_index(self):
        return [call.index for call in self.calls]

    def get_call(self, index):
        return next((call for call in self.calls if call.index == index), None)

    def update_call_state(self, index, state):
        for i, call in enumerate(self.calls):
            if call.index == index:
                self.calls[i] = HFP_AG_CALL(
                    index=call.index, direction=call.direction, state=state, number=call.number,
                    type=call.type, mpty=call.mpty
                )
                break

    def get_call_dir(self, index):
        """Get the current state of a specific call by index."""
        return next((call.direction for call in self.calls if call.index == index), None)

    def get_call_state(self, index):
        """Get the current state of a specific call by index."""
        return next((call.state for call in self.calls if call.index == index), None)

    def get_call_count(self):
        """Get the total number of calls."""
        return len(self.calls)

    def get_calls(self):
        """Get all calls."""
        return self.calls

    def wait_for_call_state(self, index, expected_state, timeout=10):
        """Wait for a call to reach a specific state."""
        wait_for_event(timeout, lambda: self.get_call_state(index) == expected_state)
        return self.get_call_state(index) == expected_state

    def get_ecnr(self):
        """Check if ECNR is enabled."""
        return self.ecnr

    def set_ecnr(self, enable):
        """Set ECNR enabled/disabled."""
        self.ecnr = enable

    def set_vgs(self, vgs):
        self.vgs = vgs

    def get_vgs(self):
        return self.vgs

    def set_vgm(self, vgm):
        self.vgm = vgm

    def get_vgm(self):
        return self.vgm

    def set_ready_accept_audio(self, ready):
        self.ready_accept_audio = ready

        def call_ready_accept_audio_callback():
            if self.ready_accept_audio_callback:
                self.ready_accept_audio_callback(self.addr)
                self.ready_accept_audio_callback = None

        if ready:
            timer = Timer(0.5, call_ready_accept_audio_callback)
            timer.daemon = True
            timer.start()

    def get_ready_accept_audio(self):
        return self.ready_accept_audio

    def register_ready_accept_audio_callback(self, callback):
        self.ready_accept_audio_callback = callback


class HFP_AG:
    def __init__(self):
        self.connections = {}

        self.mmi_round = {}

    def add_connection(self, addr):
        self.connections[addr] = HFP_AG_CONNECTION(addr=addr)

    def remove_connection(self, addr):
        self.connections.pop(addr, None)

    def get_connection(self, addr):
        return self.connections.get(addr)

    def is_connected(self, addr):
        return self.get_connection(addr) is not None

    def wait_for_connection(self, addr, timeout=10):
        conn = self.get_connection(addr)
        if conn:
            return True

        wait_for_event(timeout, lambda: self.get_connection(addr))
        return self.get_connection(addr) is not None

    def wait_for_disconnection(self, addr, timeout=10):
        conn = self.get_connection(addr)
        if not conn:
            return True

        wait_for_event(timeout, lambda: not self.get_connection(addr))
        return self.get_connection(addr) is None

    def sco_connected(self, addr):
        conn = self.get_connection(addr)
        if conn:
            conn.sco_connected()

    def sco_disconnected(self, addr):
        conn = self.get_connection(addr)
        if conn:
            conn.sco_disconnected()

    def sco_is_connected(self, addr):
        conn = self.get_connection(addr)
        if conn and conn.sco_is_connected():
            return True
        return False

    def sco_is_disconnected(self, addr):
        return not self.sco_is_connected(addr)

    def wait_for_sco_connection(self, addr, timeout=10):
        conn = self.get_connection(addr)
        if conn and conn.wait_for_sco_connection(timeout=timeout):
            return True
        return False

    def get_mmi_round(self, mmi):
        if mmi in self.mmi_round.keys():
            return self.mmi_round[mmi]
        return 0

    def increase_mmi_round(self, mmi):
        if mmi in self.mmi_round.keys():
            self.mmi_round[mmi] += 1
        else:
            self.mmi_round[mmi] = 1

    def add_call(self, addr, index, direction, number: str = ""):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.add_call(index, direction, number)

    def remove_call(self, addr, index):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.remove_call(index)

    def get_call(self, addr, index):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_call(index)

    def get_calls_index(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return []
        return conn.get_calls_index()

    def update_call_state(self, addr, index, state):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.update_call_state(index, state)

    def get_call_state(self, addr, index):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_call_state(index)

    def get_call_dir(self, addr, index):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_call_dir(index)

    def get_call_count(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return 0
        return conn.get_call_count()

    def get_calls(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_calls()

    def wait_for_call_state(self, addr, index, expected_state, timeout=10):
        wait_for_event(timeout, lambda: self.get_call_state(addr, index) == expected_state)
        return self.get_call_state(addr, index) == expected_state

    def wait_for_call_count(self, addr, expected_count, timeout=10):
        wait_for_event(timeout, lambda: self.get_call_count(addr) == expected_count)
        return self.get_call_count(addr) == expected_count

    def get_ecnr(self, addr):
        conn = self.get_connection(addr)
        if conn:
            return conn.get_ecnr()
        return None

    def set_ecnr(self, addr, enable):
        conn = self.get_connection(addr)
        if conn:
            conn.set_ecnr(enable)

    def wait_for_ecnr_off(self, addr, timeout=10):
        wait_for_event(timeout, lambda: not self.get_ecnr(addr))
        return not self.get_ecnr(addr)

    def get_vgs(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_vgs()

    def set_vgs(self, addr, vgs):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_vgs(vgs)

    def wait_for_vgs(self, addr, expected_vgs, timeout=10):
        wait_for_event(timeout, lambda: self.get_vgs(addr) == expected_vgs)
        return self.get_vgs(addr) == expected_vgs

    def get_vgm(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_vgm()

    def set_vgm(self, addr, vgm):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_vgm(vgm)

    def wait_for_vgm(self, addr, expected_vgm, timeout=10):
        wait_for_event(timeout, lambda: self.get_vgm(addr) == expected_vgm)
        return self.get_vgm(addr) == expected_vgm

    def register_ready_accept_audio_callback(self, addr, callback):
        conn = self.get_connection(addr)
        if conn:
            conn.register_ready_accept_audio_callback(callback)

    def set_ready_accept_audio(self, addr, ready):
        conn = self.get_connection(addr)
        if conn:
            conn.set_ready_accept_audio(ready)

    def get_ready_accept_audio(self, addr):
        conn = self.get_connection(addr)
        if conn:
            return conn.get_ready_accept_audio()
        return None

    def is_ready_accept_audio(self, addr):
        conn = self.get_connection(addr)
        if conn:
            return conn.get_ready_accept_audio()
        return False

    def wait_for_ready_accept_audio(self, addr, expected_ready=True, timeout=10):
        wait_for_event(timeout, lambda: self.is_ready_accept_audio(addr) == expected_ready)
        return self.is_ready_accept_audio(addr) == expected_ready
