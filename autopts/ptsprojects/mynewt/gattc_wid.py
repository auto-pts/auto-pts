#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
import socket
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import Perm, WIDParams
from autopts.pybtp import btp
from autopts.ptsprojects.testcase import MMI
from autopts.wid import generic_wid_hdl

log = logging.debug


def gattc_wid_hdl(wid, description, test_case_name):
    log(f'{gattc_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    stack = get_stack()
    if stack.is_svc_supported('GATT_CL') and 'GATT/CL' in test_case_name:
        return generic_wid_hdl(wid, description, test_case_name,
                               [__name__, 'autopts.ptsprojects.mynewt.gatt_wid',
                                'autopts.wid.gatt_client'])

    return generic_wid_hdl(wid, description, test_case_name,
                           [__name__, 'autopts.ptsprojects.mynewt.gatt_wid',
                            'autopts.wid.gatt'])


def gattc_wid_hdl_no_read_long(wid, description, test_case_name):
    if wid == 48:
        log("%s, %r, %r, %s", gattc_wid_hdl_no_read_long.__name__, wid, description,
            test_case_name)
        return hdl_wid_48_no_long_read(description)
    return gattc_wid_hdl(wid, description, test_case_name)


def hdl_wid_10(desc):
    btp.gattc_disc_all_prim(btp.pts_addr_type_get(None),
                            btp.pts_addr_get(None))
    btp.gattc_disc_all_prim_rsp()
    return True


def hdl_wid_17(desc):
    return btp.verify_description(desc)


def hdl_wid_24(desc):
    return btp.verify_description(desc)


def hdl_wid_48_no_long_read(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)

    try:
        btp.gattc_read_rsp(True, True)
    except socket.timeout:
        pass
    return True


def hdl_wid_48(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                        hdl, 0, 1)

    try:
        btp.gattc_read_long_rsp(True, True)
    except socket.timeout:
        pass

    return True


def hdl_wid_52(desc):
    return btp.verify_description(desc)


def hdl_wid_58(desc):
    MMI.reset()
    MMI.parse_description(desc)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.gattc_read_long(btp.pts_addr_type_get(None), btp.pts_addr_get(None),
                        hdl, 0, 1)

    try:
        btp.gattc_read_long_rsp(True, True)
    except socket.timeout:
        pass

    return True


def hdl_wid_151(_: WIDParams):
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

        if perm & (Perm.read_enc | Perm.read_authn | Perm.write_enc | Perm.write_authn):
            continue

        chrc_value_data = btp.gatts_get_attr_val(btp.pts_addr_type_get(),
                                                 btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, _ = chrc_value_data
        if val_len == 1:
            return '{0:04x}'.format(handle)

    return False

