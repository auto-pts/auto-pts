#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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

"""Wrapper around btp messages for the OPP (Object Push Profile) service."""

import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX
from autopts.pybtp.btp.btp import get_iut_method as get_iut

log = logging.debug

OPP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_OPP,
                       defs.BTP_OPP_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "discover": (defs.BTP_SERVICE_ID_OPP,
                 defs.BTP_OPP_CMD_DISCOVER,
                 CONTROLLER_INDEX, ""),
    "client_transport_connect": (defs.BTP_SERVICE_ID_OPP,
                                 defs.BTP_OPP_CMD_CLIENT_TRANSPORT_CONNECT,
                                 CONTROLLER_INDEX),
    "client_transport_disconnect": (defs.BTP_SERVICE_ID_OPP,
                                    defs.BTP_OPP_CMD_CLIENT_TRANSPORT_DISCONNECT,
                                    CONTROLLER_INDEX, ""),
    "client_connect": (defs.BTP_SERVICE_ID_OPP,
                       defs.BTP_OPP_CMD_CLIENT_CONNECT,
                       CONTROLLER_INDEX),
    "client_disconnect": (defs.BTP_SERVICE_ID_OPP,
                          defs.BTP_OPP_CMD_CLIENT_DISCONNECT,
                          CONTROLLER_INDEX, ""),
    "client_push": (defs.BTP_SERVICE_ID_OPP,
                    defs.BTP_OPP_CMD_CLIENT_PUSH,
                    CONTROLLER_INDEX),
    "client_pull_bcard": (defs.BTP_SERVICE_ID_OPP,
                          defs.BTP_OPP_CMD_CLIENT_PULL_BCARD,
                          CONTROLLER_INDEX, ""),
    "client_abort": (defs.BTP_SERVICE_ID_OPP,
                     defs.BTP_OPP_CMD_CLIENT_ABORT,
                     CONTROLLER_INDEX, ""),
    "client_push_2mb": (defs.BTP_SERVICE_ID_OPP,
                        defs.BTP_OPP_CMD_CLIENT_PUSH_2MB,
                        CONTROLLER_INDEX, ""),
    "server_register": (defs.BTP_SERVICE_ID_OPP,
                        defs.BTP_OPP_CMD_SERVER_REGISTER,
                        CONTROLLER_INDEX, ""),
    "server_connect_rsp": (defs.BTP_SERVICE_ID_OPP,
                           defs.BTP_OPP_CMD_SERVER_CONNECT_RSP,
                           CONTROLLER_INDEX),
    "server_disconnect_rsp": (defs.BTP_SERVICE_ID_OPP,
                              defs.BTP_OPP_CMD_SERVER_DISCONNECT_RSP,
                              CONTROLLER_INDEX),
    "server_push_rsp": (defs.BTP_SERVICE_ID_OPP,
                        defs.BTP_OPP_CMD_SERVER_PUSH_RSP,
                        CONTROLLER_INDEX),
    "server_pull_bcard_rsp": (defs.BTP_SERVICE_ID_OPP,
                              defs.BTP_OPP_CMD_SERVER_PULL_BCARD_RSP,
                              CONTROLLER_INDEX),
    "server_abort_rsp": (defs.BTP_SERVICE_ID_OPP,
                         defs.BTP_OPP_CMD_SERVER_ABORT_RSP,
                         CONTROLLER_INDEX),
    "server_prepare_push_rsp": (defs.BTP_SERVICE_ID_OPP,
                                defs.BTP_OPP_CMD_SERVER_PREPARE_PUSH_RSP,
                                CONTROLLER_INDEX),
}


def opp_discover():
    """Discover the OPP server on the connected peer via SDP.

    The result is reported via BTP_OPP_EV_DISCOVERED. No parameters.
    """
    log("opp_discover")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['discover'])


def opp_client_transport_connect(channel: int):
    """Connect the OPP client RFCOMM transport.

    Args:
        channel: RFCOMM channel obtained from SDP discovery.
    """
    log("opp_client_transport_connect channel=%r", channel)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_transport_connect'],
                                    data=bytearray([channel]))


def opp_client_transport_disconnect():
    """Disconnect the OPP client RFCOMM transport. No parameters."""
    log("opp_client_transport_disconnect")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_transport_disconnect'])


def opp_client_connect(mopl: int = 0xFFFF):
    """Send an OBEX CONNECT request from the OPP client.

    Args:
        mopl: Maximum OBEX packet length proposed by the client.
    """
    log("opp_client_connect mopl=%r", mopl)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_connect'],
                                    data=bytearray(struct.pack('<H', mopl)))


def opp_client_disconnect():
    """Send an OBEX DISCONNECT request from the OPP client. No parameters."""
    log("opp_client_disconnect")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_disconnect'])


def opp_client_push(total_length: int = 0, is_final: int = 1,
                    name: bytes = b'', mime_type: bytes = b'',
                    body: bytes = b''):
    """Send an OBEX PUT (push object) request from the OPP client.

    For multi-packet transfers, call this function once per packet.
    Set is_final=1 only on the last packet (End-of-Body).

    Args:
        total_length: Total object length in bytes (carried in OBEX Length header).
        is_final: 1 if this is the final (End-of-Body) packet, 0 otherwise.
        name: Object name as bytes (UTF-16BE with null terminator).
        mime_type: MIME type string as bytes (e.g. b'text/x-vcard\\x00').
        body: Body data bytes for this packet.
    """
    log("opp_client_push total_length=%r is_final=%r name_len=%r type_len=%r body_len=%r",
        total_length, is_final, len(name), len(mime_type), len(body))

    iutctl = get_iut()
    data_ba = bytearray(struct.pack('<IBBBH', total_length, is_final,
                                    len(name), len(mime_type), len(body)))
    data_ba.extend(name)
    data_ba.extend(mime_type)
    data_ba.extend(body)
    iutctl.btp_socket.send_wait_rsp(*OPP['client_push'], data=data_ba)


def opp_client_pull_bcard():
    """Send an OBEX GET to pull the server's default business card. No parameters."""
    log("opp_client_pull_bcard")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_pull_bcard'])


def opp_client_abort():
    """Send an OBEX ABORT request from the OPP client. No parameters."""
    log("opp_client_abort")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_abort'])


def opp_client_push_2mb():
    """Autonomously push a 2 MB BMP file to the server in multiple OBEX PUT packets.

    The IUT sends each Body chunk as soon as the server replies CONTINUE (0x90),
    and sends the final End-of-Body chunk when the last byte is queued.
    The result is reported via BTP_OPP_EV_CLIENT_PUSH once the transfer
    finishes or an error occurs. No parameters.
    """
    log("opp_client_push_2mb")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['client_push_2mb'])


def opp_server_register():
    """Register an OPP Push Server listener.

    Registers the RFCOMM transport and SDP record. No parameters.
    """
    log("opp_server_register")
    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_register'])


def opp_server_connect_rsp(mopl: int = 0xFFFF,
                            rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS):
    """Send an OBEX CONNECT response from the OPP server.

    Args:
        mopl: Maximum OBEX packet length accepted by this server.
        rsp_code: Response code (defs.BTP_OPP_RSP_CODE_*).
    """
    log("opp_server_connect_rsp mopl=%r rsp=%r", mopl, rsp_code)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_connect_rsp'],
                                    data=bytearray(struct.pack('<HB', mopl, rsp_code)))


def opp_server_disconnect_rsp(rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS):
    """Send an OBEX DISCONNECT response from the OPP server.

    Args:
        rsp_code: Response code (defs.BTP_OPP_RSP_CODE_*).
    """
    log("opp_server_disconnect_rsp rsp=%r", rsp_code)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_disconnect_rsp'],
                                    data=bytearray([rsp_code]))


def opp_server_push_rsp(rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS):
    """Send an OBEX PUT response from the OPP server.

    Use BTP_OPP_RSP_CODE_CONTINUE to request the next body chunk, or
    BTP_OPP_RSP_CODE_SUCCESS when the full object has been received.

    Args:
        rsp_code: Response code (defs.BTP_OPP_RSP_CODE_*).
    """
    log("opp_server_push_rsp rsp=%r", rsp_code)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_push_rsp'],
                                    data=bytearray([rsp_code]))


def opp_server_pull_bcard_rsp(rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS,
                               is_final: int = 1, body: bytes = b''):
    """Send an OBEX GET response (business card pull) from the OPP server.

    Args:
        rsp_code: Response code (defs.BTP_OPP_RSP_CODE_*).
        is_final: 1 if this is the final (End-of-Body) chunk, 0 otherwise.
        body: Body data bytes for this chunk.
    """
    log("opp_server_pull_bcard_rsp rsp=%r is_final=%r body_len=%r",
        rsp_code, is_final, len(body))

    iutctl = get_iut()
    data_ba = bytearray(struct.pack('<BBH', rsp_code, is_final, len(body)))
    data_ba.extend(body)
    iutctl.btp_socket.send_wait_rsp(*OPP['server_pull_bcard_rsp'], data=data_ba)


def opp_server_abort_rsp(rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS):
    """Send an OBEX ABORT response from the OPP server.

    Args:
        rsp_code: Response code (defs.BTP_OPP_RSP_CODE_*).
    """
    log("opp_server_abort_rsp rsp=%r", rsp_code)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_abort_rsp'],
                                    data=bytearray([rsp_code]))


def opp_server_prepare_push_rsp(rsp_code: int = defs.BTP_OPP_RSP_CODE_SUCCESS):
    """Pre-configure the response code for the next incoming OBEX PUT request.

    Once the matching push packet is received the stored code is cleared
    and the default auto-reply resumes.

    Args:
        rsp_code: Response code for the incoming PUT (defs.BTP_OPP_RSP_CODE_*).
    """
    log("opp_server_prepare_push_rsp rsp=%r", rsp_code)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*OPP['server_prepare_push_rsp'],
                                    data=bytearray([rsp_code]))


def opp_wait_for_discovered(timeout: int = 30):
    """Wait until the OPP discovered (SDP) event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        OppDiscoveredResult, or None on timeout.
    """
    stack = get_stack()
    return stack.opp.wait_for_discovered(timeout)


def opp_wait_for_client_transport_connected(timeout: int = 30):
    """Wait until the OPP client transport connected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_transport_connected(timeout)


def opp_wait_for_client_transport_disconnected(timeout: int = 30):
    """Wait until the OPP client transport disconnected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_transport_disconnected(timeout)


def opp_wait_for_client_connected(timeout: int = 30):
    """Wait until the OPP client OBEX session connected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_connected(timeout)


def opp_wait_for_client_disconnected(timeout: int = 30):
    """Wait until the OPP client OBEX session disconnected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_disconnected(timeout)


def opp_wait_for_client_push(timeout: int = 30):
    """Wait until the OPP client push (PUT) response event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        OBEX response code int, or None on timeout.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_push(timeout)


def opp_wait_for_client_pull_bcard(timeout: int = 30):
    """Wait until the OPP client pull business card (GET) response event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        Tuple (rsp_code, body), or None on timeout.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_pull_bcard(timeout)


def opp_wait_for_client_abort(timeout: int = 30):
    """Wait until the OPP client abort response event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        OBEX response code int, or None on timeout.
    """
    stack = get_stack()
    return stack.opp.wait_for_client_abort(timeout)


def opp_wait_for_server_transport_connected(timeout: int = 30):
    """Wait until the OPP server transport connected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_transport_connected(timeout)


def opp_wait_for_server_transport_disconnected(timeout: int = 30):
    """Wait until the OPP server transport disconnected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_transport_disconnected(timeout)


def opp_wait_for_server_connected(timeout: int = 30):
    """Wait until the OPP server OBEX session connected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived within timeout, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_connected(timeout)


def opp_wait_for_server_disconnected(timeout: int = 30):
    """Wait until the OPP server OBEX session disconnected event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_disconnected(timeout)


def opp_wait_for_server_push(timeout: int = 30):
    """Wait until the OPP server push (PUT) request event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        Tuple (total_length, is_final, name, mime_type, body), or None on timeout.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_push(timeout)


def opp_wait_for_server_pull_bcard(timeout: int = 30):
    """Wait until the OPP server pull business card (GET) request event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_pull_bcard(timeout)


def opp_wait_for_server_abort(timeout: int = 30):
    """Wait until the OPP server abort request event is received.

    Args:
        timeout: Maximum wait time in seconds.

    Returns:
        True if the event arrived, False otherwise.
    """
    stack = get_stack()
    return stack.opp.wait_for_server_abort(timeout)


def opp_discovered_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_DISCOVERED event.

    Payload: rfcomm_channel (uint8) + formats_count (uint8) + formats[].
    """
    log("%r %r", data, data_len)

    hdr_fmt = '<BB'
    hdr_len = struct.calcsize(hdr_fmt)
    rfcomm_channel, formats_count = struct.unpack_from(hdr_fmt, data)
    formats = list(struct.unpack_from(f'<{formats_count}B', data, hdr_len))

    log("rfcomm_channel:%r formats:%r", rfcomm_channel, formats)
    opp.discovered(rfcomm_channel, formats)


def opp_client_transport_connected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_TRANSPORT_CONNECTED event. No payload."""
    log("%r %r", data, data_len)
    opp.client_transport_connected()


def opp_client_transport_disconnected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_TRANSPORT_DISCONNECTED event. No payload."""
    log("%r %r", data, data_len)
    opp.client_transport_disconnected()


def opp_client_connected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_CONNECTED event.

    Payload: rsp_code (uint8) + version (uint8) + mopl (uint16 LE).
    """
    log("%r %r", data, data_len)

    rsp_code, version, mopl = struct.unpack_from('<BBH', data)
    log("rsp_code:%r version:%r mopl:%r", rsp_code, version, mopl)
    opp.client_connected(rsp_code, version, mopl)


def opp_client_disconnected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_DISCONNECTED event.

    Payload: rsp_code (uint8).
    """
    log("%r %r", data, data_len)

    rsp_code, = struct.unpack_from('<B', data)
    log("rsp_code:%r", rsp_code)
    opp.client_disconnected(rsp_code)


def opp_client_push_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_PUSH event.

    Payload: rsp_code (uint8).
    """
    log("%r %r", data, data_len)

    rsp_code, = struct.unpack_from('<B', data)
    log("rsp_code:%r", rsp_code)
    opp.client_push(rsp_code)


def opp_client_pull_bcard_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_PULL_BCARD event.

    Payload: rsp_code (uint8) + data_len (uint16 LE) + data[].
    """
    log("%r %r", data, data_len)

    hdr_fmt = '<BH'
    hdr_len = struct.calcsize(hdr_fmt)
    rsp_code, body_length = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_length]

    log("rsp_code:%r data_len:%r", rsp_code, body_length)
    opp.client_pull_bcard(rsp_code, body)


def opp_client_abort_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_CLIENT_ABORT event.

    Payload: rsp_code (uint8).
    """
    log("%r %r", data, data_len)

    rsp_code, = struct.unpack_from('<B', data)
    log("rsp_code:%r", rsp_code)
    opp.client_abort(rsp_code)


def opp_server_transport_connected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_TRANSPORT_CONNECTED event. No payload."""
    log("%r %r", data, data_len)
    opp.server_transport_connected()


def opp_server_transport_disconnected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_TRANSPORT_DISCONNECTED event. No payload."""
    log("%r %r", data, data_len)
    opp.server_transport_disconnected()


def opp_server_connected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_CONNECTED event.

    Payload: version (uint8) + mopl (uint16 LE).
    """
    log("%r %r", data, data_len)

    version, mopl = struct.unpack_from('<BH', data)
    log("version:%r mopl:%r", version, mopl)
    opp.server_connected(version, mopl)


def opp_server_disconnected_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_DISCONNECTED event. No payload."""
    log("%r %r", data, data_len)
    opp.server_disconnected()


def opp_server_push_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_PUSH event.

    Payload: total_length (uint32 LE) + is_final (uint8) + name_len (uint8)
             + type_len (uint8) + body_len (uint16 LE) + data[].
    """
    log("%r %r", data, data_len)

    hdr_fmt = '<IBBBH'
    hdr_len = struct.calcsize(hdr_fmt)
    total_length, is_final, name_len, type_len, body_len = struct.unpack_from(
        hdr_fmt, data)

    name = data[hdr_len:hdr_len + name_len]
    mime_type = data[hdr_len + name_len:hdr_len + name_len + type_len]
    body = data[hdr_len + name_len + type_len:
                hdr_len + name_len + type_len + body_len]

    log("total_length:%r is_final:%r name:%r type:%r body_len:%r",
        total_length, is_final, name, mime_type, body_len)
    opp.server_push(total_length, is_final, name, mime_type, body)


def opp_server_pull_bcard_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_PULL_BCARD event. No payload."""
    log("%r %r", data, data_len)
    opp.server_pull_bcard()


def opp_server_abort_ev(opp, data, data_len):
    """Handle BTP_OPP_EV_SERVER_ABORT event. No payload."""
    log("%r %r", data, data_len)
    opp.server_abort()


OPP_EV = {
    defs.BTP_OPP_EV_DISCOVERED: opp_discovered_ev,
    defs.BTP_OPP_EV_CLIENT_TRANSPORT_CONNECTED: opp_client_transport_connected_ev,
    defs.BTP_OPP_EV_CLIENT_TRANSPORT_DISCONNECTED: opp_client_transport_disconnected_ev,
    defs.BTP_OPP_EV_CLIENT_CONNECTED: opp_client_connected_ev,
    defs.BTP_OPP_EV_CLIENT_DISCONNECTED: opp_client_disconnected_ev,
    defs.BTP_OPP_EV_CLIENT_PUSH: opp_client_push_ev,
    defs.BTP_OPP_EV_CLIENT_PULL_BCARD: opp_client_pull_bcard_ev,
    defs.BTP_OPP_EV_CLIENT_ABORT: opp_client_abort_ev,
    defs.BTP_OPP_EV_SERVER_TRANSPORT_CONNECTED: opp_server_transport_connected_ev,
    defs.BTP_OPP_EV_SERVER_TRANSPORT_DISCONNECTED: opp_server_transport_disconnected_ev,
    defs.BTP_OPP_EV_SERVER_CONNECTED: opp_server_connected_ev,
    defs.BTP_OPP_EV_SERVER_DISCONNECTED: opp_server_disconnected_ev,
    defs.BTP_OPP_EV_SERVER_PUSH: opp_server_push_ev,
    defs.BTP_OPP_EV_SERVER_PULL_BCARD: opp_server_pull_bcard_ev,
    defs.BTP_OPP_EV_SERVER_ABORT: opp_server_abort_ev,
}
