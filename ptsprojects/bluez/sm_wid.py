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

log = logging.debug


def sm_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", sm_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e.message)


# wid handlers section begin
def hdl_wid_100(desc):
    btp.gap_conn()
    btp.gap_wait_for_connection()
    btp.gap_pair()
    return True


def hdl_wid_101(desc):
    btp.gap_conn()
    return True


def hdl_wid_102(desc):
    btp.gap_disconn()
    return True


def hdl_wid_104(desc):
    return btp.var_store_get_passkey(desc)


def hdl_wid_106(desc):
    return btp.var_store_get_wrong_passkey(desc)


def hdl_wid_108(desc):
    return True


def hdl_wid_109(desc):
    btp.gap_pair()
    return True


def hdl_wid_110(desc):
    pts_bd_addr = btp.pts_addr_get()
    pts_bd_addr_type = btp.pts_addr_type_get()
    btp.gattc_signed_write(pts_bd_addr_type, pts_bd_addr, "0001", "01")
    return True


def hdl_wid_111(desc):
    # TODO: Verify if the MAC and signed counter has been received correctly
    return True


def hdl_wid_115(desc):
    btp.gap_set_conn()
    btp.gap_adv_ind_on()
    return True


def hdl_wid_116(desc):
    # TODO: Click Yes if the failure of pairing process due to timeout has
    # been notified on the IUT.
    return True
