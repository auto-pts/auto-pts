#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
import re
from ptsprojects.stack import get_stack

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", l2cap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e.message)


# wid handlers section begin
def hdl_wid_14(desc):
    """
    Implements: TSC_MMI_iut_disable_connection
    :param desc: Initiate an L2CAP disconnection from the IUT to the PTS.
    :return:
    """
    btp.l2cap_disconn(0)

    return True


def hdl_wid_15(desc):
    """
    Implements: TSC_MMI_tester_enable_connection
    :param desc: Action: Place the IUT in connectable mode.
    :return:
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on()

    return True


def hdl_wid_22(desc):
    """
    Implements: TSC_MMI_iut_disable_acl_connection
    :param desc: Initiate an ACL disconnection from the IUT to the PTS.
    :return:
    """
    btp.gap_disconn()

    return True


def hdl_wid_36(desc):
    """
    Implements: TSC_MMI_iut_send_le_flow_control_credit
    :param desc: Command IUT to send LE Flow Control Credit to increase the LE data packet that PTS can send.
    :return:
    """

    # handled by host L2CAP layer or application
    return True


def hdl_wid_37(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_LE_data
    :param desc: Did the Upper Tester send first data frame of xxxx to the PTS.
                 Click Yes if it matched, otherwise click No.
    :return:
    """
    # This pattern is matching first data frame
    pattern = re.compile(r"frame\sof\s([0-9a-fA-F]+)")
    data = pattern.findall(desc)
    if not data:
        logging.error("%s parsing error", hdl_wid_37.__name__)
        return False

    stack = get_stack()
    tx_data = stack.l2cap.tx_data_get(0)
    if tx_data is None:
        return False

    for i in range(len(data[0])):
        if data[0][i].upper() != tx_data[i].upper():
            return False

    return True


def hdl_wid_39(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_command_not_understaood
    :param desc: Did Implementation Under Test (IUT) receive L2CAP Reject with 'command not understood' error.
                 Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received command not understood on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_40(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_data_receive
    :param desc: Please confirm the Upper Tester receive data = xxxx. Click Yes if it matched, otherwise click No.
    :return:
    """
    # This pattern is matching data received
    pattern = re.compile(r"data\s=\s([0-9a-fA-F]+)")
    data = pattern.findall(desc)
    if not data:
        logging.error("%s parsing error", hdl_wid_40.__name__)
        return False

    stack = get_stack()
    rx_data = stack.l2cap.rx_data_get_all(10)

    for value in data:
        if value.upper() in rx_data:
            rx_data.remove(value)
        else:
            return False

    return True


def hdl_wid_41(desc):
    """
    Implements: TSC_MMI_iut_send_le_credit_based_connection_request
    :param desc: Using the Implementation Under Test (IUT), send a LE Credit based connection request to PTS.
    :return:
    """
    stack = get_stack()

    btp.l2cap_conn(None, None, stack.l2cap.psm)

    return True


def hdl_wid_42(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_psm
    :param desc: Did Implementation Under Test (IUT) receive Request Reject with 'LE_PSM not supported' 0x0002 error.
                 Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received LE_PSM not supported on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_43(desc):
    """
    Implements: TSC_MMI_upper_tester_send_le_data_packet_large
    :param desc: Upper Tester command IUT to send multiple LE frame data packet to the PTS.
    :return:
    """
    stack = get_stack()

    btp.l2cap_send_data(0, "FF", 40)

    return True


def hdl_wid_48(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_resources
    :param desc: Did Implementation Under Test (IUT) receive Connection refused 'Insufficient Resources' 0x0004 error.
                 Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received insufficient resources on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_51(desc):
    """
    Implements: TSC_MMI_iut_enable_le_connection
    :param desc: Initiate or create LE ACL connection to the PTS.
    :return:
    """
    btp.gap_conn()

    return True


def hdl_wid_52(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_invalid_source_cid
    :param desc: Did Implementation Under Test (IUT) receive Connection refused 'Invalid Source CID' 0x0009 error.
                 And does not send anything over refuse LE data channel. Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received invalid source CID on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_53(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_source_cid_already_allocated
    :param desc: Did Implementation Under Test (IUT) receive Connection refused 'Source CID Already Allocated' 0x000A
                 error. And does not send anything over refuse LE data channel. Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received Source CID Already Allocated on LE based connection request it means that the channel is not
    # connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_54(desc):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_unacceptable_parameters
    :param desc: Did Implementation Under Test (IUT) receive Connection refused 'Unacceptable Parameters' 0x000B error.
                 Click Yes if it is, otherwise click No.
    :return:
    """
    stack = get_stack()

    # If IUT received Unacceptable Parameters on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)
