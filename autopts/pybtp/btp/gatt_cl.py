#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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
import struct

from autopts.pybtp import defs
from autopts.pybtp.types import addr2btp_ba, Perm
from autopts.pybtp.btp.btp import btp_hdr_check, CONTROLLER_INDEX, \
    get_iut_method as get_iut, btp2uuid, clear_verify_values, \
    add_to_verify_values, get_verify_values
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.ptsprojects.stack import get_stack, GattCharacteristic

GATTC = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_GATTC,
                       defs.GATTC_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "exchange_mtu": (defs.BTP_SERVICE_ID_GATTC,
                     defs.GATTC_EXCHANGE_MTU,
                     CONTROLLER_INDEX),
    "disc_all_prim": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_DISC_ALL_PRIM,
                      CONTROLLER_INDEX),
    "disc_prim_uuid": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_DISC_PRIM_UUID,
                       CONTROLLER_INDEX),
    "find_included": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_FIND_INCLUDED,
                      CONTROLLER_INDEX),
    "disc_all_chrc": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_DISC_ALL_CHRC,
                      CONTROLLER_INDEX),
    "disc_chrc_uuid": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_DISC_CHRC_UUID,
                       CONTROLLER_INDEX),
    "disc_all_desc": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_DISC_ALL_DESC,
                      CONTROLLER_INDEX),
    "read": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_READ, CONTROLLER_INDEX),
    "read_uuid": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_READ_UUID,
                  CONTROLLER_INDEX),
    "read_long": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_READ_LONG,
                  CONTROLLER_INDEX),
    "read_multiple": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_READ_MULTIPLE,
                      CONTROLLER_INDEX),
    "write_without_rsp": (defs.BTP_SERVICE_ID_GATTC,
                          defs.GATTC_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "signed_write": (defs.BTP_SERVICE_ID_GATTC,
                     defs.GATTC_SIGNED_WRITE_WITHOUT_RSP, CONTROLLER_INDEX),
    "write": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_WRITE, CONTROLLER_INDEX),
    "write_long": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_WRITE_LONG,
                   CONTROLLER_INDEX),
    "write_reliable": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_WRITE_RELIABLE,
                       CONTROLLER_INDEX),
    "cfg_notify": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_CFG_NOTIFY,
                   CONTROLLER_INDEX),
    "cfg_indicate": (defs.BTP_SERVICE_ID_GATTC, defs.GATTC_CFG_INDICATE,
                     CONTROLLER_INDEX),
}


def gatt_cl_mtu_exchanged_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_mtu_exchanged_ev_.__name__, data)

    fmt = '<B6sB'

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1])

    gatt_cl.mtu_exchanged.data = (addr, addr_type, status)


def gatt_cl_dec_svc_attr(data):
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


def gatt_cl_dec_incl_attr(data):
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
    svc, svc_len = gatt_cl_dec_svc_attr(data[hdr_len:])

    return (incl_hdl, svc), hdr_len + svc_len


def gatt_cl_dec_chrc_attr(data):
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


def gatt_cl_dec_desc_attr(data):
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


def gatt_cl_dec_disc_rsp(data, attr_type):
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
            attr, attr_len = gatt_cl_dec_svc_attr(attrs[offset:])
        elif attr_type == "include":
            attr, attr_len = gatt_cl_dec_incl_attr(attrs[offset:])
        elif attr_type == "characteristic":
            attr, attr_len = gatt_cl_dec_chrc_attr(attrs[offset:])
        else:  # descriptor
            attr, attr_len = gatt_cl_dec_desc_attr(attrs[offset:])

        attrs_list.append(attr)
        offset += attr_len

    return attrs_list


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


def gatt_cl_disc_all_prim_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_disc_all_prim_rsp_ev_.__name__, data)

    fmt = '<B6sBB'

    addr_type, addr, status, svc_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r svc_cnt=%r",
                  gatt_cl_disc_all_prim_rsp_ev_.__name__,
                  addr_type, addr, status, svc_cnt)

    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.prim_svcs = []
    gatt_cl.prim_svcs_cnt = svc_cnt

    if svc_cnt == 0:
        logging.debug("No services in response")
        return

    svcs = gatt_cl_dec_disc_rsp(svcs_data, 'service')

    logging.debug("%s %r", gatt_cl_disc_all_prim_rsp_ev_.__name__, svcs)

    for svc in svcs:
        start_handle = "%04X" % (svc[0],)
        end_handle = "%04X" % (svc[1],)
        uuid = svc[2].upper()

        # avoid repeated service uuid, it should be verified only once
        if uuid not in gatt_cl.prim_svcs:
            gatt_cl.prim_svcs.append((start_handle, end_handle, uuid))


def gatt_cl_disc_prim_uuid_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_disc_prim_uuid_rsp_ev_.__name__, data)

    fmt = '<B6sBB'

    addr_type, addr, status, svc_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r svc_cnt=%r",
                  gatt_cl_disc_prim_uuid_rsp_ev_.__name__,
                  addr_type, addr, status, svc_cnt)

    # svcs_data contains service count and services - adjust data offset
    # to include count
    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.prim_svcs = []
    gatt_cl.prim_svcs_cnt = svc_cnt

    if svc_cnt == 0:
        logging.debug("No services in response")
        return

    svcs = gatt_cl_dec_disc_rsp(svcs_data, 'service')

    logging.debug("%s %r", gatt_cl_disc_prim_uuid_rsp_ev_.__name__, svcs)


    for svc in svcs:
        start_handle = "%04X" % (svc[0],)
        end_handle = "%04X" % (svc[1],)

        uuid = svc[2]

        # add hyphens to long uuid: 0000-1157-0000-0000-0123-4567-89AB-CDEF
        if len(uuid) > 4:
            uuid = "-".join([uuid[i:i + 4] for i in range(0, len(uuid), 4)])

        gatt_cl.prim_svcs.append((start_handle, end_handle, uuid))


def gatt_cl_find_incld_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_find_incld_rsp_ev_.__name__, data)

    fmt = '<B6sBB'

    addr_type, addr, status, svc_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r svc_cnt=%r",
                  gatt_cl_find_incld_rsp_ev_.__name__,
                  addr_type, addr, status, svc_cnt)

    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.incl_svcs = []
    gatt_cl.incl_svcs_cnt = svc_cnt

    if svc_cnt == 0:
        logging.debug("No services in response")
        return
    incl_tuples = gatt_cl_dec_disc_rsp(svcs_data, 'include')

    logging.debug("%s %r", gatt_cl_find_incld_rsp_ev_.__name__, incl_tuples)


    for incl in incl_tuples:
        att_handle = "%04X" % (incl[0][0],)
        inc_svc_handle = "%04X" % (incl[1][0],)
        end_grp_handle = "%04X" % (incl[1][1],)
        uuid = incl[1][2]

        gatt_cl.incl_svcs.append((att_handle,
                                inc_svc_handle,
                                end_grp_handle,
                                uuid))


def gatt_cl_disc_all_chrc_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_disc_all_chrc_rsp_ev_.__name__, data)
    attrs = []

    fmt = '<B6sBB'

    addr_type, addr, status, char_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r char_cnt=%r",
                  gatt_cl_disc_all_chrc_rsp_ev_.__name__,
                  addr_type, addr, status, char_cnt)

    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.chrcs = []
    gatt_cl.chrcs_cnt = char_cnt

    if char_cnt == 0:
        logging.debug("No characteristics in response")
        return

    chrcs = gatt_cl_dec_disc_rsp(svcs_data, 'characteristic')

    logging.debug("%s %r", gatt_cl_disc_all_chrc_rsp_ev_.__name__, chrcs)

    for chrc in chrcs:
        (handle, value_handle, prop, uuid) = chrc
        attrs.append(GattCharacteristic(handle=handle,
                                        perm=Perm.read,
                                        uuid=uuid,
                                        att_rsp=0,
                                        prop=prop,
                                        value_handle=value_handle))

    for attr in attrs:
        gatt_cl.chrcs.append((attr.value_handle, attr.uuid))


def gatt_cl_disc_chrc_uuid_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_disc_chrc_uuid_rsp_ev_.__name__, data)
    attrs = []

    fmt = '<B6sBB'

    addr_type, addr, status, char_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r char_cnt=%r",
                  gatt_cl_disc_chrc_uuid_rsp_ev_.__name__,
                  addr_type, addr, status, char_cnt)

    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.chrcs = []
    gatt_cl.chrcs_cnt = char_cnt

    if char_cnt == 0:
        logging.debug("No characteristics in response")
        return

    chrcs = gatt_cl_dec_disc_rsp(svcs_data, 'characteristic')

    logging.debug("%s %r", gatt_cl_disc_chrc_uuid_rsp_ev_.__name__, chrcs)

    for chrc in chrcs:
        (handle, value_handle, prop, uuid) = chrc
        attrs.append(GattCharacteristic(handle=handle,
                                        perm=Perm.read,
                                        uuid=uuid,
                                        att_rsp=0,
                                        prop=prop,
                                        value_handle=value_handle))

    for attr in attrs:
        gatt_cl.chrcs.append((attr.value_handle, attr.uuid))


def gatt_cl_disc_all_desc_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_disc_all_desc_rsp_ev_.__name__, data)

    fmt = '<B6sBB'

    addr_type, addr, status, char_cnt = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r char_cnt=%r",
                  gatt_cl_disc_all_desc_rsp_ev_.__name__,
                  addr_type, addr, status, char_cnt)

    svcs_data = data[struct.calcsize(fmt) - 1:]

    gatt_cl.dscs = []
    gatt_cl.dscs_cnt = char_cnt

    if char_cnt == 0:
        logging.debug("No descriptors in response")
        return

    descs = gatt_cl_dec_disc_rsp(svcs_data, 'descriptor')

    logging.debug("%s %r", gatt_cl_disc_all_desc_rsp_ev_.__name__, descs)

    gatt_cl.dscs = []
    gatt_cl.dscs_cnt = char_cnt

    for desc in descs:
        handle = "%04X" % (desc[0],)
        uuid = desc[1]
        gatt_cl.dscs.append((handle, uuid))


def gatt_cl_read_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_read_rsp_ev_.__name__, data)

    fmt = '<B6sBH'

    addr_type, addr, status, data_length = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r data_len=%r",
                  gatt_cl_read_rsp_ev_.__name__,
                  addr_type, addr, status, data_length)

    clear_verify_values()

    if data_length == 0:
        logging.debug("No data in response")
        return

    rp_data = data[struct.calcsize(fmt):]

    (value,) = struct.unpack_from('%ds' % data_length, rp_data)

    logging.debug("%s %r %r", gatt_cl_read_rsp_ev_.__name__, status, value)

    add_to_verify_values(att_rsp_str[status])

    add_to_verify_values((binascii.hexlify(value)).upper())

    logging.debug("Set verify values to: %r", get_verify_values())


def gatt_cl_read_uuid_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_read_uuid_rsp_ev_.__name__, data)

    fmt = '<B6sBHB'

    addr_type, addr, status, data_length, value_length = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r data_len=%r,"
                  "value_len=%r",
                  gatt_cl_read_uuid_rsp_ev_.__name__,
                  addr_type, addr, status, data_length, value_length)

    data_fmt = '>H%ds' % value_length
    tuple_len = struct.calcsize(data_fmt)
    tuple_data = data[struct.calcsize(fmt):]
    chrc_count = data_length // tuple_len

    offset = 0
    if chrc_count > 1:
        # received several pairs of {handle, data}
        clear_verify_values()
        for x in range(chrc_count):
            handle, value = struct.unpack_from(data_fmt, tuple_data, offset)
            logging.debug("%s %r %r",
                          gatt_cl_read_uuid_rsp_ev_.__name__,
                          handle, value)
            offset += tuple_len
            add_to_verify_values((handle, binascii.hexlify(value).upper()))
    else:
        # this might be continuation - check if data in verify_values
        # fits the format
        if get_verify_values() != []:
            if not (isinstance(get_verify_values()[0], tuple) and
                    isinstance(get_verify_values()[0][0], int) and
                    isinstance(get_verify_values()[0][1], bytes)):
                # verify_values doesn't match read_uuid_rp, let's clear it
                clear_verify_values()
        handle, value = struct.unpack_from(data_fmt, tuple_data)
        logging.debug("%s %r %r",
                      gatt_cl_read_uuid_rsp_ev_.__name__,
                      handle, value)
        add_to_verify_values((handle, binascii.hexlify(value).upper()))

    logging.debug("Set verify values to: %r", get_verify_values())


def gatt_cl_read_long_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_read_long_rsp_ev_.__name__, data)

    fmt = '<B6sBH'

    addr_type, addr, status, data_length = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r data_len=%r",
                  gatt_cl_read_long_rsp_ev_.__name__,
                  addr_type, addr, status, data_length)

    rp_data = data[struct.calcsize(fmt):]

    (value,) = struct.unpack_from('%ds' % data_length, rp_data)

    logging.debug("%s %r %r", gatt_cl_read_long_rsp_ev_.__name__, status, value)

    clear_verify_values()

    add_to_verify_values(att_rsp_str[status])

    add_to_verify_values((binascii.hexlify(value)).upper())

    logging.debug("Set verify values to: %r", get_verify_values())


def gatt_cl_read_mult_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_read_mult_rsp_ev_.__name__, data)

    fmt = '<B6sBH'

    addr_type, addr, status, data_length = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r data_len=%r",
                  gatt_cl_read_mult_rsp_ev_.__name__,
                  addr_type, addr, status, data_length)

    rp_data = data[struct.calcsize(fmt):]

    if data_length == 0:
        logging.debug("No data in response")
        return

    (value, ) = struct.unpack_from('%ds' % data_length, rp_data)

    logging.debug("%s %r %r", gatt_cl_read_mult_rsp_ev_.__name__, status, value)

    if (len(get_verify_values()) > 0 and not
        (isinstance(get_verify_values()[0][0], str) and
         isinstance(get_verify_values()[0][1], bytes))):
        clear_verify_values()

    add_to_verify_values((att_rsp_str[status],
                         (binascii.hexlify(value)).upper()))

    logging.debug("Set verify values to: %r", get_verify_values())


def gatt_cl_write_rsp_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_read_mult_rsp_ev_.__name__, data)

    fmt = '<B6sB'

    addr_type, addr, status = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r status=%r",
                  gatt_cl_read_mult_rsp_ev_.__name__,
                  addr_type, addr, status)
    gatt_cl.write_status = status


def gatt_cl_notification_rxed_ev_(gatt_cl, data, data_len):
    logging.debug("%s %r", gatt_cl_notification_rxed_ev_.__name__, data)

    fmt = '<B6sBHH'

    addr_type, addr, type, handle, data_length = \
        struct.unpack_from(fmt, data[:struct.calcsize(fmt)])
    logging.debug("%s received addr_type=%r addr=%r"
                  "type=%r handle=%r data_length=%r",
                  gatt_cl_read_mult_rsp_ev_.__name__,
                  addr_type, addr, type, handle, data_length)

    if data_length == 0:
        logging.debug("No data in response")
        return

    notification_data = binascii.hexlify(data[struct.calcsize(fmt):]).upper()

    # save type, handle, data
    gatt_cl.notifications.append((type, handle, notification_data))


GATTC_EV = {
    defs.GATTC_EV_MTU_EXCHANGED: gatt_cl_mtu_exchanged_ev_,
    defs.GATTC_DISC_ALL_PRIM_RP: gatt_cl_disc_all_prim_rsp_ev_,
    defs.GATTC_DISC_PRIM_UUID_RP: gatt_cl_disc_prim_uuid_rsp_ev_,
    defs.GATTC_FIND_INCLUDED_RP: gatt_cl_find_incld_rsp_ev_,
    defs.GATTC_DISC_ALL_CHRC_RP: gatt_cl_disc_all_chrc_rsp_ev_,
    defs.GATTC_DISC_CHRC_UUID_RP: gatt_cl_disc_chrc_uuid_rsp_ev_,
    defs.GATTC_DISC_ALL_DESC_RP: gatt_cl_disc_all_desc_rsp_ev_,
    defs.GATTC_READ_RP: gatt_cl_read_rsp_ev_,
    defs.GATTC_READ_UUID_RP: gatt_cl_read_uuid_rsp_ev_,
    defs.GATTC_READ_LONG_RP: gatt_cl_read_long_rsp_ev_,
    defs.GATTC_READ_MULTIPLE_RP: gatt_cl_read_mult_rsp_ev_,
    defs.GATTC_WRITE_RP: gatt_cl_write_rsp_ev_,
    defs.GATTC_WRITE_LONG_RP: gatt_cl_write_rsp_ev_,
    defs.GATTC_RELIABLE_WRITE_RP: gatt_cl_write_rsp_ev_,
    defs.GATTC_CFG_NOTIFY_RP: gatt_cl_write_rsp_ev_,
    defs.GATTC_CFG_INDICATE_RP: gatt_cl_write_rsp_ev_,
    defs.GATTC_EV_NOTIFICATION_RXED: gatt_cl_notification_rxed_ev_,
}


def gatt_cl_command_rsp_succ():
    logging.debug("%s", gatt_cl_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATTC)


def gatt_cl_exchange_mtu(bd_addr_type, bd_addr):
    logging.debug("%s %r %r", gatt_cl_exchange_mtu.__name__, bd_addr_type,
                  bd_addr)
    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GATTC['exchange_mtu'], data=data_ba)

    gatt_cl_command_rsp_succ()


def gatt_cl_disc_all_prim(bd_addr_type, bd_addr):
    logging.debug("%s %r %r", gatt_cl_disc_all_prim.__name__, bd_addr_type,
                  bd_addr)
    stack = get_stack()
    stack.gatt_cl.prim_svcs_cnt = None
    stack.gatt_cl.prim_svcs = []

    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*GATTC['disc_all_prim'], data=data_ba)

    gatt_cl_command_rsp_succ()


def gatt_cl_disc_prim_uuid(bd_addr_type, bd_addr, uuid):
    logging.debug("%s %r %r %r", gatt_cl_disc_prim_uuid.__name__, bd_addr_type,
                  bd_addr, uuid)
    stack = get_stack()
    stack.gatt_cl.prim_svcs_cnt = None
    stack.gatt_cl.prim_svcs = []

    iutctl = get_iut()

    gap_wait_for_connection()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    if "-" in uuid:
        uuid = uuid.replace("-", "")
    if uuid.startswith("0x"):
        uuid = uuid.replace("0x", "")
    uuid_ba = binascii.unhexlify(uuid)[::-1]

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send(*GATTC['disc_prim_uuid'], data=data_ba)

    gatt_cl_command_rsp_succ()


def gatt_cl_find_included(bd_addr_type, bd_addr, start_hdl, end_hdl):
    logging.debug("%s %r %r %r %r", gatt_cl_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    iutctl = get_iut()

    gap_wait_for_connection()

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

    gatt_cl_command_rsp_succ()


def gatt_cl_find_included(bd_addr_type, bd_addr, start_hdl, end_hdl):
    logging.debug("%s %r %r %r %r", gatt_cl_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, end_hdl)
    stack = get_stack()
    stack.gatt_cl.incl_svcs_cnt = None
    stack.gatt_cl.incl_svcs = []

    iutctl = get_iut()

    gap_wait_for_connection()

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

    gatt_cl_command_rsp_succ()


def gatt_cl_disc_all_chrc(bd_addr_type, bd_addr, start_hdl, stop_hdl, svc=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_disc_all_chrc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, svc)
    stack = get_stack()
    stack.gatt_cl.chrcs_cnt = None
    stack.gatt_cl.chrcs = []

    iutctl = get_iut()

    gap_wait_for_connection()

    if svc:
        svc_nb = svc[1]
        for s in stack.prim_svcs:
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

    gatt_cl_command_rsp_succ()


def gatt_cl_disc_chrc_uuid(bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gatt_cl_disc_chrc_uuid.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid)
    iutctl = get_iut()
    stack = get_stack()
    stack.gatt_cl.chrcs_cnt = None
    stack.gatt_cl.chrcs = []

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

    gatt_cl_command_rsp_succ()


def gatt_cl_disc_all_desc(bd_addr_type, bd_addr, start_hdl, stop_hdl):
    logging.debug("%s %r %r %r %r", gatt_cl_disc_all_desc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    stack = get_stack()
    stack.gatt_cl.dscs_cnt = None
    stack.gatt_cl.dscs = []

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

    gatt_cl_command_rsp_succ()


def gatt_cl_read(bd_addr_type, bd_addr, hdl):
    logging.debug("%s %r %r %r", gatt_cl_read.__name__, bd_addr_type, bd_addr,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_read_uuid(bd_addr_type, bd_addr, start_hdl, end_hdl, uuid):
    logging.debug("%s %r %r %r %r %r", gatt_cl_read_uuid.__name__, bd_addr_type,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_read_long(bd_addr_type, bd_addr, hdl, off, modif_off=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_read_long.__name__, bd_addr_type,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_read_multiple(bd_addr_type, bd_addr, *hdls):
    logging.debug("%s %r %r %r", gatt_cl_read_multiple.__name__, bd_addr_type,
                  bd_addr, hdls)
    iutctl = get_iut()

    gap_wait_for_connection()

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

    iutctl.btp_socket.send(*GATTC['read_multiple'], data=data_ba)

    gatt_cl_command_rsp_succ()


def gatt_cl_write_without_rsp(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_write_without_rsp.__name__,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_signed_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_signed_write.__name__,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_write(bd_addr_type, bd_addr, hdl, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_write.__name__, bd_addr_type,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_write_long(bd_addr_type, bd_addr, hdl, off, val, length=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_write_long.__name__,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_write_reliable(bd_addr_type, bd_addr, hdl, off, val, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", gatt_cl_write_reliable.__name__,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_cfg_notify(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gatt_cl_cfg_notify.__name__, bd_addr_type,
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

    gatt_cl_command_rsp_succ()


def gatt_cl_cfg_indicate(bd_addr_type, bd_addr, enable, ccc_hdl):
    logging.debug("%s %r %r, %r, %r", gatt_cl_cfg_indicate.__name__,
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

    gatt_cl_command_rsp_succ()
