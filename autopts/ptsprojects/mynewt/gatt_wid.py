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
import time
from binascii import hexlify

from autopts.wid import generic_wid_hdl
from autopts.pybtp import btp
from autopts.pybtp.types import Perm, WIDParams
from autopts.ptsprojects.testcase import MMI
from autopts.ptsprojects.stack import get_stack

log = logging.debug


def gatt_wid_hdl(wid, description, test_case_name):
    stack = get_stack()
    if stack.is_svc_supported('GATT_CL') and 'GATT/CL' in test_case_name:
        return generic_wid_hdl(wid, description, test_case_name,
                               [__name__, 'autopts.wid.gatt_client'])

    log(f'{gatt_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name,
                           [__name__, 'autopts.wid.gatt'])


def hdl_wid_3(_: WIDParams):
    time.sleep(2)
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return True

def hdl_wid_49(_: WIDParams):
    time.sleep(30)
    return True


def hdl_wid_92(_: WIDParams):
    time.sleep(2)
    return True


def hdl_wid_98(_: WIDParams):
    time.sleep(5)
    return True


def hdl_wid_118(_: WIDParams):
    return '{0:04x}'.format(65000)


def hdl_wid_121(_: WIDParams):
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


def hdl_wid_122(_: WIDParams):
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
