#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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
import random
import re
import sys
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams


log = logging.debug


def micp_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log(f'{micp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    module = sys.modules[__name__]

    try:
        handler = getattr(module, f'hdl_wid_{wid}')
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


micp_aics_state_used = False


def hdl_wid_2(params: WIDParams):
    """
    Please read any characteristic.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.micp_mute_read(addr_type, addr)
    ev = stack.micp.wait_mute_state_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_5(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Gain Setting Op Code value
    of 0x01,the Gain Setting parameters set to a random value greater than 100 and the
    Change Counter parameter set.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    gain = random.randrange(101, 127, 1)
    btp.aics_set_gain(gain, addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    # opcode 0x02: set gain
    return ev[3] == 2


def hdl_wid_6(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Gain Setting Op Code value
    of 0x01, the Gain Setting parameters set to a random value less than -100 and
    the Change Counter parameter set.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    gain = random.randrange(-128, -101, 1)
    btp.aics_set_gain(gain, addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    # opcode 0x02: set gain
    return ev[3] == 2


def hdl_wid_7(params:WIDParams):
    """
    Please write to Audio Input Control Point characteristic with the Mute Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_mute(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    # opcode 0x03: mute
    return ev[3] == 3


def hdl_wid_8(params: WIDParams):
    """
    Please write to Audio Input Control Point characteristic with the Unmute Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_unmute(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    # opcode 0x04: unmute
    return ev[3] == 4


def hdl_wid_9(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Manual Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_man_gain_set(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)

    # opcode 0x05: set manual gain
    return ev[3] == 5


def hdl_wid_10(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Automatic Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_auto_gain_set(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 30)

    # opcode 0x06: set automatic gain
    return ev[3] == 6


def hdl_wid_20100(params: WIDParams):
    """
    Please initiate a GATT connection to the PTS. Verify that the Implementation
    Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.gap_conn()
    stack.gap.wait_for_connection(timeout=5, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30)
    btp.micp_discover(addr_type, addr)
    ev = stack.micp.wait_discovery_completed_ev(addr_type, addr, 30, remove=False)
    if ev is None:
        return False

    return True


def hdl_wid_20103(params: WIDParams):
    """
    Please take action to discover the xxxx from the xxxx.
    Discover the primary service if needed. Verify that the Implementation Under
    Test (IUT) can send Discover All Characteristics command.
    """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20106(params: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of Audio Input State
    characteristic to enable notification.Descriptor handle value: 0x00B3
    """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read xxxx characteristic with handle = 0xXXXX.
    """
    test_case_names = [
        "MICP/CL/SPE/BI-02-C",
        "MICP/CL/SPE/BI-03-C",
        "MICP/CL/SPE/BI-04-C",
        "MICP/CL/SPE/BI-05-C",
        "MICP/CL/SPE/BI-06-C"
    ]
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    global micp_aics_state_used

    if params.test_case_name in test_case_names:
        if not micp_aics_state_used:
            btp.aics_state_get(addr_type, addr)
            micp_aics_state_used = True
            ev = stack.aics.wait_aics_state_ev(addr_type, addr, 30)
            if ev is None:
                return False
            return True

        micp_aics_state_used = False

        return True

    if "Mute" in params.description:
        btp.micp_mute_read(addr_type, addr)
        ev = stack.micp.wait_mute_state_ev(addr_type, addr, 30)
        if ev is None:
            return False
    elif "Audio Input State" in params.description:
        btp.aics_state_get(addr_type, addr)
        ev = stack.aics.wait_aics_state_ev(addr_type, addr, 30)
        if ev is None:
            return False
    elif "Gain Setting Properties" in params.description:
        btp.aics_gain_setting_prop_get(addr_type, addr)
        ev = stack.aics.wait_aics_gain_setting_prop_ev(addr_type, addr, 30)
        if ev is None:
            return False
    elif "Audio Input Type" in params.description:
        btp.aics_type_get(addr_type, addr)
        ev = stack.aics.wait_aics_input_type_ev(addr_type, addr, 30)
        if ev is None:
            return False
    elif "Audio Input Status" in params.description:
        btp.aics_status_get(addr_type, addr)
        ev = stack.aics.wait_aics_status_ev(addr_type, addr, 30)
        if ev is None:
            return False

    return True


def hdl_wid_20110(params: WIDParams):
    """
    Please send write request to handle 0xXXXX with following value.
    Audio Input Control Point:
    Op Code: [1 (0xxx)] x
    Change Counter: <WildCard: Exists>
    Gain Setting: <WildCard: Exists>
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    if "Set Gain" in params.description:
        btp.aics_set_gain(2, addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-02-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x02: set gain
            return ev[3] == 2
    elif "Mute" in params.description:
        btp.aics_mute(addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-04-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x03: mute
            return ev[3] == 3
    elif "Unmute" in params.description:
        btp.aics_unmute(addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-03-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x04: unmute
            return ev[3] == 4
    elif "Set Manual" in params.description:
        btp.aics_man_gain_set(addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-05-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x05: set manual gain
            return ev[3] == 5
    elif "Set Automatic" in params.description:
        btp.aics_auto_gain_set(addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-06-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x06: set automatic gain
            return ev[3] == 6
    elif "Op Code: <WildCard: Exists>" in params.description:
        btp.aics_auto_gain_set(addr_type, addr)
        if params.test_case_name == "MICP/CL/SPE/BI-08-C":
            ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10, remove=False)
            # opcode 0x06: set automatic gain
            return ev[3] == 6
    elif "0x00D3" in params.description:
        btp.micp_mute(addr_type, addr)
        ev = stack.micp.wait_mute_state_ev(addr_type, addr, 30)
        if ev is None:
            return False
        return True
    else:
        return False

    ev = stack.aics.wait_aics_state_ev(addr_type, addr, 30)
    if ev is None:
        return False

    return True


def hdl_wid_20116(params: WIDParams):
    """Please send command to the PTS to discover all mandatory characteristics
     of the Microphone Control supported by the IUT. Discover primary service if needed.
     """

    # Discover and subscribe at hdl_wid_20100

    return True


def hdl_wid_20206(params: WIDParams):
    """Please verify that for each supported characteristic, attribute handle/UUID
     pair(s) is returned to the upper tester.
     Mute: Attribute Handle = 0x00A2
     Characteristic Properties = 0x1A
     Handle = 0x00A3
     UUID = 0x2BC3
     """
    stack = get_stack()

    if params.test_case_name == "MICP/CL/CGGIT/SER/BV-01-C":
        chars = (stack.micp.event_queues[defs.BTP_MICP_EV_DISCOVERED][0][3])
        chrc_list = ['{:04X}'.format(chars).upper()]
    else:
        chars = (stack.micp.event_queues[defs.BTP_MICP_EV_DISCOVERED][0][4:])
        chrc_list = ['{:04X}'.format(chrc).upper() for chrc in chars]

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    desc_params_list = [params[i] for i in range(2, len(params), 4)]

    if desc_params_list == chrc_list:
        return True

    return False


def hdl_wid_20145(params: WIDParams):
    """
    Please click Yes if IUT support Write Request, otherwise click No.
    """

    return True


