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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import BTPError, WIDParams

log = logging.debug


def avctp_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{avctp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(_: WIDParams):
    """
    description: Attempt to connect another AVCTP channel using the same PSM.
    The second attempt should not be allowed to be sent.
    """
    try:
        btp.avrcp_control_connect()
    except BTPError as err:
        log(f"Caught an error: {str(err)}")
        return str(err) == "Error opcode in response!"
    else:
        return False


def hdl_wid_8(_: WIDParams):
    """
    description: Take action to reject the AVCTP DATA request with an invalid profile id.
    """
    return True


def hdl_wid_24(_: WIDParams):
    """
    description: Press 'OK' if the following condition was met :
    The IUT returns the following AVCT_SendMessage output parameter values to the Upper Tester:
    * Result = 0x0000 (Request accepted)
    """
    return False


def hdl_wid_25(_: WIDParams):
    """
    description: Press 'OK' if the following conditions were met :
    1. The IUT returns the following AVCT_EventRegistration output parameters to the Upper Tester:
    * Result = 0x0000 (Event successfully registered)

    2. The IUT calls the MessageInd_CBTest_System callback function of the test system with the following parameters:
    * BD_ADDR = BD_ADDRTest_System
    * Transaction = TRANSTest_System
    * Type = 0
    * Data = DATA[]Lower_Tester
    * Length = LengthOf(DATA[]Lower_Tester)
    """
    return True


def hdl_wid_33(_: WIDParams):
    """
    description: Press 'OK' if the following condition was met :
    The IUT receives three AVCTP packets from the Lower Tester,
    reassembles the message and calls the MessageInd_CBTestSystem callback function with the following parameters:
    * BD_ADDR = BD_ADDRTest_System
    * Transaction = TRANSTest_System
    * Type = 0x01 (Command Message)
    * Data = ADDRESSdata_buffer (Buffer holding DATA[]Lower_Tester)
    * Length = LengthOf(DATA[]Lower_Tester)
    """
    return True


def hdl_wid_37(_: WIDParams):
    """
    description: Did the IUT receive a properly formatted GetElementAttributes response?
    """
    return True


def hdl_wid_39(_: WIDParams):
    """
    description: Take action to send the Get Element Attributes command with including all the attributes (0x00 - 0x08).
    """
    btp.avrcp_get_element_attrs([0, 1, 2, 3, 4, 5, 6, 7, 8])
    if btp.avrcp_rx_data_get(defs.BTP_AVRCP_EV_GET_ELEMENT_ATTRS_RSP) is None:
        return False
    return True


def hdl_wid_40(_: WIDParams):
    """
    description: Take action to initiate any AV/C Command.
    """
    btp.avrcp_unit_info()
    if btp.avrcp_rx_data_get(defs.BTP_AVRCP_EV_UNIT_INFO_RSP) is None:
        return False
    return True


def hdl_wid_41(_: WIDParams):
    """
    description: Action: Place the IUT in connectable mode.
    """
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_42(_: WIDParams):
    """
    description: Using the Implementation Under Test(IUT), initiate ACL Create Connection Request to the PTS.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    return True


def hdl_wid_2002(_: WIDParams):
    """
    description: Please wait while PTS creates an AVCTP control channel connection.
    """
    btp.avrcp_wait_for_connection(defs.BTP_AVRCP_EV_CONTROL_CONNECTED)
    return True


def hdl_wid_2004(_: WIDParams):
    """
    description: Please wait while PTS disconnects the AVCTP control channel connection.
    """
    btp.avrcp_wait_for_disconnection(defs.BTP_AVRCP_EV_CONTROL_CONNECTED)

    return True


def hdl_wid_2006(_: WIDParams):
    """
    description: Take action to initiate a control channel connection by sending a connection request to the PTS from the IUT.
    """
    btp.avrcp_control_connect()
    return btp.avrcp_wait_for_connection(defs.BTP_AVRCP_EV_CONTROL_CONNECTED)


def hdl_wid_2008(params: WIDParams):
    """
    description: Take action to disconnect the AVCTP control channel.
    """
    stack = get_stack()
    if stack.avrcp.is_connected(btp.pts_addr_get(None), defs.BTP_AVRCP_EV_BROWSING_CONNECTED):
        btp.avrcp_browsing_disconnect()
        if not btp.avrcp_wait_for_disconnection(defs.BTP_AVRCP_EV_BROWSING_CONNECTED):
            return False
    btp.avrcp_control_disconnect()
    if not btp.avrcp_wait_for_disconnection(defs.BTP_AVRCP_EV_CONTROL_CONNECTED):
        return False

    if params.test_case_name in ['AVCTP/CT/CCM/BV-02-C', 'AVCTP/TG/CCM/BV-02-C']:
        btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_disconnection()

    return True


def hdl_wid_3006(_: WIDParams):
    """
    description: Take action to send a valid response to the [Get Element Attributes] command sent by the PTS.
    """
    return True


def hdl_wid_3021(_: WIDParams):
    """
    description: Take action to send a valid response to the [Set Absolute Volume] command sent by the PTS.
    """
    return True
