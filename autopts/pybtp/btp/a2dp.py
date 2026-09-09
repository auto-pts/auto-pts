#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""Wrapper around BTP A2DP messages."""

import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import addr_str_to_le_bytes

log = logging.debug

A2DP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_A2DP,
                            defs.BTP_A2DP_CMD_READ_SUPPORTED_COMMANDS,
                            defs.BTP_INDEX_NONE, ""),
    'connect': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_CONNECT,
                CONTROLLER_INDEX),
    'disconnect': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_DISCONNECT,
                   CONTROLLER_INDEX),
    'start_stream': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_START_STREAM,
                     CONTROLLER_INDEX),
    'stop_stream': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_STOP_STREAM,
                    CONTROLLER_INDEX),
    'set_role': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_SET_ROLE,
                 defs.BTP_INDEX_NONE),
    'operation_rsp': (defs.BTP_SERVICE_ID_A2DP,
                      defs.BTP_A2DP_CMD_OPERATION_RSP, CONTROLLER_INDEX),
    'send_delay_report': (defs.BTP_SERVICE_ID_A2DP,
                          defs.BTP_A2DP_CMD_SEND_DELAY_REPORT,
                          CONTROLLER_INDEX),
    'get_capability': (defs.BTP_SERVICE_ID_A2DP,
                       defs.BTP_A2DP_CMD_GET_CAPABILITY, defs.BTP_INDEX_NONE),
}


def a2dp_connect(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r", a2dp_connect.__name__, bd_addr)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP['connect'], data=data_ba)


def a2dp_disconnect(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r", a2dp_disconnect.__name__, bd_addr)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP['disconnect'], data=data_ba)


def a2dp_start_stream(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r", a2dp_start_stream.__name__, bd_addr)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP['start_stream'], data=data_ba)


def a2dp_stop_stream(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r", a2dp_stop_stream.__name__, bd_addr)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP['stop_stream'], data=data_ba)


def a2dp_set_role(role):
    """Set the A2DP role the IUT plays (0 = sink, 1 = source)."""
    logging.debug("%s %r", a2dp_set_role.__name__, role)
    iutctl = get_iut()

    data_ba = bytearray(struct.pack('B', role))
    iutctl.btp_socket.send_wait_rsp(*A2DP['set_role'], data=data_ba)


def a2dp_send_delay_report(delay, bd_addr=None, bd_addr_type=None):
    """Send an AVDTP DELAYREPORT with 'delay' in 1/10 ms.

    Not every IUT can emit one on demand; check a2dp_supports() first, since a
    stack that declares delay reporting as an endpoint capability and negotiates
    it itself has no way to send one at a chosen moment.
    """
    logging.debug("%s delay=%d", a2dp_send_delay_report.__name__, delay)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack('B', pts_addr_type_get(bd_addr_type)))
    data_ba.extend(addr_str_to_le_bytes(pts_addr_get(bd_addr)))
    data_ba.extend(struct.pack('<H', delay))
    iutctl.btp_socket.send_wait_rsp(*A2DP['send_delay_report'], data=data_ba)


def a2dp_get_capability(capability, value=0):
    """Ask the IUT a yes/no question about itself, returning True or False.

    Used for the prompts PTS phrases as a question about the implementation. The
    IUT answers from its own behaviour, so the same handler is correct for any
    IUT rather than encoding one implementation's answer.
    """
    logging.debug("%s cap=0x%02x value=%d", a2dp_get_capability.__name__,
                  capability, value)

    iutctl = get_iut()

    data_ba = bytearray(struct.pack('<BH', capability, value))
    iutctl.btp_socket.send_wait_rsp(*A2DP['get_capability'], data=data_ba)

    tuple_data = iutctl.btp_socket.read()[1]
    data = tuple_data[0] if isinstance(tuple_data, tuple) else tuple_data

    return bool(data and data[0])


def a2dp_supports(opcode):
    """Whether the IUT advertises a given A2DP BTP command.

    Read from the READ_SUPPORTED_COMMANDS bitmap that core_reg_svc_univ() already
    collects into stack.supported_cmds, so a handler can skip work the IUT cannot
    do instead of waiting to find out.

    Defaults to False when the bitmap is missing, which is the safe direction: a
    handler that skips an unsupported command costs nothing, while one that issues
    it fails visibly the first time.
    """
    from autopts.ptsprojects.stack import get_stack

    try:
        stack = get_stack()
        bitmap = (stack.supported_cmds or {}).get('A2DP')
    except Exception:
        # get_stack() raises rather than returning None when there is no IUT.
        return False

    if not bitmap:
        return False

    return bool(bitmap >> opcode & 1)


def a2dp_operation_rsp(signal_id, accept=True, error_code=0, bd_addr=None,
                       bd_addr_type=None):
    """Answer an AVDTP operation the IUT reported through
    BTP_A2DP_EV_OPERATION_REQ.

    Only meaningful in response to that event: an IUT which answers these
    operations itself never raises it, and answering an event that never arrived
    is rejected. Use A2DP.take_pending_operation() to decide whether to call
    this at all - that is the "if necessary" in the PTS prompts.

    'error_code' is an AVDTP Error Code and is only read when accept is False.
    """
    logging.debug("%s signal_id=0x%02x accept=%s error=0x%02x",
                  a2dp_operation_rsp.__name__, signal_id, accept, error_code)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack('B', pts_addr_type_get(bd_addr_type)))
    data_ba.extend(addr_str_to_le_bytes(pts_addr_get(bd_addr)))
    data_ba.extend(struct.pack('BBB', signal_id, 1 if accept else 0, error_code))
    iutctl.btp_socket.send_wait_rsp(*A2DP['operation_rsp'], data=data_ba)


# A2DP event handlers

def a2dp_connected_ev_(a2dp, data, data_len):
    """Handle A2DP connected event."""
    import logging
    logging.debug("%s", a2dp_connected_ev_.__name__)
    if a2dp:
        a2dp.connected = True
        if data_len >= 7:
            a2dp.addr = data[:7]


def a2dp_disconnected_ev_(a2dp, data, data_len):
    """Handle A2DP disconnected event."""
    import logging
    logging.debug("%s", a2dp_disconnected_ev_.__name__)
    if a2dp:
        a2dp.connected = False


# Every A2DP event starts with bt_addr_le_t, which is 7 bytes, so payload fields
# begin at offset 7. Reading data[0] picks up the address type instead - 0 for a
# public BR/EDR address, which passes for a valid value and reads as "not
# streaming" no matter what the IUT reported.
_EV_PAYLOAD_OFFSET = 7


def a2dp_audio_state_ev_(a2dp, data, data_len):
    """Handle A2DP audio state event."""
    import logging
    logging.debug("%s", a2dp_audio_state_ev_.__name__)
    if a2dp and data_len > _EV_PAYLOAD_OFFSET:
        a2dp.audio_streaming = (data[_EV_PAYLOAD_OFFSET] != 0)


def a2dp_operation_req_ev_(a2dp, data, data_len):
    """An AVDTP operation is waiting on a decision from the client.

    Only an IUT that defers these decisions to the application raises this;
    an IUT whose stack answers them internally never raises it. Queuing the
    signal id is what lets a WID handler tell "the IUT needs me to accept this"
    from "the IUT already did".
    """
    import logging
    logging.debug("%s", a2dp_operation_req_ev_.__name__)
    if a2dp and data_len > _EV_PAYLOAD_OFFSET:
        signal_id = data[_EV_PAYLOAD_OFFSET]
        logging.debug("a2dp operation req: signal_id=0x%02x", signal_id)
        a2dp.event_received(defs.BTP_A2DP_EV_OPERATION_REQ, (signal_id,))


A2DP_EV = {
    defs.BTP_A2DP_EV_CONNECTED: a2dp_connected_ev_,
    defs.BTP_A2DP_EV_DISCONNECTED: a2dp_disconnected_ev_,
    defs.BTP_A2DP_EV_AUDIO_STATE: a2dp_audio_state_ev_,
    defs.BTP_A2DP_EV_OPERATION_REQ: a2dp_operation_req_ev_,
}
