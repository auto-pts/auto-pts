#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
from autopts.ptsprojects.testcase import MMI
from autopts.ptsprojects.mynewt.gatt_wid import gatt_wid_hdl

log = logging.debug


def gattc_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", gattc_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gatt_wid_hdl(wid, description, test_case_name)


def gattc_wid_hdl_no_read_long(wid, description, test_case_name):
    if wid == 48:
        log("%s, %r, %r, %s", gattc_wid_hdl_no_read_long.__name__, wid, description,
            test_case_name)
        return hdl_wid_48_no_long_read(description)
    return gattc_wid_hdl(wid, description, test_case_name)


def hdl_wid_10(desc):
    btp.gattc_disc_all_prim(btp.pts_addr_type_get(None),
                            btp.pts_addr_get(None))
    btp.gattc_disc_all_prim_rsp()
    return True


def hdl_wid_17(desc):
    return btp.verify_description(desc)


def hdl_wid_24(desc):
    return btp.verify_description(desc)


def hdl_wid_48_no_long_read(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)

    try:
        btp.gattc_read_rsp(True, True)
    except socket.timeout:
        pass
    return True


def hdl_wid_48(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                        hdl, 0, 1)

    try:
        btp.gattc_read_long_rsp(True, True)
    except socket.timeout:
        pass

    return True


def hdl_wid_52(desc):
    return btp.verify_description(desc)


def hdl_wid_58(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                        hdl, 0, 1)

    try:
        btp.gattc_read_long_rsp(True, True)
    except socket.timeout:
        pass

    return True
