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

from binascii import hexlify
from random import randint
from time import sleep
import logging
import re
import socket
import struct
import sys

from autopts.pybtp import btp
from autopts.pybtp.types import Prop, Perm, IOCap, UUID, WIDParams, GATTErrorCodes
from autopts.ptsprojects.testcase import MMI
from autopts.ptsprojects.stack import get_stack, GattPrimary, GattService, GattSecondary, GattServiceIncluded, \
    GattCharacteristic, GattCharacteristicDescriptor, GattDB

log = logging.debug

indication_subbed_already = False


def gatt_cl_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", gatt_cl_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


#TODO: port all GATT wids to GATT Client service
# wid handlers section begin
def hdl_wid_1(_: WIDParams):
    """
    Please prepare IUT into a connectable mode.

    Description: Verify that the Implementation Under Test (IUT)
    can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_2(_: WIDParams):
    """
    Please initiate a GATT connection to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can
    initiate GATT connect request to PTS.
    """
    btp.gap_conn()
    return True


def hdl_wid_3(_: WIDParams):
    """
    Please initiate a GATT disconnection to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can
    initiate GATT disconnect request to PTS.
    """
    btp.gap_disconn(btp.pts_addr_get(), btp.pts_addr_type_get())
    return get_stack().gap.wait_for_disconnection(30)


def hdl_wid_4(_: WIDParams):
    """
    Please make sure IUT does not initiate security procedure.

    Description: PTS will delete bond information. Test case requires
    that no authentication or authorization procedure has been performed
    between the IUT and the test system.
    """
    btp.gap_set_io_cap(IOCap.no_input_output)
    return True


def hdl_wid_10(_: WIDParams):
    """
    Please send discover all primary services command to the PTS.

    Description: Verify that the Implementation Under Test (IUT)
    can send Discover All Primary Services.
    """
    stack = get_stack()
    btp.gatt_cl_disc_all_prim(btp.pts_addr_type_get(),
                              btp.pts_addr_get())
    return True


def hdl_wid_11(_: WIDParams):
    """
    Please confirm that IUT received NO service uuid found in the small
    database file. Click Yes if NO service found, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover primary service by UUID in small database.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_prim_svcs()
    return stack.gatt_cl.prim_svcs == []


def hdl_wid_12(_: WIDParams):
    """
    Please send exchange MTU command to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Exchange MTU command to the tester.
    """
    stack = get_stack()
    btp.gatt_cl_exchange_mtu(btp.pts_addr_type_get(), btp.pts_addr_get())
    return True


def hdl_wid_15(_: WIDParams):
    """
    Please send discover all include services to the PTS to discover all
    Include Service supported in the PTS. Discover primary service if needed.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all include services command.
    """
    stack = get_stack()
    btp.gatt_cl_find_included(btp.pts_addr_type_get(), btp.pts_addr_get(),
                              '0001', 'FFFF')

    return True


def hdl_wid_16(_: WIDParams):
    """
    Please confirm that IUT received NO 128 bit uuid in the small database file.
    Click Yes if NO handle found, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can discover
    characteristics by UUID in small database.
    """
    return True


def hdl_wid_17(params: WIDParams):
    """
    Please confirm IUT received primary services Primary Service = '1801'O
    Primary Service = '1800'O  in database. Click Yes if IUT received it,
    otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all primary services in database."
    """

    stack = get_stack()
    stack.gatt_cl.wait_for_prim_svcs()

    handle_list = re.findall(r"\'(.*?)\'", params.description)
    for h in handle_list:
        check = [saved for saved in stack.gatt_cl.prim_svcs if saved[2] == h]
        if len(check) == 0:
            return False

    return True

def hdl_wid_18(params: WIDParams):
    """
    Please send discover primary services with UUID value set to '1800'O
    to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover Primary Services UUID = '1800'O."
    """
    stack = get_stack()

    MMI.reset()
    MMI.parse_description(params.description)

    uuid = MMI.args[0]

    if not uuid:
        logging.error("%s parsing error", hdl_wid_18.__name__)
        return False

    btp.gatt_cl_disc_prim_uuid(btp.pts_addr_type_get(),
                               btp.pts_addr_get(),
                               uuid)
    return True


def hdl_wid_19(params: WIDParams):
    """
    Please confirm IUT received primary services uuid = '1800'O
    Service start handle = '0001'O, end handle = '0007'O in database.
    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover primary service by UUID in database."
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_prim_svcs()

    desc_params = re.findall(r"\'(.*?)\'", params.description)
    return (desc_params[1], desc_params[2], desc_params[0]) in stack.gatt_cl.prim_svcs


def hdl_wid_20(params: WIDParams):
    """
    Please send discover primary services with UUID value set to
    '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover Primary Services UUID = '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    uuid = MMI.args[0]

    stack = get_stack()

    if not uuid:
        logging.error("%s parsing error", hdl_wid_20.__name__)
        return False

    btp.gatt_cl_disc_prim_uuid(btp.pts_addr_type_get(),
                               btp.pts_addr_get(),
                               uuid)

    return True


def hdl_wid_21(params: WIDParams):
    """
    Please confirm IUT received primary services
    uuid= '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O,
    Service start handle = '0090'O, end handle = '0096'O in database.
    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover primary service by UUID in database.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_prim_svcs()

    desc_params = re.findall(r"\'(.*?)\'", params.description)
    return (desc_params[1], desc_params[2], desc_params[0]) in stack.gatt_cl.prim_svcs


def hdl_wid_24(params: WIDParams):
    """
    Please confirm IUT received include services:
        Attribute Handle = '0002'O
        Included Service Attribute handle = '0080'O,
        End Group Handle = '0085'O,
        Service UUID = 'A00B'O
        Attribute Handle = '0021'O
        Included Service Attribute handle = '0001'O,
        End Group Handle = '0006'O,
        Service UUID = 'A00D'O
        Attribute Handle = '0091'O
        Included Service Attribute handle = '0001'O
        End Group Handle = '0006'O,
        Service UUID = 'A00D'O

    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all include services in database.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    if not MMI.args:
        return False

    # split MMI args into tuples (att_hdl, incl_svc_hdl, end_gp_hdl, svc_uuid)
    mmi_args_tupled = []
    for i in range(0, len(MMI.args), 4):
        mmi_args_tupled.append(tuple(MMI.args[i:i + 4]))

    stack = get_stack()
    return set(stack.gatt_cl.incl_svcs).issubset(set(mmi_args_tupled))


def hdl_wid_26(params: WIDParams):
    """
    There is no include service in the database file.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all include services in database.
    """
    stack = get_stack()
    return stack.gatt_cl.incl_svcs == []


def hdl_wid_27(params: WIDParams):
    """
    Discover all characteristics of service
        UUID= '180A'O,
        Service start handle = '0030'O,
        end handle = '0047'O.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all charactieristics of a service.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    stack = get_stack()

    start_hdl = MMI.args[1]
    end_hdl = MMI.args[2]

    if not start_hdl or not end_hdl:
        logging.error("parsing error")
        return False

    btp.gatt_cl_disc_all_chrc(btp.pts_addr_type_get(), btp.pts_addr_get(),
                              start_hdl, end_hdl)

    return True


def hdl_wid_28(params: WIDParams):
    """
    Please confirm IUT received all characteristics of service
    handle='0031'O handle='0033'O handle='0035'O handle='0037'O handle='0039'O
    handle='003B'O handle='003D'O handle='003F'O handle='0041'O handle='0043'O
    handle='0045'O  in database.
    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all characteristics of a service in database."
    """
    MMI.reset()
    MMI.parse_description(params.description)

    stack = get_stack()
    stack.gatt_cl.wait_for_chrcs()

    for hdl in MMI.args:
        hdl = int(hdl, 16)
        result = [item for item in stack.gatt_cl.chrcs if item[0] == hdl]
        if result is None:
            return False
    return True


def hdl_wid_29(params: WIDParams):
    """
    Please send discover characteristics by UUID. Range start from
    handle = '00C0'O end handle = '00C5'O characteristics UUID = 0x2AA5'O.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover characteristics by UUID."
    """
    MMI.reset()
    MMI.parse_description(params.description)

    start_hdl = MMI.args[0]
    end_hdl = MMI.args[1]
    uuid = MMI.args[2]

    if not start_hdl or not end_hdl or not uuid:
        logging.error("parsing error")
        return False

    btp.gatt_cl_disc_chrc_uuid(btp.pts_addr_type_get(),
                               btp.pts_addr_get(),
                               start_hdl, end_hdl, uuid)
    return True


def hdl_wid_30(params: WIDParams):
    """
    Please confirm IUT received characteristic handle='00C5'O UUID='2AA5'O
    in database. Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover primary service by UUID in database."
    """
    MMI.reset()
    MMI.parse_description(params.description)

    stack = get_stack()
    sleep(1)
    stack.gatt_cl.wait_for_chrcs()

    if int(MMI.args[0], 16) == stack.gatt_cl.chrcs[0][0] and \
            MMI.args[1].replace('-', '') == stack.gatt_cl.chrcs[0][1]:
        return True
    return False


def hdl_wid_31(params: WIDParams):
    """
    Please send discover characteristics descriptor range start from
    handle = '0013'O end handle = '0013'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover characteristics descriptor.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    start_hdl = MMI.args[0]
    end_hdl = MMI.args[1]

    if not start_hdl or not end_hdl:
        logging.error("parsing error")
        return False

    btp.gatt_cl_disc_all_desc(btp.pts_addr_type_get(),
                              btp.pts_addr_get(),
                              start_hdl, end_hdl)
    return True


def hdl_wid_32(params: WIDParams):
    """
    Please confirm IUT received characteristic descriptors
    handle='0013'O UUID=0x2902  in database. Click Yes if IUT received it,
    otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover characteristic descriptors in database."
    """
    MMI.reset()
    MMI.parse_description(params.description)

    stack = get_stack()
    stack.gatt_cl.wait_for_descs()

    val = re.search(r"0x[A-F0-9]+", params.description).group(0)[2:]

    if MMI.args[0] == stack.gatt_cl.dscs[0][0] and \
            val == stack.gatt_cl.dscs[0][1]:
        return True
    return False


def hdl_wid_34(_: WIDParams):
    """
    Please confirm IUT received GATT Timeout. Click Yes if IUT received it,
    otherwise click No.
    """
    return True


def hdl_wid_40(params: WIDParams):
    """
    Please confirm IUT received Invalid handle error. Click Yes if IUT received
    it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Invalid handle error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_41(params: WIDParams):
    """
    Please confirm IUT received read is not permitted error.
    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    read is not permitted error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_42(params: WIDParams):
    """
    Please confirm IUT received authorization error. Click Yes if IUT received
    it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    authorization error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_43(params: WIDParams):
    """
    Please confirm IUT received authentication error. Click Yes if IUT received
    it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    authentication error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_44(params: WIDParams):
    """
    Please confirm IUT received encryption key size error. Click Yes if IUT
    received it, otherwise click No.

    If IUT did not receive encryption key size error please change encryption
    key size to 7.

    Description: Verify that the Implementation Under Test (IUT) indicate
    encryption key size error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_45(params: WIDParams):
    """
    Please confirm IUT received attribute not found error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    attribute not found error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_46(params: WIDParams):
    """
    Please confirm IUT received Invalid offset error. Click Yes if IUT received
    it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Invalid offset error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_47(params: WIDParams):
    """
    Please confirm IUT received Application error. Click Yes if IUT received it,
    otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Application error when read a characteristic.
    """
    return btp.verify_description(params.description)


def hdl_wid_48(params: WIDParams):
    """
    Please send read characteristic handle = '00EB'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send Read
    characteristic.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]

    if not hdl:
        logging.debug("parsing error")
        return False

    btp.clear_verify_values()
    btp.gatt_cl_read_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                          hdl, 0, 0)
    return True


def hdl_wid_49(_: WIDParams):
    """
    Please wait for 30 seconds timeout to abort the procedure.

    Description: Verify that the Implementation Under Test (IUT) can handle
    timeout after send Read characteristic without receiving response
    in 30 seconds.
    """
    return True


def hdl_wid_50(params: WIDParams):
    """
    Please confirm IUT received characteristic value='54657374'O in random
    selected adopted database. Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read characteristic to PTS random select adopted database.
    """
    """
    Please confirm IUT received characteristic value='Attribute Handle = '0233'O
    Value = 7F11220405060708090A0B0C0405060708090A0B0C 'O in random selected
    adopted database. Click Yes if IUT received it, otherwise click No.
    
    Description: Verify that the Implementation Under Test (IUT) can send
    Read characteristic to PTS random select adopted database."
    """
    MMI.reset()
    MMI.parse_description(params.description)
    stack = get_stack()
    stack.gatt_cl.wait_for_read()
    MMI.args.pop(0) # get rid of parsing artifact
    for i in range(len(MMI.args)//2):
        comparing = (int(MMI.args[i], 16), bytes(MMI.args[i+1], 'utf-8'))
        if comparing not in btp.get_verify_values():
            btp.clear_verify_values()
            return False
    btp.clear_verify_values()
    return True




def hdl_wid_51(params: WIDParams):
    """
    Please send read using characteristic UUID = '6440'O handle range = '0001'O
    to 'FFFF'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send Read
    characteristic by UUID.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    uuid = MMI.args[0]
    start_hdl = MMI.args[1]
    end_hdl = MMI.args[2]

    if not uuid or not start_hdl or not end_hdl:
        logging.debug("parsing error")
        return False

    btp.clear_verify_values()
    btp.gatt_cl_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                          start_hdl, end_hdl, uuid)
    return True


def hdl_wid_52(params: WIDParams):
    """
    Please confirm IUT Handle='4'O characteristic value='0000'O
    in random selected adopted database. Click Yes if it matches the IUT,
    otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send Read
    long characteristic to PTS random select adopted database.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    value = MMI.args[1]

    stack = get_stack()
    stack.gatt_cl.wait_for_read()

    for data in btp.get_verify_values():
        if isinstance(data, bytes):
            if data.decode().upper() == value:
                return True
    return False


def hdl_wid_53(params: WIDParams):
    """
    Please send read to handle = '00FA'O and offset greater than '0081'O to
    the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read with invalid offset.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    read_hdl = MMI.args[0]
    offset = MMI.args[1]

    if not read_hdl or not offset:
        logging.debug("parsing error")
        return False

    btp.gatt_cl_read_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                          read_hdl, offset, 1)
    return True


def hdl_wid_55(params: WIDParams):
    """
    Please confirm IUT received characteristic value='DB070C1201020300'O
    and characteristic value='3F'O in random selected adopted database.
    Click Yes if it matches the IUT, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read multiple characteristics.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    stack = get_stack()
    stack.gatt_cl.wait_for_read()

    for value in MMI.args:
        check = False
        for saved_val in btp.get_verify_values():
            if value in saved_val[1].decode().upper():
                check = True
                break
            return False

    return check


def hdl_wid_57(params: WIDParams):
    """
    Please send Read Multiple Characteristics request using these handles:
    '01EC'O '0006'O

    Description: Verify that the Implementation Under Test (IUT) can send
    Read multiple characteristics.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl1 = MMI.args[0]
    hdl2 = MMI.args[1]

    if not hdl1 or not hdl2:
        logging.error("parsing error")
        return False

    btp.gatt_cl_read_multiple(btp.pts_addr_type_get(), btp.pts_addr_get(),
                              hdl1, hdl2)
    return True


def hdl_wid_58(params: WIDParams):
    """
    Please send read characteristic descriptor handle = '0073'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read characteristic descriptor.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.clear_verify_values()

    if params.test_case_name == "GATT/CL/GAR/BV-07-C":
        btp.gatt_cl_read_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                              hdl, 0, 0)
        return True

    btp.gatt_cl_read(btp.pts_addr_type_get(), btp.pts_addr_get(), hdl)

    return True


def hdl_wid_59(params: WIDParams):
    """
    Please confirm IUT received Descriptor value='0200'O in random selected
    adopted database. Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read Descriptor to PTS random select adopted database.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    value = MMI.args[0]

    stack = get_stack()
    stack.gatt_cl.wait_for_read()

    for data in btp.get_verify_values():
        if isinstance(data, bytes):
            if data.decode().upper() == value:
                return True
    return False


def hdl_wid_61(params: WIDParams):
    """
    Please confirm IUT received Invalid handle error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Invalid handle error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.invalid_handle == status


def hdl_wid_62(params: WIDParams):
    """
    Please confirm IUT received write is not permitted error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate write
    is not permitted error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.write_not_permitted == status


def hdl_wid_63(params: WIDParams):
    """
    Please confirm IUT received write authorization error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    authorization error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.insufficient_authorization == status


def hdl_wid_64(params: WIDParams):
    """
    Please confirm IUT received write authentication error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    authentication error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.insufficient_authentication == status


def hdl_wid_65(params: WIDParams):
    """
    Please confirm IUT received write encryption key size error. Click Yes
    if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    encryption key size error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.encryption_key_size_too_short == status


def hdl_wid_66(params: WIDParams):
    """
    Please confirm IUT received Invalid offset error. Click Yes if IUT
    received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Invalid offset error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.invalid_offset == status


def hdl_wid_67(params: WIDParams):
    """
    Please confirm IUT received Invalid attribute value length error.
    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) indicate
    Invalid attribute value length error when write a characteristic.
    """
    stack = get_stack()
    stack.gatt_cl.wait_for_write_rsp()

    status = stack.gatt_cl.write_status

    return GATTErrorCodes.invalid_attribute_value_length == status


def hdl_wid_69(params: WIDParams):
    """
    Please send prepare write request with handle = '00FD'O and size = '94'
    to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    data according to negotiate MTU size.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    if not MMI.args:
        logging.error("parsing error")
        return False

    handle = int(MMI.args[0], 16)
    size = int(MMI.args[1], 10)

    btp.gatt_cl_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           handle, 0, '12', size)

    return True


def hdl_wid_70(params: WIDParams):
    """
    Please send write command with handle = '0052'O with <= '1' bytes
    of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    write request.
    """
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]
    size = int(params[1])

    btp.gatt_cl_write_without_rsp(btp.pts_addr_type_get(),
                                  btp.pts_addr_get(), handle, '12', size)

    return True


def hdl_wid_71(_: WIDParams):
    """
    Please wait for 30 second timeout to abort the procedure.

    Description: Verify that the Implementation Under Test (IUT) can handle
    timeout after send Write characteristic without receiving response
    in 30 seconds.
    """
    # PTS is handling the wait
    return True


def hdl_wid_72(params: WIDParams):
    """
    Please send signed write command with handle = '00B1'O with one byte
    of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Signed write command.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]

    if not hdl:
        logging.error("parsing error")
        return False

    btp.gatt_cl_signed_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                             hdl, '12', None)
    return True


def hdl_wid_74(params: WIDParams):
    """
    Please send write request with characteristic handle = '0052'O
    with <= '1' byte of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can
    send write request."
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]
    size = int(MMI.args[1])

    if not hdl or size == 0:
        logging.error("parsing error")
        return False

    btp.gatt_cl_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                      hdl, '12', size)
    return True


def hdl_wid_76(params: WIDParams):
    """
    Please send prepare write request with handle = '00D6'O <= '43' byte
    of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    prepare write request.
    """
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]
    len = int(params[1])

    btp.gatt_cl_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           handle, 0, '12', len)

    stack = get_stack()
    stack.gatt_cl.prepared_write_hdl = handle

    return True


def hdl_wid_77(params: WIDParams):
    """
    Please send prepare write request with handle = '00F7'O and
    offset greater than '128' byte to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    prepare write request.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]
    offset = int(MMI.args[1]) + 2

    if not hdl or not offset:
        logging.error("parsing error")
        return False

    btp.gatt_cl_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           hdl, offset, '12', offset + 2)
    return True


def hdl_wid_80(params: WIDParams):
    """
    Please send write request with characteristic handle = '00A5'O
    with greater than '2' byte of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    write request.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]
    val_mtp = MMI.args[1]

    if not hdl or not val_mtp:
        logging.error("parsing error")
        return False

    btp.gatt_cl_write(btp.pts_addr_type_get(), btp.pts_addr_get(),
                      hdl, '1234', val_mtp)

    return True


def hdl_wid_81(params: WIDParams):
    """
    Please send prepare write request with handle = '00E5'O with greater
    than '49' byte of any octet value to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    prepare write request.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    hdl = MMI.args[0]
    val_mtp = MMI.args[1]

    if not hdl or not val_mtp:
        logging.error("parsing error")
        return False

    btp.gatt_cl_write_long(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           hdl, 0, '1234', val_mtp)

    return True


def hdl_wid_82(_: WIDParams):
    """
    Please send execute write request to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    execute write request.
    """
    # This is handled by host
    return True


def hdl_wid_90(_: WIDParams):
    """
    Please confirm IUT received notification from PTS. Click YES if received,
    otherwise NO.

    Description: Verify that the Implementation Under Test (IUT) can receive
    notification send from PTS.
    """
    stack = get_stack()
    return stack.gatt_cl.wait_for_notifications(expected_count=1)


def hdl_wid_91(params: WIDParams):
    """
    Please write to client characteristic configuration handle = '0126'O
    to enable notification to the PTS. Discover all characteristics if needed.

    Description: Verify that the Implementation Under Test (IUT) can receive
    notification sent from PTS.
    """
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    btp.gatt_cl_cfg_notify(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           1, handle)

    return True


def hdl_wid_95(_: WIDParams):
    """
    Please confirm IUT received indication from PTS. Click YES if received,
    otherwise NO.

    Description: Verify that the Implementation Under Test (IUT) can receive
    indication send from PTS.
    """
    stack = get_stack()
    return stack.gatt_cl.wait_for_notifications(expected_count=1)


def hdl_wid_99(params: WIDParams):
    """
    Please write to client characteristic configuration handle = '0123'O to
    enable indication to the PTS. Discover all characteristics if needed.

    Description: Verify that the Implementation Under Test (IUT) can receive
    indication sent from PTS.
    """
    pattern = re.compile("'([0-9a-fA-F]+)'")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    btp.gatt_cl_cfg_indicate(btp.pts_addr_type_get(), btp.pts_addr_get(),
                             1, handle)
    return True


def hdl_wid_108(params: WIDParams):
    """
    Please send read by type characteristic UUID = '2B2A'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read characteristic.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    uuid = MMI.args[0]

    if not uuid:
        logging.debug("parsing error")
        return False

    btp.gatt_cl_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                          "0001", "FFFF", uuid)

    return True


def hdl_wid_109(params: WIDParams):
    """
    Please send read by type characteristic
    UUID = '0000-B009-0000-0000-0123-4567-89AB-CDEF'O to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can send
    Read characteristic.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    uuid = MMI.args[0]

    if not uuid:
        logging.debug("parsing error")
        return False

    btp.gatt_cl_read_uuid(btp.pts_addr_type_get(), btp.pts_addr_get(),
                          "0001", "FFFF", uuid)
    return True


def hdl_wid_502(_: WIDParams):
    """
    Click OK will disconnect GATT connection.
    """
    return True
