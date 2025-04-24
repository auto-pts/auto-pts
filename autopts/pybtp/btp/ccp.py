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
from threading import Event, Timer
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr2btp_ba

CCP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_SUPPORTED_COMMANDS,
                             CONTROLLER_INDEX),
    'discover_tbs':        (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_DISCOVER_TBS,
                             CONTROLLER_INDEX),
    'accept_call':         (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_ACCEPT_CALL,
                             CONTROLLER_INDEX),
    'terminate_call':      (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_TERMINATE_CALL,
                             CONTROLLER_INDEX),
    'originate_call':      (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_ORIGINATE_CALL,
                             CONTROLLER_INDEX),
    'read_call_state':     (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_CALL_STATE,
                             CONTROLLER_INDEX),
    'read_bearer_name':    (defs.BTP_SERVICE_ID_CCP,
                            defs.BTP_CCP_CMD_READ_BEARER_NAME,
                            CONTROLLER_INDEX),
    'read_bearer_uci':     (defs.BTP_SERVICE_ID_CCP,
                            defs.BTP_CCP_CMD_READ_BEARER_UCI,
                            CONTROLLER_INDEX),
    'read_bearer_tech':    (defs.BTP_SERVICE_ID_CCP,
                            defs.BTP_CCP_CMD_READ_BEARER_TECH,
                            CONTROLLER_INDEX),
    'read_uri_list':       (defs.BTP_SERVICE_ID_CCP,
                            defs.BTP_CCP_CMD_READ_URI_LIST,
                            CONTROLLER_INDEX),
    'read_signal_strength': (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_SIGNAL_STRENGTH,
                             CONTROLLER_INDEX),
    'read_signal_interval': (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_SIGNAL_INTERVAL,
                             CONTROLLER_INDEX),
    'read_current_calls':   (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_CURRENT_CALLS,
                             CONTROLLER_INDEX),
    'read_ccid':            (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_CCID,
                             CONTROLLER_INDEX),
    'read_call_uri':        (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_CALL_URI,
                             CONTROLLER_INDEX),
    'read_status_flags':    (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_STATUS_FLAGS,
                             CONTROLLER_INDEX),
    'read_optional_opcodes': (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_OPTIONAL_OPCODES,
                             CONTROLLER_INDEX),
    'read_friendly_name':   (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_FRIENDLY_NAME,
                             CONTROLLER_INDEX),
    'read_remote_uri':      (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_READ_REMOTE_URI,
                             CONTROLLER_INDEX),
    'set_signal_interval':  (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_SET_SIGNAL_INTERVAL,
                             CONTROLLER_INDEX),
    'hold_call':            (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_HOLD_CALL,
                             CONTROLLER_INDEX),
    'retrieve_call':        (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_RETRIEVE_CALL,
                             CONTROLLER_INDEX),
    'join_calls':           (defs.BTP_SERVICE_ID_CCP,
                             defs.BTP_CCP_CMD_JOIN_CALLS,
                             CONTROLLER_INDEX),
}


class CallState(IntEnum):
    INCOMING = 0x00
    DIALING = 0x01
    ALERTING = 0x02
    ACTIVE = 0x03
    LOCALLY_HELD = 0x04
    REMOTELY_HELD = 0x05
    LOCALLY_AND_REMOTELY_HELD = 0x06

    def __str__(self):
        return f'{self.name}'


class CallFlags(IntFlag):
    INCOMING = 0x00
    OUTGOING = 0x01
    WITHHELD = 0x02
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


def ccp_read_bearer_name(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_bearer_name.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_bearer_name'], data=data)

    ccp_command_rsp_succ()


def ccp_read_bearer_uci(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_bearer_uci.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_bearer_uci'], data=data)

    ccp_command_rsp_succ()


def ccp_read_bearer_tech(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_bearer_tech.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_bearer_tech'], data=data)

    ccp_command_rsp_succ()


def ccp_read_uri_list(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_uri_list.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_uri_list'], data=data)

    ccp_command_rsp_succ()


def ccp_read_signal_strength(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_signal_strength.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_signal_strength'], data=data)

    ccp_command_rsp_succ()


def ccp_read_signal_interval(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_signal_interval.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_signal_interval'], data=data)

    ccp_command_rsp_succ()


def ccp_read_current_calls(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_current_calls.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_current_calls'], data=data)

    ccp_command_rsp_succ()


def ccp_read_ccid(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_ccid.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_ccid'], data=data)

    ccp_command_rsp_succ()


def ccp_read_call_uri(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_call_uri.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_call_uri'], data=data)

    ccp_command_rsp_succ()


def ccp_read_status_flags(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_status_flags.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_status_flags'], data=data)

    ccp_command_rsp_succ()


def ccp_read_optional_opcodes(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_optional_opcodes.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_optional_opcodes'], data=data)

    ccp_command_rsp_succ()


def ccp_read_friendly_name(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_friendly_name.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_friendly_name'], data=data)

    ccp_command_rsp_succ()


def ccp_read_remote_uri(index, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_read_remote_uri.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<B', index)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['read_remote_uri'], data=data)

    ccp_command_rsp_succ()


def ccp_set_signal_interval(index, interval, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_set_signal_interval.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<BB', index, interval)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['set_signal_interval'], data=data)

    ccp_command_rsp_succ()


def ccp_hold_call(index, call_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_hold_call.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<BB', index, call_id)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['hold_call'], data=data)

    ccp_command_rsp_succ()


def ccp_retrieve_call(index, call_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_retrieve_call.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('<BB', index, call_id)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['retrieve_call'], data=data)

    ccp_command_rsp_succ()


def ccp_join_calls(index, count, call_index: [], bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ccp_join_calls.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack('<B', index))
    data.extend(struct.pack('<B', count))
    if count > 1:
        for i in range(count):
            data.extend(struct.pack('<B', int(call_index[i])))
    else:
        data.extend(struct.pack('<B', int(call_index[0])))

    iutctl = get_iut()
    iutctl.btp_socket.send(*CCP['join_calls'], data=data)

    ccp_command_rsp_succ()


def ccp_timeout(flag):
    flag.clear()


def ccp_await_event(ccp, event, timeout):
    flag = Event()
    flag.set()

    initial = ccp.events[event]['count']
    timer = Timer(timeout / 1000.0, ccp_timeout, [flag])
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
    success = ccp_await_event(stack.ccp, defs.BTP_CCP_EV_DISCOVERED, timeout)

    return success, \
           stack.ccp.events[defs.BTP_CCP_EV_DISCOVERED]['status'], \
           stack.ccp.events[defs.BTP_CCP_EV_DISCOVERED]['tbs_count'], \
           stack.ccp.events[defs.BTP_CCP_EV_DISCOVERED]['gtbs']


def ccp_ev_discovered(ccp, data, data_len):
    status, tbs_count, gtbs_found = struct.unpack('<IB?', data)
    logging.debug(f"{ccp_ev_discovered.__name__} status: %u tbs count: %u gbts: %s" % (status, tbs_count, gtbs_found))

    event_dict = {
        'count': 0,
        'status': status,
        'tbs_count': tbs_count,
        'gtbs': gtbs_found
    }
    ccp.event_received(defs.BTP_CCP_EV_DISCOVERED, event_dict)


def ccp_ev_chrc_handles(ccp, data, data_len):
    logging.debug('%s %r', ccp_ev_chrc_handles.__name__, data)

    fmt = '<HHHHHHHHHHHHHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    provider_name, bearer_uci, bearer_technology, uri_list, signal_strength, signal_interval,\
        current_calls, ccid, status_flags, bearer_uri, call_state, control_point,\
        optional_opcodes, termination_reasons, incoming_call,\
        friendly_name = struct.unpack_from(fmt, data)

    logging.debug(f'CCP Characteristics Handles: Bearer Provider Name {provider_name},'
                  f' Bearer UCI Handle {bearer_uci}, Bearer Technology {bearer_technology}, '
                  f'URI List Handle {uri_list}, Signal Strength {signal_strength},'
                  f' Signal Interval Handle {signal_interval}, Current Calls {current_calls},'
                  f'CCID Handle {ccid}, Status Flags {status_flags}, Bearer URI {bearer_uri}, '
                  f'Call State {call_state}, Call Control Point {control_point}, '
                  f'Optional Opcodes Handle {optional_opcodes},'
                  f'Termination Reasons {termination_reasons}, Incoming Call {incoming_call},'
                  f'Friendly Name {friendly_name}')

    ccp.event_received_2(defs.BTP_CCP_EV_CHRC_HANDLES, (provider_name, bearer_uci, bearer_technology,
                                                    uri_list, signal_strength, signal_interval,
                                                    current_calls, ccid, status_flags, bearer_uri,
                                                    call_state, control_point, optional_opcodes,
                                                    termination_reasons, incoming_call,
                                                    friendly_name))


def ccp_ev_chrc_val(ccp, data, data_len):
    logging.debug('%s %r', ccp_ev_chrc_val.__name__, data)

    fmt = '<B6sbBB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, inst_index, value = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'CCP Characteristic Read: addr {addr} addr_type '
                  f'{addr_type}, status {status}, Instance index {inst_index},'
                  f' Value {value}')

    ccp.event_received_2(defs.BTP_CCP_EV_CHRC_VAL, (addr_type, addr, status, inst_index,
                                                value))


def ccp_ev_chrc_str(ccp, data, data_len):
    logging.debug('%s %r', ccp_ev_chrc_str.__name__, data)

    fmt = '<B6sbBB'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, status, inst_index, data_len = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    str_data = struct.unpack_from(f'<{data_len}s', data, offset=fmt_size)[0].decode('utf-8')

    logging.debug(f'CCP Characteristic String data: addr {addr} addr_type '
                  f'{addr_type}, status {status}, String Data: {str_data}')

    ccp.event_received_2(defs.BTP_CCP_EV_CHRC_STR, (addr_type, addr, status, inst_index, str_data))


def ccp_ev_cp(ccp, data, data_len):
    logging.debug('%s %r', ccp_ev_cp.__name__, data)

    fmt = '<B6sb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'CCP Control Point event: addr {addr} addr_type '
                  f'{addr_type}, status {status}')

    ccp.event_received_2(defs.BTP_CCP_EV_CP, (addr_type, addr, status))


def ccp_ev_current_calls(ccp, data, data_len):
    logging.debug('%s %r', ccp_ev_current_calls.__name__, data)

    fmt = '<B6sb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'CCP Current Calls event: addr {addr} addr_type '
                  f'{addr_type}, status {status}')

    ccp.event_received_2(defs.BTP_CCP_EV_CURRENT_CALLS, (addr_type, addr, status))


def ccp_await_call_state(timeout=1000):
    logging.debug(f"{ccp_await_call_state.__name__}")

    stack = get_stack()
    success = ccp_await_event(stack.ccp, defs.BTP_CCP_EV_CALL_STATES, timeout)

    return success, \
           stack.ccp.events[defs.BTP_CCP_EV_CALL_STATES]['status'], \
           stack.ccp.events[defs.BTP_CCP_EV_CALL_STATES]['index'], \
           stack.ccp.events[defs.BTP_CCP_EV_CALL_STATES]['call_count'], \
           stack.ccp.events[defs.BTP_CCP_EV_CALL_STATES]['states']


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
        index, state, flags = struct.unpack('<BBB', data[6 + 3 * n:9 + 3 * n])
        states = {
            'index': index,
            'state': state,
            'flags': flags
        }
        event_dict['states'].append(states)

        states_fmt = states_fmt + ',' if len(states_fmt) > 1 else states_fmt
        states_fmt += f" index:{index} {CallState(state)} flags:{ccp_fmt_flags(flags)}"
        states_fmt += " }"

    logging.debug(
        f"{ccp_ev_call_states.__name__} status: {status} index: 0x{index:02x} calls: {call_count} {states_fmt}"
    )

    ccp.event_received(defs.BTP_CCP_EV_CALL_STATES, event_dict)


CCP_EV = {
    defs.BTP_CCP_EV_DISCOVERED: ccp_ev_discovered,
    defs.BTP_CCP_EV_CALL_STATES: ccp_ev_call_states,
    defs.BTP_CCP_EV_CHRC_HANDLES: ccp_ev_chrc_handles,
    defs.BTP_CCP_EV_CHRC_VAL: ccp_ev_chrc_val,
    defs.BTP_CCP_EV_CHRC_STR: ccp_ev_chrc_str,
    defs.BTP_CCP_EV_CP: ccp_ev_cp,
    defs.BTP_CCP_EV_CURRENT_CALLS: ccp_ev_current_calls,
}
