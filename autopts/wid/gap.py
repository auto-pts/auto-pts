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
from time import sleep

from autopts.ptsprojects.stack import get_stack, ConnParams
from autopts.pybtp import types
from autopts.pybtp import btp
from autopts.pybtp.types import Prop, Perm, UUID, AdType, bdaddr_reverse, WIDParams, IOCap, OwnAddrType
from autopts.wid import generic_wid_hdl

log = logging.debug


def gap_wid_hdl(wid, description, test_case_name):
    log(f'{gap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


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


def hdl_wid_44(params: WIDParams):
    if params.test_case_name in ['GAP/SEC/AUT/BV-21-C']:
        btp.gap_wait_for_lost_bond(5)

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
                              new_params.conn_itvl_min,
                              new_params.conn_itvl_max,
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

    stack = get_stack()

    if stack.is_svc_supported('GATT_CL'):
        btp.clear_verify_values()
        btp.gatt_cl_read_uuid(bd_addr_type, bd_addr,
                              '0001', 'FFFF', UUID.device_name)
        return True

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


def hdl_wid_77(params: WIDParams):
    if params.test_case_name.startswith("GAP/BOND/BON/BV-04-C"):
        # PTS sends WID before IUT finishes encryption
        # This is a temporary workaround. Ultimately
        # we should wait for an event here or submit a PTS Issue.
        sleep(10)
    try:
        btp.gap_wait_for_connection(5)
        btp.gap_disconn()
    except types.BTPError:
        logging.debug("Ignoring expected error on disconnect")
    else:
        btp.gap_wait_for_disconnection(30)
    return True


def hdl_wid_78(params: WIDParams):
    if params.test_case_name.startswith("GAP/CONN/ACEP"):
        # Use LE ANY addr to trigger auto connection establishment procedure
        btp.gap_conn(b"00:00:00:00:00:00", 0)
    else:
        btp.gap_conn()

    return True


def hdl_wid_79(_: WIDParams):
    stack = get_stack()
    btp.gap_set_nonconn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_80(params: WIDParams):
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()

    if params.test_case_name in ['GAP/BROB/BCST/BV-05-C']:
        """ make sure we add non-pts address to allow list, alter first bytes of address """
        non_pts_addr = btp.pts_addr_get()
        non_pts_addr = f'{(bytes.fromhex(non_pts_addr)[0] + 1) % 256:x}' + non_pts_addr[2:]
        address_list = [(btp.pts_addr_type_get(), non_pts_addr)]
        btp.set_filter_accept_list(address_list)

    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd, own_addr_type=OwnAddrType.le_resolvable_private_address)

    return True


def hdl_wid_82(_: WIDParams):
    """Please prepare IUT into the Auto Connection Establishment Procedure."""
    btp.set_filter_accept_list()

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

    btp.gap_adv_ind_on(ad=stack.gap.ad, own_addr_type=OwnAddrType.le_resolvable_private_address)

    return True


def hdl_wid_91(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()

    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_100(_: WIDParams):
    btp.gap_set_bondable_off()
    btp.gap_pair()
    return True


def hdl_wid_104(_: WIDParams):
    btp.gap_set_bondable_off()
    return True


def hdl_wid_106(params: WIDParams):
    # description: Waiting for HCI_ENCRYPTION_CHANGE_EVENT...
    # Depending on test, PTS seems to start pairing on its own here or not
    if params.test_case_name in ['GAP/SEC/AUT/BV-19-C']:
        btp.gap_pair()

    btp.gap_wait_for_sec_lvl_change(1)
    return True


def hdl_wid_108(params: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_112(params: WIDParams):
    stack = get_stack()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(params.description)
    if not handle:
        return False

    if stack.is_svc_supported('GATT_CL'):
        btp.gatt_cl_read(bd_addr_type, bd_addr, handle)
    else:
        btp.gattc_read(bd_addr_type, bd_addr, handle)
        btp.gattc_read_rsp(store_rsp=True)

    if params.test_case_name in ['GAP/SEC/AUT/BV-19-C']:
        if (btp.verify_att_error("authentication error")):
            btp.gap_pair()

    return True


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
    """
    :params.desc: Please send a LL Connection Parameter Update request using valid parameters.
                  With 0x0032 value set in TSPX_conn_update_int_min
                  0x0046 value set in TSPX_conn_update_int_max
                  0x0001 value set in TSPX_conn_update_peripheral_latency and
                  0x01F4 value set in TSPX_conn_update_supervision_timeout
    """
    btp.gap_wait_for_connection()

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    params = pattern.findall(params.description)
    if not params or len(params) < 4:
        logging.error("parsing error")
        return False

    conn_itvl_min = int(params[0], 16)
    conn_itvl_max = int(params[1], 16)
    conn_latency = int(params[2], 16)
    supervision_timeout = int(params[3], 16)

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gap_conn_param_update(bd_addr, bd_addr_type,
                              conn_itvl_min,
                              conn_itvl_max,
                              conn_latency,
                              supervision_timeout)

    return True


def hdl_wid_130(params: WIDParams):
    stack = get_stack()
    gatt = stack.gatt

    # GAP/SEC/CSIGN/BI-02-C expects two successes and fail
    # we don't know if any of those were already handled so just wait for up to
    # 3 writes and then verify if only 2 occured.
    if params.test_case_name == "GAP/SEC/CSIGN/BI-02-C":
        for i in range(gatt.attr_value_get_changed_cnt(handle=gatt.signed_write_handle), 3):
            gatt.wait_attr_value_changed(handle=gatt.signed_write_handle, timeout=5)

        return gatt.attr_value_get_changed_cnt(handle=gatt.signed_write_handle) == 2

    value = gatt.wait_attr_value_changed(handle=gatt.signed_write_handle, timeout=5)
    return value is None


def hdl_wid_135(_: WIDParams):
    btp.gap_unpair()
    return True


def hdl_wid_136(_: WIDParams):
    btp.gatts_add_svc(0, UUID.VND16_1)
    btp.gatts_add_char(0, Prop.read | Prop.auth_swrite,
                       Perm.read | Perm.write_authn, UUID.VND16_2)
    btp.gatts_set_val(0, '01')
    btp.gatts_start_server()
    return True


def hdl_wid_137(params: WIDParams):
    stack = get_stack()
    gatt = stack.gatt

    value = gatt.wait_attr_value_changed(handle=gatt.signed_write_handle, timeout=5)
    return value is None


def hdl_wid_138(_: WIDParams):
    btp.gap_start_discov(transport='le', discov_type='active', mode='observe')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    return btp.check_discov_results()


def hdl_wid_139(params: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if params.test_case_name in ['GAP/SEC/SEM/BV-39-C',
                                 'GAP/SEC/SEM/BV-43-C',
                                 'GAP/SEC/SEM/BV-24-C',
                                 'GAP/SEC/SEM/BV-29-C']:
        perm = Perm.write_enc
    elif params.test_case_name in ['GAP/SEC/SEM/BV-27-C',
                                   'GAP/SEC/SEM/BV-40-C',
                                   'GAP/SEC/SEM/BV-44-C',
                                   'GAP/SEC/SEM/BV-22-C']:
        perm = Perm.write_authn
    elif params.test_case_name in ['GAP/SEC/AUT/BV-11-C']:
        perm = Perm.read_enc
    else:
        perm = Perm.read_authn

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
        if permission & perm:
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
    stack = get_stack()
    gatt = stack.gatt

    value = gatt.wait_attr_value_changed(handle=gatt.signed_write_handle, timeout=5)
    return value is not None


def hdl_wid_142(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_143(_: WIDParams):
    btp.gap_wait_for_lost_bond(5)
    return bool(get_stack().gap.bond_lost_ev_data.data)


def hdl_wid_144(params: WIDParams):
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
        if params.test_case_name == 'GAP/SEC/AUT/BV-24-C':
            perm = Perm.read_authn
        else:
            perm = Perm.read_enc
        if permission & perm:
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
    # Order IUT to add the lower tester's identity address in the filter accept list and continue
    # advertising using the gernerated resolvable private address. Press Ok when it is ready,
    # otherwise press cancel.
    stack = get_stack()

    btp.gap_adv_off()
    btp.set_filter_accept_list()
    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd, own_addr_type=OwnAddrType.le_resolvable_private_address)
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

    stack = get_stack()
    stack.gatt.signed_write_handle = handle

    return val_len


def hdl_wid_162(params: WIDParams):
    """
    Please start a Connection Update procedure using invalid parameters.

    Set TSPX_iut_invalid_connection_interval_min to 0x0008
    Set TSPX_iut_invalid_connection_interval_max to 0x00AA
    Set TSPX_iut_invalid_connection_latency to 0x0000
    Set TSPX_iut_invalid_conn_update_supervision_timeout to 0x0800
    """
    btp.gap_wait_for_connection()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    new_params = ConnParams(0x0008, 0x00AA, 0x0000, 0x0800)

    btp.gap_conn_param_update(bd_addr, bd_addr_type,
                              new_params.conn_itvl_min,
                              new_params.conn_itvl_max,
                              new_params.conn_latency,
                              new_params.supervision_timeout)

    return True


def hdl_wid_169(_: WIDParams):
    btp.gap_start_discov(discov_type='active', mode='observe')
    return True


def hdl_wid_173(_: WIDParams):
    stack = get_stack()

    if stack.gap.uri == None:
        return False

    # Prepare space for URI
    stack.gap.ad.clear()
    stack.gap.ad[AdType.uri] = stack.gap.uri

    stack.gap.sd.clear()
    stack.gap.sd[AdType.uri] = stack.gap.uri

    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd)

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
    passkey = btp.parse_passkey_description(params.description)
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    stack = get_stack()
    _ = stack.gap.get_passkey()

    try:
        btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    except types.BTPError:
        if (stack.gap.is_connected() == False):
            logging.debug("Ignoring expected error on disconnected")
        else:
            return False

    return True


def hdl_wid_208(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_209(_: WIDParams):
    return True


def hdl_wid_210(_: WIDParams):
    return True


def hdl_wid_224(_: WIDParams):
    btp.gap_set_mitm_off()
    return True


def hdl_wid_225(_: WIDParams):
    return True


def hdl_wid_226(_: WIDParams):
    return True


def hdl_wid_227(params: WIDParams):
    stack = get_stack()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(params.description)
    if not handle:
        return False

    if stack.is_svc_supported('GATT_CL'):
        btp.gatt_cl_write(bd_addr_type, bd_addr, handle, '02', 1)

        stack.gatt_cl.wait_for_write_rsp()
        if stack.gatt_cl.write_status == 5 or stack.gatt_cl.write_status == 15:
            btp.gap_pair()
    else:
        btp.gattc_write(bd_addr_type, bd_addr, handle, '02', 1)
        btp.gattc_write_rsp(store_rsp=True)

        if (btp.verify_att_error("authentication error")):
            btp.gap_pair()

        if (btp.verify_att_error("insufficient encryption")):
            btp.gap_pair()

    return True


def hdl_wid_232(_: WIDParams):
    stack = get_stack()
    stack.gap.ad[AdType.advertising_interval_long] = "000030"
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True

def hdl_wid_234(params: WIDParams):
    stack = get_stack()
    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    if stack.is_svc_supported('GATT_CL'):
        btp.gatt_cl_cfg_indicate(btp.pts_addr_type_get(), btp.pts_addr_get(),
                                 1, handle)
        return True

    btp.gattc_cfg_indicate(btp.pts_addr_type_get(), btp.pts_addr_get(),
                           1, handle)

    return True


def hdl_wid_235(params: WIDParams):
    stack = get_stack()

    pattern = re.compile(r"0x([0-9a-fA-F]+)")
    params = pattern.findall(params.description)
    if not params:
        logging.error("parsing error")
        return False

    handle = params[0]

    if stack.is_svc_supported('GATT_CL'):
        btp.gatt_cl_cfg_notify(btp.pts_addr_type_get(), btp.pts_addr_get(),
                               1, handle)
        return True

    btp.gattc_cfg_notify(btp.pts_addr_type_get(), btp.pts_addr_get(),
                         1, handle)

    return True


def hdl_wid_236(_: WIDParams):
    # Please confirm that IUT does not send a GATT_HandleValueIndication to the Upper Tester
    stack = get_stack()
    gatt = stack.gatt

    if stack.is_svc_supported('GATT_CL'):
        return not stack.gatt_cl.wait_for_notifications(expected_count=1)

    gatt.wait_notification_ev(timeout=5)

    if gatt.notification_events:
        return False

    return True


def hdl_wid_237(_: WIDParams):
    # Please confirm that IUT send a GATT_HandleValueIndication to the Upper Tester
    stack = get_stack()

    if stack.is_svc_supported('GATT_CL'):
        return stack.gatt_cl.wait_for_notifications(expected_count=1)

    gatt = stack.gatt

    gatt.wait_notification_ev(timeout=5)

    if gatt.notification_events:
        return True

    return False

def hdl_wid_238(_: WIDParams):
    # Please confirm that IUT does not send a GATT_HandleValueNotification  to the Upper Tester
    stack = get_stack()
    gatt = stack.gatt

    if stack.is_svc_supported('GATT_CL'):
        return not stack.gatt_cl.wait_for_notifications(expected_count=0)

    gatt.wait_notification_ev(timeout=5)

    if gatt.notification_events:
        return False

    return True


def hdl_wid_239(_: WIDParams):
    # Please confirm that IUT send a GATT_HandleValueNotification  to the Upper Tester
    stack = get_stack()
    gatt = stack.gatt

    if stack.is_svc_supported('GATT_CL'):
        return stack.gatt_cl.wait_for_notifications(expected_count=1)

    gatt.wait_notification_ev(timeout=5)

    if gatt.notification_events:
        return True

    return False


def hdl_wid_240(_: WIDParams):
    # confirm IUT in sec mode 1 level 2
    btp.gap_set_io_cap(IOCap.no_input_output)
    return True


def hdl_wid_241(_: WIDParams):
    # confirm IUT in sec mode 1 level 3
    btp.gap_set_io_cap(IOCap.keyboard_display)
    return True


def hdl_wid_242(_: WIDParams):
    """
    Please send a Security Request.
    """
    # This is done by PTS
    return False


def hdl_wid_243(_: WIDParams):
    """
    Please prepare IUT to send an advertising report with LE Supported Features type.
    """
    stack = get_stack()

    if stack.gap.le_supp_feat == None:
        return False

    # Prepare space for LE Supported Features
    stack.gap.ad.clear()
    stack.gap.ad[AdType.le_supp_feat] = stack.gap.le_supp_feat

    stack.gap.sd.clear()
    stack.gap.sd[AdType.le_supp_feat] = stack.gap.le_supp_feat

    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd)

    return True


def hdl_wid_265(_: WIDParams):
    # Please initiate a link encryption with the Lower Tester.
    btp.gap_pair()
    return True


def hdl_wid_267(_: WIDParams):
    # Click Yes if device support User Interaction to pair with the peer.
    stack = get_stack()
    return stack.gap.pair_user_interaction

def hdl_wid_300(_: WIDParams):
    # Please send non connectable advertise with periodic info.
    stack = get_stack()
    btp.gap_padv_configure(1, 150, 200)
    if stack.gap.periodic_data:
        btp.gap_padv_set_data((chr(len(stack.gap.periodic_data[1]) + 1) +
                               chr(stack.gap.periodic_data[0]) +
                               stack.gap.periodic_data[1]).encode())
    btp.gap_padv_start()
    return True

def hdl_wid_301(_: WIDParams):
    # Please click OK if IUT did not receive periodic advertising report.
    stack = get_stack()
    return stack.gap.wait_periodic_report(10)

def hdl_wid_302(_: WIDParams):
    # Perform Periodic Advertising Synchronization Establishment Procedure
    # Listening for Periodic Advertising.
    # Please click OK when IUT received
    # Periodic Advertising Synchronization Information.
    stack = get_stack()

    btp.gap_padv_create_sync(0, 0, 10, 0)
    return stack.gap.wait_periodic_established(10)

def hdl_wid_303(_: WIDParams):
    # Perform Periodic Advertising Synchronization Establishment Procedure
    # Without Listening for Periodic Advertising.
    # Please click OK when IUT received
    # Periodic Advertising Synchronization Information.
    stack = get_stack()

    btp.gap_padv_create_sync(0, 0, 10, 1)
    return stack.gap.wait_periodic_established(10)

def hdl_wid_304(_: WIDParams):
    # Please click OK if IUT did not receive periodic advertising report.
    stack = get_stack()
    return not stack.gap.wait_periodic_report(10)

def hdl_wid_305(_: WIDParams):
    # Please enter Periodic Advertising Synchronizability mode,
    # and then perform Periodic Advertising Synchronization Transfer Procedure
    stack = get_stack()
    btp.gap_padv_configure(1, 150, 200)
    if stack.gap.periodic_data:
        btp.gap_padv_set_data((chr(len(stack.gap.periodic_data[1]) + 1) +
                               chr(stack.gap.periodic_data[0]) +
                               stack.gap.periodic_data[1]).encode())
    btp.gap_padv_start()
    btp.gap_padv_create_sync(0, 0, 10, 1)
    btp.gap_padv_sync_transfer_set_info(0)
    return stack.gap.wait_periodic_established(10)

def hdl_wid_307(_: WIDParams):
    # Click OK when IUT is ready to perform Periodic Advertising Synchronization
    # Establishment Procedure without listening for periodic advertising events.

    btp.gap_padv_sync_transfer_recv(0, 10, 1)
    return True

def hdl_wid_308(_: WIDParams):
    # Click OK when IUT is ready to perform Periodic Advertising Synchronization
    # Establishment Procedure with listening for periodic advertising events.

    btp.gap_padv_sync_transfer_recv(0, 10, 0)
    return True

def hdl_wid_309(_: WIDParams):
    # Click OK when IUT receives periodic advertising synchronization
    # information.
    stack = get_stack()
    return stack.gap.wait_periodic_transfer_received(10)

def hdl_wid_400(_: WIDParams):
    btp.set_filter_accept_list()
    bd_addr = '000000000000'
    btp.gap_conn(bd_addr)
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

    btp.gap_conn()

    return True


def hdl_wid_406(_: WIDParams):
    # Please enter General Connectable Mode using private addresses.
    # Note: IUT is expected to do directed advertising with target address set
    # to peer RPA...when WID 403 is received

    stack = get_stack()

    if stack.gap.iut_has_privacy():
        addr_type = OwnAddrType.le_resolvable_private_address
    else:
        addr_type = OwnAddrType.le_identity_address

    btp.gap_adv_ind_on(ad=stack.gap.ad, own_addr_type=addr_type)

    return True


def hdl_wid_1000(params: WIDParams):
    # Please have IUT enter GAP Discoverable Mode and generate Advertising Packets.
    # Note: need to advertise with RPAs
    stack = get_stack()

    btp.gap_adv_off()
    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd, own_addr_type=OwnAddrType.le_resolvable_private_address)
    return True


def hdl_wid_1002(_: WIDParams):
    stack = get_stack()
    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None

    return passkey


def hdl_wid_1003(params: WIDParams):
    """
    Please confirm the following number matches IUT: [passkey]
    """
    pattern = '[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if stack.gap.get_passkey() is None:
        return False

    btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
    match = stack.gap.passkey.data == passkey

    # clear passkey for repeated pairing attempts
    stack.gap.passkey.data = None

    return match


def hdl_wid_2000(_: WIDParams):
    stack = get_stack()

    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None

    return passkey


def hdl_wid_2001(params: WIDParams):
    """
    The secureId is [passkey]
    """
    pattern = '[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if stack.gap.get_passkey() is None:
        return False

    btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    return True


def hdl_wid_2004(params: WIDParams):
    """
    Please confirm that 6 digit number is matched with [passkey].
    """
    pattern = '[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if stack.gap.get_passkey() is None:
        return False

    btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
    match = stack.gap.passkey.data == passkey

    # clear passkey for repeated pairing attempts
    stack.gap.passkey.data = None

    return match


def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()

    if stack.gap.iut_has_privacy():
        addr_type = OwnAddrType.le_resolvable_private_address
    else:
        addr_type = OwnAddrType.le_identity_address

    btp.gap_adv_ind_on(ad=stack.gap.ad, own_addr_type=addr_type)
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
