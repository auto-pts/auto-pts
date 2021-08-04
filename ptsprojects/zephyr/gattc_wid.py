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
import sys

from pybtp import btp
from ptsprojects.zephyr.gatt_wid import gatt_wid_hdl

from ptsprojects.testcase import MMI


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


def hdl_wid_24(desc):
    return btp.verify_description(desc)


def hdl_wid_17(desc):
    return btp.verify_description(desc)


def hdl_wid_52(desc):
    return btp.verify_description(desc)
