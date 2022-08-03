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

import binascii
import logging
import re
import struct
from random import randint

from autopts.ptsprojects.stack import get_stack, ConnParams
from autopts.pybtp import defs
from autopts.pybtp.types import BTPError, gap_settings_btp2txt, addr2btp_ba, Addr, OwnAddrType, AdDuration
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get, btp_hdr_check, CONTROLLER_INDEX, set_pts_addr, LeAdv, \
    get_iut_method as get_iut

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
    "passkey_confirm_rsp": (defs.BTP_SERVICE_ID_GAP,
                            defs.GAP_PASSKEY_CONFIRM,
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
    "reset": (defs.BTP_SERVICE_ID_GAP, defs.GAP_RESET, CONTROLLER_INDEX, ""),
    "set_filter_accept_list": (defs.BTP_SERVICE_ID_GAP,
                               defs.GAP_SET_FILTER_ACCEPT_LIST, CONTROLLER_INDEX),
    "set_privacy_on": (defs.BTP_SERVICE_ID_GAP,
                       defs.GAP_SET_PRIVACY, CONTROLLER_INDEX, 1),
    "set_privacy_off": (defs.BTP_SERVICE_ID_GAP,
                        defs.GAP_SET_PRIVACY, CONTROLLER_INDEX, 0),
    "set_sc_only_on": (defs.BTP_SERVICE_ID_GAP,
                       defs.GAP_SET_SC_ONLY, CONTROLLER_INDEX, 1),
    "set_sc_only_off": (defs.BTP_SERVICE_ID_GAP,
                        defs.GAP_SET_SC_ONLY, CONTROLLER_INDEX, 0),
    "set_sc_on": (defs.BTP_SERVICE_ID_GAP,
                  defs.GAP_SET_SC, CONTROLLER_INDEX, 1),
    "set_sc_off": (defs.BTP_SERVICE_ID_GAP,
                   defs.GAP_SET_SC, CONTROLLER_INDEX, 0),
    "set_min_enc_key_size": (defs.BTP_SERVICE_ID_GAP,
                             defs.GAP_SET_MIN_ENC_KEY_SIZE, CONTROLLER_INDEX),
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

    addr_type, addr, itvl, latency, timeout = struct.unpack_from(hdr_fmt, data)
    addr = binascii.hexlify(addr[::-1])

    if gap.connected.data is None:
        gap.connected.data = [(addr, addr_type)]
    else:
        gap.connected.data.append((addr, addr_type))
    gap.set_conn_params(ConnParams(itvl, itvl, latency, timeout))

    set_pts_addr(addr, addr_type)


def gap_disconnected_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_disconnected_ev_.__name__, data)

    gap.sec_level = 0
    gap.connected.data = None


def gap_passkey_disp_ev_(gap, data, data_len):
    logging.debug("%s %r", gap_passkey_disp_ev_.__name__, data)

    fmt = '<B6sI'

    addr_type, addr, passkey = struct.unpack(fmt, data)
    addr = binascii.hexlify(addr[::-1])

    # unpacking passkey to int loses leading 0s,
    # let's add them back if lost
    passkey = str(passkey).zfill(6)

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

    if _addr_t != pts_addr_type_get() or _addr.decode('utf-8') != pts_addr_get():
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

    if _addr_t != pts_addr_type_get() or _addr.decode('utf-8') != pts_addr_get():
        raise BTPError("Received data mismatch")

    logging.debug("received %r", (_addr_t, _addr, _itvl, _latency, _timeout))

    gap.set_conn_params(ConnParams(_itvl, _itvl, _latency, _timeout))


def gap_sec_level_changed_ev_(gap, data, data_len):
    logging.debug("%s", gap_sec_level_changed_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6sB'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _level = struct.unpack_from(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).decode()

    gap.sec_level = _level

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


def gap_pairing_failed_ev_(gap, data, data_len):
    stack = get_stack()
    logging.debug("%s", gap_pairing_failed_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6sB'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, _reason = struct.unpack_from(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).decode()

    logging.debug("received %r", (_addr_t, _addr, _reason))

    stack.gap.pairing_failed_rcvd.data = (_addr_t, _addr, _reason)


def gap_bond_lost_ev_(gap, data, data_len):
    logging.debug("%s", gap_bond_lost_ev_.__name__)

    logging.debug("received %r", data)

    fmt = '<B6s'
    if len(data) != struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    _addr_t, _addr, = struct.unpack_from(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).decode()

    logging.debug("received %r", (_addr_t, _addr))
    gap.bond_lost_ev_data.data = (_addr_t, _addr)


def gap_passkey_confirm_req_ev_(gap, data, data_len):
    logging.debug("%s", gap_passkey_confirm_req_ev_.__name__)
    iutctl = get_iut()

    fmt = '<B6sI'

    # Unpack and swap address

    _addr_type, _addr, _passkey = struct.unpack(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).lower().decode('utf-8')

    passkey = str(_passkey).zfill(6)

    logging.debug("passkey = %r", passkey)

    gap.passkey.data = passkey


def gap_passkey_entry_req_ev_(gap, data, data_len):
    logging.debug("%s", gap_passkey_entry_req_ev_.__name__)
    iutctl = get_iut()

    fmt = '<B6s'

    # Unpack and swap address
    _addr_type, _addr = struct.unpack(fmt, data)
    _addr = binascii.hexlify(_addr[::-1]).lower().decode('utf-8')

    gap.passkey.data = randint(0, 999999)


GAP_EV = {
    defs.GAP_EV_NEW_SETTINGS: gap_new_settings_ev_,
    defs.GAP_EV_DEVICE_FOUND: gap_device_found_ev_,
    defs.GAP_EV_DEVICE_CONNECTED: gap_connected_ev_,
    defs.GAP_EV_DEVICE_DISCONNECTED: gap_disconnected_ev_,
    defs.GAP_EV_PASSKEY_DISPLAY: gap_passkey_disp_ev_,
    defs.GAP_EV_PASSKEY_ENTRY_REQ: gap_passkey_entry_req_ev_,
    defs.GAP_EV_PASSKEY_CONFIRM_REQ: gap_passkey_confirm_req_ev_,
    defs.GAP_EV_IDENTITY_RESOLVED: gap_identity_resolved_ev_,
    defs.GAP_EV_CONN_PARAM_UPDATE: gap_conn_param_update_ev_,
    defs.GAP_EV_SEC_LEVEL_CHANGED: gap_sec_level_changed_ev_,
    defs.GAP_EV_PAIRING_CONSENT_REQ: gap_pairing_consent_ev_,
    defs.GAP_EV_PAIRING_FAILED: gap_pairing_failed_ev_,
    defs.GAP_EV_BOND_LOST: gap_bond_lost_ev_,
}


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


def gap_wait_for_pairing_fail(timeout=30):
    stack = get_stack()

    return stack.gap.gap_wait_for_pairing_fail(timeout)


def gap_wait_for_lost_bond(timeout=30):
    stack = get_stack()

    return stack.gap.gap_wait_for_lost_bond(timeout)


def gap_wait_for_sec_lvl_change(level, timeout=30):
    stack = get_stack()

    return stack.gap.gap_wait_for_sec_lvl_change(level, timeout)


def gap_adv_ind_on(ad=None, sd=None, duration=AdDuration.forever, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", gap_adv_ind_on.__name__, ad, sd)

    if ad is None:
        ad = {}
    if sd is None:
        sd = {}

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return

    iutctl = get_iut()

    data_ba = bytearray()
    ad_ba = bytearray()
    sd_ba = bytearray()
    data = bytearray()

    for ad_type, ad_data in list(ad.items()):
        if isinstance(ad_data, str):
            data = bytes.fromhex(ad_data)
        elif isinstance(ad_data, bytes):
            data = ad_data

        ad_ba.extend(bytes([ad_type]))
        ad_ba.extend(chr(len(data)).encode('utf-8'))
        ad_ba.extend(data)

    for sd_type, sd_data in list(sd.items()):
        if not isinstance(sd_data, bytes):
            try:
                data = bytes.fromhex(sd_data)
            except TypeError:
                data = bytes.fromhex(sd_data.decode('utf-8'))
        else:
            data = sd_data
        sd_ba.extend(bytes([sd_type]))
        sd_ba.extend(chr(len(data)).encode('utf-8'))
        sd_ba.extend(data)

    data_ba.extend(chr(len(ad_ba)).encode('utf-8'))
    data_ba.extend(chr(len(sd_ba)).encode('utf-8'))
    data_ba.extend(ad_ba)
    data_ba.extend(sd_ba)
    data_ba.extend(struct.pack("<I", duration))
    data_ba.extend(chr(own_addr_type).encode('utf-8'))

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


def gap_direct_adv_on(addr, addr_type, high_duty=0, peer_rpa=0):
    logging.debug("%s %r %r", gap_direct_adv_on.__name__, addr, high_duty)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_ADVERTISING]):
        return

    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(addr)
    data_ba.extend(chr(addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    opts = 0
    if high_duty:
        opts |= defs.GAP_START_DIRECT_ADV_HD

    if peer_rpa:
        opts |= defs.GAP_START_DIRECT_ADV_PEER_RPA

    data_ba.extend(struct.pack('H', opts))

    iutctl.btp_socket.send(*GAP['start_direct_adv'], data=data_ba)

    tuple_data = gap_command_rsp_succ(defs.GAP_START_DIRECT_ADV)
    __gap_current_settings_update(tuple_data)


def gap_conn(bd_addr=None, bd_addr_type=None, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", gap_conn.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    own_addr_type_ba = chr(own_addr_type).encode('utf-8')

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(own_addr_type_ba)

    iutctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()


def set_filter_accept_list(address_list=None):
    """ Send tuples (address_type, address) to IUT
        and save them to the filter accept list.
        If address_list=None, PTS's (type, address) will be sent.

        Arguments:
        address_list -- address type and address as tuples:
            address_list = [(0, 'DB:F5:72:56:C9:EF'), (0, 'DB:F5:72:56:C9:EF')]
    """
    logging.debug("%s %s", set_filter_accept_list.__name__, address_list)
    iutctl = get_iut()

    data_ba = bytearray()

    if not address_list:
        address_list = [(pts_addr_type_get(None), pts_addr_get(None))]

    addr_cnt_ba = chr(len(address_list)).encode('utf-8')
    data_ba.extend(addr_cnt_ba)

    for type, addr in address_list:
        bd_addr_type_ba = chr(type).encode('utf-8')
        bd_addr_ba = addr2btp_ba(addr)
        data_ba.extend(bd_addr_type_ba)
        data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['set_filter_accept_list'], data=data_ba)

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

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(own_addr_type).encode('utf-8'))

    iutctl.btp_socket.send(*GAP['conn'], data=data_ba)

    gap_command_rsp_succ()
    return True


def gap_disconn(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_disconn.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    stack = get_stack()

    if not stack.gap.is_connected(0):
        return

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['disconn'], data=data_ba)

    gap_command_rsp_succ()


def verify_not_connected(description):
    logging.debug("%s", verify_not_connected.__name__)
    stack = get_stack()

    gap_wait_for_connection(5)

    if stack.gap.is_connected(0):
        return False
    return True


def gap_set_io_cap(io_cap):
    logging.debug("%s %r", gap_set_io_cap.__name__, io_cap)
    iutctl = get_iut()
    stack = get_stack()
    stack.gap.io_cap = io_cap

    iutctl.btp_socket.send(*GAP['set_io_cap'], data=chr(io_cap))

    gap_command_rsp_succ()


def gap_pair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_pair.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['pair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ()


def gap_unpair(bd_addr=None, bd_addr_type=None):
    logging.debug("%s %r %r", gap_unpair.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GAP['unpair'], data=data_ba)

    # Expected result
    gap_command_rsp_succ(defs.GAP_UNPAIR)


def gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey):
    logging.debug("%s %r %r", gap_passkey_entry_rsp.__name__, bd_addr,
                  bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    if isinstance(passkey, str):
        passkey = int(passkey, 32)

    passkey_ba = struct.pack('I', passkey)
    data_ba.extend(passkey_ba)

    iutctl.btp_socket.send(*GAP['passkey_entry_rsp'], data=data_ba)

    gap_command_rsp_succ()


def gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey):
    logging.debug("%s %r %r", gap_passkey_confirm_rsp.__name__, bd_addr,
                  bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    if isinstance(passkey, str):
        passkey = int(passkey)

    match = int(passkey == int(get_stack().gap.get_passkey()))

    data_ba.extend(chr(match).encode('utf-8'))

    iutctl.btp_socket.send(*GAP['passkey_confirm_rsp'], data=data_ba)

    gap_command_rsp_succ()


def gap_reset():
    logging.debug("%s", gap_reset.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*GAP['reset'])

    gap_command_rsp_succ()


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


def gap_start_discov(transport='le', discov_type='active', mode='general'):
    """GAP Start Discovery function.

    Possible options (key: <values>):

    transport: <le, bredr>
    discov_type: <active, passive>
    mode: <general, limited, observe>

    """
    logging.debug("%s", gap_start_discov.__name__)

    iutctl = get_iut()

    flags = 0

    if transport == "le":
        flags |= defs.GAP_DISCOVERY_FLAG_LE
    else:
        flags |= defs.GAP_DISCOVERY_FLAG_BREDR

    if discov_type == "active":
        flags |= defs.GAP_DISCOVERY_FLAG_LE_ACTIVE_SCAN

    if mode == "limited":
        flags |= defs.GAP_DISCOVERY_FLAG_LIMITED
    elif mode == "observe":
        flags |= defs.GAP_DISCOVERY_FLAG_LE_OBSERVE

    stack = get_stack()
    stack.gap.reset_discovery()

    iutctl.btp_socket.send(*GAP['start_discov'], data=chr(flags))

    gap_command_rsp_succ()


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
    logging.debug("IUT address %r %r", stack.gap.iut_addr_get_str(),
                  "random" if stack.gap.iut_addr_is_random() else "public")

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
    logging.debug("%s %r %r 0x%04x 0x%04x 0x%04x 0x%04x", gap_conn_param_update.__name__,
                  bd_addr, bd_addr_type, conn_itvl_min, conn_itvl_max, conn_latency, supervision_timeout)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(chr(pts_addr_type_get(bd_addr_type)).encode('utf-8'))
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
    r, c = bytes.hex(r[::-1]), bytes.hex(c[::-1])

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


def gap_set_privacy_on():
    logging.debug("%s", gap_set_privacy_on.__name__)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_PRIVACY]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_privacy_on'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_privacy_off():
    logging.debug("%s", gap_set_privacy_off.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_PRIVACY]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_privacy_off'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_sc_only_on():
    logging.debug("%s", gap_set_sc_only_on.__name__)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_SC_ONLY]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_sc_only_on'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_sc_only_off():
    logging.debug("%s", gap_set_sc_only_off.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_SC_ONLY]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_sc_only_off'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_min_enc_key_size(enc_key_size):
    logging.debug("%s %r", gap_set_min_enc_key_size.__name__,
                  enc_key_size)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(chr(enc_key_size).encode('utf-8'))

    iutctl.btp_socket.send(*GAP['set_min_enc_key_size'], data=data_ba)

    gap_command_rsp_succ()


def gap_set_sc_on():
    logging.debug("%s", gap_set_sc_on.__name__)

    stack = get_stack()

    if stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_SC]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_sc_on'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def gap_set_sc_off():
    logging.debug("%s", gap_set_sc_off.__name__)

    stack = get_stack()

    if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_SC]):
        return

    iutctl = get_iut()

    iutctl.btp_socket.send(*GAP['set_sc_off'])

    tuple_data = gap_command_rsp_succ()
    __gap_current_settings_update(tuple_data)


def check_discov_results(addr_type=None, addr=None, discovered=True, eir=None):
    addr = pts_addr_get(addr).encode('utf-8')
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


def check_scan_rep_and_rsp(report, response):
    stack = get_stack()
    devices = stack.gap.found_devices.data

    # remove trailing zeros
    report = report.rstrip('0').upper()
    response = response.rstrip('0').upper()
    if len(report) % 2 != 0:
        report += '0'
    if len(response) % 2 != 0:
        response += '0'

    for device in devices:
        eir = str(binascii.hexlify(device.eir)).lstrip('b\'').rstrip('\'').upper()
        if report in eir and response in eir:
            return True
    return False
