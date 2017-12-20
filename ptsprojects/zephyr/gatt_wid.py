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
import btp
import re
from binascii import hexlify
from ptsprojects.stack import get_stack

log = logging.debug


def gatt_wid_hdl(wid, description):
    log("%s, %r, %r", gatt_wid_hdl.__name__, wid, description)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        log("wid nb: %d, not implemented!", wid)


# wid handlers section begin
def hdl_wid_1(desc):
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on()

    return 'Ok'


def hdl_wid_52(desc):
    # This pattern is matching IUT handle and characteristic value
    pattern = re.compile("(Handle|value)='([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_52.__name__)
        return 'No'

    params = dict(params)

    handle = int(params.get('Handle'), 16)
    value = int(params.get('value'), 16)

    (att_rsp, value_len, value_read) = btp.gatts_get_attr_val(handle)
    value_read = int(hexlify(value_read), 16)

    if value_read != value:
        return 'No'
    return 'Yes'
