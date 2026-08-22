#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
import struct
from enum import IntEnum, IntFlag
from typing import Final, NamedTuple
from uuid import UUID as StdUUID

from autopts.pybtp import defs

gap_settings_btp2txt = {
    defs.GAP_SETTINGS_POWERED: "Powered",
    defs.GAP_SETTINGS_CONNECTABLE: "Connectable",
    defs.GAP_SETTINGS_FAST_CONNECTABLE: "Fast Connectable",
    defs.GAP_SETTINGS_DISCOVERABLE: "Discoverable",
    defs.GAP_SETTINGS_BONDABLE: "Bondable",
    defs.GAP_SETTINGS_LINK_SEC_3: "Link Level Security",
    defs.GAP_SETTINGS_SSP: "SSP",
    defs.GAP_SETTINGS_BREDR: "BREDR",
    defs.GAP_SETTINGS_HS: "HS",
    defs.GAP_SETTINGS_LE: "LE",
    defs.GAP_SETTINGS_ADVERTISING: "Advertising",
    defs.GAP_SETTINGS_SC: "SC",
    defs.GAP_SETTINGS_DEBUG_KEYS: "Debug Keys",
    defs.GAP_SETTINGS_PRIVACY: "Privacy",
    defs.GAP_SETTINGS_CONTROLLER_CONFIG: "Controller Configuration",
    defs.GAP_SETTINGS_STATIC_ADDRESS: "Static Address",
    defs.GAP_SETTINGS_SC_ONLY: "SC Only",
    defs.GAP_SETTINGS_EXTENDED_ADVERTISING: "Extended Advertising",
}


# =============================================================================
# Byte Order Conversion Utilities
# =============================================================================
# BTP protocol uses little-endian byte order, while PTS often uses big-endian.
# These helpers provide explicit type-based names for byte order conversions.


def is_hex_str(value: str) -> bool:
    """Return True if value contains only hexadecimal digits."""
    return all(ch in "0123456789abcdefABCDEF" for ch in value)


def hex_str_to_le_bytes(hex_str: str) -> bytes:
    """Convert a hex string (big-endian) to little-endian bytes.

    PTS often provides values in big-endian hex format, while BTP
    expects little-endian. This function handles the conversion.

    Args:
        hex_str: Hex string in big-endian format (e.g., "0001020304050607").
                 An optional "0x" prefix is stripped automatically.
                 Must contain an even number of hex digits.

    Returns:
        Bytes in little-endian format

    Raises:
        ValueError: If hex_str has an odd number of digits or contains
                    non-hex characters.

    Example:
        >>> hex_str_to_le_bytes("0001020304050607")  # For IV conversion
        b'\\x07\\x06\\x05\\x04\\x03\\x02\\x01\\x00'
    """
    if not isinstance(hex_str, str):
        raise TypeError(f"hex_str_to_le_bytes expects str, got {type(hex_str).__name__}")

    cleaned = hex_str
    if cleaned.startswith(("0x", "0X")):
        cleaned = cleaned[2:]
    if (len(cleaned) & 1) != 0:
        raise ValueError(
            f"hex_str_to_le_bytes: odd-length hex string ({len(cleaned)} digits): {cleaned!r}")
    if not is_hex_str(cleaned):
        raise ValueError(f"hex_str_to_le_bytes: invalid hex string: {hex_str!r}")
    return bytes.fromhex(cleaned)[::-1]


def le_bytes_to_hex_str(data: bytes) -> str:
    """Convert little-endian bytes to big-endian hex string.

    Args:
        data: Bytes in little-endian format

    Returns:
        Hex string in big-endian format

    Example:
        >>> le_bytes_to_hex_str(b'\\x07\\x06\\x05\\x04\\x03\\x02\\x01\\x00')
        '0001020304050607'
    """
    return data[::-1].hex()


# -- UUID helpers --

def uuid_to_le_bytes(uuid: int | str) -> bytes:
    """Convert UUID string or integer to little-endian bytes.

    Handles 16-bit, 32-bit, and 128-bit UUIDs as strings or integers.

    Args:
        uuid: UUID as hex string (optionally with dashes or "0x" prefix)
              or as an integer

    Returns:
        UUID bytes in little-endian format

    Example:
        >>> uuid_to_le_bytes("184E")
        b'N\\x18'
        >>> uuid_to_le_bytes(0x184E)
        b'N\\x18'
    """
    if isinstance(uuid, int):
        if uuid < 0:
            raise ValueError("uuid_to_le_bytes: UUID integer must be >= 0")
        if uuid <= 0xFFFF:
            return struct.pack('<H', uuid)
        if uuid <= 0xFFFFFFFF:
            return struct.pack('<I', uuid)
        if uuid <= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
            return uuid.to_bytes(16, byteorder='little')
        raise ValueError("uuid_to_le_bytes: UUID integer out of 128-bit range")

    if not isinstance(uuid, str):
        raise TypeError(f"uuid_to_le_bytes expects int|str, got {type(uuid).__name__}")

    cleaned = uuid.replace("-", "")
    if cleaned.startswith(("0x", "0X")):
        cleaned = cleaned[2:]
    if len(cleaned) not in (4, 8, 32):
        raise ValueError(
            f"uuid_to_le_bytes: expected 16/32/128-bit UUID (4/8/32 hex chars), got {len(cleaned)}")
    if not is_hex_str(cleaned):
        raise ValueError(f"uuid_to_le_bytes: invalid UUID hex string: {uuid!r}")
    return bytes.fromhex(cleaned)[::-1]


def uuid_to_le_hex_str(uuid_str: str) -> str:
    """Convert UUID string to little-endian hex string.

    Useful for advertising data where UUID needs to be in little-endian
    hex string format.

    Args:
        uuid_str: UUID string (e.g., "184E" for ASCS)

    Returns:
        Hex string in little-endian format

    Example:
        >>> uuid_to_le_hex_str("184E")  # ASCS UUID
        '4e18'
    """
    return uuid_to_le_bytes(uuid_str).hex()


def le_bytes_to_uuid(uuid_bytes: bytes, uuid_len: int | None = None) -> str:
    """Convert little-endian UUID bytes to big-endian UUID hex string.

    Handles 16-bit, 32-bit, and 128-bit UUIDs.

    Args:
        uuid_bytes: UUID bytes in little-endian format.
        uuid_len: Length of UUID in bytes. If omitted, inferred from uuid_bytes.

    Returns:
        Uppercase hex string of UUID in big-endian format

    Example:
        >>> le_bytes_to_uuid(b'\\x4e\\x18')
        '184E'
    """
    if not isinstance(uuid_bytes, (bytes, bytearray)):
        raise TypeError(
            f"le_bytes_to_uuid: uuid bytes must be bytes-like, got {type(uuid_bytes).__name__}")
    uuid_bytes = bytes(uuid_bytes)

    if uuid_len is None:
        uuid_len = len(uuid_bytes)
    elif not isinstance(uuid_len, int):
        raise TypeError(f"le_bytes_to_uuid: uuid length must be int, got {type(uuid_len).__name__}")
    elif uuid_len != len(uuid_bytes):
        raise ValueError(
            f"le_bytes_to_uuid: uuid_len={uuid_len} does not match byte length={len(uuid_bytes)}")

    if uuid_len == 2:
        (uu,) = struct.unpack("<H", uuid_bytes)
        return format(uu, 'x').upper().rjust(4, '0')
    if uuid_len == 4:
        (uu,) = struct.unpack("<I", uuid_bytes)
        return format(uu, 'x').upper().rjust(8, '0')
    if uuid_len != 16:
        raise ValueError(f"le_bytes_to_uuid: unsupported UUID length {uuid_len}")
    return StdUUID(bytes=uuid_bytes[::-1]).urn[9:].replace('-', '').upper()


# -- Address helpers --

def addr_str_to_le_bytes(addr_str: str) -> bytes:
    """Convert address hex string to little-endian bytes.

    Accepts colon-separated or plain hex strings.

    Args:
        addr_str: Address string (e.g., "AA:BB:CC:DD:EE:FF" or "AABBCCDDEEFF")

    Returns:
        Address bytes in little-endian format
    """
    if not isinstance(addr_str, str):
        raise TypeError(f"addr_str_to_le_bytes expects str, got {type(addr_str).__name__}")

    cleaned = "".join(addr_str.split(':'))
    if len(cleaned) != 12:
        raise ValueError(
            f"addr_str_to_le_bytes: expected 12 hex digits (6 bytes), got {len(cleaned)}: {addr_str!r}")
    if not is_hex_str(cleaned):
        raise ValueError(f"addr_str_to_le_bytes: invalid address hex string: {addr_str!r}")
    return binascii.unhexlify(cleaned)[::-1]


class BTPError(Exception):
    """Exception raised if BTP error occurs.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP error has occurred.

    """


class BTPFatalError(Exception):
    """Exception raised if BTP error occurs and the IUT needs to be recovered.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP fatal error has occurred.
    """


class BTPInitError(Exception):
    """Exception raised for IUT ready event non-occurence"""


class SynchError(Exception):
    """Exception raised if cannot synchronize"""


class MissingWIDError(Exception):
    pass


class AdType:
    flags = 1
    uuid16_some = 2
    uuid16_all = 3
    name_short = 8
    name_full = 9
    tx_power = 10
    uuid16_svc_solicit = 20
    uuid16_svc_data = 22
    gap_appearance = 25
    manufacturer_data = 255
    slave_conn_interval_range = 0x12
    public_target_addr = 0x17
    random_target_addr = 0x18
    advertising_interval = 0x1a
    advertising_interval_long = 0x2f
    le_bt_device_addr = 0x1b
    le_role = 0x1c
    uri = 0x24
    le_supp_feat = 0x27
    rsi = 0x2e
    encrypted_data = 0x31


class AdFlags:
    le_limit_discov_mode = 0x01
    le_gen_discov_mode = 0x02
    br_edr_not_supp = 0x04
    sim_le_br_edr_contr = 0x08
    sim_le_br_edr_host = 0x10


class AdDuration:
    forever = 0xFFFFFFFF


class UriScheme:
    https = b'\x17'


class UUID:
    gap_svc = '1800'
    gatt_svc = '1801'
    ASCS = '184E'
    BASS = '184F'
    PACS = '1850'
    CAS = '1853'
    TMAP = '1855'
    ASE_CP = '2BC6'
    CEP = '2900'
    CUD = '2901'
    CCC = '2902'
    SCC = '2903'
    CPF = '2904'
    CAF = '2905'
    CSF = '2B29'
    device_name = '2A00'
    appearance = '2A01'
    service_changed = '2A05'
    battery_level = '2A19'
    date_of_birth = '2A85'
    gender = '2A8C'
    proxy_cli_data_in = '2ADD'
    SINK_ASE = '2BC4'
    SOURCE_ASE = '2BC5'
    SINK_PAC = '2BC9'
    SOURCE_PAC = '2BCB'
    AVAILABLE_AUDIO_CTXS = '2BCD'
    HAS_HEARING_AID_FEATUES = '2BDA'
    HAS_HEARING_AID_CONTROL_POINT = '2BDB'
    HAS_ACTIVE_PRESET_INDEX = '2BDC'
    SVND16_0 = 'AA40'
    SVND16_1 = 'AA41'
    VND16_0 = 'AA50'
    VND16_1 = 'AA51'
    VND16_2 = 'AA52'
    VND16_3 = 'AA53'
    VND16_4 = 'AA54'
    VND16_5 = 'AA55'
    VND16_6 = 'AA56'
    VND16_7 = 'AA57'
    VND16_8 = 'AA58'
    VND16_9 = 'AA59'
    VND16_10 = 'AA5A'
    VND128_1 = 'F000BB5004514000B123456789ABCDEF'
    VND128_2 = 'F000BB5104514000B123456789ABCDEF'
    VND128_3 = 'F000BB5204514000B123456789ABCDEF'


class IOCap:
    display_only = 0
    display_yesno = 1
    keyboard_only = 2
    no_input_output = 3
    keyboard_display = 4


class Addr:
    le_public = 0
    le_random = 1


class OwnAddrType:
    le_identity_address = 0
    le_resolvable_private_address = 1
    le_non_resolvable_private_address = 2


class MeshVals:
    subscription_addr_list1 = 'C302'


def decode_flag_name(flag, names_dict):
    """Returns string description that corresponds to flag"""

    decoded_str = ""
    sep = ", "

    for named_flag in sorted(names_dict.keys()):
        if (flag & named_flag) == named_flag:
            decoded_str += names_dict[named_flag] + sep

    if decoded_str.endswith(sep):
        decoded_str = decoded_str.rstrip(sep)

    return decoded_str


class Prop:
    """Properties of characteresic

    Specified in BTP spec:

    Possible values for the Properties parameter are a bit-wise of the
    following bits:

    0       Broadcast
    1       Read
    2       Write Without Response
    3       Write
    4       Notify
    5       Indicate
    6       Authenticated Signed Writes
    7       Extended Properties

    """
    broadcast = 2 ** 0
    read = 2 ** 1
    write_wo_resp = 2 ** 2
    write = 2 ** 3
    notify = 2 ** 4
    indicate = 2 ** 5
    auth_swrite = 2 ** 6
    ext_prop = 2 ** 7

    names = {
        broadcast: "Broadcast",
        read: "Read",
        write_wo_resp: "Write Without Response",
        write: "Write",
        notify: "Notify",
        indicate: "Indicate",
        auth_swrite: "Authenticated Signed Writes",
        ext_prop: "Extended Properties",
    }

    @staticmethod
    def decode(prop):
        return decode_flag_name(prop, Prop.names)


class Perm:
    """Permission of characteresic or descriptor

    Specified in BTP spec:

    Possible values for the Permissions parameter are a bit-wise of the
    following bits:

    0       Read
    1       Write
    2       Read with Encryption
    3       Write with Encryption
    4       Read with Authentication
    5       Write with Authentication
    6       Authorization

    """
    read = 2 ** 0
    write = 2 ** 1
    read_enc = 2 ** 2
    write_enc = 2 ** 3
    read_authn = 2 ** 4
    write_authn = 2 ** 5
    read_authz = 2 ** 6
    write_authz = 2 ** 7

    names = {
        read: "Read",
        write: "Write",
        read_enc: "Read with Encryption",
        write_enc: "Write with Encryption",
        read_authn: "Read with Authentication",
        write_authn: "Write with Authentication",
        read_authz: "Read with Authorization",
        write_authz: "Write with Authorization"
    }

    @staticmethod
    def decode(perm):
        return decode_flag_name(perm, Perm.names)


class L2CAPConnectionResponse:
    success = 0
    insufficient_authentication = 1
    insufficient_authorization = 2
    insufficient_encryption_key_size = 3
    insufficient_encryption = 4
    insufficient_secure_authentication = 5


class WIDParams(NamedTuple):
    wid: int
    description: str
    test_case_name: str


att_rsp_str = {0: "",
               1: "Invalid handle error",
               2: "read is not permitted error",
               3: "write is not permitted error",
               5: "authentication error",
               7: "Invalid offset error",
               8: "authorization error",
               10: "attribute not found error",
               12: "encryption key size error",
               13: "Invalid attribute value length error",
               14: "unlikely error",
               15: "insufficient encryption",
               128: "Application error",
               }


class GATTErrorCodes:
    invalid_handle = 0x01
    read_not_permitted = 0x02
    write_not_permitted = 0x03
    invalid_pdu = 0x04
    insufficient_authentication = 0x05
    request_not_supported = 0x06
    invalid_offset = 0x07
    insufficient_authorization = 0x08
    prepare_queue_full = 0x09
    attribute_not_found = 0x0a
    attribute_not_long = 0x0b
    encryption_key_size_too_short = 0x0c
    invalid_attribute_value_length = 0x0d
    unlikely_error = 0x0e
    insufficient_encryption = 0x0f
    unsupported_group_type = 0x10
    insufficient_resources = 0x11
    database_out_of_sync = 0x12
    value_not_allowed = 0x13


class ASCSState(IntEnum):
    IDLE = 0x00
    CODEC_CONFIGURED = 0x01
    QOS_CONFIGURED = 0x02
    ENABLING = 0x03
    STREAMING = 0x04
    DISABLING = 0x05
    RELEASING = 0x06


class Context(IntFlag):
    PROHIBITED = 0x0000
    UNSPECIFIED = 0x0001
    CONVERSATIONAL = 0x0002
    MEDIA = 0x0004
    GAME = 0x0008
    INSTRUCTIONAL = 0x0010
    VOICE_ASSISTANTS = 0x0020
    LIVE = 0x0040
    SOUND_EFFECTS = 0x0080
    NOTIFICATIONS = 0x0100
    RINGTONE = 0x0200
    ALERTS = 0x0400
    EMERGENCY_ALARM = 0x0800
    ANY_CONTEXT = 0x0FFF


class AudioDir:
    SINK = 0x01
    SOURCE = 0x02


class ASCSOperation:
    CONFIG_CODEC = 0x01
    CONFIG_QOS = 0x02
    ENABLE = 0x03
    RECEIVER_START_READY = 0x04
    DISABLE = 0x05
    RECEIVER_STOP_READY = 0x06
    UPDATE_METADATA = 0x07
    RELEASE = 0x08


# Assigned Numbers (2023), 6.12.4 Codec_Specific_Capabilities LTV Structures
class LC3_PAC_LTV_Type:
    SAMPLING_FREQ = 0x01
    FRAME_DURATION = 0x02
    CHANNELS = 0x03
    FRAME_LEN = 0x04
    FRAMES_PER_SDU = 0x05


# Assigned Numbers (2023), 6.12.5 Codec_Specific_Configuration LTV structures
class LC3_LTV_Config_Type:
    SAMPLING_FREQ = 0x01
    FRAME_DURATION = 0x02
    CHANNEL_ALLOCATION = 0x03
    FRAME_LEN = 0x04
    FRAMES_PER_SDU = 0x05


SAMPLING_FREQ_STR_TO_CODE = {
    '8': 0x01,  # 8000 Hz
    '11.025': 0x02,  # 11025 Hz
    '16': 0x03,  # 16000 Hz
    '22.05': 0x04,  # 22050 Hz
    '24': 0x05,  # 24000 Hz
    '32': 0x06,  # 32000 Hz
    '44.1': 0x07,  # 44100 Hz
    '48': 0x08,  # 48000 Hz
    '88.2': 0x09,  # 88200 Hz
    '96': 0x0a,  # 96000 Hz
    '176.4': 0x0b,  # 1764000 Hz
    '192': 0x0c,  # 192000 Hz
    '384': 0x0d,  # 384000 Hz
}

FRAME_DURATION_STR_TO_CODE = {
    '7.5': 0x00,  # 7.5 ms
    '10': 0x01,  # 10 ms
}

CODEC_CONFIG_SETTINGS = {
    # Set_Name: (Sampling_Frequency, Frame_Duration, Octets_Per_Codec_Frame)
    '8_1': (0x01, 0x00, 26),
    '8_2': (0x01, 0x01, 30),
    '16_1': (0x03, 0x00, 30),
    '16_2': (0x03, 0x01, 40),
    '24_1': (0x05, 0x00, 45),
    '24_2': (0x05, 0x01, 60),
    '32_1': (0x06, 0x00, 60),
    '32_2': (0x06, 0x01, 80),
    '441_1': (0x07, 0x00, 97),
    '441_2': (0x07, 0x01, 130),
    '48_1': (0x08, 0x00, 75),
    '48_2': (0x08, 0x01, 100),
    '48_3': (0x08, 0x00, 90),
    '48_4': (0x08, 0x01, 120),
    '48_5': (0x08, 0x00, 117),
    '48_6': (0x08, 0x01, 155),
}

QOS_CONFIG_SETTINGS = {
    # Set_Name: (SDU_interval, Framing, Maximum_SDU_Size, Retransmission_Number, Max_Transport_Latency)
    '8_1_1': (7500, 0x00, 26, 2, 8),
    '8_2_1': (10000, 0x00, 30, 2, 10),
    '16_1_1': (7500, 0x00, 30, 2, 8),
    '16_2_1': (10000, 0x00, 40, 2, 10),
    '24_1_1': (7500, 0x00, 45, 2, 8),
    '24_2_1': (10000, 0x00, 60, 2, 10),
    '32_1_1': (7500, 0x00, 60, 2, 8),
    '32_2_1': (10000, 0x00, 80, 2, 10),
    '441_1_1': (8163, 0x01, 97, 5, 24),
    '441_2_1': (10884, 0x01, 130, 5, 31),
    '48_1_1': (7500, 0x00, 75, 5, 15),
    '48_2_1': (10000, 0x00, 100, 5, 20),
    '48_3_1': (7500, 0x00, 90, 5, 15),
    '48_4_1': (10000, 0x00, 120, 5, 20),
    '48_5_1': (7500, 0x00, 117, 5, 15),
    '48_6_1': (10000, 0x00, 155, 5, 20),
    '8_1_2': (7500, 0x00, 26, 13, 75),
    '8_2_2': (10000, 0x00, 30, 13, 95),
    '16_1_2': (7500, 0x00, 30, 13, 75),
    '16_2_2': (10000, 0x00, 40, 13, 95),
    '24_1_2': (7500, 0x00, 45, 13, 75),
    '24_2_2': (10000, 0x00, 60, 13, 95),
    '32_1_2': (7500, 0x00, 60, 13, 75),
    '32_2_2': (10000, 0x00, 80, 13, 95),
    '441_1_2': (8163, 0x01, 97, 13, 80),
    '441_2_2': (10884, 0x01, 130, 13, 85),
    '48_1_2': (7500, 0x00, 75, 13, 75),
    '48_2_2': (10000, 0x00, 100, 13, 95),
    '48_3_2': (7500, 0x00, 90, 13, 75),
    '48_4_2': (10000, 0x00, 120, 13, 100),
    '48_5_2': (7500, 0x00, 117, 13, 75),
    '48_6_2': (10000, 0x00, 155, 13, 100),
}


def create_lc3_ltvs_bytes(sampling_freq, frame_duration, audio_locations,
                          octets_per_frame, frames_per_sdu):
    ltvs = bytearray()
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.SAMPLING_FREQ, sampling_freq)
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.FRAME_DURATION, frame_duration)

    if audio_locations:
        ltvs += struct.pack('<BBI', 5, LC3_LTV_Config_Type.CHANNEL_ALLOCATION, audio_locations)

    ltvs += struct.pack('<BBH', 3, LC3_LTV_Config_Type.FRAME_LEN, octets_per_frame)
    ltvs += struct.pack('<BBB', 2, LC3_LTV_Config_Type.FRAMES_PER_SDU, frames_per_sdu)

    return ltvs


class PaSyncState:
    NOT_SYNCED = 0x00
    SYNC_INFO_REQ = 0x01
    SYNCED = 0x02
    FAILED_TO_SYNC = 0x03
    NO_PAST = 0x04


class BIGEncryption:
    NOT_ENCRYPTED = 0x00
    BROADCAST_CODE_REQUIRED = 0x01
    DECRYPTING = 0x02
    BAD_CODE = 0x03


class BASSPASyncState:
    """Periodic Advertising state reported by the Scan Delegator.

    Values match enum bt_bap_pa_state in Zephyr.
    """
    NOT_SYNCED = 0x00
    INFO_REQ = 0x01
    SYNCED = 0x02
    FAILED = 0x03
    NO_PAST = 0x04


# 0xFFFF indicates "unknown" as per the BASS specification
BASS_PA_INTERVAL_UNKNOWN: Final[int] = 0xFFFF


class TMAPRole(IntFlag):
    CALL_GATEWAY = defs.BIT(0)
    CALL_TERMINAL = defs.BIT(1)
    UNICAST_MEDIA_SENDER = defs.BIT(2)
    UNICAST_MEDIA_RECEIVER = defs.BIT(3)
    BROADCAST_MEDIA_SENDER = defs.BIT(4)
    BROADCAST_MEDIA_RECEIVER = defs.BIT(5)


class BAPAnnouncement:
    GENERAL = 0x0
    TARGETED = 0x1


class CAPAnnouncement:
    GENERAL = 0x0
    TARGETED = 0x1


class OptionalOpcode(IntFlag):
    LOCAL_HOLD = defs.BIT(0)   # 0x0001
    JOIN = defs.BIT(1)         # 0x0002
    ALL = LOCAL_HOLD | JOIN    # 0x0003


class BearerTech(IntEnum):
    CELL_3G = 0x01
    CELL_4G = 0x02
    LTE = 0x03
    WIFI = 0x04
    CELL_5G = 0x05
    GSM = 0x06
    CDMA = 0x07
    CELL_2G = 0x08
    WCDMA = 0x09


class PBAPTransportType:
    RFCOMM_CONN = 0
    L2CAP_CONN = 1


class PBAPRole:
    PCE = 0  # Phone Book Client Equipment
    PSE = 1  # Phone Book Server Equipment


class PBAPPullType:
    PHONEBOOK = "x-bt/phonebook"
    VCARDLISTING = "x-bt/vcard-listing"
    VCARDENTRY = "x-bt/vcard"


class PBAPSupportedFeature:
    """PBAP supported features enumeration"""

    DOWNLOAD = (1 << 0)
    BROWSING = (1 << 1)
    DATABASE_IDENTIFIER = (1 << 2)
    FOLDER_VERSION_COUNTERS = (1 << 3)
    VCARD_SELECTOR = (1 << 4)
    ENHANCED_MISSED_CALLS = (1 << 5)
    UCI_VCARD_PROPERTY = (1 << 6)
    UID_VCARD_PROPERTY = (1 << 7)
    CONTACT_REFERENCING = (1 << 8)
    DEFAULT_CONTACT_IMAGE = (1 << 9)


class BtPbapApplParamTagId:
    ORDER = 0x01
    SEARCH_VALUE = 0x02
    SEARCH_PROPERTY = 0x03
    MAX_LIST_COUNT = 0x04
    LIST_START_OFFSET = 0x05
    PROPERTY_SELECTOR = 0x06
    FORMAT = 0x07
    PHONEBOOK_SIZE = 0x08
    NEW_MISSED_CALLS = 0x09
    PRIMARY_FOLDER_VERSION = 0x0a
    SECONDARY_FOLDER_VERSION = 0x0b
    VCARD_SELECTOR = 0x0c
    DATABASE_IDENTIFIER = 0x0d
    VCARD_SELECTOR_OPERATOR = 0x0e
    RESET_NEW_MISSED_CALLS = 0x0f
    SUPPORTED_FEATURES = 0x10


class PBAPAppParamTag:
    ORDER = 0x01
    SEARCH_VALUE = 0x02
    SEARCH_PROPERTY = 0x03
    MAX_LIST_COUNT = 0x04
    LIST_START_OFFSET = 0x05
    PROPERTY_SELECTOR = 0x06
    FORMAT = 0x07
    PHONEBOOK_SIZE = 0x08
    NEW_MISSED_CALLS = 0x09
    PRIMARY_FOLDER_VERSION = 0x0A
    SECONDARY_FOLDER_VERSION = 0x0B
    VCARD_SELECTOR = 0x0C
    DATABASE_IDENTIFIER = 0x0D
    VCARD_SELECTOR_OPERATOR = 0x0E
    RESET_NEW_MISSED_CALLS = 0x0F
    SUPPORTED_FEATURES = 0x10


class PBAPPropertySelector:
    VERSION = (1 << 0)
    FN = (1 << 1)
    N = (1 << 2)
    PHOTO = (1 << 3)
    BDAY = (1 << 4)
    ADR = (1 << 5)
    LABEL = (1 << 6)
    TEL = (1 << 7)
    EMAIL = (1 << 8)
    MAILER = (1 << 9)
    TZ = (1 << 10)
    GEO = (1 << 11)
    TITLE = (1 << 12)
    ROLE = (1 << 13)
    LOGO = (1 << 14)
    AGENT = (1 << 15)
    ORG = (1 << 16)
    NOTE = (1 << 17)
    REV = (1 << 18)
    SOUND = (1 << 19)
    URL = (1 << 20)
    UID = (1 << 21)
    KEY = (1 << 22)
    NICKNAME = (1 << 23)
    CATEGORIES = (1 << 24)
    PRODID = (1 << 25)
    CLASS = (1 << 26)
    SORT_STRING = (1 << 27)
    X_IRMC_CALL_DATETIME = (1 << 28)
    X_BT_SPEEDDIALKEY = (1 << 29)
    X_BT_UCI = (1 << 30)
    X_BT_UID = (1 << 31)
    PROPRIETARY_FILTER = 0x8000000000


class OBEXHdr:
    COUNT = 0xC0
    NAME = 0x01
    TYPE = 0x42
    LEN = 0xC3
    TIME_ISO_8601 = 0x44
    TIME = 0xC4
    DES = 0x05
    TARGET = 0x46
    HTTP = 0x47
    BODY = 0x48
    END_BODY = 0x49
    WHO = 0x4A
    CONN_ID = 0xCB
    APP_PARAM = 0x4C
    AUTH_CHALLENGE = 0x4D
    AUTH_RSP = 0x4E
    CREATE_ID = 0xCF
    WAN_UUID = 0x50
    OBJECT_CLASS = 0x51
    SESSION_PARAM = 0x52
    SESSION_SEQ_NUM = 0x93
    ACTION_ID = 0x94
    DEST_NAME = 0x15
    PERM = 0xD6
    SRM = 0x97
    SRMP = 0x98


class OBEXRspCode:
    CONTINUE = 0x90
    OK = 0xa0
    SUCCESS = 0xa0
    CREATED = 0xa1
    ACCEPTED = 0xa2
    NON_AUTH_INFO = 0xa3
    NO_CONTENT = 0xa4
    RESET_CONTENT = 0xa5
    PARTIAL_CONTENT = 0xa6
    MULTI_CHOICES = 0xb0
    MOVED_PERM = 0xb1
    MOVED_TEMP = 0xb2
    SEE_OTHER = 0xb3
    NOT_MODIFIED = 0xb4
    USE_PROXY = 0xb5
    BAD_REQ = 0xc0
    UNAUTH = 0xc1
    PAY_REQ = 0xc2
    FORBIDDEN = 0xc3
    NOT_FOUND = 0xc4
    NOT_ALLOW = 0xc5
    NOT_ACCEPT = 0xc6
    PROXY_AUTH_REQ = 0xc7
    REQ_TIMEOUT = 0xc8
    CONFLICT = 0xc9
    GONE = 0xca
    LEN_REQ = 0xcb
    PRECON_FAIL = 0xcc
    ENTITY_TOO_LARGE = 0xcd
    URL_TOO_LARGE = 0xce
    UNSUPP_MEDIA_TYPE = 0xcf
    INTER_ERROR = 0xd0
    NOT_IMPL = 0xd1
    BAD_GATEWAY = 0xd2
    UNAVAIL = 0xd3
    GATEWAY_TIMEOUT = 0xd4
    VER_UNSUPP = 0xd5
    DB_FULL = 0xe0
    DB_LOCK = 0xe1


class OBEXAuthTag:
    AUTH_REQ_NONCE = 0x00
    AHTH_REQ_OPTIONS = 0x01
    AUTH_REQ_REALM = 0x02
    AUTH_RSP_DIGEST = 0x00
    AUTH_RSP_USER_ID = 0x01
    AUTH_RSP_NONCE = 0x02
