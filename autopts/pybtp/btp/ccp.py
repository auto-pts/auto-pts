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

"""Wrapper around btp messages. The functions are added as needed."""
import binascii
import logging
import struct
from enum import IntEnum, IntFlag
from threading import Timer, Event
from time import sleep

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import addr2btp_ba


CCP = {
    'read_supported_cmds': ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_READ_SUPPORTED_COMMANDS,
                             CONTROLLER_INDEX),
    'discover_tbs':        ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_DISCOVER_TBS,
                             CONTROLLER_INDEX),
    'accept_call':         ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_ACCEPT_CALL,
                             CONTROLLER_INDEX),
    'terminate_call':      ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_TERMINATE_CALL,
                             CONTROLLER_INDEX),
    'originate_call':      ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_ORIGINATE_CALL,
                             CONTROLLER_INDEX),
    'read_call_state':     ( defs.BTP_SERVICE_ID_CCP,
                             defs.CCP_READ_CALL_STATE,
                             CONTROLLER_INDEX)
}

class CallState(IntEnum):
    INCOMING            = 0x00
    DIALING             = 0x01
    ALERTING            = 0x02
    ACTIVE              = 0x03
    LOCALLY_HELD        = 0x04
    REMOTELY_HELD       = 0x05
    LOCALLY_AND_REMOTELY_HELD = 0x06

    def __str__(self):
        return f'{self.name}'

class CallFlags(IntFlag):
    INCOMING            = 0x00
    OUTGOING            = 0x01
    WITHHELD            = 0x02
    WITHHELD_BY_NETWORK = 0x04

    def __str__(self):
        return f'{self.name}'


def ccp_command_rsp_succ(timeout=20.0):
    logging.debug("%s", ccp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CCP)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def ccp_discover_tbs(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_discover_tbs.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['discover_tbs'], data)

    ccp_command_rsp_succ()


def ccp_accept_call(index, call_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_accept_call.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<BB', index, call_id)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['accept_call'], data=data)

    ccp_command_rsp_succ()


def ccp_terminate_call(index, call_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_terminate_call.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<BB', index, call_id)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['terminate_call'], data=data)

    ccp_command_rsp_succ()


def ccp_originate_call(index, uri, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_originate_call.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    uri += '\0'
    size = len(uri.encode())
    data += struct.pack('<BB' + str(size) + 's', index, size, uri.encode())

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['originate_call'], data=data)

    ccp_command_rsp_succ()


def ccp_read_call_state(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_call_state.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_call_state'], data=data)

    ccp_command_rsp_succ()


def ccp_timeout(flag):
    flag.clear()


def ccp_await_event(ccp, event, timeout):
    flag = Event()
    flag.set()

    initial = ccp.events[event]['count']
    timer = Timer(timeout/1000.0, ccp_timeout, [flag])
    timer.start()

    while flag.is_set():
        if ccp.events[event]['count'] > initial:
                timer.cancel()
                flag.clear()
        else:
            sleep(0.25)

    return ccp.events[event]['count'] > initial


def ccp_await_discovered(timeout=6000):
    logging.debug(f"{ccp_await_discovered.__name__}")

    stack = get_stack()
    success = ccp_await_event(stack.ccp, defs.CCP_EV_DISCOVERED, timeout)

    return success, \
           stack.ccp.events[defs.CCP_EV_DISCOVERED]['status'], \
           stack.ccp.events[defs.CCP_EV_DISCOVERED]['tbs_count'], \
           stack.ccp.events[defs.CCP_EV_DISCOVERED]['gtbs']


def ccp_ev_discovered(ccp, data, data_len):
    status, tbs_count, gtbs_found = struct.unpack('<IB?', data)
    logging.debug(f"{ccp_ev_discovered.__name__} status: %u tbs count: %u gbts: %s" % (status, tbs_count, gtbs_found))

    event_dict = {
        'count': 0,
        'status': status,
        'tbs_count': tbs_count,
        'gtbs': gtbs_found
    }
    ccp.event_received(defs.CCP_EV_DISCOVERED, event_dict)


def ccp_await_call_state(timeout=1000):
    logging.debug(f"{ccp_await_call_state.__name__}")

    stack = get_stack()
    success = ccp_await_event(stack.ccp, defs.CCP_EV_CALL_STATES, timeout)

    return success, \
           stack.ccp.events[defs.CCP_EV_CALL_STATES]['status'], \
           stack.ccp.events[defs.CCP_EV_CALL_STATES]['index'], \
           stack.ccp.events[defs.CCP_EV_CALL_STATES]['call_count'], \
           stack.ccp.events[defs.CCP_EV_CALL_STATES]['states']


def ccp_fmt_flags(flags):
    result = str(CallFlags(flags))
    if flags and not flags & CallFlags.OUTGOING:
        result = '|' + result if result else result
        result = 'INCOMING' + result
    if not flags & CallFlags.WITHHELD_BY_NETWORK:
        result = result + '|' if result else result
        result = result + 'PROVIDED_BY_NETWORK'
    return result


def ccp_ev_call_states(ccp, data, data_len):
    status, index, call_count = struct.unpack('<IBB', data[:6])

    event_dict = {
        'count': 0,
        'status': status,
        'index': index,
        'call_count': call_count,
        'states': []
    }

    states_fmt = '{'
    for n in range(call_count):
        index, state, flags = struct.unpack('<BBB', data[6+3*n:9+3*n])
        states = {
            'index': index,
            'state': state,
            'flags': flags
        }
        event_dict['states'].append(states)

        states_fmt = states_fmt + ',' if len(states_fmt) > 1 else states_fmt
        states_fmt += ' index:%u %s flags:%s' % (index, CallState(state), ccp_fmt_flags(flags))
    states_fmt += ' }'

    logging.debug(f"{ccp_ev_call_states.__name__} status: %u index: 0x%02x calls: %u %s" % \
                  (status, index, call_count, states_fmt))

    ccp.event_received(defs.CCP_EV_CALL_STATES, event_dict)


CCP_EV = {
    defs.CCP_EV_DISCOVERED: ccp_ev_discovered,
    defs.CCP_EV_CALL_STATES: ccp_ev_call_states
}
