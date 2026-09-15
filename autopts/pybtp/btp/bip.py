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

import logging
import queue
import struct
import threading
import xml.etree.ElementTree as ET

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.stack.layers.bip import BIPObexRole, BIPSrmFlag
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.pybtp.types import (
    BIPAppParamTag,
    BIPConnType,
    BIPImagingSvclass,
    BIPRemoteDisplay,
    BIPTransportType,
    OBEXHdr,
    OBEXRspCode,
    addr_str_to_le_bytes,
    le_bytes_to_hex_str,
    obex_build_tlv,
    obex_parse_headers,
)

log = logging.debug

BIP_HDR_IMG_HANDLE = OBEXHdr.IMG_HANDLE
BIP_HDR_IMG_DESC = OBEXHdr.IMG_DESCRIPTION


SRM_ENABLE = 0x01
SRMP_WAIT = 0x01


def bt_bip_add_header_app_param(tlv_dict: dict):
    """Build the BIP Application Parameters TLV payload.

    This is the BIP counterpart of bt_pbap_add_header_app_param. Each item in
    tlv_dict maps a BIPAppParamTag id to its value. The value is encoded
    based on the tag type defined by the BIP spec (Table 5.3):

    - 1-byte tags: value as int -> packed as uint8
    - 2-byte tags: value as int -> packed as big-endian uint16
    - 4-byte tags: value as int -> packed as big-endian uint32
    - 16-byte tags (SERVICE_ID UUID): fixed 16-byte block

    Args:
        tlv_dict: {tag: value} mapping of BIP application parameters.

    Returns:
        bytearray: the concatenated TLV-encoded application parameters.
    """
    logging.debug("%s %r", bt_bip_add_header_app_param.__name__, tlv_dict)

    if not tlv_dict:
        raise ValueError("TLV dict must not be empty")

    # Tag type definitions based on BIP spec (Table 5.3)
    TAG_1BYTE = [
        BIPAppParamTag.LATEST_CAPTURED_IMAGES,
        BIPAppParamTag.END_FLAG,
        BIPAppParamTag.REMOTE_DISPLAY,
        BIPAppParamTag.STORE_FLAG,
    ]
    TAG_2BYTE = [
        BIPAppParamTag.NB_RETURNED_HANDLES,
        BIPAppParamTag.LIST_START_OFFSET,
    ]
    TAG_4BYTE = [
        BIPAppParamTag.PARTIAL_FILE_LENGTH,
        BIPAppParamTag.PARTIAL_FILE_START_OFFSET,
        BIPAppParamTag.TOTAL_FILE_SIZE,
    ]
    TAG_16BYTE = [
        BIPAppParamTag.SERVICE_ID,
    ]

    tlv_data = bytearray()
    for tag, value in tlv_dict.items():
        if tag in TAG_1BYTE:
            data = struct.pack('B', value)
        elif tag in TAG_2BYTE:
            data = struct.pack('>H', value)
        elif tag in TAG_4BYTE:
            data = struct.pack('>I', value)
        elif tag in TAG_16BYTE:
            if isinstance(value, str):
                data = bytes.fromhex(value) if len(value) == 32 else \
                    value.encode('utf-8')[:16].ljust(16, b'\x00')
            elif isinstance(value, (bytes, bytearray)):
                data = bytes(value[:16]).ljust(16, b'\x00')
            else:
                data = bytes(value)[:16].ljust(16, b'\x00')
        else:
            if isinstance(value, (bytes, bytearray)):
                data = bytes(value)
            else:
                data = struct.pack('B', value)

        tlv_data.append(tag)
        tlv_data.append(len(data))
        tlv_data.extend(data)

    return tlv_data


def bip_add_headers(buf, data):

    """Append OBEX header data to a byte array (BIP flavour).

    This is the BIP counterpart of pbap_add_headers. It encodes one or more
    OBEX headers into their OBEX wire format and appends them to buf.
    The APP_PARAM header is encoded using BIP Application Parameter tags
    (BIPAppParamTag) rather than the PBAP tag set.

    Args:
        buf: Target bytearray. Header bytes are appended in-place.
        data: Dict with OBEXHdr keys and corresponding values:
               - int: for 4-byte headers (CONN_ID, COUNT, LEN, TIME,
                 CREATE_ID, PERM, ...)
               - int (uint8): for 1-byte headers (SRM, SRMP, ACTION_ID,
                 SESSION_SEQ_NUM)
               - bytes/bytearray/str: for NAME, TYPE, BODY, END_BODY, TARGET,
                 WHO, IMG_HANDLE, IMG_DESCRIPTION, ...
               - dict: for APP_PARAM (encoded via BIPAppParamTag.TAG_SIZES),
                 AUTH_CHALLENGE, AUTH_RSP. May also be raw bytes/bytearray
                 that are already TLV-encoded.

    Returns:
        None. Modifies buf directly.
    """
    logging.debug("%s %r %r", bip_add_headers.__name__, buf, data)
    if not isinstance(buf, bytearray):
        logging.error("buf must be a bytearray")
        return

    if not isinstance(data, dict):
        logging.error("data must be a dictionary")
        return

    for header_id, value in data.items():
        if header_id == OBEXHdr.CONN_ID:
            if not isinstance(value, int):
                logging.error("Header %r requires int value", header_id)
                continue
            buf.append(header_id)
            buf.extend(struct.pack('>I', value))

        elif header_id in (OBEXHdr.SRM, OBEXHdr.SRMP):
            if not isinstance(value, int):
                logging.error("Header %r requires int value", header_id)
                continue
            buf.append(header_id)
            buf.append(value & 0xFF)

        elif header_id in (OBEXHdr.TARGET, OBEXHdr.WHO):
            length = len(value) if value else 0
            total = 1 + 2 + length
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            if value:
                buf.extend(value)

        elif header_id in (OBEXHdr.NAME, OBEXHdr.TYPE, OBEXHdr.BODY,
                           OBEXHdr.END_BODY, OBEXHdr.IMG_HANDLE,
                           OBEXHdr.IMG_DESCRIPTION):
            if isinstance(value, str):
                if header_id in (OBEXHdr.NAME, OBEXHdr.IMG_HANDLE):
                    value = bytearray(value.encode('utf-16-be'))
                else:
                    value = bytearray(value.encode('utf-8'))

            length = len(value) if value else 0

            # Null-terminate Unicode text headers (NAME, IMG_HANDLE).
            # Byte-sequence headers (BODY, END_BODY, TYPE, IMG_DESCRIPTION,
            # TARGET, WHO) are carried verbatim without a terminator.
            if value and header_id in (OBEXHdr.NAME, OBEXHdr.IMG_HANDLE):
                value = value + b'\x00\x00'
                length += 2

            total = 1 + 2 + length
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            if value:
                buf.extend(value)

        elif header_id in (OBEXHdr.APP_PARAM, OBEXHdr.AUTH_CHALLENGE,
                           OBEXHdr.AUTH_RSP):
            if isinstance(value, (bytes, bytearray)):
                payload = bytes(value)
            elif isinstance(value, dict) and len(value) > 0:
                if header_id == OBEXHdr.APP_PARAM:
                    payload = bt_bip_add_header_app_param(value)
                else:
                    # AUTH_CHALLENGE / AUTH_RSP: no BIP-specific tag sizing,
                    # encode as generic TLV.
                    payload = obex_build_tlv(value, {})

            else:
                logging.error("Header %r requires non-empty dict or bytes",
                              header_id)
                continue

            total = 1 + 2 + len(payload)
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            buf.extend(payload)

        else:
            logging.error("Unknown header_id: %r", header_id)


BIP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_BIP,
                            defs.BTP_BIP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'connect_rfcomm': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_CONNECT_RFCOMM,
                       CONTROLLER_INDEX),
    'disconnect_rfcomm': (defs.BTP_SERVICE_ID_BIP,
                          defs.BTP_BIP_CMD_DISCONNECT_RFCOMM,
                          CONTROLLER_INDEX),
    'connect_l2cap': (defs.BTP_SERVICE_ID_BIP,
                      defs.BTP_BIP_CMD_CONNECT_L2CAP,
                      CONTROLLER_INDEX),
    'disconnect_l2cap': (defs.BTP_SERVICE_ID_BIP,
                         defs.BTP_BIP_CMD_DISCONNECT_L2CAP,
                         CONTROLLER_INDEX),
    'sdp_discover': (defs.BTP_SERVICE_ID_BIP,
                     defs.BTP_BIP_CMD_SDP_DISCOVER,
                     CONTROLLER_INDEX),
    'server_register': (defs.BTP_SERVICE_ID_BIP,
                        defs.BTP_BIP_CMD_SERVER_REGISTER,
                        CONTROLLER_INDEX),
    'server_unregister': (defs.BTP_SERVICE_ID_BIP,
                          defs.BTP_BIP_CMD_SERVER_UNREGISTER,
                          CONTROLLER_INDEX),
    'client_connect': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_CLIENT_CONNECT,
                       CONTROLLER_INDEX),
    'obex_disconnect': (defs.BTP_SERVICE_ID_BIP,
                        defs.BTP_BIP_CMD_OBEX_DISCONNECT,
                        CONTROLLER_INDEX),
    'obex_abort': (defs.BTP_SERVICE_ID_BIP,
                   defs.BTP_BIP_CMD_OBEX_ABORT,
                   CONTROLLER_INDEX),
    'connect_rsp': (defs.BTP_SERVICE_ID_BIP,
                    defs.BTP_BIP_CMD_CONNECT_RSP,
                    CONTROLLER_INDEX),
    'disconnect_rsp': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_DISCONNECT_RSP,
                       CONTROLLER_INDEX),
    'abort_rsp': (defs.BTP_SERVICE_ID_BIP,
                  defs.BTP_BIP_CMD_ABORT_RSP,
                  CONTROLLER_INDEX),
    'get_capabilities': (defs.BTP_SERVICE_ID_BIP,
                         defs.BTP_BIP_CMD_GET_CAPABILITIES,
                         CONTROLLER_INDEX),
    'get_capabilities_rsp': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_GET_CAPABILITIES_RSP,
                             CONTROLLER_INDEX),
    'get_image_list': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_GET_IMAGE_LIST,
                       CONTROLLER_INDEX),
    'get_image_list_rsp': (defs.BTP_SERVICE_ID_BIP,
                           defs.BTP_BIP_CMD_GET_IMAGE_LIST_RSP,
                           CONTROLLER_INDEX),
    'get_image_properties': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_GET_IMAGE_PROPERTIES,
                             CONTROLLER_INDEX),
    'get_image_properties_rsp': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_GET_IMAGE_PROPERTIES_RSP,
                                 CONTROLLER_INDEX),
    'get_image': (defs.BTP_SERVICE_ID_BIP,
                  defs.BTP_BIP_CMD_GET_IMAGE,
                  CONTROLLER_INDEX),
    'get_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                      defs.BTP_BIP_CMD_GET_IMAGE_RSP,
                      CONTROLLER_INDEX),
    'get_linked_thumbnail': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_GET_LINKED_THUMBNAIL,
                             CONTROLLER_INDEX),
    'get_linked_thumbnail_rsp': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_GET_LINKED_THUMBNAIL_RSP,
                                 CONTROLLER_INDEX),
    'get_linked_attachment': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_GET_LINKED_ATTACHMENT,
                              CONTROLLER_INDEX),
    'get_linked_attachment_rsp': (defs.BTP_SERVICE_ID_BIP,
                                  defs.BTP_BIP_CMD_GET_LINKED_ATTACHMENT_RSP,
                                  CONTROLLER_INDEX),
    'get_partial_image': (defs.BTP_SERVICE_ID_BIP,
                          defs.BTP_BIP_CMD_GET_PARTIAL_IMAGE,
                          CONTROLLER_INDEX),
    'get_partial_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_GET_PARTIAL_IMAGE_RSP,
                              CONTROLLER_INDEX),
    'get_monitoring_image': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_GET_MONITORING_IMAGE,
                             CONTROLLER_INDEX),
    'get_monitoring_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_GET_MONITORING_IMAGE_RSP,
                                 CONTROLLER_INDEX),
    'get_status': (defs.BTP_SERVICE_ID_BIP,
                   defs.BTP_BIP_CMD_GET_STATUS,
                   CONTROLLER_INDEX),
    'get_status_rsp': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_GET_STATUS_RSP,
                       CONTROLLER_INDEX),
    'put_image': (defs.BTP_SERVICE_ID_BIP,
                  defs.BTP_BIP_CMD_PUT_IMAGE,
                  CONTROLLER_INDEX),
    'put_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                      defs.BTP_BIP_CMD_PUT_IMAGE_RSP,
                      CONTROLLER_INDEX),
    'put_linked_thumbnail': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_PUT_LINKED_THUMBNAIL,
                             CONTROLLER_INDEX),
    'put_linked_thumbnail_rsp': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_PUT_LINKED_THUMBNAIL_RSP,
                                 CONTROLLER_INDEX),
    'put_linked_attachment': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_PUT_LINKED_ATTACHMENT,
                              CONTROLLER_INDEX),
    'put_linked_attachment_rsp': (defs.BTP_SERVICE_ID_BIP,
                                  defs.BTP_BIP_CMD_PUT_LINKED_ATTACHMENT_RSP,
                                  CONTROLLER_INDEX),
    'remote_display': (defs.BTP_SERVICE_ID_BIP,
                       defs.BTP_BIP_CMD_REMOTE_DISPLAY,
                       CONTROLLER_INDEX),
    'remote_display_rsp': (defs.BTP_SERVICE_ID_BIP,
                           defs.BTP_BIP_CMD_REMOTE_DISPLAY_RSP,
                           CONTROLLER_INDEX),
    'delete_image': (defs.BTP_SERVICE_ID_BIP,
                     defs.BTP_BIP_CMD_DELETE_IMAGE,
                     CONTROLLER_INDEX),
    'delete_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                         defs.BTP_BIP_CMD_DELETE_IMAGE_RSP,
                         CONTROLLER_INDEX),
    'start_print': (defs.BTP_SERVICE_ID_BIP,
                    defs.BTP_BIP_CMD_START_PRINT,
                    CONTROLLER_INDEX),
    'start_print_rsp': (defs.BTP_SERVICE_ID_BIP,
                        defs.BTP_BIP_CMD_START_PRINT_RSP,
                        CONTROLLER_INDEX),
    'start_archive': (defs.BTP_SERVICE_ID_BIP,
                      defs.BTP_BIP_CMD_START_ARCHIVE,
                      CONTROLLER_INDEX),
    'start_archive_rsp': (defs.BTP_SERVICE_ID_BIP,
                          defs.BTP_BIP_CMD_START_ARCHIVE_RSP,
                          CONTROLLER_INDEX),
    'second_server_register': (defs.BTP_SERVICE_ID_BIP,
                               defs.BTP_BIP_CMD_SECOND_SERVER_REGISTER,
                               CONTROLLER_INDEX),
    'second_connect': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_SECOND_CONNECT,
                              CONTROLLER_INDEX),
    'second_obex_disconnect': (defs.BTP_SERVICE_ID_BIP,
                               defs.BTP_BIP_CMD_SECOND_OBEX_DISCONNECT,
                               CONTROLLER_INDEX),
    'second_obex_abort': (defs.BTP_SERVICE_ID_BIP,
                          defs.BTP_BIP_CMD_SECOND_OBEX_ABORT,
                          CONTROLLER_INDEX),
    'second_connect_rsp': (defs.BTP_SERVICE_ID_BIP,
                           defs.BTP_BIP_CMD_SECOND_CONNECT_RSP,
                           CONTROLLER_INDEX),
    'second_disconnect_rsp': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_SECOND_DISCONNECT_RSP,
                              CONTROLLER_INDEX),
    'second_abort_rsp': (defs.BTP_SERVICE_ID_BIP,
                         defs.BTP_BIP_CMD_SECOND_ABORT_RSP,
                         CONTROLLER_INDEX),
    'second_server_unregister': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_SECOND_SERVER_UNREGISTER,
                                 CONTROLLER_INDEX),
    'second_get_capabilities_rsp': (defs.BTP_SERVICE_ID_BIP,
                                    defs.BTP_BIP_CMD_SECOND_GET_CAPABILITIES_RSP,
                                    CONTROLLER_INDEX),
    'second_get_image_list_rsp': (defs.BTP_SERVICE_ID_BIP,
                                  defs.BTP_BIP_CMD_SECOND_GET_IMAGE_LIST_RSP,
                                  CONTROLLER_INDEX),
    'second_get_image_properties_rsp': (defs.BTP_SERVICE_ID_BIP,
                                        defs.BTP_BIP_CMD_SECOND_GET_IMAGE_PROPERTIES_RSP,
                                        CONTROLLER_INDEX),
    'second_get_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_SECOND_GET_IMAGE_RSP,
                             CONTROLLER_INDEX),
    'second_get_linked_thumbnail_rsp': (defs.BTP_SERVICE_ID_BIP,
                                        defs.BTP_BIP_CMD_SECOND_GET_LINKED_THUMBNAIL_RSP,
                                        CONTROLLER_INDEX),
    'second_get_linked_attachment_rsp': (defs.BTP_SERVICE_ID_BIP,
                                         defs.BTP_BIP_CMD_SECOND_GET_LINKED_ATTACHMENT_RSP,
                                         CONTROLLER_INDEX),
    'second_delete_image_rsp': (defs.BTP_SERVICE_ID_BIP,
                                defs.BTP_BIP_CMD_SECOND_DELETE_IMAGE_RSP,
                                CONTROLLER_INDEX),
    'second_connect_l2cap': (defs.BTP_SERVICE_ID_BIP,
                             defs.BTP_BIP_CMD_SECOND_CONNECT_L2CAP,
                             CONTROLLER_INDEX),
    'second_connect_rfcomm': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_SECOND_CONNECT_RFCOMM,
                              CONTROLLER_INDEX),
    'second_get_image_list': (defs.BTP_SERVICE_ID_BIP,
                              defs.BTP_BIP_CMD_SECOND_GET_IMAGE_LIST,
                              CONTROLLER_INDEX),
    'second_get_capabilities': (defs.BTP_SERVICE_ID_BIP,
                                defs.BTP_BIP_CMD_SECOND_GET_CAPABILITIES,
                                CONTROLLER_INDEX),
    'second_get_image_properties': (defs.BTP_SERVICE_ID_BIP,
                                    defs.BTP_BIP_CMD_SECOND_GET_IMAGE_PROPERTIES,
                                    CONTROLLER_INDEX),
    'second_get_image': (defs.BTP_SERVICE_ID_BIP,
                         defs.BTP_BIP_CMD_SECOND_GET_IMAGE,
                         CONTROLLER_INDEX),
    'second_get_linked_thumbnail': (defs.BTP_SERVICE_ID_BIP,
                                    defs.BTP_BIP_CMD_SECOND_GET_LINKED_THUMBNAIL,
                                    CONTROLLER_INDEX),
    'second_get_linked_attachment': (defs.BTP_SERVICE_ID_BIP,
                                     defs.BTP_BIP_CMD_SECOND_GET_LINKED_ATTACHMENT,
                                     CONTROLLER_INDEX),
    'second_get_partial_image': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_SECOND_GET_PARTIAL_IMAGE,
                                 CONTROLLER_INDEX),
    'second_delete_image': (defs.BTP_SERVICE_ID_BIP,
                            defs.BTP_BIP_CMD_SECOND_DELETE_IMAGE,
                            CONTROLLER_INDEX),
    'second_disconnect_l2cap': (defs.BTP_SERVICE_ID_BIP,
                                defs.BTP_BIP_CMD_SECOND_DISCONNECT_L2CAP,
                                CONTROLLER_INDEX),
    'second_disconnect_rfcomm': (defs.BTP_SERVICE_ID_BIP,
                                 defs.BTP_BIP_CMD_SECOND_DISCONNECT_RFCOMM,
                                 CONTROLLER_INDEX),
}


def _addr_bytes(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)
    data_ba = bytearray()
    data_ba.extend(struct.pack('B', bd_addr_type))
    data_ba.extend(addr_str_to_le_bytes(bd_addr))
    return data_ba


def bip_command_rsp_succ(timeout=20.0):
    logging.debug("%s", bip_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_BIP)

    return tuple_data


def bip_connect_rfcomm(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       channel=0x09):
    logging.debug("%s %r %r %r", bip_connect_rfcomm.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()
    gap_wait_for_connection()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*BIP['connect_rfcomm'], data=data_ba)


def bip_disconnect_rfcomm(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_disconnect_rfcomm.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['disconnect_rfcomm'], data=data_ba)


def bip_connect_l2cap(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                      psm=0x1001):
    logging.debug("%s %r %r %r", bip_connect_l2cap.__name__, bd_addr, bd_addr_type, psm)

    iutctl = get_iut()
    gap_wait_for_connection()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('<H', psm))

    iutctl.btp_socket.send_wait_rsp(*BIP['connect_l2cap'], data=data_ba)


def bip_disconnect_l2cap(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_disconnect_l2cap.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['disconnect_l2cap'], data=data_ba)


def bip_sdp_discover(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                     uuid=BIPImagingSvclass.IMAGING):
    logging.debug("%s %r %r %r", bip_sdp_discover.__name__, bd_addr,
                  bd_addr_type, uuid)

    iutctl = get_iut()
    gap_wait_for_connection()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba += struct.pack('<H', uuid)

    iutctl.btp_socket.send_wait_rsp(*BIP['sdp_discover'], data=data_ba)


def bip_server_register(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                        conn_type=0):
    logging.debug("%s %r %r %r", bip_server_register.__name__, bd_addr, bd_addr_type, conn_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', conn_type))

    iutctl.btp_socket.send_wait_rsp(*BIP['server_register'], data=data_ba)


def bip_server_unregister(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_server_unregister.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['server_unregister'], data=data_ba)


def bip_client_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       conn_type=0):
    logging.debug("%s %r %r %r", bip_client_connect.__name__, bd_addr, bd_addr_type, conn_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', conn_type))

    iutctl.btp_socket.send_wait_rsp(*BIP['client_connect'], data=data_ba)


def bip_obex_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_obex_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['obex_disconnect'], data=data_ba)


def bip_obex_abort(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_obex_abort.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['obex_abort'], data=data_ba)


def bip_connect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                    rsp_code=OBEXRspCode.SUCCESS):
    logging.debug("%s %r %r %r", bip_connect_rsp.__name__, bd_addr, bd_addr_type, rsp_code)

    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)

    # NOTE: Do NOT inject a CONN_ID header into the primary CONNECT response.
    # The Zephyr bt_bip layer assigns its own connection id to the primary
    # server at registration time (bip_get_connect_id()) and automatically
    # adds it. A client-generated conn_id does not match the firmware-assigned
    # id and makes bt_bip_connect_rsp() reject the buffer with -EINVAL
    # ("Conn id is mismatched"). We DO still send the WHO header (the target
    # UUID echoed from the peer's CONNECT), which the firmware validates
    # against the registered primary UUID via bip_check_who().
    header_data = bytearray()
    conn = get_stack().bip.get_bip_connection(bd_addr)
    if conn is None:
        # The BIP/OBEX connection is already gone. This typically happens when
        # the peer tore down the transport right after the IUT rejected the
        # OBEX CONNECT (e.g. Not Found 0xC4 on a mis-routed secondary CONNECT).
        # Log the real cause here instead of crashing later with a confusing
        # "'NoneType' object has no attribute 'conn_id'" traceback.
        logging.error("bip_connect_rsp: no BIP connection for %s; transport "
                      "likely rejected/disconnected by the peer", bd_addr)
        return

    # Operate explicitly on the primary OBEX session. Send only the WHO header;
    # let the firmware own the conn_id.
    sess = conn.get_session(BIPObexRole.PRIMARY)
    if sess:
        target = sess.conn_info.get('target')
        if target is not None:
            bip_add_headers(header_data, {OBEXHdr.WHO: target})
            logging.debug('BIP connect_rsp headers: who=%s', target.hex())

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('<H', len(header_data)))
    data_ba.extend(header_data)
    if rsp_code == OBEXRspCode.SUCCESS:
        # Track the primary OBEX session but let the firmware own the conn_id.
        get_stack().bip.add_bip_obex_connection(bd_addr)

    iutctl.btp_socket.send_wait_rsp(*BIP['connect_rsp'], data=data_ba)


def bip_disconnect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       rsp_code=0):
    logging.debug("%s %r %r %r", bip_disconnect_rsp.__name__, bd_addr, bd_addr_type, rsp_code)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send_wait_rsp(*BIP['disconnect_rsp'], data=data_ba)


def bip_abort_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                  rsp_code=0):
    logging.debug("%s %r %r %r", bip_abort_rsp.__name__, bd_addr, bd_addr_type, rsp_code)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send_wait_rsp(*BIP['abort_rsp'], data=data_ba)


def bip_second_server_register(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                               conn_type=0):
    logging.debug("%s %r %r %r", bip_second_server_register.__name__, bd_addr,
                  bd_addr_type, conn_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', conn_type))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_server_register'], data=data_ba)


def bip_second_server_unregister(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_second_server_unregister.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_server_unregister'], data=data_ba)


def bip_second_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              conn_type=BIPConnType.SEC_REFERENCED_OBJECTS):
    logging.debug("%s %r %r %r", bip_second_connect.__name__, bd_addr,
                  bd_addr_type, conn_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', conn_type))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_connect'], data=data_ba)


def bip_second_obex_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_second_obex_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_obex_disconnect'], data=data_ba)


def bip_second_obex_abort(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", bip_second_obex_abort.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_obex_abort'], data=data_ba)


def bip_second_connect_l2cap(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             psm=0x1001):
    """Actively open the secondary (Archived Objects) L2CAP transport.

    Unlike bip_connect_l2cap, this binds the new transport to the IUT's
    secondary bt_bip instance (inst->second_bip) so its role is set to
    Initiator before the subsequent BTP_BIP_CMD_SECOND_CONNECT configures
    capabilities/features/functions.
    """
    logging.debug("%s %r %r %r", bip_second_connect_l2cap.__name__, bd_addr,
                  bd_addr_type, psm)

    iutctl = get_iut()
    gap_wait_for_connection()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('<H', psm))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_connect_l2cap'], data=data_ba)


def bip_second_connect_rfcomm(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              channel=0x09):
    """Actively open the secondary (Archived Objects) RFCOMM transport.

    RFCOMM counterpart of bip_second_connect_l2cap; binds the transport to
    the IUT's secondary bt_bip instance (inst->second_bip).
    """
    logging.debug("%s %r %r %r", bip_second_connect_rfcomm.__name__, bd_addr,
                  bd_addr_type, channel)

    iutctl = get_iut()
    gap_wait_for_connection()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_connect_rfcomm'], data=data_ba)


def bip_second_disconnect_l2cap(bd_addr=None,
                                bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Tear down the secondary (Archived/Referenced Objects) L2CAP transport.

    Counterpart of bip_second_connect_l2cap; acts on the IUT's secondary
    bt_bip instance (inst->second_bip).
    """
    logging.debug("%s %r %r", bip_second_disconnect_l2cap.__name__, bd_addr,
                  bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_disconnect_l2cap'],
                                    data=data_ba)


def bip_second_disconnect_rfcomm(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Tear down the secondary (Archived/Referenced Objects) RFCOMM transport.

    Counterpart of bip_second_connect_rfcomm; acts on the IUT's secondary
    bt_bip instance (inst->second_bip).
    """
    logging.debug("%s %r %r", bip_second_disconnect_rfcomm.__name__, bd_addr,
                  bd_addr_type)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_disconnect_rfcomm'],
                                    data=data_ba)


def bip_get_connection(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):

    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)

    return get_stack().bip.get_bip_connection(bd_addr)


def bip_second_connect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                           rsp_code=0xA0):
    logging.debug("%s %r %r %r", bip_second_connect_rsp.__name__, bd_addr,
                  bd_addr_type, rsp_code)

    iutctl = get_iut()
    bd_addr = pts_addr_get(bd_addr)

    # NOTE: Do NOT inject a CONN_ID header into the secondary CONNECT response.
    # The Zephyr bt_bip layer assigns its own connection id to the secondary
    # server at registration time (bip_get_connect_id()) and automatically
    # adds it. A client-generated conn_id does not match the firmware-assigned
    # id and makes bt_bip_connect_rsp() reject the buffer with -EINVAL
    # ("Conn id is mismatched"). We DO still send the WHO header (the target
    # UUID echoed from the peer's secondary CONNECT), which the firmware
    # validates against the registered secondary UUID via bip_check_who().
    header_data = bytearray()
    conn = get_stack().bip.get_bip_connection(bd_addr)
    if conn:
        # Operate on the secondary OBEX session so it stays isolated from the
        # primary. Send only the WHO header; let the firmware own the conn_id.
        sess = conn.get_or_add_session(BIPObexRole.SECONDARY)
        target = sess.conn_info.get('target')
        if target is not None:
            bip_add_headers(header_data, {OBEXHdr.WHO: target})
            logging.debug('BIP second_connect_rsp headers: who=%s',
                          target.hex())

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('<H', len(header_data)))
    data_ba.extend(header_data)

    if rsp_code == OBEXRspCode.SUCCESS:
        get_stack().bip.add_bip_obex_connection(
            bd_addr, role=BIPObexRole.SECONDARY)

    iutctl.btp_socket.send_wait_rsp(*BIP['second_connect_rsp'], data=data_ba)


def bip_second_disconnect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              rsp_code=0):
    logging.debug("%s %r %r %r", bip_second_disconnect_rsp.__name__, bd_addr,
                  bd_addr_type, rsp_code)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_disconnect_rsp'], data=data_ba)


def bip_second_abort_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                         rsp_code=0):
    logging.debug("%s %r %r %r", bip_second_abort_rsp.__name__, bd_addr,
                  bd_addr_type, rsp_code)

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))

    iutctl.btp_socket.send_wait_rsp(*BIP['second_abort_rsp'], data=data_ba)


BIP_CMD_TYPE_MAP = {

    'get_capabilities':      b'x-bt/img-capabilities\x00',
    'get_image_list':        b'x-bt/img-listing\x00',
    'get_image_properties':  b'x-bt/img-properties\x00',
    'get_image':             b'x-bt/img-img\x00',
    'get_linked_thumbnail':  b'x-bt/img-thm\x00',
    'get_linked_attachment': b'x-bt/img-attachment\x00',
    'get_partial_image':     b'x-bt/img-partial\x00',
    'get_monitoring_image':  b'x-bt/img-monitoring\x00',
    'get_status':            b'x-bt/img-status\x00',
    'put_image':             b'x-bt/img-img\x00',
    'put_linked_thumbnail':  b'x-bt/img-thm\x00',
    'put_linked_attachment': b'x-bt/img-attachment\x00',
    'remote_display':        b'x-bt/img-display\x00',
    'delete_image':          b'x-bt/img-img\x00',
    'start_print':           b'x-bt/img-print\x00',
    'start_archive':         b'x-bt/img-archive\x00',
    'second_get_capabilities':      b'x-bt/img-capabilities\x00',
    'second_get_image_list':        b'x-bt/img-listing\x00',
    'second_get_image_properties':  b'x-bt/img-properties\x00',
    'second_get_image':             b'x-bt/img-img\x00',
    'second_get_linked_thumbnail':  b'x-bt/img-thm\x00',
    'second_get_linked_attachment': b'x-bt/img-attachment\x00',
    'second_get_partial_image':     b'x-bt/img-partial\x00',
    'second_delete_image':          b'x-bt/img-img\x00',
}


def _bip_operation_cmd(cmd_key, bd_addr=None,
                       bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       final=1, data=b'', continuation=False,
                       role=BIPObexRole.PRIMARY):
    logging.debug("%s %r %r %r %r cont=%r", cmd_key, bd_addr, bd_addr_type,
                  final, len(data), continuation)

    iutctl = get_iut()

    bd_addr_resolved = pts_addr_get(bd_addr)
    conn = get_stack().bip.get_bip_connection(bd_addr_resolved)
    # Operate on the requested OBEX session directly so all SRM handling stays
    # on the class that owns the SRM state (PRIMARY for imaging, SECONDARY for
    # Referenced/Archived Objects).
    sess = conn.get_or_add_session(role) if conn else None

    prefix = bytearray()

    if not continuation:
        if sess and sess.conn_id is not None:
            bip_add_headers(prefix, {OBEXHdr.CONN_ID: sess.conn_id})

        type_val = BIP_CMD_TYPE_MAP.get(cmd_key)
        if type_val is not None:
            bip_add_headers(prefix, {OBEXHdr.TYPE: type_val})

        if sess and sess.is_srm_allowed() and \
           not (sess.srm_flags & BIPSrmFlag.SRM_LOCAL):
            sess.srm_flags |= BIPSrmFlag.SRM_LOCAL
            prefix.append(OBEXHdr.SRM)
            prefix.append(SRM_ENABLE)
            if sess.srmp_wait_count > 0:
                sess.srm_flags |= BIPSrmFlag.SRMP_LOCAL
                prefix.append(OBEXHdr.SRMP)
                prefix.append(SRMP_WAIT)
                sess.srmp_wait_count -= 1
            else:
                sess.srm_flags &= ~BIPSrmFlag.SRMP_LOCAL

    payload = bytes(prefix) + bytes(data)

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', final))
    data_ba.extend(struct.pack('<H', len(payload)))
    data_ba.extend(payload)

    iutctl.btp_socket.send_wait_rsp(*BIP[cmd_key], data=data_ba)


def _bip_operation_rsp_cmd(cmd_key, bd_addr=None,
                           bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                           rsp_code=0, data=b''):
    logging.debug("%s %r %r %r %r", cmd_key, bd_addr, bd_addr_type, rsp_code,
                  len(data))

    iutctl = get_iut()

    data_ba = _addr_bytes(bd_addr, bd_addr_type)
    data_ba.extend(struct.pack('B', rsp_code))
    data_ba.extend(struct.pack('<H', len(data)))
    data_ba.extend(data)

    iutctl.btp_socket.send_wait_rsp(*BIP[cmd_key], data=data_ba)


def _bip_second_operation_cmd(cmd_key, bd_addr=None,
                              bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              final=1, data=b'', continuation=False):
    # Secondary (Archived/Referenced Objects) client request: same as
    # _bip_operation_cmd but resolves CONN_ID / SRM state from the SECONDARY
    # OBEX session so the request stays isolated from the primary connection.
    return _bip_operation_cmd(cmd_key, bd_addr, bd_addr_type, final, data,
                              continuation, role=BIPObexRole.SECONDARY)


def bip_second_get_capabilities(bd_addr=None,
                                bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                final=1, data=b''):
    _bip_second_operation_cmd('second_get_capabilities', bd_addr, bd_addr_type,
                              final, data)


def bip_second_get_image_list(bd_addr=None,
                              bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              final=1, data=b''):
    _bip_second_operation_cmd('second_get_image_list', bd_addr, bd_addr_type,
                              final, data)


def bip_second_get_image_properties(bd_addr=None,
                                    bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                    final=1, data=b''):
    _bip_second_operation_cmd('second_get_image_properties', bd_addr,
                              bd_addr_type, final, data)


def bip_second_get_image(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                         final=1, data=b''):
    _bip_second_operation_cmd('second_get_image', bd_addr, bd_addr_type,
                              final, data)


def bip_second_get_linked_thumbnail(bd_addr=None,
                                    bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                    final=1, data=b''):
    _bip_second_operation_cmd('second_get_linked_thumbnail', bd_addr,
                              bd_addr_type, final, data)


def bip_second_get_linked_attachment(bd_addr=None,
                                     bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                     final=1, data=b''):
    _bip_second_operation_cmd('second_get_linked_attachment', bd_addr,
                              bd_addr_type, final, data)


def bip_second_get_partial_image(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                 final=1, data=b''):
    _bip_second_operation_cmd('second_get_partial_image', bd_addr,
                              bd_addr_type, final, data)


def bip_second_delete_image(bd_addr=None,
                            bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                            final=1, data=b''):
    _bip_second_operation_cmd('second_delete_image', bd_addr, bd_addr_type,
                              final, data)


def bip_get_capabilities(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                         final=1, data=b''):
    _bip_operation_cmd('get_capabilities', bd_addr, bd_addr_type, final, data)


def bip_get_capabilities_rsp(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_capabilities_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_image_list(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       final=1, data=b''):
    """Send a GetImagesList (Get, x-bt/img-listing) request.

    Per BIP spec section 4.5.6 (Table 4.29) the request carries:
      - Application Parameters (OBEX header 0x4C) with:
          NbReturnedHandles     (tag 0x01, 2 bytes big-endian)
          ListStartOffset       (tag 0x02, 2 bytes big-endian)
          LatestCapturedImages  (tag 0x03, 1 byte)
      - Img-Description header (0x71): image handles descriptor (filter mask).
        The header must always be present but may be empty when no filtering
        is required.

    If *data* is provided (not None), it is used verbatim as the operation
    payload and the parameter-based headers below are ignored (kept for
    backward compatibility with callers that build their own payload).

    *nb_returned_handles*     -- max number of handles to return (0..65535,
                                 0xFFFF = unlimited, 0 = count only).
    *list_start_offset*       -- zero-based offset into the list (0..65535).
    *latest_captured_images*  -- 0x00 = normal list, 0x01 = only locally
                                 captured images in reverse capture order
                                 (ListStartOffset must be 0 in that case).
    *img_desc*                -- image handles descriptor bytes for the
                                 Img-Description header (empty = no filtering,
                                 header still present).
    """
    _bip_operation_cmd('get_image_list', bd_addr, bd_addr_type, final,
                       bytes(data))


def bip_get_image_list_rsp(bd_addr=None,
                           bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                           rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_image_list_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_image_properties(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             final=1, data=b''):
    _bip_operation_cmd('get_image_properties', bd_addr, bd_addr_type, final,
                       data)


def bip_get_image_properties_rsp(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                 rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_image_properties_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_image(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                  final=1, data=b''):
    _bip_operation_cmd('get_image', bd_addr, bd_addr_type, final, data)


def bip_get_image_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                      rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_image_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_linked_thumbnail(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             final=1, data=b''):
    _bip_operation_cmd('get_linked_thumbnail', bd_addr, bd_addr_type, final,
                       data)


def bip_get_linked_thumbnail_rsp(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                 rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_linked_thumbnail_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_linked_attachment(bd_addr=None,
                              bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              final=1, data=b''):
    _bip_operation_cmd('get_linked_attachment', bd_addr, bd_addr_type, final,
                       data)


def bip_get_linked_attachment_rsp(bd_addr=None,
                                  bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                  rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_linked_attachment_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_partial_image(bd_addr=None,
                          bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                          final=1, data=b''):
    _bip_operation_cmd('get_partial_image', bd_addr, bd_addr_type, final, data)


def bip_get_partial_image_rsp(bd_addr=None,
                              bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                              rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_partial_image_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_monitoring_image(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             final=1, data=b''):
    _bip_operation_cmd('get_monitoring_image', bd_addr, bd_addr_type, final,
                       data)


def bip_get_monitoring_image_rsp(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                 rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_monitoring_image_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_get_status(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                   final=1, data=b''):
    _bip_operation_cmd('get_status', bd_addr, bd_addr_type, final, data)


def bip_get_status_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('get_status_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_wait_for_operation_complete(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                   event=defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP, rsp_code=OBEXRspCode.SUCCESS, timeout=30,
                                   role=BIPObexRole.PRIMARY):
    stack = get_stack()
    if bd_addr is None:
        bd_addr = pts_addr_get(bd_addr)
    return stack.bip.wait_for_operation_complete(bd_addr, event, rsp_code=rsp_code, timeout=timeout, role=role)


def _bip_extract_body_xml(body):
    """Extract the concatenated XML document carried by an OBEX response body.

    BIP client responses wrap the requested XML document inside OBEX
    Body (0x48) / End-Body (0x49) headers. When the document exceeds one OBEX
    packet it is chunked, so the (already reassembled) body holds several Body
    headers followed by one End-Body, interleaved with other headers
    (App-Parameters, Img-Description, SRM, ...). Skip the non-body headers and
    join every body payload in order; ElementTree needs a single well-formed
    XML document.
    """
    buf = bytes(body)
    parts = []
    index = 0
    buf_len = len(buf)

    while index < buf_len:
        header_id = buf[index]
        index += 1
        enc = header_id & 0xC0

        if enc == 0x80:  # 1-byte value (e.g. SRM, SRMP)
            index += 1
            continue
        if enc == 0xC0:  # 4-byte value (e.g. CONN_ID, LEN)
            index += 4
            continue
        if index + 2 > buf_len:
            break
        header_total_len = struct.unpack('>H', buf[index:index + 2])[0]
        if header_total_len < 3:
            break
        data_len = header_total_len - 3
        index += 2
        if index + data_len > buf_len:
            break
        raw = buf[index:index + data_len]
        index += data_len
        if header_id in (OBEXHdr.BODY, OBEXHdr.END_BODY):
            parts.append(raw)

    if not parts:
        return None
    return b''.join(parts).decode('utf-8', errors='replace')


def bip_get_caps_format(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send GetCapabilities and parse the response to extract encoding/pixel."""
    result = bip_wait_for_operation_complete(
        pts_addr_get(bd_addr),
        event=defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP,
        rsp_code=OBEXRspCode.SUCCESS,
        timeout=30)

    if not result:
        return None, None

    rsp_code, body = result
    if rsp_code != OBEXRspCode.SUCCESS or not body:
        return None, None

    caps_xml = _bip_extract_body_xml(body)
    logging.debug("GetCapabilities XML: %s", caps_xml)
    if caps_xml is None:
        return None, None

    # Per BIP spec DTD 4.4.6.3, preferred-format and image-formats are EMPTY
    # elements with inline attributes. Priority: preferred-format first, then
    # the first image-formats entry. encoding is REQUIRED, pixel is IMPLIED
    # (optional) in both, so pixel may legitimately be absent.
    root = ET.fromstring(caps_xml)

    elem = root.find('preferred-format')
    if elem is None:
        elem = root.find('image-formats')

    if elem is None:
        return None, None

    return elem.get('encoding'), elem.get('pixel')


def bip_get_image_list_format(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP):
    """Wait for a GetImagesList response and return a list of image handles.

    Waits for BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP with SUCCESS, decodes the
    XML body, and extracts all <image handle="..."> attribute values.

    Returns a list of handle strings (may be empty), or None on failure.
    """
    result = bip_wait_for_operation_complete(
        pts_addr_get(bd_addr),
        event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP,
        rsp_code=OBEXRspCode.SUCCESS,
        timeout=30)

    if not result:
        return None

    rsp_code, body = result
    if rsp_code != OBEXRspCode.SUCCESS or not body:
        return None

    list_xml = _bip_extract_body_xml(body)
    logging.debug("GetImagesList XML: %s", list_xml)
    if list_xml is None:
        return None

    # Per BIP spec DTD 4.4.6.1, the images-listing root contains zero or more
    # EMPTY <image handle="..." created="..." modified="..."/> elements.
    root = ET.fromstring(list_xml)
    return [img.get('handle') for img in root.findall('image')
            if img.get('handle')]


def bip_get_image_properties_format(bd_addr=None,
                                    bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                    role=BIPObexRole.PRIMARY):
    """Wait for a GetImageProperties response and parse the properties XML.

    Waits for BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP with SUCCESS,
    decodes the image-properties XML body, and extracts:
      - handle:      the image handle from the <image-properties handle="...">
                     root element (str, or None if absent)
      - native:      dict with the <native> encoding/pixel/size (may be empty)
      - variants:    list of dicts for each <variant> encoding/pixel
      - attachments: list of dicts for each <attachment> name/content-type/size

    The linked-attachment "name" used by GetLinkedAttachment comes from the
    <attachment name="..."> attribute in this document.

    Returns a tuple (handle, native, variants, attachments). On failure
    returns (None, None, None, None).
    """

    event = defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP
    if role == BIPObexRole.SECONDARY:
        event = defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP
    result = bip_wait_for_operation_complete(
        pts_addr_get(bd_addr),
        event=event,
        rsp_code=OBEXRspCode.SUCCESS,
        role=role,
        timeout=30)
    logging.debug("bip_get_image_properties_format: result= %r", result)

    if not result:
        return None, None, None, None

    rsp_code, body = result
    if rsp_code != OBEXRspCode.SUCCESS or not body:
        return None, None, None, None

    props_xml = _bip_extract_body_xml(body)
    logging.debug("GetImageProperties XML: %s", props_xml)
    if props_xml is None:
        return None, None, None, None

    # Per BIP spec DTD 4.4.6.2, image-properties has exactly one native plus
    # zero or more variant / attachment EMPTY elements with inline attrs.
    root = ET.fromstring(props_xml)

    handle = root.get('handle')

    native = {}
    native_elem = root.find('native')
    if native_elem is not None:
        native = dict(native_elem.attrib)

    variants = [dict(v.attrib) for v in root.findall('variant')]
    attachments = [dict(a.attrib) for a in root.findall('attachment')]

    return handle, native, variants, attachments


def bip_get_attachment_names(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                             role=BIPObexRole.PRIMARY):
    """Return the list of attachment names from a GetImageProperties response.

    Convenience wrapper over bip_get_image_properties_format. The returned
    names are exactly the values that should be supplied as the "name"
    parameter of a subsequent GetLinkedAttachment request.

    Returns a list of name strings (may be empty), or None on failure.
    """
    _handle, _native, _variants, attachments = bip_get_image_properties_format(
        bd_addr, bd_addr_type, role=role)

    if attachments is None:
        return None
    return [a['name'] for a in attachments if 'name' in a]


def bip_register_put_image(handle, bd_addr=None,
                           bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Register the last image sent via bip_put_image into the local DB.

    *handle* is the Img-Handle allocated by the server in the PutImage
    response. It may be raw OBEX bytes (UTF-16BE, null-terminated) or a
    string. The remembered image (see last_put_image) is keyed under this
    handle so a subsequent PutLinkedThumbnail / PutLinkedAttachment can look
    it up and reference the same handle. A thumbnail is generated when the
    image does not already carry one.

    Returns the decoded handle string, or None when there is no image to
    register.
    """
    from autopts.ptsprojects.stack.layers.bip import _make_dummy_jpeg

    if isinstance(handle, (bytes, bytearray)):
        try:
            handle = handle.decode('utf-16-be').rstrip('\x00')
        except UnicodeDecodeError:
            handle = handle.decode('utf-8', errors='replace').rstrip('\x00')
    handle = str(handle) if handle is not None else ""

    if not handle:
        logging.debug("bip_register_put_image: empty handle, nothing to "
                      "register")
        return None

    img = get_stack().bip.image_db.last_put_image
    if img is None:
        logging.debug("bip_register_put_image: no image was sent, nothing "
                      "to register")
        return None

    img.handle = handle
    if not img.thumbnail_data:
        img.thumbnail_data = _make_dummy_jpeg(160, 120)

    stack = get_stack()
    stack.bip.image_db.ds.add_image(img)
    logging.debug("bip_register_put_image: registered sent image under "
                  "handle=%s", handle)
    return handle


def bip_prepare_put_image(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Build an image to send based on the remote GetCapabilities.


    Sends GetCapabilities, waits for and parses the response, then always
    constructs a new synthetic image matching the reported encoding and
    pixel. The image is never looked up in, nor added to, the local image
    database.

    Returns a tuple (img, encoding, pixel) where img is an ImageRecord.
    """

    import datetime

    from autopts.ptsprojects.stack.layers.bip import ImageAttachment, ImageRecord, _make_dummy_jpeg

    bip_get_capabilities()
    # Wait for and parse the GetCapabilities response.
    caps_encoding, caps_pixel = bip_get_caps_format(bd_addr, bd_addr_type)

    encoding = caps_encoding or "JPEG"
    pixel = caps_pixel or "160*120"

    # Always build a new synthetic image matching the reported encoding/pixel.
    # The image is neither looked up in nor added to the local image database.
    pix_match = pixel.replace('x', '*').split('*')
    try:
        w, h_val = int(pix_match[0]), int(pix_match[1])
    except (IndexError, ValueError):
        w, h_val = 160, 120

    image_data_gen = _make_dummy_jpeg(w, h_val)
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    img = ImageRecord(
        handle="",
        friendly_name=f"{encoding}_{pixel}.jpg",
        created=now_str,
        native_encoding=encoding,
        native_pixel=pixel,
        native_size=len(image_data_gen),
        # Seed a real thumbnail here (same rationale as the default attachment
        # below): the thumbnail is an artifact that genuinely belongs to this
        # image, so build it up-front alongside the image and let a later
        # PutLinkedThumbnail read it back from the record. bip_register_put_image
        # only falls back to generating one if it is still empty.
        #
        # The 160x120 size is not arbitrary: the BIP spec defines a fixed
        # "thumbnail image format" (EXIF2.1-compliant JPEG at 160x120 pixels).
        # The thumbnail format is not negotiated via Img-Description, so a
        # linked thumbnail is always produced at this fixed resolution.
        image_data=image_data_gen,
        thumbnail_data=_make_dummy_jpeg(160, 120),

    )
    # Seed a default attachment so a later PutLinkedAttachment can describe and

    # transfer an attachment that genuinely belongs to this image (spec 4.5.4:
    # the attachment-descriptor and body describe the attachment itself). The
    # attachment's name/content-type/charset/data all live on this record and
    # are read back by bip_put_linked_attachment; the caller need not pass them.
    att_data = b"BIP linked attachment test content.\n"
    img.attachments.append(ImageAttachment(
        name=f"{encoding}_{pixel}.txt",
        content_type="text/plain",
        data=att_data,
        charset="iso-8859-1",
        created=now_str,
    ))
    logging.debug("bip_prepare_put_image: built synthetic image "
                  "encoding=%s pixel=%s", encoding, pixel)

    return img, encoding, pixel


def bip_put_image(img, encoding, pixel, bd_addr=None,
                  bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send a PutImage request for the given image.

    This function only performs the transfer. The caller is responsible for
    resolving the image and its encoding/pixel (e.g. via
    bip_prepare_put_image).
    """
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq

    stack = get_stack()
    bd_addr_resolved = pts_addr_get(bd_addr)

    image_data = img.image_data

    # Remember the image just sent so it can be registered into the local
    # image database once the server returns its allocated Img-Handle (see
    # bip_register_put_image). This keeps the sent image, its thumbnail and
    # any attachment consistent with the handle the server assigns, which the
    # subsequent PutLinkedThumbnail / PutLinkedAttachment reference.
    stack.bip.image_db.last_put_image = img

    data = bytearray()
    img_desc_xml = (f'<image-descriptor version="1.0">'

                    f'<image encoding="{encoding}" '
                    f'pixel="{pixel}"/>'
                    f'</image-descriptor>').encode()
    bip_add_headers(data, {
        OBEXHdr.NAME: img.friendly_name,
        OBEXHdr.IMG_DESCRIPTION: img_desc_xml,

    })

    prefix_overhead = 0
    conn = stack.bip.get_bip_connection(bd_addr_resolved)
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    if sess and sess.conn_id is not None:
        prefix_overhead += 5
    type_val = BIP_CMD_TYPE_MAP.get('put_image')

    if type_val is not None:
        prefix_overhead += 3 + len(type_val)

    body_hdr_overhead = 3
    available = _CHUNK_SIZE - prefix_overhead - len(data) - body_hdr_overhead
    if available < 1:
        available = 1

    chunk_size = min(len(image_data), available)
    chunk = image_data[:chunk_size]

    is_last = (chunk_size >= len(image_data))
    if is_last:
        data.extend(_obex_hdr_byte_seq(OBEXHdr.END_BODY, chunk))
        final = 1
    else:
        data.extend(_obex_hdr_byte_seq(OBEXHdr.BODY, chunk))
        final = 0
        sess.pending_put = {
            'cmd_key': 'put_image',
            'data': image_data,
            'offset': chunk_size,
        }

    _bip_operation_cmd('put_image', bd_addr, bd_addr_type, final,
                       bytes(data))


def bip_put_image_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                      rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('put_image_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_put_linked_thumbnail(bd_addr=None,
                             bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send a PutLinkedThumbnail request (BIP 4.5.3).

    The linked image and its handle are resolved internally for consistency:
    the thumbnail is always sent for the image most recently pushed via
    PutImage (registered under the server-allocated handle by
    bip_register_put_image). Callers therefore do not pass a handle, body or
    final flag. This builds the request the same way bip_put_image does, but
    without an Img-Description header (the key difference from PutImage):
      - Img-Handle (0x30): the PutImage-allocated handle (UTF-16BE, null
        terminated).
      - Body/EndOfBody: the thumbnail file, chunked across packets when it
        does not fit into a single OBEX packet.
    """
    from autopts.ptsprojects.stack.layers.bip import _make_dummy_jpeg, _obex_hdr_byte_seq

    stack = get_stack()
    db = stack.bip.image_db
    bd_addr_resolved = pts_addr_get(bd_addr)

    # Resolve the image record whose thumbnail is to be sent. For
    # consistency the image is taken from the one most recently sent via
    # PutImage; fall back to the most-recent image in the local database.
    img = db.last_put_image
    if img is None:
        handles = db.ds.ordered_handles()
        img = db.ds.images[handles[-1]] if handles else None

    if img is None:
        logging.debug("bip_put_linked_thumbnail: no image available to send")
        return

    resolved_handle = img.handle
    thumbnail_data = img.thumbnail_data or _make_dummy_jpeg(160, 120)

    payload = bytearray()

    # Img-Handle header (0x30): UTF-16BE, null-terminated.
    handle_utf16 = str(resolved_handle).encode('utf-16-be') + b'\x00\x00'
    hdr_len = 3 + len(handle_utf16)
    payload.append(BIP_HDR_IMG_HANDLE)
    payload.append((hdr_len >> 8) & 0xFF)
    payload.append(hdr_len & 0xFF)
    payload.extend(handle_utf16)

    # Compute how much thumbnail body fits into the first packet.
    prefix_overhead = 0
    conn = stack.bip.get_bip_connection(bd_addr_resolved)
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    if sess and sess.conn_id is not None:
        prefix_overhead += 5
    type_val = BIP_CMD_TYPE_MAP.get('put_linked_thumbnail')

    if type_val is not None:
        prefix_overhead += 3 + len(type_val)

    body_hdr_overhead = 3
    available = _CHUNK_SIZE - prefix_overhead - len(payload) - \
        body_hdr_overhead
    if available < 1:
        available = 1

    chunk_size = min(len(thumbnail_data), available)
    chunk = thumbnail_data[:chunk_size]

    is_last = (chunk_size >= len(thumbnail_data))
    if is_last:
        payload.extend(_obex_hdr_byte_seq(OBEXHdr.END_BODY, chunk))
        final = 1
    else:
        payload.extend(_obex_hdr_byte_seq(OBEXHdr.BODY, chunk))
        final = 0
        sess.pending_put = {
            'cmd_key': 'put_linked_thumbnail',
            'data': thumbnail_data,
            'offset': chunk_size,
        }

    _bip_operation_cmd('put_linked_thumbnail', bd_addr, bd_addr_type, final,
                       bytes(payload))


def bip_put_linked_thumbnail_rsp(bd_addr=None,
                                 bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                 rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('put_linked_thumbnail_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_put_linked_attachment(bd_addr=None,
                              bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Send a PutLinkedAttachment request (BIP 4.5.4).

    Everything about the request is resolved internally for consistency; the
    caller passes no attachment parameters. Per spec 4.5.4 the
    attachment-descriptor (Img-Description) and the Body describe the
    attachment that genuinely belongs to the linked image, so both the linked
    handle AND the attachment's name/content-type/charset/data are taken from
    the image most recently pushed via PutImage (recorded in last_put_image,
    with a default attachment seeded by bip_prepare_put_image). Falls back to
    the most-recent image in the local database.

    Request headers (spec Table 4.25):
      - Img-Handle (0x30): the linked image handle (UTF-16BE, null
        terminated).
      - Img-Description (0x71): an attachment-descriptor XML document
        (note: this carries the ATTACHMENT descriptor, not an image
        descriptor).
      - Body/EndOfBody: the attachment file, chunked across packets when it
        does not fit into a single OBEX packet.
    """
    import datetime

    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq

    stack = get_stack()
    db = stack.bip.image_db
    bd_addr_resolved = pts_addr_get(bd_addr)

    # Resolve the linked image by consistency: reuse the image most recently
    # pushed via PutImage (recorded in last_put_image once the PutImage
    # response arrives). Fall back to the most-recent image in the local DB.
    img = db.last_put_image
    if img is None or not img.handle:
        handles = db.ds.ordered_handles()
        img = db.ds.images[handles[-1]] if handles else None

    if img is None:
        logging.debug("bip_put_linked_attachment: no image available")
        return

    resolved_handle = img.handle

    # The attachment describes an object that belongs to this image (spec
    # 4.5.4). Read its name/content-type/charset/data from the image's own
    # attachment list; use safe defaults if the image carries none.
    att = img.attachments[0] if img.attachments else None
    if att is not None:
        name = att.name
        content_type = att.content_type
        charset = att.charset or "iso-8859-1"
        attachment_data = att.data
    else:
        name = "attachment.txt"
        content_type = "text/plain"
        charset = "iso-8859-1"
        attachment_data = b"BIP linked attachment test content.\n"

    if isinstance(attachment_data, str):
        attachment_data = attachment_data.encode(charset, errors='replace')

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")
    att_desc_xml = (
        f'<attachment-descriptor version="1.0">'
        f'<attachment content-type="{content_type}" charset="{charset}" '
        f'name="{name}" size="{len(attachment_data)}" '
        f'created="{now_str}"/>'
        f'</attachment-descriptor>').encode()

    payload = bytearray()

    # Img-Handle header (0x30): UTF-16BE, null-terminated.
    handle_utf16 = str(resolved_handle).encode('utf-16-be') + b'\x00\x00'
    hdr_len = 3 + len(handle_utf16)
    payload.append(BIP_HDR_IMG_HANDLE)
    payload.append((hdr_len >> 8) & 0xFF)
    payload.append(hdr_len & 0xFF)
    payload.extend(handle_utf16)

    # Img-Description header (0x71): attachment descriptor XML.
    payload.extend(_obex_hdr_byte_seq(BIP_HDR_IMG_DESC, att_desc_xml))

    # Compute how much attachment body fits into the first packet.
    prefix_overhead = 0
    conn = stack.bip.get_bip_connection(bd_addr_resolved)
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    if sess and sess.conn_id is not None:
        prefix_overhead += 5
    type_val = BIP_CMD_TYPE_MAP.get('put_linked_attachment')

    if type_val is not None:
        prefix_overhead += 3 + len(type_val)

    body_hdr_overhead = 3
    available = _CHUNK_SIZE - prefix_overhead - len(payload) - \
        body_hdr_overhead
    if available < 1:
        available = 1

    chunk_size = min(len(attachment_data), available)
    chunk = attachment_data[:chunk_size]

    is_last = (chunk_size >= len(attachment_data))
    if is_last:
        payload.extend(_obex_hdr_byte_seq(OBEXHdr.END_BODY, chunk))
        final = 1
    else:
        payload.extend(_obex_hdr_byte_seq(OBEXHdr.BODY, chunk))
        final = 0
        sess.pending_put = {
            'cmd_key': 'put_linked_attachment',
            'data': attachment_data,
            'offset': chunk_size,
        }

    _bip_operation_cmd('put_linked_attachment', bd_addr, bd_addr_type, final,
                       bytes(payload))


def bip_put_linked_attachment_rsp(bd_addr=None,
                                  bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                                  rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('put_linked_attachment_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


# BIP RemoteDisplay DisplayedImage App-Parameter values (BIP spec Table 4.3)


def bip_remote_display(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                       handle=None, display_func=BIPRemoteDisplay.CURRENT_IMAGE):
    """Send a RemoteDisplay PUT request.

    *handle*       -- 7-character image handle string (required when
                      display_func == BIP_DISPLAY_SELECT_IMAGE, optional
                      otherwise; the first handle from bip_get_image_list_format
                      is used as a fallback when None).
    *display_func* -- one of BIP_DISPLAY_* constants (default: CurrentImage).

    OBEX headers sent (BIP spec section 5.4.2):
      - Img-Handle   (0x30): null-terminated UTF-16BE handle string
      - App-Param    (0x4C): DisplayedImage TLV (tag=0x01, len=1, value)
    """
    # Img-Handle header (OBEX type 0x30, Unicode, null-terminated UTF-16BE).
    # SelectImage: header contains the handle string value.
    # Next/Prev/CurrentImage: header must be present but empty (3-byte prefix only).
    data = bytearray()
    if handle is None and display_func == BIPRemoteDisplay.SELECT_IMAGE:
        return

    if handle is not None:
        handle_utf16 = handle.encode('utf-16-be') + b'\x00\x00'
        hdr_len = 3 + len(handle_utf16)
        data.append(BIP_HDR_IMG_HANDLE)
        data.append((hdr_len >> 8) & 0xFF)
        data.append(hdr_len & 0xFF)
        data.extend(handle_utf16)
    else:
        # Empty Img-Handle: 3-byte header only (length=3, no body)
        data.append(BIP_HDR_IMG_HANDLE)
        data.append(0x00)
        data.append(0x03)

    # Build App-Parameters TLV: DisplayedImage tag=0x08, length=0x01, value
    app_param = bytes([0x08, 0x01, display_func & 0xFF])
    bip_add_headers(data, {OBEXHdr.APP_PARAM: app_param})

    _bip_operation_cmd('remote_display', bd_addr, bd_addr_type, final=1,
                       data=bytes(data))


def bip_remote_display_rsp(bd_addr=None,
                           bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                           rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('remote_display_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_delete_image(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                     final=1, data=b''):
    _bip_operation_cmd('delete_image', bd_addr, bd_addr_type, final, data)


def bip_delete_image_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                         rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('delete_image_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_start_print(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                    final=1, data=b''):
    _bip_operation_cmd('start_print', bd_addr, bd_addr_type, final, data)


def bip_start_print_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                        rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('start_print_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


def bip_start_archive(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                      final=1, data=b''):
    _bip_operation_cmd('start_archive', bd_addr, bd_addr_type, final, data)


def bip_start_archive_rsp(bd_addr=None,
                          bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                          rsp_code=0, data=b''):
    _bip_operation_rsp_cmd('start_archive_rsp', bd_addr, bd_addr_type,
                           rsp_code, data)


# ============================================================================
# Internal Event Processing Functions
# ============================================================================

def _bip_ev_rfcomm_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_rfcomm_connected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP RFCOMM connected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.add_bip_connection(addr, BIPTransportType.RFCOMM_CONN)


def _bip_ev_rfcomm_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_rfcomm_disconnected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP RFCOMM disconnected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.remove_bip_connection(addr, BIPTransportType.RFCOMM_CONN)


def _bip_ev_l2cap_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_l2cap_connected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP L2CAP connected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.add_bip_connection(addr, BIPTransportType.L2CAP_CONN)


def _bip_ev_l2cap_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_l2cap_disconnected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP L2CAP disconnected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.remove_bip_connection(addr, BIPTransportType.L2CAP_CONN)


def _bip_ev_second_rfcomm_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_rfcomm_connected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP second RFCOMM connected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    # The secondary transport shares the peer's ACL; add_bip_connection() is
    # idempotent and records the transport type on the SECONDARY session so it
    # does not overwrite the primary transport's type.
    bip.add_bip_connection(addr, BIPTransportType.RFCOMM_CONN,
                           role=BIPObexRole.SECONDARY)


def _bip_ev_second_rfcomm_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_rfcomm_disconnected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP second RFCOMM disconnected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    # Clear the secondary session's transport type only; remove_bip_connection()
    # drops the whole connection only once no session still has a transport, so
    # a still-active primary is preserved.
    bip.remove_bip_connection(addr, BIPTransportType.RFCOMM_CONN,
                              role=BIPObexRole.SECONDARY)


def _bip_ev_second_l2cap_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_l2cap_connected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP second L2CAP connected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.add_bip_connection(addr, BIPTransportType.L2CAP_CONN,
                           role=BIPObexRole.SECONDARY)


def _bip_ev_second_l2cap_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_l2cap_disconnected.__name__, data)

    hdr_fmt = '<B6s'
    _, addr = struct.unpack_from(hdr_fmt, data)
    logging.debug('BIP second L2CAP disconnected: addr %r', addr)
    addr = le_bytes_to_hex_str(addr)
    bip.remove_bip_connection(addr, BIPTransportType.L2CAP_CONN,
                              role=BIPObexRole.SECONDARY)


def _bip_ev_server_connect_req(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_server_connect_req.__name__, data)

    hdr_fmt = '<B6sBHH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, version, mopl, body_data_len = struct.unpack_from(
        hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    logging.debug('BIP server connect req: addr %s version %d mopl %d',
                  addr, version, mopl)

    headers = obex_parse_headers(body)
    target = headers.get(OBEXHdr.TARGET)
    if target is not None:
        conn = bip.get_bip_connection(addr)
        if conn:
            sess = conn.get_session(BIPObexRole.PRIMARY)
            sess.conn_info['target'] = target
            logging.debug('BIP stored target: %s', target.hex())

    bip.rx(addr, defs.BTP_BIP_EV_SERVER_CONNECT_REQ,

           (version, mopl, body))


def _bip_ev_server_data_req(ev_id, name, bip, data, data_len):
    logging.debug('%s %r', name, data)

    hdr_fmt = '<B6sH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, body_data_len = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    bip.rx(addr, ev_id, (body,))


def _bip_ev_server_disconnect_req(bip, data, data_len):
    _bip_ev_server_data_req(defs.BTP_BIP_EV_SERVER_DISCONNECT_REQ,
                            'server_disconnect_req', bip, data, data_len)


def _bip_ev_server_abort_req(bip, data, data_len):
    _bip_ev_server_data_req(defs.BTP_BIP_EV_SERVER_ABORT_REQ,
                            'server_abort_req', bip, data, data_len)


def _parse_server_op_req(data):
    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, final, body_data_len = struct.unpack_from(hdr_fmt, data)
    raw = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)
    headers = obex_parse_headers(raw)
    srm = headers.get(OBEXHdr.SRM, None)
    srmp = headers.get(OBEXHdr.SRMP, None)
    return addr, final, headers, srm, srmp


_CHUNK_SIZE = 150

_EV_TO_GET_CMD = {
    defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP: 'get_capabilities',
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP: 'get_image_list',
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP: 'get_image_properties',
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP: 'get_image',
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP: 'get_linked_thumbnail',
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP: 'get_linked_attachment',
    defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP: 'get_partial_image',
    defs.BTP_BIP_EV_CLIENT_GET_MONITORING_IMAGE_RSP: 'get_monitoring_image',
    defs.BTP_BIP_EV_CLIENT_GET_STATUS_RSP: 'get_status',
}


def _send_continuation(addr, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq

    conn = get_stack().bip.get_bip_connection(addr)
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    pending = sess.pending_put if sess else None
    if not pending:
        return

    cmd_key = pending['cmd_key']
    image_data = pending['data']
    offset = pending['offset']

    body_hdr_overhead = 3
    available = _CHUNK_SIZE - body_hdr_overhead
    remaining = len(image_data) - offset
    chunk_size = min(remaining, available)
    chunk = image_data[offset:offset + chunk_size]

    is_last = (offset + chunk_size >= len(image_data))
    prefix = bytearray()

    if sess and sess.is_srm_allowed() and sess.srmp_wait_count > 0:
        sess.srm_flags |= BIPSrmFlag.SRMP_LOCAL
        prefix.append(OBEXHdr.SRMP)
        prefix.append(SRMP_WAIT)
        sess.srmp_wait_count -= 1
    elif sess:
        sess.srm_flags &= ~BIPSrmFlag.SRMP_LOCAL

    data = bytearray(prefix)
    if is_last:
        data.extend(_obex_hdr_byte_seq(OBEXHdr.END_BODY, chunk))
        sess.pending_put = None
        final = 1
    else:
        data.extend(_obex_hdr_byte_seq(OBEXHdr.BODY, chunk))
        pending['offset'] = offset + chunk_size
        final = 0

    iutctl = get_iut()
    data_ba = bytearray()
    data_ba.extend(struct.pack('B', bd_addr_type))
    data_ba.extend(addr_str_to_le_bytes(addr))
    data_ba.extend(struct.pack('B', final))
    data_ba.extend(struct.pack('<H', len(data)))
    data_ba.extend(data)
    iutctl.btp_socket.send_wait_rsp(*BIP[cmd_key], data=data_ba)


def _send_chunked_rsp(cmd_key, addr, chunk_key, body_data,
                      extra_headers=b'', srm_enable=False,
                      srmp_wait=False):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq

    conn = get_stack().bip.get_bip_connection(addr)
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    chunk_offsets = sess.chunk_offsets if sess else {}
    offset = chunk_offsets.get(chunk_key, 0)
    remaining = len(body_data) - offset
    body_hdr_overhead = 3
    available = _CHUNK_SIZE - body_hdr_overhead
    chunk_size = min(remaining, available)
    chunk = body_data[offset:offset + chunk_size]

    data = bytearray()

    if offset == 0:
        if srm_enable:
            data.append(OBEXHdr.SRM)
            data.append(SRM_ENABLE)
        if extra_headers:
            data.extend(extra_headers)

    if srmp_wait:
        data.append(OBEXHdr.SRMP)
        data.append(SRMP_WAIT)

    if offset + chunk_size >= len(body_data):
        data.extend(_obex_hdr_byte_seq(OBEXHdr.END_BODY, chunk))
        chunk_offsets[chunk_key] = 0
        _bip_operation_rsp_cmd(cmd_key, bd_addr=addr,
                               rsp_code=OBEXRspCode.SUCCESS,
                               data=bytes(data))
    else:
        data.extend(_obex_hdr_byte_seq(OBEXHdr.BODY, chunk))
        chunk_offsets[chunk_key] = offset + chunk_size
        _bip_operation_rsp_cmd(cmd_key, bd_addr=addr,
                               rsp_code=OBEXRspCode.CONTINUE,
                               data=bytes(data))


def _update_srm_state(conn, srm, srmp):
    """Update SRM state on the primary OBEX session of a connection.

    Accepts the transport-level BIPConnection and operates on its PRIMARY
    OBEX session explicitly (no attribute proxies).

    Returns True if SRM is being used for this operation.
    """
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    logging.debug('_update_srm_state: sess=%r srm=%r srmp=%r srm_allowed=%r srm_flags=0x%02x',

                  sess, srm, srmp,
                  sess.is_srm_allowed() if sess else None,
                  sess.srm_flags if sess else 0)
    if not sess or not sess.is_srm_allowed():
        return False

    if not (sess.srm_flags & BIPSrmFlag.SRM_REMOTE):
        if srm == SRM_ENABLE:
            sess.srm_flags |= BIPSrmFlag.SRM_REMOTE

    if srmp == SRMP_WAIT:
        sess.srm_flags |= BIPSrmFlag.SRMP_REMOTE
    else:
        sess.srm_flags &= ~BIPSrmFlag.SRMP_REMOTE

    logging.debug('_update_srm_state: after update srm_flags=0x%02x', sess.srm_flags)
    return bool(sess.srm_flags & BIPSrmFlag.SRM_REMOTE)


def _send_get_rsp_with_srm(conn, cmd_key, addr, chunk_key, body_data,
                            final, extra_headers=b''):
    # Accept the transport-level BIPConnection and operate on its PRIMARY
    # OBEX session explicitly (no attribute proxies).
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    logging.debug('_send_get_rsp_with_srm: sess=%r srm_allowed=%r '

                  'srm_flags=0x%02x srmp_wait_count=%r final=%r',
                  sess,
                  sess.is_srm_allowed() if sess else None,
                  sess.srm_flags if sess else 0,
                  sess.srmp_wait_count if sess else None,
                  final)
    if not sess or not sess.is_srm_allowed() or \
       not (sess.srm_flags & BIPSrmFlag.SRM_REMOTE):
        _send_chunked_rsp(cmd_key, addr, chunk_key, body_data,
                          extra_headers=extra_headers)
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            if sess:
                sess.reset_srm()
            sess._pending_body.pop(chunk_key, None)
        return

    srm_enable = False
    srmp_wait = False

    if not (sess.srm_flags & BIPSrmFlag.SRM_LOCAL):
        srm_enable = True
        sess.srm_flags |= BIPSrmFlag.SRM_LOCAL
        if sess.srmp_wait_count > 0:
            sess.srm_flags |= BIPSrmFlag.SRMP_LOCAL

    if sess.srm_flags & BIPSrmFlag.SRMP_LOCAL:
        if sess.srmp_wait_count > 0:
            srmp_wait = True
            sess.srmp_wait_count -= 1
        else:
            sess.srm_flags &= ~BIPSrmFlag.SRMP_LOCAL

    need_rsp = not sess.is_srm_full_speed() or srm_enable

    if need_rsp:
        _send_chunked_rsp(cmd_key, addr, chunk_key, body_data,
                          extra_headers=extra_headers,
                          srm_enable=srm_enable,
                          srmp_wait=srmp_wait)

    if sess.is_srm_full_speed() and final:
        while sess.chunk_offsets.get(chunk_key, 0) > 0:
            _send_chunked_rsp(cmd_key, addr, chunk_key, body_data)

    if sess.chunk_offsets.get(chunk_key, 0) == 0:
        sess.reset_srm()
        sess._pending_body.pop(chunk_key, None)


def _send_put_rsp_with_srm(conn, cmd_key, addr, final, rsp_code,
                            rsp_hdrs=b''):
    # Accept the transport-level BIPConnection and operate on its PRIMARY
    # OBEX session explicitly (no attribute proxies).
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None
    logging.debug('_send_put_rsp_with_srm: sess=%r srm_allowed=%r '

                  'srm_flags=0x%02x srmp_wait_count=%r final=%r',
                  sess,
                  sess.is_srm_allowed() if sess else None,
                  sess.srm_flags if sess else 0,
                  sess.srmp_wait_count if sess else None,
                  final)
    if not sess or not sess.is_srm_allowed() or \
       not (sess.srm_flags & BIPSrmFlag.SRM_REMOTE):
        _bip_operation_rsp_cmd(cmd_key, bd_addr=addr,
                               rsp_code=rsp_code, data=rsp_hdrs)
        if final and sess:
            sess.reset_srm()
        return

    srm_data = bytearray()
    srm_enable = False
    srmp_active = False

    if not (sess.srm_flags & BIPSrmFlag.SRM_LOCAL):
        srm_enable = True
        srm_data.append(OBEXHdr.SRM)
        srm_data.append(SRM_ENABLE)
        sess.srm_flags |= BIPSrmFlag.SRM_LOCAL
        if sess.srmp_wait_count > 0:
            sess.srm_flags |= BIPSrmFlag.SRMP_LOCAL

    if sess.srm_flags & BIPSrmFlag.SRMP_LOCAL:
        # A response is still required for the request carrying the SRMP WAIT
        # header, and also for the transition packet that drops it (when
        # srmp_wait_count reaches 0). Without responding on that transition
        # packet the remote never learns it may switch to full-speed SRM and
        # keeps waiting, which makes PTS time out ("Failed to complete get").
        srmp_active = True
        if sess.srmp_wait_count > 0:
            srm_data.append(OBEXHdr.SRMP)
            srm_data.append(SRMP_WAIT)
            sess.srmp_wait_count -= 1
        else:
            sess.srm_flags &= ~BIPSrmFlag.SRMP_LOCAL

    need_rsp = final or not sess.is_srm_full_speed() or srm_enable or srmp_active

    if need_rsp:
        data = bytes(srm_data) + (rsp_hdrs if rsp_hdrs else b'') if srm_data else rsp_hdrs
        code = rsp_code if final else OBEXRspCode.CONTINUE
        _bip_operation_rsp_cmd(cmd_key, bd_addr=addr,
                               rsp_code=code, data=data)

    if final:
        sess.reset_srm()


def _bip_ev_server_get_caps_req(bip, data, data_len,
                                ev_id=defs.BTP_BIP_EV_SERVER_GET_CAPS_REQ,
                                rsp_cmd='get_capabilities_rsp',
                                chunk_key='get_caps'):
    logging.debug('%s %r', _bip_ev_server_get_caps_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            sess._pending_body[chunk_key] = \
                bip.image_db.get_caps_rsp(headers)
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key,
                                sess._pending_body[chunk_key], final)


def _bip_ev_server_get_image_list_req(bip, data, data_len,
                                      ev_id=defs.BTP_BIP_EV_SERVER_GET_IMAGE_LIST_REQ,
                                      rsp_cmd='get_image_list_rsp',
                                      chunk_key='get_image_list'):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq
    logging.debug('%s %r', _bip_ev_server_get_image_list_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            app_params = headers.get(OBEXHdr.APP_PARAM, {})
            body_data, rsp_app_params, img_desc = \
                bip.image_db.get_image_list_rsp(headers, app_params)
            extra_hdrs = bytearray()
            extra_hdrs.extend(
                _obex_hdr_byte_seq(OBEXHdr.APP_PARAM, rsp_app_params))
            if img_desc:
                extra_hdrs.extend(
                    _obex_hdr_byte_seq(BIP_HDR_IMG_DESC, img_desc))
            sess._pending_body[chunk_key] = (body_data, bytes(extra_hdrs))
        body_data, extra_hdrs = sess._pending_body[chunk_key]
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key, body_data, final,
                                extra_headers=extra_hdrs)


def _bip_ev_server_get_image_properties_req(bip, data, data_len,
                                            ev_id=defs.BTP_BIP_EV_SERVER_GET_IMAGE_PROPERTIES_REQ,
                                            rsp_cmd='get_image_properties_rsp',
                                            chunk_key='get_image_properties'):
    logging.debug('%s %r',
                  _bip_ev_server_get_image_properties_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        # Spec 4.5.7 (Table 4.31): Img-Handle is mandatory and must be valid.
        # A missing handle is a Bad Request; a well-formed but unknown handle
        # is Not Found. Only build the image-properties body for a valid handle.
        req_handle = bip.image_db.extract_handle(headers)
        if not req_handle:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.BAD_REQ, data=b'')
            return
        if not bip.image_db.has_image(req_handle):
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            sess._pending_body[chunk_key] = \
                bip.image_db.get_image_properties_rsp(headers)
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key,
                                sess._pending_body[chunk_key], final)


def _bip_ev_server_get_image_req(bip, data, data_len,
                                 ev_id=defs.BTP_BIP_EV_SERVER_GET_IMAGE_REQ,
                                 rsp_cmd='get_image_rsp',
                                 chunk_key='get_image'):
    logging.debug('%s %r', _bip_ev_server_get_image_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        # Spec 4.5.8 (Table 4.33): Img-Handle is mandatory and must be valid.
        # A missing handle is a Bad Request; a well-formed but unknown handle
        # is Not Found.
        req_handle = bip.image_db.extract_handle(headers)
        if not req_handle:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.BAD_REQ, data=b'')
            return
        if not bip.image_db.has_image(req_handle):
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            sess._pending_body[chunk_key] = \
                bip.image_db.get_image_rsp(headers)
        body_data = sess._pending_body[chunk_key]
        # Spec Table 4.34: the response must carry a Length header (the image
        # file size). Per the multi-packet GET rule, non-Body headers go in the
        # first response packet, so pass it as extra_headers (injected only at
        # offset 0 by _send_chunked_rsp).
        length_hdr = bytearray()
        length_hdr.append(OBEXHdr.LEN)
        length_hdr.extend(struct.pack('>I', len(body_data)))
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key, body_data, final,
                                extra_headers=bytes(length_hdr))


def _bip_ev_server_get_linked_thumbnail_req(bip, data, data_len,
                                            ev_id=defs.BTP_BIP_EV_SERVER_GET_LINKED_THUMBNAIL_REQ,
                                            rsp_cmd='get_linked_thumbnail_rsp',
                                            chunk_key='get_linked_thumbnail'):
    logging.debug('%s %r',
                  _bip_ev_server_get_linked_thumbnail_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        # Spec 4.5.9 (Table 4.35): Img-Handle is mandatory and must be valid.
        req_handle = bip.image_db.extract_handle(headers)
        if not req_handle:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.BAD_REQ, data=b'')
            return
        if not bip.image_db.has_image(req_handle):
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            sess._pending_body[chunk_key] = \
                bip.image_db.get_linked_thumbnail_rsp(headers)
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key,
                                sess._pending_body[chunk_key], final)


def _bip_ev_server_get_linked_attachment_req(bip, data, data_len,
                                             ev_id=defs.BTP_BIP_EV_SERVER_GET_LINKED_ATTACHMENT_REQ,
                                             rsp_cmd='get_linked_attachment_rsp',
                                             chunk_key='get_linked_attachment'):
    logging.debug('%s %r',
                  _bip_ev_server_get_linked_attachment_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        # Spec 4.5.10 (Table 4.37): Img-Handle is mandatory and must be valid,
        # and the attachment is referenced by the Name header (attachment file
        # name). A missing handle is a Bad Request; an unknown handle or a
        # missing/unmatched attachment name is Not Found.
        req_handle = bip.image_db.extract_handle(headers)
        if not req_handle:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.BAD_REQ, data=b'')
            return
        if not bip.image_db.has_image(req_handle):
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        req_name = bip.image_db._extract_name(headers)
        if bip.image_db.find_attachment_data(req_handle, req_name) is None:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            sess._pending_body[chunk_key] = \
                bip.image_db.get_linked_attachment_rsp(headers)
        _send_get_rsp_with_srm(conn, rsp_cmd, addr,
                                chunk_key,
                                sess._pending_body[chunk_key], final)


def _bip_ev_server_get_partial_image_req(bip, data, data_len):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq
    logging.debug('%s %r',
                  _bip_ev_server_get_partial_image_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_GET_PARTIAL_IMAGE_REQ, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        chunk_key = 'get_partial_image'
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            app_params = headers.get(OBEXHdr.APP_PARAM, {})
            body_data, rsp_app_params = \
                bip.image_db.get_partial_image_rsp(headers, app_params)
            extra_hdrs = bytearray()
            # Spec Table 4.44: the response must carry a Length header (length
            # of the partial file returned in THIS response, 4-byte big-endian).
            # Per the multi-packet GET rule non-Body headers go in the first
            # response packet (injected only at offset 0 by _send_chunked_rsp).
            extra_hdrs.append(OBEXHdr.LEN)
            extra_hdrs.extend(struct.pack('>I', len(body_data)))
            extra_hdrs.extend(
                _obex_hdr_byte_seq(OBEXHdr.APP_PARAM, rsp_app_params))
            sess._pending_body[chunk_key] = (body_data, bytes(extra_hdrs))

        body_data, extra_hdrs = sess._pending_body[chunk_key]
        _send_get_rsp_with_srm(conn, 'get_partial_image_rsp', addr,
                                chunk_key, body_data, final,
                                extra_headers=extra_hdrs)


def _bip_ev_server_get_monitoring_image_req(bip, data, data_len):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq
    logging.debug('%s %r',
                  _bip_ev_server_get_monitoring_image_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_GET_MONITORING_IMAGE_REQ,
           (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        if conn is None:
            logging.error('BIP server auto-response: no connection for %s',
                          addr)
            return
        sess = conn.get_session(BIPObexRole.PRIMARY)
        _update_srm_state(conn, srm, srmp)
        chunk_key = 'get_monitoring_image'
        if sess.chunk_offsets.get(chunk_key, 0) == 0:
            body_data, img_handle = \
                bip.image_db.get_monitoring_image_rsp(headers)
            # Spec Table 4.50: the Img-Handle header is only returned when the
            # server actually stored a full-size captured image (StoreFlag=
            # 0x01) and has a handle to hand back. When StoreFlag=0x00 (do not
            # store) there is no handle and the header must NOT be present at
            # all; PTS rejects an empty Img-Handle here with the verdict
            # "Img-Handle not expected" (see BIP/RCR/FSF/BV-03-C). This differs
            # from RemoteDisplay (Table 4.28), where an empty Img-Handle header
            # is mandatory, so we handle it per-operation rather than globally.
            # Per the multi-packet GET rule non-Body headers go in the first
            # response packet, so pass it as extra_headers (injected only at
            # offset 0 by _send_chunked_rsp).
            if img_handle:
                extra_hdrs = bytes(
                    _obex_hdr_byte_seq(BIP_HDR_IMG_HANDLE, img_handle))
            else:
                extra_hdrs = b''
            sess._pending_body[chunk_key] = (body_data, extra_hdrs)
        body_data, extra_hdrs = sess._pending_body[chunk_key]
        _send_get_rsp_with_srm(conn, 'get_monitoring_image_rsp', addr,
                                chunk_key, body_data, final,
                                extra_headers=extra_hdrs)


def _bip_ev_server_get_status_req(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_server_get_status_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_GET_STATUS_REQ, (final, headers))
    if bip.auto_response_enabled:
        # Spec Table 4.48: the GetStatus response is a Response Code only,
        # with NO OBEX headers (not even Body/EndOfBody). Reply directly with
        # the response code rather than routing through the chunked-GET path
        # (which would emit an empty EndOfBody header). The CONTINUE/SUCCESS
        # code is derived from the live secondary OBEX session state.
        rsp_code, rsp_data = bip.build_get_status_rsp(addr)
        _bip_operation_rsp_cmd('get_status_rsp', bd_addr=addr,
                               rsp_code=rsp_code, data=rsp_data)


def _bip_ev_server_put_image_req(bip, data, data_len):
    import re as _re

    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq
    logging.debug('%s %r', _bip_ev_server_put_image_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_PUT_IMAGE_REQ, (final, headers))

    # Validate the requested image description (encoding/pixel) against the
    # capabilities the server actually advertises in GetCapabilities. We check
    # against bip.image_db (the same BIPDataStore that get_caps_rsp serializes)
    # rather than the raw TSPX_* PIXIT constants, so that whatever set of
    # encodings/pixels is exposed via GetCapabilities is exactly what is
    # accepted here. A requested format outside the advertised capabilities is
    # rejected with BAD_REQUEST.
    img_desc_raw = headers.get(BIP_HDR_IMG_DESC)
    if img_desc_raw:
        try:
            img_desc_xml = img_desc_raw.decode('utf-8', errors='replace')
            m_pixel = _re.search(r'\bpixel="([^"]+)"', img_desc_xml)
            m_enc = _re.search(r'\bencoding="([^"]+)"', img_desc_xml)
            req_pixel = m_pixel.group(1) if m_pixel else None
            req_enc = m_enc.group(1) if m_enc else None
            if not bip.image_db.is_format_supported(req_enc, req_pixel):
                logging.debug('put_image: encoding=%r pixel=%r not in '
                              'advertised capabilities (encodings=%r), '
                              'responding BAD_REQUEST',
                              req_enc, req_pixel,
                              sorted(bip.image_db.supported_encodings()))
                conn = bip.get_bip_connection(addr)
                _bip_operation_rsp_cmd('put_image_rsp', bd_addr=addr,
                               rsp_code=OBEXRspCode.BAD_REQ, data=b'')

                return
        except Exception as e:
            logging.warning('put_image: failed to check image description: %s', e)

    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        _update_srm_state(conn, srm, srmp)
        rsp_code, handle = bip.image_db.put_image_rsp(final, headers)
        rsp_hdrs = bytes(_obex_hdr_byte_seq(BIP_HDR_IMG_HANDLE, handle))
        _send_put_rsp_with_srm(conn, 'put_image_rsp', addr, final,
                                rsp_code, rsp_hdrs)


def _bip_ev_server_put_linked_thumbnail_req(bip, data, data_len):
    logging.debug('%s %r',
                  _bip_ev_server_put_linked_thumbnail_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_PUT_LINKED_THUMBNAIL_REQ,
           (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        _update_srm_state(conn, srm, srmp)
        rsp_code, rsp_data = bip.image_db.put_linked_thumbnail_rsp(
            final, headers)
        _send_put_rsp_with_srm(conn, 'put_linked_thumbnail_rsp', addr,
                                final, rsp_code, rsp_data)


def _bip_ev_server_put_linked_attachment_req(bip, data, data_len):
    logging.debug('%s %r',
                  _bip_ev_server_put_linked_attachment_req.__name__, data)
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_PUT_LINKED_ATTACHMENT_REQ,
           (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        _update_srm_state(conn, srm, srmp)
        rsp_code, rsp_data = bip.image_db.put_linked_attachment_rsp(
            final, headers)
        _send_put_rsp_with_srm(conn, 'put_linked_attachment_rsp', addr,
                                final, rsp_code, rsp_data)


def _bip_ev_server_remote_display_req(bip, data, data_len):
    from autopts.ptsprojects.stack.layers.bip import _obex_hdr_byte_seq
    logging.debug('%s %r',
                  _bip_ev_server_remote_display_req.__name__, data)
    addr, final, headers, _, _ = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_REMOTE_DISPLAY_REQ, (final, headers))
    if bip.auto_response_enabled:
        rsp_code, rsp_data = bip.image_db.remote_display_rsp(final, headers)
        # Spec Table 4.28: the Img-Handle header must ALWAYS be present in the
        # response; when no image is currently displayed it is present but
        # empty (3-byte header only, no body).
        rsp_hdrs = bytes(_obex_hdr_byte_seq(BIP_HDR_IMG_HANDLE,
                                            rsp_data or b''))
        _bip_operation_rsp_cmd('remote_display_rsp', bd_addr=addr,
                               rsp_code=rsp_code, data=rsp_hdrs)


def _bip_ev_server_delete_image_req(bip, data, data_len,
                                    ev_id=defs.BTP_BIP_EV_SERVER_DELETE_IMAGE_REQ,
                                    rsp_cmd='delete_image_rsp'):
    logging.debug('%s %r', _bip_ev_server_delete_image_req.__name__, data)
    addr, final, headers, _, _ = _parse_server_op_req(data)
    bip.rx(addr, ev_id, (final, headers))
    if bip.auto_response_enabled:
        # Spec 4.5.11 (Table 4.39): Img-Handle is mandatory and must be valid.
        req_handle = bip.image_db.extract_handle(headers)
        if not req_handle:
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.BAD_REQ, data=b'')
            return
        if not bip.image_db.has_image(req_handle):
            _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                                   rsp_code=OBEXRspCode.NOT_FOUND, data=b'')
            return
        rsp_code, rsp_data = bip.image_db.delete_image_rsp(final, headers)
        _bip_operation_rsp_cmd(rsp_cmd, bd_addr=addr,
                               rsp_code=rsp_code, data=rsp_data)


# Secondary (Archived Objects) request handlers.
#
# The 7 GET/DELETE operations below are valid on both the primary imaging
# connection and the Archived Objects secondary connection. These wrappers
# delegate to the shared base handlers but pass the secondary event opcode,
# the secondary response command key (so auto-response emits the correct
# BTP_BIP_SECOND_*_RSP opcode routed to inst->second_server), and a distinct
# chunk_key so chunked-response state does not collide with the primary.
def _bip_ev_second_server_get_caps_req(bip, data, data_len):
    _bip_ev_server_get_caps_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_CAPS_REQ,
        rsp_cmd='second_get_capabilities_rsp', chunk_key='second_get_caps')


def _bip_ev_second_server_get_image_list_req(bip, data, data_len):
    _bip_ev_server_get_image_list_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_LIST_REQ,
        rsp_cmd='second_get_image_list_rsp', chunk_key='second_get_image_list')


def _bip_ev_second_server_get_image_properties_req(bip, data, data_len):
    _bip_ev_server_get_image_properties_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_PROPERTIES_REQ,
        rsp_cmd='second_get_image_properties_rsp',
        chunk_key='second_get_image_properties')


def _bip_ev_second_server_get_image_req(bip, data, data_len):
    _bip_ev_server_get_image_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_REQ,
        rsp_cmd='second_get_image_rsp', chunk_key='second_get_image')


def _bip_ev_second_server_get_linked_thumbnail_req(bip, data, data_len):
    _bip_ev_server_get_linked_thumbnail_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_THUMBNAIL_REQ,
        rsp_cmd='second_get_linked_thumbnail_rsp',
        chunk_key='second_get_linked_thumbnail')


def _bip_ev_second_server_get_linked_attachment_req(bip, data, data_len):
    _bip_ev_server_get_linked_attachment_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_ATTACHMENT_REQ,
        rsp_cmd='second_get_linked_attachment_rsp',
        chunk_key='second_get_linked_attachment')


def _bip_ev_second_server_delete_image_req(bip, data, data_len):
    _bip_ev_server_delete_image_req(
        bip, data, data_len,
        ev_id=defs.BTP_BIP_EV_SECOND_SERVER_DELETE_IMAGE_REQ,
        rsp_cmd='second_delete_image_rsp')


def _bip_ev_server_start_print_req(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_server_start_print_req.__name__, data)
    # StartPrint is an OBEX PUT carrying the print-job object in
    # Body/End-of-Body headers, so it can span multiple packets and must
    # honour SRM/SRMP just like the other PUT handlers.
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_START_PRINT_REQ, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        _update_srm_state(conn, srm, srmp)
        rsp_code, rsp_data = bip.image_db.start_print_rsp(final, headers)
        _send_put_rsp_with_srm(conn, 'start_print_rsp', addr,
                               final, rsp_code, rsp_data)


def _bip_ev_server_start_archive_req(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_server_start_archive_req.__name__, data)
    # StartArchive is an OBEX PUT carrying the archive object in
    # Body/End-of-Body headers, so it can span multiple packets and must
    # honour SRM/SRMP just like the other PUT handlers.
    addr, final, headers, srm, srmp = _parse_server_op_req(data)
    bip.rx(addr, defs.BTP_BIP_EV_SERVER_START_ARCHIVE_REQ, (final, headers))
    if bip.auto_response_enabled:
        conn = bip.get_bip_connection(addr)
        _update_srm_state(conn, srm, srmp)
        rsp_code, rsp_data = bip.image_db.start_archive_rsp(final, headers)
        _send_put_rsp_with_srm(conn, 'start_archive_rsp', addr,
                               final, rsp_code, rsp_data)


def _bip_ev_client_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_client_connected.__name__, data)

    hdr_fmt = '<B6sBBHIH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, version, mopl, conn_id, body_data_len = \
        struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    logging.debug('BIP client connected: addr %s rsp_code %d version %d '
                  'mopl %d conn_id %d', addr, rsp_code, version, mopl,
                  conn_id)

    if rsp_code == OBEXRspCode.SUCCESS:
        bip.add_bip_obex_connection(addr)
        conn = bip.get_bip_connection(addr)
        if conn is not None:
            conn.get_session(BIPObexRole.PRIMARY).conn_id = conn_id


def _bip_ev_client_rsp(ev_id, name, bip, data, data_len):
    logging.debug('%s %r', name, data)

    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, body_data_len = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    conn = bip.get_bip_connection(addr)
    # Operate on the PRIMARY OBEX session explicitly (no attribute proxies).
    # is_srm_allowed() is a transport property and stays on the connection.
    sess = conn.get_session(BIPObexRole.PRIMARY) if conn else None

    # --- error path: rsp_code is neither SUCCESS nor CONTINUE ---
    if rsp_code not in (OBEXRspCode.SUCCESS, OBEXRspCode.CONTINUE, OBEXRspCode.PARTIAL_CONTENT):
        # discard any CONTINUE fragments buffered for this operation
        if sess:
            sess._pending_body.pop(ev_id, None)
            sess.reset_srm()
        bip.rx(addr, ev_id, (rsp_code, body))
        return

    # --- update remote SRM state from the received OBEX headers ---
    if sess and sess.is_srm_allowed():
        headers = obex_parse_headers(body)
        srm = headers.get(OBEXHdr.SRM, None)
        srmp = headers.get(OBEXHdr.SRMP, None)

        if srm == SRM_ENABLE:
            sess.srm_flags |= BIPSrmFlag.SRM_REMOTE

        if srmp == SRMP_WAIT:
            sess.srm_flags |= BIPSrmFlag.SRMP_REMOTE
        else:
            sess.srm_flags &= ~BIPSrmFlag.SRMP_REMOTE

    if rsp_code == OBEXRspCode.CONTINUE:
        # Buffer this CONTINUE fragment in a private reassembly buffer keyed by
        # ev_id. Fragments must NOT be pushed into data_rx: data_rx is the
        # queue the waiter (wait_for_operation_complete) polls, and mixing
        # partial fragments there both confuses the waiter and causes stale
        # fragments to be re-merged into the next operation's response.
        if sess is not None:
            sess._pending_body.setdefault(ev_id, bytearray()).extend(body)
    else:
        # rsp_code == SUCCESS or PARTIAL_CONTENT: merge only THIS operation's
        # buffered CONTINUE fragments with the final body, then push exactly one
        # entry carrying the real rsp_code to the rx queue for the waiter. Clear
        # the reassembly buffer afterwards so no leftover data can leak into a
        # subsequent operation.
        merged = bytearray()
        if sess is not None:
            merged.extend(sess._pending_body.pop(ev_id, bytearray()))
        merged.extend(body)
        if sess:
            sess.reset_srm()

        # Consistency hook: when a PutImage completes, register the image we
        # just sent into the local DB under the server-allocated Img-Handle so
        # a following PutLinkedThumbnail / PutLinkedAttachment references the
        # same image without the WID having to pass the handle explicitly.
        if ev_id == defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP:
            handle = obex_parse_headers(bytes(merged)).get(BIP_HDR_IMG_HANDLE)
            if handle:
                bip_register_put_image(handle, bd_addr=addr)
        bip.rx(addr, ev_id, (rsp_code, bytes(merged)))
        return

    # --- CONTINUE: drive the next request/packet ---
    get_cmd = _EV_TO_GET_CMD.get(ev_id)
    if get_cmd:
        if sess and sess.is_srm_full_speed():
            return
        _bip_operation_cmd(get_cmd, bd_addr=addr, final=1, data=b'',
                           continuation=True)
    elif sess and sess.pending_put is not None:
        if sess.is_srm_full_speed():
            while sess.pending_put is not None:

                _send_continuation(addr)
        else:
            _send_continuation(addr)


def bip_get_put_image_handle():
    img = get_stack().bip.image_db.last_put_image
    if img is None:
        return None
    return img.handle


def _bip_ev_client_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_client_disconnected.__name__, data)

    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, body_data_len = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    bip.remove_bip_obex_connection(addr)
    bip.rx(addr, defs.BTP_BIP_EV_CLIENT_DISCONNECTED, (rsp_code, body))


def _bip_ev_client_aborted(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_ABORTED,
                       'client_aborted', bip, data, data_len)


def _bip_ev_client_get_caps_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP,
                       'client_get_caps_rsp', bip, data, data_len)


def _bip_ev_client_get_image_list_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP,
                       'client_get_image_list_rsp', bip, data, data_len)


def _bip_ev_client_get_image_properties_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP,
                       'client_get_image_properties_rsp', bip, data, data_len)


def _bip_ev_client_get_image_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP,
                       'client_get_image_rsp', bip, data, data_len)


def _bip_ev_client_get_linked_thumbnail_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP,
                       'client_get_linked_thumbnail_rsp', bip, data, data_len)


def _bip_ev_client_get_linked_attachment_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP,
                       'client_get_linked_attachment_rsp', bip, data, data_len)


def _bip_ev_client_get_partial_image_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP,
                       'client_get_partial_image_rsp', bip, data, data_len)


def _bip_ev_client_get_monitoring_image_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_MONITORING_IMAGE_RSP,
                       'client_get_monitoring_image_rsp', bip, data, data_len)


def _bip_ev_client_get_status_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_GET_STATUS_RSP,
                       'client_get_status_rsp', bip, data, data_len)


def _bip_ev_client_put_image_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP,
                       'client_put_image_rsp', bip, data, data_len)


def _bip_ev_client_put_linked_thumbnail_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_PUT_LINKED_THUMBNAIL_RSP,
                       'client_put_linked_thumbnail_rsp', bip, data, data_len)


def _bip_ev_client_put_linked_attachment_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_PUT_LINKED_ATTACHMENT_RSP,
                       'client_put_linked_attachment_rsp', bip, data, data_len)


def _bip_ev_client_remote_display_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_REMOTE_DISPLAY_RSP,
                       'client_remote_display_rsp', bip, data, data_len)


def _bip_ev_client_delete_image_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_DELETE_IMAGE_RSP,
                       'client_delete_image_rsp', bip, data, data_len)


def _bip_ev_client_start_print_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_START_PRINT_RSP,
                       'client_start_print_rsp', bip, data, data_len)


def _bip_ev_client_start_archive_rsp(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_CLIENT_START_ARCHIVE_RSP,
                       'client_start_archive_rsp', bip, data, data_len)


def _bip_ev_sdp_discovered(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_sdp_discovered.__name__, data)

    fmt = '<B6sBHBHI'
    _, addr, channel, psm, caps, features, functions = \
        struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)

    logging.debug('BIP SDP discovered: addr %s channel %d psm 0x%04x '
                  'caps 0x%02x features 0x%04x functions 0x%08x',
                  addr, channel, psm, caps, features, functions)

    bip.add_sdp_connection(addr, channel, psm, caps, features, functions)


def _bip_ev_second_server_connect_req(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_server_connect_req.__name__, data)

    hdr_fmt = '<B6sBHH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, version, mopl, body_data_len = struct.unpack_from(
        hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    logging.debug('BIP second server connect req: addr %s version %d mopl %d',
                  addr, version, mopl)

    headers = obex_parse_headers(body)
    target = headers.get(OBEXHdr.TARGET)
    if target is not None:
        conn = bip.get_bip_connection(addr)
        if conn:
            # Store the target on the SECONDARY OBEX session so it stays
            # isolated from the primary session's target/conn_id.
            sess = conn.get_or_add_session(BIPObexRole.SECONDARY)
            sess.conn_info['target'] = target
            logging.debug('BIP stored second target: %s', target.hex())

    bip.rx(addr, defs.BTP_BIP_EV_SECOND_SERVER_CONNECT_REQ,
           (version, mopl, body))


def _bip_ev_second_server_disconnect_req(bip, data, data_len):
    _bip_ev_server_data_req(defs.BTP_BIP_EV_SECOND_SERVER_DISCONNECT_REQ,
                            'second_server_disconnect_req', bip, data,
                            data_len)


def _bip_ev_second_server_abort_req(bip, data, data_len):
    _bip_ev_server_data_req(defs.BTP_BIP_EV_SECOND_SERVER_ABORT_REQ,
                            'second_server_abort_req', bip, data, data_len)


def _bip_ev_second_client_connected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_client_connected.__name__, data)

    hdr_fmt = '<B6sBBHIH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, version, mopl, conn_id, body_data_len = \
        struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    logging.debug('BIP second client connected: addr %s rsp_code %d '
                  'version %d mopl %d conn_id %d', addr, rsp_code, version,
                  mopl, conn_id)

    if rsp_code == OBEXRspCode.SUCCESS:
        bip.add_bip_obex_connection(addr, role=BIPObexRole.SECONDARY)
        conn = bip.get_bip_connection(addr)
        if conn is not None:
            sess = conn.get_or_add_session(BIPObexRole.SECONDARY)
            sess.conn_id = conn_id


def _bip_ev_second_client_disconnected(bip, data, data_len):
    logging.debug('%s %r', _bip_ev_second_client_disconnected.__name__, data)

    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, body_data_len = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    bip.remove_bip_obex_connection(addr, role=BIPObexRole.SECONDARY)
    bip.rx(addr, defs.BTP_BIP_EV_SECOND_CLIENT_DISCONNECTED, (rsp_code, body))


def _bip_ev_second_client_aborted(bip, data, data_len):
    _bip_ev_client_rsp(defs.BTP_BIP_EV_SECOND_CLIENT_ABORTED,
                       'second_client_aborted', bip, data, data_len)


# Map each secondary client response event to the secondary client request
# command used to drive the next OBEX packet on an OBEX CONTINUE. Mirrors
# _EV_TO_GET_CMD for the primary imaging connection.
_EV_TO_SECOND_GET_CMD = {
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP: 'second_get_capabilities',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP: 'second_get_image_list',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP: 'second_get_image_properties',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP: 'second_get_image',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP: 'second_get_linked_thumbnail',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP: 'second_get_linked_attachment',
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP: 'second_get_partial_image',
    defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP: 'second_delete_image',
}


def _bip_ev_second_client_rsp(ev_id, name, bip, data, data_len):
    # Secondary (Archived/Referenced Objects) client response handler. Mirrors
    # _bip_ev_client_rsp but resolves SRM state, reassembly buffers and the rx
    # queue from the SECONDARY OBEX session so the response is isolated from the
    # primary imaging connection.
    logging.debug('%s %r', name, data)

    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)
    _, addr, rsp_code, body_data_len = struct.unpack_from(hdr_fmt, data)
    body = data[hdr_len:hdr_len + body_data_len]
    addr = le_bytes_to_hex_str(addr)

    conn = bip.get_bip_connection(addr)
    sess = conn.get_or_add_session(BIPObexRole.SECONDARY) if conn else None

    # --- error path: rsp_code is neither SUCCESS nor CONTINUE ---
    if rsp_code not in (OBEXRspCode.SUCCESS, OBEXRspCode.CONTINUE,
                        OBEXRspCode.PARTIAL_CONTENT):
        if sess is not None:
            sess._pending_body.pop(ev_id, None)
            sess.reset_srm()
        bip.rx(addr, ev_id, (rsp_code, body), role=BIPObexRole.SECONDARY)
        return

    # --- update remote SRM state from the received OBEX headers ---
    if sess is not None and sess.is_srm_allowed():
        headers = obex_parse_headers(body)
        srm = headers.get(OBEXHdr.SRM, None)
        srmp = headers.get(OBEXHdr.SRMP, None)

        if srm == SRM_ENABLE:
            sess.srm_flags |= BIPSrmFlag.SRM_REMOTE

        if srmp == SRMP_WAIT:
            sess.srm_flags |= BIPSrmFlag.SRMP_REMOTE
        else:
            sess.srm_flags &= ~BIPSrmFlag.SRMP_REMOTE

    if rsp_code == OBEXRspCode.CONTINUE:
        if sess is not None:
            sess._pending_body.setdefault(ev_id, bytearray()).extend(body)
    else:
        merged = bytearray()
        if sess is not None:
            merged.extend(sess._pending_body.pop(ev_id, bytearray()))
        merged.extend(body)
        if sess is not None:
            sess.reset_srm()
        bip.rx(addr, ev_id, (rsp_code, bytes(merged)),
               role=BIPObexRole.SECONDARY)
        return

    # --- CONTINUE: drive the next request/packet over the secondary session ---
    get_cmd = _EV_TO_SECOND_GET_CMD.get(ev_id)
    if get_cmd:
        if sess is not None and sess.is_srm_full_speed():
            return
        _bip_second_operation_cmd(get_cmd, bd_addr=addr, final=1, data=b'',
                                  continuation=True)


def _bip_ev_second_client_get_caps_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP,
                              'second_client_get_caps_rsp', bip, data, data_len)


def _bip_ev_second_client_get_image_list_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP,
                              'second_client_get_image_list_rsp', bip, data,
                              data_len)


def _bip_ev_second_client_get_image_properties_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP,
        'second_client_get_image_properties_rsp', bip, data, data_len)


def _bip_ev_second_client_get_image_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP,
                              'second_client_get_image_rsp', bip, data,
                              data_len)


def _bip_ev_second_client_get_linked_thumbnail_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP,
        'second_client_get_linked_thumbnail_rsp', bip, data, data_len)


def _bip_ev_second_client_get_linked_attachment_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP,
        'second_client_get_linked_attachment_rsp', bip, data, data_len)


def _bip_ev_second_client_get_partial_image_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP,
        'second_client_get_partial_image_rsp', bip, data, data_len)


def _bip_ev_second_client_delete_image_rsp(bip, data, data_len):
    _bip_ev_second_client_rsp(defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP,
                              'second_client_delete_image_rsp', bip, data,
                              data_len)


BIP_EV_HANDLERS = {


    defs.BTP_BIP_EV_RFCOMM_CONNECTED: _bip_ev_rfcomm_connected,
    defs.BTP_BIP_EV_RFCOMM_DISCONNECTED: _bip_ev_rfcomm_disconnected,
    defs.BTP_BIP_EV_L2CAP_CONNECTED: _bip_ev_l2cap_connected,
    defs.BTP_BIP_EV_L2CAP_DISCONNECTED: _bip_ev_l2cap_disconnected,
    defs.BTP_BIP_EV_SECOND_RFCOMM_CONNECTED: _bip_ev_second_rfcomm_connected,
    defs.BTP_BIP_EV_SECOND_RFCOMM_DISCONNECTED: _bip_ev_second_rfcomm_disconnected,
    defs.BTP_BIP_EV_SECOND_L2CAP_CONNECTED: _bip_ev_second_l2cap_connected,
    defs.BTP_BIP_EV_SECOND_L2CAP_DISCONNECTED: _bip_ev_second_l2cap_disconnected,
    defs.BTP_BIP_EV_SERVER_CONNECT_REQ: _bip_ev_server_connect_req,
    defs.BTP_BIP_EV_SERVER_DISCONNECT_REQ: _bip_ev_server_disconnect_req,
    defs.BTP_BIP_EV_SERVER_ABORT_REQ: _bip_ev_server_abort_req,
    defs.BTP_BIP_EV_SERVER_GET_CAPS_REQ: _bip_ev_server_get_caps_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_LIST_REQ: _bip_ev_server_get_image_list_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_PROPERTIES_REQ: _bip_ev_server_get_image_properties_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_REQ: _bip_ev_server_get_image_req,
    defs.BTP_BIP_EV_SERVER_GET_LINKED_THUMBNAIL_REQ: _bip_ev_server_get_linked_thumbnail_req,
    defs.BTP_BIP_EV_SERVER_GET_LINKED_ATTACHMENT_REQ: _bip_ev_server_get_linked_attachment_req,
    defs.BTP_BIP_EV_SERVER_GET_PARTIAL_IMAGE_REQ: _bip_ev_server_get_partial_image_req,
    defs.BTP_BIP_EV_SERVER_GET_MONITORING_IMAGE_REQ: _bip_ev_server_get_monitoring_image_req,
    defs.BTP_BIP_EV_SERVER_GET_STATUS_REQ: _bip_ev_server_get_status_req,
    defs.BTP_BIP_EV_SERVER_PUT_IMAGE_REQ: _bip_ev_server_put_image_req,
    defs.BTP_BIP_EV_SERVER_PUT_LINKED_THUMBNAIL_REQ: _bip_ev_server_put_linked_thumbnail_req,
    defs.BTP_BIP_EV_SERVER_PUT_LINKED_ATTACHMENT_REQ: _bip_ev_server_put_linked_attachment_req,
    defs.BTP_BIP_EV_SERVER_REMOTE_DISPLAY_REQ: _bip_ev_server_remote_display_req,
    defs.BTP_BIP_EV_SERVER_DELETE_IMAGE_REQ: _bip_ev_server_delete_image_req,
    defs.BTP_BIP_EV_SERVER_START_PRINT_REQ: _bip_ev_server_start_print_req,
    defs.BTP_BIP_EV_SERVER_START_ARCHIVE_REQ: _bip_ev_server_start_archive_req,
    defs.BTP_BIP_EV_CLIENT_CONNECTED: _bip_ev_client_connected,
    defs.BTP_BIP_EV_CLIENT_DISCONNECTED: _bip_ev_client_disconnected,
    defs.BTP_BIP_EV_CLIENT_ABORTED: _bip_ev_client_aborted,
    defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP: _bip_ev_client_get_caps_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP: _bip_ev_client_get_image_list_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP: _bip_ev_client_get_image_properties_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP: _bip_ev_client_get_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP: _bip_ev_client_get_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP: _bip_ev_client_get_linked_attachment_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP: _bip_ev_client_get_partial_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_MONITORING_IMAGE_RSP: _bip_ev_client_get_monitoring_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_STATUS_RSP: _bip_ev_client_get_status_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP: _bip_ev_client_put_image_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_LINKED_THUMBNAIL_RSP: _bip_ev_client_put_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_LINKED_ATTACHMENT_RSP: _bip_ev_client_put_linked_attachment_rsp,
    defs.BTP_BIP_EV_CLIENT_REMOTE_DISPLAY_RSP: _bip_ev_client_remote_display_rsp,
    defs.BTP_BIP_EV_CLIENT_DELETE_IMAGE_RSP: _bip_ev_client_delete_image_rsp,
    defs.BTP_BIP_EV_CLIENT_START_PRINT_RSP: _bip_ev_client_start_print_rsp,
    defs.BTP_BIP_EV_CLIENT_START_ARCHIVE_RSP: _bip_ev_client_start_archive_rsp,
    defs.BTP_BIP_EV_SDP_DISCOVERED: _bip_ev_sdp_discovered,
    defs.BTP_BIP_EV_SECOND_SERVER_CONNECT_REQ: _bip_ev_second_server_connect_req,
    defs.BTP_BIP_EV_SECOND_SERVER_DISCONNECT_REQ: _bip_ev_second_server_disconnect_req,
    defs.BTP_BIP_EV_SECOND_SERVER_ABORT_REQ: _bip_ev_second_server_abort_req,
    defs.BTP_BIP_EV_SECOND_CLIENT_CONNECTED: _bip_ev_second_client_connected,
    defs.BTP_BIP_EV_SECOND_CLIENT_DISCONNECTED: _bip_ev_second_client_disconnected,
    defs.BTP_BIP_EV_SECOND_CLIENT_ABORTED: _bip_ev_second_client_aborted,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_CAPS_REQ: _bip_ev_second_server_get_caps_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_LIST_REQ: _bip_ev_second_server_get_image_list_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_PROPERTIES_REQ: _bip_ev_second_server_get_image_properties_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_REQ: _bip_ev_second_server_get_image_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_THUMBNAIL_REQ: _bip_ev_second_server_get_linked_thumbnail_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_ATTACHMENT_REQ: _bip_ev_second_server_get_linked_attachment_req,
    defs.BTP_BIP_EV_SECOND_SERVER_DELETE_IMAGE_REQ: _bip_ev_second_server_delete_image_req,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP: _bip_ev_second_client_get_caps_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP: _bip_ev_second_client_get_image_list_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP: _bip_ev_second_client_get_image_properties_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP: _bip_ev_second_client_get_image_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP: _bip_ev_second_client_get_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP: _bip_ev_second_client_get_linked_attachment_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP: _bip_ev_second_client_get_partial_image_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP: _bip_ev_second_client_delete_image_rsp,
}


# ============================================================================
# BIPEventHandler

# ============================================================================

class BIPEventHandler:

    def __init__(self, bip):
        self.bip = bip
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(
                target=self._process_events, daemon=True)
            self.worker_thread.start()
            logging.debug("BIP event handler started")

    def stop(self):
        if self.running:
            self.running = False
            self.event_queue.put(None)
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logging.debug("BIP event handler stopped")

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
                logging.error(f"Error processing BIP event: {e}",
                              exc_info=True)

    def _handle_event(self, event_id, data, data_len):
        handler = BIP_EV_HANDLERS.get(event_id)
        if handler:
            try:
                handler(self.bip, data, data_len)
            except Exception as e:
                logging.error(
                    f"Error in BIP event handler {handler.__name__}: {e}",
                    exc_info=True)
        else:
            logging.warning(f"No handler for BIP event {event_id}")


# ============================================================================
# Public Event Functions (enqueue to BIPEventHandler)
# ============================================================================

def bip_ev_rfcomm_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_rfcomm_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_RFCOMM_CONNECTED, data, data_len)


def bip_ev_rfcomm_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_rfcomm_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_RFCOMM_DISCONNECTED, data, data_len)


def bip_ev_l2cap_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_l2cap_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_L2CAP_CONNECTED, data, data_len)


def bip_ev_l2cap_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_l2cap_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_L2CAP_DISCONNECTED, data, data_len)


def bip_ev_second_rfcomm_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_rfcomm_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_RFCOMM_CONNECTED, data, data_len)


def bip_ev_second_rfcomm_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_rfcomm_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_RFCOMM_DISCONNECTED, data, data_len)


def bip_ev_second_l2cap_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_l2cap_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_L2CAP_CONNECTED, data, data_len)


def bip_ev_second_l2cap_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_l2cap_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_L2CAP_DISCONNECTED, data, data_len)


def bip_ev_server_connect_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_connect_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_CONNECT_REQ, data, data_len)


def bip_ev_server_disconnect_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_disconnect_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_DISCONNECT_REQ, data, data_len)


def bip_ev_server_abort_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_abort_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_ABORT_REQ, data, data_len)


def bip_ev_server_get_caps_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_get_caps_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_CAPS_REQ, data, data_len)


def bip_ev_server_get_image_list_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_get_image_list_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_IMAGE_LIST_REQ, data, data_len)


def bip_ev_server_get_image_properties_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_get_image_properties_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_IMAGE_PROPERTIES_REQ, data, data_len)


def bip_ev_server_get_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_get_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_IMAGE_REQ, data, data_len)


def bip_ev_server_get_linked_thumbnail_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_get_linked_thumbnail_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_LINKED_THUMBNAIL_REQ, data, data_len)


def bip_ev_server_get_linked_attachment_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_get_linked_attachment_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_LINKED_ATTACHMENT_REQ, data, data_len)


def bip_ev_server_get_partial_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_get_partial_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_PARTIAL_IMAGE_REQ, data, data_len)


def bip_ev_server_get_monitoring_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_get_monitoring_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_MONITORING_IMAGE_REQ, data, data_len)


def bip_ev_server_get_status_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_get_status_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_GET_STATUS_REQ, data, data_len)


def bip_ev_server_put_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_put_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_PUT_IMAGE_REQ, data, data_len)


def bip_ev_server_put_linked_thumbnail_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_put_linked_thumbnail_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_PUT_LINKED_THUMBNAIL_REQ, data, data_len)


def bip_ev_server_put_linked_attachment_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_server_put_linked_attachment_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_PUT_LINKED_ATTACHMENT_REQ, data, data_len)


def bip_ev_server_remote_display_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_remote_display_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_REMOTE_DISPLAY_REQ, data, data_len)


def bip_ev_server_delete_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_delete_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_DELETE_IMAGE_REQ, data, data_len)


def bip_ev_server_start_print_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_start_print_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_START_PRINT_REQ, data, data_len)


def bip_ev_server_start_archive_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_server_start_archive_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SERVER_START_ARCHIVE_REQ, data, data_len)


def bip_ev_client_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_CONNECTED, data, data_len)


def bip_ev_client_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_DISCONNECTED, data, data_len)


def bip_ev_client_aborted(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_aborted.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_ABORTED, data, data_len)


def bip_ev_client_get_caps_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_get_caps_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP, data, data_len)


def bip_ev_client_get_image_list_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_get_image_list_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP, data, data_len)


def bip_ev_client_get_image_properties_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_get_image_properties_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP, data, data_len)


def bip_ev_client_get_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_get_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP, data, data_len)


def bip_ev_client_get_linked_thumbnail_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_get_linked_thumbnail_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP, data, data_len)


def bip_ev_client_get_linked_attachment_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_get_linked_attachment_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP, data, data_len)


def bip_ev_client_get_partial_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_get_partial_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP, data, data_len)


def bip_ev_client_get_monitoring_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_get_monitoring_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_MONITORING_IMAGE_RSP, data, data_len)


def bip_ev_client_get_status_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_get_status_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_GET_STATUS_RSP, data, data_len)


def bip_ev_client_put_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_put_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP, data, data_len)


def bip_ev_client_put_linked_thumbnail_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_put_linked_thumbnail_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_PUT_LINKED_THUMBNAIL_RSP, data, data_len)


def bip_ev_client_put_linked_attachment_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_client_put_linked_attachment_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_PUT_LINKED_ATTACHMENT_RSP, data, data_len)


def bip_ev_client_remote_display_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_remote_display_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_REMOTE_DISPLAY_RSP, data, data_len)


def bip_ev_client_delete_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_delete_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_DELETE_IMAGE_RSP, data, data_len)


def bip_ev_client_start_print_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_start_print_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_START_PRINT_RSP, data, data_len)


def bip_ev_client_start_archive_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_client_start_archive_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_CLIENT_START_ARCHIVE_RSP, data, data_len)


def bip_ev_sdp_discovered(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_sdp_discovered.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SDP_DISCOVERED, data, data_len)


def bip_ev_second_server_connect_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_server_connect_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_CONNECT_REQ, data, data_len)


def bip_ev_second_server_disconnect_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_disconnect_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_DISCONNECT_REQ, data, data_len)


def bip_ev_second_server_abort_req(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_server_abort_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_ABORT_REQ, data, data_len)


def bip_ev_second_client_connected(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_client_connected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_CONNECTED, data, data_len)


def bip_ev_second_client_disconnected(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_disconnected.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_DISCONNECTED, data, data_len)


def bip_ev_second_client_aborted(bip, data, data_len):
    logging.debug('%s %r %r %r', bip_ev_second_client_aborted.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_ABORTED, data, data_len)


def bip_ev_second_server_get_caps_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_caps_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_CAPS_REQ, data, data_len)


def bip_ev_second_server_get_image_list_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_image_list_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_LIST_REQ, data, data_len)


def bip_ev_second_server_get_image_properties_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_image_properties_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_PROPERTIES_REQ, data, data_len)


def bip_ev_second_server_get_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_REQ, data, data_len)


def bip_ev_second_server_get_linked_thumbnail_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_linked_thumbnail_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_THUMBNAIL_REQ, data, data_len)


def bip_ev_second_server_get_linked_attachment_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_get_linked_attachment_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_ATTACHMENT_REQ, data, data_len)


def bip_ev_second_server_delete_image_req(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_server_delete_image_req.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_SERVER_DELETE_IMAGE_REQ, data, data_len)


def bip_ev_second_client_get_caps_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_caps_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP, data, data_len)


def bip_ev_second_client_get_image_list_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_image_list_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP, data, data_len)


def bip_ev_second_client_get_image_properties_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_image_properties_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP, data, data_len)


def bip_ev_second_client_get_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP, data, data_len)


def bip_ev_second_client_get_linked_thumbnail_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_linked_thumbnail_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP, data, data_len)


def bip_ev_second_client_get_linked_attachment_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_linked_attachment_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP, data, data_len)


def bip_ev_second_client_get_partial_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_get_partial_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP, data, data_len)


def bip_ev_second_client_delete_image_rsp(bip, data, data_len):
    logging.debug('%s %r %r %r',
                  bip_ev_second_client_delete_image_rsp.__name__,
                  bip, data, data_len)
    bip.event_handler.enqueue_event(
        defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP, data, data_len)


# ============================================================================
# Wait helpers
# ============================================================================

def bip_wait_for_client_connected(bd_addr=None, role=BIPObexRole.PRIMARY,
                                   timeout=30):
    # Wait until the OBEX session for the given role has completed its OBEX
    # CONNECT. For the PRIMARY role this is the initial client connection; for
    # a SECONDARY role (e.g. SEC_ARCHIVED) it is the additional OBEX session
    # opened over the same GOEP transport, reported by the IUT via
    # BTP_BIP_EV_SECOND_CLIENT_CONNECTED. Unlike the transport-level helpers,
    # this does not treat an existing primary connection object as success.
    logging.debug("%s %r %r %r", bip_wait_for_client_connected.__name__,
                  bd_addr, role, timeout)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.is_bip_obex_connected(
        bd_addr, role=role, timeout=timeout)


def bip_has_pending_second_connect(bd_addr=None,
                                   bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    """Return True if a secondary (Referenced/Archived Objects) server OBEX
    CONNECT is awaiting a response.

    Wraps the stack-layer predicate so the WID layer does not access the
    stack directly.
    """
    logging.debug("%s %r %r", bip_has_pending_second_connect.__name__,
                  bd_addr, bd_addr_type)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.has_pending_second_connect(bd_addr)


def bip_wait_for_transport_connected(bd_addr=None, timeout=30):
    logging.debug("%s %r %r", bip_wait_for_transport_connected.__name__,
                  bd_addr, timeout)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.wait_for_bip_connection(bd_addr, timeout)


def bip_wait_for_transport_disconnected(bd_addr=None, timeout=30):
    logging.debug("%s %r %r", bip_wait_for_transport_disconnected.__name__,
                  bd_addr, timeout)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.wait_for_bip_disconnection(bd_addr, timeout)


def bip_wait_for_sdp_finished(bd_addr=None, timeout=30):
    logging.debug("%s %r %r", bip_wait_for_sdp_finished.__name__,
                  bd_addr, timeout)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.wait_for_sdp_finished(bd_addr, timeout)


def bip_get_sdp_connection(bd_addr=None):
    logging.debug("%s %r", bip_get_sdp_connection.__name__, bd_addr)
    bd_addr = pts_addr_get(bd_addr)
    return get_stack().bip.get_sdp_connection(bd_addr)


# Event handlers dictionary (public - maps to enqueue wrappers)
BIP_EV = {
    defs.BTP_BIP_EV_RFCOMM_CONNECTED: bip_ev_rfcomm_connected,
    defs.BTP_BIP_EV_RFCOMM_DISCONNECTED: bip_ev_rfcomm_disconnected,
    defs.BTP_BIP_EV_L2CAP_CONNECTED: bip_ev_l2cap_connected,
    defs.BTP_BIP_EV_L2CAP_DISCONNECTED: bip_ev_l2cap_disconnected,
    defs.BTP_BIP_EV_SECOND_RFCOMM_CONNECTED: bip_ev_second_rfcomm_connected,
    defs.BTP_BIP_EV_SECOND_RFCOMM_DISCONNECTED: bip_ev_second_rfcomm_disconnected,
    defs.BTP_BIP_EV_SECOND_L2CAP_CONNECTED: bip_ev_second_l2cap_connected,
    defs.BTP_BIP_EV_SECOND_L2CAP_DISCONNECTED: bip_ev_second_l2cap_disconnected,
    defs.BTP_BIP_EV_SERVER_CONNECT_REQ: bip_ev_server_connect_req,
    defs.BTP_BIP_EV_SERVER_DISCONNECT_REQ: bip_ev_server_disconnect_req,
    defs.BTP_BIP_EV_SERVER_ABORT_REQ: bip_ev_server_abort_req,
    defs.BTP_BIP_EV_SERVER_GET_CAPS_REQ: bip_ev_server_get_caps_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_LIST_REQ: bip_ev_server_get_image_list_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_PROPERTIES_REQ: bip_ev_server_get_image_properties_req,
    defs.BTP_BIP_EV_SERVER_GET_IMAGE_REQ: bip_ev_server_get_image_req,
    defs.BTP_BIP_EV_SERVER_GET_LINKED_THUMBNAIL_REQ: bip_ev_server_get_linked_thumbnail_req,
    defs.BTP_BIP_EV_SERVER_GET_LINKED_ATTACHMENT_REQ: bip_ev_server_get_linked_attachment_req,
    defs.BTP_BIP_EV_SERVER_GET_PARTIAL_IMAGE_REQ: bip_ev_server_get_partial_image_req,
    defs.BTP_BIP_EV_SERVER_GET_MONITORING_IMAGE_REQ: bip_ev_server_get_monitoring_image_req,
    defs.BTP_BIP_EV_SERVER_GET_STATUS_REQ: bip_ev_server_get_status_req,
    defs.BTP_BIP_EV_SERVER_PUT_IMAGE_REQ: bip_ev_server_put_image_req,
    defs.BTP_BIP_EV_SERVER_PUT_LINKED_THUMBNAIL_REQ: bip_ev_server_put_linked_thumbnail_req,
    defs.BTP_BIP_EV_SERVER_PUT_LINKED_ATTACHMENT_REQ: bip_ev_server_put_linked_attachment_req,
    defs.BTP_BIP_EV_SERVER_REMOTE_DISPLAY_REQ: bip_ev_server_remote_display_req,
    defs.BTP_BIP_EV_SERVER_DELETE_IMAGE_REQ: bip_ev_server_delete_image_req,
    defs.BTP_BIP_EV_SERVER_START_PRINT_REQ: bip_ev_server_start_print_req,
    defs.BTP_BIP_EV_SERVER_START_ARCHIVE_REQ: bip_ev_server_start_archive_req,
    defs.BTP_BIP_EV_CLIENT_CONNECTED: bip_ev_client_connected,
    defs.BTP_BIP_EV_CLIENT_DISCONNECTED: bip_ev_client_disconnected,
    defs.BTP_BIP_EV_CLIENT_ABORTED: bip_ev_client_aborted,
    defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP: bip_ev_client_get_caps_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP: bip_ev_client_get_image_list_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP: bip_ev_client_get_image_properties_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP: bip_ev_client_get_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP: bip_ev_client_get_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP: bip_ev_client_get_linked_attachment_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP: bip_ev_client_get_partial_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_MONITORING_IMAGE_RSP: bip_ev_client_get_monitoring_image_rsp,
    defs.BTP_BIP_EV_CLIENT_GET_STATUS_RSP: bip_ev_client_get_status_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP: bip_ev_client_put_image_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_LINKED_THUMBNAIL_RSP: bip_ev_client_put_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_CLIENT_PUT_LINKED_ATTACHMENT_RSP: bip_ev_client_put_linked_attachment_rsp,
    defs.BTP_BIP_EV_CLIENT_REMOTE_DISPLAY_RSP: bip_ev_client_remote_display_rsp,
    defs.BTP_BIP_EV_CLIENT_DELETE_IMAGE_RSP: bip_ev_client_delete_image_rsp,
    defs.BTP_BIP_EV_CLIENT_START_PRINT_RSP: bip_ev_client_start_print_rsp,
    defs.BTP_BIP_EV_CLIENT_START_ARCHIVE_RSP: bip_ev_client_start_archive_rsp,
    defs.BTP_BIP_EV_SDP_DISCOVERED: bip_ev_sdp_discovered,
    defs.BTP_BIP_EV_SECOND_SERVER_CONNECT_REQ: bip_ev_second_server_connect_req,
    defs.BTP_BIP_EV_SECOND_SERVER_DISCONNECT_REQ: bip_ev_second_server_disconnect_req,
    defs.BTP_BIP_EV_SECOND_SERVER_ABORT_REQ: bip_ev_second_server_abort_req,
    defs.BTP_BIP_EV_SECOND_CLIENT_CONNECTED: bip_ev_second_client_connected,
    defs.BTP_BIP_EV_SECOND_CLIENT_DISCONNECTED: bip_ev_second_client_disconnected,
    defs.BTP_BIP_EV_SECOND_CLIENT_ABORTED: bip_ev_second_client_aborted,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_CAPS_REQ: bip_ev_second_server_get_caps_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_LIST_REQ: bip_ev_second_server_get_image_list_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_PROPERTIES_REQ: bip_ev_second_server_get_image_properties_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_IMAGE_REQ: bip_ev_second_server_get_image_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_THUMBNAIL_REQ: bip_ev_second_server_get_linked_thumbnail_req,
    defs.BTP_BIP_EV_SECOND_SERVER_GET_LINKED_ATTACHMENT_REQ: bip_ev_second_server_get_linked_attachment_req,
    defs.BTP_BIP_EV_SECOND_SERVER_DELETE_IMAGE_REQ: bip_ev_second_server_delete_image_req,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP: bip_ev_second_client_get_caps_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP: bip_ev_second_client_get_image_list_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP: bip_ev_second_client_get_image_properties_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP: bip_ev_second_client_get_image_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP: bip_ev_second_client_get_linked_thumbnail_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP: bip_ev_second_client_get_linked_attachment_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP: bip_ev_second_client_get_partial_image_rsp,
    defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP: bip_ev_second_client_delete_image_rsp,
}
