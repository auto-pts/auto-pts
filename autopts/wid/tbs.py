#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
import re

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp import defs
from autopts.pybtp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug
global wid_counter
wid_counter = 0


def tbs_wid_hdl(wid, description, test_case_name):
    log(f'{tbs_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin


def hdl_wid_101(params: WIDParams):
    """Please generate incoming call from the Server"""

    btp.tbs_remote_incoming(0, 'tel:+19991111234', 'tel:+19991111235', 'tel:+19991110011')

    return True


def hdl_wid_106(params: WIDParams):
    """Please make a call ID (1) to the Remotely Held state."""

    call_id = re.findall(r'Please make a call ID \((\d+)\)', params.description)
    btp.tbs_remote_hold_call(int(call_id[0]))

    return True


def hdl_wid_110(params: WIDParams):
    """Please make one of call (Call ID: 2) to the locally
     and remotely held state."""

    call_id_list = re.findall(r'Call ID: (\d+)', params.description)
    call_id = int(call_id_list[0])
    btp.tbs_remote_hold_call(call_id)
    btp.tbs_hold_call(call_id)

    return True


def hdl_wid_111(params: WIDParams):
    """Waiting for Bearer Signal Strength Notification."""

    btp.tbs_set_signal_strength(0, 10)

    return True


def hdl_wid_116(params: WIDParams):
    """Please Configure to disallow Join."""

    # Currently there is no API to disallow Join without recompilation.

    return True


def hdl_wid_117(params: WIDParams):
    """Please make a call ID (11) to the Alerting state and send
     Call State Notification."""

    return True


def hdl_wid_118(params: WIDParams):
    """Please update Bearer Provider Name characteristic(Handle = 0x006D) and send
     a notification containing the updated value of the characteristic."""

    if "Name" in params.description:
        btp.tbs_set_bearer_name(0, 'newname')
    elif "Technology" in params.description:
        btp.tbs_set_bearer_technology(0, 0x03)
    elif "URI Schemes" in params.description:
        btp.tbs_set_uri_scheme_list(0, 'tel')
    elif "Status Flags" in params.description:
        btp.tbs_set_status_flags(0, 2)

    return True


def hdl_wid_120(params: WIDParams):
    """Please force to update Bear Signal Strength value 3 times and then send
     a Bearer Signal Strength notification using new interval."""

    btp.tbs_set_signal_strength(0, 9)
    btp.tbs_set_signal_strength(0, 8)
    btp.tbs_set_signal_strength(0, 7)

    return True


def hdl_wid_2000(_: WIDParams):
    """Please enter the secure ID."""

    stack = get_stack()

    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None

    return passkey


def hdl_wid_20001(_: WIDParams):
    """Please prepare IUT into a connectable mode. Verify that the
    Implementation Under Test (IUT) can accept GATT connect request from PTS."""

    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_20002(_: WIDParams):
    """
    Please prepare IUT into an L2CAP Credit Based Connection connectable mode.
    Description: Verify that the Implementation Under Test (IUT) can accept
    L2CAP_CREDIT_BASED_CONNECTION_REQ from PTS.
    """
    return True


def hdl_wid_20108(_: WIDParams):
    """
    Please send notifications for Characteristic '0x0088, 0x0093, 0x0085, 0x0096, ' to the PTS.
    """

    return True


def hdl_wid_20141(params: WIDParams):
    """Please update Bearer Provider Name characteristic with value whose length
     is greater than the (ATT_MTU-3). Click OK when it is ready."""

    # Insufficient authentication in all test cases (no secure pairing)
    ovs_val = 'namenamenamenamenamedddddddd'
    ovs_uri = 'tel:12345678901234567890'
    if "Name" in params.description:
        btp.tbs_set_bearer_name(0, ovs_val)
    elif "URI Schemes" in params.description:
        btp.tbs_set_uri_scheme_list(0, ovs_uri)
    elif "Current Calls" in params.description:
        for _ in range(0, 20):
            btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call Target" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call State" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Incoming Call" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call Friendly Name" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)

    return True


def hdl_wid_20142(params: WIDParams):
    """Please update Bearer Provider Name characteristic(Handle = 0x006D) and send
       a notification containing the updated value of the characteristic with
       a different value whose length is greater than the (ATT_MTU-3)"""

    ovs_val = 'namenamenamenamenamexxxxxxxx'
    ovs_uri = 'tel:12345678901234567890'

    if "Name" in params.description:
        btp.tbs_set_bearer_name(0, ovs_val)
    elif "URI Schemes" in params.description:
        btp.tbs_set_uri_scheme_list(0, ovs_uri)
    elif "Current Calls" in params.description:
        for _ in range(0, 20):
            btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call Target" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call State" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Incoming Call" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)
    elif "Call Friendly Name" in params.description:
        btp.tbs_remote_incoming(0, ovs_uri, ovs_uri, ovs_uri)

    return True
