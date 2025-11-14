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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


def hdl_wid_5(params: WIDParams):
    """Please write to Audio Input Control Point with the Set Gain Setting Op Code
    value of 0x01, the Gain Setting parameters set to a random value greater than
    100 and the Change Counter parameter set."""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    gain = random.randrange(101, 127, 1)
    btp.aics_set_gain(gain, addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)
    if ev[3] == 2:
        # opcode == 0x02: set gain
        return True
    else:
        return False


def hdl_wid_6(params: WIDParams):
    """Please write to Audio Input Control Point with the Set Gain Setting Op Code
    value of 0x01, the Gain Setting parameters set to a random value less than
    -100 and the Change Counter parameter set"""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    gain = random.randrange(-128, -101, 1)
    btp.aics_set_gain(gain, addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)
    if ev[3] == 2:
        # opcode == 0x02: set gain
        return True
    else:
        return False


def hdl_wid_7(params: WIDParams):
    """Please write to Audio Input Control Point with the Mute Op Code."""
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_mute(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)
    if ev[3] == 3:
        # opcode == 0x03: mute
        return True
    else:
        return False


def hdl_wid_8(params: WIDParams):
    """Please write to Audio Input Control Point with the Unmute Op Code."""

    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_unmute(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)
    if ev[3] == 4:
        # opcode == 0x04: unmute
        return True
    else:
        return False


def hdl_wid_9(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Manual Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_man_gain_set(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 10)
    if ev[3] == 5:
        # opcode == 0x05: set manual gain
        return True
    else:
        return False


def hdl_wid_10(params: WIDParams):
    """
    Please write to Audio Input Control Point with the Set Automatic Op Code.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    btp.aics_auto_gain_set(addr_type, addr)
    ev = stack.aics.wait_aics_procedure_ev(addr_type, addr, 30)
    if ev[3] == 6:
        # opcode == 0x06: set automatic gain
        return True
    else:
        return False


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
    gap_ev = stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30)
    if gap_ev is None:
        return False
    btp.vcp_discover(addr_type, addr)
    ev = stack.vcp.wait_discovery_completed_ev(addr_type, addr, 30, remove=False)
    if ev is None:
        return False

    return True


def hdl_wid_20103(params: WIDParams):
    """
    Please take action to discover the Volume State characteristic from the
    Volume Control. Discover the primary service if needed.
    """

    # Discover and subscribe at wid 20100/20107

    return True


def hdl_wid_20106(params: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of Volume
    State characteristic to enable notification.
    """

    # Discover and subscribe at wid 20100

    return True


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read Volume State characteristic with handle = 0x00A4
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    no_action_tc = [
        'VCP/VC/SPE/BI-01-C',
        'VCP/VC/SPE/BI-02-C',
        'VCP/VC/SPE/BI-03-C',
        'VCP/VC/SPE/BI-04-C',
        'VCP/VC/SPE/BI-05-C',
        'VCP/VC/SPE/BI-06-C',
        'VCP/VC/SPE/BI-07-C',
        'VCP/VC/SPE/BI-08-C',
        'VCP/VC/SPE/BI-09-C',
        'VCP/VC/SPE/BI-10-C',
        'VCP/VC/SPE/BI-11-C',
        'VCP/VC/SPE/BI-12-C',
        'VCP/VC/SPE/BI-13-C',
    ]

    if params.test_case_name in no_action_tc and stack.vcp.wid_counter > 0:
        return True

    description_mapping = {
        "Volume State": (btp.vcp_state_read, stack.vcp.wait_vcp_state_ev),
        "Volume Flags": (btp.vcp_volume_flags_read, stack.vcp.wait_vcp_flags_ev),
        "Offset State": (btp.vocs_offset_state_get, stack.vocs.wait_vocs_state_ev),
        "Audio Location": (btp.vocs_audio_location_get,
                           stack.vocs.wait_vocs_location_ev),
        "Audio Input State": (btp.aics_state_get, stack.aics.wait_aics_state_ev),
        "Gain Setting Properties": (btp.aics_gain_setting_prop_get,
                                    stack.aics.wait_aics_gain_setting_prop_ev),
        "Audio Input Type": (btp.aics_type_get, stack.aics.wait_aics_input_type_ev),
        "Audio Input Status": (btp.aics_status_get,
                               stack.aics.wait_aics_input_type_ev),
    }

    operation_name = re.findall(r'read\s(.*?)\scharacteristic', params.description)

    if operation_name[0] in description_mapping:
        read_func, wait_for_ev = description_mapping[operation_name[0]]
        read_func(addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10, remove=True)
        if ev is None:
            return False

    stack.vcp.wid_counter += 1

    return True


def hdl_wid_20110(params: WIDParams):
    """Please send write request to handle 0x00AA with following value.
    Volume Control Point:
    Op Code: [0 (0x00)] Relative Volume Down
    Change Counter: <WildCard: Exists>"""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    ev = None
    ev2 = None

    pattern = r'with following value\.(.*?):'
    test_val = 10
    matches = re.search(pattern, params.description, re.DOTALL)
    if matches:
        control_point = matches.group(1).strip()

    # This dict contains Control Point Names and Opcodes that are found in description
    # and assigns btp commands and btp opcodes related to them
    operations = {
        'Volume Control Point': {
            '0x00': (btp.vcp_volume_down, 5),
            '0x01': (btp.vcp_volume_up, 6),
            '0x02': (btp.vcp_unmute_vol_down, 7),
            '0x03': (btp.vcp_unmute_vol_up, 8),
            '0x04': (btp.vcp_set_vol, 9),
            '0x05': (btp.vcp_unmute, 10),
            '0x06': (btp.vcp_mute, 11),
            'WildCard': (btp.vcp_volume_up, 6),
            ev: stack.vcp.wait_vcp_state_ev,
            ev2: stack.vcp.wait_vcp_procedure_ev
        },
        'Audio Input Control Point': {
            '0x01': (btp.aics_set_gain, 2),
            '0x02': (btp.aics_unmute, 4),
            '0x03': (btp.aics_mute, 3),
            '0x04': (btp.aics_man_gain_set, 5),
            '0x05': (btp.aics_auto_gain_set, 6),
            'WildCard': (btp.aics_mute, 3),
            ev: stack.aics.wait_aics_state_ev,
            ev2: stack.aics.wait_aics_procedure_ev
        },
        'Volume Offset Control Point': {
            '0x01': (btp.vocs_offset_state_set, 6),
            'WildCard': (btp.vocs_offset_state_set, 6),
            ev: stack.vocs.wait_vocs_state_ev,
            ev2: stack.vocs.wait_vocs_procedure_ev
        }
    }

    if 'Op Code: <WildCard: Exists>' in params.description:
        op_code = 'WildCard'
    else:
        op_code = str(re.findall(r'\(([^)]+)\)', params.description)[0])

    function_to_run = operations[control_point][op_code][0]

    if 'VCP/VC/SPE' in params.test_case_name:
        wait_for_ev = operations[control_point][ev2]
        if control_point == 'Volume Control Point' and op_code == '0x04':
            function_to_run(test_val, addr_type, addr)
        elif control_point == 'Audio Input Control Point' and op_code == '0x01':
            function_to_run(test_val, addr_type, addr)
        elif control_point == 'Volume Offset Control Point':
            function_to_run(test_val, addr_type, addr)
        else:
            function_to_run(addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10)
        btp_opcode = operations[control_point][op_code][1]
        if ev[3] == btp_opcode:
            return True
        else:
            return False

    wait_for_ev = operations[control_point][ev]

    if control_point == 'Volume Control Point' and op_code == '0x04':
        function_to_run(test_val, addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10)
    elif control_point == 'Audio Input Control Point' and op_code == '0x01':
        function_to_run(test_val, addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10)
    elif control_point == 'Volume Offset Control Point':
        function_to_run(test_val, addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10)
    else:
        function_to_run(addr_type, addr)
        ev = wait_for_ev(addr_type, addr, 10)

    if ev is None:
        return False

    return True


def hdl_wid_20116(params: WIDParams):
    """
    Please send command to the PTS to discover all mandatory characteristics
    of the Volume Control supported by the IUT.
    Discover primary service if needed.
    """

    # Discover and subscribe at wid 20100

    return True


def hdl_wid_20121(params: WIDParams):
    """
    Please write value with write command (without response) to handle 0x00B5
    with following value: Any attribute value,
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()
    btp.vocs_audio_loc(10, addr_type, addr)

    return True


def hdl_wid_20144(params: WIDParams):
    """
    Please click Yes if IUT support Write Command(without response), otherwise
    click No.
    """

    return True


def hdl_wid_20206(params: WIDParams):
    """Please verify that for each supported characteristic, attribute handle/UUID
    pair(s) is returned to the upper tester.

    Volume Control Point: Attribute Handle = 0x00A9
    Characteristic Properties = 0x08
    Handle = 0x00AA
    UUID = 0x2B7E

    Volume Flags: Attribute Handle = 0x00A6
    Characteristic Properties = 0x12
    Handle = 0x00A7
    UUID = 0x2B7F

    Volume State: Attribute Handle = 0x00A3
    Characteristic Properties = 0x12
    Handle = 0x00A4
    UUID = 0x2B7D"""

    stack = get_stack()

    if params.test_case_name == "VCP/VC/CGGIT/SER/BV-01-C":
        chars = (stack.vcp.event_queues[defs.BTP_VCP_EV_DISCOVERED][0][3:6])
        chrc_list = [f'{chrc:04X}'.upper() for chrc in chars]
    elif params.test_case_name == "VCP/VC/CGGIT/SER/BV-02-C":
        chars = (stack.vcp.event_queues[defs.BTP_VCP_EV_DISCOVERED][0][6:10])
        chrc_list = [f'{chrc:04X}'.upper() for chrc in chars]
    elif params.test_case_name == "VCP/VC/CGGIT/SER/BV-03-C":
        chars = (stack.vcp.event_queues[defs.BTP_VCP_EV_DISCOVERED][0][10:])
        chrc_list = [f'{chrc:04X}'.upper() for chrc in chars]

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    desc_params_list = [params[i] for i in range(2, len(params), 4)]

    if desc_params_list == chrc_list:
        return True

    return False
