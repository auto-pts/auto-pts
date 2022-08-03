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
import struct

from autopts.ptsprojects.stack import GattCharacteristic
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import btp_hdr_check, CONTROLLER_INDEX, get_iut_method as get_iut, btp2uuid, \
    clear_verify_values, add_to_verify_values, get_verify_values, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.pybtp.types import BTPError, addr2btp_ba
from autopts.pybtp.types import Perm, att_rsp_str

#  Global temporary objects
GATT_SVCS = None

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
    "notify_mult": (defs.BTP_SERVICE_ID_GATT,
                    defs.GATT_NOTIFY_MULTIPLE, CONTROLLER_INDEX),
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
    'eatt_connect': (defs.BTP_SERVICE_ID_GATT, defs.GATT_EATT_CONNECT,
                     CONTROLLER_INDEX),
}


def gatt_attr_value_changed_ev_(gatt, data, data_len):
    (handle, value) = gatts_dec_attr_value_changed_ev_data(data)
    logging.debug("%s %r %r", gatt_attr_value_changed_ev_.__name__,
                  handle, value)

    gatt.attr_value_set(handle, binascii.hexlify(value[0]))
    gatt.attr_value_set_changed(handle)


def gatt_notification_ev_(gatt, data, data_len):
    (addr_type, addr, notification_type, handle, value) = gattc_dec_notification_ev_data(data)
    logging.debug("%s %r %r %r %r %r", gatt_notification_ev_.__name__,
                  addr_type, addr, notification_type, handle, value)

    gatt.notification_ev_recv(addr_type, addr, notification_type, handle, value)


GATT_EV = {
    defs.GATT_EV_ATTR_VALUE_CHANGED: gatt_attr_value_changed_ev_,
    defs.GATT_EV_NOTIFICATION: gatt_notification_ev_,
}


def gatts_add_svc(svc_type, uuid):
    logging.debug("%s %r %r", gatts_add_svc.__name__, svc_type, uuid)

    iutctl = get_iut()

    data_ba = bytearray()
    uuid_ba = bytes.fromhex(uuid.replace("-", ""))

    data_ba.extend(chr(svc_type).encode('utf-8'))
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTS['add_svc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_inc_svc(hdl):
    logging.debug("%s %r", gatts_add_inc_svc.__name__, hdl)

    iutctl = get_iut()

    if isinstance(hdl, str):
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

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_ba = bytes.fromhex(uuid.replace("-", ""))

    data_ba.extend(hdl_ba)
    if isinstance(prop, int):
        data_ba.extend(bytes([prop]))
    else:
        data_ba.extend(chr(prop).encode('utf-8'))

    if isinstance(perm, int):
        data_ba.extend(bytes([perm]))
    else:
        data_ba.extend(chr(perm).encode('utf-8'))

    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTS['add_char'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_set_val(hdl, val):
    logging.debug("%s %r %r ", gatts_set_val.__name__, hdl, val)

    iutctl = get_iut()

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    if isinstance(val, str):
        val_ba = binascii.unhexlify(bytearray(val, 'utf-8'))
    elif isinstance(val, bytes):
        val_ba = binascii.unhexlify(val)
    else:
        val_ba = binascii.unhexlify(bytearray(val.encode('utf-8')))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTS['set_val'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_add_desc(hdl, perm, uuid):
    logging.debug("%s %r %r %r", gatts_add_desc.__name__, hdl, perm, uuid)

    iutctl = get_iut()

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_ba = binascii.unhexlify(uuid.replace("-", ""))[:: -1]

    data_ba.extend(hdl_ba)

    if isinstance(perm, int):
        data_ba.extend(bytes([perm]))
    else:
        data_ba.extend(chr(perm).encode('utf-8'))

    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTS['add_desc'], data=data_ba)

    gatt_command_rsp_succ()


def gatts_change_database(start_hdl, end_hdl, vis):
    logging.debug("%s %r %r %r", gatts_change_database.__name__, start_hdl, end_hdl, vis)

    iutctl = get_iut()

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    if isinstance(end_hdl, str):
        end_hdl = int(end_hdl, 16)

    data_ba = bytearray()
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)
    data_ba.extend(chr(vis).encode('utf-8'))

    iutctl.btp_socket.send(*GATTS['change_database'], data=data_ba)

    gatt_command_rsp_succ()

def gatts_notify_mult(bd_addr_type, bd_addr, cnt, handles):
    logging.debug("%s %r %r", gatts_notify_mult.__name__, cnt, handles)

    iutctl = get_iut()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', cnt))
    for h in handles:
        data_ba.extend(struct.pack('H', h))

    iutctl.btp_socket.send(*GATTS['notify_mult'], data=data_ba)

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

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(enc_key_size).encode('utf-8'))

    iutctl.btp_socket.send(*GATTS['set_enc_key_size'], data=data_ba)

    gatt_command_rsp_succ()


def gattc_dec_notification_ev_data(frame):
    fmt = '<B6sBHH'
    if len(frame) < struct.calcsize(fmt):
        raise BTPError("Invalid data length")

    addr_type, addr, notification_type, handle, data_len = struct.unpack_from(fmt, frame)
    data = frame[struct.calcsize(fmt):]

    if len(data) != data_len:
        raise BTPError("Invalid data length")

    addr = binascii.hexlify(addr[::-1]).lower().decode()

    return addr_type, addr, notification_type, handle, data


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

    if isinstance(start_handle, str):
        start_handle = int(start_handle, 16)

    start_hdl_ba = struct.pack('H', start_handle)
    data_ba.extend(start_hdl_ba)

    if isinstance(end_handle, str):
        end_handle = int(end_handle, 16)

    end_hdl_ba = struct.pack('H', end_handle)
    data_ba.extend(end_hdl_ba)

    if type_uuid:
        uuid_ba = bytes.fromhex(type_uuid.replace("-", ""))
        # uuid_ba has bytes in reverse order, must bew swapped
        uuid_ba = uuid_ba[::-1]
        data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
        data_ba.extend(uuid_ba)
    else:
        data_ba.extend(chr(0).encode('utf-8'))

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
    if isinstance(handle, str):
        handle = int(handle, 16)

    hdl_ba = struct.pack('H', handle)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_prim'], data=data_ba)


def gattc_disc_prim_uuid(bd_addr_type, bd_addr, uuid):
    logging.debug("%s %r %r %r", gattc_disc_prim_uuid.__name__, bd_addr_type,
                  bd_addr, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    uuid_ba = bytes.fromhex(uuid.replace("-", ""))[::-1]

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['disc_prim_uuid'], data=data_ba)


def _gattc_find_included_req(bd_addr_type, bd_addr, start_hdl, end_hdl):
    logging.debug("%s %r %r %r %r", _gattc_find_included_req.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    iutctl = get_iut()

    if isinstance(end_hdl, str):
        end_hdl = int(end_hdl, 16)

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    incls_list = gatt_dec_disc_rsp(tuple_data[0], "include")
    logging.debug("%s %r", gattc_find_included_rsp.__name__, incls_list)

    for incl in incls_list:
        att_handle = "%04X" % (incl[0][0],)
        inc_svc_handle = "%04X" % (incl[1][0],)
        end_grp_handle = "%04X" % (incl[1][1],)
        uuid = incl[1][2]

        add_to_verify_values(att_handle)
        add_to_verify_values(inc_svc_handle)
        add_to_verify_values(end_grp_handle)
        add_to_verify_values(uuid)

    logging.debug("Set verify values to: %r", get_verify_values())


def gattc_find_included(bd_addr_type, bd_addr, start_hdl=None, end_hdl=None):
    logging.debug("%s %r %r %r %r", gattc_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    gap_wait_for_connection()

    if start_hdl and end_hdl:
        _gattc_find_included_req(bd_addr_type, bd_addr, start_hdl, end_hdl)
        return

    gattc_disc_all_prim(bd_addr_type, bd_addr)
    svcs_tuple = gattc_disc_all_prim_rsp()


    clear_verify_values()

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

    chars_list = gatt_dec_disc_rsp(tuple_data[0], "characteristic")

    for char in chars_list:
        for exp_char in exp_chars:
            # Check if option expected attribute parameters match
            # TODO: Use class and a comparison method
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

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    if isinstance(stop_hdl, str):
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_chrc'], data=data_ba)


def gattc_disc_chrc_uuid(bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gattc_disc_chrc_uuid.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    if isinstance(stop_hdl, str):
        stop_hdl = int(stop_hdl, 16)

    if isinstance(start_hdl, str):
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

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['disc_chrc_uuid'], data=data_ba)


def gattc_disc_all_desc(bd_addr_type, bd_addr, start_hdl, stop_hdl):
    logging.debug("%s %r %r %r %r", gattc_disc_all_desc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    iutctl = get_iut()

    gap_wait_for_connection()

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    if isinstance(stop_hdl, str):
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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
    if isinstance(hdl, str):
        hdl = int(hdl, 16)
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    iutctl.btp_socket.send(*GATTC['read'], data=data_ba)


def gattc_read_uuid(bd_addr_type, bd_addr, start_hdl, end_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gattc_read_uuid.__name__, bd_addr_type,
                  bd_addr, start_hdl, end_hdl, uuid)
    iutctl = get_iut()

    gap_wait_for_connection()

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    if isinstance(end_hdl, str):
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

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['read_uuid'], data=data_ba)


def gattc_read_long(bd_addr_type, bd_addr, hdl, off, modif_off=None):
    logging.debug("%s %r %r %r %r %r", gattc_read_long.__name__, bd_addr_type,
                  bd_addr, hdl, off, modif_off)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    if isinstance(off, str):
        off = int(off, 16)
    if modif_off:
        off += modif_off
    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)

    iutctl.btp_socket.send(*GATTC['read_long'], data=data_ba)


def _create_read_multiple_req(bd_addr_type, bd_addr, *hdls):
    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdls_j = ''.join(hdl for hdl in hdls)
    hdls_byte_table = [hdls_j[i:i + 2] for i in range(0, len(hdls_j), 2)]
    hdls_swp = ''.join([c[1] + c[0] for c in zip(hdls_byte_table[::2],
                                                 hdls_byte_table[1::2])])
    hdls_ba = binascii.unhexlify(hdls_swp)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(hdls)).encode('utf-8'))
    data_ba.extend(hdls_ba)
    return data_ba

def gattc_read_multiple(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gattc_read_multiple.__name__, bd_addr_type,
                  bd_addr, hdls)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = _create_read_multiple_req(bd_addr_type, bd_addr, *hdls)
    iutctl.btp_socket.send(*GATTC['read_multiple'], data=data_ba)


def gattc_read_multiple_var(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gattc_read_multiple_var.__name__, bd_addr_type,
                  bd_addr, hdls)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = _create_read_multiple_req(bd_addr_type, bd_addr, *hdls)
    iutctl.btp_socket.send(*GATTC['read_multiple_var'], data=data_ba)


def gattc_write_without_rsp(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_without_rsp.__name__,
                  bd_addr_type, bd_addr, hdl, val, val_mtp)
    iutctl = get_iut()

    gap_wait_for_connection()

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(val.encode("utf-8"))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    if isinstance(val, str):
        val_ba = binascii.unhexlify(bytearray(val, 'utf-8'))
    elif isinstance(val, bytearray):
        val_ba = binascii.unhexlify(val)
    else:
        val_ba = binascii.unhexlify(bytearray(val.encode('utf-8')))
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    val_ba = binascii.unhexlify(val)
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTC['write'], data=data_ba)


def gattc_write_long(bd_addr_type, bd_addr, hdl, off, val, length=None):
    logging.debug("%s %r %r %r %r %r", gattc_write_long.__name__,
                  bd_addr_type, hdl, off, val, length)
    gap_wait_for_connection()

    if isinstance(hdl, str):
        hdl = int(hdl, 16)  # convert string in hex format to int

    if isinstance(off, str):
        off = int(off, 16)

    if length:
        val *= int(length)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)
    val_ba = bytes.fromhex(val)
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    if isinstance(hdl, str):
        hdl = int(hdl, 16)

    if val_mtp:
        val *= int(val_mtp)

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    hdl_ba = struct.pack('H', hdl)

    off_ba = struct.pack('H', off)
    val_ba = binascii.unhexlify(val)
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
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

    if isinstance(ccc_hdl, str):
        ccc_hdl = int(ccc_hdl, 16)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable).encode('utf-8'))
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

    if isinstance(ccc_hdl, str):
        ccc_hdl = int(ccc_hdl, 16)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(bd_addr)
    ccc_hdl_ba = struct.pack('H', ccc_hdl)

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(enable).encode('utf-8'))
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

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(ev_type).encode('utf-8'))

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

    # TODO: Use types instead of tuples

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

    return attrs_list


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


def gatt_dec_read_uuid_rsp(data):
    """Decodes Read UUID Response data.
    """
    offset = 0

    hdr = '<BB'
    hdr_len = struct.calcsize(hdr)

    att_rsp, val_count = struct.unpack_from(hdr, data, offset)
    offset += hdr_len
    char_values = []

    for i in range(val_count):
        hdr = '<HB'
        hdr_len = struct.calcsize(hdr)
        handle, data_len = struct.unpack_from(hdr, data, offset)
        offset += hdr_len
        val = struct.unpack_from('%ds' % data_len, data, offset)[0]
        offset += data_len

        char_values.append((handle, val))

    return att_rsp, char_values


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

    svcs_list = gatt_dec_disc_rsp(tuple_data[0], "service")

    for svc in svcs_list:
        for exp_svc in exp_svcs:
            # Check if option expected attribute parameters match
            # TODO: Use class and a comparison method
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

    svcs_list = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_all_prim_rsp.__name__, svcs_list)

    if store_rsp:  
        clear_verify_values()

        for svc in svcs_list:
            # Keep just UUID since PTS checks only UUID.
            uuid = svc[2].upper()

            # avoid repeated service uuid, it should be verified only once
            if uuid not in get_verify_values():
                add_to_verify_values(uuid)

        logging.debug("Set verify values to: %r", get_verify_values())

    return svcs_list


def gattc_disc_prim_uuid_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_prim_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_PRIM_UUID)

    svcs_list = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_prim_uuid_rsp.__name__, svcs_list)

    if store_rsp:
        clear_verify_values()

        for svc in svcs_list:
            start_handle = "%04X" % (svc[0],)
            end_handle = "%04X" % (svc[1],)

            uuid = svc[2]

            # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
            if len(uuid) > 4:
                uuid = "-".join([uuid[i:i + 4] for i in range(0, len(uuid), 4)])

            add_to_verify_values(start_handle)
            add_to_verify_values(end_handle)

            # avoid repeated service uuid, it should be verified only once, for
            # example:
            # gattc_disc_prim_uuid_rsp ((1, 3, ('\xc9N',)),
            # (48, 50, ('\xc9N',)), (64, 66, ('\xc9N',)),
            # (80, 82, ('\xc9N',)), (144, 150, ('\xc9N',)))
            if uuid not in get_verify_values():
                add_to_verify_values(uuid)

        logging.debug("Set verify values to: %r", get_verify_values())


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
        clear_verify_values()

        for incl in incls_tuple:
            att_handle = "%04X" % (incl[0][0],)
            inc_svc_handle = "%04X" % (incl[1][0],)
            end_grp_handle = "%04X" % (incl[1][1],)
            uuid = incl[1][2]

            add_to_verify_values(att_handle)
            add_to_verify_values(inc_svc_handle)
            add_to_verify_values(end_grp_handle)
            add_to_verify_values(uuid)

        logging.debug("Set verify values to: %r", get_verify_values())


def gattc_disc_all_chrc_rsp(store_rsp=False):
    iutctl = get_iut()
    attrs = []

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_chrc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_CHRC)

    chrcs_list = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_all_chrc_rsp.__name__, chrcs_list)

    for chrc in chrcs_list:
        (handle, value_handle, prop, uuid) = chrc
        attrs.append(GattCharacteristic(handle=handle,
                                        perm=Perm.read,
                                        uuid=uuid,
                                        att_rsp=0,
                                        prop=prop,
                                        value_handle=value_handle))

    if store_rsp:
        clear_verify_values()

        for attr in attrs:
            add_to_verify_values("%04X" % attr.handle)

        logging.debug("Set verify values to: %r", get_verify_values())

    return attrs


def gattc_disc_chrc_uuid_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_chrc_uuid_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_CHRC_UUID)

    chrcs_list = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_chrc_uuid_rsp.__name__, chrcs_list)

    if store_rsp:
        clear_verify_values()

        for chrc in chrcs_list:
            handle = "%04X" % (chrc[1],)
            uuid = chrc[3]

            # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
            if len(uuid) > 4:
                uuid = "-".join([uuid[i:i + 4] for i in range(0, len(uuid), 4)])

            add_to_verify_values(handle)
            add_to_verify_values(uuid)

        logging.debug("Set verify values to: %r", get_verify_values())


def gattc_disc_all_desc_rsp(store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_desc_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_DISC_ALL_DESC)

    descs_list = gatt_dec_disc_rsp(tuple_data[0], "descriptor")
    logging.debug("%s %r", gattc_disc_all_desc_rsp.__name__, descs_list)

    if store_rsp:
        clear_verify_values()

        for desc in descs_list:
            handle = "%04X" % (desc[0],)
            uuid = desc[1]
            add_to_verify_values(handle)
            add_to_verify_values(uuid)

        logging.debug("Set verify values to: %r", get_verify_values())


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
        clear_verify_values()

        if store_rsp:
            add_to_verify_values(att_rsp_str[rsp])

        if store_val:
            add_to_verify_values(binascii.hexlify(value[0]).decode().upper())


def gattc_read_uuid_rsp(store_rsp=False, store_val=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_uuid_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_UUID)

    rsp, char_values = gatt_dec_read_uuid_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_uuid_rsp.__name__, rsp, char_values)

    if store_rsp or store_val:
        clear_verify_values()

        if store_rsp:
            add_to_verify_values(att_rsp_str[rsp])

        if not store_val:
            return

        for char_handle, char_data in char_values:
            char_data = binascii.hexlify(char_data).decode().upper()
            add_to_verify_values('{0:0>4X}'.format(char_handle))
            add_to_verify_values(char_data)


def gattc_read_long_rsp(store_rsp=False, store_val=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_long_rsp.__name__, tuple_hdr,
                  tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT, defs.GATT_READ_LONG)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_long_rsp.__name__, rsp, value)

    if store_rsp or store_val:
        clear_verify_values()

        if store_rsp:
            add_to_verify_values(att_rsp_str[rsp])

        if store_val:
            add_to_verify_values((binascii.hexlify(value[0])).decode().upper())


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
        clear_verify_values()

        if store_rsp:
            add_to_verify_values(att_rsp_str[rsp])

        if store_val:
            add_to_verify_values((binascii.hexlify(values[0])).decode().upper())

def gattc_read_multiple_var_rsp(store_val=False, store_rsp=False):
    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_multiple_var_rsp.__name__,
                  tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.GATT_READ_MULTIPLE_VAR)

    rsp, values = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_multiple_var_rsp.__name__, rsp, values)

    if store_rsp or store_val:
        clear_verify_values()

        if store_rsp:
            add_to_verify_values(att_rsp_str[rsp])

        if store_val:
            add_to_verify_values((binascii.hexlify(values[0])).decode().upper())

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
        clear_verify_values()
        add_to_verify_values(att_rsp_str[rsp])


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
        clear_verify_values()
        add_to_verify_values(att_rsp_str[rsp])


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
        clear_verify_values()
        add_to_verify_values(att_rsp_str[rsp])

def eatt_conn(bd_addr, bd_addr_type, num=1):
    logging.debug("%s %r %r", eatt_conn.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()
    gap_wait_for_connection()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', num))

    iutctl.btp_socket.send(*GATTC['eatt_connect'], data=data_ba)
