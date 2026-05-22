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
import logging
import queue
import struct
import threading
import time
from typing import Union

from autopts.ptsprojects.stack import PBAPInfo, PBAPSrmState, get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import (
    OBEXAuthTag,
    OBEXHdr,
    OBEXRspCode,
    PBAPAppParamTag,
    PBAPPropertySelector,
    PBAPRole,
    PBAPSupportedFeature,
    PBAPTransportType,
    addr_str_to_le_bytes,
)


def bt_pbap_add_header_app_param(tlv_dict: dict):
    """
    Each TLV item can be:
    - A tuple: (tag, value) where value is auto-encoded based on tag type
    - A tuple: (tag, data_len, data) for raw data (legacy support)
    - A dict: {tag: data} for raw data format

    Auto-encoding rules based on tag type:
    - 1-byte tags: value as int -> packed as uint8
    - 2-byte tags: value as int -> packed as big-endian uint16
    - 4-byte tags: value as int -> packed as big-endian uint32
    - 8-byte tags: value as int -> packed as big-endian uint64
    - String tags: value as str or bytes -> used as-is
    - 16-byte tags (folder versions, database ID): fixed 16-byte length
    """
    logging.debug("%s %r", bt_pbap_add_header_app_param.__name__, tlv_dict)

    if not tlv_dict:
        raise ValueError("TLV list must not be empty")

    # Tag type definitions based on PBAP spec and C implementation
    TAG_1BYTE = [
        PBAPAppParamTag.ORDER,
        PBAPAppParamTag.FORMAT,
        PBAPAppParamTag.SEARCH_PROPERTY,
        PBAPAppParamTag.NEW_MISSED_CALLS,
        PBAPAppParamTag.RESET_NEW_MISSED_CALLS,
        PBAPAppParamTag.VCARD_SELECTOR_OPERATOR
    ]
    TAG_2BYTE = [
        PBAPAppParamTag.MAX_LIST_COUNT,
        PBAPAppParamTag.LIST_START_OFFSET,
        PBAPAppParamTag.PHONEBOOK_SIZE
    ]
    TAG_4BYTE = [
        PBAPAppParamTag.SUPPORTED_FEATURES
    ]
    TAG_8BYTE = [
        PBAPAppParamTag.PROPERTY_SELECTOR,
        PBAPAppParamTag.VCARD_SELECTOR
    ]
    TAG_16BYTE = [
        PBAPAppParamTag.PRIMARY_FOLDER_VERSION,
        PBAPAppParamTag.SECONDARY_FOLDER_VERSION,
        PBAPAppParamTag.DATABASE_IDENTIFIER
    ]
    TAG_STRING = [
        PBAPAppParamTag.SEARCH_VALUE
    ]

    tlv_data = bytearray()
    for tag, value in tlv_dict.items():
        if tag in TAG_1BYTE:
            data = struct.pack('B', value)
        elif tag in TAG_2BYTE:
            data = struct.pack('>H', value)
        elif tag in TAG_4BYTE:
            data = struct.pack('>I', value)
        elif tag in TAG_8BYTE:
            data = struct.pack('>Q', value)
        elif tag in TAG_16BYTE:
            if isinstance(value, str):
                if len(value) == 32:
                    data = bytes.fromhex(value)
                else:
                    data = value.encode('utf-8')[:16].ljust(16, b'\x00')
            elif isinstance(value, bytes):
                if len(value) < 16:
                    data = value.ljust(16, b'\x00')
                else:
                    data = value[:16]
            else:
                data = bytes(value)[:16].ljust(16, b'\x00')
        elif tag in TAG_STRING:
            if isinstance(value, str):
                data = value.encode('utf-8')
                data = bytearray(value.encode('utf-8'))
                data.extend(b'\x00')
            elif isinstance(value, bytes):
                data = value
            else:
                data = bytes(value)
        else:
            raise ValueError(f"Unknown tag type: 0x{tag:02X}")

        tlv_data.append(tag)
        tlv_data.append(len(data))
        tlv_data.extend(data)

    return tlv_data


def bt_pbap_add_auth(tlv_dict: dict):
    logging.debug("%s %r", bt_pbap_add_auth.__name__, tlv_dict)
    TAG_1BYTE = [
        OBEXAuthTag.AHTH_REQ_OPTIONS
    ]

    TAG_16BYTE = [
        OBEXAuthTag.AUTH_REQ_NONCE,
        OBEXAuthTag.AUTH_RSP_DIGEST,
        OBEXAuthTag.AUTH_RSP_NONCE
    ]
    TAG_STRING = [
        OBEXAuthTag.AUTH_REQ_REALM,
        OBEXAuthTag.AUTH_RSP_USER_ID,
    ]

    tlv_data = bytearray()
    for tag, value in tlv_dict.items():
        if tag in TAG_1BYTE:
            data = struct.pack('B', value)
        elif tag in TAG_16BYTE:
            if isinstance(value, str):
                if len(value) == 32:
                    data = bytes.fromhex(value)
                else:
                    data = value.encode('utf-8')[:16].ljust(16, b'\x00')
            elif isinstance(value, bytearray):
                if len(value) < 16:
                    data = value.ljust(16, b'\x00')
                else:
                    data = value[:16]
            else:
                data = bytes(value)[:16].ljust(16, b'\x00')
        elif tag in TAG_STRING:
            if isinstance(value, str):
                data = value.encode('utf-8')
                data = bytearray(value.encode('utf-8'))
                data.extend(b'\x00')
            elif isinstance(value, bytes):
                data = value
            else:
                data = bytes(value)
        else:
            raise ValueError(f"Unknown tag type: 0x{tag:02X}")

        tlv_data.append(tag)
        tlv_data.append(len(data))
        tlv_data.extend(data)
    return tlv_data


def pbap_add_headers(buf: bytearray, data: dict[OBEXHdr, Union[int, bytes, bytearray, dict, str]]) -> None:
    """
    Add OBEX header data to byte array

    Args:
        buf: Target byte array, header data will be appended to the end of this array
        data: Dictionary with OBEXHdr enum as keys and corresponding data as values:
               - int: for COUNT, LEN, TIME, CONN_ID, CREATE_ID, SESSION_SEQ_NUM, PERM
               - int (uint8): for ACTION_ID, SRM, SRMP
               - bytes: for NAME, TYPE, TIME_ISO_8601, DES, TARGET, HTTP, BODY, END_BODY,
                       WHO, WAN_UUID, OBJECT_CLASS, SESSION_PARAM, DEST_NAME
               - List[tuple]: for APP_PARAM, AUTH_CHALLENGE, AUTH_RSP, format: [(tag, data), ...]
               - None: only for NAME and END_BODY (optional)

    Returns:
        None: Modifies buf directly, no return value
    """
    logging.debug("%s %r %r", pbap_add_headers.__name__, buf, data)
    if not isinstance(buf, bytearray):
        logging.error("buf must be a bytearray")
        return

    if not isinstance(data, dict):
        logging.error("data must be a dictionary")
        return

    for header_id, value in data.items():
        if header_id in [OBEXHdr.CONN_ID]:
            if not isinstance(value, int):
                logging.error(f"Header {header_id} requires int value")
                continue
            buf.append(header_id)
            buf.extend(struct.pack('>I', value))
        elif header_id in [OBEXHdr.SRM, OBEXHdr.SRMP]:
            if not isinstance(value, int):
                logging.error(f"Header {header_id} requires int value")
                continue
            buf.append(header_id)
            buf.append(value)
        elif header_id in [OBEXHdr.TARGET, OBEXHdr.WHO]:
            length = len(value)
            total = 1 + 2 + length
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            if value:
                buf.extend(value)
        elif header_id in [OBEXHdr.NAME, OBEXHdr.TYPE,
                          OBEXHdr.BODY, OBEXHdr.END_BODY]:
            if isinstance(value, str):
                if header_id == OBEXHdr.NAME:
                    value = bytearray(value.encode('utf-16-be'))
                else:
                    value = bytearray(value.encode('utf-8'))
            length = len(value) if value else 0

            if value and header_id not in [OBEXHdr.BODY, OBEXHdr.END_BODY]:
                value = value + b'\x00'
                length += 1

            total = 1 + 2 + length
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            if value:
                buf.extend(value)
        elif header_id in [OBEXHdr.APP_PARAM, OBEXHdr.AUTH_CHALLENGE,
                          OBEXHdr.AUTH_RSP]:
            if not isinstance(value, dict) or len(value) == 0:
                logging.error(f"Header {header_id} requires non-empty list of dict")
                continue

            if header_id == OBEXHdr.APP_PARAM:
                data = bt_pbap_add_header_app_param(value)
            else:
                data = bt_pbap_add_auth(value)

            total = 1 + 2 + len(data)
            buf.append(header_id)
            buf.extend(struct.pack('>H', total))
            buf.extend(data)

        else:
            logging.error(f"Unknown header_id: {header_id}")


HEADER_ENCODING_UNICODE = 0x00
HEADER_ENCODING_BYTE_SEQ = 0x40
HEADER_ENCODING_1_BYTE = 0x80
HEADER_ENCODING_4_BYTES = 0xC0


def _get_header_encoding(header_id: int) -> int:
    """Get header encoding type from header ID"""
    logging.debug("%s %r", _get_header_encoding.__name__, header_id)
    return 0xC0 & header_id


def bt_pbap_parse_header_app_param(tlv_dict: dict):
    """
    Parse application parameters from TLV format to proper data types.

    Args:
        tlv_dict: Dictionary with tag IDs as keys and raw bytes as values
                  Format: {tag_id: data_bytes}

    Returns:
        Dictionary with tag IDs as keys and parsed values (int/str/bytes)

    Example:
        >>> raw_data = {0x04: b'\x00\x64', 0x05: b'\x00\x00'}
        >>> parsed = bt_pbap_parse_header_app_param(raw_data)
        >>> print(parsed)
        {0x04: 100, 0x05: 0}
    """
    logging.debug("%s %r", bt_pbap_parse_header_app_param.__name__, tlv_dict)

    if not tlv_dict:
        return {}
    TAG_1BYTE = [
        PBAPAppParamTag.ORDER,
        PBAPAppParamTag.FORMAT,
        PBAPAppParamTag.SEARCH_PROPERTY,
        PBAPAppParamTag.NEW_MISSED_CALLS,
        PBAPAppParamTag.RESET_NEW_MISSED_CALLS,
        PBAPAppParamTag.VCARD_SELECTOR_OPERATOR
    ]
    TAG_2BYTE = [
        PBAPAppParamTag.MAX_LIST_COUNT,
        PBAPAppParamTag.LIST_START_OFFSET,
        PBAPAppParamTag.PHONEBOOK_SIZE
    ]
    TAG_4BYTE = [
        PBAPAppParamTag.SUPPORTED_FEATURES
    ]
    TAG_8BYTE = [
        PBAPAppParamTag.PROPERTY_SELECTOR,
        PBAPAppParamTag.VCARD_SELECTOR
    ]
    TAG_16BYTE = [
        PBAPAppParamTag.PRIMARY_FOLDER_VERSION,
        PBAPAppParamTag.SECONDARY_FOLDER_VERSION,
        PBAPAppParamTag.DATABASE_IDENTIFIER
    ]
    TAG_STRING = [
        PBAPAppParamTag.SEARCH_VALUE
    ]

    parsed_data = {}

    for tag, data in tlv_dict.items():
        if not isinstance(data, (bytes, bytearray)):
            logging.warning(f"Tag 0x{tag:02X} has non-bytes data, skipping")
            continue

        try:
            if tag in TAG_1BYTE:
                if len(data) >= 1:
                    parsed_data[tag] = struct.unpack('B', data[:1])[0]
                else:
                    logging.error(f"Tag 0x{tag:02X} expects 1 byte, got {len(data)}")

            elif tag in TAG_2BYTE:
                if len(data) >= 2:
                    parsed_data[tag] = struct.unpack('>H', data[:2])[0]
                else:
                    logging.error(f"Tag 0x{tag:02X} expects 2 bytes, got {len(data)}")

            elif tag in TAG_4BYTE:
                if len(data) >= 4:
                    parsed_data[tag] = struct.unpack('>I', data[:4])[0]
                else:
                    logging.error(f"Tag 0x{tag:02X} expects 4 bytes, got {len(data)}")

            elif tag in TAG_8BYTE:
                if len(data) >= 8:
                    parsed_data[tag] = struct.unpack('>Q', data[:8])[0]
                else:
                    logging.error(f"Tag 0x{tag:02X} expects 8 bytes, got {len(data)}")

            elif tag in TAG_16BYTE:
                if len(data) >= 16:
                    parsed_data[tag] = bytes(data[:16])
                else:
                    parsed_data[tag] = bytes(data).ljust(16, b'\x00')

            elif tag in TAG_STRING:
                try:
                    decoded = data.rstrip(b'\x00').decode('utf-8')
                    parsed_data[tag] = decoded
                except UnicodeDecodeError:
                    logging.warning(f"Tag 0x{tag:02X} failed UTF-8 decode, returning raw bytes")
                    parsed_data[tag] = bytes(data)
            else:
                logging.warning(f"Unknown tag type: 0x{tag:02X}, returning raw bytes")
                parsed_data[tag] = bytes(data)

        except struct.error as e:
            logging.error(f"Failed to parse tag 0x{tag:02X}: {e}")

    return parsed_data


def _parse_tlv(data_len: int, data: bytearray) -> dict:
    """Parse TLV (Tag-Length-Value) encoded data"""
    logging.debug("%s %r %r", _parse_tlv.__name__, data_len, data)
    result = {}
    index = 0
    length = data_len

    while index + 2 <= length:
        tag = data[index]
        data_len = data[index + 1]
        index += 2

        if index + data_len > length:
            break

        item_data = data[index:index + data_len]
        appl_data = bt_pbap_parse_header_app_param({tag: item_data})
        if appl_data != {}:
            result.update(appl_data)
        else:
            result[tag] = item_data
        index += data_len

    return result


def pbap_get_headers(buf_len: int, buf: bytearray) -> dict[int, Union[int, bytes, dict]]:
    logging.debug("%s %r %r", pbap_get_headers.__name__, buf_len, buf)
    """
    Parse OBEX headers from buffer

    Args:
        buf: Source byte array containing OBEX headers

    Returns:
        Dictionary with header IDs as keys and parsed data as values:
        - int: for 1-byte and 4-byte integer headers
        - bytes: for byte sequence headers
        - List[Tuple[int, bytes]]: for TLV headers (APP_PARAM, AUTH_CHALLENGE, AUTH_RSP)

    Example:
        >>> buf = bytearray(b'\xC0\x00\x00\x00\x64\x01\x00\x0D...')
        >>> headers = parse_headers(buf)
        >>> logging.error(headers)
        {0xC0: 100, 0x01: b'test.txt\x00\x00', ...}
    """
    if not isinstance(buf, bytearray):
        logging.error("buf must be a bytearray")
        return {}

    headers = {}
    index = 0

    while index < buf_len:
        if index >= buf_len:
            break

        header_id = buf[index]
        index += 1
        encoding = _get_header_encoding(header_id)

        if encoding == HEADER_ENCODING_1_BYTE:
            if index >= buf_len:
                logging.error("Buffer too short for 1-byte header value")
                break
            value = buf[index]
            index += 1
            headers[header_id] = value
        elif encoding == HEADER_ENCODING_4_BYTES:
            if index + 4 > buf_len:
                logging.error("Buffer too short for 4-byte header value")
                break
            value = struct.unpack('>I', buf[index:index + 4])[0]
            index += 4
            headers[header_id] = value
        elif encoding in [HEADER_ENCODING_UNICODE, HEADER_ENCODING_BYTE_SEQ]:
            if index + 2 > buf_len:
                logging.error("Buffer too short for length field")
                break

            header_value_len = struct.unpack('>H', buf[index:index + 2])[0]
            if header_value_len < 3:  # 1 byte ID + 2 bytes length
                logging.error(f"Invalid header length {header_value_len}")
                break
            data_len = header_value_len - 3
            index += 2

            if index + data_len > buf_len:
                logging.error("Buffer too short for header data")
                break

            data = bytes(buf[index:index + data_len])
            index += data_len
            if header_id in [OBEXHdr.APP_PARAM, OBEXHdr.AUTH_CHALLENGE, OBEXHdr.AUTH_RSP]:
                headers[header_id] = _parse_tlv(data_len, data)
            else:
                headers[header_id] = data

        else:
            logging.error(f"Unknown header encoding 0x{encoding:02X} for header 0x{header_id:02X}")
            break

    return headers


PBAP_PWD_MAX_LENGTH = 16
BT_OBEX_CHALLENGE_TAG_NONCE_LEN = 16
BT_OBEX_RESPONSE_TAG_REQ_DIGEST_LEN = 16


def bt_pbap_generate_auth_challenge_nonce() -> bytearray:
    """
    Generate PBAP authentication challenge using MD5 hash.

    Returns:
        auth_chal_req: 16-byte MD5 hash as bytearray

    Raises:
        ValueError: If password is invalid
    """
    logging.debug("%s", bt_pbap_generate_auth_challenge_nonce.__name__)

    from autopts.ptsprojects.zephyr.pbap import AUTH_PASSWORD
    pwd = bytearray(AUTH_PASSWORD.encode('utf-8'))
    if pwd is None or len(pwd) == 0:
        logging.error("Password cannot be None or empty")

    if len(pwd) > PBAP_PWD_MAX_LENGTH:
        logging.error(f"Password length exceeds maximum ({PBAP_PWD_MAX_LENGTH} bytes)")

    timestamp_ms = time.time_ns() // 1_000_000
    timestamp_bytes = struct.pack('<q', timestamp_ms)
    hash_input = bytearray()
    hash_input.extend(timestamp_bytes)
    hash_input.append(ord(':'))
    hash_input.extend(pwd)
    md5_hash = hashlib.md5(hash_input).digest()

    return bytearray(md5_hash)


def bt_pbap_generate_auth_response_digest(challenge_req_nonce: bytearray) -> bytearray:
    """
    Generate PBAP authentication response using MD5 hash.

    Args:
        pwd: Password as bytearray (max 16 bytes)
        challenge_req_nonce: Challenge nonce as bytearray (16 bytes)

    Returns:
        challenge_rsp_digest: 16-byte MD5 hash as bytearray

    Raises:
        ValueError: If parameters are invalid
    """
    logging.debug("%s %r", bt_pbap_generate_auth_response_digest.__name__, challenge_req_nonce)

    from autopts.ptsprojects.zephyr.pbap import AUTH_PASSWORD
    pwd = bytearray(AUTH_PASSWORD.encode('utf-8'))
    if pwd is None or len(pwd) == 0:
        logging.error("Password cannot be None or empty")

    if len(pwd) > PBAP_PWD_MAX_LENGTH:
        logging.error(f"Password length exceeds maximum ({PBAP_PWD_MAX_LENGTH} bytes)")

    if challenge_req_nonce is None:
        logging.error("Challenge nonce cannot be None")

    if len(challenge_req_nonce) != BT_OBEX_CHALLENGE_TAG_NONCE_LEN:
        logging.error(f"Challenge nonce must be {BT_OBEX_CHALLENGE_TAG_NONCE_LEN} bytes")

    hash_input = bytearray()
    hash_input.extend(challenge_req_nonce)
    hash_input.append(ord(':'))
    hash_input.extend(pwd)

    md5_hash = hashlib.md5(hash_input).digest()

    return bytearray(md5_hash)


def bt_pbap_verify_auth(challenge_req_nonce: bytearray,
                       challenge_rsp_digest: bytearray) -> bool:
    """
    Verify PBAP authentication response.

    Args:
        challenge_req_nonce: Challenge nonce as bytearray (16 bytes)
        challenge_rsp_digest: Response digest to verify as bytearray (16 bytes)
        pwd: Password as bytearray (max 16 bytes)

    Returns:
        True if authentication is valid, False otherwise
    """
    logging.debug("%s %r %r", bt_pbap_verify_auth.__name__, challenge_req_nonce, challenge_rsp_digest)

    from autopts.ptsprojects.zephyr.pbap import AUTH_PASSWORD
    pwd = bytearray(AUTH_PASSWORD.encode('utf-8'))
    try:
        expected_digest = bt_pbap_generate_auth_response_digest(pwd, challenge_req_nonce)
        return expected_digest == challenge_rsp_digest
    except ValueError:
        return False


def pbap_disable_auto_send():
    logging.debug("%s", pbap_disable_auto_send.__name__)
    get_stack().pbap.disable_auto_send()


def pbap_remove_vcard_property(name, property_name):
    logging.debug("%s %r %r", pbap_remove_vcard_property.__name__, name, property_name)
    return get_stack().pbap.remove_vcard_property(name, property_name)


def pbap_modify_vcard_property(name, property_name, new_value):
    logging.debug("%s %r %r %r", pbap_modify_vcard_property.__name__, name, property_name, new_value)
    return get_stack().pbap.modify_vcard_property(name, property_name, new_value)


def pbap_add_vcard_entry(name):
    logging.debug("%s %r", pbap_add_vcard_entry.__name__, name)
    return get_stack().pbap.add_vcard_entry(name)


def pbap_delete_vcard_entry(name):
    logging.debug("%s %r", pbap_delete_vcard_entry.__name__, name)
    return get_stack().pbap.delete_vcard_entry(name)


def pbap_reset_bdi():
    logging.debug("%s", pbap_reset_bdi.__name__)
    get_stack().pbap.reset_dbi()


def pbap_set_info(bd_addr=None, key=None, value=None):
    """Set PBAP information."""
    logging.debug("%s %r %r %r", pbap_set_info.__name__, bd_addr, key, value)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    get_stack().pbap.set_info(bd_addr_ba, key, value)


def pbap_get_info(bd_addr=None, key=None):
    """get PBAP information."""
    logging.debug("%s %r %r", pbap_get_info.__name__, bd_addr, key)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.get_info(bd_addr_ba, key)


PBAP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_READ_SUPPORTED_COMMANDS, defs.BTP_INDEX_NONE, ""),
    "pce_rfcomm_connect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_RFCOMM_CONNECT, CONTROLLER_INDEX),
    "pce_rfcomm_disconnect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_RFCOMM_DISCONNECT, CONTROLLER_INDEX),
    "pce_l2cap_connect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_L2CAP_CONNECT, CONTROLLER_INDEX),
    "pce_l2cap_disconnect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_L2CAP_DISCONNECT, CONTROLLER_INDEX),
    "pce_connect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_CONNECT, CONTROLLER_INDEX),
    "pce_disconnect": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_DISCONNECT, CONTROLLER_INDEX),
    "pce_pull_phonebook": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_PULL_PHONEBOOK, CONTROLLER_INDEX),
    "pce_pull_vcard_listing": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_PULL_VCARD_LISTING, CONTROLLER_INDEX),
    "pce_pull_vcard_entry": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_PULL_VCARD_ENTRY, CONTROLLER_INDEX),
    "pce_set_phone_book": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_SET_PHONE_BOOK, CONTROLLER_INDEX),
    "pce_abort": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PCE_ABORT, CONTROLLER_INDEX),
    "pse_connect_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_CONNECT_RSP, CONTROLLER_INDEX),
    "pse_disconnect_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_DISCONNECT_RSP, CONTROLLER_INDEX),
    "pse_pull_phonebook_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_PULL_PHONEBOOK_RSP, CONTROLLER_INDEX),
    "pse_pull_vcard_listing_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_PULL_VCARD_LISTING_RSP, CONTROLLER_INDEX),
    "pse_pull_vcard_entry_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_PULL_VCARD_ENTRY_RSP, CONTROLLER_INDEX),
    "pse_set_phone_book_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_SET_PHONE_BOOK_RSP, CONTROLLER_INDEX),
    "pse_abort_rsp": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_PSE_ABORT_RSP, CONTROLLER_INDEX),
    "sdp_discover": (defs.BTP_SERVICE_ID_PBAP, defs.BTP_PBAP_CMD_SDP_DISCOVER, CONTROLLER_INDEX),
}


def pbap_command_rsp_succ(op=None):
    logging.debug("%s %r", pbap_command_rsp_succ.__name__, op)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_PBAP, op)


def pbap_pce_rfcomm_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=0):
    logging.debug("%s %r %r %r", pbap_pce_rfcomm_connect.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", channel))

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_rfcomm_connect"], data=data_ba)


def pbap_pce_rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", pbap_pce_rfcomm_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_rfcomm_disconnect"], data=data_ba)


def pbap_pce_l2cap_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, psm=0):
    logging.debug("%s %r %r %r", pbap_pce_l2cap_connect.__name__, bd_addr, bd_addr_type, psm)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", psm))

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_l2cap_connect"], data=data_ba)


def pbap_pce_l2cap_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", pbap_pce_l2cap_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_l2cap_disconnect"], data=data_ba)


def pbap_pce_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, mopl=256, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pce_connect.__name__, bd_addr, bd_addr_type, mopl, buf)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", mopl))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    pbap = get_stack().pbap
    pbap.tx_data_clear(bd_addr, defs.BTP_PBAP_CMD_PCE_CONNECT)
    pbap.tx(bd_addr, defs.BTP_PBAP_CMD_PCE_CONNECT, buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_connect"], data=data_ba)


def pbap_pce_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, buf=b""):
    logging.debug("%s %r %r %r", pbap_pce_disconnect.__name__, bd_addr, bd_addr_type, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_disconnect"], data=data_ba)


def pbap_pce_pull_phonebook(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, buf=b""):
    logging.debug("%s %r %r %r", pbap_pce_pull_phonebook.__name__, bd_addr, bd_addr_type, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_pull_phonebook"], data=data_ba)


def pbap_pce_pull_vcard_listing(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, buf=b""):
    logging.debug("%s %r %r %r", pbap_pce_pull_vcard_listing.__name__, bd_addr, bd_addr_type, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_pull_vcard_listing"], data=data_ba)


def pbap_pce_pull_vcard_entry(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, buf=b""):
    logging.debug("%s %r %r %r", pbap_pce_pull_vcard_entry.__name__, bd_addr, bd_addr_type, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_pull_vcard_entry"], data=data_ba)


def pbap_pce_set_phone_book(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, flags=0, path=""):
    logging.debug("%s %r %r %r %s", pbap_pce_set_phone_book.__name__, bd_addr, bd_addr_type, flags, path)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    if path == '/' or path == '':
        # Go to root
        flags = 0x02
        folder_name = ''
    elif path == '..':
        # Go up one level
        flags = 0x03
        folder_name = ''
    elif path.startswith('../'):
        # Go up one level then navigate to path
        flags = 0x03
        folder_name = path[3:]  # Remove '../' prefix
    else:
        # Navigate to path
        flags = 0x02
        folder_name = path

    conn_id = pbap_get_info(bd_addr, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: bytearray(folder_name.encode('utf-16-be'))
    }
    header_data = bytearray()
    pbap_add_headers(header_data, hdr)

    data_ba = bytearray(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', flags))
    data_ba.extend(struct.pack('H', len(header_data)))
    data_ba.extend(header_data)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_set_phone_book"], data=data_ba)


def pbap_pce_abort(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, buf=b""):
    logging.debug("%s %r %r %r", pbap_pce_abort.__name__, bd_addr, bd_addr_type, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pce_abort"], data=data_ba)


# ============================================================================
# PSE Commands
# ============================================================================

def pbap_pse_connect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, mopl=265, rsp_code=OBEXRspCode.SUCCESS, buf=b""):
    logging.debug("%s %r %r %r %r %r", pbap_pse_connect_rsp.__name__, bd_addr, bd_addr_type, mopl, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = pts_addr_get(bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(bd_addr_ba)
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("<H", mopl))
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_connect_rsp"], data=data_ba)


def pbap_pse_disconnect_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_disconnect_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_disconnect_rsp"], data=data_ba)


def pbap_pse_pull_phonebook_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_pull_phonebook_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_pull_phonebook_rsp"], data=data_ba)


def pbap_pse_pull_vcard_listing_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_pull_vcard_listing_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_pull_vcard_listing_rsp"], data=data_ba)


def pbap_pse_pull_vcard_entry_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_pull_vcard_entry_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_pull_vcard_entry_rsp"], data=data_ba)


def pbap_pse_set_phone_book_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_set_phone_book_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_set_phone_book_rsp"], data=data_ba)


def pbap_pse_abort_rsp(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, rsp_code=0, buf=b""):
    logging.debug("%s %r %r %r %r", pbap_pse_abort_rsp.__name__, bd_addr, bd_addr_type, rsp_code, buf)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", rsp_code))
    data_ba.extend(struct.pack("<H", len(buf)))
    data_ba.extend(buf)

    iutctl.btp_socket.send_wait_rsp(*PBAP["pse_abort_rsp"], data=data_ba)


def pbap_sdp_discover(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", pbap_sdp_discover.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*PBAP["sdp_discover"], data=data_ba)


# ============================================================================
# Internal Event Processing Functions
# ============================================================================

def _pbap_pce_rfcomm_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_rfcomm_connected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PCE RFCOMM connected to addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.add_pbap_connection(bd_addr, PBAPTransportType.RFCOMM_CONN)


def _pbap_pce_rfcomm_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_rfcomm_disconnected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PCE RFCOMM disconnected from addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.remove_pbap_connection(bd_addr, PBAPTransportType.RFCOMM_CONN)


def _pbap_pce_l2cap_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_l2cap_connected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PCE L2CAP connected to addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.add_pbap_connection(bd_addr, PBAPTransportType.L2CAP_CONN)


def _pbap_pce_l2cap_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_l2cap_disconnected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PCE L2CAP disconnected from addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.remove_pbap_connection(bd_addr, PBAPTransportType.L2CAP_CONN)


def _pbap_pce_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_connected_ev.__name__, pbap, data, data_len)

    def handle_auth_challenge(conn_info, tx_data):
        auth_challenge = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.AUTH_CHALLENGE)
        if not auth_challenge:
            logging.error("Auth challenge header not found in response")
            return

        auth_challenge_req_nonce = auth_challenge.get(OBEXAuthTag.AUTH_REQ_NONCE)
        if not auth_challenge_req_nonce:
            logging.error("Auth challenge nonce not found")
            return

        logging.debug("Auth challenge nonce: %r", auth_challenge_req_nonce)

        auth_challenge_rsp_digest = {
            OBEXAuthTag.AUTH_RSP_DIGEST: bt_pbap_generate_auth_response_digest(
                auth_challenge_req_nonce
            )
        }
        rsp_buf = {OBEXHdr.AUTH_RSP: auth_challenge_rsp_digest}

        pbap_add_headers(tx_data, rsp_buf)
        pbap_pce_connect(buf=tx_data)

    def verify_auth_response(conn_info, challenge_req):
        nonce = challenge_req.get(OBEXAuthTag.AUTH_REQ_NONCE)
        if not nonce:
            logging.error("Challenge request nonce not found")
            return False

        challenge_rsp = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.AUTH_RSP)
        if challenge_rsp is None:
            logging.error("Challenge response header not found")
            return False

        challenge_rsp_digest = challenge_rsp.get(OBEXAuthTag.AUTH_RSP_DIGEST)
        if not challenge_rsp_digest:
            logging.error("Challenge response digest not found")
            return False

        if not bt_pbap_verify_auth(nonce, challenge_rsp_digest):
            logging.error("Authentication response digest verification failed")
            return False

        logging.debug("Authentication response verified successfully")
        return True

    def handle_connection_success(conn_info, tx_data, rsp_code, buf):
        conn_info[PBAPInfo.TX_DATA] = pbap_get_headers(len(tx_data), tx_data)

        challenge_req = conn_info[PBAPInfo.TX_DATA].get(OBEXHdr.AUTH_CHALLENGE)
        if challenge_req:
            if not verify_auth_response(conn_info, challenge_req):
                return
        else:
            logging.info("No authentication challenge verification needed")

        pbap.add_pbap_obex_connection(bd_addr, PBAPRole.PCE)

        conn_id = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.CONN_ID)
        if conn_id is not None:
            pbap.set_info(bd_addr, PBAPInfo.CONN_ID, conn_id)

        pbap.tx_data_clear(bd_addr, defs.BTP_PBAP_CMD_PCE_CONNECT)
        pbap.clear_tx_state(bd_addr)
        pbap.clear_rx_state(bd_addr)
        pbap.rx(bd_addr, defs.BTP_PBAP_CMD_PCE_CONNECT, (rsp_code, buf))

    hdr_fmt = "<B6sBBHH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, rsp_code, version, mopl, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    logging.debug("PBAP PCE connected to addr %r, rsp_code %r, version %r, mopl %r",
                  bd_addr, rsp_code, version, mopl)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    conn = pbap.get_pbap_connection(bd_addr)
    if conn is None:
        logging.error("Transport connection is not established")
        return

    conn_info = conn.conn_info
    conn_info[PBAPInfo.RX_DATA] = pbap_get_headers(len(buf), bytearray(buf))
    logging.debug("Received headers: %r", conn_info[PBAPInfo.RX_DATA])

    tx_data = pbap.tx_data_get(bd_addr, defs.BTP_PBAP_CMD_PCE_CONNECT, timeout=0)

    if rsp_code == OBEXRspCode.UNAUTH:
        handle_auth_challenge(conn_info, tx_data)
    elif rsp_code == OBEXRspCode.SUCCESS:
        handle_connection_success(conn_info, tx_data, rsp_code, buf)
    else:
        logging.error("PBAP PCE connection failed with rsp_code 0x%02X", rsp_code)


def _pbap_pce_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_disconnected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, rsp_code, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    logging.debug("PBAP PCE disconnected from addr %r, rsp_code %r", bd_addr, rsp_code)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    if rsp_code == OBEXRspCode.SUCCESS:
        pbap.clear_tx_state(bd_addr)
        pbap.clear_rx_state(bd_addr)
        pbap.remote_pbap_obex_connection(bd_addr)
    pbap.rx(bd_addr, defs.BTP_PBAP_CMD_PCE_DISCONNECT, (rsp_code, buf))


def _pbap_pce_pull_operation_ev(pbap, data, data_len, cmd_type, continue_func):

    def _handle_srm_negotiation(conn_info, rx_data):
        """Handle SRM (Single Response Mode) negotiation logic."""
        if conn_info.get(PBAPInfo.LOCAL_SRM) and conn_info.get(PBAPInfo.SRM_STATE) == PBAPSrmState.SRM_DISABLED:
            conn_info[PBAPInfo.LOCAL_SRM] = False
            if rx_data.get(OBEXHdr.SRM, 0) == 1:
                conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED
                if rx_data.get(OBEXHdr.SRMP, 0) == 1:
                    conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED_BUT_WAITING
                if conn_info.get(PBAPInfo.LOCAL_SRMP):
                    conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED_BUT_WAITING

    def _handle_srm_waiting_state(conn_info, rx_data):
        """Handle SRM waiting state transitions."""
        if conn_info.get(PBAPInfo.SRM_STATE) == PBAPSrmState.SRM_ENABLED_BUT_WAITING:
            if rx_data.get(OBEXHdr.SRMP, 0) != 1 and not conn_info.get(PBAPInfo.LOCAL_SRMP):
                conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED

            if rx_data.get(OBEXHdr.SRMP, 0) == 1:
                del rx_data[OBEXHdr.SRMP]

            if conn_info.get(PBAPInfo.LOCAL_SRMP):
                conn_info[PBAPInfo.LOCAL_SRMP] -= 1

    def _send_continue_request(conn_info, bd_addr, continue_func):
        """Send continue request if SRM is not enabled."""
        pbap = get_stack().pbap
        if conn_info.get(PBAPInfo.SRM_STATE) != PBAPSrmState.SRM_ENABLED:
            request_buf = bytearray()
            local_srmp = conn_info.get(PBAPInfo.LOCAL_SRMP, 0)
            if local_srmp > 0:
                hdr = {OBEXHdr.SRMP: 1}
                pbap_add_headers(request_buf, hdr)
            if pbap.auto_send and pbap.is_pbap_obex_connected(bd_addr):
                continue_func(bd_addr=bd_addr, buf=request_buf)

    hdr_fmt = "<B6sBH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, rsp_code, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    conn = pbap.get_pbap_connection(bd_addr)
    if conn is None:
        logging.error('Connection not found for addr %s', bd_addr)
        return

    conn_info = conn.conn_info
    rx_data = pbap_get_headers(len(buf), bytearray(buf))
    conn_info[PBAPInfo.RX_DATA] = rx_data

    if rsp_code != OBEXRspCode.CONTINUE:
        pbap.rx(bd_addr, cmd_type, (rsp_code, rx_data))
        pbap.clear_rx_state(bd_addr)
        pbap.clear_tx_state(bd_addr)
        return

    _handle_srm_negotiation(conn_info, rx_data)

    _handle_srm_waiting_state(conn_info, rx_data)

    _send_continue_request(conn_info, bd_addr, continue_func)


def _pbap_pce_pull_phonebook_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_pull_phonebook_ev.__name__, pbap, data, data_len)
    _pbap_pce_pull_operation_ev(pbap, data, data_len,
                                 defs.BTP_PBAP_CMD_PCE_PULL_PHONEBOOK,
                                 pbap_pce_pull_phonebook)


def _pbap_pce_pull_vcard_listing_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_pull_vcard_listing_ev.__name__, pbap, data, data_len)
    _pbap_pce_pull_operation_ev(pbap, data, data_len,
                                 defs.BTP_PBAP_CMD_PCE_PULL_VCARD_LISTING,
                                 pbap_pce_pull_vcard_listing)


def _pbap_pce_pull_vcard_entry_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_pull_vcard_entry_ev.__name__, pbap, data, data_len)
    _pbap_pce_pull_operation_ev(pbap, data, data_len,
                                 defs.BTP_PBAP_CMD_PCE_PULL_VCARD_ENTRY,
                                 pbap_pce_pull_vcard_entry)


def _pbap_pce_set_phone_book_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_set_phone_book_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, rsp_code, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]

    logging.debug("PBAP PCE set path from addr %r, rsp_code %r", bd_addr, rsp_code)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().pbap.rx(bd_addr, defs.BTP_PBAP_CMD_PCE_SET_PHONE_BOOK, (rsp_code, buf))


def _pbap_pce_abort_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pce_abort_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, rsp_code, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    logging.debug("PBAP PCE abort from addr %r, rsp_code %r", bd_addr, rsp_code)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().pbap.rx(bd_addr, defs.BTP_PBAP_CMD_PCE_ABORT, (rsp_code, buf))


def _pbap_pse_rfcomm_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_rfcomm_connected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PSE RFCOMM connected to addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.add_pbap_connection(bd_addr, PBAPTransportType.RFCOMM_CONN)


def _pbap_pse_rfcomm_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_rfcomm_disconnected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PSE RFCOMM disconnected from addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.remove_pbap_connection(bd_addr, PBAPTransportType.RFCOMM_CONN)


def _pbap_pse_l2cap_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_l2cap_connected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PSE L2CAP connected to addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.add_pbap_connection(bd_addr, PBAPTransportType.L2CAP_CONN)


def _pbap_pse_l2cap_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_l2cap_disconnected_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP PSE L2CAP disconnected from addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.remove_pbap_connection(bd_addr, PBAPTransportType.L2CAP_CONN)


PSE_ENABLE_AUTH = False


def _pbap_pse_connect_ev(pbap, data, data_len):
    def handle_client_auth_challenge(conn_info, rsp_hdr):
        auth_challenge_req = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.AUTH_CHALLENGE)
        if not auth_challenge_req:
            return
        auth_challenge_req_nonce = auth_challenge_req.get(OBEXAuthTag.AUTH_REQ_NONCE)
        if not auth_challenge_req_nonce:
            logging.error("Auth challenge nonce not found")
            return
        logging.info(f"Received auth challenge, nonce length: {len(auth_challenge_req_nonce)}")
        try:
            auth_challenge_rsp_digest = bt_pbap_generate_auth_response_digest(
                auth_challenge_req_nonce
            )
            rsp_hdr[OBEXHdr.AUTH_RSP] = {
                OBEXAuthTag.AUTH_RSP_DIGEST: auth_challenge_rsp_digest
            }
            logging.debug("Auth response digest generated successfully")
        except Exception as e:
            logging.error(f"Failed to generate auth response: {e}")

    def verify_client_auth_response(conn_info):
        try:
            auth_challenge_req_nonce = (
                conn_info[PBAPInfo.TX_DATA]
                .get(OBEXHdr.AUTH_CHALLENGE, {})
                .get(OBEXAuthTag.AUTH_REQ_NONCE)
            )

            if not auth_challenge_req_nonce:
                logging.error("Auth challenge nonce not found in TX_DATA")
                return OBEXRspCode.NOT_ACCEPT

            auth_challenge_rsp = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.AUTH_RSP)
            if not auth_challenge_rsp:
                logging.error("Auth response not found in client's request")
                return OBEXRspCode.NOT_ACCEPT

            auth_challenge_rsp_digest = auth_challenge_rsp.get(OBEXAuthTag.AUTH_RSP_DIGEST)
            if not auth_challenge_rsp_digest:
                logging.error("Auth response digest not found")
                return OBEXRspCode.NOT_ACCEPT

            logging.info(f"Verifying auth response digest, length: {len(auth_challenge_rsp_digest)}")

            if not bt_pbap_verify_auth(auth_challenge_req_nonce, auth_challenge_rsp_digest):
                logging.error("Auth response digest verification failed")
                return OBEXRspCode.NOT_ACCEPT

            logging.info("Auth response digest verification passed")
            return OBEXRspCode.SUCCESS

        except Exception as e:
            logging.error(f"Exception during auth verification: {e}")
            return OBEXRspCode.NOT_ACCEPT

    def send_response_and_cleanup(pbap, bd_addr, conn_info, rsp_code, rsp_buf):
        """Send response and cleanup connection state if successful."""
        pbap_set_info(bd_addr, PBAPInfo.TX_DATA, rsp_hdr)

        if rsp_code == OBEXRspCode.SUCCESS:
            pbap.add_pbap_obex_connection(bd_addr, PBAPRole.PSE)
            pbap.tx(bd_addr, defs.BTP_PBAP_CMD_PSE_CONNECT_RSP, (rsp_code, rsp_buf))
            pbap.clear_tx_state(bd_addr)
            pbap.clear_rx_state(bd_addr)

        pbap_pse_connect_rsp(mopl=conn_info[PBAPInfo.LOCAL_MOPL], rsp_code=rsp_code, buf=rsp_buf)

    logging.debug("%s %r %r %r", _pbap_pse_connect_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBHH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, version, mopl, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]

    logging.debug("PBAP PSE connect from addr %r, version %r, mopl %r", bd_addr, version, mopl)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    conn = pbap.get_pbap_connection(bd_addr)
    if conn is None:
        logging.error("Transport connection is not established")
        return

    conn_info = conn.conn_info
    pbap.set_info(bd_addr, PBAPInfo.REMOTE_MOPL, mopl)
    conn_info[PBAPInfo.RX_DATA] = pbap_get_headers(len(buf), bytearray(buf))

    remote_support_feature = 0x3  # Default features
    appl_param = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM)
    if appl_param:
        remote_support_feature = appl_param.get(
            PBAPAppParamTag.SUPPORTED_FEATURES,
            remote_support_feature
        )
    pbap.set_info(bd_addr, PBAPInfo.REMOTE_SUPPORT_FEATURE, remote_support_feature)

    who = bytearray([0x79, 0x61, 0x35, 0xf0, 0xf0, 0xc5,
                     0x11, 0xd8, 0x09, 0x66, 0x08, 0x00,
                     0x20, 0x0c, 0x9a, 0x66])
    rsp_hdr = {
        OBEXHdr.WHO: who,
        OBEXHdr.CONN_ID: 0x01
    }

    is_first_connection = (conn_info[PBAPInfo.TX_DATA] == {})
    if is_first_connection:
        if PSE_ENABLE_AUTH:
            rsp_hdr[OBEXHdr.AUTH_CHALLENGE] = {
                OBEXAuthTag.AUTH_REQ_NONCE: bt_pbap_generate_auth_challenge_nonce()
            }
            rsp_code = OBEXRspCode.UNAUTH
            logging.info("Sending auth challenge to client")
        else:
            handle_client_auth_challenge(conn_info, rsp_hdr)
            rsp_code = OBEXRspCode.SUCCESS
    else:
        handle_client_auth_challenge(conn_info, rsp_hdr)
        if PSE_ENABLE_AUTH:
            rsp_code = verify_client_auth_response(conn_info)
        else:
            rsp_code = OBEXRspCode.SUCCESS
    rsp_buf = bytearray()
    pbap_add_headers(rsp_buf, rsp_hdr)
    send_response_and_cleanup(pbap, bd_addr, conn_info, rsp_code, rsp_buf)


def _pbap_pse_disconnect_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_disconnect_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    rsp_code = OBEXRspCode.SUCCESS
    pbap.tx(bd_addr, defs.BTP_PBAP_CMD_PSE_DISCONNECT_RSP, (rsp_code, bytearray()))
    pbap_pse_disconnect_rsp(rsp_code=rsp_code)


OBEX_HEADER_OVERHEAD = 7
DEFAULT_MAX_LIST_COUNT = 1024
DEFAULT_LIST_START_OFFSET = 0
DEFAULT_RESET_NEW_MISSED_CALLS = 0
DEFAULT_VCARD_SELECTOR_OPERATOR = 1
DEFAULT_FORMAT_TYPE = 0x01


def _both_support_feature(conn_info, feature):
    return (conn_info[PBAPInfo.LOCAL_SUPPORT_FEATURE] & feature and
            conn_info[PBAPInfo.REMOTE_SUPPORT_FEATURE] & feature)


def _parse_request_header(data, data_len):
    hdr_fmt = "<B6sH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    return bd_addr, buf


def _validate_connection(pbap, bd_addr):
    conn = pbap.get_pbap_connection(bd_addr)
    if conn is None:
        logging.error("transport connection is not established")
        return None, None
    conn_info = conn.conn_info
    mopl = min(conn_info[PBAPInfo.REMOTE_MOPL], conn_info[PBAPInfo.LOCAL_MOPL])
    return conn, conn_info, mopl


def _extract_name_from_headers(rx_data, allow_empty=False):
    name_data = rx_data.get(OBEXHdr.NAME)
    if not name_data:
        return '' if allow_empty else None
    try:
        return name_data.decode('utf-16-be').rstrip('\x00')
    except (UnicodeDecodeError, AttributeError):
        return None


def _validate_phonebook_name(pbap, name):
    if not name:
        return False
    if '.vcf' not in name:
        return False
    path = name.rsplit('.vcf')[0]
    result = pbap.is_valid_combined_path(path)
    return result


def _get_default_property_selector(format_type):
    if format_type == 1:
        return (PBAPPropertySelector.FN | PBAPPropertySelector.N |
                PBAPPropertySelector.VERSION | PBAPPropertySelector.TEL)
    else:
        return (PBAPPropertySelector.N | PBAPPropertySelector.VERSION |
                PBAPPropertySelector.TEL)


def _filter_property_selector(conn_info, propertyselector, format_type):
    default_selector = _get_default_property_selector(format_type)

    if not (_both_support_feature(conn_info, PBAPSupportedFeature.UID_VCARD_PROPERTY) and
            _both_support_feature(conn_info, PBAPSupportedFeature.CONTACT_REFERENCING)):
        propertyselector = (
            propertyselector & (~PBAPPropertySelector.X_BT_UID)
                if propertyselector is not None else default_selector
        )

    if not _both_support_feature(conn_info, PBAPSupportedFeature.UCI_VCARD_PROPERTY):
        propertyselector = (
            propertyselector & (~PBAPPropertySelector.X_BT_UCI)
                if propertyselector is not None else default_selector
        )

    return propertyselector


def _build_app_param_response(pbap, conn_info, name, max_list_count, data,
                               reset_new_missed_calls, include_database_id_only=False):
    rsp_hdr = {OBEXHdr.APP_PARAM: {}}

    if include_database_id_only:
        if conn_info[PBAPInfo.LOCAL_SUPPORT_FEATURE] & PBAPSupportedFeature.DATABASE_IDENTIFIER:
            rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.DATABASE_IDENTIFIER] = pbap.phonebook.database_identifier
        return rsp_hdr

    if max_list_count == 0:
        rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.PHONEBOOK_SIZE] = data['phonebook_size']

    if _both_support_feature(conn_info, PBAPSupportedFeature.ENHANCED_MISSED_CALLS):
        if 'mch' in name or 'cch' in name:
            rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.NEW_MISSED_CALLS] = 0 if reset_new_missed_calls == 0 else 1
    elif 'mch' in name:
        rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.NEW_MISSED_CALLS] = 0 if reset_new_missed_calls == 0 else 1

    if _both_support_feature(conn_info, PBAPSupportedFeature.FOLDER_VERSION_COUNTERS):
        rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.PRIMARY_FOLDER_VERSION] = pbap.phonebook.primary_folder_version
        rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.SECONDARY_FOLDER_VERSION] = pbap.phonebook.secondary_folder_version

    if _both_support_feature(conn_info, PBAPSupportedFeature.DATABASE_IDENTIFIER):
        rsp_hdr[OBEXHdr.APP_PARAM][PBAPAppParamTag.DATABASE_IDENTIFIER] = pbap.phonebook.database_identifier

    return rsp_hdr


def _handle_srm_negotiation(conn, conn_info, rx_data, rsp_hdr):
    is_l2cap = conn.transport_type == PBAPTransportType.L2CAP_CONN
    if is_l2cap and rx_data.get(OBEXHdr.SRM, 0) == 1:
        rsp_hdr[OBEXHdr.SRM] = 1
        conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED
        if rx_data.get(OBEXHdr.SRMP, 0) == 1:
            conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED_BUT_WAITING


def _update_srm_waiting_state(conn_info):
    if conn_info.get(PBAPInfo.SRM_STATE) == PBAPSrmState.SRM_ENABLED_BUT_WAITING:
        if conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.SRMP, 0) == 1:
            del conn_info[PBAPInfo.RX_DATA][OBEXHdr.SRMP]
        else:
            conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_ENABLED


def _send_chunked_data(pbap, bd_addr, conn_info, mopl, initial_rsp_hdr, rsp_func):
    while True:
        data = conn_info[PBAPInfo.TX_DATA]['data']
        rsp_buf = bytearray()
        if conn_info[PBAPInfo.TX_CNT] == 0:
            remaining_len = len(data)
            offset = 0
            rsp_hdr = initial_rsp_hdr
        else:
            remaining_len = conn_info[PBAPInfo.TX_DATA]['remain_len']
            offset = conn_info[PBAPInfo.TX_DATA]['offset']
            rsp_hdr = {}

        pbap_add_headers(rsp_buf, rsp_hdr)
        buf_available_len = mopl - len(rsp_buf) - OBEX_HEADER_OVERHEAD

        if remaining_len > buf_available_len:
            hdr = {OBEXHdr.BODY: data[offset:offset + buf_available_len]}
            remaining_len -= buf_available_len
            offset += buf_available_len
            rsp_code = OBEXRspCode.CONTINUE
            tx_data_info = {
                'data': data,
                'remain_len': remaining_len,
                'offset': offset
            }
            pbap.set_info(bd_addr, key=PBAPInfo.TX_DATA, value=tx_data_info)
            pbap.set_info(bd_addr, key=PBAPInfo.TX_CNT, value=conn_info[PBAPInfo.TX_CNT] + 1)
        else:
            hdr = {OBEXHdr.END_BODY: data[offset:]}
            rsp_code = OBEXRspCode.SUCCESS

        pbap_add_headers(rsp_buf, hdr)
        rsp_func(rsp_code=rsp_code, buf=rsp_buf)

        if rsp_code != OBEXRspCode.CONTINUE:
            pbap.clear_tx_state(bd_addr)
            pbap.clear_rx_state(bd_addr)
            break

        if conn_info.get(PBAPInfo.SRM_STATE) != PBAPSrmState.SRM_ENABLED or (not pbap.auto_send) or \
           (not pbap.is_pbap_obex_connected(bd_addr)):
            break


def _pbap_pse_pull_phonebook_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_pull_phonebook_ev.__name__, pbap, data, data_len)
    bd_addr, buf = _parse_request_header(data, data_len)

    conn, conn_info, mopl = _validate_connection(pbap, bd_addr)
    if conn is None:
        return

    rsp_hdr = {}
    if conn_info[PBAPInfo.TX_CNT] == 0:
        conn_info[PBAPInfo.RX_DATA] = pbap_get_headers(len(buf), bytearray(buf))
        logging.info(f"PBAPInfo.RX_DATA = {conn_info[PBAPInfo.RX_DATA]}")

        name = _extract_name_from_headers(conn_info[PBAPInfo.RX_DATA])
        if not _validate_phonebook_name(pbap, name):
            pbap_pse_pull_phonebook_rsp(rsp_code=OBEXRspCode.BAD_REQ)
            return

        appl_param = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.APP_PARAM, {})
        max_list_count = appl_param.get(PBAPAppParamTag.MAX_LIST_COUNT, DEFAULT_MAX_LIST_COUNT)
        list_start_offset = appl_param.get(PBAPAppParamTag.LIST_START_OFFSET, DEFAULT_LIST_START_OFFSET)
        reset_new_missed_calls = appl_param.get(PBAPAppParamTag.RESET_NEW_MISSED_CALLS, DEFAULT_RESET_NEW_MISSED_CALLS)
        vcard_selector = appl_param.get(PBAPAppParamTag.VCARD_SELECTOR)
        vcard_selector_operator = appl_param.get(PBAPAppParamTag.VCARD_SELECTOR_OPERATOR, DEFAULT_VCARD_SELECTOR_OPERATOR)
        propertyselector = appl_param.get(PBAPAppParamTag.PROPERTY_SELECTOR)
        format_type = appl_param.get(PBAPAppParamTag.FORMAT, DEFAULT_FORMAT_TYPE)

        propertyselector = _filter_property_selector(conn_info, propertyselector, format_type)

        logging.info(f'propertyselector = {propertyselector}, format_type = {format_type}')
        data = pbap.pull_phonebook(
            max_list_count=max_list_count,
            list_start_offset=list_start_offset,
            property_selector=propertyselector,
            vcard_selector=vcard_selector,
            vcard_selector_operator=vcard_selector_operator,
            format_type=format_type
        )

        rsp_hdr = _build_app_param_response(pbap, conn_info, name, max_list_count, data, reset_new_missed_calls)
        _handle_srm_negotiation(conn, conn_info, conn_info[PBAPInfo.RX_DATA], rsp_hdr)

        pbap.set_info(bd_addr, key=PBAPInfo.TX_DATA, value={'data': data['content']})

    _update_srm_waiting_state(conn_info)
    _send_chunked_data(pbap, bd_addr, conn_info, mopl, rsp_hdr, pbap_pse_pull_phonebook_rsp)


def _pbap_pse_pull_vcard_listing_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_pull_vcard_listing_ev.__name__, pbap, data, data_len)
    bd_addr, buf = _parse_request_header(data, data_len)

    conn, conn_info, mopl = _validate_connection(pbap, bd_addr)
    if conn is None:
        return

    rsp_hdr = {}
    if conn_info[PBAPInfo.TX_CNT] == 0:
        rx_data = pbap_get_headers(len(buf), bytearray(buf))
        conn_info[PBAPInfo.RX_DATA] = rx_data
        name = _extract_name_from_headers(rx_data, allow_empty=True)

        appl_param = rx_data.get(OBEXHdr.APP_PARAM, {})
        max_list_count = appl_param.get(PBAPAppParamTag.MAX_LIST_COUNT, DEFAULT_MAX_LIST_COUNT)
        list_start_offset = appl_param.get(PBAPAppParamTag.LIST_START_OFFSET, DEFAULT_LIST_START_OFFSET)
        reset_new_missed_calls = appl_param.get(PBAPAppParamTag.RESET_NEW_MISSED_CALLS, DEFAULT_RESET_NEW_MISSED_CALLS)
        search_value = appl_param.get(PBAPAppParamTag.SEARCH_VALUE)
        search_attribute = appl_param.get(PBAPAppParamTag.SEARCH_PROPERTY)
        vcard_selector = appl_param.get(PBAPAppParamTag.VCARD_SELECTOR)
        vcard_selector_operator = appl_param.get(PBAPAppParamTag.VCARD_SELECTOR_OPERATOR, DEFAULT_VCARD_SELECTOR_OPERATOR)

        logging.info(f'vcard_selector = {vcard_selector}')
        data = pbap.pull_vcard_listing(
            max_list_count=max_list_count,
            list_start_offset=list_start_offset,
            search_value=search_value,
            search_attribute=search_attribute,
            vcard_selector=vcard_selector,
            vcard_selector_operator=vcard_selector_operator
        )

        logging.info(f"data = {data['content']}")
        rsp_hdr = _build_app_param_response(pbap, conn_info, name, max_list_count, data, reset_new_missed_calls)
        _handle_srm_negotiation(conn, conn_info, rx_data, rsp_hdr)
        pbap.set_info(bd_addr, key=PBAPInfo.TX_DATA, value={'data': data['content']})

    _update_srm_waiting_state(conn_info)
    _send_chunked_data(pbap, bd_addr, conn_info, mopl, rsp_hdr, pbap_pse_pull_vcard_listing_rsp)


def _pbap_pse_pull_vcard_entry_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_pull_vcard_entry_ev.__name__, pbap, data, data_len)
    bd_addr, buf = _parse_request_header(data, data_len)

    conn, conn_info, mopl = _validate_connection(pbap, bd_addr)
    if conn is None:
        return

    rsp_hdr = {}
    if conn_info[PBAPInfo.TX_CNT] == 0:
        rx_data = pbap_get_headers(len(buf), bytearray(buf))
        conn_info[PBAPInfo.RX_DATA] = rx_data
        name = _extract_name_from_headers(rx_data)
        if name is None:
            return

        appl_param = rx_data.get(OBEXHdr.APP_PARAM, {})
        propertyselector = appl_param.get(PBAPAppParamTag.PROPERTY_SELECTOR)
        format_type = appl_param.get(PBAPAppParamTag.FORMAT, DEFAULT_FORMAT_TYPE)
        logging.info(f'propertyselector = {propertyselector}')
        propertyselector = _filter_property_selector(conn_info, propertyselector, format_type)
        logging.info(f'propertyselector = {propertyselector}')
        data = pbap.pull_vcard_entry(handle=name, propertyselector=propertyselector, format_type=format_type)

        if data['content'] is None or len(data['content']) == 0:
            pbap_pse_pull_vcard_entry_rsp(rsp_code=OBEXRspCode.NOT_FOUND)
            return

        logging.info(f"data = {data['content']}")
        rsp_hdr = _build_app_param_response(pbap, conn_info, name, 0, data, 0, include_database_id_only=True)
        _handle_srm_negotiation(conn, conn_info, rx_data, rsp_hdr)
        pbap.set_info(bd_addr, key=PBAPInfo.TX_DATA, value={'data': data['content']})

    _update_srm_waiting_state(conn_info)
    _send_chunked_data(pbap, bd_addr, conn_info, mopl, rsp_hdr, pbap_pse_pull_vcard_entry_rsp)


def _pbap_pse_set_phone_book_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_set_phone_book_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, flags, buf_len = struct.unpack_from(hdr_fmt, data)
    buf = data[hdr_len:hdr_len + buf_len]
    logging.debug("PBAP PSE set path from addr %r, flags %r", bd_addr, flags)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    conn = pbap.get_pbap_connection(bd_addr)
    if conn is None:
        logging.error("transport connection is not be estabilshed")
        return

    conn_info = conn.conn_info
    conn_info[PBAPInfo.RX_DATA] = pbap_get_headers(len(buf), bytearray(buf))
    name = conn_info[PBAPInfo.RX_DATA].get(OBEXHdr.NAME)
    result = pbap.set_path(flags, name)
    rsp_code = OBEXRspCode.SUCCESS
    if result is None:
        rsp_code = OBEXRspCode.NOT_FOUND
    pbap.tx(bd_addr, defs.BTP_PBAP_CMD_PSE_SET_PHONE_BOOK_RSP, (rsp_code, bytearray()))
    pbap_pse_set_phone_book_rsp(rsp_code=rsp_code)


def _pbap_pse_abort_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_pse_abort_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sH"
    hdr_len = struct.calcsize(hdr_fmt)
    _, bd_addr, buf_len = struct.unpack_from(hdr_fmt, data)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    rsp_code = OBEXRspCode.SUCCESS
    pbap.tx(bd_addr, defs.BTP_PBAP_CMD_PSE_ABORT_RSP, (rsp_code, bytearray()))
    pbap_pse_abort_rsp(rsp_code=rsp_code)


def _pbap_sdp_discover_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", _pbap_sdp_discover_ev.__name__, pbap, data, data_len)
    hdr_fmt = "<B6sBHIB"
    _, bd_addr, rfcomm_channel, l2cap_psm, supported_features, supported_repositories = struct.unpack_from(hdr_fmt, data)
    logging.debug("PBAP SDP discover from addr %r, channel %r, psm %r, features 0x%08x, repos %r",
                  bd_addr, rfcomm_channel, l2cap_psm, supported_features, supported_repositories)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    pbap.add_sdp_connection(bd_addr, rfcomm_channel, l2cap_psm,
                                         supported_features, supported_repositories)


def pbap_wait_for_sdp_finished(bd_addr=None, timeout=60):
    logging.debug("%s %r %r", pbap_wait_for_sdp_finished.__name__, bd_addr, timeout)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.wait_for_sdp_finished(bd_addr_ba, timeout)


def pbap_get_sdp_connection(bd_addr=None):
    logging.debug("%s %r", pbap_get_sdp_connection.__name__, bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.get_sdp_connection(bd_addr_ba)


def pbap_wait_for_transport_connected(bd_addr=None, timeout=60):
    logging.debug("%s %r %r", pbap_wait_for_transport_connected.__name__, bd_addr, timeout)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.wait_for_pbap_connection(bd_addr_ba, timeout)


def pbap_get_pbap_connection(bd_addr=None):
    logging.debug("%s %r", pbap_get_pbap_connection.__name__, bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.get_pbap_connection(bd_addr_ba)


def pbap_connection_is_l2cap(bd_addr=None):
    logging.debug("%s %r", pbap_connection_is_l2cap.__name__, bd_addr)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().pbap.get_pbap_connection(bd_addr_ba).transport_type == PBAPTransportType.L2CAP_CONN


FUNC_HADNLE = {
        pbap_pce_connect.__name__: defs.BTP_PBAP_CMD_PCE_CONNECT,
        pbap_pce_disconnect.__name__: defs.BTP_PBAP_CMD_PCE_DISCONNECT,
        pbap_pce_set_phone_book.__name__: defs.BTP_PBAP_CMD_PCE_SET_PHONE_BOOK,
        pbap_pce_pull_phonebook.__name__: defs.BTP_PBAP_CMD_PCE_PULL_PHONEBOOK,
        pbap_pce_pull_vcard_listing.__name__: defs.BTP_PBAP_CMD_PCE_PULL_VCARD_LISTING,
        pbap_pce_pull_vcard_entry.__name__: defs.BTP_PBAP_CMD_PCE_PULL_VCARD_ENTRY,
        pbap_pce_abort.__name__: defs.BTP_PBAP_CMD_PCE_ABORT,
        pbap_pse_connect_rsp.__name__: defs.BTP_PBAP_CMD_PSE_CONNECT_RSP,
        pbap_pse_disconnect_rsp.__name__: defs.BTP_PBAP_CMD_PSE_DISCONNECT_RSP,
        pbap_pse_set_phone_book_rsp.__name__: defs.BTP_PBAP_CMD_PSE_SET_PHONE_BOOK_RSP,
        pbap_pse_pull_phonebook_rsp.__name__: defs.BTP_PBAP_CMD_PSE_PULL_PHONEBOOK_RSP,
        pbap_pse_pull_vcard_listing_rsp.__name__: defs.BTP_PBAP_CMD_PSE_PULL_VCARD_LISTING_RSP,
        pbap_pse_pull_vcard_entry_rsp.__name__: defs.BTP_PBAP_CMD_PSE_PULL_VCARD_ENTRY_RSP,
}


def pbap_wait_for_func_finished(bd_addr=None, func_name=None, except_state=OBEXRspCode.SUCCESS, timeout=120, clear=True):
    logging.debug("%s", pbap_wait_for_func_finished.__name__)
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()

    if 'pce' in func_name:
        data = get_stack().pbap.rx_data_get(bd_addr_ba, FUNC_HADNLE.get(func_name), timeout, clear)
    else:
        data = get_stack().pbap.tx_data_get(bd_addr_ba, FUNC_HADNLE.get(func_name), timeout, clear)
    logging.debug(f"data = {data}")
    if data is None:
        return False
    return data[0] == except_state


class PBAPEventHandler:
    """PBAP event handler that processes events in a separate thread"""

    def __init__(self, pbap):
        self.pbap = pbap
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.worker_thread.start()
            logging.debug("PBAP event handler started")

    def stop(self):
        if self.running:
            self.running = False
            self.event_queue.put(None)  # Send stop signal
            if self.worker_thread:
                self.worker_thread.join(timeout=5)
            logging.debug("PBAP event handler stopped")

    def enqueue_event(self, event_id, data, data_len):
        self.event_queue.put((event_id, data, data_len))

    def _process_events(self):
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
                logging.error(f"Error processing PBAP event: {e}", exc_info=True)

    def _handle_event(self, event_id, data, data_len):
        handler = PBAP_EV_HANDLERS.get(event_id)
        if handler:
            try:
                handler(self.pbap, data, data_len)
            except Exception as e:
                logging.error(f"Error in PBAP event handler {handler.__name__}: {e}", exc_info=True)
        else:
            logging.warning(f"No handler for PBAP event {event_id}")


PBAP_EV_HANDLERS = {
    # PBAP Client (PCE) events
    defs.BTP_PBAP_EV_PCE_RFCOMM_CONNECTED: _pbap_pce_rfcomm_connected_ev,
    defs.BTP_PBAP_EV_PCE_RFCOMM_DISCONNECTED: _pbap_pce_rfcomm_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_L2CAP_CONNECTED: _pbap_pce_l2cap_connected_ev,
    defs.BTP_PBAP_EV_PCE_L2CAP_DISCONNECTED: _pbap_pce_l2cap_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_CONNECTED: _pbap_pce_connected_ev,
    defs.BTP_PBAP_EV_PCE_DISCONNECTED: _pbap_pce_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_PULL_PHONEBOOK: _pbap_pce_pull_phonebook_ev,
    defs.BTP_PBAP_EV_PCE_PULL_VCARD_LISTING: _pbap_pce_pull_vcard_listing_ev,
    defs.BTP_PBAP_EV_PCE_PULL_VCARD_ENTRY: _pbap_pce_pull_vcard_entry_ev,
    defs.BTP_PBAP_EV_PCE_SET_PHONE_BOOK: _pbap_pce_set_phone_book_ev,
    defs.BTP_PBAP_EV_PCE_ABORT: _pbap_pce_abort_ev,

    # PBAP Server (PSE) events
    defs.BTP_PBAP_EV_PSE_RFCOMM_CONNECTED: _pbap_pse_rfcomm_connected_ev,
    defs.BTP_PBAP_EV_PSE_RFCOMM_DISCONNECTED: _pbap_pse_rfcomm_disconnected_ev,
    defs.BTP_PBAP_EV_PSE_L2CAP_CONNECTED: _pbap_pse_l2cap_connected_ev,
    defs.BTP_PBAP_EV_PSE_L2CAP_DISCONNECTED: _pbap_pse_l2cap_disconnected_ev,
    defs.BTP_PBAP_EV_PSE_CONNECT: _pbap_pse_connect_ev,
    defs.BTP_PBAP_EV_PSE_DISCONNECT: _pbap_pse_disconnect_ev,
    defs.BTP_PBAP_EV_PSE_PULL_PHONEBOOK: _pbap_pse_pull_phonebook_ev,
    defs.BTP_PBAP_EV_PSE_PULL_VCARD_LISTING: _pbap_pse_pull_vcard_listing_ev,
    defs.BTP_PBAP_EV_PSE_PULL_VCARD_ENTRY: _pbap_pse_pull_vcard_entry_ev,
    defs.BTP_PBAP_EV_PSE_SET_PHONE_BOOK: _pbap_pse_set_phone_book_ev,
    defs.BTP_PBAP_EV_PSE_ABORT: _pbap_pse_abort_ev,

    # SDP event
    defs.BTP_PBAP_EV_SDP_DISCOVER: _pbap_sdp_discover_ev,
}


def pbap_pce_rfcomm_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_rfcomm_connected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_RFCOMM_CONNECTED, data, data_len)


def pbap_pce_rfcomm_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_rfcomm_disconnected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_RFCOMM_DISCONNECTED, data, data_len)


def pbap_pce_l2cap_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_l2cap_connected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_L2CAP_CONNECTED, data, data_len)


def pbap_pce_l2cap_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_l2cap_disconnected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_L2CAP_DISCONNECTED, data, data_len)


def pbap_pce_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_connected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_CONNECTED, data, data_len)


def pbap_pce_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_disconnected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_DISCONNECTED, data, data_len)


def pbap_pce_pull_phonebook_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_pull_phonebook_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_PULL_PHONEBOOK, data, data_len)


def pbap_pce_pull_vcard_listing_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_pull_vcard_listing_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_PULL_VCARD_LISTING, data, data_len)


def pbap_pce_pull_vcard_entry_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_pull_vcard_entry_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_PULL_VCARD_ENTRY, data, data_len)


def pbap_pce_set_phone_book_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_set_phone_book_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_SET_PHONE_BOOK, data, data_len)


def pbap_pce_abort_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pce_abort_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PCE_ABORT, data, data_len)


def pbap_pse_rfcomm_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_rfcomm_connected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_RFCOMM_CONNECTED, data, data_len)


def pbap_pse_rfcomm_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_rfcomm_disconnected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_RFCOMM_DISCONNECTED, data, data_len)


def pbap_pse_l2cap_connected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_l2cap_connected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_L2CAP_CONNECTED, data, data_len)


def pbap_pse_l2cap_disconnected_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_l2cap_disconnected_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_L2CAP_DISCONNECTED, data, data_len)


def pbap_pse_connect_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_connect_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_CONNECT, data, data_len)


def pbap_pse_disconnect_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_disconnect_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_DISCONNECT, data, data_len)


def pbap_pse_pull_phonebook_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_pull_phonebook_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_PULL_PHONEBOOK, data, data_len)


def pbap_pse_pull_vcard_listing_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_pull_vcard_listing_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_PULL_VCARD_LISTING, data, data_len)


def pbap_pse_pull_vcard_entry_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_pull_vcard_entry_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_PULL_VCARD_ENTRY, data, data_len)


def pbap_pse_set_phone_book_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_set_phone_book_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_SET_PHONE_BOOK, data, data_len)


def pbap_pse_abort_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_pse_abort_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_PSE_ABORT, data, data_len)


def pbap_sdp_discover_ev(pbap, data, data_len):
    logging.debug("%s %r %r %r", pbap_sdp_discover_ev.__name__, pbap, data, data_len)
    pbap.event_handler.enqueue_event(defs.BTP_PBAP_EV_SDP_DISCOVER, data, data_len)


# Event handlers dictionary
PBAP_EV = {
    defs.BTP_PBAP_EV_PCE_RFCOMM_CONNECTED: pbap_pce_rfcomm_connected_ev,
    defs.BTP_PBAP_EV_PCE_RFCOMM_DISCONNECTED: pbap_pce_rfcomm_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_L2CAP_CONNECTED: pbap_pce_l2cap_connected_ev,
    defs.BTP_PBAP_EV_PCE_L2CAP_DISCONNECTED: pbap_pce_l2cap_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_CONNECTED: pbap_pce_connected_ev,
    defs.BTP_PBAP_EV_PCE_DISCONNECTED: pbap_pce_disconnected_ev,
    defs.BTP_PBAP_EV_PCE_PULL_PHONEBOOK: pbap_pce_pull_phonebook_ev,
    defs.BTP_PBAP_EV_PCE_PULL_VCARD_LISTING: pbap_pce_pull_vcard_listing_ev,
    defs.BTP_PBAP_EV_PCE_PULL_VCARD_ENTRY: pbap_pce_pull_vcard_entry_ev,
    defs.BTP_PBAP_EV_PCE_SET_PHONE_BOOK: pbap_pce_set_phone_book_ev,
    defs.BTP_PBAP_EV_PCE_ABORT: pbap_pce_abort_ev,
    defs.BTP_PBAP_EV_PSE_RFCOMM_CONNECTED: pbap_pse_rfcomm_connected_ev,
    defs.BTP_PBAP_EV_PSE_RFCOMM_DISCONNECTED: pbap_pse_rfcomm_disconnected_ev,
    defs.BTP_PBAP_EV_PSE_L2CAP_CONNECTED: pbap_pse_l2cap_connected_ev,
    defs.BTP_PBAP_EV_PSE_L2CAP_DISCONNECTED: pbap_pse_l2cap_disconnected_ev,
    defs.BTP_PBAP_EV_PSE_CONNECT: pbap_pse_connect_ev,
    defs.BTP_PBAP_EV_PSE_DISCONNECT: pbap_pse_disconnect_ev,
    defs.BTP_PBAP_EV_PSE_PULL_PHONEBOOK: pbap_pse_pull_phonebook_ev,
    defs.BTP_PBAP_EV_PSE_PULL_VCARD_LISTING: pbap_pse_pull_vcard_listing_ev,
    defs.BTP_PBAP_EV_PSE_PULL_VCARD_ENTRY: pbap_pse_pull_vcard_entry_ev,
    defs.BTP_PBAP_EV_PSE_SET_PHONE_BOOK: pbap_pse_set_phone_book_ev,
    defs.BTP_PBAP_EV_PSE_ABORT: pbap_pse_abort_ev,
    defs.BTP_PBAP_EV_SDP_DISCOVER: pbap_sdp_discover_ev,
}
