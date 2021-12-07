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

import copy
import logging
import re
import struct
import sys
from time import sleep

from ptsprojects.stack import get_stack
from pybtp import btp, types
from pybtp.types import Prop, Perm, UUID, AdType, bdaddr_reverse, WIDParams

log = logging.debug


def gap_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", gap_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


# wid handlers section begin
def hdl_wid_4(_: WIDParams):
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    return btp.check_discov_results()


def hdl_wid_5(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd)
    return True


def hdl_wid_9(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_10(_: WIDParams):
    btp.gap_stop_discov()
    return btp.check_discov_results(discovered=True)


def hdl_wid_11(_: WIDParams):
    btp.gap_stop_discov()
    return btp.check_discov_results(discovered=False)


def hdl_wid_12(_: WIDParams):
    btp.gap_start_discov(discov_type='passive', mode='observe')
    return True


def hdl_wid_13(_: WIDParams):
    btp.gap_start_discov(mode='limited')
    return True


def hdl_wid_14(_: WIDParams):
    btp.gap_stop_discov()
    return btp.check_discov_results(discovered=True)


def hdl_wid_20(_: WIDParams):
    stack = btp.get_stack()
    btp.gap_set_nonconn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_21(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_23(_: WIDParams):
    btp.gap_start_discov()
    return True


def hdl_wid_24(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_25(_: WIDParams):
    stack = get_stack()

    if stack.gap.flags:
        stack.gap.ad[AdType.flags] = stack.gap.flags

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_26(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.manufacturer_data] = stack.gap.manufacturer_data

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_27(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.tx_power] = '00'

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_29(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.slave_conn_interval_range] = 'ffffffff'

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_35(_: WIDParams):
    stack = get_stack()

    if stack.gap.svcs:
        stack.gap.ad[AdType.uuid16_some] = stack.gap.svcs

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_40(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_44(_: WIDParams):
    btp.gap_disconn()
    return True


def hdl_wid_46(_: WIDParams):
    """
    :params.desc: Please send an L2CAP Connection Parameter Update request using valid parameters.
    :return:
    """
    btp.gap_wait_for_connection()

    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    new_params = copy.deepcopy(stack.gap.conn_params.data)

    new_params.conn_latency += 1

    btp.gap_conn_param_update(bd_addr, bd_addr_type,
                              new_params.conn_itvl,
                              new_params.conn_itvl,
                              new_params.conn_latency,
                              new_params.supervision_timeout)

    return True


def hdl_wid_47(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_49(_: WIDParams):
    stack = get_stack()

    btp.gap_set_limdiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_50(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_limdiscov()
    btp.gap_set_conn()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_51(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_52(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_53(params: WIDParams):
    return hdl_wid_51(params)


def hdl_wid_54(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_gendiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_55(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_limdiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_56(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.uuid16_svc_solicit] = stack.gap.svc_data

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_57(_: WIDParams):
    stack = get_stack()

    if stack.gap.svc_data:
        stack.gap.ad[AdType.uuid16_svc_data] = stack.gap.svc_data

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_59(_: WIDParams):
    stack = get_stack()

    btp.gap_set_nonconn()
    btp.gap_set_limdiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_60(_: WIDParams):
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gap_direct_adv_on(bd_addr, bd_addr_type)

    return True


def hdl_wid_72(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()
    btp.gap_set_nondiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_73(_: WIDParams):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gattc_read_uuid(bd_addr_type, bd_addr,
                        '0001', 'FFFF', UUID.device_name)
    btp.gattc_read_uuid_rsp()

    return True


def hdl_wid_74(params: WIDParams):
    return hdl_wid_72(params)


def hdl_wid_75(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_76(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()
    btp.gap_set_limdiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_77(_: WIDParams):
    try:
        btp.gap_disconn()
    except types.BTPError:
        logging.debug("Ignoring expected error on disconnect")
    return True


def hdl_wid_78(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_79(_: WIDParams):
    stack = get_stack()
    btp.gap_set_nonconn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_80(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_82(_: WIDParams):
    return True


def hdl_wid_83(_: WIDParams):
    return True


def hdl_wid_84(_: WIDParams):
    return True


def hdl_wid_85(_: WIDParams):
    return True


def hdl_wid_89(_: WIDParams):
    return True


def hdl_wid_90(_: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_91(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_100(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_104(_: WIDParams):
    btp.gap_set_bondable_off()
    return True


def hdl_wid_106(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_108(params: WIDParams):
    if params.description == 'Please start the Bonding Procedure in bondable mode.':
        btp.gap_set_bondable_on()
    else:
        # Please configure the IUT into LE Security and start pairing process.
        btp.gap_pair()
    return True


def hdl_wid_112(_: WIDParams):
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gattc_disc_all_chrc(bd_addr_type, bd_addr, 0x0001, 0xffff)
    attrs = btp.gattc_disc_all_chrc_rsp()

    for attr in attrs:
        if attr.prop & Prop.read:
            btp.gattc_read(bd_addr_type, bd_addr, attr.value_handle)
            btp.gattc_read_rsp()
            return True

    return False


def hdl_wid_114(params: WIDParams):
    return hdl_wid_46(params)


def hdl_wid_118(_: WIDParams):
    return True


def hdl_wid_120(_: WIDParams):
    return True


def hdl_wid_121(_: WIDParams):
    btp.gap_set_limdiscov()
    btp.gap_set_nonconn()

    return True


def hdl_wid_122(_: WIDParams):
    btp.gap_set_nonconn()
    btp.gap_set_gendiscov()

    return True


def hdl_wid_124(_: WIDParams):
    return True


def hdl_wid_125(params: WIDParams):
    match = re.findall(r'(0[xX])?([0-9a-fA-F]{4})', params.description)
    handle = match[0][1]

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()
    btp.gattc_signed_write(bd_addr_type, bd_addr, handle, "01")

    return True


def hdl_wid_127(params: WIDParams):
    return hdl_wid_46(params)


def hdl_wid_130(params: WIDParams):
    return btp.gatts_verify_write_fail(params.description)


def hdl_wid_135(_: WIDParams):
    btp.gap_unpair()
    return True


def hdl_wid_136(_: WIDParams):
    btp.core_reg_svc_gatt()
    btp.gatts_add_svc(0, UUID.VND16_1)
    btp.gatts_add_char(0, Prop.read | Prop.auth_swrite,
                       Perm.read | Perm.write_authn, UUID.VND16_2)
    btp.gatts_set_val(0, '01')
    btp.gatts_start_server()
    return True


def hdl_wid_137(params: WIDParams):
    return btp.gatts_verify_write_fail(params.description)


def hdl_wid_138(_: WIDParams):
    btp.gap_start_discov(transport='le', discov_type='active', mode='observe')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    return btp.check_discov_results()


def hdl_wid_139(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    for attr in attrs:
        if not attr:
            continue

        (handle, permission, type_uuid) = attr
        data = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not data:
            continue

        (att_rsp, val_len, val) = data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        (props, handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & Perm.read_authn:
            return format(handle, 'x').zfill(4)

    return False


def hdl_wid_139_mode1_lvl2(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    for attr in attrs:
        if not attr:
            continue

        (handle, permission, type_uuid) = attr
        data = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not data:
            continue

        (att_rsp, val_len, val) = data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        (props, handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & Perm.write_enc:
            return format(handle, 'x').zfill(4)

    return False


def hdl_wid_139_mode1_lvl4(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    for attr in attrs:
        if not attr:
            continue

        (handle, permission, type_uuid) = attr
        data = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not data:
            continue

        (att_rsp, val_len, val) = data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        (props, handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & Perm.write_authn:
            return format(handle, 'x').zfill(4)

    return False


def hdl_wid_141(params: WIDParams):
    return btp.gatts_verify_write_success(params.description)


def hdl_wid_142(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_143(_: WIDParams):
    return bool(get_stack().gap.bond_lost_ev_data.data)


def hdl_wid_144(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    for attr in attrs:
        if not attr:
            continue

        (handle, permission, type_uuid) = attr
        data = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
        if not data:
            continue

        (att_rsp, val_len, val) = data

        hdr = '<BH'
        hdr_len = struct.calcsize(hdr)
        uuid_len = val_len - hdr_len

        (props, handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len, val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & Perm.read_enc:
            return format(handle, 'x').zfill(4)

    return False


def hdl_wid_148(_: WIDParams):
    btp.gap_conn()
    return not btp.gap_wait_for_connection(10)


def hdl_wid_149(_: WIDParams):
    stack = get_stack()

    if stack.gap.appearance:
        stack.gap.ad[AdType.gap_appearance] = stack.gap.appearance

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_152(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.public_target_addr] = bdaddr_reverse(btp.pts_addr_get())

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_153(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.random_target_addr] = bdaddr_reverse(btp.pts_addr_get())

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_154(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.advertising_interval] = "0030"

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_155(_: WIDParams):
    stack = get_stack()

    device_addr = '{:02d}'.format(stack.gap.iut_bd_addr.data["type"]) + \
                  bdaddr_reverse(stack.gap.iut_bd_addr.data["address"])

    stack.gap.ad[AdType.le_bt_device_addr] = device_addr

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_156(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.le_role] = '02'

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_157(params: WIDParams):
    btp.gap_start_discov(transport='le', discov_type='active', mode='observe')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    report, response = re.findall(r'[a-fA-F0-9]{62}', params.description)
    return btp.check_scan_rep_and_rsp(report, response)


def hdl_wid_158(_: WIDParams):
    return True


def hdl_wid_159(_: WIDParams):
    return True


def hdl_wid_161(params: WIDParams):
    match = re.findall(r'(0[xX])?([0-9a-fA-F]{4})', params.description)
    handle = int(match[0][1], 16)

    attr = btp.gatts_get_attrs(handle, handle)
    if not attr:
        return None

    (handle, permission, type_uuid) = attr.pop()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    # Check if characteristic has signed write property
    value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle - 1)
    if not value:
        return None

    (att_rsp, val_len, val) = value

    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)
    uuid_len = val_len - hdr_len

    (properties, value_handle, chrc_uuid) = struct.unpack("<BH%ds" % uuid_len,
                                                          val)

    if properties & Prop.auth_swrite == 0:
        return None

    value = btp.gatts_get_attr_val(bd_addr_type, bd_addr, handle)
    if not value:
        return None

    (att_rsp, val_len, val) = value
    return val_len


def hdl_wid_162(params: WIDParams):
    return hdl_wid_46(params)


def hdl_wid_169(_: WIDParams):
    btp.gap_start_discov(discov_type='active', mode='observe')
    return True


def hdl_wid_173(_: WIDParams):
    stack = get_stack()

    # Prepare space for URI
    stack.gap.ad.clear()
    stack.gap.ad[AdType.uri] = stack.gap.uri

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_174(params: WIDParams):
    btp.gap_rpa_conn(params.description)
    return True


def hdl_wid_176(_: WIDParams):
    return True


def hdl_wid_177(_: WIDParams):
    return True


def hdl_wid_178(_: WIDParams):
    return True


def hdl_wid_179(_: WIDParams):
    return True


def hdl_wid_204(_: WIDParams):
    btp.gap_start_discov(discov_type='passive', mode='observe')
    sleep(10)
    btp.gap_stop_discov()
    return btp.check_discov_results()


def hdl_wid_206(params: WIDParams):
    stack = get_stack()

    passkey = btp.parse_passkey_description(params.description)
    stack.gap.passkey.data = passkey

    btp.gap_passkey_entry_req_ev()
    return True


def hdl_wid_208(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_209(_: WIDParams):
    return True


def hdl_wid_224(_: WIDParams):
    btp.gap_set_mitm_off()
    return True


def hdl_wid_225(_: WIDParams):
    return True


def hdl_wid_226(_: WIDParams):
    return True


def hdl_wid_227(_: WIDParams):
    try:
        btp.l2cap_conn(None, None, 128)
    except types.BTPError:
        pass
    return True


def hdl_wid_232(_: WIDParams):
    stack = get_stack()

    stack.gap.ad[AdType.advertising_interval_long] = "000030"

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_267(_: WIDParams):
    # Click Yes if device support User Interaction to pair with the peer.
    # As we are already paired, we can only enable security - return False
    return False


def hdl_wid_400(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_402(_: WIDParams):
    # Please perform the General Connection Establishment Procedure using RPA
    # then resolve the PTS address and connect with PTS.
    stack = get_stack()

    if not stack.gap.iut_has_privacy():
        return False

    btp.gap_conn()
    return True


def hdl_wid_403(_: WIDParams):
    # Please perform the Directed Connection Establishment Procedure using RPA
    # then resolve the PTS address and connect with PTS.
    stack = get_stack()

    if not stack.gap.iut_has_privacy():
        return False

    if stack.gap.peripheral.data:
        bd_addr = btp.pts_addr_get()
        bd_addr_type = btp.pts_addr_type_get()

        btp.gap_direct_adv_on(bd_addr, bd_addr_type, 0, 1)
    else:
        btp.gap_conn()

    return True


def hdl_wid_406(_: WIDParams):
    # Please enter General Connectable Mode using private addresses.
    # Note: IUT is expected to do directed advertising with target address set
    # to peer RPA...when WID 403 is received

    stack = get_stack()
    stack.gap.peripheral.data = True

    return True


def hdl_wid_1002(_: WIDParams):
    stack = get_stack()
    return stack.gap.get_passkey()


def hdl_wid_2000(_: WIDParams):
    stack = get_stack()

    passkey = stack.gap.passkey.data
    stack.gap.passkey.data = None

    return passkey


def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20115(_: WIDParams):
    btp.gap_disconn()
    return True


def hdl_wid_20100(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_2142(_: WIDParams):
    btp.gap_conn()
    return True
