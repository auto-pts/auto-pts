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
import secrets

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


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


def hdl_wid_20(params: WIDParams):
    """
        Please update the characteristic Set Identity Resolving Key value with different data and send a notification.
        Please update the characteristic Coordinated Set Size value with different data and send a notification.
    """
    # The same wid is used for two different test cases, with different descriptions, so we check the description.
    if 'Set Identity Resolving Key' in params.description:
        # Generate 16 random characters for SIRK
        sirk = secrets.token_hex(8)
        btp.csis_set_sirk(sirk)

    elif 'Coordinated Set Size' in params.description:
        # Increase the Coordinated Set Size by 1
        stack = get_stack()

        if stack.csis is None:
            logging.error("hdl_wid_20: stack.csis is not initialized")
            return False

        stack.csis.set_size += 1
        btp.csis_set_set_size(stack.csis.set_size, 1)

    else:
        logging.error(f"hdl_wid_20: Unknown description: {params.description}")
        return False

    return True


def hdl_wid_21(params: WIDParams):
    """
        Please update the characteristic Set Identity Resolving Key value with different data and enter connectable mode.
        Please update the characteristic Coordinated Set Size value with different data and enter connectable mode.
    """

    # The IUT is already in connectable mode from previous WID.
    return hdl_wid_20(params)


def hdl_wid_20001(params: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """

    if params.test_case_name == "CSIS/SR/SP/BV-07-C":
        btp.csis_set_sirk_type(defs.CSIS_SIRK_TYPE_OOB_ONLY)
    elif params.test_case_name == "CSIS/SR/SP/BV-08-C":
        btp.csis_set_sirk_type(defs.CSIS_SIRK_TYPE_ENCRYPTED)
    else:
        btp.csis_set_sirk_type(defs.CSIS_SIRK_TYPE_PLAINTEXT)

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
