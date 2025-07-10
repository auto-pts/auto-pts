#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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
import struct
from binascii import hexlify
from time import sleep

from autopts.ptsprojects.stack import (
    GattDB,
    GattsCharacteristic,
    GattsCharacteristicDescriptor,
    GattsPrimary,
    GattsSecondary,
    GattsService,
    GattsServiceIncluded,
)
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp
from autopts.pybtp.types import UUID, Perm, Prop, WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug

indication_subbed_already = False


def gatt_sr_wid_hdl(wid, description, test_case_name):
    log(f'{gatt_sr_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def gatt_server_fetch_db():
    db = GattDB()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    attrs = btp.gatt_sr_get_attrs()
    for attr in attrs:
        handle, perm, type_uuid = attr

        attr_val = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle)
        if not attr_val:
            logging.debug("cannot read value %r", handle)
            continue

        att_rsp, val_len, val = attr_val

        if type_uuid in ('2800', '2801'):
            uuid = btp.btp2uuid(val_len, val)

            if type_uuid == '2800':
                db.attr_add(handle, GattsPrimary(handle, perm, uuid, att_rsp))
            else:
                db.attr_add(handle, GattsSecondary(handle, perm, uuid, att_rsp))
        elif type_uuid == '2803':

            hdr = '<BH'
            hdr_len = struct.calcsize(hdr)
            uuid_len = val_len - hdr_len

            prop, value_handle, uuid = struct.unpack(f"<BH{uuid_len}s", val)
            uuid = btp.btp2uuid(uuid_len, uuid)

            db.attr_add(handle, GattsCharacteristic(handle, perm, uuid, att_rsp, prop, value_handle))
        elif type_uuid == '2802':
            hdr = "<HH"
            hdr_len = struct.calcsize(hdr)
            uuid_len = val_len - hdr_len
            incl_svc_hdl, end_grp_hdl, uuid = struct.unpack(hdr + f"{uuid_len}s", val)
            uuid = btp.btp2uuid(uuid_len, uuid)

            db.attr_add(handle, GattsServiceIncluded(handle, perm, uuid, att_rsp, incl_svc_hdl, end_grp_hdl))
        else:
            uuid = type_uuid.replace("0x", "").replace("-", "").upper()

            db.attr_add(handle, GattsCharacteristicDescriptor(handle, perm, uuid, att_rsp, val))

    return db


COMPARED_VALUE = []
# wid handlers section begin


def hdl_wid_17(params: WIDParams):
    if params.test_case_name.startswith('GATT/CL'):
        return btp.verify_description(params.description)

    MMI.reset()
    MMI.parse_description(params.description)
    pts_services = MMI.args
    if not pts_services:
        logging.error("%s parsing error", hdl_wid_17.__name__)
        return False

    iut_services = []

    # Get all primary services
    attrs = btp.gatt_sr_get_attrs(type_uuid='2800')
    for attr in attrs:
        handle, perm, type_uuid = attr
        (_, uuid_len, uuid) = btp.gatt_sr_get_attr_val(
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


def hdl_wid_22(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    parsed_args = []

    parsed_args = [[char for char in arg if char != "-"] for arg in MMI.args]

    handles = []
    uuids = []

    # Extract UUID's from parsed arguments
    uuids_from_parse = parsed_args[::3]

    # Delete unwanted UUID values
    del parsed_args[0::3]
    parsed_handles = parsed_args

    # Convert remaining arguments to integers
    parsed_handles = [int("".join(arg), 16) for arg in parsed_handles]

    # Increment every 2nd handle
    parsed_handles[1::2] = [arg + 1 for arg in parsed_handles[1::2]]

    # Get all primary services
    attrs = btp.gatt_sr_get_attrs(type_uuid='2800')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
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


def hdl_wid_23(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

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
    attrs = btp.gatt_sr_get_attrs(type_uuid='2800')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        if iut_service:
            iut_service[1] = start_handle - 1
            iut_services.append(iut_service)
            iut_service = None

        val = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, start_handle)
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


def hdl_wid_24(params: WIDParams):
    if params.test_case_name.startswith('GATT/CL'):
        return btp.verify_description(params.description)

    MMI.reset()
    MMI.parse_description(params.description)

    db = gatt_server_fetch_db()

    if not MMI.args:
        return False

    incl_handle = int(MMI.args[1], 16)
    attr = db.attr_lookup_handle(incl_handle)
    if attr is None or not isinstance(attr, GattsService):
        logging.error("service not found")
        return False

    incl_uuid = attr.uuid
    attr = db.attr_lookup_handle(int(MMI.args[0], 16))
    if attr is None or not isinstance(attr, GattsServiceIncluded):
        logging.error("included not found")
        return False

    if attr.end_grp_hdl != int(MMI.args[2], 16) \
            or incl_uuid != MMI.args[3]:
        logging.error("end group handle not found")
        return False

    return True


def hdl_wid_25(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    pts_chrc_uuid = MMI.args[0]
    pts_chrc_handles = [int(MMI.args[i], 16) for i in range(1, len(MMI.args))]

    iut_start_handle = None
    iut_end_handle = None

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    # Find pts_chrc_uuid service, and it's handle range
    svcs = btp.gatt_sr_get_attrs(type_uuid='2800')
    for svc in svcs:
        handle, perm, type_uuid = svc

        if iut_start_handle:
            iut_end_handle = handle - 1
            break

        svc_val = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle)
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
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803',
                                  start_handle=iut_start_handle,
                                  end_handle=iut_end_handle)
    for chrc in chrcs:
        handle, perm, type_uuid = chrc
        iut_chrc_handles.append(handle)

    if iut_chrc_handles != pts_chrc_handles:
        return False

    return True


def hdl_wid_36(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    pts_services = [[int(MMI.args[0], 16), int(MMI.args[1], 16), int(MMI.args[2], 16), MMI.args[3]]]

    if not pts_services:
        logging.debug("parsing error")
        return False

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    iut_services = []

    # Get all included services
    attrs = btp.gatt_sr_get_attrs(type_uuid='2802')
    for attr in attrs:
        start_handle, perm, type_uuid = attr

        attr_val = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, start_handle)
        if not attr_val:
            continue

        att_rsp, val_len, val = attr_val

        hdr = "<HH"
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len
        incl_svc_hdl, end_grp_hdl, uuid = struct.unpack(hdr + f"{uuid_len}s", val)
        uuid = btp.btp2uuid(uuid_len, uuid)

        iut_service = [start_handle, incl_svc_hdl, end_grp_hdl, uuid]
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


def hdl_wid_52(params: WIDParams):
    if params.test_case_name.startswith('GATT/CL'):
        return btp.verify_description(params.description)

    MMI.reset()
    MMI.parse_description(params.description)

    handle = int(MMI.args[0], 16)
    value = MMI.args[1]

    db = gatt_server_fetch_db()
    attr = db.attr_lookup_handle(handle)
    if attr is None:
        return False

    if not isinstance(attr, GattsCharacteristicDescriptor):
        return False

    if attr.uuid == UUID.CEP:
        (value_read,) = struct.unpack("<H", attr.value)
        value_read_str = f'{value_read:04x}'
    else:
        value_read = hexlify(attr.value).upper()
        value_read_str = value_read.decode('utf-8')

    # PTS may select characteristic with value bigger than MTU but asks to
    # verify only MTU bytes of data
    if value_read_str != value:
        if not value_read_str.startswith(value):
            return False

    return True


def hdl_wid_56(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    if not MMI.args or len(MMI.args) != 3:
        logging.error("parsing error")

    handle1 = MMI.args[0]
    handle2 = MMI.args[1]
    values = MMI.args[2]

    values_read = ""

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    att_rsp, value_len, value = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle1)
    values_read += value.hex()

    att_rsp, value_len, value = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle2)
    values_read += value.hex()

    if values_read.upper() != values.upper():
        return False

    return True


def hdl_wid_92(params: WIDParams):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    # This pattern is matching Notification handle
    pattern = re.compile(r"(handle)\s?=\s?'([0-9a-fA-F]+)'")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    params = dict(params)
    handle = int(params.get('handle'), 16)
    att_rsp, value_len, value = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle)

    if att_rsp:
        logging.debug("cannot read chrc value")
        return False

    # delay, to let the PTS subscribe for notifications
    sleep(2)

    btp.gatt_sr_set_val(bd_addr_type, bd_addr, [handle], ['01'])

    return True


def hdl_wid_93(params: WIDParams):
    # Please send an Handle Value MULTIPLE Notification to PTS.
    # Description: Verify that the Implementation Under Test (IUT) can send
    # handle value multiple notification to the PTS.

    return False


def hdl_wid_98(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)
    if not MMI.args:
        logging.error("parsing error")
        return False

    handle = int(MMI.args[0], 16)
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    att_rsp, value_len, value = btp.gatt_sr_get_attr_val(bd_addr_type, bd_addr, handle)

    if att_rsp:
        logging.debug("cannot read chrc value")
        return False

    # delay, to let the PTS subscribe for notifications
    sleep(2)

    btp.gatt_sr_set_val(bd_addr_type, bd_addr, [handle], ['01'])

    return True


def hdl_wid_110(_: WIDParams):
    # Lookup characteristic handle that does not permit reading
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not prop & Prop.read:
            return f'{handle:04x}'

    return '0000'


def hdl_wid_111(_: WIDParams):
    # Lookup characteristic UUID that does not permit reading
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not prop & Prop.read:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_112(_: WIDParams):
    # Lookup characteristic handle that requires "read" authorization
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        (att_rsp, val_len, val) = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        # Check if returned ATT Insufficient Authorization error
        att_rsp, val_len, val = chrc_value_data
        if att_rsp != 8:
            continue

        return f'{handle:04x}'

    return '0000'


def hdl_wid_113(_: WIDParams):
    # Lookup characteristic UUID that requires "read" authorization
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                             btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        att_rsp, val_len, val = chrc_value_data

        # Check if returned ATT Insufficient Authorization error
        if att_rsp != 8:
            continue

        return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_114(_: WIDParams):
    # Lookup characteristic UUID that requires "read" authentication
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if perm & Perm.read_authn:
            return f'{handle:04x}'

    return '0000'


def hdl_wid_115(_: WIDParams):
    # Lookup characteristic UUID that requires "read" authentication
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if perm & Perm.read_authn:
            return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_118(_: WIDParams):
    # Lookup invalid attribute handle
    handle = None

    attrs = btp.gatt_sr_get_attrs()
    for attr in attrs:
        handle, perm, type_uuid = attr

    if handle is None:
        logging.error("No attribute found!")
        return "0000"

    return f'{handle + 1:04x}'


def hdl_wid_119(_: WIDParams):
    # Lookup UUID that is not present on IUT GATT Server
    uuid_list = []

    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, uuid = struct.unpack(f"<BH{uuid_len}s", val)
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


def hdl_wid_120(_: WIDParams):
    # Lookup characteristic handle that does not permit write
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        att_rsp, val_len, val = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.write or not prop & Prop.write:
            return f'{handle:04x}'

    return '0000'


def hdl_wid_121(_: WIDParams):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                            btp.pts_addr_get(), handle)
        if not chrc_val:
            continue

        (att_rsp, val_len, val) = chrc_val

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        # Check if returned ATT Insufficient Encryption Key Size error
        att_rsp, val_len, val = chrc_value_data
        if att_rsp != 0x0c:
            continue

        return f'{handle:04x}'

    return '0000'


def hdl_wid_122(_: WIDParams):
    # Lookup characteristic UUID that returns Insufficient Encryption Key Size
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                             btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        att_rsp, val_len, val = chrc_value_data

        # Check if returned ATT Insufficient Authorization error
        if att_rsp != 0x0c:
            continue

        return btp.btp2uuid(uuid_len, chrc_uuid)

    return '0000'


def hdl_wid_132(_: WIDParams):
    btp.gatt_sr_change_database(0, 0, 0x02)
    return True


def hdl_wid_138(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    read_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    COMPARED_VALUE.append(read_val)

    return True


def hdl_wid_139(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    read_val = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    return bool(read_val == COMPARED_VALUE[0])


def hdl_wid_151(_: WIDParams):
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                             btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not perm & Perm.write:
            continue

        if perm & (Perm.read_enc | Perm.read_authn | Perm.write_enc | Perm.write_authn):
            continue

        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, _ = chrc_value_data
        if val_len > 0:
            return f'{handle:04x}'

    return False


def hdl_wid_152(_: WIDParams):
    chrcs = btp.gatt_sr_get_attrs(type_uuid='2803')
    for chrc in chrcs:
        handle, perm, type_uuid = chrc

        chrc_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                             btp.pts_addr_get(), handle)
        if not chrc_data:
            continue

        att_rsp, val_len, val = chrc_data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        prop, handle, chrc_uuid = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatt_sr_get_attrs(start_handle=handle,
                                                end_handle=handle)
        if not chrc_value_attr:
            continue

        handle, perm, type_uuid = chrc_value_attr[0]
        if not perm & Perm.read or not perm & Perm.write:
            continue

        chrc_value_data = btp.gatt_sr_get_attr_val(btp.pts_addr_type_get(),
                                                   btp.pts_addr_get(), handle)
        if not chrc_value_data:
            continue

        _, val_len, _ = chrc_value_data
        if val_len > 64:
            return f'{handle:04x}'

    return False


def hdl_wid_304(params: WIDParams):
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]
    val = MMI.args[1]
    _, _, data = btp.gatts_get_attr_val(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)
    data = hexlify(data).decode().upper()
    return bool(data in val)
