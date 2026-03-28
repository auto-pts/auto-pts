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

from autopts.ptsprojects.stack import get_stack
from autopts.wid import generic_wid_hdl

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    use_gattc = get_stack().is_svc_supported("GATT_CL")
    if test_case_name.startswith("GATT/CL/GAR/") and use_gattc:
        return generic_wid_hdl(wid, description, test_case_name, [__name__, "autopts.wid.gatt_client", "autopts.wid.gatt"])

    log(f"{gatt_wid_hdl.__name__}, {wid}, {description}, {test_case_name}")
    return generic_wid_hdl(wid, description, test_case_name, [__name__, "autopts.wid.gatt"])
