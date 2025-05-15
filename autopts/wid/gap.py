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

import binascii
import copy
import logging
import re
import struct
from time import sleep

from autopts.ptsprojects.stack import ConnParams, get_stack
from autopts.pybtp import btp, defs, types
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import UUID, AdType, IOCap, OwnAddrType, Perm, Prop, WIDParams, bdaddr_reverse
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
    if params.test_case_name in ['GAP/DISC/GENM/BV-02-C']:
        return True

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
        if params.test_case_name in ['GAP/DM/LEP/BV-09-C']:
            get_stack().gap.wait_for_connection(timeout=5, conn_count=2)
            btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        else:
            btp.gap_wait_for_connection(5)

        if params.test_case_name in ['GAP/SEC/SEM/BV-05-C', 'GAP/SEC/SEM/BV-50-C',
                                     'GAP/SEC/SEM/BV-07-C', 'GAP/SEC/SEM/BV-51-C',
                                     'GAP/SEC/SEM/BV-52-C', 'GAP/SEC/SEM/BV-09-C',
                                     'GAP/SEC/SEM/BV-53-C', 'GAP/DM/BON/BV-01-C',
                                     'GAP/SEC/SEM/BV-54-C', 'GAP/SEC/SEM/BV-55-C',
                                     'GAP/DM/LEP/BV-17-C', 'GAP/SEC/SEM/BV-06-C']:
            btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        elif params.test_case_name in ['GAP/DM/LEP/BV-20-C', 'GAP/DM/LEP/BV-13-C']:
            if get_stack().gap.get_mmi_round(77) == 1:
                btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            else:
                btp.gap_disconn()
        elif params.test_case_name in ['GAP/DM/LEP/BV-22-C', 'GAP/DM/LEP/BV-18-C']:
            if get_stack().gap.get_mmi_round(77) == 1:
                btp.gap_disconn()
            else:
                btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        else:
            btp.gap_disconn()
    except types.BTPError:
        logging.debug("Ignoring expected error on disconnect")
    else:
        btp.gap_wait_for_disconnection(30)

    get_stack().gap.increase_mmi_round(77)

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
    if params.test_case_name in ['GAP/BOND/BON/BV-02-C', 'GAP/SEC/AUT/BV-19-C']:
        if params.description.startswith('Please configure the IUT into LE Security and start pairing process.'):
            return True

    stack = get_stack()

    if params.test_case_name in ['GAP/SEC/SEM/BV-28-C', 'GAP/SEC/SEM/BV-42-C']:
        if not stack.gap.delay_mmi:
            # Note: this is part of a workaround related to PTS issue 136305 which
            # is needed to properly handle two conflicting MMIs (208 and 227)
            hdl_wid_227(params, 7)
            stack.gap.delay_mmi = True

    if params.test_case_name in ['GAP/SEC/SEM/BV-50-C', 'GAP/SEC/SEM/BV-51-C',
                                 'GAP/SEC/SEM/BV-52-C', 'GAP/SEC/SEM/BV-53-C',
                                 'GAP/SEC/SEM/BV-54-C', 'GAP/SEC/SEM/BV-55-C']:
        btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    else:
        btp.gap_pair()

    if params.test_case_name in ['GAP/SEC/SEM/BV-52-C', 'GAP/SEC/SEM/BV-53-C']:
        passkey = stack.gap.get_passkey()
        if passkey is not None:
            btp.gap_passkey_confirm_rsp(btp.pts_addr_get(), defs.BTP_BR_ADDRESS_TYPE, passkey)

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
        for _i in range(gatt.attr_value_get_changed_cnt(handle=gatt.signed_write_handle), 3):
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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
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

    (properties, value_handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)

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

    if stack.gap.uri is None:
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
        if not stack.gap.is_connected():
            logging.debug("Ignoring expected error on disconnected")
        else:
            return False

    return True


def hdl_wid_208(params: WIDParams):
    stack = get_stack()

    if params.test_case_name in ['GAP/SEC/SEM/BV-26-C']:
        if not stack.gap.delay_mmi:
            # Note: this is part of a workaround related to PTS issue 136305 which
            # is needed to properly handle two conflicting MMIs (208 and 227)
            hdl_wid_227(params, 7)
            stack.gap.delay_mmi = True

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


def hdl_wid_227(params: WIDParams, desc_handle=None):
    # There seems to be issue in PTS regarding using WID112 and WID227 in that test
    # Should be removed if PTS fix this.
    stack = get_stack()

    if params.test_case_name in ['GAP/SEC/SEM/BV-26-C', 'GAP/SEC/SEM/BV-28-C', 'GAP/SEC/SEM/BV-42-C']:
        # Note: this is part of a workaround related to PTS issue 136305 which
        # is needed to properly handle two conflicting MMIs (208 and 227)
        if stack.gap.delay_mmi is True:
            return True

    if params.test_case_name in ['GAP/SEC/AUT/BV-19-C']:
        btp.gap_pair()
        return True

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    handle = btp.parse_handle_description(params.description) or desc_handle
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

        if btp.verify_att_error("authentication error"):
            btp.gap_pair()

        if btp.verify_att_error("insufficient encryption"):
            btp.gap_pair()

    stack.gap.delay_mmi = True
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

    if stack.gap.le_supp_feat is None:
        return False

    # Prepare space for LE Supported Features
    stack.gap.ad.clear()
    stack.gap.ad[AdType.le_supp_feat] = stack.gap.le_supp_feat

    stack.gap.sd.clear()
    stack.gap.sd[AdType.le_supp_feat] = stack.gap.le_supp_feat

    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd)

    return True


def hdl_wid_246(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    perm = Perm.write_authn

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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & perm:
            return format(handle, 'x').zfill(4)

    return 0


def hdl_wid_247(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    perm = Perm.write_authn

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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & perm:
            return format(handle, 'x').zfill(4)

    return 0


def hdl_wid_248(_: WIDParams):
    attrs = btp.gatts_get_attrs(type_uuid='2803')
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    perm = Perm.write_enc

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

        (props, handle, chrc_uuid) = struct.unpack(f"<BH{uuid_len}s", val)
        chrc_value_attr = btp.gatts_get_attrs(start_handle=handle,
                                              end_handle=handle)
        if not chrc_value_attr:
            continue

        (handle, permission, type_uuid) = chrc_value_attr[0]
        if permission & perm:
            return format(handle, 'x').zfill(4)

    return False


def hdl_wid_265(params: WIDParams):
    # Please initiate a link encryption with the Lower Tester.
    if params.test_case_name in ['GAP/SEC/SEM/BI-12-C', 'GAP/SEC/SEM/BI-06-C',
                                 'GAP/SEC/SEM/BI-17-C', 'GAP/SEC/SEM/BI-18-C']:
        btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    elif params.test_case_name in ['GAP/SEC/SEM/BI-07-C', 'GAP/SEC/SEM/BI-19-C']:
        btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                        level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_3)
    elif params.test_case_name in ['GAP/SEC/SEM/BI-08-C']:
        btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                        level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_4)
    else:
        btp.gap_pair()
    return True


def hdl_wid_267(_: WIDParams):
    # Click Yes if device support User Interaction to pair with the peer.
    stack = get_stack()
    return stack.gap.pair_user_interaction


def hdl_wid_300(params: WIDParams):
    # Please send non-connectable advertise with periodic info.
    stack = get_stack()
    btp.gap_padv_configure(1, 150, 200)
    if stack.gap.periodic_data:
        btp.gap_padv_set_data((chr(len(stack.gap.periodic_data[1]) + 1) +
                               chr(stack.gap.periodic_data[0]) +
                               stack.gap.periodic_data[1]).encode())
    btp.gap_padv_start()

    if params.test_case_name in ['GAP/SEC/SEM/BV-34-C', 'GAP/SEC/SEM/BV-35-C']:
        broadcast_code = None
        if params.test_case_name in ['GAP/SEC/SEM/BV-35-C']:
            # broadcast code from TSPX_broadcast_code in ptsproject/x/gap.py
            broadcast_code = stack.gap.big_broadcast_code
        btp.gap_create_big(0, 1, 10000, 20, 0, 0, broadcast_code)

        if not stack.gap.wait_bis_data_path_setup():
            log('Failed to setup BIS data path')
            return False

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

    btp.gap_padv_create_sync(0, 0, 100, 0)
    return stack.gap.wait_periodic_established(10)


def hdl_wid_303(_: WIDParams):
    # Perform Periodic Advertising Synchronization Establishment Procedure
    # Without Listening for Periodic Advertising.
    # Please click OK when IUT received
    # Periodic Advertising Synchronization Information.
    stack = get_stack()

    btp.gap_padv_create_sync(0, 0, 100, 1)
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
    btp.gap_padv_sync_transfer_set_info(0)
    return True


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
    pattern = r'[\d]{6}'
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
    Or, Please verify the passKey is correct: [passkey]
    """
    pattern = r'[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if params.test_case_name in ['GAP/IDLE/BON/BV-04-C', 'GAP/IDLE/BON/BV-06-C',
                                 'GAP/SEC/SEM/BV-06-C', 'GAP/SEC/SEM/BV-07-C',
                                 'GAP/SEC/SEM/BV-51-C', 'GAP/SEC/SEM/BV-09-C',
                                 'GAP/SEC/SEM/BV-53-C', 'GAP/SEC/SEM/BV-11-C',
                                 'GAP/SEC/SEM/BV-12-C', 'GAP/SEC/SEM/BV-13-C',
                                 'GAP/SEC/SEM/BV-14-C', 'GAP/SEC/SEM/BV-15-C',
                                 'GAP/SEC/SEM/BV-47-C', 'GAP/SEC/SEM/BV-48-C',
                                 'GAP/SEC/SEM/BV-49-C', 'GAP/SEC/SEM/BV-16-C',
                                 'GAP/SEC/SEM/BV-17-C', 'GAP/SEC/SEM/BV-18-C',
                                 'GAP/SEC/SEM/BV-54-C', 'GAP/SEC/SEM/BV-19-C',
                                 'GAP/SEC/SEM/BV-20-C', 'GAP/SEC/SEM/BV-55-C',
                                 'GAP/SEC/SEM/BI-03-C', 'GAP/SEC/SEM/BI-07-C',
                                 'GAP/SEC/SEM/BI-31-C', 'GAP/SEC/SEM/BI-16-C',
                                 'GAP/SEC/SEM/BI-04-C', 'GAP/SEC/SEM/BI-19-C',
                                 'GAP/SEC/SEM/BI-08-C', 'GAP/SEC/SEM/BI-27-C',
                                 'GAP/SEC/SEM/BI-32-C', 'GAP/SEC/SEM/BI-26-C',
                                 'GAP/DM/LEP/BV-13-C', 'GAP/SEC/SEM/BI-29-C',
                                 'GAP/SEC/SEM/BI-30-C', 'GAP/SEC/SEM/BI-33-C',
                                 'GAP/SEC/SEM/BV-52-C']:
        bd_addr_type = defs.BTP_BR_ADDRESS_TYPE

    if stack.gap.get_passkey() is None:
        return False

    if 'Please verify the passKey is correct' in params.description:
        btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
    else:
        btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    return True


def hdl_wid_2004(params: WIDParams):
    """
    Please confirm that 6 digit number is matched with [passkey].
    """
    pattern = r'[\d]{6}'
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


def hdl_wid_20115(params: WIDParams):
    if params.test_case_name in ['GAP/DM/LEP/BI-01-C', 'GAP/SEC/SEM/BI-32-C',
                                 'GAP/SEC/SEM/BI-33-C']:
        btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        return True

    btp.gap_disconn()
    return True


def hdl_wid_20100(params: WIDParams):
    btp.gap_conn()
    if params.test_case_name in ['GAP/DM/LEP/BV-20-C', 'GAP/DM/LEP/BV-17-C',
                                 'GAP/DM/LEP/BV-18-C', 'GAP/DM/LEP/BV-13-C']:
        btp.gap_pair()
    return True


def hdl_wid_2142(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_31(_: WIDParams):
    """
    Please make IUT not discoverable. Press OK to continue.
    """
    btp.gap_set_nondiscov()
    return True


def hdl_wid_32(_: WIDParams):
    """
    Please make IUT limited discoverable. Press OK to continue.
    """
    btp.gap_set_limdiscov()
    return True


def hdl_wid_160(_: WIDParams):
    """
    Please set IUT to limited discovery mode. Lower tester is continue using
    GIAC to Inquiry and waiting for Inquiry result.
    """
    btp.gap_set_limdiscov()
    return True


def hdl_wid_145(_: WIDParams):
    """
    Waiting for limited discovery to time out so it is not able to discover IUT.
    """
    return True


def hdl_wid_33(params: WIDParams):
    """
    Please make IUT general discoverable.
    """
    btp.gap_set_nondiscov()
    btp.gap_set_gendiscov()

    if (
            params.test_case_name in ['GAP/SEC/SEM/BV-10-C']
            or (
            params.test_case_name in ['GAP/SEC/SEM/BI-24-C']
            and get_stack().gap.get_mmi_round(33) == 1
    )
    ):
        # ALT1 - Responder the test results in pass when the IUT initiates the Secure Simple
        # Pairing procedure autonomously before the Lower Tester initiates the L2CAP connection.
        btp.gap_wait_for_connection()
        btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_sec_lvl_change(2)

    get_stack().gap.increase_mmi_round(33)

    return True


def hdl_wid_34(_: WIDParams):
    """
    Please make IUT not connectable. Press OK to continue.
    """
    btp.gap_set_nonconn()
    return True


def hdl_wid_105(_: WIDParams):
    """
    Please make IUT connectable. Press OK to continue.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True


def hdl_wid_222(_: WIDParams):
    """
    Please initiate a BR/EDR security authentication and pairing with interaction of HCI commands.
    """
    return True


def hdl_wid_146(_: WIDParams):
    """
    Please start general inquiry. Click 'Yes' If IUT does discovers PTS and ready for PTS to
    initiate a create connection otherwise click 'No'.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()
    return btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE)


def hdl_wid_147(_: WIDParams):
    """
    Please start limited inquiry. Click 'Yes' If IUT does discovers PTS otherwise click 'No'.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='limited')
    sleep(10)
    btp.gap_stop_discov()
    return btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE)


def hdl_wid_164(_: WIDParams):
    """
    Please confirm that IUT is in Idle mode with security mode 4. Press OK when IUT is ready to
    start device discovery.
    """
    return True


def hdl_wid_165(params: WIDParams):
    """
    Please confirm that IUT has discovered PTS and retrieved its name 'PTS-GAP-E449'.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    pattern = re.compile(r"'(.*)'")
    macthed = pattern.findall(params.description)
    if not macthed:
        logging.error("parsing error")
        return False

    name = macthed[0]
    name = binascii.hexlify(name.encode()).decode()

    return btp.check_scan_rep_and_rsp(name, name)


def hdl_wid_102(params: WIDParams):
    """
    Please send an HCI connect request to establish a basic rate connection after the IUT
    discovers the Lower Tester over BR and LE.
    """
    if params.test_case_name in ['GAP/SEC/SEM/BI-11-C', 'GAP/SEC/SEM/BI-02-C',
                                 'GAP/SEC/SEM/BI-03-C', 'GAP/SEC/SEM/BI-14-C',
                                 'GAP/SEC/SEM/BI-15-C', 'GAP/SEC/SEM/BI-16-C',
                                 'GAP/SEC/SEM/BI-04-C']:
        return True

    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    if params.test_case_name in ['GAP/DM/LEP/BV-09-C']:
        get_stack().gap.wait_for_connection(timeout=30, conn_count=2)
    else:
        btp.gap_wait_for_connection()

    get_stack().gap.increase_mmi_round(102)

    if get_stack().gap.get_mmi_round(102) > 1 and params.test_case_name in ['GAP/SEC/SEM/BI-32-C']:
        return True

    if params.test_case_name in ['GAP/IDLE/BON/BV-05-C', 'GAP/IDLE/BON/BV-06-C',
                                 'GAP/SEC/SEM/BV-50-C', 'GAP/SEC/SEM/BV-06-C',
                                 'GAP/SEC/SEM/BV-07-C', 'GAP/SEC/SEM/BV-51-C',
                                 'GAP/SEC/SEM/BV-52-C', 'GAP/SEC/SEM/BV-09-C',
                                 'GAP/SEC/SEM/BV-53-C', 'GAP/DM/BON/BV-01-C',
                                 'GAP/SEC/SEM/BV-18-C', 'GAP/SEC/SEM/BV-54-C',
                                 'GAP/SEC/SEM/BV-19-C', 'GAP/SEC/SEM/BV-55-C',
                                 'GAP/SEC/SEM/BI-12-C', 'GAP/SEC/SEM/BI-06-C',
                                 'GAP/SEC/SEM/BI-07-C', 'GAP/SEC/SEM/BI-17-C',
                                 'GAP/SEC/SEM/BI-18-C', 'GAP/SEC/SEM/BI-19-C',
                                 'GAP/SEC/SEM/BI-08-C', 'GAP/DM/LEP/BV-09-C',
                                 'GAP/DM/LEP/BV-10-C', 'GAP/DM/LEP/BV-12-C',
                                 'GAP/DM/LEP/BV-15-C', 'GAP/DM/LEP/BV-17-C',
                                 'GAP/DM/LEP/BV-22-C', 'GAP/DM/LEP/BV-18-C',
                                 'GAP/SEC/SEM/BI-27-C', 'GAP/SEC/SEM/BI-26-C',
                                 'GAP/SEC/SEM/BI-25-C', 'GAP/DM/LEP/BV-13-C']:
        return True

    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    if params.test_case_name in ['GAP/SEC/SEM/BV-25-C', 'GAP/SEC/SEM/BV-30-C']:
        passkey = get_stack().gap.get_passkey()
        if passkey is not None:
            btp.gap_passkey_confirm_rsp(btp.pts_addr_get(), defs.BTP_BR_ADDRESS_TYPE, passkey)

    return True


def hdl_wid_264(_: WIDParams):
    """
    Please send L2CAP Connection Request to PTS.
    """
    stack = get_stack()
    l2cap = stack.l2cap
    btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu)
    return True


def hdl_wid_166(_: WIDParams):
    """
    Please order the IUT to go in connectable mode and in security mode 4. Press OK to continue.
    """
    return True


def hdl_wid_251(_: WIDParams):
    """
    Please send L2CAP Connection Response to PTS.
    """
    return True


def hdl_wid_231(_: WIDParams):
    """
    Please start the Bonding Procedure in bondable mode.
    After Bonding Procedure is completed, please send a disconnect request to terminate connection.
    """
    btp.gap_wait_for_sec_lvl_change(level=2)
    btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_103(params: WIDParams):
    """
    Please initiate BR/EDR security authentication and pairing to establish a service level
    enforced security!
    After that, please create the service channel using L2CAP Connection Request.
    """
    stack = get_stack()
    br_psm = 0x1001
    br_psm_2 = 0x2001

    stack.gap.set_passkey(None)

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()

    if params.test_case_name in ['GAP/SEC/SEM/BV-09-C', 'GAP/SEC/SEM/BV-53-C']:
        if get_stack().gap.get_mmi_round(103) == 0:
            btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        else:
            btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                            mode=defs.BTP_GAP_CMD_PAIR_V2_MODE_4,
                            level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_3)

        if get_stack().gap.get_mmi_round(103) == 0:
            passkey = stack.gap.get_passkey()
            if passkey is not None:
                btp.gap_passkey_confirm_rsp(btp.pts_addr_get(), defs.BTP_BR_ADDRESS_TYPE, passkey)
            stack.l2cap_init(br_psm_2, stack.l2cap.initial_mtu)
            btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, stack.l2cap.psm, stack.l2cap.initial_mtu)
        else:
            stack.l2cap_init(br_psm, stack.l2cap.initial_mtu)
            btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, stack.l2cap.psm, stack.l2cap.initial_mtu)
    else:
        if params.test_case_name in ['GAP/SEC/SEM/BV-07-C', 'GAP/SEC/SEM/BV-52-C']:
            btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                            mode=defs.BTP_GAP_CMD_PAIR_V2_MODE_4,
                            level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_3)
        else:
            btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

        l2cap = stack.l2cap
        btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu)

    get_stack().gap.increase_mmi_round(103)
    return True


def hdl_wid_167(_: WIDParams):
    """
    Please start simple pairing procedure.
    """
    return True


def hdl_wid_151(_: WIDParams):
    """
    Please set IUT into bondable mode. Press OK to continue.
    """
    btp.gap_set_bondable_on()
    return True


def hdl_wid_20117(params: WIDParams):
    """
    Please start encryption. Use previously distributed key if available.
    Description: Verify that the Implementation Under Test (IUT) can
    successfully start and complete encryption.
    """
    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    if params.test_case_name in ['GAP/DM/LEP/BV-18-C']:
        passkey = get_stack().gap.get_passkey()
        if passkey is not None:
            btp.gap_passkey_confirm_rsp(btp.pts_addr_get(), defs.BTP_BR_ADDRESS_TYPE, passkey)
    return True


def hdl_wid_36(_: WIDParams):
    """
    Please start general discovery over BR/EDR and over LE. If IUT discovers PTS
    with both BR/EDR and LE method, press OK.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    btp.gap_start_discov(transport='le', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    if not btp.check_discov_results():
        return False

    get_stack().gap.reset_discovery()
    return True


def hdl_wid_7(_: WIDParams):
    """
    Please start limited discovery over BR/EDR and over LE. If IUT discovers PTS
    with both BR/EDR and LE method, press OK.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='limited')
    btp.gap_start_discov(transport='le', discov_type='passive', mode='limited')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    if not btp.check_discov_results():
        return False

    get_stack().gap.reset_discovery()
    return True


def hdl_wid_123(_: WIDParams):
    """
    Please start limited discovery over BR/EDR and over LE. If IUT does not discovers PTS
    with both BR/EDR and LE method, press OK.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='limited')
    btp.gap_start_discov(transport='le', discov_type='passive', mode='limited')
    sleep(10)
    btp.gap_stop_discov()

    if btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    if btp.check_discov_results():
        return False

    get_stack().gap.reset_discovery()
    return True


def hdl_wid_86(_: WIDParams):
    """
    Please start device name discovery over BR/EDR . If IUT discovers PTS, press OK to continue.
    """
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False
    get_stack().gap.reset_discovery()
    return True


def hdl_wid_252(_: WIDParams):
    """
    Please send L2CAP Connection Response with Security Blocked to PTS.
    """
    return True


def hdl_wid_220(_: WIDParams):
    """
    Please confirm IUT rejects the Upper Tester's request to establish a channel to access the
    service on the Lower Tester
    Click Yes, if rejected
    Click No, if not rejected.
    """
    stack = get_stack()
    if stack.gap.wait_for_disconnection(timeout=3):
        # ACL connection has been disconnect due to the AUTH failed
        return True
    l2cap = stack.l2cap
    btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu)
    if stack.l2cap.wait_for_connection(chan_id=2, timeout=30):
        return False
    return True


def hdl_wid_255(_: WIDParams):
    """
    Please bring IUT to Security Mode 2. Press OK to continue.
    """
    return True


def hdl_wid_266(params: WIDParams):
    """
    Please confirm that the IUT signals to the Upper Tester that the channel establishment
    failure after link encryption.
    Click 'Yes' If there is channel establishment failure otherwise click 'No'.
    """
    if params.test_case_name in ['GAP/SEC/SEM/BI-27-C']:
        return not get_stack().gap.gap_wait_for_encrypted()

    btp.gap_wait_for_disconnection()
    return True


def hdl_wid_256(_: WIDParams):
    """
    Please bring IUT to Mode 4 level 1 security and make IUT general discoverable.
    Press OK to continue.
    """
    return True


def hdl_wid_260(_: WIDParams):
    """
    Please bring IUT to Security Mode 4 level 1. Press OK to continue.
    """
    return True


def hdl_wid_257(_: WIDParams):
    """
    Please bring IUT to Mode 4 level 2 security and make IUT general discoverable.
    Press OK to continue.
    """
    return True


def hdl_wid_261(_: WIDParams):
    """
    Please bring IUT to Security Mode 4 level 2. Press OK to continue.
    """
    return True


def hdl_wid_258(_: WIDParams):
    """
    Please bring IUT to Mode 4 level 3 security and make IUT general discoverable.
    Press OK to continue.
    """
    return True


def hdl_wid_262(_: WIDParams):
    """
    Please bring IUT to Security Mode 4 level 3. Press OK to continue.
    """
    return True


def hdl_wid_259(_: WIDParams):
    """
    Please bring IUT to Mode 4 level 4 security and make IUT general discoverable.
    Press OK to continue.
    """
    return True


def hdl_wid_263(_: WIDParams):
    """
    Please bring IUT to Security Mode 4 level 4. Press OK to continue.
    """
    return True


def hdl_wid_213(_: WIDParams):
    """
    Please make sure the IUT does initiate the BR secure connection pairing proccess.
    Click OK when ready.
    """
    return True


def hdl_wid_221(_: WIDParams):
    """
    Please initiate BR/EDR Secure Simple Pairing then LE Secure Connections pairing for
    this test case.
    """
    return True


def hdl_wid_217(_: WIDParams):
    """
    Please initiate security after upgrade the LTK to authenticated. Click OK when ready.
    """
    btp.gap_pair_v2(level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_4)
    return True


def hdl_wid_216(params: WIDParams):
    """
    Please initiate security after upgrade the BR/EDR link key to authenticated.
    Click OK when ready.
    """
    if params.test_case_name in ['GAP/DM/LEP/BV-13-C']:
        btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_4)

    return True


def hdl_wid_273(params: WIDParams):
    """
    Please trigger channel creation. Expect to perform link encryption before channel creation.
    """
    if params.test_case_name in ['GAP/SEC/SEM/BI-25-C']:
        btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_2)
        return True

    if params.test_case_name in ['GAP/SEC/SEM/BI-26-C']:
        btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_3)
        return True

    btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_4)
    return True


def hdl_wid_274(_: WIDParams):
    '''
    Please send L2CAP G-Frame with unicast data. Expect to perform link encryption before sending G-Frame.
    '''
    return True


def hdl_wid_352(params: WIDParams):
    '''
    Please click OK when IUT establishes BIG sync, and ready to receive ISO data.
    '''
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    btp.gap_start_discov(transport='le', discov_type='passive', mode='observe')
    sleep(10)
    btp.gap_stop_discov()
    if not btp.check_discov_results(addr_type=addr_type, addr=addr):
        log('Peer device not found.')
        return False

    stack = get_stack()

    log('Synchronizing to broadcast')
    btp.gap_padv_create_sync(0, 0, 0x200, 0)
    if not stack.gap.wait_periodic_established(10):
        log('Failed to periodic sync established')
        return False

    biginfo = stack.gap.read_periodic_biginfo()
    if not biginfo:
        log('Failed to read periodic biginfo')
        return False

    if biginfo.encryption:
        # broadcast code from TSPX_broadcast_code in ptsproject/x/gap.py
        broadcast_code = stack.gap.big_broadcast_code
    else:
        broadcast_code = None

    btp.gap_big_create_sync(biginfo.sid, biginfo.num_bis, 1, 255, broadcast_code)
    if not stack.gap.wait_big_established():
        log('BIG sync establishment failed')
        return False

    if not stack.gap.wait_bis_data_path_setup():
        log('Failed to setup BIS data path')
        return False

    return True


def hdl_wid_351(_: WIDParams):
    '''
    Wait for Broadcast ISO request.
    '''
    return True


def hdl_wid_356(_: WIDParams):
    '''
    Please broadcast valid ISO data packets (more than 3 packets).
    '''
    stack = get_stack()
    try:
        for _ in range(1, 100):
            for bis_id in stack.gap.big_bis_data_path_setup:
                btp.gap_bis_broadcast(bis_id, '00')
    except types.BTPError:
        log("Ignore BIS broadcast failure")

    return True


def hdl_wid_355(params: WIDParams):
    '''
    Please verify that IUT received BIS data of 0x01, 0x02, 0x03, 0x04, 0x05, and 0x06
    '''
    pattern = r'0x([0-9a-fA-F]{2})'
    hex_values = re.findall(pattern, params.description)

    if not hex_values:
        log('No hex values found in description')
        return False

    expected_data = bytes([int(val, 16) for val in hex_values])
    log(f'Expected data: {expected_data.hex()}')

    for _ in range(1, 100):
        data = get_stack().gap.read_bis_stream_received_data()
        log(f'Received data: {data}')

        if not data:
            log('No BIS data received')
            return False

        if expected_data in data.stream_data:
            return True

    log('Incorrect BIS data received')
    return False
