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

def vcs_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", vcs_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)

# wid handlers section begin
def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True

def hdl_wid_1(_: WIDParams):
    btp.vcs_set_vol(2)
    return True

def hdl_wid_2(_: WIDParams):
    btp.vcs_set_vol(2)
    btp.vcs_mute()
    return True

def hdl_wid_3(_: WIDParams):
    btp.vcs_set_vol(255)
    return True

def hdl_wid_4(_: WIDParams):
    btp.vcs_set_vol(255)
    btp.vcs_mute()
    return True
