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

from binascii import hexlify
from random import randint
from time import sleep
import logging
import re
import socket
import struct
import sys

from pybtp import btp
from pybtp.types import Prop, Perm, IOCap, UUID
from ptsprojects.testcase import MMI
from ptsprojects.stack import get_stack, GattPrimary, GattService, GattSecondary, GattServiceIncluded, \
    GattCharacteristic, GattCharacteristicDescriptor, GattDB

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", gatt_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e)


def gatt_wid_hdl_no_write_rsp_check(wid, description, test_case_name):
    if wid == 76:
        log("%s, %r, %r, %s", gatt_wid_hdl_no_write_rsp_check.__name__, wid, description,
            test_case_name)
        return hdl_wid_76_no_rsp_check(description)
    return gatt_wid_hdl(wid, description, test_case_name)


def gatt_server_fetch_db():
    db = GattDB()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    attrs = btp.gatts_get_attrs()
    for attr in attrs:
        handle, perm, type_uuid = attr

        attr_val = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not attr_val:
            logging.debug("cannot read value %r", handle)
            continue

        att_rsp, val_len, val = attr_val

        if type_uuid in ('2800', '2801'):
            uuid = btp.btp2uuid(val_len, val)

            if type_uuid == '2800':
                db.attr_add(handle, GattPrimary(handle, perm, uuid, att_rsp))
            else:
                db.attr_add(handle, GattSecondary(handle, perm, uuid, att_rsp))
        elif type_uuid == '2803':

            hdr = '<BH'
            hdr_len = struct.calcsize(hdr)
            uuid_len = val_len - hdr_len

            prop, value_handle, uuid = struct.unpack("<BH%ds" % uuid_len, val)
            uuid = btp.btp2uuid(uuid_len, uuid)

            db.attr_add(handle, GattCharacteristic(handle, perm, uuid, att_rsp, prop, value_handle))
        elif type_uuid == '2802':
            hdr = "<HH"
            hdr_len = struct.calcsize(hdr)
            uuid_len = val_len - hdr_len
            incl_svc_hdl, end_grp_hdl, uuid = struct.unpack(hdr + "%ds" % uuid_len, val)
            uuid = btp.btp2uuid(uuid_len, uuid)

            db.attr_add(handle, GattServiceIncluded(handle, perm, uuid, att_rsp, incl_svc_hdl, end_grp_hdl))
        else:
            uuid = type_uuid.replace("0x", "").replace("-", "").upper()

            db.attr_add(handle, GattCharacteristicDescriptor(handle, perm, uuid, att_rsp, val))

    return db


COMPARED_VALUE = []


# wid handlers section begin
def hdl_wid_1(desc):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_2(desc):
    btp.gap_conn()
    return True


def hdl_wid_3(desc):
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return True


def hdl_wid_4(desc):
    btp.gap_set_io_cap(IOCap.no_input_output)
    return True


def hdl_wid_10(desc):
    btp.gattc_disc_all_prim(btp.pts_addr_type_get(),
                            btp.pts_addr_get())
    btp.gattc_disc_all_prim_rsp()
    return True


def hdl_wid_11(desc):
    return True


def hdl_wid_12(desc):
    btp.gattc_exchange_mtu(btp.pts_addr_type_get(), btp.pts_addr_get())
    return True


def hdl_wid_15(desc):
    btp.gattc_find_included(btp.pts_addr_type_get(), btp.pts_addr_get(),
                            '0001', 'FFFF')

    btp.gattc_find_included_rsp(True)
    return True


def hdl_wid_16(desc):
    return True


def hdl_wid_17(desc):
    MMI.reset()
    MMI.parse_description(desc)
    pts_services = MMI.args
    if not pts_services:
        logging.error("%s parsing error", hdl_wid_17.__name__)
        return False

    iut_services = []

    # Get all primary services
    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        handle, perm, type_uuid = attr
        (_, uuid_len, uuid) = btp.gatts_get_attr_val(
            btp.pts_addr_type_get(),
            btp.pts_addr_get(), handle)
        uuid = btp.btp2uuid(uuid_len, uuid)
        iut_services.append(uuid)

    # Verification
    for service in pts_services:
        if service in iut_services:
            iut_services.remove(service)
            logging.debug("Service %s found", service)
            continue
        logging.error("Service %s not found", service)
        return False
    return True


def hdl_wid_18(desc):
    MMI.reset()
    MMI.parse_description(desc)

    uuid = MMI.args[0]

    if not uuid:
        logging.error("%s parsing error", hdl_wid_18.__name__)
        return False

    btp.gattc_disc_prim_uuid(btp.pts_addr_type_get(),
                             btp.pts_addr_get(),
                             uuid)

    btp.gattc_disc_prim_uuid_rsp(True)

    return True


def hdl_wid_19(desc):
    return btp.verify_description(desc)


def hdl_wid_21(desc):
    return btp.verify_description(desc)


def hdl_wid_20(desc):
    MMI.reset()
    MMI.parse_description(desc)

    uuid = MMI.args[0]

    if not uuid:
        logging.error("%s parsing error", hdl_wid_20.__name__)
        return False

    btp.gattc_disc_prim_uuid(btp.pts_addr_type_get(),
                             btp.pts_addr_get(),
                             uuid)

    btp.gattc_disc_prim_uuid_rsp(True)

    return True


def hdl_wid_22(desc):
    MMI.reset()
    MMI.parse_description(desc)

    parsed_args = []

    for arg in MMI.args:
        parsed_args.append([char for char in arg if char != "-"])

    handles = []
    uuids = []

    # Extract UUID's from parsed arguments
    uuids_from_parse = parsed_args[::3]

    # Delete unwanted UUID values
    del parsed_args[0::3]
    parsed_handles = parsed_args

    # Convert remaining arguments to integers
    parsed_handles = [int("".join(arg), 16) for arg in parsed_handles]

    # Increment every 2th handle
    parsed_handles[1::2] = [arg + 1 for arg in parsed_handles[1::2]]

    # Get all primary services
    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                     btp.pts_addr_get(), start_handle)
        if not val:
            continue

        (_, uuid_len, uuid) = val

        uuids.append(str(btp.btp2uuid(uuid_len, uuid)))
        handles.append(start_handle)

    for uuid in uuids_from_parse:
        if uuid in uuids_from_parse:
            logging.debug("UUUID %r present", uuid)
            continue
        logging.debug("UUID %r not present", uuid)
        return False

    for handle in parsed_handles:
        if handle in parsed_handles:
            logging.debug("Handle %r present", handle)
            continue
        logging.debug("Handle %r not present", handle)
        return False

    return True


def hdl_wid_23(desc):
    MMI.reset()
    MMI.parse_description(desc)

    pts_services = [[int(MMI.args[1], 16), int(MMI.args[2], 16), MMI.args[0]]]

    if not pts_services:
        logging.debug("parsing error")
        return False

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    iut_services = []

    # [start_hdl, end_hdl, uuid]
    iut_service = []

    # Get all primary services
    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        if iut_service:
            iut_service[1] = start_handle - 1
            iut_services.append(iut_service)
            iut_service = None

        val = btp.gatts_get_attr_val(bd_addr_type, bd_addr, start_handle)
        if not val:
            continue

        (_, uuid_len, uuid) = val
        iut_service = [start_handle, "unknown", btp.btp2uuid(uuid_len, uuid)]

    iut_services.append(iut_service)

    # Verification
    for service in pts_services:
        if service in iut_services:
            iut_services.remove(service)
            logging.debug("Service %r found", service)
            continue
        logging.error("Service %r not found", service)
        return False

    return True


def hdl_wid_24(desc):
    MMI.reset()
    MMI.parse_description(desc)

    db = gatt_server_fetch_db()

    if not MMI.args:
        return False

    incl_handle = int(MMI.args[1], 16)
    attr = db.attr_lookup_handle(incl_handle)
    if attr is None or not isinstance(attr, GattService):
        logging.error("service not found")
        return False

    incl_uuid = attr.uuid
    attr = db.attr_lookup_handle(int(MMI.args[0], 16))
    if attr is None or not isinstance(attr, GattServiceIncluded):
        logging.error("included not found")
        return False

    if attr.end_grp_hdl != int(MMI.args[2], 16) \
            or incl_uuid != MMI.args[3]:
        logging.error("end group handle not found")
        return False

    return True


def hdl_wid_25(desc):
    MMI.reset()
    MMI.parse_description(desc)

    pts_chrc_uuid = MMI.args[0]
    pts_chrc_handles = [int(MMI.args[1], 16), int(MMI.args[2], 16),
                        int(MMI.args[3], 16), int(MMI.args[4], 16)]

    iut_start_handle = None
    iut_end_handle = None

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    # Find pts_chrc_uuid service and it's handle range
    svcs = btp.gatts_get_attrs(type_uuid='2800')
    for svc in svcs:
        handle, perm, type_uuid = svc

        if iut_start_handle:
            iut_end_handle = handle - 1
            break

        svc_val = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not svc_val:
            continue

        att_rsp, uuid_len, uuid = svc_val
        if btp.btp2uuid(uuid_len, uuid) == pts_chrc_uuid:
            iut_start_handle = handle

    if iut_start_handle is None or iut_end_handle is None:
        logging.error("service %s not found", pts_chrc_uuid)
        return False

    iut_chrc_handles = []

    # Lookup all services within service range
    chrcs = btp.gatts_get_attrs(type_uuid='2803',
                                start_handle=iut_start_handle,
                                end_handle=iut_end_handle)
    for chrc in chrcs:
        handle, perm, type_uuid = chrc
        iut_chrc_handles.append(handle)

    if iut_chrc_handles != pts_chrc_handles:
        return False

    return True


def hdl_wid_26(desc):
    return btp.verify_description(desc)


def hdl_wid_27(desc):
    MMI.reset()
    MMI.parse_description(desc)

    start_hdl = MMI.args[1]
    end_hdl = MMI.args[2]

    if not start_hdl or not end_hdl:
        logging.error("parsing error")
        return False

    btp.gattc_disc_all_chrc(btp.pts_addr_type_get(), btp.pts_addr_get(),
                            start_hdl, end_hdl)

    btp.gattc_disc_all_chrc_rsp(True)

    return True


def hdl_wid_28(desc):
    return btp.verify_description(desc)


def hdl_wid_29(desc):
    MMI.reset()
    MMI.parse_description(desc)

    start_hdl = MMI.args[0]
    end_hdl = MMI.args[1]
    uuid = MMI.args[2]

    if not start_hdl or not end_hdl or not uuid:
        logging.error("parsing error")
        return False

    btp.gattc_disc_chrc_uuid(btp.pts_addr_type_get(),
                             btp.pts_addr_get(),
                             start_hdl, end_hdl, uuid)

    btp.gattc_disc_chrc_uuid_rsp(True)

    return True


def hdl_wid_30(desc):
    return btp.verify_description(desc)


def hdl_wid_31(desc):
    MMI.reset()
    MMI.parse_description(desc)

    start_hdl = MMI.args[0]
    end_hdl = MMI.args[1]

    if not start_hdl or not end_hdl:
        logging.error("parsing error")
        return False

    btp.gattc_disc_all_desc(btp.pts_addr_type_get(),
                            btp.pts_addr_get(),
                            start_hdl, end_hdl)

    btp.gattc_disc_all_desc_rsp(True)

    return True


def hdl_wid_32(desc):
    return btp.verify_description(desc)


def hdl_wid_34(desc):
    return True


def hdl_wid_40(desc):
    return btp.verify_description(desc)


def hdl_wid_41(desc):
    return btp.verify_description(desc)


def hdl_wid_42(desc):
    return btp.verify_description(desc)


def hdl_wid_43(desc):
    return btp.verify_description(desc)


def hdl_wid_44(desc):
    return btp.verify_description(desc)


def hdl_wid_45(desc):
    return btp.verify_description(desc)


def hdl_wid_46(desc):
    return btp.verify_description(desc)


def hdl_wid_47(desc):
    return btp.verify_description(desc)


def hdl_wid_48(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        hdl, 0, 1)

    btp.gattc_read_long_rsp(False, True)
    return True


def hdl_wid_49(desc):
    return True


def hdl_wid_50(desc):
    return btp.verify_description(desc)


def hdl_wid_51(desc):
    MMI.reset()
    MMI.parse_description(desc)

    uuid = MMI.args[0]
    start_hdl = MMI.args[1]
    end_hdl = MMI.args[2]

    if not uuid or not start_hdl or not end_hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        start_hdl, end_hdl, uuid)

    try:
        btp.gattc_read_uuid_rsp(True, True)
    except socket.timeout:
        pass

    return True


def hdl_wid_52(desc):
    MMI.reset()
    MMI.parse_description(desc)

    handle = int(MMI.args[0], 16)
    value = MMI.args[1]

    db = gatt_server_fetch_db()
    attr = db.attr_lookup_handle(handle)
    if attr is None:
        return False

    if not isinstance(attr, GattCharacteristicDescriptor):
        return False

    if attr.uuid == UUID.CEP:
        (value_read,) = struct.unpack("<H", attr.value)
        value_read = '{0:04x}'.format(value_read)
    else:
        value_read = hexlify(attr.value).upper()

    value_read = value_read.decode('utf-8')
    if value_read != value:
        return False

    return True


def hdl_wid_53(desc):
    MMI.reset()
    MMI.parse_description(desc)

    read_hdl = MMI.args[0]
    offset = MMI.args[1]

    if not read_hdl or not offset:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        read_hdl, offset, 1)

    btp.gattc_read_long_rsp(True, False)

    return True


def hdl_wid_55(desc):
    return btp.verify_multiple_read_description(desc)


def hdl_wid_56(desc):
    MMI.reset()
    MMI.parse_description(desc)

    if not MMI.args or len(MMI.args) != 3:
        logging.error("parsing error")

    handle1 = MMI.args[0]
    handle2 = MMI.args[1]
    values = MMI.args[2]

    values_read = ""

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    att_rsp, value_len, value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle1)
    values_read += value.hex()

    att_rsp, value_len, value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle2)
    values_read += value.hex()

    if values_read.upper() != values.upper():
        return False

    return True


def hdl_wid_57(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl1 = MMI.args[0]
    hdl2 = MMI.args[1]

    if not hdl1 or not hdl2:
        logging.error("parsing error")
        return False

    btp.gattc_read_multiple(btp.pts_addr_type_get(), btp.pts_addr_get(),
                            hdl1, hdl2)

    btp.gattc_read_multiple_rsp(True, True)

    return True


def hdl_wid_58(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)

    btp.gattc_read_rsp(True, True)

    return True


def hdl_wid_59(desc):
    return btp.verify_description(desc)


def hdl_wid_61(desc):
    return btp.verify_description(desc)


def hdl_wid_62(desc):
    return btp.verify_description(desc)


def hdl_wid_63(desc):
    return btp.verify_description(desc)


def hdl_wid_64(desc):
    return btp.verify_description(desc)


def hdl_wid_65(desc):
    return btp.verify_description(desc)


def hdl_wid_66(desc):
    return btp.verify_description(desc)


def hdl_wid_67(desc):
    return btp.verify_description(desc)


def hdl_wid_69(desc):
    MMI.reset()
    MMI.parse_description(desc)

    if not MMI.args:
        logging.error("parsing error")
        return False

    handle = int(MMI.args[0], 16)
    size = int(MMI.args[1], 10)

    btp.gattc_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         handle, 0, '12', size)

    btp.gattc_write_long_rsp()

    return True


def hdl_wid_70(desc):
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]
    size = int(params[1])

    btp.gattc_write_without_rsp(btp.pts_addr_type_get(),
                                btp.pts_addr_get(), handle, '12', size)

    return True


def hdl_wid_71(desc):
    return True


def hdl_wid_72(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.gattc_signed_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           hdl, '12', None)

    return True


def hdl_wid_74(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]
    size = int(MMI.args[1])

    if not hdl or size == 0:
        logging.error("parsing error")
        return False

    btp.gattc_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                    hdl, '12', size)

    try:
        btp.gattc_write_rsp(True, 40)
    except socket.timeout:
        pass

    return True


def hdl_wid_75(desc):
    MMI.reset()
    MMI.parse_description(desc)
    if not MMI.args:
        logging.debug("parsing error")

    handle = int(MMI.args[0], 16)
    value = int(MMI.args[1], 16)

    stack = get_stack()

    val = stack.gatt.wait_attr_value_changed(handle, 10)
    if val is None:
        return False

    val = int(val, 16)

    return val == value


def hdl_wid_76(desc):
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]
    off = int(params[1])

    btp.gattc_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         handle, off, '12', None)
    btp.gattc_write_long_rsp(True)

    return True


def hdl_wid_76_no_rsp_check(desc):
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]
    off = int(params[1])

    btp.gattc_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         handle, off, '12', None)

    return True


def hdl_wid_77(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]
    offset = int(MMI.args[1])

    if not hdl or not offset:
        logging.error("parsing error")
        return False

    btp.gattc_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         hdl, offset, '12', None)

    btp.gattc_write_long_rsp(True)

    return True


def hdl_wid_80(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]
    val_mtp = MMI.args[1]

    if not hdl or not val_mtp:
        logging.error("parsing error")
        return False

    btp.gattc_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                    hdl, '1234', val_mtp)

    btp.gattc_write_rsp(True)

    return True


def hdl_wid_81(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]
    val_mtp = MMI.args[1]

    if not hdl or not val_mtp:
        logging.error("parsing error")
        return False

    btp.gattc_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         hdl, 0, '1234', val_mtp)

    btp.gattc_write_long_rsp(True)

    return True


def hdl_wid_82(desc):
    return True


def hdl_wid_90(desc):
    btp.gattc_notification_ev(btp.pts_addr_get(),
                              btp.pts_addr_type_get(), 1)
    return True


def hdl_wid_91(desc):
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    btp.gattc_cfg_notify(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         1, handle)

    return True


def hdl_wid_92(desc):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    # This pattern is matching Notification handle
    pattern = re.compile(r"(handle)\s?=\s?'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    params = dict(params)
    handle = int(params.get('handle'), 16)
    att_rsp, value_len, value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)

    if att_rsp:
        logging.debug("cannot read chrc value")
        return False

    # delay to let the PTS subscribe for notifications
    sleep(2)

    btp.gatts_set_val(handle, hexlify(value))

    return True


def hdl_wid_95(desc):
    return True


def hdl_wid_96(desc):
    return True


def hdl_wid_97(desc):
    sleep(30)
    return True


def hdl_wid_98(desc):
    MMI.reset()
    MMI.parse_description(desc)
    if not MMI.args:
        logging.error("parsing error")
        return False

    handle = int(MMI.args[0], 16)
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    att_rsp, value_len, value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)

    if att_rsp:
        logging.debug("cannot read chrc value")
        return False

    # delay to let the PTS subscribe for notifications
    sleep(2)

    btp.gatts_set_val(handle, hexlify(value))

    return True


def hdl_wid_99(desc):
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    btp.gattc_cfg_indicate(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           1, handle)

    btp.gattc_notification_ev(btp.pts_addr_get(),
                              btp.pts_addr_type_get(), 2)

    return True


def hdl_wid_102(desc):
    pattern = re.compile(r"(ATTRIBUTE\sHANDLE|"
                         r"INCLUDED\sSERVICE\sATTRIBUTE\sHANDLE|"
                         r"END\sGROUP\sHANDLE|"
                         "UUID|"
                         "PROPERTIES|"
                         "HANDLE|"
                         r"SECONDARY\sSERVICE)\s?=\s?'([0-9a-fA-F]+)'", re.IGNORECASE)
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    params = {k.upper(): v for (k, v) in params}
    db = gatt_server_fetch_db()

    if "INCLUDED SERVICE ATTRIBUTE HANDLE" in params:
        incl_handle = int(params.get('INCLUDED SERVICE ATTRIBUTE HANDLE'), 16)
        attr = db.attr_lookup_handle(incl_handle)
        if attr is None or not isinstance(attr, GattService):
            logging.error("service not found")
            return False

        incl_uuid = attr.uuid
        attr = db.attr_lookup_handle(int(params.get('ATTRIBUTE HANDLE'), 16))
        if attr is None or not isinstance(attr, GattServiceIncluded):
            logging.error("included not found")
            return False

        if attr.end_grp_hdl != int(params.get('END GROUP HANDLE'), 16) \
                or incl_uuid != params.get('UUID').upper():
            return False

        return True

    if "PROPERTIES" in params:
        attr_handle = int(params.get('ATTRIBUTE HANDLE'), 16)
        attr = db.attr_lookup_handle(attr_handle)
        if attr is None or not isinstance(attr, GattCharacteristic):
            logging.error("characteristic not found")
            return False

        if attr.prop != int(params.get('PROPERTIES'), 16) \
                or attr.value_handle != int(params.get('HANDLE'), 16) \
                or attr.uuid != params.get('UUID').upper():
            return False

        return True

    if "SECONDARY SERVICE" in params:
        attr_handle = int(params.get('ATTRIBUTE HANDLE'), 16)
        attr = db.attr_lookup_handle(attr_handle)
        if attr is None:
            logging.error("characteristic not found")
            return False

        if not isinstance(attr, GattSecondary) or \
                attr.uuid != params.get('SECONDARY SERVICE').upper():
            return False

        return True

    return False


def hdl_wid_104(desc):
    pattern = re.compile(r"(ATTRIBUTE\sHANDLE|"
                         "VALUE|"
                         "FORMAT|"
                         "EXPONENT|"
                         "UINT|"
                         "NAMESPACE|"
                         r"DESCRIPTION)\s?=\s?'?([0-9a-fA-F]+)'?", re.IGNORECASE)
    params = pattern.findall(desc)
    if not params:
        logging.error("parsing error")
        return False

    params = {k.upper(): v for (k, v) in params}
    db = gatt_server_fetch_db()

    attr = db.attr_lookup_handle(int(params.get('ATTRIBUTE HANDLE'), 16))
    if attr is None or not isinstance(attr, GattCharacteristicDescriptor):
        logging.error("included not found")
        return False

    p_format = int(params.get('FORMAT'), 16)
    p_exponent = int(params.get('EXPONENT'), 16)
    p_uint = int(params.get('UINT'), 16)
    p_namespace = int(params.get('NAMESPACE'), 16)
    p_description = int(params.get('DESCRIPTION'), 16)

    i_format, i_exponent, i_uint, i_namespace, i_description = struct.unpack("<BBHBH", attr.value)

    if p_format != i_format \
            or p_exponent != i_exponent \
            or p_uint != i_uint \
            or p_namespace != i_namespace \
            or p_description != i_description:
        return False

    return True


def hdl_wid_107(desc):
    return True


def hdl_wid_108(desc):
    MMI.reset()
    MMI.parse_description(desc)

    uuid = MMI.args[0]

    if not uuid:
        logging.debug("parsing error")
        return False

    btp.gattc_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        "0001", "FFFF", uuid)

    try:
        btp.gattc_read_uuid_rsp(False, True)
    except socket.timeout:
        return False

    return True


def hdl_wid_109(desc):
    MMI.reset()
    MMI.parse_description(desc)

    uuid = MMI.args[0]

    if not uuid:
        logging.debug("parsing error")
        return False

    btp.gattc_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        "0001", "FFFF", uuid)

    try:
        btp.gattc_read_uuid_rsp(False, True)
    except socket.timeout:
        return False

    return True


def hdl_wid_110(desc):
    # Lookup characteristic handle that does not permit reading
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not prop & Prop.read:
            return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_111(desc):
    # Lookup characteristic UUID that does not permit reading
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not prop & Prop.read:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_112(desc):
    # Lookup characteristic handle that requires read authorization
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        (att_rsp, val_len, val) = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        # Check if returned ATT Insufficient Authorization error
        att_rsp, val_len, val = chrc_value_data
        if att_rsp != 8:
            continue

        return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_113(desc):
    # Lookup characteristic UUID that requires read authorization
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                           btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        att_rsp, val_len, val = chrc_value_data

        # Check if returned ATT Insufficient Authorization error
        if att_rsp != 8:
            continue

        return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_114(desc):
    # Lookup characteristic UUID that requires read authentication
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if perm & Perm.read_authn:
            return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_115(desc):
    # Lookup characteristic UUID that requires read authentication
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if perm & Perm.read_authn:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_118(desc):
    # Lookup invalid attribute handle
    handle = None

    attrs = btp.gatts_get_attrs()
    for attr in attrs:
        handle, perm, type_uuid = attr

    if handle is None:
        logging.error("No attribute found!")
        return "0000"

    return '{0:04x}'.format(handle + 1)


def hdl_wid_119(desc):
    # Lookup UUID that is not present on IUT GATT Server
    uuid_list = []

    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, uuid = struct.unpack("<BH%ds" % uuid_len, val)
        uuid_list.append(btp.btp2uuid(uuid_len, uuid))

    if len(uuid_list) == 0:
        logging.error("No attribute found!")
        return "0000"

    uuid_invalid = 1

    while True:
        if format(uuid_invalid).zfill(4) in uuid_list:
            uuid_invalid += 1
        else:
            uuid_invalid = format(uuid_invalid).zfill(4)
            break

    return uuid_invalid


def hdl_wid_120(desc):
    # Lookup characteristic handle that does not permit write
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.write or not prop & Prop.write:
            return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_121(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        (att_rsp, val_len, val) = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        # Check if returned ATT Insufficient Authorization error
        att_rsp, val_len, val = chrc_value_data
        if att_rsp != 0x0c:
            continue

        return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_122(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                           btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        att_rsp, val_len, val = chrc_value_data

        # Check if returned ATT Insufficient Authorization error
        if att_rsp != 0x0c:
            continue

        return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_130(desc):
    return True


def hdl_wid_132(desc):
    rnd = randint(1000, 9999)
    btp.gatts_add_svc(0, str(rnd))
    btp.gatts_start_server()
    return True


def hdl_wid_133(desc):
    return True


def hdl_wid_134(desc):
    return True


def hdl_wid_135(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.gattc_write(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                    hdl, '01', 1)
    return True


def hdl_wid_136(desc):
    btp.gatts_add_svc(0, UUID.VND16_2)
    btp.gatts_start_server()
    return True


def hdl_wid_137(desc):
    return True


def hdl_wid_138(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    read_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    COMPARED_VALUE.append(read_val)

    return True


def hdl_wid_140(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl1 = MMI.args[0]
    hdl2 = MMI.args[1]
    btp.gattc_read_multiple_var(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl1, hdl2)
    return '0000'


def hdl_wid_141(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl1 = MMI.args[0]
    hdl2 = MMI.args[1]
    btp.gattc_read_multiple(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl1, hdl2)
    return '0000'


def hdl_wid_142(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.gattc_write(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                    hdl, '02', 1)
    return True


def hdl_wid_144(desc):
    """
    Please initiate one L2CAP channel disconnection to the PTS.
    """
    # TODO: This requires disconnecting one of EATT channels while EATT is being enabled -
    # we would need to access these channels via bttester API, have them saved and receive
    # callbacks from them (like for regular L2CAP server)
    return False


def hdl_wid_139(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    read_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    return bool(read_val == COMPARED_VALUE[0])


def hdl_wid_151(desc):
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                           btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not perm & Perm.write:
            continue

        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, _ = chrc_value_data
        if val_len == 1:
            return '{0:04x}'.format(handle)

    return False


def hdl_wid_152(desc):
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                           btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not perm & Perm.write:
            continue

        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, _ = chrc_value_data
        if val_len == 300:
            return '{0:04x}'.format(handle)

    return False


def hdl_wid_304(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]
    val = MMI.args[1]
    _, _, data = btp.gatts_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    data = hexlify(data).decode().upper()
    return bool(data in val)


def hdl_wid_400(desc):
    return True


def hdl_wid_502(desc):
    return True


def hdl_wid_2000(desc):
    stack = get_stack()

    passkey = stack.gap.passkey.data
    stack.gap.passkey.data = None

    return passkey
