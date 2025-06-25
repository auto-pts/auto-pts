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
from enum import IntEnum, IntFlag

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


class OpCode(IntEnum):
    ACCEPT = 0x00
    TERMINATE = 0x01
    LOCAL_HOLD = 0x02
    LOCAL_RETRIEVE = 0x03
    ORIGINATE = 0x04
    JOIN = 0x05
    ILLEGAL = 0x06


class ResultCode(IntEnum):
    SUCCESS = 0x00
    OPCODE_NOT_SUPPORTED = 0x01
    OPERATION_NOT_POSSIBLE = 0x02
    INVALID_CALL_INDEX = 0x03
    STATE_MISMATCH = 0x04
    LACK_OF_RESOURCES = 0x05
    INVALID_OUTGOING_URI = 0x06


class CallState(IntEnum):
    INCOMING = 0x00
    DIALING = 0x01
    ALERTING = 0x02
    ACTIVE = 0x03
    LOCALLY_HELD = 0x04
    REMOTELY_HELD = 0x05
    LOCALLY_REMOTELY_HELD = 0x06


class CallFlags(IntFlag):
    INCOMING = 0x00
    OUTGOING = 0x01
    WITHHELD = 0x02
    WITHHELD_BY_NETWORK = 0x04


class Uuid(IntEnum):
    TBS = 0x184b  # Telephone Bearer service
    GTBS = 0x184c  # Generic Telephone Bearer service
    CCC = 0x2902  # Client Characteristic Configuration
    CALLSC = 0x2bbd  # Call State Characteristic
    CALLCPC = 0x2bbe  # Call Control Point Characteristic


BT_TBS_GTBS_INDEX = 0xff
# 0x00 is TBS Service index instance

global __gtbs_ccpc_handle, __round

__gtbs_ccpc_handle, __round = None, None


def disc_full(svc_uuid=None, ch_uuid=None):
    attrs = {}
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if svc_uuid:
        btp.gattc_disc_prim_uuid(bd_addr_type, bd_addr, svc_uuid)
        svcs = btp.gattc_disc_prim_uuid_rsp()
    else:
        btp.gattc_disc_all_prim(bd_addr_type, bd_addr)
        svcs = btp.gattc_disc_all_prim_rsp()

    if not svcs:
        return attrs

    for svc in svcs:
        attrs[svc] = {}

        if ch_uuid:
            btp.gattc_disc_chrc_uuid(bd_addr_type, bd_addr, svc.handle, svc.end_handle, ch_uuid)
            chars = btp.gattc_disc_chrc_uuid_rsp()
        else:
            btp.gattc_disc_all_chrc(bd_addr_type, bd_addr, svc.handle, svc.end_handle)
            chars = btp.gattc_disc_all_chrc_rsp()

        if not chars:
            continue

        for i in range(0, len(chars)):
            start_hdl = chars[i].value_handle + 1

            btp.gattc_disc_all_desc(btp.pts_addr_type_get(),
                                    btp.pts_addr_get(),
                                    start_hdl, start_hdl + 1)

            descs = btp.gattc_disc_all_desc_rsp()
            attrs[svc][chars[i]] = descs

    return attrs


def characteristic_handle(attrs, serv_uuid, char_uuid):
    for service in attrs:
        if int(service.uuid, 16) == serv_uuid:
            for char in attrs[service]:
                if int(char.uuid, 16) == char_uuid:
                    return char.value_handle
    return None


def descriptor_handle(attrs, serv_uuid, char_uuid, desc_uuid):
    for service in attrs:
        if int(service.uuid, 16) == serv_uuid:
            for char in attrs[service]:
                if int(char.uuid, 16) == char_uuid:
                    for desc in attrs[service][char]:
                        if int(desc.uuid, 16) == desc_uuid:
                            return desc.handle
    return None


def dump_services(attrs):
    print()
    for service in attrs:
        print(f"Service: {service.uuid} handles [{service.handle}, {service.end_handle}]")
        for char in attrs[service]:
            print(f"\tCharacteristic: {char.uuid} handles [{char.handle}, {char.value_handle}]")
            for desc in attrs[service][char]:
                print(f"\t\tDescriptor: {desc.uuid} handle {desc.handle}")


def hdl_wid_104(params: WIDParams):
    """
    Please Write(WRITE_REQ) Call Control Point Op Code:(0x00) and Call ID(1)
    Description: Accept the incoming call with Call_Index 1
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    tbs_testcases = ["CCP/CL/CP/BV-01-C",
                     "CCP/CL/CP/BV-02-C",
                     "CCP/CL/CP/BV-03-C",
                     "CCP/CL/CP/BV-04-C",
                     "CCP/CL/CP/BV-05-C",
                     "CCP/CL/CP/BV-06-C",
                     "CCP/CL/CP/BV-07-C",
                     "CCP/CL/SPE/BI-05-C"]

    if params.test_case_name in tbs_testcases:
        inst_index = 0x00
    else:
        inst_index = BT_TBS_GTBS_INDEX

    result = re.search(r'Op Code:\((0x[0-9A-F]{2})\) and Call ID\((\d)\)', params.description)

    if result:
        opCode, callID = int(result.group(1), 16), int(result.group(2))
        if opCode == 0:
            btp.ccp_accept_call(inst_index, callID)
        elif opCode == 1:
            btp.ccp_terminate_call(inst_index, callID)
        elif opCode == 2:
            btp.ccp_hold_call(inst_index, callID)
        elif opCode == 3:
            btp.ccp_retrieve_call(inst_index, callID)
        elif opCode == 4:
            btp.ccp_originate_call(inst_index, 'skype:test')

    ev = stack.ccp.wait_cp_ev(addr_type, addr, 30, remove=False)

    if ev is None:
        return False
    elif ev[2] != 0:
        if params.test_case_name == 'CCP/CL/SPE/BI-06-C':
            # Invalid opcode should be returned
            log(f'INVALID OPCODE: {ev[2]}')
            return True
        return False

    return True


def hdl_wid_112(params: WIDParams):
    """
    Please Write(WRITE_REQ) Call Control Point with Originate Op Code:
    (0x04) with a valid formatted URI.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    if params.test_case_name == "CCP/CL/CP/BV-06-C":
        # TBS testcase
        inst_index = 0x00
    else:
        inst_index = BT_TBS_GTBS_INDEX

    btp.ccp_originate_call(inst_index, 'skype:test')

    ev = stack.ccp.wait_cp_ev(addr_type, addr, 10)
    if ev[2] != 0:
        return False

    return True


def hdl_wid_113(params: WIDParams):
    """
    Please Write(WRITE_REQ) Call Control Point with Join Op Code:
    (0x05) with Call ID(1) and Call ID(2)
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    call_index = re.findall(r'Call ID\((\d+)\)', params.description)
    count = len(call_index)

    tbs_testcases = ["CCP/CL/CP/BV-06-C",
                     "CCP/CL/CP/BV-07-C",
                     "CCP/CL/SPE/BI-03-C"]

    if params.test_case_name in tbs_testcases:
        inst_index = 0x00
    else:
        inst_index = BT_TBS_GTBS_INDEX

    btp.ccp_join_calls(inst_index, count, call_index, addr_type, addr)
    ev = stack.ccp.wait_cp_ev(addr_type, addr, 30, remove=False)

    if ev[2] != 0:
        if params.test_case_name == 'CCP/CL/SPE/BI-03-C' or \
                params.test_case_name == 'CCP/CL/SPE/BI-04-C':
            # Invalid opcode should be returned
            return True
        return False

    return True


def hdl_wid_114(params: WIDParams):
    """
    Please send Write(WRITE_REQ) or Write Without Response to Call Control Point
    with any Op Code and Call ID with any value.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    if params.test_case_name == "CCP/CL/SPE/BI-01-C":
        # TBS testcase
        inst_index = 0x00
    else:
        inst_index = BT_TBS_GTBS_INDEX

    btp.ccp_terminate_call(inst_index, 1)
    ev = stack.ccp.wait_cp_ev(addr_type, addr, 20, remove=True)

    if ev is not None and ev[2] != 0:
        # Invalid opcode should be returned
        log(f'Invalid opcode {ev[2]}')
        return True

    return False


def hdl_wid_115(params: WIDParams):
    """
    Please execute the GATT Read Characteristic Value sub-procedure for any characteristic.
    We choose to read the call state.
    """
    btp.ccp_read_call_state(BT_TBS_GTBS_INDEX)
    success, status, index, call_count, states = btp.ccp_await_call_state()
    return success and (status == 0)


def hdl_wid_20001(_: WIDParams):
    """
    Please prepare IUT into a connectable mode.
    Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    hdl_wid_20106.count = 0
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20103(_: WIDParams):
    """
    Please take action to discover the Call State characteristic from the Generic Telephone Bearer.
    Discover the primary service if needed.
    Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    btp.ccp_discover_tbs()
    success, status, tbs_count, gtbs = btp.ccp_await_discovered()
    ev = stack.ccp.wait_chrc_handles_ev(addr_type, addr, 10, remove=True)
    if status != 0 and ev is None:
        return False

    return True


def hdl_wid_20106(_: WIDParams):
    """
    Please write to Client Characteristic Configuration Descriptor of Call Control Point
    characteristic to enable notification.
    """
    if hdl_wid_20106.count > 0:
        return True

    if not hdl_wid_20106.count:
        hdl_wid_20106.count += 1
    btp.ccp_discover_tbs()
    success, status, tbs_count, gtbs = btp.ccp_await_discovered()
    if status != 0:
        return False

    return True
    # This is done automatically by Zephyr during service discovery.


def hdl_wid_20107(params: WIDParams):
    """
    Please send Read Request to read Call State characteristic with handle = 0x00ED.
    """
    stack = get_stack()
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    ev = None

    if "0x0112" in params.description or "0x00D2" in params.description:
        inst_index = (0x00 if "0x00D2" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_bearer_name(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x0115" in params.description or "0x00D5" in params.description:
        inst_index = (0x00 if "0x00D5" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_bearer_uci(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x0117" in params.description or "0x00D7" in params.description:
        inst_index = (0x00 if "0x00D7" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_bearer_tech(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_value_ev(addr_type, addr, 30)
    elif "0x011A" in params.description or "0x00DA" in params.description:
        inst_index = (0x00 if "0x00DA" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_uri_list(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x011D" in params.description or "0x00DD" in params.description:
        inst_index = (0x00 if "0x00DD" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_signal_strength(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_value_ev(addr_type, addr, 30)
    elif "0x0120" in params.description or "0x00E0" in params.description:
        inst_index = (0x00 if "0x00E0" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_signal_interval(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_value_ev(addr_type, addr, 30)
    elif "0x0122" in params.description or "0x00E2" in params.description:
        inst_index = (0x00 if "0x00E2" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_current_calls(inst_index, addr_type, addr)
        ev = stack.ccp.wait_current_ev(addr_type, addr, 30)
    elif "0x0125" in params.description or "0x00E5" in params.description:
        # CCID is read by a client during service discovery. This is needed for
        # sending characteristic handles BTP event.
        # Testcase CCP/CL/CGGIT/CHA/BV-24-C ends in hdl_wid_20103
        return True
    elif "0x0127" in params.description or "0x00E7" in params.description:
        inst_index = (0x00 if "0x00E7" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_call_uri(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x012A" in params.description or "0x00EA" in params.description:
        inst_index = (0x00 if "0x00EA" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_status_flags(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_value_ev(addr_type, addr, 30)
    elif "0x013C" in params.description or "0x00FC" in params.description:
        inst_index = (0x00 if "0x00FC" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_optional_opcodes(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_value_ev(addr_type, addr, 30)
    elif "0x0136" in params.description or "0x00F6" in params.description:
        inst_index = (0x00 if "0x00F6" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_remote_uri(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x0139" in params.description or "0x00F9" in params.description:
        inst_index = (0x00 if "0x00F9" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_friendly_name(inst_index, addr_type, addr)
        ev = stack.ccp.wait_characteristic_str_ev(addr_type, addr, 30)
    elif "0x012D" in params.description or "0x00ED" in params.description:
        inst_index = (0x00 if "0x00ED" in params.description else BT_TBS_GTBS_INDEX)
        btp.ccp_read_call_state(inst_index)
        success, status, index, call_count, states = btp.ccp_await_call_state()
        return success and (status == 0)

    if ev is None:
        logging.error("Invalid or missing handle for Call State characteristic to Read Request.")
        return False

    return True


def hdl_wid_20116(_: WIDParams):
    """
    Please send command to the PTS to discover all mandatory characteristics of the
    Generic Telephone Bearer supported by the IUT. Discover primary service if needed.
    """
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()
    stack = get_stack()

    btp.ccp_discover_tbs()

    success, status, tbs_count, gtbs = btp.ccp_await_discovered()
    ev = stack.ccp.wait_chrc_handles_ev(addr_type, addr, 10, remove=True)
    if status != 0 and ev is None:
        return False

    return True


def hdl_wid_20121(params: WIDParams):
    """Please write value with write command (without response) to handle 0x00F3
     with following value. Any attribute value"""
    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    if params.test_case_name == "CCP/CL/CGGIT/CHA/BV-06-C":
        # TBS testcase
        inst_index = 0x00
    else:
        inst_index = BT_TBS_GTBS_INDEX

    btp.ccp_set_signal_interval(inst_index, 254, addr_type, addr)

    # TODO: find a way to confirm that operation was successful. Currently there
    #   is no proper callback in Zephyr.

    return True


def hdl_wid_20144(params: WIDParams):
    """Please click Yes if IUT support Write Command(without response), otherwise click No."""

    return True


def hdl_wid_20145(params: WIDParams):
    """Please click Yes if IUT support Write Request, otherwise click No."""

    return False


def hdl_wid_20206(params: WIDParams):
    """
    Please verify that for each supported characteristic, attribute handle/UUID pair(s)
    is returned to the upper tester.
    """
    stack = get_stack()

    if len(stack.ccp.events[defs.BTP_CCP_EV_CHRC_HANDLES]) > 0:
        chars = stack.ccp.events[defs.BTP_CCP_EV_CHRC_HANDLES][0]
        chrc_list = [f'{chrc:04X}' for chrc in chars]

        pattern = re.compile(r"0x([0-9a-fA-F]+)")
        desc_params = pattern.findall(params.description)
        if not desc_params:
            logging.error("parsing error")
            return False

        desc_params_list = desc_params[2::4]

        if desc_params_list == chrc_list:
            return True

    logging.debug('No attribute handle/UUID pair for supported characteristic to verify.')
    return False


hdl_wid_20106.count = 0
