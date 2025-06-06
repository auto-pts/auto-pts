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
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    stack = get_stack()
    if stack.is_svc_supported('GATT_CL') and 'GATT/CL' in test_case_name:
        return generic_wid_hdl(wid, description, test_case_name,
                               [__name__, 'autopts.wid.gatt_client'])

    log(f'{gatt_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name,
                           [__name__, 'autopts.wid.gatt'])


def hdl_wid_3(_: WIDParams):
    time.sleep(2)
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return True


def hdl_wid_49(_: WIDParams):
    time.sleep(30)
    return True


def hdl_wid_92(_: WIDParams):
    time.sleep(2)
    return True


def hdl_wid_98(_: WIDParams):
    time.sleep(5)
    return True


def hdl_wid_118(_: WIDParams):
    return f'{65000:04x}'
