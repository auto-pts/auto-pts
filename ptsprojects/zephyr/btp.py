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

"""Wrapper around btp messages. The functions are added as needed."""

import logging
import binascii
import struct
import re
import socket
from threading import Timer, Event

import iutctl
import btpdef
from random import randint
from collections import namedtuple
from uuid import UUID
from ptsprojects.stack import get_stack

#  Global temporary objects
PASSKEY = None
GATT_SVCS = None
IUT_BD_ADDR = None
L2CAP_CHAN = []

# Address
LeAddress = namedtuple('LeAddress', 'addr_type addr')
PTS_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')

# Devices found
LeAdv = namedtuple('LeAdv', 'addr_type addr rssi flags eir')
DISCOV_RESULTS = []

# DUT's GAP current settings
GAP_CURRENT_SETTINGS = None

#  A sequence of values to verify in PTS MMI description
VERIFY_VALUES = None

CONTROLLER_INDEX = 0

CORE = {
    "gap_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_GAP),
    "gatts_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                  btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_GATT),
    "l2cap_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                  btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_L2CAP),
    "read_supp_cmds": (btpdef.BTP_SERVICE_ID_CORE,
                       btpdef.CORE_READ_SUPPORTED_COMMANDS,
                       btpdef.BTP_INDEX_NONE, ""),
    "read_supp_svcs": (btpdef.BTP_SERVICE_ID_CORE,
                       btpdef.CORE_READ_SUPPORTED_SERVICES,
                       btpdef.BTP_INDEX_NONE, ""),
}

GAP = {
    "start_adv": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_START_ADVERTISING,
                  CONTROLLER_INDEX),
    "stop_adv": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_STOP_ADVERTISING,
                 CONTROLLER_INDEX, ""),
    "conn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_CONNECT, CONTROLLER_INDEX),
    "pair": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_PAIR, CONTROLLER_INDEX),
    "unpair": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_UNPAIR, CONTROLLER_INDEX),
    "disconn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_DISCONNECT,
                CONTROLLER_INDEX),
    "set_io_cap": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_IO_CAP,
                   CONTROLLER_INDEX),
    "set_conn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_CONNECTABLE,
                 CONTROLLER_INDEX, 1),
    "set_nonconn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_CONNECTABLE,
                    CONTROLLER_INDEX, 0),
    "set_nondiscov": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, btpdef.GAP_NON_DISCOVERABLE),
    "set_gendiscov": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, btpdef.GAP_GENERAL_DISCOVERABLE),
    "set_limdiscov": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, btpdef.GAP_LIMITED_DISCOVERABLE),
    "start_discov": (btpdef.BTP_SERVICE_ID_GAP,
                     btpdef.GAP_START_DISCOVERY, CONTROLLER_INDEX),
    "stop_discov": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_STOP_DISCOVERY,
                    CONTROLLER_INDEX, ""),
    "read_ctrl_info": (btpdef.BTP_SERVICE_ID_GAP,
                       btpdef.GAP_READ_CONTROLLER_INFO,
                       CONTROLLER_INDEX, ""),
    "passkey_entry_rsp": (btpdef.BTP_SERVICE_ID_GAP,
                          btpdef.GAP_PASSKEY_ENTRY,
                          CONTROLLER_INDEX),
}

GATTS = {
    "add_svc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_SERVICE,
                CONTROLLER_INDEX),
    "start_server": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_START_SERVER,
                     CONTROLLER_INDEX, ""),
    "add_inc_svc": (btpdef.BTP_SERVICE_ID_GATT,
                    btpdef.GATT_ADD_INCLUDED_SERVICE, CONTROLLER_INDEX),
    "add_char": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_CHARACTERISTIC,
                 CONTROLLER_INDEX),
    "set_val": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_SET_VALUE,
                CONTROLLER_INDEX),
    "add_desc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_DESCRIPTOR,
                 CONTROLLER_INDEX),
    "set_enc_key_size": (btpdef.BTP_SERVICE_ID_GATT,
                         btpdef.GATT_SET_ENC_KEY_SIZE, CONTROLLER_INDEX),
    "get_attrs": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_GET_ATTRIBUTES,
                 CONTROLLER_INDEX),
    "get_attr_val": (btpdef.BTP_SERVICE_ID_GATT,
                     btpdef.GATT_GET_ATTRIBUTE_VALUE, CONTROLLER_INDEX)
}

GATTC = {
    "exchange_mtu": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_EXCHANGE_MTU,
                     CONTROLLER_INDEX),
    "disc_prim_uuid": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_PRIM_UUID,
                       CONTROLLER_INDEX),
    "find_included": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_FIND_INCLUDED,
                      CONTROLLER_INDEX),
    "disc_all_chrc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_CHRC,
                      CONTROLLER_INDEX),
    "disc_chrc_uuid": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_CHRC_UUID,
                       CONTROLLER_INDEX),
    "disc_all_desc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_DESC,
                      CONTROLLER_INDEX),
    "read": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ, CONTROLLER_INDEX),
    "read_long": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_LONG,
                  CONTROLLER_INDEX),
    "read_multiple": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_MULTIPLE,
                      CONTROLLER_INDEX),
    "write_without_rsp": (btpdef.BTP_SERVICE_ID_GATT,
                          btpdef.GATT_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "signed_write": (btpdef.BTP_SERVICE_ID_GATT,
                     btpdef.GATT_SIGNED_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "write": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE, CONTROLLER_INDEX),
    "write_long": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE_LONG,
                   CONTROLLER_INDEX),
    "cfg_notify": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_CFG_NOTIFY,
                   CONTROLLER_INDEX),
    "cfg_indicate": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_CFG_INDICATE,
                     CONTROLLER_INDEX),
}

L2CAP = {
    "read_supp_cmds": (btpdef.BTP_SERVICE_ID_L2CAP,
                       btpdef.L2CAP_READ_SUPPORTED_COMMANDS,
                       btpdef.BTP_INDEX_NONE, ""),
    "connect": (btpdef.BTP_SERVICE_ID_L2CAP, btpdef.L2CAP_CONNECT,
                CONTROLLER_INDEX),
    "disconnect": (btpdef.BTP_SERVICE_ID_L2CAP, btpdef.L2CAP_DISCONNECT,
                   CONTROLLER_INDEX),
    "send_data": (btpdef.BTP_SERVICE_ID_L2CAP, btpdef.L2CAP_SEND_DATA,
                  CONTROLLER_INDEX),
    "listen": (btpdef.BTP_SERVICE_ID_L2CAP, btpdef.L2CAP_LISTEN,
               CONTROLLER_INDEX),
}

MESH = {
    "read_supp_cmds": (btpdef.BTP_SERVICE_ID_MESH,
                       btpdef.MESH_READ_SUPPORTED_COMMANDS,
                       btpdef.BTP_INDEX_NONE, ""),
    "config_prov": (btpdef.BTP_SERVICE_ID_MESH,
                  btpdef.MESH_CONFIG_PROVISIONING,
                  CONTROLLER_INDEX),
    "prov_node": (btpdef.BTP_SERVICE_ID_MESH,
                    btpdef.MESH_PROVISION_NODE,
                    CONTROLLER_INDEX),
    "init": (btpdef.BTP_SERVICE_ID_MESH,
             btpdef.MESH_INIT,
             CONTROLLER_INDEX, ""),
    "reset": (btpdef.BTP_SERVICE_ID_MESH,
              btpdef.MESH_RESET,
              CONTROLLER_INDEX, ""),
    "input_num": (btpdef.BTP_SERVICE_ID_MESH,
                  btpdef.MESH_INPUT_NUMBER,
                  CONTROLLER_INDEX),
    "input_str": (btpdef.BTP_SERVICE_ID_MESH,
                  btpdef.MESH_INPUT_STRING,
                  CONTROLLER_INDEX),
    "iv_update_test_mode": (btpdef.BTP_SERVICE_ID_MESH,
                            btpdef.MESH_IV_UPDATE_TEST_MODE,
                            CONTROLLER_INDEX),
    "iv_update_toggle": (btpdef.BTP_SERVICE_ID_MESH,
                         btpdef.MESH_IV_UPDATE_TOGGLE,
                         CONTROLLER_INDEX, ""),
}


class Addr:
    le_public = 0
    le_random = 1


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
    broadcast     = 2 ** 0
    read          = 2 ** 1
    write_wo_resp = 2 ** 2
    write         = 2 ** 3
    nofity        = 2 ** 4
    indicate      = 2 ** 5
    auth_swrite   = 2 ** 6
    ext_prop      = 2 ** 7

    names = {
        broadcast     : "Broadcast",
        read          : "Read",
        write_wo_resp : "Write Without Response",
        write         : "Write",
        nofity        : "Notify",
        indicate      : "Indicate",
        auth_swrite   : "Authenticated Signed Writes",
        ext_prop      : "Extended Properties",
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
    read        = 2 ** 0
    write       = 2 ** 1
    read_enc    = 2 ** 2
    write_enc   = 2 ** 3
    read_authn  = 2 ** 4
    write_authn = 2 ** 5
    read_authz  = 2 ** 6
    write_authz = 2 ** 7

    names = {
        read        : "Read",
        write       : "Write",
        read_enc    : "Read with Encryption",
        write_enc   : "Write with Encryption",
        read_authn  : "Read with Authentication",
        write_authn : "Write with Authentication",
        read_authz  : "Read with Authorization",
        write_authz : "Write with Authorization"
    }

    @staticmethod
    def decode(perm):
        return decode_flag_name(perm, Perm.names)


class BTPError(Exception):
    """Exception raised if BTP error occurs.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP error has occurred.

    """
    pass


def verify_description(description):
    """A function to verify that values are in PTS MMI description

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description = description.upper()

    global VERIFY_VALUES
    logging.debug("Verifying values: %r", VERIFY_VALUES)

    if not VERIFY_VALUES:
        return True

    # VERIFY_VALUES shall not be a string: all its characters will be verified
    assert isinstance(VERIFY_VALUES, list), "VERIFY_VALUES should be a list!"

    for value in VERIFY_VALUES:
        logging.debug("Verifying: %r", value)

        value = value.upper()

        if value not in description:
            logging.debug("Verification failed, value not in description")
            return False

    logging.debug("All verifications passed")

    VERIFY_VALUES = None

    return True


def verify_multiple_read_description(description):
    """A function to verify that merged multiple read att values are in

    PTS MMI description.

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    global VERIFY_VALUES
    logging.debug("Verifying values: %r", VERIFY_VALUES)

    if not VERIFY_VALUES:
        return True

    # VERIFY_VALUES shall not be a string: all its characters will be verified
    assert isinstance(VERIFY_VALUES, list), "VERIFY_VALUES should be a list!"

    exp_mtp_read = "".join(VERIFY_VALUES)
    got_mtp_read = "".join(re.findall(r"\b[0-9A-Fa-f]+\b", description))

    if exp_mtp_read not in got_mtp_read:
        logging.debug("Verification failed, value not in description")
        return False

    logging.debug("Multiple read verifications passed")

    VERIFY_VALUES = None

    return True


def btp_hdr_check(rcv_hdr, exp_svc_id, exp_op=None):
    if rcv_hdr.svc_id != exp_svc_id:
        raise BTPError("Incorrect service ID %s in the response, expected %s!"
                       % (rcv_hdr.svc_id, exp_svc_id))

    if rcv_hdr.op == btpdef.BTP_STATUS:
        raise BTPError("Error opcode in response!")

    if exp_op and exp_op != rcv_hdr.op:
        raise BTPError(
            "Invalid opcode 0x%.2x in the response, expected 0x%.2x!" %
            (rcv_hdr.op, exp_op))


def bd_addr_convert(bdaddr):
    """ Remove colons from address and convert to lower case """
    return "".join(bdaddr.split(':')).lower()


def pts_addr_get(bd_addr=None):
    """" If address provided, convert, otherwise, use stored address. """
    if bd_addr is None:
        return PTS_BD_ADDR.addr
    return bd_addr_convert(bd_addr)


def pts_addr_type_get(bd_addr_type=None):
    """" If address type provided, return it, otherwise, use stored address. """
    if bd_addr_type is None:
        return PTS_BD_ADDR.addr_type
    return bd_addr_type


def set_pts_addr(addr, addr_type):
    global PTS_BD_ADDR
    PTS_BD_ADDR = LeAddress(addr_type=addr_type, addr=bd_addr_convert(addr))


def core_reg_svc_gap():
    logging.debug("%s", core_reg_svc_gap.__name__)

    zephyrctl = iutctl.get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gap_reg'])

    core_reg_svc_rsp_succ()


def core_reg_svc_gatts():
    logging.debug("%s", core_reg_svc_gatts.__name__)

    zephyrctl = iutctl.get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gatts_reg'])

    core_reg_svc_rsp_succ()


def core_reg_svc_l2cap():
    logging.debug("%s", core_reg_svc_l2cap.__name__)

    zephyrctl = iutctl.get_zephyr()
    zephyrctl.btp_socket.send(*CORE['l2cap_reg'])

    core_reg_svc_rsp_succ()


def core_reg_svc_rsp_succ():
    logging.debug("%s", core_reg_svc_rsp_succ.__name__)
    zephyrctl = iutctl.get_zephyr()

    expected_frame = ((btpdef.BTP_SERVICE_ID_CORE,
                       btpdef.CORE_REGISTER_SERVICE,
                       btpdef.BTP_INDEX_NONE,
                       0),
                      ('',))

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    else:
        logging.debug("response is valid")


def __gap_current_settings_update(settings):
    logging.debug("%s %r", __gap_current_settings_update.__name__, settings)
    if isinstance(settings, tuple):
        fmt = '<I'
        if len(settings[0]) != struct.calcsize(fmt):
            raise BTPError("Invalid data length")

        settings = struct.unpack(fmt, settings[0])
        settings = settings[0] # Result of unpack is always a tuple

    global GAP_CURRENT_SETTINGS
    GAP_CURRENT_SETTINGS = settings


def __gap_current_settings_is_set(bit):
    # This should maintain conformance
    if GAP_CURRENT_SETTINGS is None or not (GAP_CURRENT_SETTINGS & (1 << bit)):
        return False
    return True


def gap_adv_ind_on(ad=None, sd=None):
    logging.debug("%s %r %r", gap_adv_ind_on.__name__, ad, sd)

    if __gap_current_settings_is_set(btpdef.GAP_SETTINGS_ADVERTISING):
        return

    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    ad_ba = bytearray()
    sd_ba = bytearray()

    if ad:
        for entry in ad:
            data = binascii.unhexlify(bytearray(entry[1]))
            ad_ba.extend(chr(entry[0]))
            ad_ba.extend(chr(len(data)))
            ad_ba.extend(data)

    if sd:
        for entry in sd:
            data = binascii.unhexlify(bytearray(entry[1]))
            sd_ba.extend(chr(entry[0]))
            sd_ba.extend(chr(len(data)))
            sd_ba.extend(data)

    data_ba.extend(chr(len(ad_ba)))
    data_ba.extend(chr(len(sd_ba)))
    data_ba.extend(ad_ba)
    data_ba.extend(sd_ba)

    zephyrctl.btp_socket.send(*GAP['start_adv'], data=data_ba)

    tuple_data = gap_command_rsp_succ(btpdef.GAP_START_ADVERTISING)
    __gap_current_settings_update(tuple_data)


def gap_adv_off():
    logging.debug("%s", gap_adv_off.__name__)

    if not __gap_current_settings_is_set(btpdef.GAP_SETTINGS_ADVERTISING):
        return

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['stop_adv'])

    tuple_data = gap_command_rsp_succ(btpdef.GAP_STOP_ADVERTISING)
    __gap_current_settings_update(tuple_data)


def gap_connected_ev(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_connected_ev.__name__, bd_addr, bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_EV_DEVICE_CONNECTED)

    fmt = '<6sB'
    if len(tuple_data[0]) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    # Unpack and swap address
    _addr, _addr_type = struct.unpack(fmt, tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1])

    # Do not compare addresses here, because if PTS uses Privacy, addresses will
    # be different

    set_pts_addr(_addr, _addr_type)


def gap_conn(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_conn.__name__, bd_addr, bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(pts_addr_get(bd_addr))[::-1]

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()


def gap_rpa_conn(description):
    """Initiate connection with PTS using RPA address provided
    in MMI description. Function returns True.

    Arguments:
    description -- description provided in PTS MMI.
    """
    logging.debug("%s %s", gap_conn.__name__, description)
    zephyrctl = iutctl.get_zephyr()

    # FIXME use regex
    dsc_split = description.split(' ')
    bd_addr = dsc_split[-1]
    bd_addr_type = Addr.le_random

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(pts_addr_get(bd_addr))[::-1]

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()
    return True


def gap_disconnected_ev(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_disconnected_ev.__name__, bd_addr,
                  bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_EV_DEVICE_DISCONNECTED)

    fmt = '<6sB'
    if len(tuple_data[0]) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    # Unpack and swap address
    _addr, _addr_type = struct.unpack(fmt, tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1]).lower()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    if _addr_type != bd_addr_type or _addr != bd_addr:
        raise BTPError("Received data mismatch")


def gap_disconn(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_disconn.__name__, bd_addr, bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(pts_addr_get(bd_addr))[::-1]

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['disconn'], data=data_ba)

    gap_command_rsp_succ()


def verify_not_connected(description):
    logging.debug("%s", verify_not_connected.__name__)
    try:
        gap_connected_ev()
        return False
    except socket.timeout:
        return True


def gap_set_io_cap(io_cap):
    logging.debug("%s %r", gap_set_io_cap.__name__, io_cap)
    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_io_cap'], data=chr(io_cap))

    gap_command_rsp_succ()


def gap_pair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_pair.__name__, bd_addr, bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(pts_addr_get(bd_addr))[::-1]

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['pair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_unpair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_unpair.__name__, bd_addr, bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(pts_addr_get(bd_addr))[::-1]

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['unpair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ(btpdef.GAP_UNPAIR)


def var_store_get_passkey(description, bd_addr=None, bd_addr_type=None):
    gap_passkey_disp_ev(bd_addr, bd_addr_type, store=True)
    return var_get_passkey(description)


def var_store_get_wrong_passkey(description, bd_addr=None, bd_addr_type=None):
    gap_passkey_disp_ev(bd_addr, bd_addr_type, store=True)
    return var_get_wrong_passkey()


def var_get_passkey(description):
    return str(PASSKEY)


def var_get_wrong_passkey():
    # Passkey is in range 0-999999
    if PASSKEY > 0:
        return str(PASSKEY - 1)
    else:
        return str(PASSKEY + 1)


def gap_passkey_disp_ev(bd_addr=None, bd_addr_type=None, store=False):
    logging.debug("%s %r %r", gap_passkey_disp_ev.__name__, bd_addr,
                  bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_EV_PASSKEY_DISPLAY)

    fmt = '<B6sI'
    if len(tuple_data[0]) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    # Unpack and swap address
    _addr_type, _addr, _passkey = struct.unpack(fmt, tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1]).lower()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    if _addr_type != bd_addr_type or _addr != bd_addr:
        raise BTPError("Received data mismatch")

    logging.debug("passkey = %r", _passkey)

    if store:
        global PASSKEY
        PASSKEY = _passkey


def gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey):
    logging.debug("%s %r %r", gap_passkey_entry_rsp.__name__, bd_addr,
                  bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify(bd_addr)[::-1]

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    if isinstance(passkey, str):
        passkey = int(passkey, 32)

    passkey_ba = struct.pack('I', passkey)
    data_ba.extend(passkey_ba)

    zephyrctl.btp_socket.send(*GAP['passkey_entry_rsp'], data=data_ba)

    gap_command_rsp_succ()


def gap_passkey_entry_req_ev(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_passkey_entry_req_ev.__name__, bd_addr,
                  bd_addr_type)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_EV_PASSKEY_ENTRY_REQ)

    fmt = '<B6s'
    if len(tuple_data[0]) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    # Unpack and swap address
    _addr_type, _addr = struct.unpack(fmt, tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1]).lower()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    if _addr_type != bd_addr_type or _addr != bd_addr:
        raise BTPError("Received data mismatch")

    # Generate some passkey
    global PASSKEY
    PASSKEY = randint(0, 999999)

    gap_passkey_entry_rsp(bd_addr, bd_addr_type, PASSKEY)


def gap_set_conn():
    logging.debug("%s", gap_set_conn.__name__)

    if __gap_current_settings_is_set(btpdef.GAP_SETTINGS_CONNECTABLE):
        return

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_conn'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_nonconn():
    logging.debug("%s", gap_set_nonconn.__name__)

    if not __gap_current_settings_is_set(btpdef.GAP_SETTINGS_CONNECTABLE):
        return

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_nonconn'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_nondiscov():
    logging.debug("%s", gap_set_nondiscov.__name__)

    if not __gap_current_settings_is_set(btpdef.GAP_SETTINGS_DISCOVERABLE):
        return

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_nondiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_gendiscov():
    logging.debug("%s", gap_set_gendiscov.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_gendiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_limdiscov():
    logging.debug("%s", gap_set_limdiscov.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_limdiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def __gap_device_found_timeout(continue_flag):
    logging.debug("%s", __gap_device_found_timeout.__name__)
    continue_flag.clear()


def __gap_device_found_ev(duration):
    logging.debug("%s %r", __gap_device_found_ev.__name__, duration)

    zephyrctl = iutctl.get_zephyr()

    continue_flag = Event()
    continue_flag.set()
    t = Timer(duration, __gap_device_found_timeout, [continue_flag])
    t.start()

    while continue_flag.is_set():
        try:
            # Use 1 second socket timeout to check continue_flag every second
            tuple_hdr, tuple_data = zephyrctl.btp_socket.read(1)
        except socket.timeout:
            continue

        btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                      btpdef.GAP_EV_DEVICE_FOUND)

        fmt = '<6sBBBH'
        if len(tuple_data[0]) < struct.calcsize(fmt):
            raise BTPError("Invalid data length")

        _addr, _addr_type, _rssi, _flags, _len = struct.unpack_from(fmt,
                                                                 tuple_data[0])
        _eir = tuple_data[0][struct.calcsize(fmt):]

        if len(_eir) != _len:
            raise BTPError("Invalid data length")

        _addr = binascii.hexlify(_addr[::-1]).lower()

        logging.debug("found %r type %r", _addr, _addr_type)

        global DISCOV_RESULTS
        DISCOV_RESULTS.append(LeAdv(_addr_type, _addr, _rssi, _flags, _eir))


def gap_start_discov(transport='le', type='active', mode='general', duration=10):
    """GAP Start Discovery function.

    duration - Discovery duration in seconds (10 by default).
               After this period of time discovery will be stopped.

    Possible options (key: <values>):

    transport: <le, bredr>
    type: <active, passive>
    mode: <general, limited, observe>

    """
    logging.debug("%s", gap_start_discov.__name__)

    zephyrctl = iutctl.get_zephyr()

    flags = 0

    if transport == "le":
        flags |= btpdef.GAP_DISCOVERY_FLAG_LE
    else:
        flags |= btpdef.GAP_DISCOVERY_FLAG_BREDR

    if type == "active":
        flags |= btpdef.GAP_DISCOVERY_FLAG_LE_ACTIVE_SCAN

    if mode == "limited":
        flags |= btpdef.GAP_DISCOVERY_FLAG_LIMITED
    elif mode == "observe":
        flags |= btpdef.GAP_DISCOVERY_FLAG_LE_OBSERVE

    zephyrctl.btp_socket.send(*GAP['start_discov'], data=chr(flags))

    gap_command_rsp_succ()

    # Make sure there are no previous results
    global DISCOV_RESULTS
    del DISCOV_RESULTS[:]

    __gap_device_found_ev(duration)

    # Stop discovery if expired
    __gap_stop_discov()


def check_discov_results(description, addr_type=None, addr=None,
                         discovered=True, eir=None):

    addr = pts_addr_get(addr)
    addr_type = pts_addr_type_get(addr_type)

    logging.debug("%s %r %r %r %r", check_discov_results.__name__, addr_type,
                  addr, discovered, eir)

    found = False

    global DISCOV_RESULTS

    while len(DISCOV_RESULTS):
        result = DISCOV_RESULTS.pop()

        if addr_type != result.addr_type:
            continue
        if addr != result.addr:
            continue
        if eir and eir != result.eir:
            continue

        found = True
        break

    # Cleanup
    del DISCOV_RESULTS[:]

    if discovered == found:
        return True

    return False


def discover_and_verify(description, transport='le', type='active',
                        mode='general', duration=10, addr=None, addr_type=None):
    """Verify discovery results

    This function verifies if the advertisement has been received and
    optionally verifies the presence of specific eir data in received
    advertisement

    Returns True if verification is successful, False if not.

    description -- MMI description
    """
    gap_start_discov(transport, type, mode, duration)

    return check_discov_results(addr_type, addr)


def __gap_stop_discov():
    logging.debug("%s", __gap_stop_discov.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['stop_discov'])

    gap_command_rsp_succ()


def wrap(func, *args):
    """Call function with given arguments

    If arguments list item is a callable it will be invoked and replaced in the
    list with its own return value.

    """
    _args = []
    for x in args:
        if callable(x):
            x = x()
        _args.append(x)
    func(*_args)


def get_stored_bd_addr():
    return str(IUT_BD_ADDR)


def gap_read_ctrl_info():
    logging.debug("%s", gap_read_ctrl_info.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send(*GAP['read_ctrl_info'])

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_READ_CONTROLLER_INFO)

    fmt = '<6sII3s249s11s'
    if len(tuple_data[0]) < struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr, _supp_set, _curr_set, _cod, _name, _name_sh = struct.unpack_from(fmt,
                                                                tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1]).lower()

    global IUT_BD_ADDR
    IUT_BD_ADDR = _addr
    logging.debug("IUT address %r", IUT_BD_ADDR)

    __gap_current_settings_update(_curr_set)


def gap_identity_resolved_ev():
    logging.debug("%s", gap_identity_resolved_ev.__name__)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP,
                  btpdef.GAP_EV_IDENTITY_RESOLVED)

    fmt = '<B6sB6s'
    if len(tuple_data[0]) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _id_addr_t, _id_addr = struct.unpack_from('<B6sB6s',
                                                              tuple_data[0])
    # Convert addresses to lower case
    _addr = binascii.hexlify(_addr[::-1]).lower()
    _id_addr = binascii.hexlify(_id_addr[::-1]).lower()

    if _addr_t != pts_addr_type_get() or _addr != pts_addr_get():
        raise BTPError("Received data mismatch")

    # Update RPA with Identity Address
    set_pts_addr(_id_addr, _id_addr_t)


def gap_command_rsp_succ(op=None):
    logging.debug("%s", gap_command_rsp_succ.__name__)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GAP, op)

    return tuple_data


def gatts_add_svc(svc_type, uuid):
    logging.debug("%s %r %r", gatts_add_svc.__name__, svc_type, uuid)

    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(chr(svc_type))
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_svc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_inc_svc(hdl):
    logging.debug("%s %r", gatts_add_inc_svc.__name__, hdl)

    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTS['add_inc_svc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_char(hdl, prop, perm, uuid):
    logging.debug("%s %r %r %r %r", gatts_add_char.__name__, hdl, prop, perm,
                  uuid)

    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(prop))
    data_ba.extend(chr(perm))
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_char'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_set_val(hdl, val):
    logging.debug("%s %r %r ", gatts_set_val.__name__, hdl, val)

    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTS['set_val'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_desc(hdl, perm, uuid):
    logging.debug("%s %r %r %r", gatts_add_desc.__name__, hdl, perm, uuid)

    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(perm))
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_desc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_start_server():
    logging.debug("%s", gatts_start_server.__name__)

    zephyrctl = iutctl.get_zephyr()
    zephyrctl.btp_socket.send(*GATTS['start_server'])

    gatt_command_rsp_succ()


def gatts_set_enc_key_size(hdl, enc_key_size):
    logging.debug("%s %r %r", gatts_set_enc_key_size.__name__,
                  hdl, enc_key_size)

    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(enc_key_size))

    zephyrctl.btp_socket.send(*GATTS['set_enc_key_size'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_dec_attr_value_changed_ev_data(frame):
    """Decodes BTP Attribute Value Changed Event data

    Event data frame format
    0             16            32
    +--------------+-------------+------+
    | Attribute ID | Data Length | Data |
    +--------------+-------------+------+

    """
    hdr = '<HH'
    hdr_len = struct.calcsize(hdr)

    (handle, data_len) = struct.unpack_from(hdr, frame)
    data = struct.unpack_from('%ds' % data_len, frame, hdr_len)

    return handle, data


def gatts_attr_value_changed_ev():
    logging.debug("%s", gatts_attr_value_changed_ev.__name__)

    zephyrctl = iutctl.get_zephyr()

    (tuple_hdr, tuple_data) = zephyrctl.btp_socket.read()

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_EV_ATTR_VALUE_CHANGED)

    (handle, data) = gatts_dec_attr_value_changed_ev_data(tuple_data[0])
    logging.debug("%s %r %r", gatts_attr_value_changed_ev.__name__, handle, data)

    return handle, data


def gatts_verify_write_success(description):
    """
    This verifies if PTS initiated write operation succeeded
    """
    logging.debug("%s", gatts_verify_write_success.__name__)

    # If write is successful, Attribute Value Changed Event will be received
    try:
        (handle, value) = gatts_attr_value_changed_ev()
        logging.debug("%s Handle %r. Value %r has been successfully written",
                      gatts_verify_write_success.__name__, handle, value)
        return True
    except:
        logging.debug("%s PTS failed to write attribute value",
                      gatts_verify_write_success.__name__)
        return False


def gatts_verify_write_fail(description):
    return not gatts_verify_write_success(description)


def btp2uuid(uuid_len, uu):
    if uuid_len == 2:
        (uu,) = struct.unpack("H", uu)
        return hex(uu)
    else:
        return UUID(bytes_le=uu).urn[9:]


def dec_gatts_get_attrs_rp(data, data_len):
    logging.debug("%s %r %r", dec_gatts_get_attrs_rp.__name__, data, data_len)

    hdr = '<B'
    hdr_len = struct.calcsize(hdr)
    data_len = data_len - hdr_len

    (attr_count, attrs) = struct.unpack(hdr + '%ds' % data_len, data)

    attributes = []

    while (attr_count - 1) >= 0:
        hdr = '<HBB'
        hdr_len = struct.calcsize(hdr)
        data_len = data_len - hdr_len

        (handle, permission, type_uuid_len, frag) = \
            struct.unpack(hdr + '%ds' % data_len, attrs)

        data_len = data_len - type_uuid_len

        (type_uuid, attrs) = struct.unpack('%ds%ds' % (type_uuid_len,
                                                       data_len), frag)

        type_uuid = btp2uuid(type_uuid_len, type_uuid)

        attributes.append((handle, permission, type_uuid))

        attr_count = attr_count - 1

        logging.debug("handle %r perm %r type_uuid %r", handle, permission,
                      type_uuid)

    return attributes


def gatts_get_attrs(start_handle=0x0001, end_handle=0xffff, type_uuid=None):
    logging.debug("%s %r %r %r", gatts_get_attrs.__name__, start_handle,
                  end_handle, type_uuid)

    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    if type(start_handle) is str:
        start_handle = int(start_handle, 16)

    start_hdl_ba = struct.pack('H', start_handle)
    data_ba.extend(start_hdl_ba)

    if type(end_handle) is str:
        end_handle = int(end_handle, 16)

    end_hdl_ba = struct.pack('H', end_handle)
    data_ba.extend(end_hdl_ba)

    if type_uuid:
        uuid_ba = binascii.unhexlify(type_uuid.translate(None, "-"))[::-1]
        data_ba.extend(chr(len(uuid_ba)))
        data_ba.extend(uuid_ba)
    else:
        data_ba.extend(chr(0))

    zephyrctl.btp_socket.send(*GATTS['get_attrs'], data=data_ba)

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_GET_ATTRIBUTES)

    return dec_gatts_get_attrs_rp(tuple_data[0], tuple_hdr.data_len)


def gatts_get_attr_val(handle):
    logging.debug("%s %r", gatts_get_attr_val.__name__, handle)

    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    if type(handle) is str:
        handle = int(handle, 16)

    hdl_ba = struct.pack('H', handle)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTS['get_attr_val'], data=data_ba)

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_GET_ATTRIBUTE_VALUE)

    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)
    data_len = tuple_hdr.data_len - hdr_len

    return struct.unpack(hdr + '%ds' % data_len, tuple_data[0])


def gattc_exchange_mtu(bd_addr_type, bd_addr):
    logging.debug("%s %r %r", gattc_exchange_mtu.__name__, bd_addr_type,
                  bd_addr)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GATTC['exchange_mtu'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_disc_prim_uuid(bd_addr_type, bd_addr, uuid):
    logging.debug("%s %r %r %r", gattc_disc_prim_uuid.__name__, bd_addr_type,
                  bd_addr, uuid)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_prim_uuid'], data=data_ba)


def gattc_find_included(bd_addr_type, bd_addr, start_hdl, stop_hdl):
    logging.debug("%s %r %r %r %r", gattc_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    zephyrctl = iutctl.get_zephyr()

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['find_included'], data=data_ba)


def gattc_disc_all_chrc_find_attrs_rsp(exp_chars, store_attrs=False):
    """Parse and find requested characteristics from rsp

    ATTRIBUTE FORMAT (CHARACTERISTIC) - (handle, val handle, props, uuid)

    """
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r",
                  gattc_disc_all_chrc_find_attrs_rsp.__name__, tuple_hdr,
                  tuple_data)
    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_ALL_CHRC)

    chars_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")

    for char in chars_tuple:
        for exp_char in exp_chars:
            # Check if option expected attribute parameters match
            char_uuid = binascii.hexlify(char[3][0][::-1])
            if ((exp_char[0] and exp_char[0] != char[0]) or
                    (exp_char[1] and exp_char[1] != char[1]) or
                    (exp_char[2] and exp_char[2] != char[2]) or
                    (exp_char[3] and exp_char[3] != char_uuid)):

                logging.debug("gatt char not matched = %r != %r", char,
                              exp_char)

                continue

            logging.debug("gatt char matched = %r == %r", char, exp_char)

            if store_attrs:
                global GATT_CHARS

                GATT_CHARS = []

                GATT_CHARS.append(char)


def gattc_disc_all_chrc(bd_addr_type, bd_addr, start_hdl, stop_hdl, svc=None):
    logging.debug("%s %r %r %r %r %r", gattc_disc_all_chrc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, svc)
    zephyrctl = iutctl.get_zephyr()

    if svc:
        svc_nb = svc[1]
        for s in GATT_SVCS:
            if not ((svc[0][0] and svc[0][0] != s[0]) and
                    (svc[0][1] and svc[0][1] != s[1]) and
                    (svc[0][2] and svc[0][2] != s[2])):

                    # To take n-th service
                    svc_nb -= 1
                    if svc_nb != 0:
                        continue

                    start_hdl = s[0]
                    stop_hdl = s[1]

                    logging.debug("Got requested service!")

                    break

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_all_chrc'], data=data_ba)


def gattc_disc_chrc_uuid(bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gattc_disc_chrc_uuid.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid)
    zephyrctl = iutctl.get_zephyr()

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    if "-" in uuid:
        uuid = uuid.replace("-", "")
    if uuid.startswith("0x"):
        uuid = uuid.replace("0x", "")
    uuid_ba = binascii.unhexlify(uuid)[::-1]

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_chrc_uuid'], data=data_ba)


def gattc_disc_all_desc(bd_addr_type, bd_addr, start_hdl, stop_hdl):
    logging.debug("%s %r %r %r %r", gattc_disc_all_desc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    zephyrctl = iutctl.get_zephyr()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_all_desc'], data=data_ba)


def gattc_read_char_val(bd_addr_type, bd_addr, char):
    logging.debug("%s %r %r %r", gattc_read_char_val.__name__, bd_addr_type,
                  bd_addr, char)

    char_nb = char[1]
    for c in GATT_CHARS:
        if not ((char[0][0] and char[0][0] != c[0]) and
                (char[0][1] and char[0][1] != c[1]) and
                (char[0][2] and char[0][2] != c[2])
                (char[0][3] and char[0][3] != c[3])):

                # To take n-th service
                char_nb -= 1
                if char_nb != 0:
                    continue

                logging.debug("Got requested char, val handle = %r!", c[1])

                gattc_read(bd_addr_type, bd_addr, c[1])

                break


def gattc_read(bd_addr_type, bd_addr, hdl):
    logging.debug("%s %r %r %r", gattc_read.__name__, bd_addr_type, bd_addr,
                  hdl)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    if type(hdl) is str:
        hdl = int(hdl, 16)
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['read'], data=data_ba)


def gattc_read_long(bd_addr_type, bd_addr, hdl, off, modif_off=None):
    logging.debug("%s %r %r %r %r %r", gattc_read_long.__name__, bd_addr_type,
                  bd_addr, hdl, off, modif_off)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    if type(off) is str:
        off = int(off, 16)
    if modif_off:
        off += modif_off
    if type(hdl) is str:
        hdl = int(hdl, 16)

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)

    zephyrctl.btp_socket.send(*GATTC['read_long'], data=data_ba)


def gattc_read_multiple(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gattc_read_multiple.__name__, bd_addr_type,
                  bd_addr, hdls)
    zephyrctl = iutctl.get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdls_j = ''.join(hdl for hdl in hdls)
    hdls_byte_table = [hdls_j[i:i + 2] for i in range(0, len(hdls_j), 2)]
    hdls_swp = ''.join([c[1] + c[0] for c in zip(hdls_byte_table[::2],
                                                 hdls_byte_table[1::2])])
    hdls_ba = binascii.unhexlify(bytearray(hdls_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(hdls)))
    data_ba.extend(hdls_ba)

    zephyrctl.btp_socket.send(*GATTC['read_multiple'], data=data_ba)


def gattc_write_without_rsp(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_without_rsp.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write_without_rsp'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_signed_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_signed_write.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['signed_write'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write.__name__, bd_addr_type,
                  bd_addr, hdl, val, val_mtp)
    zephyrctl = iutctl.get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write'], data=data_ba)


def gattc_write_long(bd_addr_type, bd_addr, hdl, off, val, length=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_long.__name__,
                  bd_addr_type, hdl, off, val, length)

    if type(hdl) is str:
        hdl = int(hdl, 16)  # convert string in hex format to int

    if type(off) is str:
        off = int(off, 16)

    if length:
        val *= int(length)

    zephyrctl = iutctl.get_zephyr()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write_long'], data=data_ba)


def gattc_cfg_notify(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gattc_cfg_notify.__name__, bd_addr_type,
                  bd_addr, enable, ccc_hdl)

    if type(ccc_hdl) is str:
        ccc_hdl = int(ccc_hdl, 16)

    zephyrctl = iutctl.get_zephyr()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable))
    data_ba.extend(ccc_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['cfg_notify'], data=data_ba)

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_cfg_notify.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_CFG_NOTIFY)


def gattc_cfg_indicate(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gattc_cfg_indicate.__name__,
                  bd_addr_type, bd_addr, enable, ccc_hdl)

    if type(ccc_hdl) is str:
        ccc_hdl = int(ccc_hdl, 16)

    zephyrctl = iutctl.get_zephyr()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable))
    data_ba.extend(ccc_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['cfg_indicate'], data=data_ba)

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_cfg_indicate.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_CFG_INDICATE)


def gattc_notification_ev(bd_addr, bd_addr_type, ev_type):
    logging.debug("%s %r %r %r", gattc_notification_ev.__name__, bd_addr,
                  bd_addr_type, ev_type)
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_EV_NOTIFICATION)

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(ev_type))

    if tuple_data[0][0:len(data_ba)] != data_ba:
        raise BTPError("Error in notification event data")


def gatt_command_rsp_succ():
    logging.debug("%s", gatt_command_rsp_succ.__name__)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT)


def gatt_dec_svc_attr(data):
    """Decodes Service Attribute data from Discovery Response data.

    BTP Single Service Attribute
    0             16           32            40
    +--------------+------------+-------------+------+
    | Start Handle | End Handle | UUID Length | UUID |
    +--------------+------------+-------------+------+

    """
    hdr = '<HHB'
    hdr_len = struct.calcsize(hdr)

    start_hdl, end_hdl, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (start_hdl, end_hdl, uuid), hdr_len + uuid_len


def gatt_dec_incl_attr(data):
    """Decodes Included Service Attribute data from Discovery Response data.

    BTP Single Included Service Attribute
    0                16
    +-----------------+-------------------+
    | Included Handle | Service Attribute |
    +-----------------+-------------------+

    """
    hdr = '<H'
    hdr_len = struct.calcsize(hdr)

    incl_hdl = struct.unpack_from(hdr, data)
    svc, svc_len = gatt_dec_svc_attr(data[hdr_len:])

    return (incl_hdl, svc), hdr_len + svc_len


def gatt_dec_chrc_attr(data):
    """Decodes Characteristic Attribute data from Discovery Response data.

    BTP Single Characteristic Attribute
    0       16             32           40            48
    +--------+--------------+------------+-------------+------+
    | Handle | Value Handle | Properties | UUID Length | UUID |
    +--------+--------------+------------+-------------+------+

    """
    hdr = '<HHBB'
    hdr_len = struct.calcsize(hdr)

    chrc_hdl, val_hdl, props, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (chrc_hdl, val_hdl, props, uuid), hdr_len + uuid_len


def gatt_dec_desc_attr(data):
    """Decodes Descriptor Attribute data from Discovery Response data.

    BTP Single Descriptor Attribute
    0       16            24
    +--------+-------------+------+
    | Handle | UUID Length | UUID |
    +--------+-------------+------+

    """
    hdr = '<HB'
    hdr_len = struct.calcsize(hdr)

    hdl, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (hdl, uuid), hdr_len + uuid_len


def gatt_dec_disc_rsp(data, attr_type):
    """Decodes Discovery Response data.

    BTP Discovery Response frame format
    0                  8
    +------------------+------------+
    | Attributes Count | Attributes |
    +------------------+------------+

    """
    attrs_len = len(data) - 1
    attr_cnt, attrs = struct.unpack('B%ds' % attrs_len, data)

    attrs_list = []
    offset = 0

    for x in range(attr_cnt):
        if attr_type == "service":
            attr, attr_len = gatt_dec_svc_attr(attrs[offset:])
        elif attr_type == "include":
            attr, attr_len = gatt_dec_incl_attr(attrs[offset:])
        elif attr_type == "characteristic":
            attr, attr_len = gatt_dec_chrc_attr(attrs[offset:])
        else:  # descriptor
            attr, attr_len = gatt_dec_desc_attr(attrs[offset:])

        attrs_list.append(attr)
        offset += attr_len

    return tuple(attrs_list)


def gatt_dec_read_rsp(data):
    """Decodes Read Response data.

    BTP Read Response frame format
    0              8            24
    +--------------+-------------+------+
    | ATT Response | Data Length | Data |
    +--------------+-------------+------+

    """
    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)

    att_rsp, val_len = struct.unpack_from(hdr, data)
    val = struct.unpack_from('%ds' % val_len, data, hdr_len)

    return att_rsp, val


def gatt_dec_write_rsp(data):
    """Decodes Write Response data.

    BTP Write Response frame format
    0              8
    +--------------+
    | ATT Response |
    +--------------+

    """
    return ord(data)


def gattc_disc_prim_uuid_find_attrs_rsp(exp_svcs, store_attrs=False):
    """Parse and find requested services from rsp

    ATTRIBUTE FORMAT (PRIMARY SERVICE) - (start handle, end handle, uuid)

    """
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r",
                  gattc_disc_prim_uuid_find_attrs_rsp.__name__, tuple_hdr,
                  tuple_data)
    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_PRIM_UUID)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")

    for svc in svcs_tuple:
        for exp_svc in exp_svcs:
            # Check if option expected attribute parameters match
            svc_uuid = binascii.hexlify(svc[2][0][::-1])
            if ((exp_svc[0] and exp_svc[0] != svc[0]) or
                    (exp_svc[1] and exp_svc[1] != svc[1]) or
                    (exp_svc[2] and exp_svc[2] != svc_uuid)):

                logging.debug("gatt svc not matched = %r != %r", svc, exp_svc)

                continue

            logging.debug("gatt svc matched = %r == %r", svc, exp_svc)

            if store_attrs:
                global GATT_SVCS

                GATT_SVCS = []

                GATT_SVCS.append(svc)


def gattc_disc_prim_uuid_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_prim_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_PRIM_UUID)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_prim_uuid_rsp.__name__, svcs_tuple)

    if store_rsp:
        global VERIFY_VALUES

        VERIFY_VALUES = []

        for svc in svcs_tuple:
            start_handle = "%04X" % (svc[0],)
            end_handle = "%04X" % (svc[1],)

            uuid_ba = svc[2][0]
            uuid = binascii.hexlify(uuid_ba[::-1]).upper()

            # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
            if len(uuid) > 4:
                uuid = "-".join([uuid[i:i+4] for i in range(0, len(uuid), 4)])

            VERIFY_VALUES.append(start_handle)
            VERIFY_VALUES.append(end_handle)

            # avoid repeated service uuid, it should be verified only once, for
            # example:
            # gattc_disc_prim_uuid_rsp ((1, 3, ('\xc9N',)),
            # (48, 50, ('\xc9N',)), (64, 66, ('\xc9N',)),
            # (80, 82, ('\xc9N',)), (144, 150, ('\xc9N',)))
            if uuid not in VERIFY_VALUES:
                VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_find_included_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_find_included_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_FIND_INCLUDED)

    incls_tuple = gatt_dec_disc_rsp(tuple_data[0], "include")
    logging.debug("%s %r", gattc_find_included_rsp.__name__, incls_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for incl in incls_tuple:
            att_handle = "%04X" % (incl[0][0],)
            inc_svc_handle = "%04X" % (incl[1][0],)
            end_grp_handle = "%04X" % (incl[1][1],)

            uuid_ba = incl[1][2][0]
            uuid = binascii.hexlify(uuid_ba[::-1]).upper()

            VERIFY_VALUES.append(att_handle)
            VERIFY_VALUES.append(inc_svc_handle)
            VERIFY_VALUES.append(end_grp_handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_disc_all_chrc_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_chrc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_ALL_CHRC)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_all_chrc_rsp.__name__, chrcs_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for chrc in chrcs_tuple:

            handle = "%04X" % (chrc[0],)
            VERIFY_VALUES.append(handle)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_disc_chrc_uuid_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_chrc_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_CHRC_UUID)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_chrc_uuid_rsp.__name__, chrcs_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for chrc in chrcs_tuple:
            handle = "%04X" % (chrc[1],)

            uuid_ba = chrc[3][0]
            uuid = binascii.hexlify(uuid_ba[::-1]).upper()

            # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
            if len(uuid) > 4:
                uuid = "-".join([uuid[i:i+4] for i in range(0, len(uuid), 4)])

            VERIFY_VALUES.append(handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_disc_all_desc_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_desc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_DISC_ALL_DESC)

    descs_tuple = gatt_dec_disc_rsp(tuple_data[0], "descriptor")
    logging.debug("%s %r", gattc_disc_all_desc_rsp.__name__, descs_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for desc in descs_tuple:
            handle = "%04X" % (desc[0],)
            uuid_ba = desc[1][0]
            uuid = binascii.hexlify(uuid_ba[::-1]).upper()
            VERIFY_VALUES.append(handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


att_rsp_str = {0:   "No error",
               1:   "Invalid handle error",
               2:   "read is not permitted error",
               3:   "write is not permitted error",
               5:   "authentication error",
               7:   "Invalid offset error",
               8:   "authorization error",
               12:  "encryption key size error",
               13:  "Invalid attribute value length error",
               128: "Application error",
               }


def gattc_read_rsp(store_rsp=False, store_val=False, timeout=None):
    zephyrctl = iutctl.get_zephyr()

    if timeout:
        tuple_hdr, tuple_data = zephyrctl.btp_socket.read(timeout)
    else:
        tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_rsp.__name__, rsp, value)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            VERIFY_VALUES.append((binascii.hexlify(value[0])).upper())


def gattc_read_long_rsp(store_rsp=False, store_val=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_long_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_LONG)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_long_rsp.__name__, rsp, value)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            VERIFY_VALUES.append((binascii.hexlify(value[0])).upper())


def gattc_read_multiple_rsp(store_val=False, store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_multiple_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_READ_MULTIPLE)

    rsp, values = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_multiple_rsp.__name__, rsp, values)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            VERIFY_VALUES.append((binascii.hexlify(values[0])).upper())


def gattc_write_rsp(store_rsp=False, timeout=None):
    zephyrctl = iutctl.get_zephyr()

    if timeout:
        tuple_hdr, tuple_data = zephyrctl.btp_socket.read(timeout)
    else:
        tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_rsp.__name__, rsp)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(att_rsp_str[rsp])


def gattc_write_long_rsp(store_rsp=False):
    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_long_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT,
                  btpdef.GATT_WRITE_LONG)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_long_rsp.__name__, rsp)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(att_rsp_str[rsp])


def l2cap_command_rsp_succ(op=None):
    logging.debug("%s", l2cap_command_rsp_succ.__name__)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_L2CAP, op)


def l2cap_conn(bd_addr, bd_addr_type, psm):
    logging.debug("%s %r %r %r", l2cap_conn.__name__, bd_addr, bd_addr_type,
                  psm)

    zephyrctl = iutctl.get_zephyr()

    if type(psm) is str:
        psm = int(psm, 16)

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba = bytearray(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))

    zephyrctl.btp_socket.send(*L2CAP['connect'], data=data_ba)


l2cap_result_str = {0:  "Connection successful",
                    2:  "LE_PSM not supported",
                    4:  "Insufficient Resources",
                    5:  "insufficient authentication",
                    6:  "insufficient authorization",
                    7:  "insufficient encryption key size",
                    8:  "insufficient encryption",
                    9:  "Invalid Source CID",
                    10: "Source CID already allocated",
                    }


def l2cap_conn_rsp():
    logging.debug("%s", l2cap_conn_rsp.__name__)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_L2CAP, btpdef.L2CAP_CONNECT)

    chan_id = struct.unpack_from('<B', tuple_data[0])[0]

    global L2CAP_CHAN
    L2CAP_CHAN.append(chan_id)

    logging.debug("new L2CAP channel: id %r", chan_id)


def l2cap_disconn(chan_id):
    logging.debug("%s %r", l2cap_disconn.__name__, chan_id)

    zephyrctl = iutctl.get_zephyr()

    global L2CAP_CHAN
    try:
        idx = L2CAP_CHAN.index(chan_id)
    except ValueError:
        raise BTPError("Channel with given chan_id: %r does not exists" %
                       (chan_id))

    chan_id = L2CAP_CHAN[idx]

    data_ba = bytearray(chr(chan_id))

    zephyrctl.btp_socket.send(*L2CAP['disconnect'], data=data_ba)

    l2cap_command_rsp_succ(btpdef.L2CAP_DISCONNECT)


def l2cap_send_data(chan_id, val, val_mtp=None):
    logging.debug("%s %r %r %r", l2cap_send_data.__name__, chan_id, val,
                  val_mtp)

    zephyrctl = iutctl.get_zephyr()

    if val_mtp:
        val *= int(val_mtp)

    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray(chr(chan_id))
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*L2CAP['send_data'], data=data_ba)

    l2cap_command_rsp_succ(btpdef.L2CAP_SEND_DATA)


def l2cap_listen(psm, transport):
    logging.debug("%s %r %r", l2cap_le_listen.__name__, psm, transport)

    zephyrctl = iutctl.get_zephyr()

    if type(psm) is str:
        psm = int(psm, 16)

    data_ba = bytearray(struct.pack('H', psm))
    data_ba.extend(struct.pack('B', transport))

    zephyrctl.btp_socket.send(*L2CAP['listen'], data=data_ba)

    l2cap_command_rsp_succ(btpdef.L2CAP_LISTEN)

def l2cap_le_listen(psm):
    l2cap_listen(psm, btpdef.L2CAP_TRANSPORT_LE)


def l2cap_connected_ev():
    logging.debug("%s", l2cap_connected_ev.__name__)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_L2CAP,
                  btpdef.L2CAP_EV_CONNECTED)

    chan_id, psm, bd_addr_type, bd_addr = struct.unpack_from('<BHB6s',
                                                             tuple_data[0])
    logging.debug("New L2CAP connection ID:%r on PSM:%r, Addr %r Type %r",
                  chan_id, psm, bd_addr, bd_addr_type)

    global L2CAP_CHAN

    # Append incoming connection only
    if chan_id not in L2CAP_CHAN:
        L2CAP_CHAN.append(chan_id)


def l2cap_disconnected_ev(exp_chan_id, store=False):
    logging.debug("%s %r", l2cap_disconnected_ev.__name__, exp_chan_id)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_L2CAP,
                  btpdef.L2CAP_EV_DISCONNECTED)

    res, chan_id, psm, bd_addr_type, bd_addr = struct.unpack_from('<HBHB6s',
                                                                  tuple_data[0])

    global L2CAP_CHAN
    L2CAP_CHAN.remove(chan_id)

    logging.debug("L2CAP channel disconnected: id %r", chan_id)

    if chan_id != exp_chan_id:
        raise BTPError("Error in L2CAP disconnected event data")

    if store:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(l2cap_result_str[res])

def l2cap_data_rcv_ev(chan_id=None, store=False):
    logging.debug("%s %r %r", l2cap_data_rcv_ev.__name__, chan_id, store)

    zephyrctl = iutctl.get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_L2CAP,
                  btpdef.L2CAP_EV_DATA_RECEIVED)

    data_hdr = '<BH'
    data_hdr_len = struct.calcsize(data_hdr)

    rcv_chan_id, data_len = struct.unpack_from(data_hdr, tuple_data[0])
    data = binascii.hexlify(struct.unpack_from('%ds' % data_len, tuple_data[0],
                                               data_hdr_len)[0])

    if chan_id and chan_id != rcv_chan_id:
        raise BTPError("Error in L2CAP data received event data")

    if store:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(data)


def gap_connected_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_connected_ev_.__name__, data)

    hdr_fmt = '<6sB'
    hdr_len = struct.calcsize(hdr_fmt)

    addr, addr_type = struct.unpack_from(hdr_fmt, data)
    addr = binascii.hexlify(addr[::-1])

    gap.connected.data = (addr, addr_type)

    set_pts_addr(addr, addr_type)


def gap_disconnected_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_disconnected_ev_.__name__, data)

    gap.connected.data = None


GAP_EV = {
    btpdef.GAP_EV_DEVICE_CONNECTED: gap_connected_ev_,
    btpdef.GAP_EV_DEVICE_DISCONNECTED: gap_disconnected_ev_,
}


def mesh_config_prov(uuid, static_auth, output_size, output_actions, input_size,
              input_actions):
    logging.debug("%s %r %r %r %r %r %r", mesh_config_prov.__name__, uuid,
                  static_auth, output_size, output_actions, input_size,
                  input_actions)

    zephyrctl = iutctl.get_zephyr()

    uuid = binascii.unhexlify(uuid)
    static_auth = binascii.unhexlify(static_auth)

    data = bytearray(struct.pack("<16s16sBHBH", uuid, static_auth, output_size,
                                 output_actions, input_size, input_actions))

    zephyrctl.btp_socket.send_wait_rsp(*MESH['config_prov'], data=data)


def mesh_prov_node():
    logging.debug("%s", mesh_config_prov.__name__)

    stack = get_stack()

    net_key = binascii.unhexlify(stack.mesh.net_key)
    dev_key = binascii.unhexlify(stack.mesh.dev_key)

    data = bytearray(struct.pack("<16sHBIIH16s", net_key, stack.mesh.net_key_idx,
                                 stack.mesh.flags, stack.mesh.iv_idx,
                                 stack.mesh.seq_num, stack.mesh.addr, dev_key))

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send_wait_rsp(*MESH['prov_node'], data=data)


def mesh_init():
    logging.debug("%s", mesh_init.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send_wait_rsp(*MESH['init'])


def mesh_reset():
    logging.debug("%s", mesh_reset.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send_wait_rsp(*MESH['reset'])

    stack = get_stack()

    stack.mesh.is_provisioned.data = False


def mesh_input_number(number):
    logging.debug("%s %r", mesh_input_number.__name__, number)

    zephyrctl = iutctl.get_zephyr()

    if type(number) is str:
        number = int(number)

    data = bytearray(struct.pack("<I", number))

    zephyrctl.btp_socket.send_wait_rsp(*MESH['input_num'], data=data)


def mesh_input_string(string):
    logging.debug("%s %s", mesh_input_string.__name__, string)

    zephyrctl = iutctl.get_zephyr()

    data = bytearray(string)

    zephyrctl.btp_socket.send_wait_rsp(*MESH['input_str'], data=data)


def mesh_iv_update_test_mode(enable):
    logging.debug("%s", mesh_iv_update_test_mode.__name__)

    zephyrctl = iutctl.get_zephyr()

    if enable:
        data = bytearray(struct.pack("<B", 0x01))
    else:
        data = bytearray(struct.pack("<B", 0x00))

    zephyrctl.btp_socket.send_wait_rsp(*MESH['iv_update_test_mode'], data=data)

    stack = get_stack()
    stack.mesh.is_iv_test_mode_enabled.data = True


def mesh_iv_update_toggle():
    logging.debug("%s", mesh_iv_update_toggle.__name__)

    zephyrctl = iutctl.get_zephyr()

    zephyrctl.btp_socket.send_wait_rsp(*MESH['iv_update_toggle'])


def mesh_out_number_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_out_number_action_ev.__name__, data)

    action, number = struct.unpack_from('<HI', data)

    mesh.oob_action.data = action
    mesh.oob_data.data = number


def mesh_out_string_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_out_string_action_ev.__name__, data)

    hdr_fmt = '<B'
    hdr_len = struct.calcsize(hdr_fmt)

    (str_len,) = struct.unpack_from(hdr_fmt, data)
    (string,) = struct.unpack_from('<%ds' % str_len, data, hdr_len)

    mesh.oob_data.data = string


def mesh_in_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_in_action_ev.__name__, data)

    action, size = struct.unpack('<HB', data)


def mesh_provisioned_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_provisioned_ev.__name__, data)

    mesh.is_provisioned.data = True


def mesh_prov_link_open_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_open_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('open', bearer)


def mesh_prov_link_closed_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_closed_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('closed', bearer)


MESH_EV = {
    btpdef.MESH_EV_OUT_NUMBER_ACTION: mesh_out_number_action_ev,
    btpdef.MESH_EV_OUT_STRING_ACTION: mesh_out_string_action_ev,
    btpdef.MESH_EV_IN_ACTION: mesh_in_action_ev,
    btpdef.MESH_EV_PROVISIONED: mesh_provisioned_ev,
    btpdef.MESH_EV_PROV_LINK_OPEN: mesh_prov_link_open_ev,
    btpdef.MESH_EV_PROV_LINK_CLOSED: mesh_prov_link_closed_ev,
}


def event_handler(hdr, data):
    logging.debug("%s %r %r", event_handler.__name__, hdr, data)

    stack = get_stack()
    if not stack:
        logging.info("Stack not initialized")
        return False

    if hdr.svc_id == btpdef.BTP_SERVICE_ID_MESH:
        if hdr.op in MESH_EV and stack.mesh:
            cb = MESH_EV[hdr.op]
            cb(stack.mesh, data[0], hdr.data_len)
            return True
    elif hdr.svc_id == btpdef.BTP_SERVICE_ID_GAP:
        if hdr.op in GAP_EV and stack.gap:
            cb = GAP_EV[hdr.op]
            cb(stack.gap, data[0], hdr.data_len)
            return True

    # TODO: Raise BTP error instead of logging
    logging.error("Unhandled event! svc_id %s op %s", hdr.svc_id, hdr.op)
    return False
