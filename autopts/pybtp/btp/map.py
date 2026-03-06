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

import binascii
import logging
import queue
import struct
import threading
from datetime import datetime

from autopts.ptsprojects.stack import (
    MAP_FILLER_BYTE,
    MAP_MANDATORY_SUPPORTED_FEATURES,
    MAP_MCE_SUPPORTED_FEATURES,
    MAP_MSE_SUPPORTED_FEATURES,
    MAPInfo,
    MAPSrmState,
    MAPSupportedFeatures,
    get_stack,
)
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, MAPAppParam, OBEXHdr, OBEXRspCode, addr_str_to_le_bytes

log = logging.debug

MAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_MAP,
                            defs.BTP_MAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    # MAP Client MAS commands
    'mce_mas_rfcomm_connect': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_CONNECT,
                               CONTROLLER_INDEX),
    'mce_mas_rfcomm_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_DISCONNECT,
                                  CONTROLLER_INDEX),
    'mce_mas_l2cap_connect': (defs.BTP_SERVICE_ID_MAP,
                              defs.BTP_MAP_CMD_MCE_MAS_L2CAP_CONNECT,
                              CONTROLLER_INDEX),
    'mce_mas_l2cap_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MCE_MAS_L2CAP_DISCONNECT,
                                 CONTROLLER_INDEX),
    'mce_mas_connect': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MCE_MAS_CONNECT,
                        CONTROLLER_INDEX),
    'mce_mas_disconnect': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MCE_MAS_DISCONNECT,
                           CONTROLLER_INDEX),
    'mce_mas_abort': (defs.BTP_SERVICE_ID_MAP,
                      defs.BTP_MAP_CMD_MCE_MAS_ABORT,
                      CONTROLLER_INDEX),
    'mce_mas_set_folder': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MCE_MAS_SET_FOLDER,
                           CONTROLLER_INDEX),
    'mce_mas_set_ntf_reg': (defs.BTP_SERVICE_ID_MAP,
                            defs.BTP_MAP_CMD_MCE_MAS_SET_NTF_REG,
                            CONTROLLER_INDEX),
    'mce_mas_get_folder_listing': (defs.BTP_SERVICE_ID_MAP,
                                   defs.BTP_MAP_CMD_MCE_MAS_GET_FOLDER_LISTING,
                                   CONTROLLER_INDEX),
    'mce_mas_get_msg_listing': (defs.BTP_SERVICE_ID_MAP,
                                defs.BTP_MAP_CMD_MCE_MAS_GET_MSG_LISTING,
                                CONTROLLER_INDEX),
    'mce_mas_get_msg': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MCE_MAS_GET_MSG,
                        CONTROLLER_INDEX),
    'mce_mas_set_msg_status': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MCE_MAS_SET_MSG_STATUS,
                               CONTROLLER_INDEX),
    'mce_mas_push_msg': (defs.BTP_SERVICE_ID_MAP,
                         defs.BTP_MAP_CMD_MCE_MAS_PUSH_MSG,
                         CONTROLLER_INDEX),
    'mce_mas_update_inbox': (defs.BTP_SERVICE_ID_MAP,
                             defs.BTP_MAP_CMD_MCE_MAS_UPDATE_INBOX,
                             CONTROLLER_INDEX),
    'mce_mas_get_mas_inst_info': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MCE_MAS_GET_MAS_INST_INFO,
                                  CONTROLLER_INDEX),
    'mce_mas_set_owner_status': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MCE_MAS_SET_OWNER_STATUS,
                                 CONTROLLER_INDEX),
    'mce_mas_get_owner_status': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MCE_MAS_GET_OWNER_STATUS,
                                 CONTROLLER_INDEX),
    'mce_mas_get_convo_listing': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MCE_MAS_GET_CONVO_LISTING,
                                  CONTROLLER_INDEX),
    'mce_mas_set_ntf_filter': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MCE_MAS_SET_NTF_FILTER,
                               CONTROLLER_INDEX),
    # MAP Client MNS commands
    'mce_mns_rfcomm_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MCE_MNS_RFCOMM_DISCONNECT,
                                  CONTROLLER_INDEX),
    'mce_mns_l2cap_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MCE_MNS_L2CAP_DISCONNECT,
                                 CONTROLLER_INDEX),
    'mce_mns_connect': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MCE_MNS_CONNECT,
                        CONTROLLER_INDEX),
    'mce_mns_disconnect': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MCE_MNS_DISCONNECT,
                           CONTROLLER_INDEX),
    'mce_mns_abort': (defs.BTP_SERVICE_ID_MAP,
                      defs.BTP_MAP_CMD_MCE_MNS_ABORT,
                      CONTROLLER_INDEX),
    'mce_mns_send_event': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MCE_MNS_SEND_EVENT,
                           CONTROLLER_INDEX),
    # MAP Server MAS commands
    'mse_mas_rfcomm_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MSE_MAS_RFCOMM_DISCONNECT,
                                  CONTROLLER_INDEX),
    'mse_mas_l2cap_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MSE_MAS_L2CAP_DISCONNECT,
                                 CONTROLLER_INDEX),
    'mse_mas_connect': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MSE_MAS_CONNECT,
                        CONTROLLER_INDEX),
    'mse_mas_disconnect': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MSE_MAS_DISCONNECT,
                           CONTROLLER_INDEX),
    'mse_mas_abort': (defs.BTP_SERVICE_ID_MAP,
                      defs.BTP_MAP_CMD_MSE_MAS_ABORT,
                      CONTROLLER_INDEX),
    'mse_mas_set_folder': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MSE_MAS_SET_FOLDER,
                           CONTROLLER_INDEX),
    'mse_mas_set_ntf_reg': (defs.BTP_SERVICE_ID_MAP,
                            defs.BTP_MAP_CMD_MSE_MAS_SET_NTF_REG,
                            CONTROLLER_INDEX),
    'mse_mas_get_folder_listing': (defs.BTP_SERVICE_ID_MAP,
                                   defs.BTP_MAP_CMD_MSE_MAS_GET_FOLDER_LISTING,
                                   CONTROLLER_INDEX),
    'mse_mas_get_msg_listing': (defs.BTP_SERVICE_ID_MAP,
                                defs.BTP_MAP_CMD_MSE_MAS_GET_MSG_LISTING,
                                CONTROLLER_INDEX),
    'mse_mas_get_msg': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MSE_MAS_GET_MSG,
                        CONTROLLER_INDEX),
    'mse_mas_set_msg_status': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MSE_MAS_SET_MSG_STATUS,
                               CONTROLLER_INDEX),
    'mse_mas_push_msg': (defs.BTP_SERVICE_ID_MAP,
                         defs.BTP_MAP_CMD_MSE_MAS_PUSH_MSG,
                         CONTROLLER_INDEX),
    'mse_mas_update_inbox': (defs.BTP_SERVICE_ID_MAP,
                             defs.BTP_MAP_CMD_MSE_MAS_UPDATE_INBOX,
                             CONTROLLER_INDEX),
    'mse_mas_get_mas_inst_info': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MSE_MAS_GET_MAS_INST_INFO,
                                  CONTROLLER_INDEX),
    'mse_mas_set_owner_status': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MSE_MAS_SET_OWNER_STATUS,
                                 CONTROLLER_INDEX),
    'mse_mas_get_owner_status': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MSE_MAS_GET_OWNER_STATUS,
                                 CONTROLLER_INDEX),
    'mse_mas_get_convo_listing': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MSE_MAS_GET_CONVO_LISTING,
                                  CONTROLLER_INDEX),
    'mse_mas_set_ntf_filter': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MSE_MAS_SET_NTF_FILTER,
                               CONTROLLER_INDEX),
    # MAP Server MNS commands
    'mse_mns_rfcomm_connect': (defs.BTP_SERVICE_ID_MAP,
                               defs.BTP_MAP_CMD_MSE_MNS_RFCOMM_CONNECT,
                               CONTROLLER_INDEX),
    'mse_mns_rfcomm_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                  defs.BTP_MAP_CMD_MSE_MNS_RFCOMM_DISCONNECT,
                                  CONTROLLER_INDEX),
    'mse_mns_l2cap_connect': (defs.BTP_SERVICE_ID_MAP,
                              defs.BTP_MAP_CMD_MSE_MNS_L2CAP_CONNECT,
                              CONTROLLER_INDEX),
    'mse_mns_l2cap_disconnect': (defs.BTP_SERVICE_ID_MAP,
                                 defs.BTP_MAP_CMD_MSE_MNS_L2CAP_DISCONNECT,
                                 CONTROLLER_INDEX),
    'mse_mns_connect': (defs.BTP_SERVICE_ID_MAP,
                        defs.BTP_MAP_CMD_MSE_MNS_CONNECT,
                        CONTROLLER_INDEX),
    'mse_mns_disconnect': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MSE_MNS_DISCONNECT,
                           CONTROLLER_INDEX),
    'mse_mns_abort': (defs.BTP_SERVICE_ID_MAP,
                      defs.BTP_MAP_CMD_MSE_MNS_ABORT,
                      CONTROLLER_INDEX),
    'mse_mns_send_event': (defs.BTP_SERVICE_ID_MAP,
                           defs.BTP_MAP_CMD_MSE_MNS_SEND_EVENT,
                           CONTROLLER_INDEX),
    'sdp_discover': (defs.BTP_SERVICE_ID_MAP,
                     defs.BTP_MAP_CMD_SDP_DISCOVER,
                     CONTROLLER_INDEX),
}


def map_is_connected(conn_type, instance_id=None, bd_addr=None):
    stack = get_stack()
    return stack.map.is_connected(pts_addr_get(bd_addr), conn_type, instance_id)


def map_wait_for_connection(conn_type, instance_id=None, bd_addr=None, timeout=5):
    stack = get_stack()
    return stack.map.wait_for_connection(pts_addr_get(bd_addr), conn_type, timeout, instance_id)


def map_wait_for_disconnection(conn_type, instance_id=None, bd_addr=None, timeout=5):
    stack = get_stack()
    return stack.map.wait_for_disconnection(pts_addr_get(bd_addr), conn_type, timeout, instance_id)


def map_rx_data_get(ev, instance_id=None, bd_addr=None, timeout=60):
    stack = get_stack()
    return stack.map.rx_data_get(pts_addr_get(bd_addr), ev, timeout, instance_id)


def map_set_info(key, value, instance_id=None, bd_addr=None):
    stack = get_stack()
    return stack.map.set_info(pts_addr_get(bd_addr), key, value, instance_id)


def map_get_info(key, instance_id=None, bd_addr=None):
    stack = get_stack()
    return stack.map.get_info(pts_addr_get(bd_addr), key, instance_id)


def map_dec_app_param(data, data_len):
    err = False
    dct = {}
    offset = 0

    while offset < data_len:
        tag, tag_len = struct.unpack_from("<BB", data, offset)
        offset += struct.calcsize("<BB")

        if tag_len + offset > data_len:
            err = True
            break

        if tag_len == 1:
            dct[tag] = struct.unpack_from("<B", data, offset)[0]
        elif tag_len == 2:
            dct[tag] = struct.unpack_from(">H", data, offset)[0]
        elif tag_len == 4:
            dct[tag] = struct.unpack_from(">I", data, offset)[0]
        else:
            dct[tag] = struct.unpack_from(f"<{tag_len}s", data, offset)[0].decode('utf-8')
        offset += tag_len

    return err, dct


def map_dec_hdr(dct, data, data_len):
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
        elif hi == OBEXHdr.CONN_ID:
            dct[hi] = struct.unpack_from('>I', data, offset)[0]
        elif hi == OBEXHdr.NAME:
            if hv_len > 0:
                dct[hi] = struct.unpack_from(f'{hv_len}s', data, offset)[0].decode('utf-16-be').rstrip('\x00')
            else:
                dct[hi] = ''
        elif hi == OBEXHdr.APP_PARAM:
            err, dct[hi] = map_dec_app_param(data[offset:], hv_len)
            if err:
                break
        elif (hi == OBEXHdr.BODY) or (hi == OBEXHdr.END_OF_BODY):
            if OBEXHdr.BODY in dct:
                dct[OBEXHdr.BODY] += struct.unpack_from(f'{hv_len}s', data, offset)[0]
            else:
                dct[OBEXHdr.BODY] = struct.unpack_from(f'{hv_len}s', data, offset)[0]

        offset += hv_len

    return err, dct


def map_enc_app_param(app_param_dict):
    """Encode application parameters dictionary to bytes according to MAP specification"""

    # Define fixed lengths for MAP Application Parameters according to MAP spec
    # Format: tag_id: (length_in_bytes, is_string)
    app_param_map = {
        MAPAppParam.MAX_LIST_COUNT: (2, False),
        MAPAppParam.LIST_START_OFFSET: (2, False),
        MAPAppParam.FILTER_MESSAGE_TYPE: (1, False),
        MAPAppParam.FILTER_PERIOD_BEGIN: (0, True),  # Variable length string
        MAPAppParam.FILTER_PERIOD_END: (0, True),    # Variable length string
        MAPAppParam.FILTER_READ_STATUS: (1, False),
        MAPAppParam.FILTER_RECIPIENT: (0, True),     # Variable length string
        MAPAppParam.FILTER_ORIGINATOR: (0, True),    # Variable length string
        MAPAppParam.FILTER_PRIORITY: (1, False),
        MAPAppParam.ATTACHMENT: (1, False),
        MAPAppParam.TRANSPARENT: (1, False),
        MAPAppParam.RETRY: (1, False),
        MAPAppParam.NEW_MESSAGE: (1, False),
        MAPAppParam.NOTIFICATION_STATUS: (1, False),
        MAPAppParam.MAS_INSTANCE_ID: (1, False),
        MAPAppParam.PARAMETER_MASK: (4, False),
        MAPAppParam.FOLDER_LISTING_SIZE: (2, False),
        MAPAppParam.LISTING_SIZE: (2, False),
        MAPAppParam.SUBJECT_LENGTH: (1, False),
        MAPAppParam.CHARSET: (1, False),
        MAPAppParam.FRACTION_REQUEST: (1, False),
        MAPAppParam.FRACTION_DELIVER: (1, False),
        MAPAppParam.STATUS_INDICATOR: (1, False),
        MAPAppParam.STATUS_VALUE: (1, False),
        MAPAppParam.MSE_TIME: (0, True),             # Variable length string
        MAPAppParam.DATABASE_IDENTIFIER: (0, True),   # Variable length string
        MAPAppParam.CONV_LIST_VER_CNTR: (0, True),   # Variable length string (16 bytes)
        MAPAppParam.PRESENCE_AVAILABILITY: (1, False),
        MAPAppParam.PRESENCE_TEXT: (0, True),        # Variable length string
        MAPAppParam.LAST_ACTIVITY: (0, True),        # Variable length string
        MAPAppParam.FILTER_LAST_ACTIVITY_BEGIN: (0, True),  # Variable length string
        MAPAppParam.FILTER_LAST_ACTIVITY_END: (0, True),    # Variable length string
        MAPAppParam.CHAT_STATE: (1, False),
        MAPAppParam.CONVERSATION_ID: (0, True),      # Variable length string (16 bytes)
        MAPAppParam.FOLDER_VER_CNTR: (0, True),      # Variable length string (16 bytes)
        MAPAppParam.FILTER_MSG_HANDLE: (0, True),    # Variable length string
        MAPAppParam.NOTIFICATION_FILTER_MASK: (4, False),
        MAPAppParam.CONV_PARAMETER_MASK: (4, False),
        MAPAppParam.OWNER_UCI: (0, True),            # Variable length string
        MAPAppParam.EXTENDED_DATA: (0, True),        # Variable length string
        MAPAppParam.MAP_SUPPORTED_FEATURES: (4, False),
        MAPAppParam.MESSAGE_HANDLE: (0, True),       # Variable length string
        MAPAppParam.MODIFY_TEXT: (1, False),
    }

    data = bytearray()

    for tag, value in app_param_dict.items():
        data.append(tag)

        param_info = app_param_map.get(tag)

        if param_info is None:
            # Unknown parameter
            if isinstance(value, int):
                if value <= 0xFF:
                    data.append(1)
                    data.extend(struct.pack('<B', value))
                elif value <= 0xFFFF:
                    data.append(2)
                    data.extend(struct.pack('>H', value))
                else:
                    data.append(4)
                    data.extend(struct.pack('>I', value))
            else:
                value_bytes = value.encode('utf-8') if isinstance(value, str) else value
                data.append(len(value_bytes))
                data.extend(value_bytes)
            continue

        fixed_length, is_string = param_info

        if is_string:
            # Variable length string parameter
            value_bytes = value.encode('utf-8') if isinstance(value, str) else value
            data.append(len(value_bytes))
            data.extend(value_bytes)
        else:
            # Fixed length integer parameter
            data.append(fixed_length)
            if fixed_length == 1:
                data.extend(struct.pack('>B', value))
            elif fixed_length == 2:
                data.extend(struct.pack('>H', value))
            elif fixed_length == 4:
                data.extend(struct.pack('>I', value))
            else:
                raise ValueError(f"Unsupported fixed length {fixed_length} for tag {tag}")

    return bytes(data)


def map_enc_hdr(hdr_dict, remaining_space, body_offset=0):
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
        OBEXHdr.CONN_ID,
        OBEXHdr.SRM,
        OBEXHdr.SRMP,
        OBEXHdr.TYPE,
        OBEXHdr.NAME,
        OBEXHdr.APP_PARAM,
        OBEXHdr.BODY,
    ]

    # Track which headers have been processed
    processed_headers = set()

    for hdr_id in header_priority:
        if hdr_id not in hdr_dict:
            continue

        hdr_value = hdr_dict[hdr_id]
        hdr_bytes = bytearray()

        if hdr_id == OBEXHdr.CONN_ID:
            hdr_bytes = struct.pack('>B', hdr_id) + struct.pack('>I', hdr_value)
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
        elif hdr_id == OBEXHdr.NAME:
            name_bytes = hdr_value.encode('utf-16-be') if isinstance(hdr_value, str) else hdr_value
            if len(name_bytes) != 0:
                name_bytes += b'\x00\x00'  # Null terminator for UTF-16
            hdr_bytes = struct.pack('>BH', hdr_id, len(name_bytes) + 3) + name_bytes
        elif hdr_id == OBEXHdr.APP_PARAM:
            app_param_bytes = map_enc_app_param(hdr_value)
            hdr_bytes = struct.pack('>BH', hdr_id, len(app_param_bytes) + 3) + app_param_bytes
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


def map_command_rsp_succ(op=None, timeout=20.0):
    logging.debug("%s", map_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_MAP, op)

    return tuple_data


# MAP Client MAS commands
def map_mce_mas_rfcomm_connect(instance_id, channel, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mce_mas_rfcomm_connect.__name__,
                  instance_id, channel, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send(*MAP['mce_mas_rfcomm_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_CONNECT)


def map_mce_mas_rfcomm_disconnect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mas_rfcomm_disconnect.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mce_mas_rfcomm_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_DISCONNECT)


def map_mce_mas_l2cap_connect(instance_id, psm, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mce_mas_l2cap_connect.__name__,
                  instance_id, psm, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('H', psm))

    iutctl.btp_socket.send(*MAP['mce_mas_l2cap_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_L2CAP_CONNECT)


def map_mce_mas_l2cap_disconnect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mas_l2cap_disconnect.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mce_mas_l2cap_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_L2CAP_DISCONNECT)


def map_mce_mas_connect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mas_connect.__name__, instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    stack = get_stack()
    sdp_list = stack.map.rx_sdp_get(bd_addr, timeout=0)
    if sdp_list is None or len(sdp_list) == 0:
        raise BTPError("SDP not found for MAS")

    sdp = next(s for s in sdp_list
        if s.role == 'mas' and s.instance_id == instance_id)

    send_supp_feat = 1 if sdp.supported_features & MAPSupportedFeatures.SUPPORTED_FEATURES_CONNECT_REQ else 0

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', send_supp_feat))

    iutctl.btp_socket.send(*MAP['mce_mas_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_CONNECT)


def map_mce_mas_disconnect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mas_disconnect.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mce_mas_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_DISCONNECT)


def map_mce_mas_abort(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mas_abort.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mce_mas_abort'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_ABORT)


def map_mce_mas_set_folder(instance_id, folder='', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mce_mas_set_folder.__name__,
                  instance_id, folder, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    if folder == '/' or folder == '':
        # Go to root
        flags = 0x02
        folder_name = ''
    elif folder == '..':
        # Go up one level
        flags = 0x03
        folder_name = ''
    elif folder.startswith('../'):
        # Go up one level then navigate to folder
        flags = 0x03
        folder_name = folder[3:]  # Remove '../' prefix
    else:
        # Navigate to folder
        flags = 0x02
        folder_name = folder

    conn_id = map_get_info(MAPInfo.CONN_ID, instance_id, bd_addr)
    mopl = map_get_info(MAPInfo.MOPL, instance_id, bd_addr)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: folder_name
    }

    encoded_hdr, _, _ = map_enc_hdr(hdr, mopl - 5)

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', flags))
    data_ba.extend(struct.pack('H', len(encoded_hdr)))
    data_ba.extend(encoded_hdr)

    iutctl.btp_socket.send(*MAP['mce_mas_set_folder'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_SET_FOLDER)


def map_mce_mas_set_ntf_reg(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_set_ntf_reg.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_set_ntf_reg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_SET_NTF_REG)


def map_mce_mas_get_folder_listing(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_folder_listing.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_folder_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_FOLDER_LISTING)


def map_mce_mas_get_msg_listing(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_msg_listing.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_msg_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_MSG_LISTING)


def map_mce_mas_get_msg(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_msg.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_msg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_MSG)


def map_mce_mas_set_msg_status(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_set_msg_status.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_set_msg_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_SET_MSG_STATUS)


def map_mce_mas_push_msg(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_push_msg.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_push_msg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_PUSH_MSG)


def map_mce_mas_update_inbox(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_update_inbox.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_update_inbox'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_UPDATE_INBOX)


def map_mce_mas_get_mas_inst_info(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_mas_inst_info.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_mas_inst_info'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_MAS_INST_INFO)


def map_mce_mas_set_owner_status(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_set_owner_status.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_set_owner_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_SET_OWNER_STATUS)


def map_mce_mas_get_owner_status(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_owner_status.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_owner_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_OWNER_STATUS)


def map_mce_mas_get_convo_listing(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_get_convo_listing.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_get_convo_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_GET_CONVO_LISTING)


def map_mce_mas_set_ntf_filter(instance_id, final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mce_mas_set_ntf_filter.__name__,
                  instance_id, final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mas_set_ntf_filter'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MAS_SET_NTF_FILTER)


# MAP Client MNS commands
def map_mce_mns_rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mce_mns_rfcomm_disconnect.__name__,
                  bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mce_mns_rfcomm_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_RFCOMM_DISCONNECT)


def map_mce_mns_l2cap_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mce_mns_l2cap_disconnect.__name__,
                  bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mce_mns_l2cap_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_L2CAP_DISCONNECT)


def map_mce_mns_connect(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mns_connect.__name__,
                  rsp_code, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mce_mns_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_CONNECT)


def map_mce_mns_disconnect(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mns_disconnect.__name__,
                  rsp_code, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mce_mns_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_DISCONNECT)


def map_mce_mns_abort(rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mce_mns_abort.__name__,
                  rsp_code, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mce_mns_abort'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_ABORT)


def map_mce_mns_send_event(rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mce_mns_send_event.__name__,
                  rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mce_mns_send_event'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MCE_MNS_SEND_EVENT)


# MAP Server MAS commands
def map_mse_mas_rfcomm_disconnect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mse_mas_rfcomm_disconnect.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mse_mas_rfcomm_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_RFCOMM_DISCONNECT)


def map_mse_mas_l2cap_disconnect(instance_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mse_mas_l2cap_disconnect.__name__,
                  instance_id, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))

    iutctl.btp_socket.send(*MAP['mse_mas_l2cap_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_L2CAP_DISCONNECT)


def map_mse_mas_connect(instance_id, rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mse_mas_connect.__name__,
                  instance_id, rsp_code, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mse_mas_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_CONNECT)


def map_mse_mas_disconnect(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_disconnect.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mse_mas_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_DISCONNECT)


def map_mse_mas_abort(instance_id, rsp_code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mse_mas_abort.__name__,
                  instance_id, rsp_code, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send(*MAP['mse_mas_abort'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_ABORT)


def map_mse_mas_set_folder(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_set_folder.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_set_folder'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_SET_FOLDER)


def map_mse_mas_set_ntf_reg(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_set_ntf_reg.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_set_ntf_reg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_SET_NTF_REG)


def map_mse_mas_get_folder_listing(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_folder_listing.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_folder_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_FOLDER_LISTING)


def map_mse_mas_get_msg_listing(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_msg_listing.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_msg_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_MSG_LISTING)


def map_mse_mas_get_msg(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_msg.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_msg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_MSG)


def map_mse_mas_set_msg_status(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_set_msg_status.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_set_msg_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_SET_MSG_STATUS)


def map_mse_mas_push_msg(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_push_msg.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_push_msg'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_PUSH_MSG)


def map_mse_mas_update_inbox(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_update_inbox.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_update_inbox'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_UPDATE_INBOX)


def map_mse_mas_get_mas_inst_info(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_mas_inst_info.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_mas_inst_info'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_MAS_INST_INFO)


def map_mse_mas_set_owner_status(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_set_owner_status.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_set_owner_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_SET_OWNER_STATUS)


def map_mse_mas_get_owner_status(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_owner_status.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_owner_status'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_OWNER_STATUS)


def map_mse_mas_get_convo_listing(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_get_convo_listing.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_get_convo_listing'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_GET_CONVO_LISTING)


def map_mse_mas_set_ntf_filter(instance_id, rsp_code, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", map_mse_mas_set_ntf_filter.__name__,
                  instance_id, rsp_code, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', instance_id))
    data_ba.extend(struct.pack('B', rsp_code))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mas_set_ntf_filter'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MAS_SET_NTF_FILTER)


# MAP Server MNS commands
def map_mse_mns_rfcomm_connect(channel, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mse_mns_rfcomm_connect.__name__,
                  channel, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send(*MAP['mse_mns_rfcomm_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_RFCOMM_CONNECT)


def map_mse_mns_rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mse_mns_rfcomm_disconnect.__name__,
                  bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mse_mns_rfcomm_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_RFCOMM_DISCONNECT)


def map_mse_mns_l2cap_connect(psm, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_mse_mns_l2cap_connect.__name__,
                  psm, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))

    iutctl.btp_socket.send(*MAP['mse_mns_l2cap_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_L2CAP_CONNECT)


def map_mse_mns_l2cap_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mse_mns_l2cap_disconnect.__name__,
                  bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mse_mns_l2cap_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_L2CAP_DISCONNECT)


def map_mse_mns_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mse_mns_connect.__name__, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mse_mns_connect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_CONNECT)


def map_mse_mns_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mse_mns_disconnect.__name__, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mse_mns_disconnect'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_DISCONNECT)


def map_mse_mns_abort(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r", map_mse_mns_abort.__name__, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*MAP['mse_mns_abort'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_ABORT)


def map_mse_mns_send_event(final, buf_data=b'', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", map_mse_mns_send_event.__name__,
                  final, buf_data, bd_addr)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', 1 if final else 0))

    if isinstance(buf_data, str):
        buf_data = bytes.fromhex(buf_data)

    data_ba.extend(struct.pack('<H', len(buf_data)))
    data_ba.extend(buf_data)

    iutctl.btp_socket.send(*MAP['mse_mns_send_event'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_MSE_MNS_SEND_EVENT)


def map_sdp_discover(role='mas', bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", map_sdp_discover.__name__,
                  role, bd_addr)

    iutctl = get_iut()

    if role == 'mas':
        uuid = 0x1132  # Message Access Server Service Class
    else:
        uuid = 0x1133  # Message Notification Server Service Class

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('<H', uuid))

    iutctl.btp_socket.send(*MAP['sdp_discover'], data=data_ba)
    map_command_rsp_succ(defs.BTP_MAP_CMD_SDP_DISCOVER)


# Event handlers
def _map_ev_decode_addr(data):
    hdr = '<B6s'
    hdr_len = struct.calcsize(hdr)
    if len(data) < hdr_len:
        raise BTPError('Invalid data length')

    _, addr = struct.unpack_from(hdr, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    return addr, data[hdr_len:]


def _map_ev_decode_addr_and_id(data):
    addr, data = _map_ev_decode_addr(data)

    hdr = 'B'
    hdr_len = struct.calcsize(hdr)
    if len(data) < hdr_len:
        raise BTPError('Invalid data length')

    instance_id = struct.unpack_from(hdr, data)[0]

    return addr, instance_id, data[hdr_len:]


def _map_decode_rsp(data, dct=None):
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

    map_dec_hdr(dct, data, len(data))
    return rsp_code, dct


def _map_decode_req(data, dct=None):
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

    map_dec_hdr(dct, data, len(data))
    return final, dct


def _map_dec_conn_rsp(data):
    dct = {}

    hdr = '<BBHH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    rsp_code, version, mopl, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    map_dec_hdr(dct, data, len(data))

    return rsp_code, version, mopl, dct


def _map_dec_conn_req(data):
    dct = {}

    hdr = '<BHH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        raise BTPError("Invalid data length")

    version, mopl, buf_len = struct.unpack_from(hdr, data)

    data = data[hdr_size:]
    if len(data) < buf_len:
        raise BTPError("Invalid data length")

    map_dec_hdr(dct, data, len(data))

    return version, mopl, dct


# Internal event handler functions
def _map_mce_mas_rfcomm_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_rfcomm_connected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.default_mce_mas[addr] = instance_id
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, instance_id)


def _map_mce_mas_rfcomm_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_rfcomm_disconnected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MAS_CONNECT, instance_id)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, instance_id)


def _map_mce_mas_l2cap_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_l2cap_connected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.default_mce_mas[addr] = instance_id
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, instance_id)


def _map_mce_mas_l2cap_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_l2cap_disconnected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MAS_CONNECT, instance_id)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, instance_id)


def _map_mce_mas_connect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_connect_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, version, mopl, rsp_hdr = _map_dec_conn_rsp(data)
    if rsp_code != OBEXRspCode.SUCCESS:
        return

    sdp_list = _map.rx_sdp_get(pts_addr_get(), timeout=0)
    if sdp_list is None or len(sdp_list) == 0:
        logging.error("SDP not found for MAS")
        return

    sdp = next(s for s in sdp_list
        if s.role == 'mas' and s.instance_id == instance_id)

    _map.set_info(addr, MAPInfo.CHANNEL, sdp.channel, instance_id)
    _map.set_info(addr, MAPInfo.PSM, sdp.psm, instance_id)
    supported_features = sdp.supported_features & MAP_MCE_SUPPORTED_FEATURES
    if supported_features & MAPSupportedFeatures.UTC_OFFSET_TIMESTAMP_FORMAT:
        _map.set_info(addr, MAPInfo.UTC_OFFSET, True, instance_id)
    _map.set_info(addr, MAPInfo.SUPPORTED_FEATURES, supported_features, instance_id)
    _map.set_info(addr, MAPInfo.MOPL, mopl, instance_id)
    _map.set_info(addr, MAPInfo.CONN_ID, rsp_hdr[OBEXHdr.CONN_ID], instance_id)
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MAS_CONNECT, instance_id)


def _map_mce_mas_disconnect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_disconnect_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    if rsp_code == OBEXRspCode.SUCCESS:
        _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MAS_CONNECT, instance_id)


def _map_mce_mas_abort_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_abort_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.clear_rx_tx_state(addr, instance_id)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_ABORT, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_set_ntf_reg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_set_ntf_reg_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_set_folder_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_set_folder_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_get_folder_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_folder_listing_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_folder_listing(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_get_msg_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_msg_listing_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_msg_listing(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_get_msg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_msg_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_MSG, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_msg(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_set_msg_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_set_msg_status_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_push_msg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_push_msg_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
                del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        is_final = len(p[MAPInfo.TX_DATA]) == 0
        map_mce_mas_push_msg(instance_id, is_final, encoded_hdr)

        if is_final:
            _map.clear_rx_tx_state(addr, instance_id)
            break

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break


def _map_mce_mas_update_inbox_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_update_inbox_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_UPDATE_INBOX, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_get_mas_inst_info_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_mas_inst_info_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_MAS_INST_INFO, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_mas_inst_info(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_set_owner_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_set_owner_status_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_SET_OWNER_STATUS, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mas_get_owner_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_owner_status_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_OWNER_STATUS, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_owner_status(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_get_convo_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_get_convo_listing_ev.__name__, data)

    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
            if p.get(MAPInfo.LOCAL_SRMP):
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, (rsp_code, p[MAPInfo.RX_DATA]), instance_id)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) != 1 and not p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

        if p.get(MAPInfo.LOCAL_SRMP):
            p[MAPInfo.LOCAL_SRMP] -= 1

    if p.get(MAPInfo.SRM_STATE) != MAPSrmState.SRM_ENABLED:
        if p[MAPInfo.LOCAL_SRMP]:
            hdr = {OBEXHdr.SRMP: 1}
            encoded_hdr, _, _ = map_enc_hdr(hdr, p[MAPInfo.MOPL] - 3, 0)
        else:
            encoded_hdr = b''
        map_mce_mas_get_convo_listing(instance_id=instance_id, final=True, buf_data=encoded_hdr)


def _map_mce_mas_set_ntf_filter_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mas_set_ntf_filter_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.rx(addr, defs.BTP_MAP_EV_MCE_MAS_SET_NTF_FILTER, (rsp_code, rsp_hdr), instance_id)


def _map_mce_mns_rfcomm_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_rfcomm_connected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED)


def _map_mce_mns_rfcomm_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_rfcomm_disconnected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MNS_CONNECT)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED)


def _map_mce_mns_l2cap_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_l2cap_connected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED)


def _map_mce_mns_l2cap_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_l2cap_disconnected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MNS_CONNECT)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED)


def _map_mce_mns_connect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_connect_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    version, mopl, rsp_hdr = _map_dec_conn_req(data)
    map_mce_mns_connect(OBEXRspCode.SUCCESS)
    _map.set_info(addr, MAPInfo.MOPL, mopl)
    _map.add_connection(addr, defs.BTP_MAP_EV_MCE_MNS_CONNECT)


def _map_mce_mns_disconnect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_disconnect_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    map_mce_mns_disconnect(OBEXRspCode.SUCCESS)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MCE_MNS_CONNECT)


def _map_mce_mns_abort_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_abort_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    map_mce_mns_abort(OBEXRspCode.SUCCESS)
    _map.clear_rx_tx_state(addr)


def _map_mce_mns_send_event_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mce_mns_send_event_ev.__name__, data)

    addr, data = _map_ev_decode_addr(data)

    conn = _map.conn_lookup(addr)
    if not conn:
        logging.error('Connection not found for addr %s', addr)
        return
    p = conn.conn_info

    tx_hdr = {}
    first = not p[MAPInfo.RX_DATA]

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])

    if first and not final:
        is_l2cap = _map.is_connected(addr=addr, conn_type=defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            tx_hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
                del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    if final:
        rsp_code = OBEXRspCode.SUCCESS
        encoded_hdr, _, _ = map_enc_hdr(tx_hdr, p[MAPInfo.MOPL] - 3)
        map_mce_mns_send_event(rsp_code, encoded_hdr)
        _map.clear_rx_tx_state(addr)
        return

    if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
        encoded_hdr, _, _ = map_enc_hdr(tx_hdr, p[MAPInfo.MOPL] - 3)
        map_mce_mns_send_event(OBEXRspCode.CONTINUE, encoded_hdr)


def terminate_mse_mns_service(addr, _map):
    connections = _map.get_all_connections(addr)
    connected_instances = [conn.instance_id for conn in connections
                        if conn.obex_type == defs.BTP_MAP_EV_MSE_MAS_CONNECT]
    is_connected = _map.is_connected(addr=addr, conn_type=defs.BTP_MAP_EV_MSE_MNS_CONNECT)
    if not connected_instances and is_connected:
        try:
            map_mse_mns_disconnect()
        except Exception:
            logging.warning('MAP MNS disconnect failed')


def _map_mse_mas_rfcomm_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_rfcomm_connected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.default_mse_mas[addr] = instance_id
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED, instance_id)


def _map_mse_mas_rfcomm_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_rfcomm_disconnected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MAS_CONNECT, instance_id)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED, instance_id)
    terminate_mse_mns_service(addr, _map)


def _map_mse_mas_l2cap_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_l2cap_connected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.default_mse_mas[addr] = instance_id
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED, instance_id)


def _map_mse_mas_l2cap_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_l2cap_disconnected_ev.__name__, data)
    addr, instance_id, _ = _map_ev_decode_addr_and_id(data)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MAS_CONNECT, instance_id)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED, instance_id)
    terminate_mse_mns_service(addr, _map)


def _map_mse_mas_connect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_connect_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    version, mopl, rsp_hdr = _map_dec_conn_req(data)
    map_mse_mas_connect(instance_id, OBEXRspCode.SUCCESS)
    supported_features = rsp_hdr.get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.MAP_SUPPORTED_FEATURES,
                                                                MAP_MANDATORY_SUPPORTED_FEATURES)
    _map.storage_init()
    _map.set_info(addr, MAPInfo.MOPL, mopl, instance_id)
    supported_features &= MAP_MSE_SUPPORTED_FEATURES
    if supported_features & MAPSupportedFeatures.UTC_OFFSET_TIMESTAMP_FORMAT:
        _map.set_info(addr, MAPInfo.UTC_OFFSET, True, instance_id)
    _map.set_info(addr, MAPInfo.SUPPORTED_FEATURES, supported_features, instance_id)
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MAS_CONNECT, instance_id)


def _map_mse_mas_disconnect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_disconnect_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    map_mse_mas_disconnect(instance_id, OBEXRspCode.SUCCESS)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MAS_CONNECT, instance_id)
    terminate_mse_mns_service(addr, _map)


def _map_mse_mas_abort_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_abort_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    map_mse_mas_abort(instance_id, OBEXRspCode.SUCCESS)
    _map.clear_rx_tx_state(addr, instance_id)


def _map_mse_mas_set_ntf_reg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_set_ntf_reg_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    final, req_hdr = _map_decode_req(data)
    if not final:
        map_mse_mas_set_ntf_reg(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    notification_status = None
    if req_hdr.get(OBEXHdr.APP_PARAM):
        notification_status = req_hdr[OBEXHdr.APP_PARAM].get(MAPAppParam.NOTIFICATION_STATUS)

    if notification_status is None:
        map_mse_mas_set_ntf_reg(instance_id, OBEXRspCode.BAD_REQ)
        return

    map_mse_mas_set_ntf_reg(instance_id, OBEXRspCode.SUCCESS)

    is_connected = _map.is_connected(addr=addr, conn_type=defs.BTP_MAP_EV_MSE_MNS_CONNECT)
    reg_ntf_cnt = _map.get_info(addr, MAPInfo.REG_NTF_CNT)
    if reg_ntf_cnt is None:
        reg_ntf_cnt = 0

    if notification_status == 1:
        if not is_connected:
            sdp_list = _map.rx_sdp_get(addr=addr, timeout=0)
            if sdp_list is None or len(sdp_list) == 0:
                # Discover MNS service to get L2CAP PSM
                map_sdp_discover(role='mns')
                return

            sdp = next(s for s in sdp_list if s.role == 'mns')
            if sdp.psm != 0:
                map_mse_mns_l2cap_connect(sdp.psm)
            else:
                map_mse_mns_rfcomm_connect(sdp.channel)
        else:
            _map.set_info(addr, MAPInfo.REG_NTF_CNT, reg_ntf_cnt + 1)
    else:
        if reg_ntf_cnt > 0:
            _map.set_info(addr, MAPInfo.REG_NTF_CNT, reg_ntf_cnt - 1)

        if reg_ntf_cnt == 0 and is_connected:
            map_mse_mns_disconnect()


def _map_mse_mas_set_folder_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_set_folder_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    hdr = '<BH'
    hdr_size = struct.calcsize(hdr)
    if len(data) < hdr_size:
        logging.error('Invalid data length')
        map_mse_mas_set_folder(instance_id, OBEXRspCode.BAD_REQ)
        return

    flags, buf_len = struct.unpack_from(hdr, data)
    data = data[hdr_size:]

    req_hdr = {}
    map_dec_hdr(req_hdr, data, len(data))

    folder_name = req_hdr.get(OBEXHdr.NAME)
    if folder_name is None:
        logging.error('Folder name not found in request')
        map_mse_mas_set_folder(instance_id, OBEXRspCode.BAD_REQ)
        return

    success = _map.storage.set_folder(folder_name, flags)

    rsp_code = OBEXRspCode.SUCCESS if success else OBEXRspCode.NOT_FOUND
    map_mse_mas_set_folder(instance_id, rsp_code)


def _map_mse_mas_get_folder_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_folder_listing_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_folder_listing(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        app_param = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})
        max_list_count = app_param.get(MAPAppParam.MAX_LIST_COUNT, 0xFFFF)
        list_start_offset = app_param.get(MAPAppParam.LIST_START_OFFSET, 0)

        body_bytes = _map.storage.build_folder_listing(max_list_count, list_start_offset)

        hdr = {}
        if max_list_count != 0:
            hdr[OBEXHdr.BODY] = body_bytes
        else:
            hdr[OBEXHdr.APP_PARAM] = {}
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.FOLDER_LISTING_SIZE] = 0

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_folder_listing(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_get_msg_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_msg_listing_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_msg_listing(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.NAME) is None:
            map_mse_mas_get_msg_listing(instance_id, OBEXRspCode.BAD_REQ)
            _map.clear_rx_tx_state(addr, instance_id)
            return

        app_param = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})

        # List control parameters
        max_list_count = app_param.get(MAPAppParam.MAX_LIST_COUNT, 0xFFFF)
        list_start_offset = app_param.get(MAPAppParam.LIST_START_OFFSET, 0)

        # Subject and parameter mask
        subject_length = app_param.get(MAPAppParam.SUBJECT_LENGTH, 0xFF)
        parameter_mask = app_param.get(MAPAppParam.PARAMETER_MASK, 0xFFFFFFFF)

        # Filter parameters
        filter_message_type = app_param.get(MAPAppParam.FILTER_MESSAGE_TYPE, 0)
        filter_period_begin = app_param.get(MAPAppParam.FILTER_PERIOD_BEGIN, "")
        filter_period_end = app_param.get(MAPAppParam.FILTER_PERIOD_END, "")
        filter_read_status = app_param.get(MAPAppParam.FILTER_READ_STATUS, 0)
        filter_recipient = app_param.get(MAPAppParam.FILTER_RECIPIENT, "")
        filter_originator = app_param.get(MAPAppParam.FILTER_ORIGINATOR, "")
        filter_priority = app_param.get(MAPAppParam.FILTER_PRIORITY, 0)
        filter_message_handle = app_param.get(MAPAppParam.FILTER_MSG_HANDLE, "")
        conversation_id = app_param.get(MAPAppParam.CONVERSATION_ID, "")

        folder_name = p[MAPInfo.RX_DATA].get(OBEXHdr.NAME, '')
        version_1_1 = p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.MSG_LISTING_FORMAT_VERSION_1_1
        version = "1.1" if version_1_1 else "1.0"

        listing_size, body_bytes = _map.storage.build_message_listing(
            folder=folder_name,
            max_list_count=max_list_count,
            list_start_offset=list_start_offset,
            subject_length=subject_length,
            filter_message_type=filter_message_type,
            filter_period_begin=filter_period_begin,
            filter_period_end=filter_period_end,
            filter_read_status=filter_read_status,
            filter_recipient=filter_recipient,
            filter_originator=filter_originator,
            filter_priority=filter_priority,
            filter_message_handle=filter_message_handle,
            conversation_id=conversation_id,
            parameter_mask=parameter_mask,
            version=version,
            utc_offset=p[MAPInfo.UTC_OFFSET]
        )

        hdr = {OBEXHdr.APP_PARAM: {}}
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.NEW_MESSAGE] = 1
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.MSE_TIME] = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.LISTING_SIZE] = listing_size
        hdr[OBEXHdr.BODY] = body_bytes if max_list_count != 0 else MAP_FILLER_BYTE

        # Add Folder Version Counter and Database Identifier ONLY when max_list_count == 0
        if max_list_count == 0:
            if p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.FOLDER_VERSION_CNTR:
                # Get the target folder path
                if folder_name:
                    current_folder = _map.storage.get_current_folder()
                    target_folder = folder_name if current_folder == "" else f"{current_folder}/{folder_name}"
                else:
                    target_folder = _map.storage.get_current_folder()

                folder_version_counter = _map.storage.get_folder_version_counter(target_folder)
                hdr[OBEXHdr.APP_PARAM][MAPAppParam.FOLDER_VER_CNTR] = folder_version_counter

            if p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.DATABASE_ID:
                database_identifier = _map.storage.get_database_identifier()
                hdr[OBEXHdr.APP_PARAM][MAPAppParam.DATABASE_IDENTIFIER] = database_identifier

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_msg_listing(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_get_msg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_msg_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_msg(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        msg_handle = p[MAPInfo.RX_DATA].get(OBEXHdr.NAME, '')
        version_1_1 = p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1
        version = "1.1" if version_1_1 else "1.0"
        body_bytes = _map.storage.get_message_bmessage(msg_handle, version)

        if body_bytes is None:
            map_mse_mas_get_msg(instance_id, OBEXRspCode.NOT_FOUND)
            _map.clear_rx_tx_state(addr, instance_id)
            return

        hdr = {OBEXHdr.BODY: body_bytes}

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_msg(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_push_msg_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_push_msg_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    tx_hdr = {}
    first = not p[MAPInfo.RX_DATA]

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])

    if first and not final:
        rsp_code = OBEXRspCode.SUCCESS
        folder = p[MAPInfo.RX_DATA].get(OBEXHdr.NAME)

        if folder is None:
            rsp_code = OBEXRspCode.BAD_REQ
        elif not folder:
            rsp_code = OBEXRspCode.SUCCESS
        elif _map.storage.is_valid_folder_name(folder):
            rsp_code = OBEXRspCode.SUCCESS
        else:
            rsp_code = OBEXRspCode.PRECOND_FAILED

        # Extract application parameters
        app_param = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})

        # Extract parameters for push_message
        message_handle = app_param.get(MAPAppParam.MESSAGE_HANDLE, "")
        attachment = app_param.get(MAPAppParam.ATTACHMENT, None)
        modify_text = app_param.get(MAPAppParam.MODIFY_TEXT, None)

        # Validate message forwarding parameters
        if message_handle:
            if not _map.storage.get_message(message_handle):
                rsp_code = OBEXRspCode.NOT_FOUND
            if attachment is None or modify_text is None:
                rsp_code = OBEXRspCode.BAD_REQ

        if rsp_code != OBEXRspCode.SUCCESS:
            map_mse_mas_push_msg(instance_id, rsp_code)
            _map.clear_rx_tx_state(addr, instance_id)
            return

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            tx_hdr[OBEXHdr.SRM] = 1

    if final:
        # Extract application parameters
        app_param = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})

        # Extract parameters for push_message
        transparent = app_param.get(MAPAppParam.TRANSPARENT, 0) == 1
        charset = app_param.get(MAPAppParam.CHARSET, 1)
        retry = app_param.get(MAPAppParam.RETRY, 0) == 1
        conversation_id = app_param.get(MAPAppParam.CONVERSATION_ID, "")
        message_handle = app_param.get(MAPAppParam.MESSAGE_HANDLE, "")
        attachment = app_param.get(MAPAppParam.ATTACHMENT, None)
        modify_text = app_param.get(MAPAppParam.MODIFY_TEXT, None)

        # Get folder name and body
        folder = p[MAPInfo.RX_DATA].get(OBEXHdr.NAME, "")
        bmessage = p[MAPInfo.RX_DATA].get(OBEXHdr.BODY)

        # Call storage push_message with all parameters
        msg_handle, success = _map.storage.push_message(
            bmessage=bmessage,
            folder=folder,
            transparent=transparent,
            retry=retry,
            charset=charset,
            conversation_id=conversation_id,
            message_handle=message_handle,
            attachment=attachment,
            modify_text=modify_text
        )

        if success:
            rsp_code = OBEXRspCode.SUCCESS
            tx_hdr[OBEXHdr.NAME] = msg_handle
        else:
            rsp_code = OBEXRspCode.INT_SERVER_ERR
            tx_hdr = {}

        encoded_hdr, _, _ = map_enc_hdr(tx_hdr, p[MAPInfo.MOPL] - 3)
        map_mse_mas_push_msg(instance_id, rsp_code, encoded_hdr)
        _map.clear_rx_tx_state(addr, instance_id)
        return

    if p[MAPInfo.LOCAL_SRMP]:
        tx_hdr[OBEXHdr.SRMP] = 1

    if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
        encoded_hdr, _, _ = map_enc_hdr(tx_hdr, p[MAPInfo.MOPL] - 3)
        map_mse_mas_push_msg(instance_id, OBEXRspCode.CONTINUE, encoded_hdr)

    if tx_hdr.get(OBEXHdr.SRM, 0) == 1 and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
        del p[MAPInfo.RX_DATA][OBEXHdr.SRM]
        p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
        if p[MAPInfo.LOCAL_SRMP]:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.LOCAL_SRMP]:
            p[MAPInfo.LOCAL_SRMP] -= 1
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED


def _map_mse_mas_set_msg_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_set_msg_status_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_set_msg_status(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    msg_handle = p[MAPInfo.RX_DATA].get(OBEXHdr.NAME, '')
    status_indicator = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.STATUS_INDICATOR, None)
    status_value = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.STATUS_VALUE, None)

    success = _map.storage.set_message_status(msg_handle, status_indicator, status_value)

    rsp_code = OBEXRspCode.SUCCESS if success else OBEXRspCode.NOT_FOUND
    map_mse_mas_set_msg_status(instance_id, rsp_code)
    _map.clear_rx_tx_state(addr, instance_id)


def _map_mse_mas_update_inbox_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_update_inbox_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)
    final, req_hdr = _map_decode_req(data)
    if not final:
        map_mse_mas_update_inbox(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return
    map_mse_mas_update_inbox(instance_id, OBEXRspCode.SUCCESS)


def _map_mse_mas_get_mas_inst_info_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_mas_inst_info_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_mas_inst_info(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        mas_inst_id = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.MAS_INSTANCE_ID, None)
        connections = _map.get_all_connections(addr)
        connected_instances = [conn.instance_id for conn in connections
                            if conn.obex_type == defs.BTP_MAP_EV_MSE_MAS_CONNECT]

        if mas_inst_id not in connected_instances:
            map_mse_mas_get_mas_inst_info(instance_id, OBEXRspCode.NOT_FOUND)
            _map.clear_rx_tx_state(addr, instance_id)
            return

        body_bytes = f"MAP MAS Instance Information {mas_inst_id}".encode()

        hdr = {OBEXHdr.BODY: body_bytes}

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_mas_inst_info(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_set_owner_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_set_owner_status_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    final, req_hdr = _map_decode_req(data)
    if not final:
        map_mse_mas_set_owner_status(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    app_params = req_hdr.get(OBEXHdr.APP_PARAM, {})
    conversation_id = app_params.get(MAPAppParam.CONVERSATION_ID, "")
    presence_availability = app_params.get(MAPAppParam.PRESENCE_AVAILABILITY, None)
    presence_text = app_params.get(MAPAppParam.PRESENCE_TEXT, None)
    last_activity = app_params.get(MAPAppParam.LAST_ACTIVITY, None)
    chat_state = app_params.get(MAPAppParam.CHAT_STATE, None)

    success = _map.storage.set_owner_status(conversation_id, presence_availability,
                                            presence_text, last_activity, chat_state)

    rsp_code = OBEXRspCode.SUCCESS if success else OBEXRspCode.INT_SERVER_ERR
    map_mse_mas_set_owner_status(instance_id, rsp_code)


def _map_mse_mas_get_owner_status_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_owner_status_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_owner_status(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        conversation_id = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.CONVERSATION_ID, "")
        owner_status = _map.storage.get_owner_status(conversation_id)

        if owner_status is None:
            map_mse_mas_get_owner_status(instance_id, OBEXRspCode.NOT_FOUND)
            _map.clear_rx_tx_state(addr, instance_id)
            return

        hdr = {OBEXHdr.APP_PARAM: {}}
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.PRESENCE_AVAILABILITY] = owner_status.presence_availability
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.PRESENCE_TEXT] = owner_status.presence_text
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.LAST_ACTIVITY] = owner_status.last_activity
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.CHAT_STATE] = owner_status.chat_state
        hdr[OBEXHdr.BODY] = MAP_FILLER_BYTE

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_owner_status(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_get_convo_listing_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_get_convo_listing_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    conn = _map.conn_lookup(addr, instance_id)
    if not conn:
        logging.error('Connection not found for addr %s id %r', addr, instance_id)
        return
    p = conn.conn_info

    final, p[MAPInfo.RX_DATA] = _map_decode_req(data, p[MAPInfo.RX_DATA])
    if not final:
        _map.clear_rx_tx_state(addr, instance_id)
        map_mse_mas_get_convo_listing(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    if p[MAPInfo.TX_CNT] == 0:
        app_param = p[MAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})

        # List control parameters
        max_list_count = app_param.get(MAPAppParam.MAX_LIST_COUNT, 0xFFFF)
        list_start_offset = app_param.get(MAPAppParam.LIST_START_OFFSET, 0)
        filter_read_status = app_param.get(MAPAppParam.FILTER_READ_STATUS, 0)
        filter_recipient = app_param.get(MAPAppParam.FILTER_RECIPIENT, "")
        filter_last_activity_begin = app_param.get(MAPAppParam.FILTER_LAST_ACTIVITY_BEGIN, "")
        filter_last_activity_end = app_param.get(MAPAppParam.FILTER_LAST_ACTIVITY_END, "")
        conversation_id = app_param.get(MAPAppParam.CONVERSATION_ID, "")
        conv_parameter_mask = app_param.get(MAPAppParam.CONV_PARAMETER_MASK, 0xFFFFFFFF)

        listing_size, body_bytes = _map.storage.build_conversation_listing(
            max_list_count=max_list_count,
            list_start_offset=list_start_offset,
            filter_read_status=filter_read_status,
            filter_recipient=filter_recipient,
            filter_last_activity_begin=filter_last_activity_begin,
            filter_last_activity_end=filter_last_activity_end,
            conversation_id=conversation_id,
            conv_parameter_mask=conv_parameter_mask,
            utc_offset=p[MAPInfo.UTC_OFFSET]
        )

        hdr = {OBEXHdr.APP_PARAM: {}}

        if p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.DATABASE_ID:
            database_identifier = _map.storage.get_database_identifier()
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.DATABASE_IDENTIFIER] = database_identifier
            logging.debug(f"Added Database Identifier (always): {database_identifier}")
        else:
            # For backward compatibility, send zeros if feature not supported
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.DATABASE_IDENTIFIER] = "0" * 32  # 128-bit hex string
            logging.debug("Added Database Identifier (backward compatibility): zeros")

        if max_list_count == 0:
            if p[MAPInfo.SUPPORTED_FEATURES] & MAPSupportedFeatures.CONVO_VERSION_CNTR:
                conversation_listing_version_counter = _map.storage.get_conversation_listing_version_counter()
                hdr[OBEXHdr.APP_PARAM][MAPAppParam.CONV_LIST_VER_CNTR] = conversation_listing_version_counter
                logging.debug(f"Added Conversation-Listing Version Counter: {conversation_listing_version_counter}")

        hdr[OBEXHdr.APP_PARAM][MAPAppParam.LISTING_SIZE] = listing_size
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.MSE_TIME] = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        hdr[OBEXHdr.BODY] = body_bytes if max_list_count != 0 else MAP_FILLER_BYTE

        is_l2cap = _map.is_connected(addr=addr, instance_id=instance_id,
                                    conn_type=defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED)

        if is_l2cap and p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            hdr[OBEXHdr.SRM] = 1
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING

        p[MAPInfo.TX_DATA] = dict(hdr)

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        rsp_code = OBEXRspCode.SUCCESS if len(p[MAPInfo.TX_DATA]) == 0 else OBEXRspCode.CONTINUE

        map_mse_mas_get_convo_listing(instance_id, rsp_code, encoded_hdr)

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break

        if rsp_code != OBEXRspCode.CONTINUE:
            _map.clear_rx_tx_state(addr, instance_id)
            break


def _map_mse_mas_set_ntf_filter_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mas_set_ntf_filter_ev.__name__, data)
    addr, instance_id, data = _map_ev_decode_addr_and_id(data)

    final, req_hdr = _map_decode_req(data)
    if not final:
        map_mse_mas_set_ntf_filter(instance_id, OBEXRspCode.NOT_IMPLEMENTED)
        return

    ntf_filter_mask = req_hdr.get(OBEXHdr.APP_PARAM, {}).get(MAPAppParam.NOTIFICATION_FILTER_MASK, None)
    if ntf_filter_mask is None:
        map_mse_mas_set_ntf_filter(instance_id, OBEXRspCode.BAD_REQ)

    _map.ntf_filter_mask[addr] = ntf_filter_mask
    map_mse_mas_set_ntf_filter(instance_id, OBEXRspCode.SUCCESS)


def _map_mse_mns_rfcomm_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_rfcomm_connected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED)
    map_mse_mns_connect(bd_addr=addr)


def _map_mse_mns_rfcomm_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_rfcomm_disconnected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MNS_CONNECT)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED)


def _map_mse_mns_l2cap_connected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_l2cap_connected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    map_mse_mns_connect(bd_addr=addr)


def _map_mse_mns_l2cap_disconnected_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_l2cap_disconnected_ev.__name__, data)
    addr = _map_ev_decode_addr(data)[0]
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MNS_CONNECT)
    _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)


def _map_mse_mns_connect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_connect_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    rsp_code, version, mopl, rsp_hdr = _map_dec_conn_rsp(data)
    if rsp_code != OBEXRspCode.SUCCESS:
        return

    sdp_list = _map.rx_sdp_get(pts_addr_get(), timeout=0)
    if sdp_list is None or len(sdp_list) == 0:
        logging.error("SDP not found for MAS")
        return

    sdp = next(s for s in sdp_list if s.role == 'mns')

    _map.set_info(addr, MAPInfo.CHANNEL, sdp.channel)
    _map.set_info(addr, MAPInfo.PSM, sdp.psm)
    supported_features = sdp.supported_features & MAP_MSE_SUPPORTED_FEATURES
    _map.set_info(addr, MAPInfo.SUPPORTED_FEATURES, supported_features)
    _map.set_info(addr, MAPInfo.MOPL, mopl)
    _map.set_info(addr, MAPInfo.CONN_ID, rsp_hdr[OBEXHdr.CONN_ID])

    if supported_features & MAPSupportedFeatures.UTC_OFFSET_TIMESTAMP_FORMAT:
        _map.set_info(addr, MAPInfo.UTC_OFFSET, True)

    event_version = "1.0"
    if supported_features & MAPSupportedFeatures.EXT_EVENT_VERSION_1_2:
        event_version = "1.2"
    elif supported_features & MAPSupportedFeatures.EXT_EVENT_REPORT_1_1:
        event_version = "1.1"
    _map.set_info(addr, MAPInfo.EVENT_VERSION, event_version)

    if _map.ntf_filter_mask.get(addr) is None:
        _map.ntf_filter_mask[addr] = 0x00007FFF
    _map.add_connection(addr, defs.BTP_MAP_EV_MSE_MNS_CONNECT)


def _map_mse_mns_disconnect_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_disconnect_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    if rsp_code == OBEXRspCode.SUCCESS:
        _map.remove_connection(addr, defs.BTP_MAP_EV_MSE_MNS_CONNECT)

    if _map.is_connected(addr=addr, conn_type=defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED):
        map_mse_mns_rfcomm_disconnect(bd_addr=addr)
    elif _map.is_connected(addr=addr, conn_type=defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED):
        map_mse_mns_l2cap_disconnect(bd_addr=addr)


def _map_mse_mns_abort_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_abort_ev.__name__, data)
    addr, data = _map_ev_decode_addr(data)
    rsp_code, rsp_hdr = _map_decode_rsp(data)
    _map.clear_rx_tx_state(addr)
    _map.rx(addr, defs.BTP_MAP_EV_MSE_MNS_ABORT, (rsp_code, rsp_hdr))


def _map_mse_mns_send_event_ev(_map, data, data_len):
    logging.debug('%s %r', _map_mse_mns_send_event_ev.__name__, data)

    addr, data = _map_ev_decode_addr(data)

    conn = _map.conn_lookup(addr)
    if not conn:
        logging.error('Connection not found for addr %s', addr)
        return
    p = conn.conn_info

    rsp_code, p[MAPInfo.RX_DATA] = _map_decode_rsp(data, p[MAPInfo.RX_DATA])

    if p.get(MAPInfo.LOCAL_SRM) and p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_DISABLED:
        p[MAPInfo.LOCAL_SRM] = False
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRM, 0) == 1:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED
            if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
                p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED_BUT_WAITING
                del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]

    if rsp_code != OBEXRspCode.CONTINUE:
        _map.rx(addr, defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT, (rsp_code, p[MAPInfo.RX_DATA]))
        _map.clear_rx_tx_state(addr)
        return

    if p.get(MAPInfo.SRM_STATE) == MAPSrmState.SRM_ENABLED_BUT_WAITING:
        if p[MAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del p[MAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            p[MAPInfo.SRM_STATE] = MAPSrmState.SRM_ENABLED

    while True:
        encoded_hdr, p[MAPInfo.TX_DATA], p[MAPInfo.TX_CNT] = map_enc_hdr(
            p[MAPInfo.TX_DATA], p[MAPInfo.MOPL] - 3, p[MAPInfo.TX_CNT]
        )
        is_final = len(p[MAPInfo.TX_DATA]) == 0
        map_mse_mns_send_event(is_final, encoded_hdr)

        if is_final:
            _map.clear_rx_tx_state(addr)
            break

        if p[MAPInfo.SRM_STATE] != MAPSrmState.SRM_ENABLED:
            break


def _map_sdp_record_ev(_map, data, data_len):
    logging.debug('%s %r', _map_sdp_record_ev.__name__, data)

    fmt = '<B6sBHBBHHIBB'
    hdr_len = struct.calcsize(fmt)
    if len(data) < hdr_len:
        raise BTPError("Invalid data length")

    _, addr, final, uuid, instance_id, rfcomm_channel, l2cap_psm, version, supported_features, \
        msg_types, service_name_len = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    service_name = ''
    if service_name_len > 0:
        service_name = struct.unpack_from(f'{service_name_len}s', data, hdr_len)[0].decode('utf-8')

    if uuid == 0x1133:
        # Message Notification Server Service Class
        _map.rx_sdp(addr, 'mns', final, rfcomm_channel, l2cap_psm, version,
            supported_features, msg_types, instance_id, service_name)
        if l2cap_psm != 0:
            map_mse_mns_l2cap_connect(l2cap_psm)
        else:
            map_mse_mns_rfcomm_connect(rfcomm_channel)
    else:
        _map.rx_sdp(addr, 'mas', final, rfcomm_channel, l2cap_psm, version,
            supported_features, msg_types, instance_id, service_name)


# Event handler mapping table
MAP_EV_HANDLERS = {
    # MAP Client MAS events
    defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED: _map_mce_mas_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MCE_MAS_RFCOMM_DISCONNECTED: _map_mce_mas_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED: _map_mce_mas_l2cap_connected_ev,
    defs.BTP_MAP_EV_MCE_MAS_L2CAP_DISCONNECTED: _map_mce_mas_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MAS_CONNECT: _map_mce_mas_connect_ev,
    defs.BTP_MAP_EV_MCE_MAS_DISCONNECT: _map_mce_mas_disconnect_ev,
    defs.BTP_MAP_EV_MCE_MAS_ABORT: _map_mce_mas_abort_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG: _map_mce_mas_set_ntf_reg_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER: _map_mce_mas_set_folder_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING: _map_mce_mas_get_folder_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING: _map_mce_mas_get_msg_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MSG: _map_mce_mas_get_msg_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS: _map_mce_mas_set_msg_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG: _map_mce_mas_push_msg_ev,
    defs.BTP_MAP_EV_MCE_MAS_UPDATE_INBOX: _map_mce_mas_update_inbox_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MAS_INST_INFO: _map_mce_mas_get_mas_inst_info_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_OWNER_STATUS: _map_mce_mas_set_owner_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_OWNER_STATUS: _map_mce_mas_get_owner_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING: _map_mce_mas_get_convo_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_NTF_FILTER: _map_mce_mas_set_ntf_filter_ev,

    # MAP Client MNS events
    defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED: _map_mce_mns_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MCE_MNS_RFCOMM_DISCONNECTED: _map_mce_mns_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED: _map_mce_mns_l2cap_connected_ev,
    defs.BTP_MAP_EV_MCE_MNS_L2CAP_DISCONNECTED: _map_mce_mns_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MNS_CONNECT: _map_mce_mns_connect_ev,
    defs.BTP_MAP_EV_MCE_MNS_DISCONNECT: _map_mce_mns_disconnect_ev,
    defs.BTP_MAP_EV_MCE_MNS_ABORT: _map_mce_mns_abort_ev,
    defs.BTP_MAP_EV_MCE_MNS_SEND_EVENT: _map_mce_mns_send_event_ev,

    # MAP Server MAS events
    defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED: _map_mse_mas_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MSE_MAS_RFCOMM_DISCONNECTED: _map_mse_mas_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED: _map_mse_mas_l2cap_connected_ev,
    defs.BTP_MAP_EV_MSE_MAS_L2CAP_DISCONNECTED: _map_mse_mas_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MAS_CONNECT: _map_mse_mas_connect_ev,
    defs.BTP_MAP_EV_MSE_MAS_DISCONNECT: _map_mse_mas_disconnect_ev,
    defs.BTP_MAP_EV_MSE_MAS_ABORT: _map_mse_mas_abort_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_NTF_REG: _map_mse_mas_set_ntf_reg_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_FOLDER: _map_mse_mas_set_folder_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_FOLDER_LISTING: _map_mse_mas_get_folder_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MSG_LISTING: _map_mse_mas_get_msg_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MSG: _map_mse_mas_get_msg_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_MSG_STATUS: _map_mse_mas_set_msg_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_PUSH_MSG: _map_mse_mas_push_msg_ev,
    defs.BTP_MAP_EV_MSE_MAS_UPDATE_INBOX: _map_mse_mas_update_inbox_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MAS_INST_INFO: _map_mse_mas_get_mas_inst_info_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_OWNER_STATUS: _map_mse_mas_set_owner_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_OWNER_STATUS: _map_mse_mas_get_owner_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_CONVO_LISTING: _map_mse_mas_get_convo_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_NTF_FILTER: _map_mse_mas_set_ntf_filter_ev,

    # MAP Server MNS events
    defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED: _map_mse_mns_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MSE_MNS_RFCOMM_DISCONNECTED: _map_mse_mns_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED: _map_mse_mns_l2cap_connected_ev,
    defs.BTP_MAP_EV_MSE_MNS_L2CAP_DISCONNECTED: _map_mse_mns_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MNS_CONNECT: _map_mse_mns_connect_ev,
    defs.BTP_MAP_EV_MSE_MNS_DISCONNECT: _map_mse_mns_disconnect_ev,
    defs.BTP_MAP_EV_MSE_MNS_ABORT: _map_mse_mns_abort_ev,
    defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT: _map_mse_mns_send_event_ev,

    # SDP event
    defs.BTP_MAP_EV_SDP_RECORD: _map_sdp_record_ev,
}


# Create event handler class
class MAPEventHandler:
    """MAP event handler that processes events in a separate thread"""

    def __init__(self, map_instance):
        self.map = map_instance
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        """Start event processing thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.worker_thread.start()
            logging.debug("MAP event handler started")

    def stop(self):
        """Stop event processing thread"""
        if self.running:
            self.running = False
            self.event_queue.put(None)  # Send stop signal
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logging.debug("MAP event handler stopped")

    def enqueue_event(self, event_id, data, data_len):
        """Add event to processing queue"""
        self.event_queue.put((event_id, data, data_len))

    def _process_events(self):
        """Event processing loop"""
        while self.running:
            try:
                item = self.event_queue.get(timeout=1)
                if item is None:  # Stop signal
                    break

                event_id, data, data_len = item
                self._handle_event(event_id, data, data_len)

            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing MAP event: {e}", exc_info=True)

    def _handle_event(self, event_id, data, data_len):
        """Dispatch event to specific handler"""
        handler = MAP_EV_HANDLERS.get(event_id)
        if handler:
            try:
                handler(self.map, data, data_len)
            except Exception as e:
                logging.error(f"Error in MAP event handler {handler.__name__}: {e}", exc_info=True)
        else:
            logging.warning(f"No handler for MAP event {event_id}")


# MAP Client MAS events
def map_mce_mas_rfcomm_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, data, data_len)


def map_mce_mas_rfcomm_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_DISCONNECTED, data, data_len)


def map_mce_mas_l2cap_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, data, data_len)


def map_mce_mas_l2cap_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_L2CAP_DISCONNECTED, data, data_len)


def map_mce_mas_connect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_CONNECT, data, data_len)


def map_mce_mas_disconnect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_DISCONNECT, data, data_len)


def map_mce_mas_abort_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_ABORT, data, data_len)


def map_mce_mas_set_ntf_reg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG, data, data_len)


def map_mce_mas_set_folder_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, data, data_len)


def map_mce_mas_get_folder_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, data, data_len)


def map_mce_mas_get_msg_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, data, data_len)


def map_mce_mas_get_msg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, data, data_len)


def map_mce_mas_push_msg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, data, data_len)


def map_mce_mas_get_mas_inst_info_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_MAS_INST_INFO, data, data_len)


def map_mce_mas_get_owner_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_OWNER_STATUS, data, data_len)


def map_mce_mas_get_convo_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, data, data_len)


def map_mce_mas_set_msg_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, data, data_len)


def map_mce_mas_update_inbox_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_UPDATE_INBOX, data, data_len)


def map_mce_mas_set_owner_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_SET_OWNER_STATUS, data, data_len)


def map_mce_mas_set_ntf_filter_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MAS_SET_NTF_FILTER, data, data_len)


# MAP Client MNS events
def map_mce_mns_rfcomm_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED, data, data_len)


def map_mce_mns_rfcomm_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_RFCOMM_DISCONNECTED, data, data_len)


def map_mce_mns_l2cap_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED, data, data_len)


def map_mce_mns_l2cap_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_L2CAP_DISCONNECTED, data, data_len)


def map_mce_mns_connect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_CONNECT, data, data_len)


def map_mce_mns_disconnect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_DISCONNECT, data, data_len)


def map_mce_mns_abort_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_ABORT, data, data_len)


def map_mce_mns_send_event_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MCE_MNS_SEND_EVENT, data, data_len)


# MAP Server MAS events
def map_mse_mas_rfcomm_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED, data, data_len)


def map_mse_mas_rfcomm_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_RFCOMM_DISCONNECTED, data, data_len)


def map_mse_mas_l2cap_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED, data, data_len)


def map_mse_mas_l2cap_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_L2CAP_DISCONNECTED, data, data_len)


def map_mse_mas_connect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_CONNECT, data, data_len)


def map_mse_mas_disconnect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_DISCONNECT, data, data_len)


def map_mse_mas_abort_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_ABORT, data, data_len)


def map_mse_mas_set_ntf_reg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_SET_NTF_REG, data, data_len)


def map_mse_mas_set_folder_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_SET_FOLDER, data, data_len)


def map_mse_mas_get_folder_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_FOLDER_LISTING, data, data_len)


def map_mse_mas_get_msg_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_MSG_LISTING, data, data_len)


def map_mse_mas_get_msg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_MSG, data, data_len)


def map_mse_mas_push_msg_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_PUSH_MSG, data, data_len)


def map_mse_mas_set_msg_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_SET_MSG_STATUS, data, data_len)


def map_mse_mas_update_inbox_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_UPDATE_INBOX, data, data_len)


def map_mse_mas_get_mas_inst_info_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_MAS_INST_INFO, data, data_len)


def map_mse_mas_set_owner_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_SET_OWNER_STATUS, data, data_len)


def map_mse_mas_get_owner_status_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_OWNER_STATUS, data, data_len)


def map_mse_mas_get_convo_listing_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_GET_CONVO_LISTING, data, data_len)


def map_mse_mas_set_ntf_filter_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MAS_SET_NTF_FILTER, data, data_len)


# MAP Server MNS events
def map_mse_mns_rfcomm_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED, data, data_len)


def map_mse_mns_rfcomm_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_RFCOMM_DISCONNECTED, data, data_len)


def map_mse_mns_l2cap_connected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED, data, data_len)


def map_mse_mns_l2cap_disconnected_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_L2CAP_DISCONNECTED, data, data_len)


def map_mse_mns_connect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_CONNECT, data, data_len)


def map_mse_mns_disconnect_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_DISCONNECT, data, data_len)


def map_mse_mns_abort_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_ABORT, data, data_len)


def map_mse_mns_send_event_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT, data, data_len)


# SDP event
def map_sdp_record_ev(_map, data, data_len):
    _map.event_handler.enqueue_event(defs.BTP_MAP_EV_SDP_RECORD, data, data_len)


MAP_EV = {
    # MAP Client MAS events
    defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED: map_mce_mas_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MCE_MAS_RFCOMM_DISCONNECTED: map_mce_mas_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED: map_mce_mas_l2cap_connected_ev,
    defs.BTP_MAP_EV_MCE_MAS_L2CAP_DISCONNECTED: map_mce_mas_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MAS_CONNECT: map_mce_mas_connect_ev,
    defs.BTP_MAP_EV_MCE_MAS_DISCONNECT: map_mce_mas_disconnect_ev,
    defs.BTP_MAP_EV_MCE_MAS_ABORT: map_mce_mas_abort_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG: map_mce_mas_set_ntf_reg_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER: map_mce_mas_set_folder_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING: map_mce_mas_get_folder_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING: map_mce_mas_get_msg_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MSG: map_mce_mas_get_msg_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS: map_mce_mas_set_msg_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG: map_mce_mas_push_msg_ev,
    defs.BTP_MAP_EV_MCE_MAS_UPDATE_INBOX: map_mce_mas_update_inbox_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_MAS_INST_INFO: map_mce_mas_get_mas_inst_info_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_OWNER_STATUS: map_mce_mas_set_owner_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_OWNER_STATUS: map_mce_mas_get_owner_status_ev,
    defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING: map_mce_mas_get_convo_listing_ev,
    defs.BTP_MAP_EV_MCE_MAS_SET_NTF_FILTER: map_mce_mas_set_ntf_filter_ev,

    # MAP Client MNS events
    defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED: map_mce_mns_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MCE_MNS_RFCOMM_DISCONNECTED: map_mce_mns_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED: map_mce_mns_l2cap_connected_ev,
    defs.BTP_MAP_EV_MCE_MNS_L2CAP_DISCONNECTED: map_mce_mns_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MCE_MNS_CONNECT: map_mce_mns_connect_ev,
    defs.BTP_MAP_EV_MCE_MNS_DISCONNECT: map_mce_mns_disconnect_ev,
    defs.BTP_MAP_EV_MCE_MNS_ABORT: map_mce_mns_abort_ev,
    defs.BTP_MAP_EV_MCE_MNS_SEND_EVENT: map_mce_mns_send_event_ev,

    # MAP Server MAS events
    defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED: map_mse_mas_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MSE_MAS_RFCOMM_DISCONNECTED: map_mse_mas_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED: map_mse_mas_l2cap_connected_ev,
    defs.BTP_MAP_EV_MSE_MAS_L2CAP_DISCONNECTED: map_mse_mas_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MAS_CONNECT: map_mse_mas_connect_ev,
    defs.BTP_MAP_EV_MSE_MAS_DISCONNECT: map_mse_mas_disconnect_ev,
    defs.BTP_MAP_EV_MSE_MAS_ABORT: map_mse_mas_abort_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_NTF_REG: map_mse_mas_set_ntf_reg_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_FOLDER: map_mse_mas_set_folder_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_FOLDER_LISTING: map_mse_mas_get_folder_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MSG_LISTING: map_mse_mas_get_msg_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MSG: map_mse_mas_get_msg_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_MSG_STATUS: map_mse_mas_set_msg_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_PUSH_MSG: map_mse_mas_push_msg_ev,
    defs.BTP_MAP_EV_MSE_MAS_UPDATE_INBOX: map_mse_mas_update_inbox_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_MAS_INST_INFO: map_mse_mas_get_mas_inst_info_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_OWNER_STATUS: map_mse_mas_set_owner_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_OWNER_STATUS: map_mse_mas_get_owner_status_ev,
    defs.BTP_MAP_EV_MSE_MAS_GET_CONVO_LISTING: map_mse_mas_get_convo_listing_ev,
    defs.BTP_MAP_EV_MSE_MAS_SET_NTF_FILTER: map_mse_mas_set_ntf_filter_ev,

    # MAP Server MNS events
    defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED: map_mse_mns_rfcomm_connected_ev,
    defs.BTP_MAP_EV_MSE_MNS_RFCOMM_DISCONNECTED: map_mse_mns_rfcomm_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED: map_mse_mns_l2cap_connected_ev,
    defs.BTP_MAP_EV_MSE_MNS_L2CAP_DISCONNECTED: map_mse_mns_l2cap_disconnected_ev,
    defs.BTP_MAP_EV_MSE_MNS_CONNECT: map_mse_mns_connect_ev,
    defs.BTP_MAP_EV_MSE_MNS_DISCONNECT: map_mse_mns_disconnect_ev,
    defs.BTP_MAP_EV_MSE_MNS_ABORT: map_mse_mns_abort_ev,
    defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT: map_mse_mns_send_event_ev,

    # SDP event
    defs.BTP_MAP_EV_SDP_RECORD: map_sdp_record_ev,
}
