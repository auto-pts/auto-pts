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

import logging
import re
import socket
import struct
import sys
import time
from binascii import hexlify
from time import sleep

from ptsprojects.stack import get_stack
from ptsprojects.testcase import MMI
from pybtp import btp
from pybtp.types import Prop, Perm, IOCap

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", gatt_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e.message)


# wid handlers section begin
def hdl_wid_1(desc):
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on()
    return True


def hdl_wid_2(desc):
    btp.gap_conn()
    return True


def hdl_wid_3(desc):
    time.sleep(2)
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
    sleep(10)
    return True


def hdl_wid_15(desc):
    btp.gattc_find_included(btp.pts_addr_type_get(), btp.pts_addr_get(),
                            None, None)
    return True


def hdl_wid_16(desc):
    return True


def hdl_wid_17(desc):
    MMI.reset()
    MMI.parse_description(desc)

    iut_services = []

    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        handle, perm, type_uuid = attr
        (_, uuid_len, uuid) = btp.gatts_get_attr_val(
            btp.pts_addr_type_get(),
            btp.pts_addr_get(), handle)
        uuid = btp.btp2uuid(uuid_len, uuid)
        iut_services.append(uuid)

    if iut_services == MMI.args:
        return True
    else:
        return False


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
        parsed_args.append(filter(lambda char: char != "-", arg))

    handles = []
    uuids = []

    # Extract UUID's from parsed arguments
    uuids_from_parse = parsed_args[::3]

    # Delete unwanted UUID values
    del parsed_args[0::3]
    parsed_handles = parsed_args

    # Convert remaining arguments to integers
    parsed_handles = [int(arg, 16) for arg in parsed_handles]

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
        else:
            logging.debug("UUID %r not present", uuid)
            return False
    for handle in parsed_handles:
        if handle in parsed_handles:
            logging.debug("Handle %r present", handle)
            continue
        else:
            logging.debug("Handle $r not present", handle)
            return False

    return True


def hdl_wid_23(desc):
    MMI.reset()
    MMI.parse_description(desc)

    pts_services = [[int(MMI.args[1], 16), int(MMI.args[2], 16), MMI.args[0]]]

    if not pts_services:
        logging.debug("parsing error")
        return False

    iut_services = []

    # [start_hdl, end_hdl, uuid]
    iut_service = None

    # Get all primary services
    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        if iut_service is not None:
            iut_service[1] = start_handle - 1
            iut_services.append(iut_service)
            iut_service = None

        val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                     btp.pts_addr_get(), start_handle)
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
        else:
            logging.error("Service %r not found", service)
            return False

    return True


def hdl_wid_24(desc):
    MMI.reset()
    MMI.parse_description(desc)

    # Include service in description should have 3 parameters:
    # Attribute Handle, Included Service Attribute Handle and End Group Handle
    num_includes = len(MMI.args) / 3

    pts_services = []

    for i in range(num_includes):
        pts_services.append([int(MMI.args[i+0], 16),
                             int(MMI.args[i+1], 16),
                             int(MMI.args[i+2], 16)])

    iut_services = []

    # Get all Included services
    attrs = btp.gatts_get_attrs(type_uuid='2802')
    for attr in attrs:
        handle, perm, type_uuid = attr

        val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                     btp.pts_addr_get(), handle)
        if not val:
            continue

        (_, val_len, attr_value) = val

        hdr = '<HH'
        hdr_len = struct.calcsize(hdr)
        data_len = val_len - hdr_len
        incl_hdl, end_hdl, _ = struct.unpack(hdr + '%ds' % data_len, attr_value)
        iut_services.append([handle, incl_hdl, end_hdl])

    # Verification
    for service in pts_services:
        if service in iut_services:
            iut_services.remove(service)
            logging.debug("Service %r found", service)
            continue
        else:
            logging.error("Service %r not found", service)
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

    # Find pts_chrc_uuid service and it's handle range
    svcs = btp.gatts_get_attrs(type_uuid='2800')
    for svc in svcs:
        handle, perm, type_uuid = svc

        if iut_start_handle:
            iut_end_handle = handle - 1
            break

        svc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                         btp.pts_addr_get(), handle)
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

    btp.gattc_disc_all_desc(btp.pts_addr_type_get(), btp.pts_addr_get(),
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


def hdl_wid_45(desc):
    return btp.verify_description(desc)


def hdl_wid_44(desc):
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

    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(),
                   hdl)

    try:
        btp.gattc_read_rsp(True, True, 40)
    except socket.timeout:
        pass

    return True


def hdl_wid_49(desc):
    sleep(30)
    return True


def hdl_wid_50(desc):
    return btp.verify_description(desc)


def hdl_wid_51(desc):
    MMI.reset()
    MMI.parse_description(desc)

    btp.gattc_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        MMI.args[1], MMI.args[2], MMI.args[0])

    btp.gattc_read_uuid_rsp(True)

    return True


def hdl_wid_52(desc):
    MMI.reset()
    MMI.parse_description(desc)

    handle = int(MMI.args[0], 16)

    _, _, value = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                         btp.pts_addr_get(), handle)

    value_read = hexlify(value)

    if value_read == MMI.args[1]:
        return True
    else:
        return False


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

    att_rsp, value_len, value = btp.gatts_get_attr_val(
        btp.pts_addr_type_get(),
        btp.pts_addr_get(), handle1)
    values_read += hexlify(value)

    att_rsp, value_len, value = btp.gatts_get_attr_val(
        btp.pts_addr_type_get(),
        btp.pts_addr_get(), handle2)
    values_read += hexlify(value)

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
    size = int(MMI.args[1], 16)

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
    value = MMI.args[1]

    sleep(5)

    attr = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                  btp.pts_addr_get(), handle)

    _, _, val = attr

    parsed_val = hexlify(val).upper()

    if value == parsed_val:
        return True
    else:
        return False


def hdl_wid_76(desc):
    MMI.reset()
    MMI.parse_description(desc)

    btp.gattc_write_reliable(btp.pts_addr_type_get(),
                             btp.pts_addr_get(),
                             MMI.args[0], 0, '12', MMI.args[1])

    btp.gattc_write_reliable_rsp(True)

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
                         hdl, offset, '12', offset + 2)

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
    val_mtp = int(MMI.args[1], 16)

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
    sleep(2)
    return True


def hdl_wid_95(desc):
    return True


def hdl_wid_96(desc):
    return True


def hdl_wid_97(desc):
    sleep(30)
    return True


def hdl_wid_98(desc):
    sleep(5)
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


def hdl_wid_107(desc):
    return True


def hdl_wid_108(desc):
    MMI.reset()
    MMI.parse_description(desc)

    btp.gattc_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                        0x0001, 0xffff, MMI.args[0])

    btp.gattc_read_uuid_rsp(True, True)

    return True


def hdl_wid_109(desc):
    return hdl_wid_108(desc)


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
        if not (perm & Perm.read):
            return '{0:04x}'.format(handle, 'x')

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
        if not (perm & Perm.read) or not (prop & Prop.read):
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

        return '{0:04x}'.format(handle, 'x')

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
            return '{0:04x}'.format(handle, 'x')

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
    return '{0:04x}'.format(65000, 'x')


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
        if format(uuid_invalid, 'x').zfill(4) in uuid_list:
            uuid_invalid += 1
        else:
            uuid_invalid = format(uuid_invalid, 'x').zfill(4)
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
        if not (perm & Perm.write) or not (prop & Prop.write):
            return '{0:04x}'.format(handle, 'x')

    return '0000'


def hdl_wid_121(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    # TODO This needs reworking
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

        if perm & Perm.write_enc and perm & Perm.read_enc:
            return '{0:04x}'.format(handle, 'x')

    return '0000'


def hdl_wid_122(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    # TODO This needs reworking
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

        if perm & Perm.read and perm & Perm.read_enc:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_2000(desc):
    stack = get_stack()

    passkey = stack.gap.passkey.data
    stack.gap.passkey.data = None

    return passkey
