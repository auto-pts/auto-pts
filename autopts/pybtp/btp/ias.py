#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup.
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

import logging

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs


def ias_ev_out_alert_action(ias, data, data_len):
    logging.debug("%s %r", ias_ev_out_alert_action.__name__, data)
    stack = get_stack()

    alert_lvl = int.from_bytes(data, "little")

    stack.ias.alert_lvl = alert_lvl

IAS_EV = {
    defs.BTP_IAS_EV_OUT_ALERT_ACTION: ias_ev_out_alert_action,
}
