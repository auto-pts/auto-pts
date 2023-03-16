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
import socket
import sys

from autopts.pybtp import btp
from autopts.pybtp.types import UUID, AdType, UriScheme
from autopts.wid.gap import gap_wid_hdl as gen_wid_hdl, hdl_wid_139_mode1_lvl2, hdl_wid_139_mode1_lvl4
from autopts.ptsprojects.stack import get_stack

log = logging.debug


def gap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", gap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


# For tests in SC only, mode 1 level 3
def gap_wid_hdl_mode1_lvl2(wid, description, test_case_name):
    if wid == 139:
        log("%s, %r, %r, %s", gap_wid_hdl_mode1_lvl2.__name__, wid, description,
            test_case_name)
        return hdl_wid_139_mode1_lvl2(description)
    return gap_wid_hdl(wid, description, test_case_name)


def gap_wid_hdl_mode1_lvl4(wid, description, test_case_name):
    if wid == 139:
        log("%s, %r, %r, %s", gap_wid_hdl.__name__, wid, description,
            test_case_name)
        return hdl_wid_139_mode1_lvl4(description)
    return gap_wid_hdl(wid, description, test_case_name)


def hdl_wid_104(desc):
    return True


def hdl_wid_114(desc):
    return True


def hdl_wid_127(desc):
    btp.gap_conn_param_update(btp.pts_addr_get(), btp.pts_addr_type_get(),
                              720, 864, 0, 400)
    return True


def hdl_wid_162(desc):
    return True


def hdl_wid_173(desc):
    stack = get_stack()

    # Prepare space for URI
    stack.gap.sd.clear()
    stack.gap.sd[AdType.uri] = UriScheme.https + \
        'github.com/intel/auto-pts'.encode()

    btp.gap_adv_ind_on(sd=stack.gap.sd)

    return True


def hdl_wid_224(desc):
    return True
