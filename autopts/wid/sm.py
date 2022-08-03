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
import re
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams, IOCap

log = logging.debug


def sm_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", sm_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


def hdl_wid_100(_: WIDParams):
    btp.gap_conn()
    return get_stack().gap.wait_for_connection(30)


def hdl_wid_101(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_102(_: WIDParams):
    btp.gap_disconn()
    return get_stack().gap.wait_for_disconnection(30)


def hdl_wid_104(params: WIDParams):
    stack = get_stack()
    if stack.gap.io_cap == IOCap.keyboard_only:
        bd_addr = btp.pts_addr_get()
        bd_addr_type = btp.pts_addr_type_get()
        passkey = stack.gap.get_passkey()
        btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    return btp.var_store_get_passkey(params.description)


def hdl_wid_106(params: WIDParams):
    return btp.var_store_get_wrong_passkey(params.description)


def hdl_wid_107(params: WIDParams):
    passkey = btp.parse_passkey_description(params.description)
    stack = get_stack()

    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    return True


def hdl_wid_108(_: WIDParams):
    btp.gap_pair()
    return True


def hdl_wid_109(_: WIDParams):
    btp.gap_set_mitm_off()
    btp.gap_pair()
    return True


def hdl_wid_110(_: WIDParams):
    pts_bd_addr = btp.pts_addr_get()
    pts_bd_addr_type = btp.pts_addr_type_get()
    btp.gattc_signed_write(pts_bd_addr_type, pts_bd_addr, "0001", "01")
    return True


def hdl_wid_111(_: WIDParams):
    # TODO: Verify if the MAC and signed counter has been received correctly
    return True


def hdl_wid_115(_: WIDParams):
    stack = get_stack()

    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad, sd=stack.gap.sd)
    return True


def hdl_wid_116(_: WIDParams):
    # TODO: Click Yes if the failure of pairing process due to timeout has
    # been notified on the IUT.
    return True


def hdl_wid_141(params: WIDParams):
    return btp.var_store_get_passkey(params.description)


def hdl_wid_142(params: WIDParams):
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


def hdl_wid_143(params: WIDParams):
    """
    Please reset your device.
    TODO:
    """
    return True


def hdl_wid_145(_: WIDParams):
    """
    Please configure IUT's OOB data flag with 'No remote OOB data present'

    TODO: This is done by default but we should set it explicitly
    """
    return True


def hdl_wid_146(_: WIDParams):
    """
    Please configure IUT's OOB flag with 'Remote OOB data present'

    TODO: The flag will be set when we handle wid 149 - set remote oob data
    """
    return True


def hdl_wid_147(_: WIDParams):
    """
    Please enter 16 bytes IUT's OOB Data (confirmation).
    """
    r, c = btp.gap_oob_sc_get_local_data()
    return c


def hdl_wid_148(_: WIDParams):
    """
    Please enter 16 bytes IUT's OOB Key (random number).
    """
    r, c = btp.gap_oob_sc_get_local_data()
    return r


def hdl_wid_149(params: WIDParams):
    """
    Please enter the following OOB confirmation and OOB random to the IUT.
    """
    m = re.findall(r"\[([A-Fa-f0-9]+)]", params.description)
    conf, rand = m
    btp.gap_oob_sc_set_remote_data(r=rand, c=conf)
    return True


def hdl_wid_152(_: WIDParams):
    return True


def hdl_wid_154(_: WIDParams):
    return True


def hdl_wid_155(_: WIDParams):
    return True


def hdl_wid_156(_: WIDParams):
    stack = get_stack()
    return not stack.gap.is_connected(0)


def hdl_wid_173(_: WIDParams):
    return btp.gap_wait_for_pairing_fail()


def hdl_wid_1009(params: WIDParams):
    return btp.var_store_get_passkey(params.description)


def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_20011(params: WIDParams):
    return btp.var_store_get_passkey(params.description)


def hdl_wid_20115(_: WIDParams):
    btp.gap_disconn()
    return True
