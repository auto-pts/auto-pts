#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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
from time import sleep

from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


def hdl_wid_6000(_: WIDParams):
    '''
    If necessary take action to accept the SDP channel connection.
    '''
    return True


def hdl_wid_6002(_: WIDParams):
    '''
    If necessary take action to accept the Service Search operation.
    '''
    return True


def hdl_wid_6001(_: WIDParams):
    '''
    If necessary take action to respond to the Service Attribute operation appropriately.
    '''
    return True


def hdl_wid_6003(_: WIDParams):
    '''
    If necessary take action to respond to the Service Search Attribute operation appropriately.
    '''
    return True


def hdl_wid_1(_: WIDParams):
    '''
    Are all browsable service classes listed below?
    '''
    return True


SDP_RECORD_HANDLE = 0


def hdl_wid_102(params: WIDParams):
    '''
    Please send an HCI connect request to establish a basic rate connection after the IUT discovers
    the Lower Tester over BR and LE.
    '''
    global SDP_RECORD_HANDLE

    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    if params.test_case_name in ["SDP/CL/SSA/BV-01-C"]:
        btp.sdp_search_attr_req(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, uuid=0x0100)
    elif params.test_case_name in ["SDP/CL/SA/BV-01-C"]:
        btp.sdp_search_req(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, uuid=0x0100)
        handle = btp.sdp_wait_for_service_record_handle()
        SDP_RECORD_HANDLE = handle
    return True


def hdl_wid_6007(_: WIDParams):
    '''
    Please order IUT to send SDP_SERVICE_ATTR_REQ to the Lower Tester.
    '''
    if SDP_RECORD_HANDLE != 0:
        btp.sdp_attr_req(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE,
                         service_record_handle=SDP_RECORD_HANDLE)
    else:
        return False
    return True


def hdl_wid_6008(_: WIDParams):
    '''
    Please order IUT to send SDP_SERVICE_SEARCH_ATTR_REQ to the Lower Tester.
    '''
    return True
