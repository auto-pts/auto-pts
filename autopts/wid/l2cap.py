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
import binascii
import logging
import re
import socket
import sys
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import BTPError, WIDParams

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", l2cap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)

# wid handlers section begin
def hdl_wid_14(_: WIDParams):
    """
    Implements: TSC_MMI_iut_disable_connection
    description: Initiate an L2CAP disconnection from the IUT to the PTS.
    """
    btp.l2cap_disconn(0)

    return True


def hdl_wid_15(_: WIDParams):
    """
    Implements: TSC_MMI_tester_enable_connection
    description: Action: Place the IUT in connectable mode.
    """
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_22(_: WIDParams):
    """
    Implements: TSC_MMI_iut_disable_acl_connection
    description: Initiate an ACL disconnection from the IUT to the PTS.
    """
    btp.gap_wait_for_connection()
    btp.gap_disconn()

    return True


def hdl_wid_36(_: WIDParams):
    """
    Implements: TSC_MMI_iut_send_le_flow_control_credit
    description: Command IUT to send LE Flow Control Credit to increase the LE data packet that PTS can send.
    """

    # handled by host L2CAP layer or application
    return True


def hdl_wid_37(params: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_LE_data
    description: Did the Upper Tester send the data xxxx to the PTS?
                 Click Yes if it matched, otherwise click No.
    """
    # This pattern is matching first data frame
    pattern = re.compile(r"send\sthe\sdata\s([0-9a-fA-F]+)")
    data = pattern.findall(params.description)
    if not data:
        logging.error("%s parsing error", hdl_wid_37.__name__)
        return False

    stack = get_stack()
    tx_data = stack.l2cap.tx_data_get(0)
    if tx_data is None or len(tx_data) < 1:
        return False

    return data[0] == tx_data[0]


def hdl_wid_38(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_send_LE_data_packet1
    description: Upper Tester command IUT to send a nonsegmented LE data packet to the PTS with any values.
    """
    stack = get_stack()
    stack.l2cap.wait_for_connection(0)
    channel = stack.l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF')
    return True


def hdl_wid_39(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_command_not_understaood
    description: Did Implementation Under Test (IUT) receive L2CAP Reject with 'command not understood' error.
                 Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received command not understood on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_40(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_data_receive
    description: Please confirm the Upper Tester receive data
    """
    stack = get_stack()
    rx_data = stack.l2cap.rx_data_get_all(10)
    return rx_data is not None


def hdl_wid_41(params: WIDParams):
    """
    Implements: TSC_MMI_iut_send_le_credit_based_connection_request
    description: Using the Implementation Under Test (IUT), send a LE Credit based connection request to PTS.
    """
    stack = get_stack()
    l2cap = stack.l2cap

    if params.test_case_name in ['L2CAP/LE/CFC/BV-02-C']:
        if not l2cap.is_connected(0):
            btp.l2cap_conn(None, None, stack.l2cap.psm, l2cap.initial_mtu)
        else:
            pass # skip second wid call
    else:
        btp.l2cap_conn(None, None, stack.l2cap.psm, l2cap.initial_mtu)

    return True


def hdl_wid_42(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_psm
    description: Did Implementation Under Test (IUT) receive Request Reject with 'LE_PSM not supported' 0x0002 error.
                 Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received LE_PSM not supported on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_43(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_send_le_data_packet_large
    description: Upper Tester command IUT to send multiple LE frame data packet to the PTS.
    """
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF' * channel.peer_mps)

    return True


def hdl_wid_48(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_resources
    description: Did Implementation Under Test (IUT) receive Connection refused 'Insufficient Resources' 0x0004 error.
                 Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received insufficient resources on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_51(_: WIDParams):
    """
    Implements: TSC_MMI_iut_enable_le_connection
    description: Initiate or create LE ACL connection to the PTS.
    """
    btp.gap_wait_for_disconnection(5)
    btp.gap_conn()

    return True


def hdl_wid_52(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_invalid_source_cid
    description: Did Implementation Under Test (IUT) receive Connection refused 'Invalid Source CID' 0x0009 error.
                 And does not send anything over refuse LE data channel. Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received invalid source CID on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_53(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_source_cid_already_allocated
    description: Did Implementation Under Test (IUT) receive Connection refused 'Source CID Already Allocated' 0x000A
                 error. And does not send anything over refuse LE data channel. Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received Source CID Already Allocated on LE based connection request it means that the channel is not
    # connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_54(_: WIDParams):
    """
    Implements: TSC_MMI_upper_tester_confirm_receive_reject_unacceptable_parameters
    description: Did Implementation Under Test (IUT) receive Connection refused 'Unacceptable Parameters' 0x000B error.
                 Click Yes if it is, otherwise click No.
    """
    stack = get_stack()

    # If IUT received Unacceptable Parameters on LE based connection request it means that the channel is not connected.
    return not stack.l2cap.is_connected(0)


def hdl_wid_55(_: WIDParams):
    """
    description: Upper Tester command IUT to send LE data packet to the PTS with
    larger or equal to the TSPX_tester_mps and smaller or equal to the TSPX_tester_mtu values.

    """
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, '00' * channel.peer_mps)
    return True


def hdl_wid_56(_: WIDParams):
    """
    Implements: TSC_MMI_tester_enable_connection
    description: Action: Place the IUT in connectable mode.
    """
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    return True


def hdl_wid_57(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for i in range(4):
        btp.l2cap_send_data(0, '00')
        time.sleep(2)
    return True


def hdl_wid_58(_: WIDParams):
    return True


def hdl_wid_59(_: WIDParams):
    btp.gap_conn_param_update(btp.pts_addr_get(), btp.pts_addr_type_get(),
                              720, 864, 0, 400)
    return True


def hdl_wid_60(params: WIDParams):
    # use (\w{4,}) to avoid catching word "L2CAP"
    control_data = re.search(r"(\w{4,})([A-F0-9]+)", params.description).group(0)
    stack = get_stack()
    l2cap = stack.l2cap

    channels = l2cap.rx_data_get_all(10)

    for chan in channels:
        for data in chan:
            if binascii.hexlify(data).decode().upper() in control_data:
                return True

    return False


def hdl_wid_61(_: WIDParams):
    """description: Please confirm the IUT does not send the L2CAP Data to the Upper Tester."""
    return True


def hdl_wid_100(_: WIDParams):
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


def hdl_wid_101(_: WIDParams):
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        try:
            btp.l2cap_disconn(channel.id)
        except BTPError:
            logging.debug("Ignoring expected error on L2CAP disconnect")
    return True


def hdl_wid_102(_: WIDParams):
    btp.l2cap_credits(0)
    return True


def hdl_wid_103(_: WIDParams):
    stack = get_stack()
    chan = stack.l2cap.chan_lookup_id(0)
    time.sleep(10)
    btp.l2cap_reconfigure(None, None, chan.our_mtu + 1,
                          [chan.id for chan in stack.l2cap.channels])
    return True


def hdl_wid_104(_: WIDParams):
    stack = get_stack()
    stack.l2cap.clear_data()
    return True


def hdl_wid_105(_: WIDParams):
    logging.error("Updating MPS size is not supported.")
    return False


def hdl_wid_106(_: WIDParams):
    return True


def hdl_wid_107(_: WIDParams):
    return True


def hdl_wid_108(_: WIDParams):
    """ desciption: Please configure the IUT into LE Security and start pairing process."""
    btp.gap_pair()
    return True


def hdl_wid_111(params: WIDParams):
    pattern = re.compile(r"\s([0-9]+)\s")
    data = pattern.findall(params.description)
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


def hdl_wid_112(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap

    channels = l2cap.rx_data_get_all(10)
    if len(channels) != 2:
        return False

    data_0 = channels[0]
    data_1 = channels[1]

    data_0_unfolded = []
    for x in data_0:
        data_0_unfolded.extend(x)


    data_1_unfolded = []
    for x in data_1:
        data_1_unfolded.extend(x)


    expected = [0xaa] * len(data_0_unfolded)
    if not data_0_unfolded == expected:
        return False

    expected = [0x55] * len(data_1_unfolded)
    if not data_1_unfolded == expected:
        return False

    return True


def hdl_wid_135(_: WIDParams):
    return True


def hdl_wid_136(_: WIDParams):
    return True


def hdl_wid_137(_: WIDParams):
    return True


def hdl_wid_138(_: WIDParams):
    """"description: Please make sure an encryption requirement exists for a channel
    L2CAP. When receiving Credit Based Connection Request from PTS, please respond with
    Result 0x0008 (Insufficient Encryption)
    """
    return get_stack().gap.wait_for_connection(5)


def hdl_wid_251(_: WIDParams):
    # TODO: Fix to actually verify result of 'Insufficient Encryption' 0x0008 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_252(_: WIDParams):
    # TODO: Fix to actually verify result of 'Insufficient Authentication' 0x0005 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_253(_: WIDParams):
    # TODO: Fix to actually verify result of 'Insufficient Authorization' 0x0006 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_254(_: WIDParams):
    # TODO: Fix to actually verify result of 'Insufficient Encryption Key Size' 0x0007 error
    return get_stack().l2cap.wait_for_disconnection(0, 30)


def hdl_wid_255(params: WIDParams):
    """ description: Please send L2CAP Credit Based Connection REQ to PTS."""
    stack = get_stack()

    if params.test_case_name == "L2CAP/TIM/BV-03-C":
        # This L2CAP test tests a requirement on EATT, not L2CAP
        btp.eatt_conn(None, None, 1)
    else:
        l2cap = stack.l2cap
        btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu, l2cap.num_channels, 1, l2cap.hold_credits)

        # Wait until all channels connected to avoid race condition between channel connection and new received wid
        for channel_id in range(l2cap.num_channels):
            l2cap.wait_for_connection(channel_id)

    return True


def hdl_wid_256(_: WIDParams):
    btp.gap_wait_for_connection()
    return True


def hdl_wid_257(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(2):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
    return True


def hdl_wid_258(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(2):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
    return True


def hdl_wid_259(_: WIDParams):
    return True


def hdl_wid_260(_: WIDParams):
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


def hdl_wid_261(_: WIDParams):
    time.sleep(2)
    stack = get_stack()
    chan = stack.l2cap.chan_lookup_id(0)
    rx_data = stack.l2cap.rx_data_get(0, 10)

    size = [len(d) for d in rx_data]
    return size == 2 * [chan.our_mtu]


def hdl_wid_262(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    for _ in range(5):
        btp.l2cap_send_data(0, '00' * channel.peer_mtu)
        time.sleep(2)
    return True


def hdl_wid_267(_: WIDParams):
    # PTS want us to use specific Source CID, but we can just ignore it as it
    # should not require that
    stack = get_stack()
    l2cap = stack.l2cap

    btp.l2cap_conn(None, None, l2cap.psm, l2cap.initial_mtu)
    return True


def hdl_wid_268(_: WIDParams):
    # PTS ask to disconnect channel with specified SCID and DCID, but we can just
    # disconnect last connected channel (1) to be conforming with TS

    btp.l2cap_disconn(1)

    # Wait for disconnected event before replying to PTS to avoid sending next
    # connect too soon
    get_stack().l2cap.wait_for_disconnection(1, 30)
    return True


def hdl_wid_270(_: WIDParams):
    return True


def hdl_wid_271(_: WIDParams):
    disconnected = get_stack().l2cap.wait_for_disconnection(0, 30)
    disconnected &= get_stack().l2cap.wait_for_disconnection(1, 30)
    return disconnected


def hdl_wid_272(_: WIDParams):
    """"description: Please press ok to disconnect the link."""
    return True


def hdl_wid_2000(_: WIDParams):
    stack = get_stack()

    passkey = stack.gap.get_passkey()
    stack.gap.passkey.data = None

    return passkey


def hdl_wid_20001(_: WIDParams):
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(_: WIDParams):
    btp.gap_conn()
    return True


def hdl_wid_20128(_: WIDParams):
    return True
