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
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import BTPError, WIDParams
from autopts.wid.common import _l2cap_send_forever, _safe_l2cap_disconnect

log = logging.debug


# wid handlers section begin
def hdl_wid_14(params: WIDParams):
    """
    Implements: TSC_MMI_iut_disable_connection
    description: Initiate an L2CAP disconnection from the IUT to the PTS.
    """
    if params.test_case_name in ['L2CAP/COS/CED/BV-09-C', 'L2CAP/COS/CFD/BV-08-C',
                                 'L2CAP/COS/CED/BV-04-C', 'L2CAP/COS/IEX/BV-01-C',
                                 'L2CAP/COS/CFD/BV-10-C', 'L2CAP/COS/CED/BV-10-C',
                                 'L2CAP/COS/CFD/BV-13-C', 'L2CAP/ERM/BV-11-C',
                                 'L2CAP/ERM/BV-12-C', 'L2CAP/CMC/BI-01-C',
                                 'L2CAP/CMC/BI-02-C', 'L2CAP/CMC/BI-03-C',
                                 'L2CAP/CMC/BI-04-C', 'L2CAP/CMC/BV-10-C',
                                 'L2CAP/CMC/BV-11-C', 'L2CAP/CMC/BI-05-C',
                                 'L2CAP/CMC/BI-06-C', 'L2CAP/EWC/BV-03-C',
                                 'L2CAP/COS/CFD/BV-09-C', 'L2CAP/COS/CED/BV-01-C']:
        l2cap = get_stack().l2cap
        for channel in l2cap.channels:
            _l2cap_chan_disconn_safely(channel.id)
        return True

    btp.l2cap_disconn(0)

    return True


def _l2cap_chan_disconn_safely(chan_id):
    """
    Safely disconnect L2CAP channel with error handling
    """
    try:
        btp.l2cap_disconn(chan_id)
    except BTPError:
        log("Safely ignored L2CAP disconnect error")


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


def hdl_wid_22(params: WIDParams):
    """
    Implements: TSC_MMI_iut_disable_acl_connection
    description: Initiate an ACL disconnection from the IUT to the PTS.
    """
    btp.gap_wait_for_connection()

    if params.test_case_name in ['L2CAP/COS/CED/BV-09-C', 'L2CAP/COS/CFD/BV-08-C',
                                 'L2CAP/COS/CED/BV-04-C', 'L2CAP/COS/ECH/BV-02-C',
                                 'L2CAP/COS/IEX/BV-01-C', 'L2CAP/COS/CFD/BV-10-C',
                                 'L2CAP/COS/CED/BV-10-C', 'L2CAP/COS/CFD/BV-13-C',
                                 'L2CAP/ERM/BV-11-C', 'L2CAP/ERM/BV-12-C',
                                 'L2CAP/CMC/BI-01-C', 'L2CAP/CMC/BI-02-C',
                                 'L2CAP/CMC/BI-03-C', 'L2CAP/CMC/BI-04-C',
                                 'L2CAP/CMC/BV-10-C', 'L2CAP/CMC/BV-11-C',
                                 'L2CAP/CMC/BI-05-C', 'L2CAP/CMC/BI-06-C',
                                 'L2CAP/EWC/BV-03-C', 'L2CAP/COS/CFD/BV-09-C',
                                 'L2CAP/COS/CED/BV-01-C', 'L2CAP/CLS/CLR/BV-01-C',
                                 'L2CAP/CLS/UCD/BV-02-C', 'L2CAP/CLS/UCD/BV-03-C']:
        btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        return True

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
            pass  # skip second wid call
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

    for _i in range(4):
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
        _l2cap_send_forever(channel.id)
    return True


def hdl_wid_101(_: WIDParams):
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        _safe_l2cap_disconnect(channel.id)
    return True


def hdl_wid_102(_: WIDParams):
    btp.l2cap_credits(0)
    return True


def hdl_wid_103(_: WIDParams):
    stack = get_stack()
    stack.l2cap.clear_data()
    chan = stack.l2cap.chan_lookup_id(0)
    time.sleep(10)
    btp.l2cap_reconfigure(None, None, chan.our_mtu + 1,
                          [chan.id for chan in stack.l2cap.channels])
    return True


def hdl_wid_104(_: WIDParams):
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
    """
    description: Please confirm the length of assembled segmentations is _X_ and received data
    is in sequence staring from 0 in 8-bit range.
    """
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

    comp_data = bytearray([i % 256 for i in range(len(data_packet))])
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


def hdl_wid_118(_: WIDParams):
    # Please send L2CAP Disconnection Response to PTS.

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

    if rx_data is None:
        return False

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


def hdl_wid_274(_: WIDParams):
    # Did the Implementation Under Test (IUT) discard the frame that has incorrect
    # octets of Information Payload Data? Click Yes if the IUT discarded it,
    # otherwise click No.

    return True


def hdl_wid_275(params: WIDParams):
    # Did the Upper Tester issue a warning for incorrect PDU length?

    if params.test_case_name in ['L2CAP/COS/CED/BI-04-C', 'L2CAP/COS/CED/BI-08-C',
                                 'L2CAP/COS/CED/BI-10-C', 'L2CAP/COS/CED/BI-15-C']:
        return True

    return False


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


def _l2cap_chann_send_safely(channel_id, data, data_length):
    """
    Safely send L2CAP channel data with error handling
    """
    try:
        btp.l2cap_send_data(channel_id, data * data_length)
    except BTPError:
        logging.debug("Ignoring expected error on L2CAP sending")


def hdl_wid_49(params: WIDParams):
    '''
    Using the Implementation Under Test(IUT), initiate ACL Create Connection Request to the PTS.
    '''
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    l2cap = btp.get_stack().l2cap

    if params.test_case_name in ['L2CAP/COS/CFD/BV-08-C', 'L2CAP/COS/CFD/BV-09-C',
                                 'L2CAP/COS/CED/BV-01-C']:
        btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu)

    if params.test_case_name in ['L2CAP/COS/CFD/BV-10-C']:
        btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                          mode=defs.L2CAP_CONNECT_V2_MODE_RET)

    if params.test_case_name in ['L2CAP/COS/CED/BV-10-C', 'L2CAP/COS/CFD/BV-13-C']:
        time.sleep(2)
        btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                          mode=defs.L2CAP_CONNECT_V2_MODE_FC)
        time.sleep(2)
        l2cap = get_stack().l2cap
        for _ in range(0, 5):
            for channel in l2cap.channels:
                _l2cap_chann_send_safely(channel.id, '00', 1)

    return True


def hdl_wid_113(_: WIDParams):
    '''
    Please send Configure Request.
    '''
    return True


def hdl_wid_116(params: WIDParams):
    '''
    Please send Configure Response.
    '''
    btp.gap_wait_for_connection()
    l2cap = btp.get_stack().l2cap

    for channel in l2cap.channels:
        if params.test_case_name in ['L2CAP/EWC/BV-02-C']:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_23(params: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send L2CAP_Data over the assigned channel with correct DCID to the PTS.
    '''
    l2cap = get_stack().l2cap

    if params.test_case_name in ['L2CAP/LE/CID/BV-01-C', 'L2CAP/LE/CID/BV-02-C']:
        channel = l2cap.chan_lookup_id(2)
        if not channel:
            return False
        btp.l2cap_send_data(channel.id, '00')
        return True

    for channel in l2cap.channels:
        if params.test_case_name in ['L2CAP/COS/CFD/BV-09-C']:
            btp.l2cap_send_data(channel.id, '00', 48)
        else:
            btp.l2cap_send_data(channel.id, '00')
    return True


def hdl_wid_276(_: WIDParams):
    '''
    Please confirm the IUT sent the L2CAP Data to the Upper Tester.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        btp.l2cap_send_data(channel.id, '00')
    return True


def hdl_wid_277(params: WIDParams):
    '''
    Please confirm the Upper Tester received values are %s.
    Click Yes if it is, otherwise click No.
    '''
    pattern = re.compile(r'values\s+are\s+([0-9a-fA-F]+)')
    value = pattern.findall(params.description)
    if not value:
        return False

    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        rx_data = l2cap.rx_data_get(channel.id, 10)

        if rx_data is None:
            return False

        for data in rx_data:
            if value[0].upper() in data.hex().upper():
                return True

    return False


def hdl_wid_26(params: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send an Echo Request to the PTS.
    '''
    btp.l2cap_echo_req(None, defs.BTP_BR_ADDRESS_TYPE, '00')
    return True


def hdl_wid_1(params: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send an I - Frame(data) to the PTS.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        if params.test_case_name in ['L2CAP/ERM/BV-23-C', 'L2CAP/STM/BV-03-C']:
            _l2cap_chann_send_safely(channel.id, '00', 120)
        elif params.test_case_name in ['L2CAP/ERM/BV-15-C']:
            for _ in range(0, 4):
                _l2cap_chann_send_safely(channel.id, '00', 1)
        else:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_134(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send an I - Frame(data) to the PTS until TxWindow is full.
    '''
    l2cap = get_stack().l2cap
    for _ in range(0, 5):
        for channel in l2cap.channels:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_114(_: WIDParams):
    '''
    Please send Configure Request with Enhanced Retransmission Mode.
    '''
    return True


def hdl_wid_7(_: WIDParams):
    '''
    Place the Implementation Under Test(IUT) in a state to receive an I - Frame from the PTS, then click Ok.
    '''
    return True


def hdl_wid_35(_: WIDParams):
    '''
    Did the Upper Tester receive 48 bytes of data
    Description : The Implementation Under Test(IUT) should receive 48 bytes of data and notify upper tester.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        rx_data = l2cap.rx_data_get(channel.id, 10)

        if rx_data is None:
            return False

        for data in rx_data:
            if len(data) == 48:
                return True
    return True


def hdl_wid_128(_: WIDParams):
    '''
    Please send a Poll BIT(P=1) using S-Frame.
    '''
    return True


def hdl_wid_130(_: WIDParams):
    '''
    Please send a FINAL BIT(F=1) using S-Frame.
    '''
    return True


def hdl_wid_9(_: WIDParams):
    '''
    Place the Implementation Under Test(IUT) in a state to receive an S - Frame with Poll bit set(P = 1) from the PTS.
    '''
    return True


def hdl_wid_129(_: WIDParams):
    '''
    Please send a Poll BIT(P=1) using S-Frame when every monitor timer is expired.
    '''
    return True


def hdl_wid_32(_: WIDParams):
    '''
    Wait for monitor timeout to Initiate an L2CAP disconnection from the IUT to the PTS.
    Description: The Implementation Under Test(IUT) should disconnect the active L2CAP channel by
    sending a disconnect request to PTS after monitor timer expired.
    '''
    return True


def hdl_wid_34(_: WIDParams):
    '''
    Did the Upper Tester receive 4 bytes of data
    Description : The Implementation Under Test(IUT) should receive 4 bytes of data and notify upper tester.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        rx_data = l2cap.rx_data_get(channel.id, 10)

        if rx_data is None:
            return False

        for data in rx_data:
            if len(data) == 4:
                return True
    return True


def hdl_wid_17(_: WIDParams):
    '''
    Place the Implementation Under Test(IUT) into the Local Busy Condition, such that an RNR S - Frame will be sent to the PTS.
    '''
    return True


def hdl_wid_8(_: WIDParams):
    '''
    Place the Implementation Under Test(IUT) in a state to receive I - Frames from the PTS.
    '''
    return True


def hdl_wid_19(_: WIDParams):
    '''
    Is the Upper Tester of the Implementation Under Test able to force the IUT into a Local Busy Condition
    '''
    return True


def hdl_wid_18(_: WIDParams):
    '''
    The Upper Tester should now clear the Local Busy Condition which should cause the Implementation
    Under Test(IUT) to send an RR S - Frame.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        btp.l2cap_credits(channel.id)
    return True


def hdl_wid_10(_: WIDParams):
    '''
    Place the Implementation Under Test(IUT) in a state to receive data from the PTS.
    '''
    return True


def hdl_wid_131(_: WIDParams):
    '''
    Please send a RR using S-Frame.
    '''
    return True


def hdl_wid_121(_: WIDParams):
    '''
    Please initiate Information Request procedure to discover supported features and configure connection.
    '''
    return True


def hdl_wid_6(params: WIDParams):
    '''
    Did the Implementation Under Test(IUT) inform the Upper Tester the connection attempt failed?
    '''
    l2cap = btp.get_stack().l2cap
    try:
        if params.test_case_name in ['L2CAP/CMC/BV-13-C']:
            btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                              mode=defs.L2CAP_CONNECT_V2_MODE_STREAM)
        else:
            btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                              mode=defs.L2CAP_CONNECT_V2_MODE_ERET)
    except BTPError:
        # L2CAP channel connection failed, which matches the test case scenario
        return True
    return False


def hdl_wid_115(_: WIDParams):
    '''
    Please send Configure Request with Streaming Mode.
    '''
    return True


def hdl_wid_119(params: WIDParams):
    '''
    Please send L2CAP Information Request with InfoType to Extended Features(0x0002).
    '''
    btp.gap_wait_for_connection()
    l2cap = get_stack().l2cap
    if params.test_case_name in ['L2CAP/CMC/BV-11-C']:
        btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                          mode=defs.L2CAP_CONNECT_V2_MODE_STREAM,
                          options=defs.L2CAP_CONNECT_V2_OPT_MODE_OPTIONAL)
    else:
        btp.l2cap_conn_v2(None, defs.BTP_BR_ADDRESS_TYPE, l2cap.psm, l2cap.initial_mtu,
                          mode=defs.L2CAP_CONNECT_V2_MODE_ERET,
                          options=defs.L2CAP_CONNECT_V2_OPT_MODE_OPTIONAL)
    return True


def hdl_wid_20(_: WIDParams):
    '''
    Verify that the following test conditions are true :
    1. The implementation Under Test(IUT) must specify the capability of sending SDUs of N bytes.
    2.  The PIXIT setting for TSPX_IUT_SDU_SIZE_N_BYTES is set correctly.
    '''
    return True


def hdl_wid_2(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), queue up and send two I - Frames(data) to the PTS.
    '''
    l2cap = get_stack().l2cap
    for _ in range(0, 2):
        for channel in l2cap.channels:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_3(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), queue up and send four(4) I - Frames(data) to the PTS.
    '''
    l2cap = get_stack().l2cap
    for _ in range(0, 4):
        for channel in l2cap.channels:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_124(_: WIDParams):
    '''
    Please send L2CAP Configuration Request with EWS Option Bit set to 1.
    '''
    return True


def hdl_wid_125(_: WIDParams):
    '''
    Please send L2CAP Configuration Request with EWS Option Bit set to 0.
    '''
    return True


def hdl_wid_4(params: WIDParams):
    '''
    Using the Implementation Under Test(IUT) send extended control I - Frame data to the PTS.
    '''
    l2cap = get_stack().l2cap
    for channel in l2cap.channels:
        if params.test_case_name in ['L2CAP/ECF/BV-08-C']:
            _l2cap_chann_send_safely(channel.id, '00', 120)
        else:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_24(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), queue up and send two(2) extended control field
    data(I - Frames) to the PTS.
    '''
    l2cap = get_stack().l2cap
    for _ in range(0, 2):
        for channel in l2cap.channels:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


def hdl_wid_25(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send an extended control field data four(4) times to the PTS.
    '''
    l2cap = get_stack().l2cap
    for _ in range(0, 4):
        for channel in l2cap.channels:
            _l2cap_chann_send_safely(channel.id, '00', 1)
    return True


br_psm = 0x1001
br_initial_mtu = 120


def hdl_wid_263(_: WIDParams):
    '''
    Please send L2CAP Connection REQ to PTS.
    '''
    btp.l2cap_conn(None, defs.BTP_BR_ADDRESS_TYPE, br_psm, br_initial_mtu)
    return True


def hdl_wid_264(_: WIDParams):
    '''
    Please place the IUT in L2CAP connectable mode.
    Description: PTS requires that the IUT be in L2CAP connectable mode. The PTS will open an L2CAP channel.
    '''
    return True


def hdl_wid_50(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send connectionless data to the PTS using
    connectionless channel.
    Description : The Implementation Under Test(IUT) should send connectionless data to PTS through
    connectionless channel.
    '''
    btp.l2cap_cls_send(None, defs.BTP_BR_ADDRESS_TYPE, 0x1001, '00')
    return True


def hdl_wid_62(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), send unencrypted connectionless data to the PTS using
    connectionless channel.
    Description : The Implementation Under Test(IUT) should send unencrypted connectionless data to
    PTS through connectionless channel.
    '''
    btp.l2cap_cls_send(None, defs.BTP_BR_ADDRESS_TYPE, 0x1001, '00')
    return True


def hdl_wid_33(_: WIDParams):
    '''
    Using the Implementation Under Test(IUT), initiate security procedure to send encrypted data to
    the PTS using connectionless channel.
    Description : The Implementation Under Test(IUT) should initiate the security procedure before
    sending encrypted data to PTS through connectionless channel.
    '''
    btp.gap_pair_v2(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, level=defs.BTP_GAP_CMD_PAIR_V2_LEVEL_2)
    btp.gap_wait_for_sec_lvl_change(level=2)
    btp.l2cap_cls_send(None, defs.BTP_BR_ADDRESS_TYPE, 0x1001, '00')
    return True


def hdl_wid_265(_: WIDParams):
    '''
    Please confirm the Upper Tester did receive no data.
    Click Yes if Upper Tester received no data, otherwise click No.
    '''
    return True
