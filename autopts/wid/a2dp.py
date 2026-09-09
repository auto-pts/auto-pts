#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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
"""WID handlers for A2DP.

Every docstring below is the prompt PTS actually sends, copied verbatim from a
run over the full A2DP suite (49 cases: SRC 19, SNK 30). Only numbers observed in
that run have a handler: an unobserved number can only be implemented by guessing
what it means, and a guess that lands on a number PTS does use answers the wrong
thing silently - WID 102 did exactly that, claiming "Accept A2DP disconnection"
while PTS was asking the IUT to connect, and the case waited out five minutes.

An unhandled WID raises MissingWIDError, which is the honest outcome: it names
the number and the prompt so a handler can be written against the real text.
"""

import logging
import re

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug

# How long to wait for BTP_A2DP_EV_OPERATION_REQ before concluding the IUT
# answered the operation itself. PTS gives a prompt about 20s before deciding the
# operator never confirmed it, so this has to stay well short of that - on this
# IUT the timeout is the expected outcome, not the exception.
_PENDING_OP_TIMEOUT = 2


def a2dp_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{a2dp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# Delay used when the IUT is asked to emit a Delay Report and the prompt does not
# name one. AVDTP carries the delay in 1/10 ms; this is 100 ms.
_DEFAULT_DELAY = 1000


def _delay_from(description):
    """Pull the delay value out of a prompt, in ms.

    PTS names it inline ("Is the delay value 1000, ..."), and it is not fixed per
    test case, so parse it rather than hardcoding.
    """
    match = re.search(r'delay value\s+(\d+)', description, re.IGNORECASE)
    if not match:
        raise ValueError(f'no delay value in description: {description!r}')

    return int(match.group(1))


def _answer_if_pending(signal_id, accept=True, error_code=0):
    """Answer an AVDTP operation, but only if this IUT expects to be asked.

    This is the "if necessary" in the PTS prompts, and the decision is made from
    READ_SUPPORTED_COMMANDS rather than from a timeout. An IUT that answers these
    operations itself does not advertise BTP_A2DP_OPERATION_RSP, so there is
    nothing to wait for and the handler returns immediately.

    Waiting instead would cost real time for nothing: these prompts occur 184
    times across the 49 case A2DP suite, so even a 2s wait each adds six minutes
    of certain timeouts on an IUT that answers these internally.

    Only when the IUT does advertise the command is the event worth waiting for -
    then the wait is bounded well short of the roughly 20s PTS allows before it
    decides the prompt was never confirmed.
    """
    if not btp.a2dp_supports(defs.BTP_A2DP_CMD_OPERATION_RSP):
        log(f'AVDTP signal 0x{signal_id:02x}: IUT answers these itself')
        return True

    stack = get_stack()

    if stack.a2dp.wait_operation_req_ev(signal_id, _PENDING_OP_TIMEOUT) is None:
        log(f'AVDTP signal 0x{signal_id:02x}: nothing pending')
        return True

    btp.a2dp_operation_rsp(signal_id, accept=accept, error_code=error_code)
    return True


def hdl_wid_6(params: WIDParams):
    '''Is the delay value 1000, within a device acceptable range?'''
    # A question about the IUT, so ask it rather than answering for it. The delay
    # is quoted in ms in the prompt and carried in 1/10 ms on the wire.
    delay = _delay_from(params.description)
    return btp.a2dp_get_capability(defs.A2DP_CAP_DELAY_ACCEPTABLE, delay * 10)


def hdl_wid_9(_: WIDParams):
    '''Take action if necessary to initiate a Delay Reporting command.'''
    # An action, so drive it. Not every IUT can emit a delay report on demand -
    # one that declares it as an endpoint capability and lets the stack negotiate
    # it has no such call - hence the "if necessary" in the prompt.
    if not btp.a2dp_supports(defs.BTP_A2DP_CMD_SEND_DELAY_REPORT):
        log('IUT cannot send a delay report on demand')
        return True

    btp.a2dp_send_delay_report(_DEFAULT_DELAY, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_12(_: WIDParams):
    '''Delete the link key with PTS on the Implementation Under Test (IUT), and
    then click OK to continue. Description: For end product, this can be
    achieved by forgetting PTS from the IUT.
    '''
    # gap_unpair() exists and is the command for this prompt, but it must not be
    # used here: PTS keeps its own link key, so dropping the IUT's leaves the two
    # sides asymmetric - PTS answers the next SEC_LINK_KEY_REQUEST with a key the
    # IUT no longer has, authentication ends in HCI_PIN_OR_KEY_MISSING and the
    # AVDTP channel never opens.
    #
    # TSPX_delete_link_key encodes the same choice, and rfcomm, hfp and hid all
    # answer this prompt the same way.
    return True


def hdl_wid_13(_: WIDParams):
    '''Is the IUT capable of establishing connection to an unpaired device?'''
    # A question about the IUT, so ask it.
    return btp.a2dp_get_capability(defs.A2DP_CAP_CONNECT_UNPAIRED)


def hdl_wid_15(_: WIDParams):
    '''Please prepare the IUT to reject an AVDTP SET CONFIGURATION command with
    error code NOT_SUPPORTED_SAMPLING_FREQUENCY, then press 'OK' to continue.'''
    # The IUT's stack validates SET CONFIGURATION against the registered endpoint
    # capabilities and answers the matching AVDTP error on its own, so it cannot
    # be told to reject a request it would otherwise accept.
    return _answer_if_pending(
        defs.AVDTP_SIG_SET_CONFIGURATION, accept=False,
        error_code=defs.AVDTP_ERR_NOT_SUPPORTED_SAMPLING_FREQUENCY)


def hdl_wid_102(_: WIDParams):
    '''Please send an HCI connect request to establish a basic rate connection
    after the IUT discovers the Lower Tester over BR and LE.

    Connecting A2DP brings up the ACL on the way, which is what the prompt is
    after. This number used to carry an invented "Accept A2DP disconnection"
    meaning and simply returned True, so the case sat waiting for a connection
    that was never attempted until PTS gave up.
    '''
    btp.a2dp_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_1001(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Close operation initiated
    by the tester.'''
    # The IUT's stack closes the AVDTP transport channel itself.
    return _answer_if_pending(defs.AVDTP_SIG_CLOSE)


def hdl_wid_1002(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Signaling Channel
    Connection initiated by the tester. Description: Make sure the IUT
    (Implementation Under Test) is in a state to accept incoming Bluetooth
    connections. Some devices may need to be on a specific screen, like a
    Bluetooth settings screen, in order to pair with PTS. If the IUT is still
    having problems pairing with PTS, try running a test case where the IUT
    connects to PTS to establish pairing.'''
    # The IUT's stack registers the AVDTP signalling PSM at startup and accepts
    # the L2CAP connection on its own.
    return _answer_if_pending(defs.AVDTP_SIG_SIGNALING_CHANNEL)


def hdl_wid_1004(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Discover operation
    initiated by the tester.'''
    # The IUT's stack answers Discover from its registered stream endpoints.
    return _answer_if_pending(defs.AVDTP_SIG_DISCOVER)


def hdl_wid_1006(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Open operation initiated by
    the tester.'''
    # The IUT's stack accepts the AVDTP transport channel itself.
    return _answer_if_pending(defs.AVDTP_SIG_OPEN)


def hdl_wid_1009(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Set Configuration operation
    initiated by the tester.'''
    # The IUT's stack negotiates the codec configuration itself.
    return _answer_if_pending(defs.AVDTP_SIG_SET_CONFIGURATION)


def hdl_wid_1010(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Start operation initiated
    by the tester.'''
    # The IUT's stack answers Start itself.
    return _answer_if_pending(defs.AVDTP_SIG_START)


def hdl_wid_1012(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Suspend operation initiated
    by the tester.'''
    # The IUT's stack answers Suspend itself, same as Start.
    #
    # SNK/SUS/BV-01-C used to pass with no handler at all, which is misleading:
    # the prompt raised MissingWIDError, the case still passed because PTS does
    # not gate the verdict on this confirmation, and the failure was only
    # visible in the client log. A passing verdict is not evidence a handler ran.
    return _answer_if_pending(defs.AVDTP_SIG_SUSPEND)


def hdl_wid_1015(_: WIDParams):
    '''Close the streaming channel. Action: Disconnect the streaming channel, or
    close the Bluetooth connection to the PTS.

    The prompt wants an AVDTP Close. Stopping the stream sends Suspend, which is
    a different signal and leaves the tester waiting for Close, so disconnect
    instead - the IUT only emits Close as part of tearing the A2DP connection
    down, having no notion of closing a stream on its own.
    '''
    btp.a2dp_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_1016(_: WIDParams):
    '''Create an AVDTP signaling channel. Action: Create an audio or video
    connection with PTS.

    a2dp_connect() already brings the signaling channel up along with the ACL,
    and by the time this prompt arrives that connect is in flight, so there is
    nothing further to drive from here.
    '''
    return True


def hdl_wid_1020(_: WIDParams):
    '''Open a streaming media channel. Action: If the IUT (Implementation Under
    Test) is already connected to PTS, attempting to send or receive streaming
    media should trigger this action. If the IUT is not connected to PTS,
    attempting to connect may trigger this action.'''
    btp.a2dp_start_stream(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_1029(_: WIDParams):
    '''Move the IUT out of range to create a link loss scenario. Action: This can
    be also be done by placing the IUT or PTS in an RF shielded box.

    Both of the actions PTS offers are physical, and neither is reachable behind
    btproxy. Answering Ok used to leave PTS waiting for a link loss that never
    comes: the case burned its full five minute guard, came back PTS TIMEOUT,
    and left both sides mid-procedure so the rest of the session had to be
    rebuilt before it could be trusted.

    Cancel instead. The case ends immediately as INCONC, which is what it
    honestly is - not performed - and the session stays usable. Do not turn this
    into Ok to make a number look better; a pass obtained by claiming a link
    loss that did not happen is not evidence.
    '''
    log('WID 1029: RF link loss cannot be produced in this setup, cancelling')
    return False


def hdl_wid_1032(_: WIDParams):
    '''Send a start command to PTS. Action: If the IUT (Implementation Under
    Test) is already connected to PTS, attempting to send or receive streaming
    media should trigger this action. If the IUT is not connected to PTS,
    attempting to connect may trigger this action.

    Some procedures ask for the start right after the signalling channel is
    accepted, before the IUT has finished coming up. Its A2DP state machine
    drops a start request while it is still Idle, so wait for the connection to
    be reported first - otherwise the command is silently swallowed and the
    tester waits out its timeout for a Start that was never sent.
    '''
    stack = get_stack()
    if not stack.a2dp.wait_for_connection(timeout=20):
        log('hdl_wid_1032: A2DP still not connected, starting anyway')

    btp.a2dp_start_stream(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_1037(_: WIDParams):
    '''If necessary, take action to accept the AVDTP Get All Capabilities
    operation initiated by the tester.'''
    # The IUT's stack answers Get All Capabilities itself.
    return _answer_if_pending(defs.AVDTP_SIG_GET_ALL_CAPABILITIES)


def hdl_wid_1042(_: WIDParams):
    '''Take action to accept transport channels for the recently configured
    media stream.'''
    # The IUT's stack accepts the transport channels itself.
    return _answer_if_pending(defs.AVDTP_SIG_TRANSPORT_CHANNEL)


def hdl_wid_1043(_: WIDParams):
    '''Is the test system properly playing back the media being sent by the IUT?

    Nothing here can observe the tester's own playback. What decides the case is
    whether PTS actually received media packets, which it checks itself and fails
    on beforehand if the IUT sent none.
    '''
    return True


def hdl_wid_1046(_: WIDParams):
    '''Begin streaming media ... Note: If the IUT has suspended the stream please
    restart the stream to begin streaming media.'''
    btp.a2dp_start_stream(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_20000(_: WIDParams):
    '''Please prepare IUT into a connectable mode in BR/EDR. Description: Verify
    that the Implementation Under Test (IUT) can accept GATT connect request from
    PTS.'''
    # Set the BR/EDR scan mode rather than relying on the pre_conditions having
    # done it: that is what decides whether a peer can page the IUT, and a caller
    # of these handlers cannot be assumed to have set it - other systems'
    # pre_conditions may not include the step at all.
    btp.gap_set_br_scan_mode(defs.BT_SCAN_MODE_CONNECTABLE_DISCOVERABLE)
    return True
