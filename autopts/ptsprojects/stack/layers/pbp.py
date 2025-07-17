#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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


class PBP:
    def __init__(self):
        self.program_info = None
        self.broadcast_name = None
        self.event_queues = {
            defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND: [],
        }

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)

    def wait_public_broadcast_event_found_ev(self, addr_type, addr, broadcast_name, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND],
            lambda ev: (addr_type, addr, broadcast_name) == (ev['addr_type'], ev['addr'], ev['broadcast_name']),
            timeout, remove)

    def set_program_info(self, program_info):
        if not isinstance(program_info, str):
            raise TypeError('Tried to set improper program info')
        if len(program_info) == 0:
            raise ValueError('Tried to set empty program info')
        self.program_info = program_info

    def set_broadcast_name(self, broadcast_name):
        if not isinstance(broadcast_name, str):
            raise TypeError('Tried to set improper broadcast name')
        if len(broadcast_name) < 4 or len(broadcast_name) > 32:
            raise ValueError(f'Tried to set broadcast name with invalid length: \'{broadcast_name}\' ({len(broadcast_name)})')
        self.broadcast_name = broadcast_name
