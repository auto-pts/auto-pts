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

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import defs


@dataclass(frozen=True)
class HFP_HF_CALL:
    index: int
    direction: int
    state: int
    number: str
    type: int
    mpty: int


class HFP_HF_CONNECTION:
    def __init__(self, addr):
        self.addr = addr
        self.sco_connect = False
        self.calls = []
        self.signal = None
        self.roam = None
        self.last_battery = None
        self.battery = None
        self.operator = ""
        self.vgs = None
        self.vgm = None
        self.subscriber = []
        self.voice_recognition = None

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
            defs.BTP_HFP_HF_CALL_STATUS_INCOMING
            if direction is defs.BTP_HFP_HF_CALL_DIR_INCOMING
            else defs.BTP_HFP_HF_CALL_STATUS_DIALING
        )
        if not any(call.index == index for call in self.calls):
            call = HFP_HF_CALL(index=index, direction=direction, state=state, number=number,
                               type=0, mpty=0)
            self.calls.append(call)

    def remove_call(self, index):
        self.calls = [call for call in self.calls if call.index != index]

    def get_call(self, index):
        return next((call for call in self.calls if call.index == index), None)

    def update_call_state(self, index, state):
        for i, call in enumerate(self.calls):
            if call.index == index:
                self.calls[i] = HFP_HF_CALL(
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

    def set_signal(self, signal):
        self.signal = signal

    def get_signal(self):
        return self.signal

    def set_roam(self, roam):
        self.roam = roam

    def get_roam(self):
        return self.roam

    def set_battery(self, battery):
        self.last_battery = self.battery
        self.battery = battery

    def get_battery(self):
        return self.battery

    def get_last_battery(self):
        return self.last_battery

    def set_operator(self, operator):
        self.operator = operator

    def get_operator(self):
        return self.operator

    def set_vgs(self, vgs):
        self.vgs = vgs

    def get_vgs(self):
        return self.vgs

    def set_vgm(self, vgm):
        self.vgm = vgm

    def get_vgm(self):
        return self.vgm

    def get_subscriber(self):
        return self.subscriber

    def add_subscriber_number(self, number_info):
        """Add a single subscriber number to the list."""
        self.subscriber.append(number_info)

    def clear_subscriber(self):
        """Clear all subscriber numbers."""
        self.subscriber = []

    def has_subscriber_number(self, number_info):
        for subscriber in self.subscriber:
            if subscriber == number_info:
                return True
        return False

    def set_voice_recognition(self, activate):
        self.voice_recognition = activate

    def get_voice_recognition(self):
        return self.voice_recognition

    def is_voice_recognition_active(self):
        return self.voice_recognition


class HFP_HF:
    def __init__(self):
        self.connections = {}

        self.mmi_round = {}

    def add_connection(self, addr):
        self.connections[addr] = HFP_HF_CONNECTION(addr=addr)

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

    def get_signal(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_signal()

    def set_signal(self, addr, signal):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_signal(signal)

    def wait_for_signal(self, addr, expected_signal, timeout=10):
        wait_for_event(timeout, lambda: self.get_signal(addr) == expected_signal)
        return self.get_signal(addr) == expected_signal

    def get_roam(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_roam()

    def set_roam(self, addr, roam):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_roam(roam)

    def wait_for_roam(self, addr, expected_roam, timeout=10):
        wait_for_event(timeout, lambda: self.get_roam(addr) == expected_roam)
        return self.get_roam(addr) == expected_roam

    def get_battery(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_battery()

    def get_last_battery(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_last_battery()

    def set_battery(self, addr, battery):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_battery(battery)

    def wait_for_battery(self, addr, expected_battery, timeout=10):
        wait_for_event(timeout, lambda: self.get_battery(addr) == expected_battery)
        return self.get_battery(addr) == expected_battery

    def wait_for_battery_changed(self, addr, timeout=10):
        wait_for_event(timeout, lambda: self.get_battery(addr) != self.get_last_battery(addr))
        return self.get_battery(addr) != self.get_last_battery(addr)

    def wait_for_unexpected_battery(self, addr, unexpected_battery, timeout=10):
        wait_for_event(timeout, lambda: self.get_battery(addr) != unexpected_battery)
        return self.get_battery(addr) != unexpected_battery

    def get_operator(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_operator()

    def set_operator(self, addr, operator):
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.set_operator(operator)

    def wait_for_operator(self, addr, expected_operator, timeout=10):
        wait_for_event(timeout, lambda: self.get_operator(addr) == expected_operator)
        return self.get_operator(addr) == expected_operator

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

    def get_subscriber(self, addr):
        conn = self.get_connection(addr)
        if conn is None:
            return None
        return conn.get_subscriber()

    def add_subscriber_number(self, addr, number_info):
        """Add a single subscriber number to the connection."""
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.add_subscriber_number(number_info)

    def clear_subscriber(self, addr):
        """Clear all subscriber numbers for the connection."""
        conn = self.get_connection(addr)
        if conn is None:
            return
        conn.clear_subscriber()

    def has_subscriber_number(self, addr, number_info):
        """Check if a subscriber number exists in the connection."""
        conn = self.get_connection(addr)
        if conn is None:
            return False
        return conn.has_subscriber_number(number_info)

    def wait_for_subscriber_number(self, addr, expected_subscriber, timeout=10):
        """Wait for subscriber list to match expected value."""
        wait_for_event(timeout, lambda: self.has_subscriber_number(addr, expected_subscriber))
        return self.has_subscriber_number(addr, expected_subscriber)

    def wait_for_subscriber_count(self, addr, expected_count, timeout=10):
        """Wait for subscriber list to have expected number of entries."""
        wait_for_event(timeout, lambda: len(self.get_subscriber(addr) or []) == expected_count)
        return len(self.get_subscriber(addr) or []) == expected_count

    def set_voice_recognition(self, addr, activate):
        conn = self.get_connection(addr)
        if conn:
            conn.set_voice_recognition(activate)

    def get_voice_recognition(self, addr):
        conn = self.get_connection(addr)
        if conn:
            return conn.get_voice_recognition()
        return None

    def is_voice_recognition_active(self, addr):
        conn = self.get_connection(addr)
        if conn:
            return conn.is_voice_recognition_active()
        return False

    def wait_for_voice_recognition(self, addr, expected_activate=True, timeout=10):
        wait_for_event(timeout, lambda: self.is_voice_recognition_active(addr) == expected_activate)
        return self.is_voice_recognition_active(addr) == expected_activate
