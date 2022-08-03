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


class AdType:
    flags = 1
    uuid16_some = 2
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
    VND16_1 = 'AA50'
    VND16_2 = 'AA51'
    VND16_3 = 'AA52'
    VND16_4 = 'AA53'
    VND16_5 = 'AA54'
    VND16_6 = 'AA55'
    VND16_7 = 'AA56'
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
