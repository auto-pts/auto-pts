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

import defs
from types import BTPError, gap_settings_btp2txt, addr2btp_ba, Addr, OwnAddrType, AdDuration
from pybtp.types import Perm
from iutctl_common import set_event_handler
from random import randint
from collections import namedtuple
from uuid import UUID
from ptsprojects.stack import get_stack, GattCharacteristic, ConnParams

#  get IUT global method from iutctl
get_iut = None

#  Global temporary objects
GATT_SVCS = None

# Address
LeAddress = namedtuple('LeAddress', 'addr_type addr')
PTS_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')

# Devices found
LeAdv = namedtuple('LeAdv', 'addr_type addr rssi flags eir')

#  A sequence of values to verify in PTS MMI description
VERIFY_VALUES = None

CONTROLLER_INDEX = 0

CORE = {
    "gap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gatt_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "gatt_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "l2cap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "l2cap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                    defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "mesh_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "mesh_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "read_supp_cmds": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "read_supp_svcs": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_SERVICES,
                       defs.BTP_INDEX_NONE, ""),
    "log_message":    (defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE,
                       defs.BTP_INDEX_NONE),
}

GAP = {
    "start_adv": (defs.BTP_SERVICE_ID_GAP, defs.GAP_START_ADVERTISING,
                  CONTROLLER_INDEX),
    "stop_adv": (defs.BTP_SERVICE_ID_GAP, defs.GAP_STOP_ADVERTISING,
                 CONTROLLER_INDEX, ""),
    "conn": (defs.BTP_SERVICE_ID_GAP, defs.GAP_CONNECT, CONTROLLER_INDEX),
    "pair": (defs.BTP_SERVICE_ID_GAP, defs.GAP_PAIR, CONTROLLER_INDEX),
    "unpair": (defs.BTP_SERVICE_ID_GAP, defs.GAP_UNPAIR, CONTROLLER_INDEX),
    "disconn": (defs.BTP_SERVICE_ID_GAP, defs.GAP_DISCONNECT,
                CONTROLLER_INDEX),
    "set_io_cap": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_IO_CAP,
                   CONTROLLER_INDEX),
    "set_conn": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_CONNECTABLE,
                 CONTROLLER_INDEX, 1),
    "set_nonconn": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_CONNECTABLE,
                    CONTROLLER_INDEX, 0),
    "set_nondiscov": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, defs.GAP_NON_DISCOVERABLE),
    "set_gendiscov": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, defs.GAP_GENERAL_DISCOVERABLE),
    "set_limdiscov": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_DISCOVERABLE,
                      CONTROLLER_INDEX, defs.GAP_LIMITED_DISCOVERABLE),
    "set_powered_on": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_POWERED,
                       CONTROLLER_INDEX, 1),
    "set_powered_off": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_POWERED,
                        CONTROLLER_INDEX, 0),
    "set_bondable_on": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_BONDABLE,
                        CONTROLLER_INDEX, 1),
    "set_bondable_off": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_BONDABLE,
                         CONTROLLER_INDEX, 0),
    "start_discov": (defs.BTP_SERVICE_ID_GAP,
                     defs.GAP_START_DISCOVERY, CONTROLLER_INDEX),
    "stop_discov": (defs.BTP_SERVICE_ID_GAP, defs.GAP_STOP_DISCOVERY,
                    CONTROLLER_INDEX, ""),
    "read_ctrl_info": (defs.BTP_SERVICE_ID_GAP,
                       defs.GAP_READ_CONTROLLER_INFO,
                       CONTROLLER_INDEX, ""),
    "passkey_entry_rsp": (defs.BTP_SERVICE_ID_GAP,
                          defs.GAP_PASSKEY_ENTRY,
                          CONTROLLER_INDEX),
    "start_direct_adv": (defs.BTP_SERVICE_ID_GAP, defs.GAP_START_DIRECT_ADV,
                         CONTROLLER_INDEX),
    "conn_param_update": (defs.BTP_SERVICE_ID_GAP,
                          defs.GAP_CONN_PARAM_UPDATE,
                          CONTROLLER_INDEX),
    "pairing_consent_rsp": (defs.BTP_SERVICE_ID_GAP,
                            defs.GAP_PAIRING_CONSENT_RSP,
                            CONTROLLER_INDEX),
    "oob_legacy_set_data": (defs.BTP_SERVICE_ID_GAP,
                            defs.GAP_OOB_LEGACY_SET_DATA,
                            CONTROLLER_INDEX),
    "oob_sc_get_local_data": (defs.BTP_SERVICE_ID_GAP,
                              defs.GAP_OOB_SC_GET_LOCAL_DATA,
                              CONTROLLER_INDEX),
    "oob_sc_set_remote_data": (defs.BTP_SERVICE_ID_GAP,
                               defs.GAP_OOB_SC_SET_REMOTE_DATA,
                               CONTROLLER_INDEX),
    "set_mitm_on": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_MITM,
                    CONTROLLER_INDEX, 1),
    "set_mitm_off": (defs.BTP_SERVICE_ID_GAP, defs.GAP_SET_MITM,
                     CONTROLLER_INDEX, 0),
    "reset": (defs.BTP_SERVICE_ID_GAP, defs.GAP_RESET, CONTROLLER_INDEX, "")
}

GATTS = {
    "add_svc": (defs.BTP_SERVICE_ID_GATT, defs.GATT_ADD_SERVICE,
                CONTROLLER_INDEX),
    "start_server": (defs.BTP_SERVICE_ID_GATT, defs.GATT_START_SERVER,
                     CONTROLLER_INDEX, ""),
    "add_inc_svc": (defs.BTP_SERVICE_ID_GATT,
                    defs.GATT_ADD_INCLUDED_SERVICE, CONTROLLER_INDEX),
    "add_char": (defs.BTP_SERVICE_ID_GATT, defs.GATT_ADD_CHARACTERISTIC,
                 CONTROLLER_INDEX),
    "set_val": (defs.BTP_SERVICE_ID_GATT, defs.GATT_SET_VALUE,
                CONTROLLER_INDEX),
    "add_desc": (defs.BTP_SERVICE_ID_GATT, defs.GATT_ADD_DESCRIPTOR,
                 CONTROLLER_INDEX),
    "set_enc_key_size": (defs.BTP_SERVICE_ID_GATT,
                         defs.GATT_SET_ENC_KEY_SIZE, CONTROLLER_INDEX),
    "get_attrs": (defs.BTP_SERVICE_ID_GATT, defs.GATT_GET_ATTRIBUTES,
                  CONTROLLER_INDEX),
    "get_attr_val": (defs.BTP_SERVICE_ID_GATT,
                     defs.GATT_GET_ATTRIBUTE_VALUE, CONTROLLER_INDEX),
    "change_database": (defs.BTP_SERVICE_ID_GATT,
                        defs.GATT_CHANGE_DATABASE, CONTROLLER_INDEX),
}

GATTC = {
    "exchange_mtu": (defs.BTP_SERVICE_ID_GATT, defs.GATT_EXCHANGE_MTU,
                     CONTROLLER_INDEX),
    "disc_all_prim": (defs.BTP_SERVICE_ID_GATT, defs.GATT_DISC_ALL_PRIM,
                      CONTROLLER_INDEX),
    "disc_prim_uuid": (defs.BTP_SERVICE_ID_GATT, defs.GATT_DISC_PRIM_UUID,
                       CONTROLLER_INDEX),
    "find_included": (defs.BTP_SERVICE_ID_GATT, defs.GATT_FIND_INCLUDED,
                      CONTROLLER_INDEX),
    "disc_all_chrc": (defs.BTP_SERVICE_ID_GATT, defs.GATT_DISC_ALL_CHRC,
                      CONTROLLER_INDEX),
    "disc_chrc_uuid": (defs.BTP_SERVICE_ID_GATT, defs.GATT_DISC_CHRC_UUID,
                       CONTROLLER_INDEX),
    "disc_all_desc": (defs.BTP_SERVICE_ID_GATT, defs.GATT_DISC_ALL_DESC,
                      CONTROLLER_INDEX),
    "read": (defs.BTP_SERVICE_ID_GATT, defs.GATT_READ, CONTROLLER_INDEX),
    "read_uuid": (defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_UUID,
                  CONTROLLER_INDEX),
    "read_long": (defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_LONG,
                  CONTROLLER_INDEX),
    "read_multiple": (defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_MULTIPLE,
                      CONTROLLER_INDEX),
    "read_multiple_var": (defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_MULTIPLE_VAR,
                          CONTROLLER_INDEX),
    "write_without_rsp": (defs.BTP_SERVICE_ID_GATT,
                          defs.GATT_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "signed_write": (defs.BTP_SERVICE_ID_GATT,
                     defs.GATT_SIGNED_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "write": (defs.BTP_SERVICE_ID_GATT, defs.GATT_WRITE, CONTROLLER_INDEX),
    "write_long": (defs.BTP_SERVICE_ID_GATT, defs.GATT_WRITE_LONG,
                   CONTROLLER_INDEX),
    "write_reliable": (defs.BTP_SERVICE_ID_GATT, defs.GATT_WRITE_RELIABLE,
                       CONTROLLER_INDEX),
    "cfg_notify": (defs.BTP_SERVICE_ID_GATT, defs.GATT_CFG_NOTIFY,
                   CONTROLLER_INDEX),
    "cfg_indicate": (defs.BTP_SERVICE_ID_GATT, defs.GATT_CFG_INDICATE,
                     CONTROLLER_INDEX),
}

L2CAP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_L2CAP,
                       defs.L2CAP_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_CONNECT,
                CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_DISCONNECT,
                   CONTROLLER_INDEX),
    "send_data": (defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_SEND_DATA,
                  CONTROLLER_INDEX),
    "listen": (defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_LISTEN,
               CONTROLLER_INDEX),
    "reconfigure": (defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_RECONFIGURE,
                    CONTROLLER_INDEX),
}

MESH = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "config_prov": (defs.BTP_SERVICE_ID_MESH,
                    defs.MESH_CONFIG_PROVISIONING,
                    CONTROLLER_INDEX),
    "prov_node": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_PROVISION_NODE,
                  CONTROLLER_INDEX),
    "init": (defs.BTP_SERVICE_ID_MESH,
             defs.MESH_INIT,
             CONTROLLER_INDEX, ""),
    "reset": (defs.BTP_SERVICE_ID_MESH,
              defs.MESH_RESET,
              CONTROLLER_INDEX, ""),
    "input_num": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_INPUT_NUMBER,
                  CONTROLLER_INDEX),
    "input_str": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_INPUT_STRING,
                  CONTROLLER_INDEX),
    "iv_update_test_mode": (defs.BTP_SERVICE_ID_MESH,
                            defs.MESH_IV_UPDATE_TEST_MODE,
                            CONTROLLER_INDEX),
    "iv_update_toggle": (defs.BTP_SERVICE_ID_MESH,
                         defs.MESH_IV_UPDATE_TOGGLE,
                         CONTROLLER_INDEX, ""),
    "net_send": (defs.BTP_SERVICE_ID_MESH,
                 defs.MESH_NET_SEND,
                 CONTROLLER_INDEX),
    "health_generate_faults": (defs.BTP_SERVICE_ID_MESH,
                               defs.MESH_HEALTH_ADD_FAULTS,
                               CONTROLLER_INDEX, ""),
    "mesh_clear_faults": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_HEALTH_CLEAR_FAULTS,
                          CONTROLLER_INDEX, ""),
    "lpn": (defs.BTP_SERVICE_ID_MESH,
            defs.MESH_LPN_SET,
            CONTROLLER_INDEX),
    "lpn_poll": (defs.BTP_SERVICE_ID_MESH,
                 defs.MESH_LPN_POLL,
                 CONTROLLER_INDEX, ""),
    "model_send": (defs.BTP_SERVICE_ID_MESH,
                   defs.MESH_MODEL_SEND,
                   CONTROLLER_INDEX),
    "lpn_subscribe": (defs.BTP_SERVICE_ID_MESH,
                      defs.MESH_LPN_SUBSCRIBE,
                      CONTROLLER_INDEX),
    "lpn_unsubscribe": (defs.BTP_SERVICE_ID_MESH,
                        defs.MESH_LPN_UNSUBSCRIBE,
                        CONTROLLER_INDEX),
    "rpl_clear": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_RPL_CLEAR,
                  CONTROLLER_INDEX, ""),
    "proxy_identity": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_PROXY_IDENTITY,
                       CONTROLLER_INDEX, ""),
}


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


def parse_passkey_description(description):
    """A function to parse passkey from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\b[0-9]+\b", description)
    if match:
        pk = match.group(0)
        logging.debug("passkey=%r", pk)
        return int(pk)

    return None


def parse_handle_description(description):
    """A function to parse handle from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\bhandle \b([0-9A-Fa-f]+)\b", description)
    if match:
        handle = match.group(1)
        logging.debug("handle=%r", handle)
        return int(handle)

    return None


def btp_hdr_check(rcv_hdr, exp_svc_id, exp_op=None):
    if rcv_hdr.svc_id != exp_svc_id:
        raise BTPError("Incorrect service ID %s in the response, expected %s!"
                       % (rcv_hdr.svc_id, exp_svc_id))

    if rcv_hdr.op == defs.BTP_STATUS:
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
    """"
    If address type provided, return it, otherwise,
    use stored address.
    """
    if bd_addr_type is None:
        return PTS_BD_ADDR.addr_type
    return bd_addr_type


def set_pts_addr(addr, addr_type):
    global PTS_BD_ADDR
    PTS_BD_ADDR = LeAddress(addr_type=addr_type, addr=bd_addr_convert(addr))


def core_reg_svc_gap():
    logging.debug("%s", core_reg_svc_gap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gap_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_gap():
    logging.debug("%s", core_unreg_svc_gap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gap_unreg'])

    core_unreg_svc_rsp_succ()


def core_reg_svc_gatt():
    logging.debug("%s", core_reg_svc_gatt.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gatt_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_gatt():
    logging.debug("%s", core_unreg_svc_gatt.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gatt_unreg'])


def core_reg_svc_l2cap():
    logging.debug("%s", core_reg_svc_l2cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['l2cap_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_l2cap():
    logging.debug("%s", core_unreg_svc_l2cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['l2cap_unreg'])


def core_reg_svc_mesh():
    logging.debug("%s", core_reg_svc_mesh.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['mesh_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_mesh():
    logging.debug("%s", core_unreg_svc_mesh.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mesh_unreg'])


def core_reg_svc_rsp_succ():
    logging.debug("%s", core_reg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_REGISTER_SERVICE,
                       defs.BTP_INDEX_NONE,
                       0),
                      ('',))

    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    else:
        logging.debug("response is valid")


def core_unreg_svc_rsp_succ():
    logging.debug("%s", core_unreg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_UNREGISTER_SERVICE,
                       defs.BTP_INDEX_NONE,
                       0),
                      ('',))

    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    else:
        logging.debug("response is valid")


def core_log_message(message):
    logging.debug("%s", core_log_message.__name__)

    message_data = bytearray(message)
    data = struct.pack('H', len(message_data))
    data.extend(message_data)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['log_message'], data=data)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE)


def __gap_current_settings_update(settings):
    logging.debug("%s %r", __gap_current_settings_update.__name__, settings)
    if isinstance(settings, tuple):
        fmt = '<I'
        if len(settings[0]) != struct.calcsize(fmt):
            raise BTPError("Invalid data length")

        settings = struct.unpack(fmt, settings[0])
        settings = settings[0]  # Result of unpack is always a tuple

    stack = get_stack()

    for bit in gap_settings_btp2txt:
        if settings & (1 << bit):
            stack.gap.current_settings_set(gap_settings_btp2txt[bit])
        else:
            stack.gap.current_settings_clear(gap_settings_btp2txt[bit])


def gap_wait_for_connection(timeout=30):
    stack = get_stack()

    stack.gap.wait_for_connection(timeout)


def gap_wait_for_disconnection(timeout=30):
    stack = get_stack()

    stack.gap.wait_for_disconnection(timeout)


def gap_adv_ind_on(ad={}, sd={}, duration=AdDuration.forever, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", gap_adv_ind_on.__name__, ad, sd)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return

    iutctl = get_iut()

    data_ba = bytearray()
    ad_ba = bytearray()
    sd_ba = bytearray()

    for ad_type, ad_data in ad.iteritems():
        data = binascii.unhexlify(bytearray(ad_data))
        ad_ba.extend(chr(ad_type))
        ad_ba.extend(chr(len(data)))
        ad_ba.extend(data)

    for sd_type, sd_data in sd.iteritems():
        data = binascii.unhexlify(bytearray(sd_data))
        sd_ba.extend(chr(sd_type))
        sd_ba.extend(chr(len(data)))
        sd_ba.extend(data)

    data_ba.extend(chr(len(ad_ba)))
    data_ba.extend(chr(len(sd_ba)))
    data_ba.extend(ad_ba)
    data_ba.extend(sd_ba)
    data_ba.extend(struct.pack("<I", duration))
    data_ba.extend(chr(own_addr_type))

    iutctl.btp_socket.send(*GAP['start_adv'], data=data_ba)

    tuple_data = gap_command_rsp_succ(defs.GAP_START_ADVERTISING)
    __gap_current_settings_update(tuple_data)


def gap_adv_off():
    logging.debug("%s", gap_adv_off.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['stop_adv'])

    tuple_data = gap_command_rsp_succ(defs.GAP_STOP_ADVERTISING)
    __gap_current_settings_update(tuple_data)


def gap_direct_adv_on(addr, addr_type, high_duty=0):
    logging.debug("%s %r %r", gap_direct_adv_on.__name__, addr, high_duty)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return

    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(addr)
    data_ba.extend(chr(addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(high_duty))

    iutctl.btp_socket.send(*GAP['start_direct_adv'], data=data_ba)

    tuple_data = gap_command_rsp_succ(defs.GAP_START_DIRECT_ADV)
    __gap_current_settings_update(tuple_data)


def gap_conn(bd_addr=None, bd_addr_type=None, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", gap_conn.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(own_addr_type))

    iutctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()


def gap_rpa_conn(description, own_addr_type=OwnAddrType.le_identity_address):
    """Initiate connection with PTS using RPA address provided
    in MMI description. Function returns True.

    Arguments:
    description -- description provided in PTS MMI.
    """
    logging.debug("%s %s", gap_conn.__name__, description)
    iutctl = get_iut()

    bd_addr = re.search("[a-fA-F0-9]{12}", description).group(0)
    bd_addr_type = Addr.le_random

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(own_addr_type))

    iutctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()
    return True


def gap_disconn(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_disconn.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    stack = get_stack()

    if not stack.gap.is_connected():
        return

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['disconn'], data=data_ba)

    gap_command_rsp_succ()


def verify_not_connected(description):
    logging.debug("%s", verify_not_connected.__name__)
    stack = get_stack()

    gap_wait_for_connection(5)

    if stack.gap.is_connected():
        return False
    return True


def gap_set_io_cap(io_cap):
    logging.debug("%s %r", gap_set_io_cap.__name__, io_cap)
    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_io_cap'], data=chr(io_cap))

    gap_command_rsp_succ()


def gap_pair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_pair.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['pair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_unpair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_unpair.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['unpair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ(defs.GAP_UNPAIR)


def var_store_get_passkey(description):
    pk = get_stack().gap.get_passkey()
    if pk:
        return str(pk).zfill(6)
    else:
        return '000000'


def var_store_get_wrong_passkey(description):
    passkey = get_stack().gap.get_passkey()

    # Passkey is in range 0-999999
    if passkey > 0:
        return str(passkey - 1).zfill(6)
    else:
        return str(passkey + 1).zfill(6)


def gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey):
    logging.debug("%s %r %r", gap_passkey_entry_rsp.__name__, bd_addr,
                  bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    if isinstance(passkey, str):
        passkey = int(passkey, 32)

    passkey_ba = struct.pack('I', passkey)
    data_ba.extend(passkey_ba)

    iutctl.btp_socket.send(*GAP['passkey_entry_rsp'], data=data_ba)

    gap_command_rsp_succ()


def gap_reset():
    logging.debug("%s", gap_reset.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*GAP['reset'])

    gap_command_rsp_succ()


def gap_passkey_entry_req_ev(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_passkey_entry_req_ev.__name__, bd_addr,
                  bd_addr_type)
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GAP,
                  defs.GAP_EV_PASSKEY_ENTRY_REQ)

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

    stack = get_stack()
    if not stack.gap.passkey.data:
        # Generate some passkey
        stack.gap.passkey.data = randint(0, 999999)

    gap_passkey_entry_rsp(bd_addr, bd_addr_type, stack.gap.passkey.data)


def gap_set_conn():
    logging.debug("%s", gap_set_conn.__name__)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_CONNECTABLE]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_conn'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_nonconn():
    logging.debug("%s", gap_set_nonconn.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_CONNECTABLE]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_nonconn'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_nondiscov():
    logging.debug("%s", gap_set_nondiscov.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_DISCOVERABLE]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_nondiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_gendiscov():
    logging.debug("%s", gap_set_gendiscov.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_gendiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_limdiscov():
    logging.debug("%s", gap_set_limdiscov.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_limdiscov'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_powered_on():
    logging.debug("%s", gap_set_powered_on.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_powered_on'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_powered_off():
    logging.debug("%s", gap_set_powered_off.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_powered_off'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_bondable_on():
    logging.debug("%s", gap_set_bondable_on.__name__)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_BONDABLE]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_bondable_on'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_bondable_off():
    logging.debug("%s", gap_set_bondable_off.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_BONDABLE]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_bondable_off'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_start_discov(transport='le', type='active', mode='general'):
    """GAP Start Discovery function.

    Possible options (key: <values>):

    transport: <le, bredr>
    type: <active, passive>
    mode: <general, limited, observe>

    """
    logging.debug("%s", gap_start_discov.__name__)

    iutctl = get_iut()

    flags = 0

    if transport == "le":
        flags |= defs.GAP_DISCOVERY_FLAG_LE
    else:
        flags |= defs.GAP_DISCOVERY_FLAG_BREDR

    if type == "active":
        flags |= defs.GAP_DISCOVERY_FLAG_LE_ACTIVE_SCAN

    if mode == "limited":
        flags |= defs.GAP_DISCOVERY_FLAG_LIMITED
    elif mode == "observe":
        flags |= defs.GAP_DISCOVERY_FLAG_LE_OBSERVE

    stack = get_stack()
    stack.gap.reset_discovery()

    iutctl.btp_socket.send(*GAP['start_discov'], data=chr(flags))

    gap_command_rsp_succ()


def check_discov_results(addr_type=None, addr=None, discovered=True, eir=None):
    addr = pts_addr_get(addr)
    addr_type = pts_addr_type_get(addr_type)

    logging.debug("%s %r %r %r %r", check_discov_results.__name__, addr_type,
                  addr, discovered, eir)

    found = False

    stack = get_stack()
    devices = stack.gap.found_devices.data

    for device in devices:
        logging.debug("matching %r", device)
        if addr_type != device.addr_type:
            continue
        if addr != device.addr:
            continue
        if eir and eir != device.eir:
            continue

        found = True
        break

    if discovered == found:
        return True

    return False


def gap_stop_discov():
    logging.debug("%s", gap_stop_discov.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['stop_discov'])

    gap_command_rsp_succ()

    stack = get_stack()
    stack.gap.discoverying.data = False


def gap_read_ctrl_info():
    logging.debug("%s", gap_read_ctrl_info.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['read_ctrl_info'])

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GAP,
                  defs.GAP_READ_CONTROLLER_INFO)

    fmt = '<6sII3s249s11s'
    if len(tuple_data[0]) < struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr, _supp_set, _curr_set, _cod, _name, _name_sh = \
        struct.unpack_from(fmt, tuple_data[0])
    _addr = binascii.hexlify(_addr[::-1]).lower()

    stack = get_stack()

    addr_type = Addr.le_random if \
        (_curr_set & (1 << defs.GAP_SETTINGS_PRIVACY)) or \
        (_curr_set & (1 << defs.GAP_SETTINGS_STATIC_ADDRESS)) else \
        Addr.le_public

    stack.gap.iut_addr_set(_addr, addr_type)
    logging.debug("IUT address %r", stack.gap.iut_addr_get_str())

    __gap_current_settings_update(_curr_set)


def gap_command_rsp_succ(op=None):
    logging.debug("%s", gap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GAP, op)

    return tuple_data


def gap_conn_param_update(bd_addr, bd_addr_type, conn_itvl_min,
                          conn_itvl_max, conn_latency, supervision_timeout):
    logging.debug("%s %r %r", gap_conn_param_update.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)))
    data_ba.extend(bd_addr_ba)

    conn_itvl_min_ba = struct.pack('H', conn_itvl_min)
    conn_itvl_max_ba = struct.pack('H', conn_itvl_max)
    conn_latency_ba = struct.pack('H', conn_latency)
    supervision_timeout_ba = struct.pack('H', supervision_timeout)

    data_ba.extend(conn_itvl_min_ba)
    data_ba.extend(conn_itvl_max_ba)
    data_ba.extend(conn_latency_ba)
    data_ba.extend(supervision_timeout_ba)

    iutctl.btp_socket.send(*GAP['conn_param_update'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_oob_legacy_set_data(oob_data):
    logging.debug("%s %r", gap_oob_legacy_set_data.__name__, oob_data)
    iutctl = get_iut()

    data_ba = binascii.unhexlify(oob_data)[::-1]

    iutctl.btp_socket.send(*GAP['oob_legacy_set_data'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_oob_sc_get_local_data():
    logging.debug("%s", gap_oob_sc_get_local_data.__name__)
    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['oob_sc_get_local_data'], data=bytearray())

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gap_oob_sc_get_local_data.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GAP,
                  defs.GAP_OOB_SC_GET_LOCAL_DATA)

    hdr = '<16s16s'
    r, c = struct.unpack_from(hdr, tuple_data[0])
    r, c = binascii.hexlify(r[::-1]), binascii.hexlify(c[::-1])

    logging.debug("r=%s c=%s", r, c)
    return r, c


def gap_oob_sc_set_remote_data(r, c):
    logging.debug("%s %r %r", gap_oob_sc_set_remote_data.__name__, r, c)
    iutctl = get_iut()

    data_ba = bytearray()
    r_ba = binascii.unhexlify(r)[::-1]
    c_ba = binascii.unhexlify(c)[::-1]

    data_ba.extend(r_ba)
    data_ba.extend(c_ba)

    iutctl.btp_socket.send(*GAP['oob_sc_set_remote_data'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_set_mitm_on():
    logging.debug("%s", gap_set_mitm_on.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_mitm_on'])

    gap_command_rsp_succ()


def gap_set_mitm_off():
    logging.debug("%s", gap_set_mitm_off.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_mitm_off'])

    gap_command_rsp_succ()


def gatts_add_svc(svc_type, uuid):
    logging.debug("%s %r %r", gatts_add_svc.__name__, svc_type, uuid)

    iutctl = get_iut()

    data_ba = bytearray()
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(chr(svc_type))
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTS['add_svc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_inc_svc(hdl):
    logging.debug("%s %r", gatts_add_inc_svc.__name__, hdl)

    iutctl = get_iut()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    data_ba.extend(hdl_ba)

    iutctl.btp_socket.send(*GATTS['add_inc_svc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_char(hdl, prop, perm, uuid):
    logging.debug("%s %r %r %r %r", gatts_add_char.__name__, hdl, prop, perm,
                  uuid)

    iutctl = get_iut()

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

    iutctl.btp_socket.send(*GATTS['add_char'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_set_val(hdl, val):
    logging.debug("%s %r %r ", gatts_set_val.__name__, hdl, val)

    iutctl = get_iut()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTS['set_val'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_desc(hdl, perm, uuid):
    logging.debug("%s %r %r %r", gatts_add_desc.__name__, hdl, perm, uuid)

    iutctl = get_iut()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(perm))
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTS['add_desc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_change_database(start_hdl, end_hdl, vis):
    logging.debug("%s %r %r %r", gatts_change_database.__name__, start_hdl, end_hdl, vis)

    iutctl = get_iut()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(end_hdl) is str:
        end_hdl = int(end_hdl, 16)

    data_ba = bytearray()
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)
    data_ba.extend(chr(vis))

    iutctl.btp_socket.send(*GATTS['change_database'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_start_server():
    logging.debug("%s", gatts_start_server.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*GATTS['start_server'])

    gatt_command_rsp_succ()


def gatts_set_enc_key_size(hdl, enc_key_size):
    logging.debug("%s %r %r", gatts_set_enc_key_size.__name__,
                  hdl, enc_key_size)

    iutctl = get_iut()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(enc_key_size))

    iutctl.btp_socket.send(*GATTS['set_enc_key_size'], data=data_ba)

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

    iutctl = get_iut()

    (tuple_hdr, tuple_data) = iutctl.btp_socket.read()

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_EV_ATTR_VALUE_CHANGED)

    (handle, data) = gatts_dec_attr_value_changed_ev_data(tuple_data[0])
    logging.debug("%s %r %r", gatts_attr_value_changed_ev.__name__,
                  handle, data)

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
    except BaseException:
        logging.debug("%s PTS failed to write attribute value",
                      gatts_verify_write_success.__name__)
        return False


def gatts_verify_write_fail(description):
    return not gatts_verify_write_success(description)


def btp2uuid(uuid_len, uu):
    if uuid_len == 2:
        (uu,) = struct.unpack("H", uu)
        return format(uu, 'x').upper()
    else:
        return UUID(bytes=uu[::-1]).urn[9:].replace('-', '').upper()


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

    iutctl = get_iut()

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

    iutctl.btp_socket.send(*GATTS['get_attrs'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_GET_ATTRIBUTES)

    return dec_gatts_get_attrs_rp(tuple_data[0], tuple_hdr.data_len)


def gatts_get_attr_val(bd_addr_type, bd_addr, handle):
    logging.debug("%s %r", gatts_get_attr_val.__name__, handle)

    iutctl = get_iut()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    if type(handle) is str:
        handle = int(handle, 16)

    hdl_ba = struct.pack('H', handle)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    iutctl.btp_socket.send(*GATTS['get_attr_val'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_GET_ATTRIBUTE_VALUE)

    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)
    data_len = tuple_hdr.data_len - hdr_len

    return struct.unpack(hdr + '%ds' % data_len, tuple_data[0])


def gattc_exchange_mtu(bd_addr_type, bd_addr):
    logging.debug("%s %r %r", gattc_exchange_mtu.__name__, bd_addr_type,
                  bd_addr)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GATTC['exchange_mtu'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_disc_all_prim(bd_addr_type, bd_addr):
    logging.debug("%s %r %r", gattc_disc_all_prim.__name__, bd_addr_type,
                   bd_addr)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_prim'], data=data_ba)


def gattc_disc_prim_uuid(bd_addr_type, bd_addr, uuid):
    logging.debug("%s %r %r %r", gattc_disc_prim_uuid.__name__, bd_addr_type,
                  bd_addr, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    uuid_ba = binascii.unhexlify(uuid.translate(None, "-"))[::-1]

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['disc_prim_uuid'], data=data_ba)


def _gattc_find_included_req(bd_addr_type, bd_addr, start_hdl, end_hdl):
    logging.debug("%s %r %r %r %r", _gattc_find_included_req.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    iutctl = get_iut()

    if type(end_hdl) is str:
        end_hdl = int(end_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)

    iutctl.btp_socket.send(*GATTC['find_included'], data=data_ba)


def _gattc_find_included_rsp():
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_find_included_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_FIND_INCLUDED)

    incls_tuple = gatt_dec_disc_rsp(tuple_data[0], "include")
    logging.debug("%s %r", gattc_find_included_rsp.__name__, incls_tuple)

    for incl in incls_tuple:
        att_handle = "%04X" % (incl[0][0],)
        inc_svc_handle = "%04X" % (incl[1][0],)
        end_grp_handle = "%04X" % (incl[1][1],)
        uuid = incl[1][2]

        VERIFY_VALUES.append(att_handle)
        VERIFY_VALUES.append(inc_svc_handle)
        VERIFY_VALUES.append(end_grp_handle)
        VERIFY_VALUES.append(uuid)

    logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_find_included(bd_addr_type, bd_addr, start_hdl=None, end_hdl=None):
    logging.debug("%s %r %r %r %r", gattc_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    gap_wait_for_connection()

    if start_hdl and end_hdl:
        _gattc_find_included_req(bd_addr_type, bd_addr, start_hdl, end_hdl)
        return

    gattc_disc_all_prim(bd_addr_type, bd_addr)
    svcs_tuple = gattc_disc_all_prim_rsp()

    global VERIFY_VALUES
    VERIFY_VALUES = []

    for start, end, _ in svcs_tuple:
        _gattc_find_included_req(bd_addr_type, bd_addr, start, end)
        _gattc_find_included_rsp()


def gattc_disc_all_chrc_find_attrs_rsp(exp_chars, store_attrs=False):
    """Parse and find requested characteristics from rsp

    ATTRIBUTE FORMAT (CHARACTERISTIC) - (handle, val handle, props, uuid)

    """
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r",
                  gattc_disc_all_chrc_find_attrs_rsp.__name__, tuple_hdr,
                  tuple_data)
    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_CHRC)

    chars_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")

    for char in chars_tuple:
        for exp_char in exp_chars:
            # Check if option expected attribute parameters match
            if ((exp_char[0] and exp_char[0] != char[0]) or
                    (exp_char[1] and exp_char[1] != char[1]) or
                    (exp_char[2] and exp_char[2] != char[2]) or
                    (exp_char[3] and exp_char[3] != char[3])):

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
    iutctl = get_iut()

    gap_wait_for_connection()

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

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_chrc'], data=data_ba)


def gattc_disc_chrc_uuid(bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gattc_disc_chrc_uuid.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
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

    iutctl.btp_socket.send(*GATTC['disc_chrc_uuid'], data=data_ba)


def gattc_disc_all_desc(bd_addr_type, bd_addr, start_hdl, stop_hdl):
    logging.debug("%s %r %r %r %r", gattc_disc_all_desc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_desc'], data=data_ba)


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
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    if type(hdl) is str:
        hdl = int(hdl, 16)
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    iutctl.btp_socket.send(*GATTC['read'], data=data_ba)


def gattc_read_uuid(bd_addr_type, bd_addr, start_hdl, end_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gattc_read_uuid.__name__, bd_addr_type,
                  bd_addr, start_hdl, end_hdl, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(end_hdl) is str:
        end_hdl = int(end_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)

    if "-" in uuid:
        uuid = uuid.replace("-", "")
    if uuid.startswith("0x"):
        uuid = uuid.replace("0x", "")
    uuid_ba = binascii.unhexlify(uuid)[::-1]

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)
    data_ba.extend(chr(len(uuid_ba)))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['read_uuid'], data=data_ba)


def gattc_read_long(bd_addr_type, bd_addr, hdl, off, modif_off=None):
    logging.debug("%s %r %r %r %r %r", gattc_read_long.__name__, bd_addr_type,
                  bd_addr, hdl, off, modif_off)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    if type(off) is str:
        off = int(off, 16)
    if modif_off:
        off += modif_off
    if type(hdl) is str:
        hdl = int(hdl, 16)

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)

    iutctl.btp_socket.send(*GATTC['read_long'], data=data_ba)


def gattc_read_multiple(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gattc_read_multiple.__name__, bd_addr_type,
                  bd_addr, hdls)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdls_j = ''.join(hdl for hdl in hdls)
    hdls_byte_table = [hdls_j[i:i + 2] for i in range(0, len(hdls_j), 2)]
    hdls_swp = ''.join([c[1] + c[0] for c in zip(hdls_byte_table[::2],
                                                 hdls_byte_table[1::2])])
    hdls_ba = binascii.unhexlify(bytearray(hdls_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(hdls)))
    data_ba.extend(hdls_ba)

    iutctl.btp_socket.send(*GATTC['read_multiple'], data=data_ba)


def gattc_read_multiple_var(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gattc_read_multiple_var.__name__, bd_addr_type,
                  bd_addr, hdls)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdls_j = ''.join(hdl for hdl in hdls)
    hdls_byte_table = [hdls_j[i:i + 2] for i in range(0, len(hdls_j), 2)]
    hdls_swp = ''.join([c[1] + c[0] for c in zip(hdls_byte_table[::2],
                                                 hdls_byte_table[1::2])])
    hdls_ba = binascii.unhexlify(bytearray(hdls_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(hdls)))
    data_ba.extend(hdls_ba)

    iutctl.btp_socket.send(*GATTC['read_multiple_var'], data=data_ba)


def gattc_write_without_rsp(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_without_rsp.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTC['write_without_rsp'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_signed_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_signed_write.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTC['signed_write'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write.__name__, bd_addr_type,
                  bd_addr, hdl, val, val_mtp)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTC['write'], data=data_ba)


def gattc_write_long(bd_addr_type, bd_addr, hdl, off, val, length=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_long.__name__,
                  bd_addr_type, hdl, off, val, length)
    gap_wait_for_connection()

    if type(hdl) is str:
        hdl = int(hdl, 16)  # convert string in hex format to int

    if type(off) is str:
        off = int(off, 16)

    if length:
        val *= int(length)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
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

    iutctl.btp_socket.send(*GATTC['write_long'], data=data_ba)


def gattc_write_reliable(bd_addr_type, bd_addr, hdl, off, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_reliable.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    iutctl = get_iut()

    gap_wait_for_connection()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', int(off))
    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTC['write_reliable'], data=data_ba)


def gattc_cfg_notify(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gattc_cfg_notify.__name__, bd_addr_type,
                  bd_addr, enable, ccc_hdl)
    gap_wait_for_connection()

    if type(ccc_hdl) is str:
        ccc_hdl = int(ccc_hdl, 16)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable))
    data_ba.extend(ccc_hdl_ba)

    iutctl.btp_socket.send(*GATTC['cfg_notify'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_cfg_notify.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_CFG_NOTIFY)


def gattc_cfg_indicate(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gattc_cfg_indicate.__name__,
                  bd_addr_type, bd_addr, enable, ccc_hdl)
    gap_wait_for_connection()

    if type(ccc_hdl) is str:
        ccc_hdl = int(ccc_hdl, 16)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable))
    data_ba.extend(ccc_hdl_ba)

    iutctl.btp_socket.send(*GATTC['cfg_indicate'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_cfg_indicate.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_CFG_INDICATE)


def gattc_notification_ev(bd_addr, bd_addr_type, ev_type):
    logging.debug("%s %r %r %r", gattc_notification_ev.__name__, bd_addr,
                  bd_addr_type, ev_type)
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_EV_NOTIFICATION)

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(ev_type))

    if tuple_data[0][0:len(data_ba)] != data_ba:
        raise BTPError("Error in notification event data")


def gatt_command_rsp_succ():
    logging.debug("%s", gatt_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT)


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
    (uuid,) = struct.unpack_from('%ds' % uuid_len, data, hdr_len)
    uuid = btp2uuid(uuid_len, uuid)

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
    (uuid,) = struct.unpack_from('%ds' % uuid_len, data, hdr_len)
    uuid = btp2uuid(uuid_len, uuid)

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
    (uuid,) = struct.unpack_from('%ds' % uuid_len, data, hdr_len)
    uuid = btp2uuid(uuid_len, uuid)

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
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r",
                  gattc_disc_prim_uuid_find_attrs_rsp.__name__, tuple_hdr,
                  tuple_data)
    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_PRIM_UUID)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")

    for svc in svcs_tuple:
        for exp_svc in exp_svcs:
            # Check if option expected attribute parameters match
            if ((exp_svc[0] and exp_svc[0] != svc[0]) or
                    (exp_svc[1] and exp_svc[1] != svc[1]) or
                    (exp_svc[2] and exp_svc[2] != svc[2])):

                logging.debug("gatt svc not matched = %r != %r", svc, exp_svc)

                continue

            logging.debug("gatt svc matched = %r == %r", svc, exp_svc)

            if store_attrs:
                global GATT_SVCS

                GATT_SVCS = []

                GATT_SVCS.append(svc)


def gattc_disc_all_prim_rsp(store_rsp=False):
    logging.debug("%s", gattc_disc_all_prim_rsp.__name__)
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_prim_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_PRIM)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_all_prim_rsp.__name__, svcs_tuple)

    if store_rsp:
        global VERIFY_VALUES

        VERIFY_VALUES = []

        for svc in svcs_tuple:
            # Keep just UUID since PTS checks only UUID.
            uuid = svc[2].upper()

            # avoid repeated service uuid, it should be verified only once
            if uuid not in VERIFY_VALUES:
                VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)

    return svcs_tuple


def gattc_disc_prim_uuid_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_prim_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_PRIM_UUID)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_prim_uuid_rsp.__name__, svcs_tuple)

    if store_rsp:
        global VERIFY_VALUES

        VERIFY_VALUES = []

        for svc in svcs_tuple:
            start_handle = "%04X" % (svc[0],)
            end_handle = "%04X" % (svc[1],)

            uuid = svc[2]

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
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_find_included_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_FIND_INCLUDED)

    incls_tuple = gatt_dec_disc_rsp(tuple_data[0], "include")
    logging.debug("%s %r", gattc_find_included_rsp.__name__, incls_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for incl in incls_tuple:
            att_handle = "%04X" % (incl[0][0],)
            inc_svc_handle = "%04X" % (incl[1][0],)
            end_grp_handle = "%04X" % (incl[1][1],)
            uuid = incl[1][2]

            VERIFY_VALUES.append(att_handle)
            VERIFY_VALUES.append(inc_svc_handle)
            VERIFY_VALUES.append(end_grp_handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_disc_all_chrc_rsp(store_rsp=False):
    iutctl = get_iut()
    attrs = []

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_chrc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_CHRC)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_all_chrc_rsp.__name__, chrcs_tuple)

    for chrc in chrcs_tuple:
        (handle, value_handle, prop, uuid) = chrc
        attrs.append(GattCharacteristic(handle=handle,
                                        perm=Perm.read,
                                        uuid=uuid,
                                        att_rsp=0,
                                        prop=prop,
                                        value_handle=value_handle))

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for attr in attrs:
            VERIFY_VALUES.append("%04X" % attr.handle)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)

    return attrs


def gattc_disc_chrc_uuid_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_chrc_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_CHRC_UUID)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_chrc_uuid_rsp.__name__, chrcs_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for chrc in chrcs_tuple:
            handle = "%04X" % (chrc[1],)
            uuid = chrc[3]

            # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
            if len(uuid) > 4:
                uuid = "-".join([uuid[i:i+4] for i in range(0, len(uuid), 4)])

            VERIFY_VALUES.append(handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


def gattc_disc_all_desc_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_desc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_DESC)

    descs_tuple = gatt_dec_disc_rsp(tuple_data[0], "descriptor")
    logging.debug("%s %r", gattc_disc_all_desc_rsp.__name__, descs_tuple)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        for desc in descs_tuple:
            handle = "%04X" % (desc[0],)
            uuid = desc[1]
            VERIFY_VALUES.append(handle)
            VERIFY_VALUES.append(uuid)

        logging.debug("Set verify values to: %r", VERIFY_VALUES)


att_rsp_str = {0:   "",
               1:   "Invalid handle error",
               2:   "read is not permitted error",
               3:   "write is not permitted error",
               5:   "authentication error",
               7:   "Invalid offset error",
               8:   "authorization error",
               10:  "attribute not found error",
               12:  "encryption key size error",
               13:  "Invalid attribute value length error",
               14:  "unlikely error",
               128: "Application error",
               }


def gattc_read_rsp(store_rsp=False, store_val=False, timeout=None):
    iutctl = get_iut()

    if timeout:
        tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    else:
        tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_READ)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_rsp.__name__, rsp, value)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            VERIFY_VALUES.append((binascii.hexlify(value[0])).upper())


def gattc_read_uuid_rsp(store_rsp=False, store_val=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_uuid_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_UUID)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_uuid_rsp.__name__, rsp, value)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            n = len(value[0])
            value = (binascii.hexlify(value[0])).upper()
            if value != '':
                chunks = [value[i:i+len(value)/n] for i in range(0, len(value), len(value)/n)]
                VERIFY_VALUES.extend(chunks)


def gattc_read_long_rsp(store_rsp=False, store_val=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_long_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_LONG)

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
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_multiple_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_READ_MULTIPLE)

    rsp, values = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_multiple_rsp.__name__, rsp, values)

    if store_rsp or store_val:
        global VERIFY_VALUES
        VERIFY_VALUES = []

        if store_rsp:
            VERIFY_VALUES.append(att_rsp_str[rsp])

        if store_val:
            VERIFY_VALUES.append((binascii.hexlify(values[0])).upper())


def gattc_read_multiple_rsp(store_val=False, store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_multiple_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_READ_MULTIPLE)

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
    iutctl = get_iut()

    if timeout:
        tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    else:
        tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_WRITE)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_rsp.__name__, rsp)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(att_rsp_str[rsp])


def gattc_write_long_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_long_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_WRITE_LONG)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_long_rsp.__name__, rsp)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(att_rsp_str[rsp])


def gattc_write_reliable_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_reliable_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_WRITE_RELIABLE)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_long_rsp.__name__, rsp)

    if store_rsp:
        global VERIFY_VALUES
        VERIFY_VALUES = []
        VERIFY_VALUES.append(att_rsp_str[rsp])


def l2cap_command_rsp_succ(op=None):
    logging.debug("%s", l2cap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, op)


def l2cap_conn(bd_addr, bd_addr_type, psm, mtu=0, num=1):
    logging.debug("%s %r %r %r", l2cap_conn.__name__, bd_addr, bd_addr_type,
                  psm)
    iutctl = get_iut()
    gap_wait_for_connection()

    if type(psm) is str:
        psm = int(psm, 16)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', num))

    iutctl.btp_socket.send(*L2CAP['connect'], data=data_ba)

    chan_ids = l2cap_conn_rsp()
    logging.debug("id %r", chan_ids)


l2cap_result_str = {0:  "Success",
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

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_CONNECT)
    num = struct.unpack_from('<B', tuple_data[0])[0]
    channels = struct.unpack_from('%ds' % num, tuple_data[0], 1)[0]
    return list(channels)


def l2cap_disconn(chan_id):
    logging.debug("%s %r", l2cap_disconn.__name__, chan_id)

    iutctl = get_iut()

    data_ba = bytearray(chr(chan_id))

    iutctl.btp_socket.send(*L2CAP['disconnect'], data=data_ba)

    l2cap_command_rsp_succ(defs.L2CAP_DISCONNECT)


def l2cap_send_data(chan_id, val, val_mtp=None):
    logging.debug("%s %r %r %r", l2cap_send_data.__name__, chan_id, val,
                  val_mtp)

    iutctl = get_iut()

    if val_mtp:
        val *= int(val_mtp)

    val_ba = binascii.unhexlify(bytearray(val))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray(chr(chan_id))
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*L2CAP['send_data'], data=data_ba)

    stack = get_stack()
    stack.l2cap.tx(chan_id, val)


def l2cap_listen(psm, transport, mtu=0, response=0):
    logging.debug("%s %r %r", l2cap_le_listen.__name__, psm, transport)

    iutctl = get_iut()

    if type(psm) is str:
        psm = int(psm, 16)

    data_ba = bytearray(struct.pack('H', psm))
    data_ba.extend(struct.pack('B', transport))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('H', response))

    iutctl.btp_socket.send(*L2CAP['listen'], data=data_ba)

    l2cap_command_rsp_succ(defs.L2CAP_LISTEN)


def l2cap_le_listen(psm, mtu=0, response=0):
    l2cap_listen(psm, defs.L2CAP_TRANSPORT_LE, mtu, response)


def l2cap_reconfigure(bd_addr, bd_addr_type, mtu, channels):
    logging.debug("%s %r %r %r %r", l2cap_reconfigure.__name__,
                  bd_addr, bd_addr_type, mtu, channels)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', len(channels)))
    for chan in channels:
        data_ba.extend(struct.pack('B', chan))

    iutctl.btp_socket.send(*L2CAP['reconfigure'], data=data_ba)

    l2cap_command_rsp_succ(defs.L2CAP_RECONFIGURE)


def l2cap_connected_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_connected_ev.__name__, data, data_len)

    hdr_fmt = '<BHHHHHB6s'
    chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps, \
        bd_addr_type, bd_addr = struct.unpack_from(hdr_fmt, data)
    l2cap.connected(chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                    bd_addr_type, bd_addr)

    logging.debug("id:%r on psm:%r, peer_mtu:%r, peer_mps:%r, our_mtu:%r, "
                  "our_mps:%r, addr %r type %r",
                  chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                  bd_addr, bd_addr_type)


def l2cap_disconnected_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_disconnected_ev.__name__, data, data_len)

    hdr_fmt = '<HBHB6s'
    res, chan_id, psm, bd_addr_type, bd_addr = struct.unpack_from(hdr_fmt, data)
    result_str = l2cap_result_str[res]
    l2cap.disconnected(chan_id, psm, bd_addr_type, bd_addr, result_str)

    logging.debug("id:%r on psm:%r, addr %r type %r, res %r",
                  chan_id, psm, bd_addr, bd_addr_type, result_str)


def l2cap_data_rcv_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_data_rcv_ev.__name__, data, data_len)

    hdr_fmt = '<BH'
    hdr_len = struct.calcsize(hdr_fmt)

    chan_id, data_len = struct.unpack_from(hdr_fmt, data)
    data_rx = struct.unpack_from('%ds' % data_len, data, hdr_len)[0]
    l2cap.rx(chan_id, data_rx)

    logging.debug("id:%r, data:%s", chan_id, binascii.hexlify(data_rx))


def l2cap_reconfigured_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_reconfigured_ev.__name__, data, data_len)

    hdr_fmt = '<BHHHH'
    chan_id, peer_mtu, peer_mps, our_mtu, our_mps = \
        struct.unpack_from(hdr_fmt, data)
    l2cap.reconfigured(chan_id, peer_mtu, peer_mps, our_mtu, our_mps)
    logging.debug("id:%r, peer_mtu:%r, peer_mps:%r our_mtu:%r our_mps:%r",
                  chan_id, peer_mtu, peer_mps, our_mtu, our_mps)


L2CAP_EV = {
    defs.L2CAP_EV_CONNECTED: l2cap_connected_ev,
    defs.L2CAP_EV_DISCONNECTED: l2cap_disconnected_ev,
    defs.L2CAP_EV_DATA_RECEIVED: l2cap_data_rcv_ev,
    defs.L2CAP_EV_RECONFIGURED: l2cap_reconfigured_ev,
}


def gap_new_settings_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_new_settings_ev_.__name__, data)

    data_fmt = '<I'

    curr_set, = struct.unpack_from(data_fmt, data)

    __gap_current_settings_update(curr_set)


def gap_device_found_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_device_found_ev_.__name__, data)

    fmt = '<B6sBBH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    addr_type, addr, rssi, flags, eir_len = struct.unpack_from(fmt, data)
    eir = data[struct.calcsize(fmt):]

    if len(eir) != eir_len:
        raise BTPError("Invalid data length")

    addr = binascii.hexlify(addr[::-1]).lower()

    logging.debug("found %r type %r eir %r", addr, addr_type, eir)

    stack = get_stack()
    stack.gap.found_devices.data.append(LeAdv(addr_type, addr, rssi, flags,
                                              eir))


def gap_connected_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_connected_ev_.__name__, data)

    hdr_fmt = '<B6sHHH'
    hdr_len = struct.calcsize(hdr_fmt)

    addr_type, addr, itvl, latency, timeout = struct.unpack_from(hdr_fmt, data)
    addr = binascii.hexlify(addr[::-1])

    gap.connected.data = (addr, addr_type)
    gap.set_conn_params(ConnParams(itvl, latency, timeout))

    set_pts_addr(addr, addr_type)


def gap_disconnected_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_disconnected_ev_.__name__, data)

    gap.connected.data = None


def gap_passkey_disp_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_passkey_disp_ev_.__name__, data)

    fmt = '<B6sI'

    addr_type, addr, passkey = struct.unpack(fmt, data)
    addr = binascii.hexlify(addr[::-1])

    logging.debug("passkey = %r", passkey)

    gap.passkey.data = passkey


def gap_identity_resolved_ev_(gap, data, data_len):
    logging.debug("%s", gap_identity_resolved_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6sB6s'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _id_addr_t, _id_addr = struct.unpack_from(fmt, data)
    # Convert addresses to lower case
    _addr = binascii.hexlify(_addr[::-1]).lower()
    _id_addr = binascii.hexlify(_id_addr[::-1]).lower()

    if _addr_t != pts_addr_type_get() or _addr != pts_addr_get():
        raise BTPError("Received data mismatch")

    # Update RPA with Identity Address
    set_pts_addr(_id_addr, _id_addr_t)


def gap_conn_param_update_ev_(gap, data, data_len):
    logging.debug("%s", gap_conn_param_update_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6sHHH'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _itvl, _latency, _timeout = struct.unpack_from(fmt, data)
    # Convert addresses to lower case
    _addr = binascii.hexlify(_addr[::-1]).lower()

    if _addr_t != pts_addr_type_get() or _addr != pts_addr_get():
        raise BTPError("Received data mismatch")

    logging.debug("received %r", (_addr_t, _addr, _itvl, _latency, _timeout))

    gap.set_conn_params(ConnParams(_itvl, _latency, _timeout))


def gap_sec_level_changed_ev_(gap, data, data_len):
    logging.debug("%s", gap_sec_level_changed_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6sB'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _level = struct.unpack_from(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).decode()

    logging.debug("received %r", (_addr_t, _addr, _level))


def gap_pairing_consent_ev_(gap, data, data_len):
    logging.debug("%s", gap_pairing_consent_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6s'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, = struct.unpack_from(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).decode()

    logging.debug("received %r", (_addr_t, _addr))


GAP_EV = {
    defs.GAP_EV_NEW_SETTINGS: gap_new_settings_ev_,
    defs.GAP_EV_DEVICE_FOUND: gap_device_found_ev_,
    defs.GAP_EV_DEVICE_CONNECTED: gap_connected_ev_,
    defs.GAP_EV_DEVICE_DISCONNECTED: gap_disconnected_ev_,
    defs.GAP_EV_PASSKEY_DISPLAY: gap_passkey_disp_ev_,
    defs.GAP_EV_IDENTITY_RESOLVED: gap_identity_resolved_ev_,
    defs.GAP_EV_CONN_PARAM_UPDATE: gap_conn_param_update_ev_,
    defs.GAP_EV_SEC_LEVEL_CHANGED: gap_sec_level_changed_ev_,
    defs.GAP_EV_PAIRING_CONSENT_REQ: gap_pairing_consent_ev_,
}


def gatt_attr_value_changed_ev_(gatt, data, data_len):
    (handle, value) = gatts_dec_attr_value_changed_ev_data(data)
    logging.debug("%s %r %r", gatt_attr_value_changed_ev_.__name__,
                  handle, value)

    gatt.attr_value_set(handle, binascii.hexlify(value[0]))
    gatt.attr_value_set_changed(handle)


GATT_EV = {
    defs.GATT_EV_ATTR_VALUE_CHANGED: gatt_attr_value_changed_ev_,
}


def mesh_config_prov():
    logging.debug("%s", mesh_config_prov.__name__)

    iutctl = get_iut()

    stack = get_stack()

    uuid = binascii.unhexlify(stack.mesh.dev_uuid)
    static_auth = binascii.unhexlify(stack.mesh.static_auth)
    output_size = stack.mesh.output_size
    output_actions = stack.mesh.output_actions
    input_size = stack.mesh.input_size
    input_actions = stack.mesh.input_actions

    data = bytearray(struct.pack("<16s16sBHBH", uuid, static_auth, output_size,
                                 output_actions, input_size, input_actions))

    iutctl.btp_socket.send_wait_rsp(*MESH['config_prov'], data=data)


def mesh_prov_node():
    logging.debug("%s", mesh_config_prov.__name__)

    stack = get_stack()

    net_key = binascii.unhexlify(stack.mesh.net_key)
    dev_key = binascii.unhexlify(stack.mesh.dev_key)

    data = bytearray(struct.pack("<16sHBIIH16s", net_key,
                                 stack.mesh.net_key_idx, stack.mesh.flags,
                                 stack.mesh.iv_idx, stack.mesh.seq_num,
                                 stack.mesh.addr, dev_key))

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['prov_node'], data=data)


def mesh_init():
    logging.debug("%s", mesh_init.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['init'])

    stack = get_stack()

    stack.mesh.is_initialized = True
    if stack.mesh.iv_test_mode_autoinit:
        mesh_iv_update_test_mode(True)


def mesh_reset():
    logging.debug("%s", mesh_reset.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['reset'])

    stack = get_stack()

    stack.mesh.is_provisioned.data = False
    stack.mesh.is_initialized = True

def mesh_input_number(number):
    logging.debug("%s %r", mesh_input_number.__name__, number)

    iutctl = get_iut()

    if type(number) is str:
        number = int(number)

    data = bytearray(struct.pack("<I", number))

    iutctl.btp_socket.send_wait_rsp(*MESH['input_num'], data=data)


def mesh_input_string(string):
    logging.debug("%s %s", mesh_input_string.__name__, string)

    iutctl = get_iut()

    data = bytearray(string)

    iutctl.btp_socket.send_wait_rsp(*MESH['input_str'], data=data)


def mesh_iv_update_test_mode(enable):
    logging.debug("%s", mesh_iv_update_test_mode.__name__)

    iutctl = get_iut()

    if enable:
        data = bytearray(struct.pack("<B", 0x01))
    else:
        data = bytearray(struct.pack("<B", 0x00))

    iutctl.btp_socket.send_wait_rsp(*MESH['iv_update_test_mode'], data=data)

    stack = get_stack()
    stack.mesh.is_iv_test_mode_enabled.data = True


def mesh_iv_update_toggle():
    logging.debug("%s", mesh_iv_update_toggle.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MESH['iv_update_toggle'])
    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    if tuple_hdr.op == defs.BTP_STATUS:
        logging.info("IV Update in progress")


def mesh_net_send(ttl, src, dst, payload):
    logging.debug("%s %r %r %r %r", mesh_net_send.__name__, ttl, src, dst,
                  payload)

    if ttl is None:
        ttl = 0xff  # Use default TTL
    elif isinstance(ttl, str):
        ttl = int(ttl, 16)

    if isinstance(src, str):
        src = int(src, 16)

    if isinstance(dst, str):
        dst = int(dst, 16)

    payload = binascii.unhexlify(payload)
    payload_len = len(payload)

    if payload_len > 0xff:
        raise BTPError("Payload exceeds PDU")

    data = bytearray(struct.pack("<BHHB", ttl, src, dst, payload_len))
    data.extend(payload)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['net_send'], data=data)


def mesh_health_generate_faults():
    logging.debug("%s", mesh_health_generate_faults.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_generate_faults'])

    hdr_fmt = '<BBB'
    hdr_len = struct.calcsize(hdr_fmt)

    (test_id, cur_faults_cnt, reg_faults_cnt) = \
        struct.unpack_from(hdr_fmt, rsp)
    (cur_faults,) = struct.unpack_from('<%ds' % cur_faults_cnt, rsp, hdr_len)
    (reg_faults,) = struct.unpack_from('<%ds' % reg_faults_cnt, rsp,
                                       hdr_len + cur_faults_cnt)

    cur_faults = binascii.hexlify(cur_faults)
    reg_faults = binascii.hexlify(reg_faults)

    return test_id, cur_faults, reg_faults


def mesh_health_clear_faults():
    logging.debug("%s", mesh_health_clear_faults.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['mesh_clear_faults'])


def mesh_lpn(enable):
    logging.debug("%s %r", mesh_lpn.__name__, enable)

    if enable:
        enable = 0x01
    else:
        enable = 0x00

    data = bytearray(struct.pack("<B", enable))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn'], data=data)


def mesh_lpn_poll():
    logging.debug("%s", mesh_lpn_poll.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_poll'])


def mesh_model_send(src, dst, payload):
    logging.debug("%s %r %r %r", mesh_model_send.__name__, src, dst, payload)

    if isinstance(src, str):
        src = int(src, 16)

    if isinstance(dst, str):
        dst = int(dst, 16)

    payload = binascii.unhexlify(payload)
    payload_len = len(payload)

    if payload_len > 0xff:
        raise BTPError("Payload exceeds PDU")

    data = bytearray(struct.pack("<HHB", src, dst, payload_len))
    data.extend(payload)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['model_send'], data=data)


def mesh_lpn_subscribe(address):
    logging.debug("%s %r", mesh_lpn_subscribe.__name__, address)

    if isinstance(address, str):
        address = int(address, 16)

    data = bytearray(struct.pack("<H", address))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_subscribe'], data=data)


def mesh_lpn_unsubscribe(address):
    logging.debug("%s %r", mesh_lpn_unsubscribe.__name__, address)

    if isinstance(address, str):
        address = int(address, 16)

    data = bytearray(struct.pack("<H", address))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_unsubscribe'], data=data)


def mesh_rpl_clear():
    logging.debug("%s", mesh_rpl_clear.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['rpl_clear'])


def mesh_proxy_identity():
    logging.debug("%s", mesh_proxy_identity.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['proxy_identity'])


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
    stack = get_stack()

    mesh.is_provisioned.data = True

    if stack.mesh.proxy_identity:
        mesh_proxy_identity()


def mesh_prov_link_open_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_open_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('open', bearer)


def mesh_prov_link_closed_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_closed_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('closed', bearer)


def mesh_store_net_data():
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = True


def mesh_iv_test_mode_autoinit():
    stack = get_stack()

    stack.mesh.iv_test_mode_autoinit = True


def mesh_net_rcv_ev(mesh, data, data_len):
    stack = get_stack()

    if not stack.mesh.net_recv_ev_store.data:
        return

    logging.debug("%s %r %r", mesh_net_rcv_ev.__name__, data, data_len)

    hdr_fmt = '<BBHHB'
    hdr_len = struct.calcsize(hdr_fmt)

    (ttl, ctl, src, dst, payload_len) = struct.unpack_from(hdr_fmt, data, 0)
    (payload,) = struct.unpack_from('<%ds' % payload_len, data, hdr_len)
    payload = binascii.hexlify(payload)

    stack.mesh.net_recv_ev_data.data = (ttl, ctl, src, dst, payload)


def mesh_invalid_bearer_ev(mesh, data, data_len):
    stack = get_stack()

    logging.debug("%s %r %r", mesh_invalid_bearer_ev.__name__, data, data_len)

    hdr_fmt = '<B'
    hdr_len = struct.calcsize(hdr_fmt)

    (opcode,) = struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.prov_invalid_bearer_rcv.data = True


def mesh_incomp_timer_exp_ev(mesh, data, data_len):
    logging.debug("%s", mesh_incomp_timer_exp_ev.__name__)

    stack = get_stack()

    stack.mesh.incomp_timer_exp.data = True


MESH_EV = {
    defs.MESH_EV_OUT_NUMBER_ACTION: mesh_out_number_action_ev,
    defs.MESH_EV_OUT_STRING_ACTION: mesh_out_string_action_ev,
    defs.MESH_EV_IN_ACTION: mesh_in_action_ev,
    defs.MESH_EV_PROVISIONED: mesh_provisioned_ev,
    defs.MESH_EV_PROV_LINK_OPEN: mesh_prov_link_open_ev,
    defs.MESH_EV_PROV_LINK_CLOSED: mesh_prov_link_closed_ev,
    defs.MESH_EV_NET_RECV: mesh_net_rcv_ev,
    defs.MESH_EV_INVALID_BEARER: mesh_invalid_bearer_ev,
    defs.MESH_EV_INCOMP_TIMER_EXP: mesh_incomp_timer_exp_ev,
}


def event_handler(hdr, data):
    logging.debug("%s %r %r", event_handler.__name__, hdr, data)

    stack = get_stack()
    if not stack:
        logging.info("Stack not initialized")
        return False

    cb = None

    if hdr.svc_id == defs.BTP_SERVICE_ID_MESH:
        if hdr.op in MESH_EV and stack.mesh:
            cb = MESH_EV[hdr.op]
            cb(stack.mesh, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_L2CAP:
        if hdr.op in L2CAP_EV and stack.l2cap:
            cb = L2CAP_EV[hdr.op]
            cb(stack.l2cap, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_GAP:
        if hdr.op in GAP_EV and stack.gap:
            cb = GAP_EV[hdr.op]
            cb(stack.gap, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_GATT:
        if hdr.op in GATT_EV and stack.gatt:
            cb = GATT_EV[hdr.op]
            cb(stack.gatt, data[0], hdr.data_len)
            return True

    # TODO: Raise BTP error instead of logging
    logging.error("Unhandled event! svc_id %s op %s", hdr.svc_id, hdr.op)
    return False


def init(get_iut_method):
    global get_iut

    get_iut = get_iut_method
    set_event_handler(event_handler)
