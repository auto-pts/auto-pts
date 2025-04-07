#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl


log = logging.debug


def csis_wid_hdl(wid, description, test_case_name):
    log(f'{csis_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin

def hdl_wid_1(_: WIDParams):
    """
        Please make sure IUT has been locked by another Lower Tester by executing CSIS_SR_SP_BV_01_C.
    """
    btp.csis_set_member_lock(True, False)
    return True


def hdl_wid_2(_: WIDParams):
    """
        PTS will wait for half of TSPX_Lock_Timeout_Seconds IXIT Entry seconds for timeout.
    """
    return True


def hdl_wid_7(_: WIDParams):
    """
        PTS is verifying no notification of the Lock characteristic is received.
        Please wait for time out.
    """
    return True


def hdl_wid_20001(params: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """

    if params.test_case_name == "CSIS/SR/SP/BV-08-C":
        # Encrypted SIRK
        btp.csis_set_sirk_type(1)
    else:
        # Plain Text SIRK
        btp.csis_set_sirk_type(0)

    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20108(_: WIDParams):
    """
        Please send notifications for Characteristic 'Set Member Lock' to the PTS.
        Expected Value: Any value
    """
    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True
