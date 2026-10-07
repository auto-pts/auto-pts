#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, NXP.
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
import hashlib
import hmac
import logging
import queue
import struct
import threading
import time

from autopts.ptsprojects.stack import (
    FtpAuthStatus,
    FtpInfo,
    FtpSrmState,
    get_stack,
)
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, OBEXDigestChallenge, OBEXDigestResponse, OBEXHdr, OBEXRspCode, addr_str_to_le_bytes

log = logging.debug


FTP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_FTP,
                            defs.BTP_FTP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    # FTP Client commands
    'client_rfcomm_connect': (defs.BTP_SERVICE_ID_FTP,
                              defs.BTP_FTP_CMD_CLIENT_RFCOMM_CONNECT,
                              CONTROLLER_INDEX),
    'client_rfcomm_disconnect': (defs.BTP_SERVICE_ID_FTP,
                                 defs.BTP_FTP_CMD_CLIENT_RFCOMM_DISCONNECT,
                                 CONTROLLER_INDEX),
    'client_l2cap_connect': (defs.BTP_SERVICE_ID_FTP,
                             defs.BTP_FTP_CMD_CLIENT_L2CAP_CONNECT,
                             CONTROLLER_INDEX),
    'client_l2cap_disconnect': (defs.BTP_SERVICE_ID_FTP,
                                defs.BTP_FTP_CMD_CLIENT_L2CAP_DISCONNECT,
                                CONTROLLER_INDEX),
    'client_connect': (defs.BTP_SERVICE_ID_FTP,
                       defs.BTP_FTP_CMD_CLIENT_CONNECT,
                       CONTROLLER_INDEX),
    'client_disconnect': (defs.BTP_SERVICE_ID_FTP,
                          defs.BTP_FTP_CMD_CLIENT_DISCONNECT,
                          CONTROLLER_INDEX),
    'client_abort': (defs.BTP_SERVICE_ID_FTP,
                     defs.BTP_FTP_CMD_CLIENT_ABORT,
                     CONTROLLER_INDEX),
    'client_set_folder': (defs.BTP_SERVICE_ID_FTP,
                          defs.BTP_FTP_CMD_CLIENT_SET_FOLDER,
                          CONTROLLER_INDEX),
    'client_pull_folder_listing': (defs.BTP_SERVICE_ID_FTP,
                                   defs.BTP_FTP_CMD_CLIENT_PULL_FOLDER_LISTING,
                                   CONTROLLER_INDEX),
    'client_push_file': (defs.BTP_SERVICE_ID_FTP,
                         defs.BTP_FTP_CMD_CLIENT_PUSH_FILE,
                         CONTROLLER_INDEX),
    'client_pull_file': (defs.BTP_SERVICE_ID_FTP,
                         defs.BTP_FTP_CMD_CLIENT_PULL_FILE,
                         CONTROLLER_INDEX),
    'client_delete': (defs.BTP_SERVICE_ID_FTP,
                      defs.BTP_FTP_CMD_CLIENT_DELETE,
                      CONTROLLER_INDEX),
    'client_rename': (defs.BTP_SERVICE_ID_FTP,
                      defs.BTP_FTP_CMD_CLIENT_RENAME,
                      CONTROLLER_INDEX),
    'client_copy': (defs.BTP_SERVICE_ID_FTP,
                    defs.BTP_FTP_CMD_CLIENT_COPY,
                    CONTROLLER_INDEX),
    'client_set_permission': (defs.BTP_SERVICE_ID_FTP,
                              defs.BTP_FTP_CMD_CLIENT_SET_PERMISSION,
                              CONTROLLER_INDEX),
    # FTP Server commands
    'server_rfcomm_disconnect': (defs.BTP_SERVICE_ID_FTP,
                                 defs.BTP_FTP_CMD_SERVER_RFCOMM_DISCONNECT,
                                 CONTROLLER_INDEX),
    'server_l2cap_disconnect': (defs.BTP_SERVICE_ID_FTP,
                                defs.BTP_FTP_CMD_SERVER_L2CAP_DISCONNECT,
                                CONTROLLER_INDEX),
    'server_connect': (defs.BTP_SERVICE_ID_FTP,
                       defs.BTP_FTP_CMD_SERVER_CONNECT,
                       CONTROLLER_INDEX),
    'server_disconnect': (defs.BTP_SERVICE_ID_FTP,
                          defs.BTP_FTP_CMD_SERVER_DISCONNECT,
                          CONTROLLER_INDEX),
    'server_abort': (defs.BTP_SERVICE_ID_FTP,
                     defs.BTP_FTP_CMD_SERVER_ABORT,
                     CONTROLLER_INDEX),
    'server_set_folder': (defs.BTP_SERVICE_ID_FTP,
                          defs.BTP_FTP_CMD_SERVER_SET_FOLDER,
                          CONTROLLER_INDEX),
    'server_pull_folder_listing': (defs.BTP_SERVICE_ID_FTP,
                                   defs.BTP_FTP_CMD_SERVER_PULL_FOLDER_LISTING,
                                   CONTROLLER_INDEX),
    'server_push_file': (defs.BTP_SERVICE_ID_FTP,
                         defs.BTP_FTP_CMD_SERVER_PUSH_FILE,
                         CONTROLLER_INDEX),
    'server_pull_file': (defs.BTP_SERVICE_ID_FTP,
                         defs.BTP_FTP_CMD_SERVER_PULL_FILE,
                         CONTROLLER_INDEX),
    'server_delete': (defs.BTP_SERVICE_ID_FTP,
                      defs.BTP_FTP_CMD_SERVER_DELETE,
                      CONTROLLER_INDEX),
    'server_rename': (defs.BTP_SERVICE_ID_FTP,
                      defs.BTP_FTP_CMD_SERVER_RENAME,
                      CONTROLLER_INDEX),
    'server_copy': (defs.BTP_SERVICE_ID_FTP,
                    defs.BTP_FTP_CMD_SERVER_COPY,
                    CONTROLLER_INDEX),
    'server_set_permission': (defs.BTP_SERVICE_ID_FTP,
                              defs.BTP_FTP_CMD_SERVER_SET_PERMISSION,
                              CONTROLLER_INDEX),
}


def ftp_enc_digest_challenge_tlv(tlv_dict) -> bytes:
    """Encode AUTH_CHALLENGE dict to TLV bytes.

    OBEXDigestChallenge.NONCE:   bytes (16B)
    OBEXDigestChallenge.OPTIONS: int (uint8)
    OBEXDigestChallenge.REALM:   bytes
    """
    result = bytearray()
    for tag, value in tlv_dict.items():
        if tag == OBEXDigestChallenge.OPTIONS:
            raw = struct.pack('B', value)
        else:
            raw = value  # bytes
        result += struct.pack('BB', tag, len(raw)) + raw
    return bytes(result)


def ftp_enc_digest_response_tlv(tlv_dict) -> bytes:
    """Encode AUTH_RESPONSE dict to TLV bytes.

    OBEXDigestResponse.REQUEST_DIGEST: bytes (16B)
    OBEXDigestResponse.USER_ID:        str (max 20B)
    OBEXDigestResponse.NONCE:          bytes (16B)
    """
    result = bytearray()
    for tag, value in tlv_dict.items():
        if tag == OBEXDigestResponse.USER_ID:
            raw = value.encode('utf-8') if isinstance(value, str) else value
        else:
            raw = value  # bytes
        result += struct.pack('BB', tag, len(raw)) + raw
    return bytes(result)


def ftp_enc_hdr(hdr_dict, remaining_space, body_offset=0):
    """
    Encode OBEX headers to bytes

    Args:
        hdr_dict: Dictionary of headers to encode
        remaining_space: Available space in current packet
        body_offset: Current offset in body data (for fragmentation)

    Returns:
        tuple: (encoded_bytes, remaining_headers, new_body_offset)
    """
    data = bytearray()
    remaining_headers = {}
    new_body_offset = body_offset

    # Process headers in priority order
    header_priority = [
        OBEXHdr.TARGET,
        OBEXHdr.CONN_ID,
        OBEXHdr.AUTH_CHALLENGE,
        OBEXHdr.AUTH_RESPONSE,
        OBEXHdr.SRM,
        OBEXHdr.SRMP,
        OBEXHdr.ACTION_ID,
        OBEXHdr.TYPE,
        OBEXHdr.NAME,
        OBEXHdr.DEST_NAME,
        OBEXHdr.PERMISSION,
        OBEXHdr.BODY,
    ]

    # Track which headers have been processed
    processed_headers = set()

    for hdr_id in header_priority:
        if hdr_id not in hdr_dict:
            continue

        hdr_value = hdr_dict[hdr_id]
        hdr_bytes = bytearray()

        if hdr_id == OBEXHdr.CONN_ID or hdr_id == OBEXHdr.PERMISSION:
            hdr_bytes = struct.pack('>B', hdr_id) + struct.pack('>I', hdr_value)
        elif hdr_id == OBEXHdr.ACTION_ID:
            hdr_bytes = struct.pack('>BB', hdr_id, hdr_value)
        elif hdr_id == OBEXHdr.SRM or hdr_id == OBEXHdr.SRMP:
            if hdr_value == 0:
                processed_headers.add(hdr_id)  # Mark as processed
                continue
            hdr_bytes = struct.pack('>BB', hdr_id, hdr_value)
        elif hdr_id == OBEXHdr.TYPE:
            type_bytes = hdr_value.encode('utf-8') if isinstance(hdr_value, str) else hdr_value
            if len(type_bytes) != 0:
                type_bytes += b'\x00'  # Null terminator for string
            hdr_bytes = struct.pack('>BH', hdr_id, len(type_bytes) + 3) + type_bytes
        elif hdr_id == OBEXHdr.AUTH_CHALLENGE:
            tlv_bytes = ftp_enc_digest_challenge_tlv(hdr_value)
            hdr_bytes = struct.pack('>BH', hdr_id, len(tlv_bytes) + 3) + tlv_bytes
        elif hdr_id == OBEXHdr.AUTH_RESPONSE:
            tlv_bytes = ftp_enc_digest_response_tlv(hdr_value)
            hdr_bytes = struct.pack('>BH', hdr_id, len(tlv_bytes) + 3) + tlv_bytes
        elif hdr_id == OBEXHdr.TARGET:
            uuid_bytes = hdr_value.bytes
            hdr_bytes = struct.pack('>BH', hdr_id, len(uuid_bytes) + 3) + uuid_bytes
        elif hdr_id == OBEXHdr.NAME or hdr_id == OBEXHdr.DEST_NAME:
            name_bytes = hdr_value.encode('utf-16-be') if isinstance(hdr_value, str) else hdr_value
            if len(name_bytes) != 0:
                name_bytes += b'\x00\x00'  # Null terminator for UTF-16
            hdr_bytes = struct.pack('>BH', hdr_id, len(name_bytes) + 3) + name_bytes
        elif hdr_id == OBEXHdr.BODY:
            body_data = hdr_value if isinstance(hdr_value, bytes) else hdr_value.encode('utf-8')

            # Calculate available space for body (reserve 3 bytes for header + length)
            available_body_space = remaining_space - len(data) - 3

            if available_body_space <= 0:
                # No space for body in this packet
                remaining_headers[hdr_id] = hdr_value
                continue

            # Determine how much body data to include
            remaining_body = body_data[body_offset:]
            body_chunk_size = min(len(remaining_body), available_body_space)
            body_chunk = remaining_body[:body_chunk_size]

            new_body_offset = body_offset + body_chunk_size
            is_final_body = new_body_offset >= len(body_data)

            # Use END_OF_BODY for final chunk, BODY for intermediate chunks
            body_hdr_id = OBEXHdr.END_OF_BODY if is_final_body else OBEXHdr.BODY
            hdr_bytes = struct.pack('>BH', body_hdr_id, len(body_chunk) + 3) + body_chunk

            # If not final, keep BODY in remaining headers for next packet
            if not is_final_body:
                remaining_headers[OBEXHdr.BODY] = hdr_value
        else:
            continue

        # Check if adding this header exceeds remaining space
        if len(data) + len(hdr_bytes) > remaining_space:
            # Can't fit this header, save for next packet
            if hdr_id != OBEXHdr.BODY:  # Body already handled above
                remaining_headers[hdr_id] = hdr_value
            break  # Stop processing, remaining headers will be added below

        data.extend(hdr_bytes)
        processed_headers.add(hdr_id)  # Mark as processed

    # Add all unprocessed headers to remaining_headers
    for hdr_id, hdr_value in hdr_dict.items():
        if hdr_id not in processed_headers and hdr_id not in remaining_headers:
            remaining_headers[hdr_id] = hdr_value

    return bytes(data), remaining_headers, new_body_offset


def ftp_command_rsp_succ(op=None, timeout=20.0):
    logging.debug('%s', ftp_command_rsp_succ.__name__)
    iutctl = get_iut()
    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug('received %r %r', tuple_hdr, tuple_data)
    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_FTP)
    return tuple_data


def ftp_is_connected(conn_type, bd_addr=None):
    """Return True if a connection of *conn_type* is active."""
    stack = get_stack()
    return stack.ftp.is_connected(pts_addr_get(bd_addr), conn_type)


def ftp_wait_for_connection(conn_type, bd_addr=None, timeout=30):
    """Block until a connection of *conn_type* is active. Returns True or None on timeout."""
    stack = get_stack()
    return stack.ftp.wait_for_connection(pts_addr_get(bd_addr), conn_type, timeout)


def ftp_wait_for_disconnection(conn_type, bd_addr=None, timeout=30):
    """Block until a connection of *conn_type* is gone. Returns True or None on timeout."""
    stack = get_stack()
    return stack.ftp.wait_for_disconection(pts_addr_get(bd_addr), conn_type, timeout)


def ftp_rx_data_get(ev, bd_addr=None, timeout=60):
    """Block until event *ev* arrives for *bd_addr* and return the payload."""
    stack = get_stack()
    return stack.ftp.rx_data_get(pts_addr_get(bd_addr), ev, timeout)


def ftp_get_info(key, bd_addr=None):
    """Return connection info value for key."""
    stack = get_stack()
    return stack.ftp.get_info(pts_addr_get(bd_addr), key)


def ftp_set_info(key, value, bd_addr=None):
    """Set connection info value for key."""
    stack = get_stack()
    stack.ftp.set_info(pts_addr_get(bd_addr), key, value)


def ftp_set_read_only():
    """Set the server to read only mode"""
    stack = get_stack()
    stack.ftp.storage.set_permissions_recursive("/", 0x010101)


def ftp_create_folder(name, perms):
    """Crete a new folder in the server storage."""
    stack = get_stack()
    stack.ftp.storage.create_folder(name, perms)

# ---------------------------------------------------------------------------
# BTP command send functions
# ---------------------------------------------------------------------------


def ftp_client_rfcomm_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_RFCOMM_CONNECT.
    Payload: bt_addr_le_t (addr_type + addr).
    """
    logging.debug('%s %r', ftp_client_rfcomm_connect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_rfcomm_connect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_RFCOMM_CONNECT)


def ftp_client_rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_RFCOMM_DISCONNECT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_client_rfcomm_disconnect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_rfcomm_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_RFCOMM_DISCONNECT)


def ftp_client_l2cap_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_L2CAP_CONNECT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_client_l2cap_connect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_l2cap_connect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_L2CAP_CONNECT)


def ftp_client_l2cap_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_L2CAP_DISCONNECT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_client_l2cap_disconnect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_l2cap_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_L2CAP_DISCONNECT)


def ftp_client_connect(buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_CONNECT (OBEX CONNECT).
    Payload: bt_addr_le_t + buf_len (2B) + buf.
    """
    logging.debug('%s %r', ftp_client_connect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_connect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_CONNECT)


def ftp_client_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_DISCONNECT (OBEX DISCONNECT).
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_client_disconnect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_DISCONNECT)


def ftp_client_abort(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_ABORT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_client_abort.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['client_abort'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_ABORT)


def ftp_client_set_folder(flags, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_SET_FOLDER (SET_PATH).
    Payload: bt_addr_le_t + flags (1B) + buf_len (2B) + buf.
    flags: 0x02 = navigate down/root, 0x03 = navigate up.
    """
    logging.debug('%s flags=%r %r', ftp_client_set_folder.__name__,
                  flags, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', flags))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_set_folder'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_SET_FOLDER)


def ftp_client_pull_folder_listing(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_PULL_FOLDER_LISTING (GET folder listing).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_pull_folder_listing.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_pull_folder_listing'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_PULL_FOLDER_LISTING)


def ftp_client_push_file(final, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_PUSH_FILE (PUT file).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_push_file.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_push_file'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_PUSH_FILE)


def ftp_client_pull_file(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_PULL_FILE (GET file).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_pull_file.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_pull_file'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_PULL_FILE)


def ftp_client_delete(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_DELETE.
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_delete.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_delete'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_DELETE)


def ftp_client_rename(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_RENAME (MOVE/RENAME ACTION).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_rename.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_rename'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_RENAME)


def ftp_client_copy(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_COPY (COPY ACTION).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_copy.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_copy'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_COPY)


def ftp_client_set_permission(final=True, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_CLIENT_SET_PERMISSION (SET PERMISSIONS ACTION).
    Payload: bt_addr_le_t + final (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s final=%r %r', ftp_client_set_permission.__name__, final, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['client_set_permission'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_CLIENT_SET_PERMISSION)


# --- Server commands ---

def ftp_server_rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_RFCOMM_DISCONNECT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_server_rfcomm_disconnect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['server_rfcomm_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_RFCOMM_DISCONNECT)


def ftp_server_l2cap_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_L2CAP_DISCONNECT.
    Payload: bt_addr_le_t.
    """
    logging.debug('%s %r', ftp_server_l2cap_disconnect.__name__, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    iutctl.btp_socket.send(*FTP['server_l2cap_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_L2CAP_DISCONNECT)


def ftp_server_connect(rsp_code, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_CONNECT (OBEX CONNECT response).
    Payload: bt_addr_le_t + rsp_code (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_connect.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['server_connect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_CONNECT)


def ftp_server_disconnect(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_DISCONNECT (OBEX DISCONNECT response).
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_disconnect.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_disconnect'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_DISCONNECT)


def ftp_server_abort(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_ABORT.
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_abort.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_abort'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_ABORT)


def ftp_server_set_folder(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_SET_FOLDER (SET_PATH response).
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_set_folder.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_set_folder'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_SET_FOLDER)


def ftp_server_pull_folder_listing(rsp_code, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_PULL_FOLDER_LISTING (GET folder listing response).
    Payload: bt_addr_le_t + rsp_code (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_pull_folder_listing.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['server_pull_folder_listing'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_PULL_FOLDER_LISTING)


def ftp_server_push_file(rsp_code, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_PUSH_FILE (PUT file response).
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_push_file.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['server_push_file'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_PUSH_FILE)


def ftp_server_pull_file(rsp_code, buf=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_PULL_FILE (GET file response).
    Payload: bt_addr_le_t + rsp_code (1B) + buf_len (2B) + buf.
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_pull_file.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('H', len(buf)))
    data_ba.extend(buf)
    iutctl.btp_socket.send(*FTP['server_pull_file'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_PULL_FILE)


def ftp_server_delete(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_DELETE.
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_delete.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_delete'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_DELETE)


def ftp_server_rename(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_RENAME.
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_rename.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_rename'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_RENAME)


def ftp_server_copy(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_COPY.
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_copy.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_copy'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_COPY)


def ftp_server_set_permission(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send BTP_FTP_SERVER_SET_PERMISSION.
    Payload: bt_addr_le_t + rsp_code (1B).
    """
    logging.debug('%s rsp=0x%02x %r', ftp_server_set_permission.__name__, rsp_code, bd_addr)
    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))
    iutctl.btp_socket.send(*FTP['server_set_permission'], data=data_ba)
    ftp_command_rsp_succ(defs.BTP_FTP_CMD_SERVER_SET_PERMISSION)


# ---------------------------------------------------------------------------
# OBEX header helpers for FTP
# ---------------------------------------------------------------------------

def bt_ftp_calculate_nonce(pwd: str) -> bytes:
    """Calculate a 16-byte OBEX authentication nonce from a password.

    Mirrors bt_ftp_calculate_nonce() in ftp.c.
    Algorithm: MD5(timestamp_bytes ':' password)
    Uses a monotonic nanosecond timestamp (mirrors k_uptime_get() in C).

    Args:
        pwd: Password string (must be non-empty).

    Returns:
        16-byte nonce bytes.

    Raises:
        ValueError: If pwd is empty.
    """
    if not pwd:
        raise ValueError("Password must not be empty")
    # Use monotonic nanosecond timestamp (mirrors k_uptime_get() in C), packed as little-endian int64.
    timestamp = struct.pack('<q', time.monotonic_ns())
    hash_input = timestamp + b':' + pwd.encode('utf-8')
    return hashlib.md5(hash_input).digest()


def bt_ftp_calculate_rsp_digest(pwd: str, nonce: bytes) -> bytes:
    """Calculate the 16-byte OBEX authentication response digest.

    Mirrors bt_ftp_calculate_rsp_digest() in ftp.c.
    Algorithm: MD5(nonce ':' password)

    Args:
        pwd:   Password string (must be non-empty).
        nonce: 16-byte challenge nonce from the peer.

    Returns:
        16-byte response digest bytes.

    Raises:
        ValueError: If pwd is empty or nonce is not 16 bytes.
    """
    if not pwd:
        raise ValueError("Password must not be empty")
    hash_input = nonce + b':' + pwd.encode('utf-8')
    return hashlib.md5(hash_input).digest()


def bt_ftp_verify_authentication(nonce: bytes, rsp_digest: bytes, pwd: str) -> bool:
    """Verify an OBEX authentication response digest against the local nonce.

    Mirrors bt_ftp_verify_authentication() in ftp.c.

    Args:
        nonce:      16-byte nonce that was originally sent as a challenge.
        rsp_digest: 16-byte response digest received from the peer.
        pwd:        Expected password string.

    Returns:
        True if the digest matches, False otherwise.
    """
    try:
        expected = bt_ftp_calculate_rsp_digest(pwd, nonce)
    except ValueError:
        return False
    return hmac.compare_digest(expected, rsp_digest)


def ftp_dec_digest_challenge_tlv(data, data_len):
    """Decode AUTH_CHALLENGE TLV bytes to a dict.

    OBEXDigestChallenge.NONCE   (0x00): 16-byte nonce, stored as bytes
    OBEXDigestChallenge.OPTIONS (0x01): uint8, stored as int
    OBEXDigestChallenge.REALM   (0x02): stored as bytes (no parse)
    """
    err = False
    dct = {}
    offset = 0
    while offset < data_len:
        if offset + 2 > data_len:
            err = True
            break
        tag, length = struct.unpack_from('BB', data, offset)
        offset += 2
        if offset + length > data_len:
            err = True
            break
        if tag == OBEXDigestChallenge.NONCE:
            dct[tag] = struct.unpack_from(f'{length}s', data, offset)[0]   # 16B bytes
        elif tag == OBEXDigestChallenge.OPTIONS:
            dct[tag] = struct.unpack_from('B', data, offset)[0] if length >= 1 else 0  # uint8
        elif tag == OBEXDigestChallenge.REALM:
            dct[tag] = struct.unpack_from(f'{length}s', data, offset)[0]   # bytes
        offset += length
    return err, dct


def ftp_dec_digest_response_tlv(data, data_len):
    """Decode AUTH_RESPONSE TLV bytes to a dict.

    OBEXDigestResponse.REQUEST_DIGEST (0x00): 16-byte digest, stored as bytes
    OBEXDigestResponse.USER_ID        (0x01): string
    OBEXDigestResponse.NONCE          (0x02): 16-byte nonce, stored as bytes
    """
    err = False
    dct = {}
    offset = 0
    while offset < data_len:
        if offset + 2 > data_len:
            err = True
            break
        tag, length = struct.unpack_from('BB', data, offset)
        offset += 2
        if offset + length > data_len:
            err = True
            break
        if tag == OBEXDigestResponse.REQUEST_DIGEST:
            dct[tag] = struct.unpack_from(f'{length}s', data, offset)[0]    # 16B bytes
        elif tag == OBEXDigestResponse.USER_ID:
            dct[tag] = struct.unpack_from(f'{length}s', data, offset)[0].decode('utf-8')  # string
        elif tag == OBEXDigestResponse.NONCE:
            dct[tag] = struct.unpack_from(f'{length}s', data, offset)[0]    # 16B bytes
        offset += length
    return err, dct


def ftp_ev_decode_addr(data):
    hdr = '<B6s'
    hdr_len = struct.calcsize(hdr)
    if len(data) < hdr_len:
        raise BTPError('Invalid data length')

    _, addr = struct.unpack_from(hdr, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    return addr, data[hdr_len:]


def ftp_dec_hdr(dct, data, data_len):
    err = False
    offset = 0

    while offset < data_len:
        hi = struct.unpack_from("<B", data, offset)[0]
        offset += struct.calcsize("<B")
        if ((hi >> 6) == 0x3):
            hv_len = 4
        elif ((hi >> 6) == 0x2):
            hv_len = 1
        else:
            hv_len = struct.unpack_from(">H", data, offset)[0]
            offset += struct.calcsize(">H")
            if hv_len < 3:  # 3 = 1(hdr) + 2(length)
                err = True
                break
            hv_len -= 3

        if hv_len + offset > data_len:
            err = True
            break

        if hi == OBEXHdr.TYPE:
            dct[hi] = struct.unpack_from(f'{hv_len}s', data, offset)[0].decode().rstrip('\x00')
        elif hi == OBEXHdr.SRM or hi == OBEXHdr.SRMP:
            dct[hi] = struct.unpack_from('B', data, offset)[0]
        elif hi == OBEXHdr.CONN_ID or hi == OBEXHdr.PERMISSION:
            dct[hi] = struct.unpack_from('>I', data, offset)[0]
        elif hi == OBEXHdr.NAME or hi == OBEXHdr.DEST_NAME:
            if hv_len > 0:
                dct[hi] = struct.unpack_from(f'{hv_len}s', data, offset)[0].decode('utf-16-be').rstrip('\x00')
            else:
                dct[hi] = ''
        elif (hi == OBEXHdr.BODY) or (hi == OBEXHdr.END_OF_BODY):
            if OBEXHdr.BODY in dct:
                dct[OBEXHdr.BODY] += struct.unpack_from(f'{hv_len}s', data, offset)[0]
            else:
                dct[OBEXHdr.BODY] = struct.unpack_from(f'{hv_len}s', data, offset)[0]
        elif hi == OBEXHdr.AUTH_CHALLENGE:
            err, dct[hi] = ftp_dec_digest_challenge_tlv(data[offset:], hv_len)
            if err:
                break
        elif hi == OBEXHdr.AUTH_RESPONSE:
            err, dct[hi] = ftp_dec_digest_response_tlv(data[offset:], hv_len)
            if err:
                break

        offset += hv_len

    return err, dct


def ftp_dec_req(data, dct=None):
    """Decode final(1B) + buf_len(2B) + OBEX headers. Return (final, dict)."""
    if dct is None:
        dct = {}
    hdr = '<BH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    final, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    ftp_dec_hdr(dct, data, len(data))
    return final, dct


def ftp_dec_rsp(data, dct=None):
    """Decode rsp_code(1B) + buf_len(2B) + OBEX headers. Return (rsp_code, dct)."""
    if dct is None:
        dct = {}
    hdr = '<BH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    rsp_code, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    ftp_dec_hdr(dct, data, len(data))
    return rsp_code, dct


# ---------------------------------------------------------------------------
# Internal FTP event handler functions (called from FtpEventHandler worker)
# ---------------------------------------------------------------------------

# -- Client transport events --

def _ftp_client_rfcomm_connected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_rfcomm_connected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.add_connection(addr, defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED)


def _ftp_client_rfcomm_disconnected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_rfcomm_disconnected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_CLIENT_CONNECT)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED)


def _ftp_client_l2cap_connected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_l2cap_connected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.add_connection(addr, defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)


def _ftp_client_l2cap_disconnected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_l2cap_disconnected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_CLIENT_CONNECT)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)


# -- Client OBEX events --

def ftp_dec_conn_rsp(data):
    dct = {}

    hdr = '<BBHH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    rsp_code, version, mopl, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    ftp_dec_hdr(dct, data, len(data))

    return rsp_code, version, mopl, dct


def _ftp_client_connect_ev(ftp, data, data_len):
    """Handle OBEX CONNECT response event for the FTP client.

    - SUCCESS + LOCAL_AUTH_ENABLED: verify server's auth response digest.
      Disconnect on failure.
    - UNAUTH: extract peer challenge nonce, then immediately re-send CONNECT
      with AUTH_CHALLENGE + AUTH_RESPONSE using the stored password.
    """
    logging.debug('%s %r', _ftp_client_connect_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, version, mopl, rsp_hdr = ftp_dec_conn_rsp(data)

    if rsp_code == OBEXRspCode.SUCCESS:
        ftp.set_info(addr, FtpInfo.MOPL, mopl)
        conn_id = rsp_hdr.get(OBEXHdr.CONN_ID)
        if conn_id is not None:
            ftp.set_info(addr, FtpInfo.CONN_ID, conn_id)

        auth_state = ftp.get_info(addr, FtpInfo.AUTH_STATE) or 0
        if auth_state & FtpAuthStatus.LOCAL_AUTH_ENABLED:
            # We sent a challenge; verify the server's auth response digest.
            # rsp_hdr[OBEXHdr.AUTH_RESPONSE] is a decoded dict from ftp_dec_hdr.
            auth_rsp_dict = rsp_hdr.get(OBEXHdr.AUTH_RESPONSE)
            if auth_rsp_dict is None:
                logging.error('_ftp_client_connect_ev: no AUTH_RESPONSE from server')
                ftp_client_disconnect(bd_addr=addr)
                return

            rsp_digest = auth_rsp_dict.get(OBEXDigestResponse.REQUEST_DIGEST)
            if rsp_digest is None:
                logging.error('_ftp_client_connect_ev: cannot extract digest from AUTH_RESPONSE')
                ftp_client_disconnect(bd_addr=addr)
                return

            local_nonce = ftp.get_info(addr, FtpInfo.LOCAL_NONCE)
            pwd = ftp.get_info(addr, FtpInfo.PWD)
            if not bt_ftp_verify_authentication(local_nonce, rsp_digest, pwd):
                logging.error('_ftp_client_connect_ev: server auth response verification failed')
                ftp_client_disconnect(bd_addr=addr)
                return

            logging.debug('_ftp_client_connect_ev: server authentication succeeded')

        # Clear auth state and complete OBEX connection
        ftp.set_info(addr, FtpInfo.AUTH_STATE, 0)
        ftp.set_info(addr, FtpInfo.LOCAL_NONCE, None)
        ftp.set_info(addr, FtpInfo.PEER_NONCE, None)
        ftp.add_connection(addr, defs.BTP_FTP_EV_CLIENT_CONNECT)

    elif rsp_code == OBEXRspCode.UNAUTH:
        # Server requires authentication; extract its challenge nonce.
        # rsp_hdr[OBEXHdr.AUTH_CHALLENGE] is a decoded dict from ftp_dec_hdr.
        auth_chal_dict = rsp_hdr.get(OBEXHdr.AUTH_CHALLENGE)
        if auth_chal_dict is None:
            logging.warning('_ftp_client_connect_ev: UNAUTH but no AUTH_CHALLENGE from server')
            return

        peer_nonce = auth_chal_dict.get(OBEXDigestChallenge.NONCE)
        if peer_nonce is None:
            logging.warning('_ftp_client_connect_ev: cannot extract nonce from AUTH_CHALLENGE')
            return

        pwd = ftp.get_info(addr, FtpInfo.PWD)
        if pwd is None:
            logging.error('_ftp_client_connect_ev: server requires authentication, but no password configured')
            return

        # Password available: build and send the authenticated re-CONNECT inline.
        local_nonce = bt_ftp_calculate_nonce(pwd)
        ftp.set_info(addr, FtpInfo.LOCAL_NONCE, local_nonce)
        ftp.set_info(addr, FtpInfo.PEER_NONCE, peer_nonce)

        digest = bt_ftp_calculate_rsp_digest(pwd, peer_nonce)
        auth_hdr = {
            OBEXHdr.AUTH_CHALLENGE: {OBEXDigestChallenge.NONCE: local_nonce},
            OBEXHdr.AUTH_RESPONSE:  {OBEXDigestResponse.REQUEST_DIGEST: digest},
        }
        buf, _, _ = ftp_enc_hdr(auth_hdr, mopl)

        auth_state = ftp.get_info(addr, FtpInfo.AUTH_STATE) or 0
        ftp.set_info(addr, FtpInfo.AUTH_STATE, auth_state | FtpAuthStatus.LOCAL_AUTH_ENABLED)

        logging.debug('_ftp_client_connect_ev: re-sending CONNECT with auth headers')
        ftp_client_connect(buf=buf, bd_addr=addr)


def _ftp_client_disconnect_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_disconnect_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    if rsp_code == OBEXRspCode.SUCCESS:
        ftp.remove_connection(addr, defs.BTP_FTP_EV_CLIENT_CONNECT)


def _ftp_client_abort_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_abort_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.clear_rx_tx_state(addr)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_ABORT, (rsp_code, rsp_hdr))


def _ftp_client_set_folder_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_set_folder_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_SET_FOLDER, (rsp_code, rsp_hdr))


def _ftp_client_pull_folder_listing_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_pull_folder_listing_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        logging.error('Connection not found for addr %s', addr)
        return
    p = conn.conn_info

    rsp_code, p[FtpInfo.RX_DATA] = ftp_dec_rsp(data, p[FtpInfo.RX_DATA])

    if rsp_code != OBEXRspCode.CONTINUE:
        ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_PULL_FOLDER_LISTING, (rsp_code, p[FtpInfo.RX_DATA]))
        ftp.clear_rx_tx_state(addr)
        return

    if p.get(FtpInfo.LOCAL_SRM) and p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_DISABLED:
        p[FtpInfo.LOCAL_SRM] = False
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
            if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(FtpInfo.LOCAL_SRMP):
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(FtpInfo.LOCAL_SRMP):
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED

        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[FtpInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(FtpInfo.LOCAL_SRMP):
            p[FtpInfo.LOCAL_SRMP] -= 1

    if p.get(FtpInfo.SRM_STATE) != FtpSrmState.SRM_ENABLED:
        if p.get(FtpInfo.LOCAL_SRMP):
            encoded_hdr = struct.pack('BB', OBEXHdr.SRMP, 1)
        else:
            encoded_hdr = b''
        ftp_client_pull_folder_listing(True, buf=encoded_hdr, bd_addr=addr)


def _ftp_client_push_file_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_push_file_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        logging.error('Connection not found for addr %s', addr)
        return
    p = conn.conn_info

    rsp_code, p[FtpInfo.RX_DATA] = ftp_dec_rsp(data, p[FtpInfo.RX_DATA])

    if rsp_code != OBEXRspCode.CONTINUE:
        ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_PUSH_FILE, (rsp_code, p[FtpInfo.RX_DATA]))
        ftp.clear_rx_tx_state(addr)
        return

    if p.get(FtpInfo.LOCAL_SRM) and p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_DISABLED:
        p[FtpInfo.LOCAL_SRM] = False
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
            if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[FtpInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[FtpInfo.TX_DATA], p[FtpInfo.TX_CNT] = ftp_enc_hdr(
            p[FtpInfo.TX_DATA], p.get(FtpInfo.MOPL) - 3, p[FtpInfo.TX_CNT]
        )
        is_final = len(p[FtpInfo.TX_DATA]) == 0
        ftp_client_push_file(is_final, buf=encoded_hdr, bd_addr=addr)

        if is_final:
            ftp.clear_rx_tx_state(addr)
            break

        if p.get(FtpInfo.SRM_STATE) != FtpSrmState.SRM_ENABLED:
            break


def _ftp_client_pull_file_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_pull_file_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        logging.error('Connection not found for addr %s', addr)
        return
    p = conn.conn_info

    rsp_code, p[FtpInfo.RX_DATA] = ftp_dec_rsp(data, p[FtpInfo.RX_DATA])

    if rsp_code != OBEXRspCode.CONTINUE:
        ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_PULL_FILE, (rsp_code, p[FtpInfo.RX_DATA]))
        ftp.clear_rx_tx_state(addr)
        return

    if p.get(FtpInfo.LOCAL_SRM) and p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_DISABLED:
        p[FtpInfo.LOCAL_SRM] = False
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
            if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(FtpInfo.LOCAL_SRMP):
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(FtpInfo.LOCAL_SRMP):
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED

        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[FtpInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(FtpInfo.LOCAL_SRMP):
            p[FtpInfo.LOCAL_SRMP] -= 1

    if p.get(FtpInfo.SRM_STATE) != FtpSrmState.SRM_ENABLED:
        if p.get(FtpInfo.LOCAL_SRMP):
            encoded_hdr = struct.pack('BB', OBEXHdr.SRMP, 1)
        else:
            encoded_hdr = b''
        ftp_client_pull_file(True, buf=encoded_hdr, bd_addr=addr)


def _ftp_client_delete_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_delete_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_DELETE, (rsp_code, rsp_hdr))


def _ftp_client_rename_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_rename_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_RENAME, (rsp_code, rsp_hdr))


def _ftp_client_copy_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_copy_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_COPY, (rsp_code, rsp_hdr))


def _ftp_client_set_permission_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_client_set_permission_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    rsp_code, rsp_hdr = ftp_dec_rsp(data)
    ftp.rx(addr, defs.BTP_FTP_EV_CLIENT_SET_PERMISSION, (rsp_code, rsp_hdr))


# -- Server transport events --

def _ftp_server_rfcomm_connected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_rfcomm_connected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.add_connection(addr, defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED)


def _ftp_server_rfcomm_disconnected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_rfcomm_disconnected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_SERVER_CONNECT)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED)


def _ftp_server_l2cap_connected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_l2cap_connected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.add_connection(addr, defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED)


def _ftp_server_l2cap_disconnected_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_l2cap_disconnected_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_SERVER_CONNECT)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED)


# -- Server OBEX events (auto-respond using FtpStorage) --

def ftp_dec_conn_req(data):
    dct = {}

    hdr = '<BHH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    version, mopl, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    ftp_dec_hdr(dct, data, len(data))

    return version, mopl, dct


def _ftp_server_connect_ev(ftp, data, data_len):
    """Handle OBEX CONNECT request event for the FTP server.

    - If LOCAL_AUTH_ENABLED (we previously sent a challenge): verify the
      client's AUTH_RESPONSE digest. Return FORBIDDEN.
    - If the client also sent an AUTH_CHALLENGE: send AUTH_RESPONSE digest.
    - If a password is configured and no challenge has been sent yet:
      generate a nonce, send UNAUTH with AUTH_CHALLENGE, set LOCAL_AUTH_ENABLED.
    - Otherwise: send plain SUCCESS.
    """
    logging.debug('%s %r', _ftp_server_connect_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    version, mopl, req_hdr = ftp_dec_conn_req(data)
    ftp.set_info(addr, FtpInfo.MOPL, mopl)

    auth_state = ftp.get_info(addr, FtpInfo.AUTH_STATE) or 0
    pwd = ftp.get_info(addr, FtpInfo.PWD)

    # Step 1: Verify client's auth response if we previously sent a challenge.
    if auth_state & FtpAuthStatus.LOCAL_AUTH_ENABLED:
        # req_hdr[OBEXHdr.AUTH_RESPONSE] is a decoded dict from ftp_dec_hdr.
        auth_rsp_dict = req_hdr.get(OBEXHdr.AUTH_RESPONSE)
        if auth_rsp_dict is None:
            logging.warning('_ftp_server_connect_ev: no AUTH_RESPONSE from client')
            return

        rsp_digest = auth_rsp_dict.get(OBEXDigestResponse.REQUEST_DIGEST)
        if rsp_digest is None:
            logging.warning('_ftp_server_connect_ev: cannot extract digest from AUTH_RESPONSE')
            return

        local_nonce = ftp.get_info(addr, FtpInfo.LOCAL_NONCE)
        if not bt_ftp_verify_authentication(local_nonce, rsp_digest, pwd):
            logging.error('_ftp_server_connect_ev: client auth response verification failed')
            ftp_server_connect(OBEXRspCode.FORBIDDEN, bd_addr=addr)
            return

        logging.debug('_ftp_server_connect_ev: client authentication succeeded')

        # Check if the client also sent a challenge (mutual auth).
        # req_hdr[OBEXHdr.AUTH_CHALLENGE] is a decoded dict from ftp_dec_hdr.
        peer_nonce = req_hdr.get(OBEXHdr.AUTH_CHALLENGE, {}).get(OBEXDigestChallenge.NONCE)
        if peer_nonce is not None:
            logging.debug('_ftp_server_connect_ev: client also requires authentication')

            digest = bt_ftp_calculate_rsp_digest(pwd, peer_nonce)
            rsp_buf, _, _ = ftp_enc_hdr(
                {OBEXHdr.AUTH_RESPONSE: {OBEXDigestResponse.REQUEST_DIGEST: digest}}, mopl)
        else:
            rsp_buf = b''

        # Clear auth state
        ftp.set_info(addr, FtpInfo.AUTH_STATE, 0)
        ftp.set_info(addr, FtpInfo.LOCAL_NONCE, None)
        ftp_server_connect(OBEXRspCode.SUCCESS, buf=rsp_buf, bd_addr=addr)
        ftp.add_connection(addr, defs.BTP_FTP_EV_SERVER_CONNECT)
        return

    # Step 2: Check if a password is configured and no challenge sent yet.
    if pwd:
        # Send UNAUTH with AUTH_CHALLENGE so the client must authenticate.
        local_nonce = bt_ftp_calculate_nonce(pwd)
        ftp.set_info(addr, FtpInfo.LOCAL_NONCE, local_nonce)
        rsp_buf, _, _ = ftp_enc_hdr(
            {OBEXHdr.AUTH_CHALLENGE: {OBEXDigestChallenge.NONCE: local_nonce}}, mopl)
        ftp.set_info(addr, FtpInfo.AUTH_STATE, auth_state | FtpAuthStatus.LOCAL_AUTH_ENABLED)
        ftp_server_connect(OBEXRspCode.UNAUTH, buf=rsp_buf, bd_addr=addr)
        return

    # Step 3: No authentication required -- plain SUCCESS.
    ftp_server_connect(OBEXRspCode.SUCCESS, bd_addr=addr)
    ftp.add_connection(addr, defs.BTP_FTP_EV_SERVER_CONNECT)


def _ftp_server_disconnect_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_disconnect_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    ftp_server_disconnect(OBEXRspCode.SUCCESS, bd_addr=addr)
    ftp.remove_connection(addr, defs.BTP_FTP_EV_SERVER_CONNECT)


def _ftp_server_abort_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_abort_ev.__name__, data)
    addr, _ = ftp_ev_decode_addr(data)
    ftp.clear_rx_tx_state(addr)
    ftp_server_abort(OBEXRspCode.SUCCESS, bd_addr=addr)


def _ftp_server_set_folder_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_set_folder_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)

    hdr_fmt = '<BH'
    hdr_size = struct.calcsize(hdr_fmt)
    if len(data) < hdr_size:
        logging.error('FTP server_set_folder: invalid data length')
        ftp_server_set_folder(OBEXRspCode.BAD_REQ, bd_addr=addr)
        return

    flags, buf_len = struct.unpack_from(hdr_fmt, data)
    data = data[hdr_size:]

    req_hdr = {}
    ftp_dec_hdr(req_hdr, data, len(data))

    folder_name = req_hdr.get(OBEXHdr.NAME, '')

    if flags == 0:
        rsp_code = ftp.storage.create_folder(folder_name)
        if rsp_code == OBEXRspCode.SUCCESS:
            ftp.storage.set_folder(folder_name, 0x02)
    else:
        # backup (go up) or navigate to root
        rsp_code = ftp.storage.set_folder(folder_name, flags)

    ftp_server_set_folder(rsp_code, bd_addr=addr)


def _ftp_server_pull_folder_listing_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_pull_folder_listing_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        ftp_server_pull_folder_listing(OBEXRspCode.NOT_FOUND, bd_addr=addr)
        ftp.clear_rx_tx_state(addr)
        return
    p = conn.conn_info

    final, p[FtpInfo.RX_DATA] = ftp_dec_req(data, p[FtpInfo.RX_DATA])
    if not final:
        ftp_server_pull_folder_listing(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        ftp.clear_rx_tx_state(addr)
        return

    if p[FtpInfo.TX_CNT] == 0:
        rsp_code, body = ftp.storage.build_folder_listing()
        if rsp_code != OBEXRspCode.SUCCESS:
            ftp_server_pull_folder_listing(rsp_code, bd_addr=addr)
            ftp.clear_rx_tx_state(addr)
            return

        hdr = {OBEXHdr.BODY: body}

        is_l2cap = ftp.is_connected(addr=addr, conn_type=defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED)
        req_hdr = p[FtpInfo.RX_DATA]
        if is_l2cap and req_hdr.get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
            if req_hdr.get(OBEXHdr.SRMP, 0) == 1:
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

        p[FtpInfo.TX_DATA] = hdr

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[FtpInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED

    mopl = p.get(FtpInfo.MOPL, 255)
    while True:
        encoded_hdr, p[FtpInfo.TX_DATA], p[FtpInfo.TX_CNT] = ftp_enc_hdr(
            p[FtpInfo.TX_DATA], mopl - 3, p[FtpInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[FtpInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE
        ftp_server_pull_folder_listing(rsp_code, buf=encoded_hdr, bd_addr=addr)

        if rsp_code != OBEXRspCode.CONTINUE:
            ftp.clear_rx_tx_state(addr)
            break

        if p.get(FtpInfo.SRM_STATE) != FtpSrmState.SRM_ENABLED:
            break


def _ftp_server_push_file_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_push_file_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        ftp_server_push_file(OBEXRspCode.NOT_FOUND, bd_addr=addr)
        return
    p = conn.conn_info

    tx_hdr = {}
    first = not p[FtpInfo.RX_DATA]

    final, p[FtpInfo.RX_DATA] = ftp_dec_req(data, p[FtpInfo.RX_DATA])

    if first:
        rsp_code = OBEXRspCode.SUCCESS
        name = p[FtpInfo.RX_DATA].get(OBEXHdr.NAME)
        if not name:
            rsp_code = OBEXRspCode.BAD_REQ
        elif ftp.storage.is_existing_file_name(name):
            rsp_code = OBEXRspCode.NOT_ACCEPTABLE
        else:
            rsp_code = ftp.storage.check_write_permission()

        if rsp_code != OBEXRspCode.SUCCESS:
            ftp_server_push_file(rsp_code, bd_addr=addr)
            ftp.clear_rx_tx_state(addr)
            return

        # negotiate SRM on L2CAP
        is_l2cap = ftp.is_connected(addr=addr, conn_type=defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED)
        if is_l2cap and p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1 and not final:
            tx_hdr[OBEXHdr.SRM] = 1

    if final:
        # Get name and body
        name = p[FtpInfo.RX_DATA].get(OBEXHdr.NAME)
        body = p[FtpInfo.RX_DATA].get(OBEXHdr.BODY)

        rsp_code = ftp.storage.push_file(name, body)
        ftp_server_push_file(rsp_code, bd_addr=addr)
        ftp.clear_rx_tx_state(addr)
        return

    if p[FtpInfo.LOCAL_SRMP] and tx_hdr.get(OBEXHdr.SRM, 0) == 1:
        tx_hdr[OBEXHdr.SRMP] = 1

    if p[FtpInfo.SRM_STATE] != FtpSrmState.SRM_ENABLED:
        encoded_hdr, _, _ = ftp_enc_hdr(tx_hdr, p[FtpInfo.MOPL] - 3)
        ftp_server_push_file(OBEXRspCode.CONTINUE, encoded_hdr)

    if tx_hdr.get(OBEXHdr.SRM, 0) == 1 and p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
        del p[FtpInfo.RX_DATA][OBEXHdr.SRM]
        p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
        if p[FtpInfo.LOCAL_SRMP]:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.LOCAL_SRMP]:
            p[FtpInfo.LOCAL_SRMP] -= 1
        else:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED


def _ftp_server_pull_file_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_pull_file_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    conn = ftp.conn_lookup(addr)
    if conn is None:
        ftp_server_pull_file(OBEXRspCode.NOT_FOUND, bd_addr=addr)
        ftp.clear_rx_tx_state(addr)
        return
    p = conn.conn_info

    final, p[FtpInfo.RX_DATA] = ftp_dec_req(data, p[FtpInfo.RX_DATA])
    if not final:
        ftp_server_pull_file(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        ftp.clear_rx_tx_state(addr)
        return

    if p[FtpInfo.TX_CNT] == 0:
        name = p[FtpInfo.RX_DATA].get(OBEXHdr.NAME)
        if not name:
            logging.error('FTP server_pull_file: file name missing')
            ftp_server_pull_file(OBEXRspCode.BAD_REQ, bd_addr=addr)
            ftp.clear_rx_tx_state(addr)
            return

        rsp_code, body = ftp.storage.pull_file(name)
        if rsp_code != OBEXRspCode.SUCCESS:
            ftp_server_pull_file(rsp_code, bd_addr=addr)
            ftp.clear_rx_tx_state(addr)
            return

        hdr = {OBEXHdr.BODY: body}

        is_l2cap = ftp.is_connected(addr=addr, conn_type=defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED)
        if is_l2cap and p[FtpInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED
            if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED_BUT_WAITING

        p[FtpInfo.TX_DATA] = hdr

    if p.get(FtpInfo.SRM_STATE) == FtpSrmState.SRM_ENABLED_BUT_WAITING:
        if p[FtpInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[FtpInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[FtpInfo.SRM_STATE] = FtpSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[FtpInfo.TX_DATA], p[FtpInfo.TX_CNT] = ftp_enc_hdr(
            p[FtpInfo.TX_DATA], p[FtpInfo.MOPL] - 3, p[FtpInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[FtpInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE
        ftp_server_pull_file(rsp_code, buf=encoded_hdr, bd_addr=addr)

        if rsp_code != OBEXRspCode.CONTINUE:
            ftp.clear_rx_tx_state(addr)
            break

        if p.get(FtpInfo.SRM_STATE) != FtpSrmState.SRM_ENABLED:
            break


def _ftp_server_delete_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_delete_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    final, req_hdr = ftp_dec_req(data)

    if not final:
        ftp_server_delete(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        return

    name = req_hdr.get(OBEXHdr.NAME)
    if not name:
        ftp_server_delete(OBEXRspCode.BAD_REQ, bd_addr=addr)
        return

    if ftp.storage is None:
        ftp_server_delete(OBEXRspCode.FORBIDDEN, bd_addr=addr)
        return

    rsp_code = ftp.storage.delete(name)
    ftp_server_delete(rsp_code, bd_addr=addr)


def _ftp_server_rename_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_rename_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    final, req_hdr = ftp_dec_req(data)

    if not final:
        ftp_server_rename(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        return

    src_name = req_hdr.get(OBEXHdr.NAME)
    dst_name = req_hdr.get(OBEXHdr.DEST_NAME)
    if not src_name or not dst_name:
        ftp_server_rename(OBEXRspCode.BAD_REQ, bd_addr=addr)
        return

    if ftp.storage is None:
        ftp_server_rename(OBEXRspCode.FORBIDDEN, bd_addr=addr)
        return

    rsp_code = ftp.storage.rename(src_name, dst_name)
    ftp_server_rename(rsp_code, bd_addr=addr)


def _ftp_server_copy_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_copy_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    final, req_hdr = ftp_dec_req(data)

    if not final:
        ftp_server_copy(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        return

    src_name = req_hdr.get(OBEXHdr.NAME)
    dst_name = req_hdr.get(OBEXHdr.DEST_NAME)
    if not src_name or not dst_name:
        ftp_server_copy(OBEXRspCode.BAD_REQ, bd_addr=addr)
        return

    if ftp.storage is None:
        ftp_server_copy(OBEXRspCode.FORBIDDEN, bd_addr=addr)
        return

    rsp_code = ftp.storage.copy(src_name, dst_name)
    ftp_server_copy(rsp_code, bd_addr=addr)


def _ftp_server_set_permission_ev(ftp, data, data_len):
    logging.debug('%s %r', _ftp_server_set_permission_ev.__name__, data)
    addr, data = ftp_ev_decode_addr(data)
    final, req_hdr = ftp_dec_req(data)

    if not final:
        ftp_server_set_permission(OBEXRspCode.NOT_IMPLEMENTED, bd_addr=addr)
        return

    name = req_hdr.get(OBEXHdr.NAME)
    perms = req_hdr.get(OBEXHdr.PERMISSION)
    if not name or perms is None:
        ftp_server_set_permission(OBEXRspCode.BAD_REQ, bd_addr=addr)
        return

    if ftp.storage is None:
        ftp_server_set_permission(OBEXRspCode.FORBIDDEN, bd_addr=addr)
        return

    rsp_code = ftp.storage.set_permissions(name, perms)
    ftp_server_set_permission(rsp_code, bd_addr=addr)


# ---------------------------------------------------------------------------
# Internal handler dispatch table (used by FtpEventHandler._handle_event)
# ---------------------------------------------------------------------------

FTP_EV_HANDLERS = {
    defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED:     _ftp_client_rfcomm_connected_ev,
    defs.BTP_FTP_EV_CLIENT_RFCOMM_DISCONNECTED:  _ftp_client_rfcomm_disconnected_ev,
    defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED:      _ftp_client_l2cap_connected_ev,
    defs.BTP_FTP_EV_CLIENT_L2CAP_DISCONNECTED:   _ftp_client_l2cap_disconnected_ev,
    defs.BTP_FTP_EV_CLIENT_CONNECT:              _ftp_client_connect_ev,
    defs.BTP_FTP_EV_CLIENT_DISCONNECT:           _ftp_client_disconnect_ev,
    defs.BTP_FTP_EV_CLIENT_ABORT:                _ftp_client_abort_ev,
    defs.BTP_FTP_EV_CLIENT_SET_FOLDER:           _ftp_client_set_folder_ev,
    defs.BTP_FTP_EV_CLIENT_PULL_FOLDER_LISTING:  _ftp_client_pull_folder_listing_ev,
    defs.BTP_FTP_EV_CLIENT_PUSH_FILE:            _ftp_client_push_file_ev,
    defs.BTP_FTP_EV_CLIENT_PULL_FILE:            _ftp_client_pull_file_ev,
    defs.BTP_FTP_EV_CLIENT_DELETE:               _ftp_client_delete_ev,
    defs.BTP_FTP_EV_CLIENT_RENAME:               _ftp_client_rename_ev,
    defs.BTP_FTP_EV_CLIENT_COPY:                 _ftp_client_copy_ev,
    defs.BTP_FTP_EV_CLIENT_SET_PERMISSION:       _ftp_client_set_permission_ev,
    defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED:     _ftp_server_rfcomm_connected_ev,
    defs.BTP_FTP_EV_SERVER_RFCOMM_DISCONNECTED:  _ftp_server_rfcomm_disconnected_ev,
    defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED:      _ftp_server_l2cap_connected_ev,
    defs.BTP_FTP_EV_SERVER_L2CAP_DISCONNECTED:   _ftp_server_l2cap_disconnected_ev,
    defs.BTP_FTP_EV_SERVER_CONNECT:              _ftp_server_connect_ev,
    defs.BTP_FTP_EV_SERVER_DISCONNECT:           _ftp_server_disconnect_ev,
    defs.BTP_FTP_EV_SERVER_ABORT:                _ftp_server_abort_ev,
    defs.BTP_FTP_EV_SERVER_SET_FOLDER:           _ftp_server_set_folder_ev,
    defs.BTP_FTP_EV_SERVER_PULL_FOLDER_LISTING:  _ftp_server_pull_folder_listing_ev,
    defs.BTP_FTP_EV_SERVER_PUSH_FILE:            _ftp_server_push_file_ev,
    defs.BTP_FTP_EV_SERVER_PULL_FILE:            _ftp_server_pull_file_ev,
    defs.BTP_FTP_EV_SERVER_DELETE:               _ftp_server_delete_ev,
    defs.BTP_FTP_EV_SERVER_RENAME:               _ftp_server_rename_ev,
    defs.BTP_FTP_EV_SERVER_COPY:                 _ftp_server_copy_ev,
    defs.BTP_FTP_EV_SERVER_SET_PERMISSION:       _ftp_server_set_permission_ev,
}


# ---------------------------------------------------------------------------
# FTP event handler (threaded, MAP-style)
# ---------------------------------------------------------------------------

class FtpEventHandler:
    """FTP event handler that processes events in a separate thread."""

    def __init__(self, ftp_instance):
        self.ftp = ftp_instance
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.worker_thread.start()
            logging.debug('FTP event handler started')

    def stop(self):
        if self.running:
            self.running = False
            self.event_queue.put(None)
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logging.debug('FTP event handler stopped')

    def enqueue_event(self, event_id, data, data_len):
        self.event_queue.put((event_id, data, data_len))

    def _process_events(self):
        while self.running:
            try:
                item = self.event_queue.get(timeout=1)
                if item is None:
                    break
                event_id, data, data_len = item
                self._handle_event(event_id, data, data_len)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error('Error processing FTP event: %s', e, exc_info=True)

    def _handle_event(self, event_id, data, data_len):
        handler = FTP_EV_HANDLERS.get(event_id)
        if handler:
            try:
                handler(self.ftp, data, data_len)
            except Exception as e:
                logging.error('Error in FTP event handler %s: %s', handler.__name__, e, exc_info=True)
        else:
            logging.warning('No handler for FTP event 0x%02x', event_id)


# ---------------------------------------------------------------------------
# Public ftp_*_ev functions (called by btp.py event routing, enqueue to worker)
# ---------------------------------------------------------------------------

def ftp_client_rfcomm_connected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED, data, data_len)


def ftp_client_rfcomm_disconnected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_RFCOMM_DISCONNECTED, data, data_len)


def ftp_client_l2cap_connected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED, data, data_len)


def ftp_client_l2cap_disconnected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_L2CAP_DISCONNECTED, data, data_len)


def ftp_client_connect_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_CONNECT, data, data_len)


def ftp_client_disconnect_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_DISCONNECT, data, data_len)


def ftp_client_abort_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_ABORT, data, data_len)


def ftp_client_set_folder_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_SET_FOLDER, data, data_len)


def ftp_client_pull_folder_listing_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_PULL_FOLDER_LISTING, data, data_len)


def ftp_client_push_file_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_PUSH_FILE, data, data_len)


def ftp_client_pull_file_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_PULL_FILE, data, data_len)


def ftp_client_delete_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_DELETE, data, data_len)


def ftp_client_rename_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_RENAME, data, data_len)


def ftp_client_copy_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_COPY, data, data_len)


def ftp_client_set_permission_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_CLIENT_SET_PERMISSION, data, data_len)


def ftp_server_rfcomm_connected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED, data, data_len)


def ftp_server_rfcomm_disconnected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_RFCOMM_DISCONNECTED, data, data_len)


def ftp_server_l2cap_connected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED, data, data_len)


def ftp_server_l2cap_disconnected_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_L2CAP_DISCONNECTED, data, data_len)


def ftp_server_connect_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_CONNECT, data, data_len)


def ftp_server_disconnect_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_DISCONNECT, data, data_len)


def ftp_server_abort_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_ABORT, data, data_len)


def ftp_server_set_folder_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_SET_FOLDER, data, data_len)


def ftp_server_pull_folder_listing_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_PULL_FOLDER_LISTING, data, data_len)


def ftp_server_push_file_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_PUSH_FILE, data, data_len)


def ftp_server_pull_file_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_PULL_FILE, data, data_len)


def ftp_server_delete_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_DELETE, data, data_len)


def ftp_server_rename_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_RENAME, data, data_len)


def ftp_server_copy_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_COPY, data, data_len)


def ftp_server_set_permission_ev(ftp, data, data_len):
    ftp.event_handler.enqueue_event(defs.BTP_FTP_EV_SERVER_SET_PERMISSION, data, data_len)


# Public FTP_EV dict (used by btp.py event routing)
FTP_EV = {
    # FTP Client events
    defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED:    ftp_client_rfcomm_connected_ev,
    defs.BTP_FTP_EV_CLIENT_RFCOMM_DISCONNECTED: ftp_client_rfcomm_disconnected_ev,
    defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED:     ftp_client_l2cap_connected_ev,
    defs.BTP_FTP_EV_CLIENT_L2CAP_DISCONNECTED:  ftp_client_l2cap_disconnected_ev,
    defs.BTP_FTP_EV_CLIENT_CONNECT:             ftp_client_connect_ev,
    defs.BTP_FTP_EV_CLIENT_DISCONNECT:          ftp_client_disconnect_ev,
    defs.BTP_FTP_EV_CLIENT_ABORT:               ftp_client_abort_ev,
    defs.BTP_FTP_EV_CLIENT_SET_FOLDER:          ftp_client_set_folder_ev,
    defs.BTP_FTP_EV_CLIENT_PULL_FOLDER_LISTING: ftp_client_pull_folder_listing_ev,
    defs.BTP_FTP_EV_CLIENT_PUSH_FILE:           ftp_client_push_file_ev,
    defs.BTP_FTP_EV_CLIENT_PULL_FILE:           ftp_client_pull_file_ev,
    defs.BTP_FTP_EV_CLIENT_DELETE:              ftp_client_delete_ev,
    defs.BTP_FTP_EV_CLIENT_RENAME:              ftp_client_rename_ev,
    defs.BTP_FTP_EV_CLIENT_COPY:                ftp_client_copy_ev,
    defs.BTP_FTP_EV_CLIENT_SET_PERMISSION:      ftp_client_set_permission_ev,
    # FTP Server events
    defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED:    ftp_server_rfcomm_connected_ev,
    defs.BTP_FTP_EV_SERVER_RFCOMM_DISCONNECTED: ftp_server_rfcomm_disconnected_ev,
    defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED:     ftp_server_l2cap_connected_ev,
    defs.BTP_FTP_EV_SERVER_L2CAP_DISCONNECTED:  ftp_server_l2cap_disconnected_ev,
    defs.BTP_FTP_EV_SERVER_CONNECT:             ftp_server_connect_ev,
    defs.BTP_FTP_EV_SERVER_DISCONNECT:          ftp_server_disconnect_ev,
    defs.BTP_FTP_EV_SERVER_ABORT:               ftp_server_abort_ev,
    defs.BTP_FTP_EV_SERVER_SET_FOLDER:          ftp_server_set_folder_ev,
    defs.BTP_FTP_EV_SERVER_PULL_FOLDER_LISTING: ftp_server_pull_folder_listing_ev,
    defs.BTP_FTP_EV_SERVER_PUSH_FILE:           ftp_server_push_file_ev,
    defs.BTP_FTP_EV_SERVER_PULL_FILE:           ftp_server_pull_file_ev,
    defs.BTP_FTP_EV_SERVER_DELETE:              ftp_server_delete_ev,
    defs.BTP_FTP_EV_SERVER_RENAME:              ftp_server_rename_ev,
    defs.BTP_FTP_EV_SERVER_COPY:                ftp_server_copy_ev,
    defs.BTP_FTP_EV_SERVER_SET_PERMISSION:      ftp_server_set_permission_ev,
}
