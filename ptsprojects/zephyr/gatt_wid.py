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
import re
from binascii import hexlify
from ptsprojects.stack import get_stack

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


def hdl_wid_17(desc):
    # This pattern is matching Primary Service
    pattern = re.compile(r"Service\s=\s'([0-9a-fA-F]+)'")
    pts_services = pattern.findall(desc)
    if not pts_services:
        logging.error("%s parsing error", hdl_wid_17.__name__)
        return False

    # Normalize UUIDs
    pts_services = [hex(int(service, 16)) for service in pts_services]

    iut_services = []

    # Get all primary services
    attrs = btp.gatts_get_attrs(type_uuid='2800')
    for attr in attrs:
        handle, perm, type_uuid = attr
        (_, uuid_len, uuid) = btp.gatts_get_attr_val(handle)
        uuid = btp.btp2uuid(uuid_len, uuid)
        iut_services.append(uuid)

    # Verification
    for service in pts_services:
        if service in iut_services:
            iut_services.remove(service)
            logging.debug("Service %s found", service)
            continue
        else:
            logging.error("Service %s not found", service)
            return False
    return True


def hdl_wid_52(desc):
    # This pattern is matching IUT handle and characteristic value
    pattern = re.compile("(Handle|value)='([0-9a-fA-F]+)'")
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_52.__name__)
        return False

    params = dict(params)

    handle = int(params.get('Handle'), 16)
    value = int(params.get('value'), 16)

    (att_rsp, value_len, value_read) = btp.gatts_get_attr_val(handle)
    value_read = int(hexlify(value_read), 16)

    if value_read != value:
        return False
    return True
