#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025-2026 NXP
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
from autopts.pybtp.types import WIDParams

log = logging.debug


# wid handlers section begin
def hdl_wid_0(_: WIDParams):
    """
    Take action to accept the SABM operation initiated by the tester.

    This function accepts the Set Asynchronous Balanced Mode (SABM) operation,
    which is used to establish the RFCOMM control channel.

    Note: RFCOMM server channel should be correctly set in TSPX_server_channel_iut
    """
    return True


def hdl_wid_1(_: WIDParams):
    """
    Take action to accept a new DLC initiated by the tester.

    This function is called when PTS expects the IUT to accept
    a new RFCOMM Data Link Connection (DLC) initiated by the tester.

    Returns:
        str: "OK" if the DLC was accepted successfully
    """
    return "OK"


def hdl_wid_2(_: WIDParams):
    """
    Take action to accept the DISC operation initiated by the tester.

    This function accepts the Disconnect (DISC) operation
    initiated by the tester to terminate an RFCOMM connection.
    """
    return True


def hdl_wid_3(_: WIDParams):
    """
    Take action to respond MSC.

    This function handles the response to Modem Status Command (MSC) operation
    initiated by the tester. MSC is used to convey V.24 control signals over
    RFCOMM channel.
    """
    return True


def hdl_wid_4(_: WIDParams):
    """
    Take action to respond NSC.

    This function handles the response to Non-Supported Command (NSC) operation
    initiated by the tester. NSC is used to indicate that a command is not
    supported by the RFCOMM implementation.
    """
    return True


def hdl_wid_5(_: WIDParams):
    """
    Take action to respond RPN.

    This function handles the Remote Port Negotiation (RPN) command
    from the tester. RPN is used to exchange serial port parameters
    over RFCOMM channel.
    """
    return True


def hdl_wid_6(_: WIDParams):
    """
    Take action to respond PN.

    This handler responds to the RFCOMM DLC Parameter Negotiation (PN) command
    received from the tester. The PN command is used to establish communication
    parameters for a specific DLCI.
    """
    return True


def hdl_wid_7(_: WIDParams):
    """
    Take action to respond RLS command.

    This function handles the Remote Line Status (RLS) command
    from the tester. RLS is used to convey V.24 modem control signals
    over RFCOMM channel.
    """
    return True


def hdl_wid_8(_: WIDParams):
    """
    Take action to accept the RFCOMM service level connection from the tester.

    This function configures the IUT to accept an incoming RFCOMM service
    level connection request from the PTS tester.
    """
    stack = get_stack()

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    btp.rfcomm_listen()
    return True


def hdl_wid_9(_: WIDParams):
    """
    Handle confirmation that no data is sent

    Please wait while the tester confirms no data is sent
    """
    return True


def hdl_wid_11(_: WIDParams):
    """
    Take action to respond Test.
    """
    return True


def hdl_wid_12(_: WIDParams):
    """
    Take action to initiate an SABM operation for the RFCOMM control channel.

    This function initiates an SABM (Set Asynchronous Balanced Mode) operation
    for the RFCOMM control channel to establish communication.
    """
    return True


def hdl_wid_13(_: WIDParams):
    """
    Take action to initiate an SABM operation for an RFCOMM data channel.
    """
    return "OK"


def hdl_wid_14(_: WIDParams):
    """
    Take action to initiate a DISC operation for the RFCOMM control channel.

    This function initiates a Disconnect (DISC) operation for the RFCOMM
    control channel to terminate the RFCOMM communication.
    """
    btp.rfcomm_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_17(_: WIDParams):
    """
    Take action to initiate MSC command.

    This function initiates the Modem Status Command (MSC) to convey
    V.24 modem control signals over RFCOMM channel.
    """
    return True


def hdl_wid_18(_: WIDParams):
    """
    Take action to initiate PN.
    """
    return True


def hdl_wid_20(_: WIDParams):
    """
    Take action to initiate an RFCOMM service level connection (l2cap).

    This function initiates an RFCOMM service level connection over L2CAP
    to the PTS tester device.
    """
    stack = get_stack()
    stack.gap.set_passkey(None)

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    btp.rfcomm_connect()
    return True


def hdl_wid_22(_: WIDParams):
    """
    Take action to send data on the open DLC on PTS with at least 2 frames.

    This function sends multiple data frames over the already established
    RFCOMM Data Link Connection (DLC) to the PTS tester.
    """
    btp.rfcomm_send_data(val="01", val_mtp=10)
    btp.rfcomm_send_data(val="0F", val_mtp=10)
    return True


def hdl_wid_23(_: WIDParams):
    """
    Take multiple actions to send data on the open DLC on PTS.

    This function sends multiple data frames with different content
    over the established RFCOMM Data Link Connection (DLC) to the PTS tester.
    """
    btp.rfcomm_send_data(val="01", val_mtp=10)
    btp.rfcomm_send_data(val="0F", val_mtp=10)
    btp.rfcomm_send_data(val="AA", val_mtp=10)
    return True
