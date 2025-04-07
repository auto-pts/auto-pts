#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

"""Wrapper around btp messages. The functions are added as needed."""
import logging

from autopts.pybtp import defs


def core_iut_ready_ev(core, data, data_len):
    logging.debug("%s", core_iut_ready_ev.__name__)

    core.event_received(defs.BTP_CORE_EV_IUT_READY, True)


CORE_EV = {
    defs.BTP_CORE_EV_IUT_READY: core_iut_ready_ev,
}
