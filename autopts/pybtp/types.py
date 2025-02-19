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

import struct

from enum import IntEnum, IntFlag
from binascii import unhexlify
from typing import NamedTuple

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


def addr2btp_ba(addr_str):
    return unhexlify("".join(addr_str.split(':')))[::-1]


def bdaddr_reverse(addr):
    return ''.join([addr[i:i + 2] for i in range(0, len(addr), 2)][::-1])


class BTPError(Exception):
    """Exception raised if BTP error occurs.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP error has occurred.

    """


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
    IDLE                = 0x00
    CODEC_CONFIGURED    = 0x01
    QOS_CONFIGURED      = 0x02
    ENABLING            = 0x03
    STREAMING           = 0x04
    DISABLING           = 0x05
    RELEASING           = 0x06


class Context(IntFlag):
    PROHIBITED          = 0x0000
    UNSPECIFIED         = 0x0001
    CONVERSATIONAL      = 0x0002
    MEDIA               = 0x0004
    GAME                = 0x0008
    INSTRUCTIONAL       = 0x0010
    VOICE_ASSISTANTS    = 0x0020
    LIVE                = 0x0040
    SOUND_EFFECTS       = 0x0080
    NOTIFICATIONS       = 0x0100
    RINGTONE            = 0x0200
    ALERTS              = 0x0400
    EMERGENCY_ALARM     = 0x0800
    ANY_CONTEXT         = 0x0FFF



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
    NOT_SYNCED     = 0x00
    SYNC_INFO_REQ  = 0x01
    SYNCED         = 0x02
    FAILED_TO_SYNC = 0x03
    NO_PAST        = 0x04


class BIGEncryption:
    NOT_ENCRYPTED           = 0x00
    BROADCAST_CODE_REQUIRED = 0x01
    DECRYPTING              = 0x02
    BAD_CODE                = 0x03

class BAS_BATTERY_PRESENT(IntEnum):
    BATTERY_NOT_PRESENT = 0
    BATTERY_PRESENT = 1
