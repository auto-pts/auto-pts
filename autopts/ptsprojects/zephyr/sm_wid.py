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

from autopts.wid import generic_wid_hdl
from autopts.pybtp import btp
from autopts.ptsprojects.zephyr.iutctl import get_iut
from autopts.pybtp.types import WIDParams
from autopts.ptsprojects.stack import get_stack

log = logging.debug


def sm_wid_hdl(wid, description, test_case_name):
    log(f'{sm_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.sm'])


# wid handlers section begin
def hdl_wid_143(desc):
    zephyrctl = get_iut()

    zephyrctl.wait_iut_ready_event()
    btp.core_reg_svc_gap()
    btp.gap_read_ctrl_info()

    return True


def hdl_wid_172(_: WIDParams):
    btp.gap_conn_br()
    btp.gap_wait_for_connection()
    btp.gap_pair()
    return True


def hdl_wid_20117(_: WIDParams):
    return True


def hdl_wid_112(_: WIDParams):
    return True


def hdl_wid_100(params: WIDParams):
    btp.gap_conn()
    get_stack().gap.wait_for_connection(30)

    if (params.test_case_name.startswith("SM/CEN/SCCT/BV-03-C") or
        params.test_case_name.startswith("SM/CEN/SCCT/BV-05-C")):
        btp.gap_pair()
    return True


def hdl_wid_171(_: WIDParams):
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True
