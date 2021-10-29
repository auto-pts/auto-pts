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
from autopts.pybtp.types import UUID
from autopts.wid.gatt import gatt_wid_hdl as gen_wid_hdl, gatt_server_fetch_db

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", gatt_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


def hdl_wid_10(dec):
    # Send Discover All Primary Services Request
    btp.gattc_disc_all_prim(btp.pts_addr_type_get(), btp.pts_addr_get())

    # Read Discover All Primary Services Response and store it for later use.
    btp.gattc_disc_all_prim_rsp(True)
    return True


def hdl_wid_151(desc):
    # Return handle of characteristic that has fixed, known size, and does not require security.
    # In Zephyr there are two options: CCC and CSF.
    db = gatt_server_fetch_db().db
    for i in range(1, len(db) + 1):

        if db[i].uuid == UUID.CSF:
            return '{0:04x}'.format(db[i].value_handle)
        if db[i].uuid == UUID.CCC:
            return '{0:04x}'.format(db[i].handle)
    # if nothing found, return correctly formatted response that will cause other response than expected and FAIL,
    # but will prevent infinite loop of asking wid 151
    return '{0:04x}'.format(1)


def hdl_wid_152(desc):
    # Return handle of characteristic that has fixed, known size larger than MTU-3, and does not require security.
    # In Zephyr this can be only device name.
    db = gatt_server_fetch_db().db
    for i in range(1, len(db) + 1):
        if db[i].uuid == UUID.device_name:
            return '{0:04x}'.format(db[i].value_handle)
    # if nothing found, return correctly formatted response that will cause other response than expected and FAIL,
    # but will prevent infinite loop of asking wid 152
    return '{0:04x}'.format(1)
