#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, nxp.
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
from autopts.pybtp import defs


class A2DP:

    def __init__(self):
        self.event_queues = {
        }

        self.STATUS = {
            defs.BTP_A2DP_EV_CONNECTED: 'CONNECTED',
            defs.BTP_A2DP_EV_DISCOVER_RSP: 'DISCOVERED',
            defs.BTP_A2DP_EV_GET_CAPABILITIES_RSP: 'GET_CONFIG_CAPABILITIES',
            defs.BTP_A2DP_EV_SET_CONFIGURATION_RSP: 'SET_CONFIG_COMPLETED',
            defs.BTP_A2DP_EV_ESTABLISH_RSP: 'ESTABLISHED',
            defs.BTP_A2DP_EV_RELEASE_RSP: 'RELEASED',
            defs.BTP_A2DP_EV_START_RSP: 'STARTED',
            defs.BTP_A2DP_EV_SUSPEND_RSP: 'SUSPENDED',
            defs.BTP_A2DP_EV_DISCONNECTED: 'DISCONNECTED',
            defs.BTP_A2DP_EV_ABORT_RSP: 'ABORTED',
            defs.BTP_A2DP_EV_SEND_DELAY_REPORT_RSP: 'SEND_DELAY_REPORT_RSP',
            defs.BTP_A2DP_EV_GET_CONFIG_RSP: 'GET_CONFIGURATION',
        }
        self.status = self.STATUS[defs.BTP_A2DP_EV_DISCONNECTED]
        self.media = []
        self.mmi_round = {}

    class recv_media:
        def __init__(self, frame_num, length, data):
            self.frame_num = frame_num
            self.length = length
            self.data = data

    def is_correct_status(self, cmd):
        if cmd in self.STATUS:
            if self.status == self.STATUS[cmd]:
                return True
            else:
                return False
        else:
            return False

    def wait_for_command_rsp(self, cmd, timeout=5):
        if self.is_correct_status(cmd):
            return True
        return wait_for_event(timeout, self.is_correct_status, cmd=cmd)

    def is_recv_media(self, timeout=5):
        if self.media != []:
            return True
        return wait_for_event(timeout, lambda: self.media != [])

    def increase_mmi_round(self, key):
        if key not in self.mmi_round:
            self.mmi_round[key] = 1
        else:
            self.mmi_round[key] += 1

    def get_mmi_round(self, key):
        if key in self.mmi_round:
            return self.mmi_round[key]
        return 0

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)
