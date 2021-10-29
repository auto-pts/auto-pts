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
from autopts.wid.sm import sm_wid_hdl as gen_wid_hdl
from autopts.ptsprojects.zephyr.iutctl import get_iut

log = logging.debug


def sm_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", sm_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


# wid handlers section begin
def hdl_wid_143(desc):
    zephyrctl = get_iut()

    zephyrctl.wait_iut_ready_event()
    btp.core_reg_svc_gap()
    btp.gap_read_ctrl_info()

    return True
