#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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

from autopts.ptsprojects.stack import L2CapChannelStatusCode, get_stack
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log(f'{l2cap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.l2cap'])


# wid handlers section begin
def hdl_wid_251(_: WIDParams):
    """
        Did Implementation Under Test(IUT) receive Connection refused 'Insufficient Encryption' 0x0008 error?
    """
    stack = get_stack()
    stack.l2cap.wait_for_conn_req_reject_ev()
    reason = stack.l2cap.conn_req_reject_reason
    if reason == L2CapChannelStatusCode.INSUFFICIENT_ENCRYPTION:
        return True
    return False


def hdl_wid_252(_: WIDParams):
    """
        Did Implementation Under Test(IUT) receive Connection refused 'Insufficient Authentication' 0x0005 error
    """
    stack = get_stack()
    stack.l2cap.wait_for_conn_req_reject_ev()
    reason = stack.l2cap.conn_req_reject_reason
    if reason == L2CapChannelStatusCode.INSUFFICIENT_AUTHENTICATION:
        return True
    return False


def hdl_wid_253(_: WIDParams):
    """
        Did Implementation Under Test(IUT) receive Connection refused 'Insufficient Authorization' 0x0006 error
    """
    stack = get_stack()
    stack.l2cap.wait_for_conn_req_reject_ev()
    reason = stack.l2cap.conn_req_reject_reason
    if reason == L2CapChannelStatusCode.INSUFFICIENT_AUTHORIZATION:
        return True
    return False


def hdl_wid_254(_: WIDParams):
    """
        Did Implementation Under Test(IUT) receive Connection refused 'Insufficient Encryption Key Size' 0x0007 error
    """
    stack = get_stack()
    stack.l2cap.wait_for_conn_req_reject_ev()
    reason = stack.l2cap.conn_req_reject_reason
    if reason == L2CapChannelStatusCode.INSUFFICIENT_ENCRYPTION_KEY_SIZE:
        return True
    return False
