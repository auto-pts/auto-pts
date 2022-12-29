#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
import sys

from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams
from autopts.ptsprojects.stack import get_stack

log = logging.debug

def ias_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", ias_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)

def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True

def hdl_wid_1(params: WIDParams):
    stack = get_stack()

    stack.ias.wait_for_high_alert()

    return stack.ias.alert_lvl == 2

def hdl_wid_2(params: WIDParams):
    stack = get_stack()

    stack.ias.wait_for_stop_alert()

    return stack.ias.alert_lvl == 0

def hdl_wid_0(params: WIDParams):
    stack = get_stack()

    stack.ias.wait_for_mild_alert()

    return stack.ias.alert_lvl == 1

def hdl_wid_20207(params: WIDParams):
    stack = get_stack()

    stack.ias.wait_for_mild_alert()

    return stack.ias.alert_lvl == 1
