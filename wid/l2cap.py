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
import re
import socket
import sys
import time

from ptsprojects.stack import get_stack
from pybtp import btp, defs
from pybtp.types import BTPError, L2CAPConnectionResponse

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", l2cap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError as e:
        logging.exception(e)


def l2cap_wid_hdl_one_ecfc_chan(wid, description, test_case_name):
    log("%s, %r, %r, %s", l2cap_wid_hdl.__name__, wid, description,
        test_case_name)

    if wid == 255:
        stack = get_stack()
        l2cap = stack.l2cap

        btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu, 1, 1)
        return True
    else:
        return l2cap_wid_hdl(wid, description, test_case_name)



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
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_22(desc):
    """
    Implements: TSC_MMI_iut_disable_acl_connection
    :param desc: Initiate an ACL disconnection from the IUT to the PTS.
    :return:
    """
    btp.gap_wait_for_connection()
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
    :param desc: Did the Upper Tester send the data xxxx to the PTS?
                 Click Yes if it matched, otherwise click No.
    :return:
    """
    # This pattern is matching first data frame
    pattern = re.compile(r"send\sthe\sdata\s([0-9a-fA-F]+)")
    data = pattern.findall(desc)
    if not data:
        logging.error("%s parsing error", hdl_wid_37.__name__)
        return False

    stack = get_stack()
    tx_data = stack.l2cap.tx_data_get(0)
    if tx_data is None or len(tx_data) < 1:
        return False

    return data[0] == tx_data[0]


def hdl_wid_38(desc):
    """
    Implements: TSC_MMI_upper_tester_send_LE_data_packet1
    :param desc: Upper Tester command IUT to send a nonsegmented LE data packet to the PTS with any values.
    :return:
    """
    stack = get_stack()
    channel = stack.l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF')
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
    :param desc: Please confirm the Upper Tester receive data
    :return:
    """
    stack = get_stack()
    rx_data = stack.l2cap.rx_data_get_all(10)
    return rx_data is not None


def hdl_wid_41(desc):
    """
    Implements: TSC_MMI_iut_send_le_credit_based_connection_request
    :param desc: Using the Implementation Under Test (IUT), send a LE Credit based connection request to PTS.
    :return:
    """
    stack = get_stack()

    btp.l2cap_conn(None, None, stack.l2cap.psm, 256)

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
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF' * channel.peer_mps)

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


def hdl_wid_55(desc):
    """
    :param desc: Upper Tester command IUT to send LE data packet to the PTS with
    larger or equal to the TSPX_tester_mps and smaller or equal to the TSPX_tester_mtu values.
    :return:

    """
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, '00' * channel.peer_mps)
    return True


def hdl_wid_56(desc):
    """
    Implements: TSC_MMI_tester_enable_connection
    :param desc: Action: Place the IUT in connectable mode.
    :return:
    """
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_57(desc):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for i in range(4):
        btp.l2cap_send_data(0, '00')
        time.sleep(2)
    return True


def hdl_wid_58(desc):
    return True


def hdl_wid_59(desc):
    btp.gap_conn_param_update(btp.pts_addr_get(), btp.pts_addr_type_get(),
                              720, 864, 0, 400)
    return True


def hdl_wid_100(desc):
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        try:
            while True:
                btp.l2cap_send_data(channel.id, '00')
        except BTPError:
            pass
        except socket.timeout:
            pass
    return True


def hdl_wid_101(desc):
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        btp.l2cap_disconn(channel.id)
    return True


def hdl_wid_102(desc):
    return True


def hdl_wid_103(desc):
    stack = get_stack()
    chan = stack.l2cap.chan_lookup_id(0)
    time.sleep(10)
    btp.l2cap_reconfigure(None, None, chan.our_mtu + 1,
                          [chan.id for chan in stack.l2cap.channels])
    return True


def hdl_wid_104(desc):
    stack = get_stack()
    stack.l2cap.clear_data()
    return True


def hdl_wid_105(desc):
    logging.error("Updating MPS size is not supported.")
    return False


def hdl_wid_106(desc):
    stack = get_stack()
    l2cap = stack.l2cap

    btp.l2cap_listen(l2cap.psm, defs.L2CAP_TRANSPORT_LE,
                     l2cap.initial_mtu, L2CAPConnectionResponse.insufficient_authentication)
    return True


def hdl_wid_107(desc):
    stack = get_stack()
    l2cap = stack.l2cap

    btp.l2cap_listen(l2cap.psm, defs.L2CAP_TRANSPORT_LE,
                     l2cap.initial_mtu, L2CAPConnectionResponse.insufficient_authorization)
    return True


def hdl_wid_108(desc):
    stack = get_stack()
    l2cap = stack.l2cap

    btp.l2cap_listen(l2cap.psm, defs.L2CAP_TRANSPORT_LE,
                     l2cap.initial_mtu, L2CAPConnectionResponse.insufficient_encryption_key_size)
    return True


def hdl_wid_111(desc):
    pattern = re.compile(r"\s([0-9]+)\s")
    data = pattern.findall(desc)
    if not data:
        logging.error("%s parsing error", hdl_wid_111.__name__)
        return False

    stack = get_stack()
    l2cap = stack.l2cap

    channels = l2cap.rx_data_get_all(10)
    if len(channels) == 0:
        return False

    rx_data = channels[0]
    if not len(rx_data) == 1:
        return False

    data_packet = rx_data[0]
    if not len(data_packet) == int(data[0]):
        return False

    comp_data = bytearray(list(range(len(data_packet))))
    if not data_packet == comp_data:
        return False

    return True


def hdl_wid_112(desc):
    stack = get_stack()
    l2cap = stack.l2cap

    channels = l2cap.rx_data_get_all(10)
    if len(channels) != 2:
        return False

    data_0 = channels[0]
    if len(data_0) != 1:
        return False

    data_0 = data_0[0]
    data_1 = channels[1]
    if len(data_1) != 1:
        return False

    data_1 = data_1[0]

    expected = bytes.fromhex('aa' * len(data_0))
    if not data_0 == expected:
        return False

    expected = bytes.fromhex('55' * len(data_1))
    if not data_1 == expected:
        return False

    return True


def hdl_wid_135(desc):
    return True


def hdl_wid_136(desc):
    return True


def hdl_wid_137(desc):
    return True


def hdl_wid_252(desc):
    # TODO: Fix to actually verify result of 'Insufficient Authentication' 0x0005 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_253(desc):
    # TODO: Fix to actually verify result of 'Insufficient Authorization' 0x0006 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_254(desc):
    # TODO: Fix to actually verify result of 'Insufficient Encryption Key Size' 0x0007 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_255(desc):
    stack = get_stack()
    l2cap = stack.l2cap

    btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu, 2, 1)
    return True


def hdl_wid_256(desc):
    btp.gap_wait_for_connection()
    return True


def hdl_wid_257(desc):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(2):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
    return True


def hdl_wid_258(desc):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(2):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
    return True


def hdl_wid_259(desc):
    return True


def hdl_wid_260(desc):
    # Verify if IUT received "Some connections refused –
    # insufficient resources available"
    # Verify if IUT received "All connections refused –
    # unacceptable parameters"
    stack = get_stack()
    # We test it on 2 channels, so we expect only one
    # to be connected (for condition 1) or none
    # (for condition 2)
    chan1 = stack.l2cap.is_connected(0)
    chan2 = stack.l2cap.is_connected(1)
    result = (chan1 ^ chan2) or (not chan1 and not chan2)
    return result


def hdl_wid_261(desc):
    time.sleep(2)
    stack = get_stack()
    channels = stack.l2cap.rx_data_get_all(10)
    chan = stack.l2cap.chan_lookup_id(0)
    if len(channels) != 1:
        return False

    rx_data = channels[0]
    size = [len(d) for d in rx_data]
    return size == 2 * [chan.our_mtu]


def hdl_wid_262(desc):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(5):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
        time.sleep(2)
    return True


def hdl_wid_20001(desc):
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(desc):
    btp.gap_conn()
    return True
