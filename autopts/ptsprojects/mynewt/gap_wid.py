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
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl
from autopts.wid.gap import hdl_wid_139_mode1_lvl2, hdl_wid_139_mode1_lvl4

log = logging.debug


def gap_wid_hdl(wid, description, test_case_name):
    log(f'{gap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.gap'])


# For tests in SC only, mode 1 level 3
def gap_wid_hdl_mode1_lvl2(wid, description, test_case_name):
    if wid == 139:
        log("%s, %r, %r, %s", gap_wid_hdl_mode1_lvl2.__name__, wid, description,
            test_case_name)
        return hdl_wid_139_mode1_lvl2(description)
    return gap_wid_hdl(wid, description, test_case_name)


# For tests in SC only, mode 1 level 4
def gap_wid_hdl_mode1_lvl4(wid, description, test_case_name):
    if wid == 139:
        log("%s, %r, %r, %s", gap_wid_hdl_mode1_lvl4.__name__, wid, description,
            test_case_name)
        return hdl_wid_139_mode1_lvl4(description)
    return gap_wid_hdl(wid, description, test_case_name)


def hdl_wid_104(_: WIDParams):
    return True


def hdl_wid_112(params: WIDParams):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(params.description)
    if not handle:
        return False

    btp.gatt_cl_read(bd_addr_type, bd_addr, handle)
    return True


def hdl_wid_204(_: WIDParams):
    btp.gap_start_discov(discov_type='passive', mode='observe')
    sleep(10)
    btp.gap_stop_discov()
    return btp.check_discov_results(addr_type=0x02)


def hdl_wid_1002(_: WIDParams):
    stack = get_stack()
    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None
    return passkey
