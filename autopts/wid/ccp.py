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

import binascii
import logging
import sys
import re
import struct

from enum import IntEnum, IntFlag
from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug

class OpCode(IntEnum):
    ACCEPT                  = 0x00
    TERMINATE               = 0x01
    LOCAL_HOLD              = 0x02
    LOCAL_RETRIEVE          = 0x03
    ORIGINATE               = 0x04
    JOIN                    = 0x05
    ILLEGAL                 = 0x06

class ResultCode(IntEnum):
    SUCCESS                 = 0x00
    OPCODE_NOT_SUPPORTED    = 0x01
    OPERATION_NOT_POSSIBLE  = 0x02
    INVALID_CALL_INDEX      = 0x03
    STATE_MISMATCH          = 0x04
    LACK_OF_RESOURCES       = 0x05
    INVALID_OUTGOING_URI    = 0x06

class CallState(IntEnum):
    INCOMING                = 0x00
    DIALING                 = 0x01
    ALERTING                = 0x02
    ACTIVE                  = 0x03
    LOCALLY_HELD            = 0x04
    REMOTELY_HELD           = 0x05
    LOCALLY_REMOTELY_HELD   = 0x06

class CallFlags(IntFlag):
    INCOMING                = 0x00
    OUTGOING                = 0x01
    WITHHELD                = 0x02
    WITHHELD_BY_NETWORK     = 0x04

class Uuid(IntEnum):
    TBS                     = 0x184b # Telephone Bearer service
    GTBS                    = 0x184c # Generic Telephone Bearer service
    CCC                     = 0x2902 # Client Characteristic Configuration 
    CALLSC                  = 0x2bbd # Call State Characteristic
    CALLCPC                 = 0x2bbe # Call Control Point Characteristic

BT_TBS_GTBS_INDEX = 0xff

global __gtbs_ccpc_handle, __round

__gtbs_ccpc_handle, __round = None, None

def ccp_wid_hdl(wid, description, test_case_name):
    log(f'{ccp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin

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
                                    start_hdl, start_hdl+1)

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
        print("Service: %s handles [%d, %d]" % (service.uuid, service.handle, service.end_handle))
        for char in attrs[service]:
            print("\tCharacteristic: %s handles [%d, %d]" % (char.uuid, char.handle, char.value_handle))
            for desc in attrs[service][char]:
                print("\t\tDescriptor: %s handle %d" % (desc.uuid, desc.handle))
    

def hdl_wid_104(_: WIDParams):
    """
        Please Write(WRITE_REQ) Call Control Point Op Code:(0x00) and Call ID(1)
        Description: Accept the incoming call with Call_Index 1
        ........................................................................
        Please Write(WRITE_REQ) Call Control Point Op Code:(0x01) and Call ID(1)
        Description: Terminate the call with Call_Index 1
    """
    result = re.search(r'Op Code:\((0x[0-9A-F]{2})\) and Call ID\((\d)\)', _.description)
    if result:
        opCode, callID = int(result.group(1), 16), int(result.group(2))
        if opCode == 0:
            btp.ccp_accept_call(BT_TBS_GTBS_INDEX, callID)
        elif opCode == 1:
            btp.ccp_terminate_call(BT_TBS_GTBS_INDEX, callID)
        return opCode in [0,1]
    return False


def hdl_wid_114(_: WIDParams):
    """
        Please send Write(WRITE_REQ) or Write Without Response to Call Control Point with any Op Code and Call ID with any value'
        It is not possible to sent an invalid Op Code with the current tbs_client API.  This must be done manually.
    """
    global __gtbs_ccpc_handle, __round

    __round = 1 if not __round else __round + 1

    if __round == 1:
        data = binascii.hexlify(struct.pack('<BB', OpCode.ILLEGAL, 1)).decode()
        btp.gattc_write_without_rsp(btp.pts_addr_type_get(), btp.pts_addr_get(), __gtbs_ccpc_handle, data)
    elif __round == 2:
        btp.ccp_terminate_call(BT_TBS_GTBS_INDEX, 5)
    elif __round == 3:
        btp.ccp_terminate_call(BT_TBS_GTBS_INDEX, 6)
    else:
        btp.ccp_originate_call(BT_TBS_GTBS_INDEX, 'skype:killroy')

    if __round > 1:
        stack = get_stack()
        stack.gatt.wait_notification_ev(0.5)
        if stack.gatt.notification_events:
            handle, data = stack.gatt.notification_events[-1][-2:]
            opcode, index, reason = struct.unpack('<BBB', data)
            return (__round, opcode, reason) == (2, OpCode.TERMINATE, ResultCode.OPCODE_NOT_SUPPORTED) or \
                   (__round, opcode, reason) == (3, OpCode.TERMINATE, ResultCode.INVALID_CALL_INDEX) or \
                   (__round, opcode, reason) == (4, OpCode.ORIGINATE, ResultCode.STATE_MISMATCH) or \
                   (__round, opcode, reason) == (5, OpCode.ORIGINATE, ResultCode.LACK_OF_RESOURCES)
        return False
    
    return True


def hdl_wid_115(_: WIDParams):
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
    btp.ccp_discover_tbs()
    success, status, tbs_count, gtbs = btp.ccp_await_discovered()
    return success and (status == 0) and gtbs


def hdl_wid_20106(_: WIDParams):
    global __gtbs_ccpc_handle
    """
        Please write to Client Characteristic Configuration Descriptor of Call Control Point characteristic to enable notification.
        Not possible to do with the current tbs_client API. Only way it to discover all characteristics and enable all notifications.
        NOTE: PTS does not accept the discover and enable notifications that occur in parallel.
              It gets confused and call this function three or more times before it gives up.
              This is the reason behind the manual enabling of notifications for the Call Control Point and the counter.
    """
    if not hdl_wid_20106.count:
        hdl_wid_20106.count += 1
        btp.ccp_discover_tbs()
        success, status, tbs_count, gtbs = btp.ccp_await_discovered()
        if (success, status, tbs_count, gtbs) == (True, 0, 0, True):
            attrs = disc_full("%04X" % Uuid.GTBS, "%04X" % Uuid.CALLCPC)
            __gtbs_ccpc_handle = characteristic_handle(attrs, Uuid.GTBS, Uuid.CALLCPC)
            handle = descriptor_handle(attrs, Uuid.GTBS, Uuid.CALLCPC, Uuid.CCC)
            btp.gattc_cfg_notify(btp.pts_addr_type_get(), btp.pts_addr_get(), 1, handle)
            return True
        return False
    return True

def hdl_wid_20107(_: WIDParams):
    """
        Please send Read Request to read Call State characteristic with handle = 0x00ED.
    """
    btp.ccp_read_call_state(BT_TBS_GTBS_INDEX)
    success, status, index, call_count, states = btp.ccp_await_call_state()
    return success and (status == 0)


def hdl_wid_20116(_: WIDParams):
    """
        Please send command to the PTS to discover all mandatory characteristics of the Generic Telephone Bearer supported by the IUT. 
        Discover primary service if needed.
    """
    btp.ccp_discover_tbs()
    success, status, tbs_count, gtbs = btp.ccp_await_discovered()
    return success and (status == 0) and gtbs


def hdl_wid_20206(_: WIDParams):
    """
        Please verify that for each supported characteristic, attribute handle/UUID pair(s) is returned to the upper tester.
        There is currently NO WAY to do that with the current API. If discovery was successfull, we must assume that we got
        all characteristics.
    """
    return True

hdl_wid_20106.count = 0
