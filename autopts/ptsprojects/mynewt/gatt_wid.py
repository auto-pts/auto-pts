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
import struct
import sys
import time
from binascii import hexlify

from autopts.pybtp import btp
from autopts.pybtp.types import Perm
from autopts.wid.gatt import gatt_wid_hdl as gen_wid_hdl
from autopts.ptsprojects.testcase import MMI
from autopts.ptsprojects.stack import get_stack
from autopts.wid.gatt_client import gatt_cl_wid_hdl

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    stack = get_stack()
    if stack.is_svc_supported('GATT_CL') and 'GATT/CL' in test_case_name:
        return gatt_cl_wid_hdl(wid, description, test_case_name)
    log("%s, %r, %r, %s", gatt_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


def hdl_wid_3(desc):
    time.sleep(2)
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return True


def hdl_wid_12(desc):
    btp.gattc_exchange_mtu(btp.pts_addr_type_get(), btp.pts_addr_get())
    time.sleep(10)
    return True


def hdl_wid_15(desc):
    btp.gattc_find_included(btp.pts_addr_type_get(), btp.pts_addr_get(),
                            None, None)
    return True


def hdl_wid_17(desc):
    MMI.reset()
    MMI.parse_description(desc)

    iut_services = []

    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        handle, _, _ = attr
        (_, uuid_len, uuid) = btp.gatts_get_attr_val(
            btp.pts_addr_type_get(),
            btp.pts_addr_get(), handle)
        uuid = btp.btp2uuid(uuid_len, uuid)
        iut_services.append(uuid)

    return bool(iut_services == MMI.args)


def hdl_wid_24(desc):
    MMI.reset()
    MMI.parse_description(desc)

    # Include service in description should have 3 parameters:
    # Attribute Handle, Included Service Attribute Handle and End Group Handle
    num_includes = len(MMI.args) // 3

    pts_services = []

    for i in range(num_includes):
        pts_services.append([int(MMI.args[i + 0], 16),
                             int(MMI.args[i + 1], 16),
                             int(MMI.args[i + 2], 16)])

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
        logging.error("Service %r not found", service)
        return False

    return True


def hdl_wid_49(desc):
    time.sleep(30)
    return True


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

    value_read = hexlify(value).decode('utf-8')

    return bool(value_read == MMI.args[1])


def hdl_wid_92(desc):
    time.sleep(2)
    return True


def hdl_wid_98(desc):
    time.sleep(5)
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
        if not perm & Perm.read:
            return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_118(desc):
    return '{0:04x}'.format(65000)


def hdl_wid_121(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    # TODO This needs reworking
    chrcs = btp.gatts_get_attrs(type_uuid='2803')

    for chrc in chrcs:
        handle, perm, _ = chrc

        chrc_val = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                          btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        (_, val_len, val) = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        _, handle, _ = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, _ = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        if perm & Perm.write_enc and perm & Perm.read_enc:
            return '{0:04x}'.format(handle)

    return '0000'


def hdl_wid_122(desc):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    # TODO This needs reworking
    chrcs = btp.gatts_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, _ = chrc

        chrc_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                           btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        _, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        _, handle, chrc_uuid = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, _ = chrc_value_attr[0]
        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, val = chrc_value_data

        if perm & Perm.read and perm & Perm.read_enc:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_142(desc):
    log("Mynewt sends EATT supported bit")
    return True


def hdl_wid_400(desc):
    log("Mynewt sends EATT supported bit")
    return '0000'


def hdl_wid_402(desc):
    log("Mynewt sends EATT supported bit")
    return '0000'
