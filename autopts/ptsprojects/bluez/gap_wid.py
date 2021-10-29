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
import time

from autopts.pybtp import btp
from autopts.pybtp.types import Prop, AdType
from autopts.ptsprojects.stack import get_stack
from autopts.wid.gap import gap_wid_hdl as gen_wid_hdl

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


def hdl_wid_47(desc):
    stack = get_stack()

    btp.gap_set_nonconn()

    # Name cannot be used for AD Data in BlueZ because BlueZ alwasy use Name
    # for SD Data. So, override the AD data here.
    stack.gap.ad = {AdType.manufacturer_data: 'FFFFABCD'}

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_77(desc):
    time.sleep(2)
    btp.gap_disconn()
    return True


def hdl_wid_78(desc):
    btp.gap_conn()
    btp.gap_wait_for_connection()
    return True


def hdl_wid_79(desc):
    return hdl_wid_80(desc)


def hdl_wid_80(desc):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()

    # Name cannot be used for AD Data in BlueZ because BlueZ alwasy use Name
    # for SD Data. So, override the AD data here.
    stack.gap.ad = {}
    stack.gap.ad[AdType.manufacturer_data] = 'FFFFABCD'

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_108(desc):
    btp.gap_wait_for_connection()
    btp.gap_pair()
    return True


def hdl_wid_112(desc):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gattc_disc_all_chrc(bd_addr_type, bd_addr, 0x0001, 0xffff)
    attrs = btp.gattc_disc_all_chrc_rsp()

    for attr in attrs:
        if attr.prop & Prop.read:
            btp.gattc_read(bd_addr_type, bd_addr, attr.value_handle)
            btp.gattc_read_rsp()
            return True

    return False


def hdl_wid_1002(desc):
    stack = get_stack()
    passkey = stack.gap.passkey.data
    stack.gap.passkey.data = None
    return passkey
