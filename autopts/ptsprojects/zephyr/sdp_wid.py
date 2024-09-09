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
from time import sleep

log = logging.debug


def sdp_wid_hdl(wid, description, test_case_name):
    log(f'{sdp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])

def hdl_wid_6000(_: WIDParams):
    return True

def hdl_wid_6002(_: WIDParams):
    return True

def hdl_wid_6001(_: WIDParams):
    return True

def hdl_wid_6003(_: WIDParams):
    return True

def hdl_wid_1(_: WIDParams):
    return True

def hdl_wid_102(params: WIDParams):
    btp.gap_start_discov(transport='bredr')
    sleep(30)  # Give some time to discover devices
    if btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        btp.clear_discov_results()
        btp.gap_conn_br()
        btp.gap_wait_for_connection()
        if params.test_case_name in ["SDP/CL/SSA/BV-01-C"]:
            btp.sdp_search_attr_req(uuid=0x0100)
        else:
        #     btp.sdp_search_req(uuid=0x0100)
        #     handle = btp.sdp_wait_for_service_record_handle()
            handle = 0x10002
            if handle != 0:
                btp.sdp_attr_req(service_record_handle=handle)
            else:
                return False
    return True

def hdl_wid_6008(_: WIDParams):
    btp.sdp_search_attr_req(uuid=0x0100)
    return True

def hdl_wid_6007(_: WIDParams):
    btp.sdp_search_req(uuid=0x0100)
    return True
