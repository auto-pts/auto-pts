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
import socket
from time import sleep

from autopts.pybtp import btp
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


# For tests that expect "OK" response even if read operation is not successful
def gap_wid_hdl_failed_read(wid, description, test_case_name):
    if wid == 112:
        log("%s, %r, %r, %s", gap_wid_hdl_failed_read.__name__, wid, description,
            test_case_name)
        return hdl_wid_112_timeout(description)
    return gap_wid_hdl(wid, description, test_case_name)


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
        log("%s, %r, %r, %s", gap_wid_hdl_mode1_lvl2.__name__, wid, description,
            test_case_name)
        return hdl_wid_139_mode1_lvl4(description)
    return gap_wid_hdl(wid, description, test_case_name)


def hdl_wid_104(desc):
    return True


def hdl_wid_112(desc):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(desc)
    if not handle:
        return False

    try:
        btp.gattc_read(bd_addr_type, bd_addr, handle)
        btp.gattc_read_rsp()
    except socket.timeout:
        return False
    return True


def hdl_wid_112_timeout(desc):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(desc)
    if not handle:
        return False

    try:
        btp.gattc_read(bd_addr_type, bd_addr, handle)
        btp.gattc_read_rsp()
    except socket.timeout:
        pass
    return True


def hdl_wid_204(desc):
    btp.gap_start_discov(discov_type='passive', mode='observe')
    sleep(10)
    btp.gap_stop_discov()
    return btp.check_discov_results(addr_type=0x02)


def hdl_wid_242(desc):
    """
    Please send a Security Request.
    """
    btp.gap_pair()
    return True


def hdl_wid_1002(desc):
    stack = get_stack()
    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None
    return passkey
