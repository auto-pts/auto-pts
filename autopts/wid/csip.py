#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import AdType, OwnAddrType, WIDParams, gap_settings_btp2txt

log = logging.debug


def hdl_wid_3(_: WIDParams):
    """Please create different workspaces and run this test case with 3 instances of PTS."""

    return True


def hdl_wid_4(_: WIDParams):
    """Please verify the number of discovered Set Members is equal to 3."""

    stack = get_stack()

    if stack.csip.member_cnt != 3:
        return False

    return True


def hdl_wid_5(params: WIDParams):
    """
        Please have IUT enter GAP Discoverable Mode and generate Advertising Packets.
    """

    if params.test_case_name == "CSIP/SR/SP/BV-03-C":
        # Encrypted SIRK
        btp.csis_set_sirk_type(1)
    else:
        # Plain Text SIRK
        btp.csis_set_sirk_type(0)

    rsi = btp.csis_get_member_rsi()
    if not rsi:
        return False

    advdata = {}
    advdata[AdType.rsi] = struct.pack('<6B', *rsi)

    stack = get_stack()

    key = gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]
    if stack.gap.current_settings_get(key):
        btp.gap_adv_off()

    btp.gap_adv_ind_on(ad=advdata, own_addr_type=OwnAddrType.le_resolvable_private_address)
    return True


def hdl_wid_9(_: WIDParams):
    """Please verify IUT write to the Lock characteristic on PTS in ascending order of
       the Rank characteristic value.(LT1, LT2, LT3)"""

    # In zephyr the members are locked starting from lowest rank going up.

    return True


def hdl_wid_10(_: WIDParams):
    """Please verify IUT write to the Lock characteristic on PTS in descending order
       of the Rank characteristic value.(LT3, LT2, LT1)"""

    # In zephyr the members are unlocked starting from highest rank going down.

    return True


def hdl_wid_11(_: WIDParams):
    """Please read any characteristic."""

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_sirk_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_12(_: WIDParams):
    """
    Please verify that SIRK is not encrypted. Click Yes, if it is Plain Text
    otherwise click No.
    """

    return True


def hdl_wid_13(params: WIDParams):
    """
    Please verify that decrypted SIRK is 838E680553F1415AA265BBAFC6EA03B8.
    Click Yes, if it is Encrypted otherwise click No.
    """

    stack = get_stack()
    sirk = stack.csip.event_queues[defs.BTP_CSIP_EV_SIRK][0][2]
    pattern = r'decrypted SIRK is (\w+)\.'
    match = re.search(pattern, params.description)
    desc_sirk = match.group(1)

    if sirk.upper() != desc_sirk:
        return False

    return True


def hdl_wid_14(params: WIDParams):
    """Please confirm that IUT stopped the Coordinated Set Discovery procedure.
       Click Yes, if stopped otherwise click No."""

    stack = get_stack()

    if stack.csip.event_queues[defs.BTP_CSIP_EV_DISCOVERED] != []:
        return False

    return True


def hdl_wid_20001(_: WIDParams):
    """
    Please prepare IUT into a connectable mode.
    Description: Verify that the Implementation Under Test (IUT) can accept
    GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad, own_addr_type=OwnAddrType.le_resolvable_private_address)
    return True


def hdl_wid_20100(params: WIDParams):
    """Please initiate a GATT connection to the PTS."""

    stack = get_stack()

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    elif 'LT3' in params.test_case_name:
        addr_type = btp.lt3_addr_type_get()
        addr = btp.lt3_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    btp.gap_conn(addr, addr_type)
    stack.gap.wait_for_connection(timeout=10, addr=addr)
    sec_lvl = stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=10, addr=addr)

    # Workaround for issue described by PTS Request ID 170874
    if sec_lvl != 2:
        btp.gap_pair(addr, addr_type)
        stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30, addr=addr)

    # CSIP/CL/SP/BV-07-C will receive the WID 20101. Hence, no need to perform discovery here.

    if 'CSIP/CL/SP/BV-03-C' in params.test_case_name or\
            'CSIP/CL/SP/BV-04-C' in params.test_case_name or\
            'CSIP/CL/SPE/BI-01-C' in params.test_case_name or\
            'CSIP/CL/SPE/BI-02-C' in params.test_case_name or\
            'CSIP/CL/SPE/BI-03-C' in params.test_case_name:
        btp.csip_discover(addr_type, addr)
        ev = stack.csip.wait_sirk_ev(addr_type, addr, 30)
        if ev is None:
            return False
        stack.csip.member_cnt += 1

    return True


def hdl_wid_20101(params: WIDParams):
    """
    Please send discover primary services command to the PTS.
    """
    stack = get_stack()

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    elif 'LT3' in params.test_case_name:
        addr_type = btp.lt3_addr_type_get()
        addr = btp.lt3_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_sirk_ev(addr_type, addr, 30)
    if ev is None:
        return False

    stack.csip.member_cnt += 1

    return True


def hdl_wid_20103(_: WIDParams):
    """
    Please take action to discover the xxxx from the xxxx.
    Discover the primary service if needed. Verify that the Implementation Under
    Test (IUT) can send Discover All Characteristics command.
    """

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_sirk_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_20106(_: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of xxxx
    characteristic to enable notification.Descriptor handle value: 0x00B3
    """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read Set Identity Resolving Key
    characteristic with handle = 0x0162.
    """
    stack = get_stack()
    if stack.csip.wid_cnt > 0:
        return True

    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_sirk_ev(addr_type, addr, 10, remove=False)
    stack.csip.wid_cnt += 1
    if params.test_case_name == 'CSIP/CL/SPE/BI-04-C':
        # This test validates that Discovery procedure was stopped.
        # SIRK is read during discovery
        if ev is None:
            return True
        return False

    if ev is None:
        return False

    return True


def hdl_wid_20108(_: WIDParams):
    """
    Please send notifications for Characteristic 'Set Member Lock' to the PTS.
    Expected Value: Any value
    """

    return True


def hdl_wid_20110(params: WIDParams):
    """
    Please send write request to handle 0x0164 with following value.
    Set Member Lock:
    Set Member Lock: [2 (0x02)]
    """
    stack = get_stack()

    # LT3 test cases
    if 'CSIP/CL/SPE/BI-01-C' in params.test_case_name:
        if stack.csip.wid_cnt > 1:
            return True
        if stack.csip.wid_cnt == 1:
            stack.csip.wid_cnt += 1
            stack.csip.wait_lock_ev(10)
            return True
        btp.csip_set_coordinator_lock()
        stack.csip.wait_lock_ev(10)
        stack.csip.wid_cnt += 1
        return True

    # LT3 test cases
    if 'CSIP/CL/SP/BV-03-C' in params.test_case_name:
        if stack.csip.wid_cnt > 0:
            return True
        btp.csip.csip_set_coordinator_lock()
        ev = stack.csip.wait_lock_ev(10)
        if ev[0] != 0:
            # success
            return False
        stack.csip.wid_cnt += 1
        return True

    # LT3 test cases
    if 'CSIP/CL/SP/BV-04-C' in params.test_case_name:
        if stack.csip.wid_cnt > 0:
            return True
        btp.csip.csip_set_coordinator_release()
        ev = stack.csip.wait_lock_ev(10)
        if ev[0] != 0:
            # success
            return False
        stack.csip.wid_cnt += 1
        return True

    if "Set Member Lock: [2 (0x02)]" in params.description:
        btp.csip.csip_set_coordinator_lock()
    else:
        btp.csip.csip_set_coordinator_release()

    ev = stack.csip.wait_lock_ev(10)
    if ev is None:
        return False

    return True


def hdl_wid_20115(params: WIDParams):
    """
    Please initiate a GATT disconnection to the PTS.
    """

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    elif 'LT3' in params.test_case_name:
        addr_type = btp.lt3_addr_type_get()
        addr = btp.lt3_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    btp.gap_disconn(addr, addr_type)

    return True


def hdl_wid_20116(params: WIDParams):
    """
    Please send command to the PTS to discover all mandatory characteristics
    of the Coordinated Set Identification supported by the IUT.
    Discover primary service if needed.
    """

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_sirk_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_20128(_: WIDParams):
    """
    Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True


def hdl_wid_20206(params: WIDParams):
    """
    Please verify that for each supported characteristic, attribute
    handle/UUID pair(s) is returned to the upper tester.
    """
    stack = get_stack()

    # Fix: Check if the event queue is empty
    # Workaround for PTS Request ID 173881
    discovered_events = stack.csip.event_queues[defs.BTP_CSIP_EV_DISCOVERED]
    if not discovered_events:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

        btp.csip_discover(addr_type, addr)
        ev = stack.csip.wait_discovery_completed_ev(addr_type, addr, 30, False)
        if ev is None:
            logging.error("No CSIP discovery events received")
            return False

    chars = stack.csip.event_queues[defs.BTP_CSIP_EV_DISCOVERED][0][3:]
    chrc_list = [f'{chrc:04X}' for chrc in chars]

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    desc_params = pattern.findall(params.description)
    if not desc_params:
        logging.error("parsing error")
        return False

    desc_params_list = desc_params[2::4]

    if desc_params_list == chrc_list:
        return True

    return False
