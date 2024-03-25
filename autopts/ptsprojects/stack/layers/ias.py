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


class IAS:
    ALERT_LEVEL_NONE = 0
    ALERT_LEVEL_MILD = 1
    ALERT_LEVEL_HIGH = 2

    def __init__(self):
        self.alert_lvl = None

    def is_mild_alert_set(self, *args):
        return self.alert_lvl == self.ALERT_LEVEL_MILD

    def is_high_alert_set(self, *args):
        return self.alert_lvl == self.ALERT_LEVEL_HIGH

    def is_alert_stopped(self, *args):
        return self.alert_lvl == self.ALERT_LEVEL_NONE

    def wait_for_mild_alert(self, timeout=30):
        return wait_for_event(timeout, self.is_mild_alert_set)

    def wait_for_high_alert(self, timeout=30):
        return wait_for_event(timeout, self.is_high_alert_set)

    def wait_for_stop_alert(self, timeout=30):
        return wait_for_event(timeout, self.is_alert_stopped)
