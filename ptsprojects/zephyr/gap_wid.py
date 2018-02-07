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
import sys
from pybtp import btp
from pybtp.types import Prop, Perm, UUID
import re
import struct
from ptsprojects.stack import get_stack

log = logging.debug


def gap_wid_hdl(wid, description):
    log("%s, %r, %r", gap_wid_hdl.__name__, wid, description)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e.message)


# wid handlers section begin
def hdl_wid_77(desc):
    btp.gap_disconn()
    return True


def hdl_wid_91(desc):
    btp.gap_set_conn()
    btp.gap_adv_ind_on()
    return True


def hdl_wid_108(desc):
    btp.gap_pair()
    return True


def hdl_wid_118(desc):
    return True


def hdl_wid_130(desc):
    return btp.gatts_verify_write_fail(desc)


def hdl_wid_137(desc):
    return btp.gatts_verify_write_fail(desc)


def hdl_wid_141(desc):
    return btp.gatts_verify_write_success(desc)


def hdl_wid_135(desc):
    btp.gap_unpair()
    return True


def hdl_wid_136(desc):
    btp.core_reg_svc_gatt()
    btp.gatts_add_svc(0, UUID.VND16_1)
    btp.gatts_add_char(0, Prop.read | Prop.auth_swrite,
                       Perm.read | Perm.write_authn, UUID.VND16_2)
    btp.gatts_set_val(0, '01')
    btp.gatts_start_server()
    return True


def hdl_wid_141(desc):
    return btp.gatts_verify_write_success(desc)


def hdl_wid_161(desc):
    match = re.findall(r'(0[xX])?([0-9a-fA-F]{4})', desc)
    handle = int(match[0][1], 16)

    attr = btp.gatts_get_attrs(handle, handle)
    if not attr:
        return

    (handle, permission, type_uuid) = attr.pop()

    # Check if characteristic has signed write property
    value = btp.gatts_get_attr_val(handle - 1)
    if not value:
        return

    (att_rsp, val_len, val) = value

    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)
    uuid_len = val_len - hdr_len

    (properties, value_handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len,
                                                          val)

    if properties & Prop.auth_swrite == 0:
        return

    chrc_uuid = btp.btp2uuid(uuid_len, chrc_uuid)

    value = btp.gatts_get_attr_val(handle)
    if not value:
        return

    (att_rsp, val_len, val) = value
    return val_len
