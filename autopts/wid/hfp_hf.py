#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


def hfp_hf_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl

    log(f"{hfp_hf_wid_hdl.__name__}, {wid}, {description}, {test_case_name}")
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_0(params: WIDParams):
    """
    Make the Implementation Under Test (IUT) connectable, then click Ok.
    """
    if params.test_case_name in ["HFP/HF/SLC/BV-01-C", "HFP/HF/SLC/BI-01-C", "HFP/HF/SLC/BV-11-C"]:
        return True
    return True


def hdl_wid_1(params: WIDParams):
    """
    Click Ok, then initiate a service level connection from the Implementation Under Test (IUT) to
    the PTS.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    stack.gap.set_passkey(None)

    stack.hfp_hf.increase_mmi_round(1)

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
        if not stack.gap.is_connected():
            return False

    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    if params.test_case_name in ["HFP/HF/SLC/BV-11-C", "HFP/HF/WBS/BV-04-C"]:
        return True

    if params.test_case_name in ["HFP/HF/CGSIT/SFC/BV-01-C"]:
        if stack.hfp_hf.get_mmi_round(1) < 2:
            return True

    if params.test_case_name in ["HFP/HF/SDP/BV-03-C"]:
        stack.hfp_hf.wait_for_disconnection(bd_addr)
        btp.hfp_hf_connect(7)
        return True

    if not stack.hfp_hf.is_connected(bd_addr):
        btp.hfp_hf_connect(1)
    return True


def hdl_wid_2(_: WIDParams):
    """
    Click Ok, then disable the service level connection using the Implementation Under Test (IUT).
    """
    btp.hfp_hf_disconnect()
    return True


def hdl_wid_3(params: WIDParams):
    """
    Click Ok, then initiate an audio connection (SCO) from the Implementation Under Test (IUT) to
    the PTS.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_hf.sco_is_connected(bd_addr):
        return True

    if params.test_case_name in ["HFP/HF/ATA/BV-02-C", "HFP/HF/ATH/BV-03-C", "HFP/HF/ATH/BV-04-C",
                                 "HFP/HF/ATH/BV-09-C"]:
        return True

    bd_addr = btp.pts_addr_get()
    btp.hfp_hf_audio_connect()
    return True


def hdl_wid_4(_: WIDParams):
    """
    Click Ok, then close the audio connection (SCO) between the Implementation Under Test (IUT)
    and the PTS.
    Do not close the service level connection (SLC) or power-off the IUT.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_hf.sco_is_disconnected(bd_addr):
        return True

    btp.hfp_hf_audio_disconnect()
    return True


def hdl_wid_8(_: WIDParams):
    """
    Click Ok, then answer the incoming call on the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_accept_call(call_index)
    return True


def hdl_wid_9(params: WIDParams):
    """
    Click Ok, then answer the incoming call using the Implementation Under Test (IUT).
    """
    if params.test_case_name in ["HFP/HF/CIT/BV-01-C"]:
        return True

    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0
    stack.hfp_hf.wait_for_call_count(bd_addr, 1)
    btp.hfp_hf_accept_call(call_index)
    return True


def hdl_wid_10(_: WIDParams):
    """
    Click Ok, then reject the incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_reject_call(call_index)
    return True


def hdl_wid_21(_: WIDParams):
    """
    Click Ok, then place an outgoing call from the Implementation Under Test (IUT) using an entered
    phone number.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    stack.hfp_hf.wait_for_connection(bd_addr)
    number = "1234567"
    btp.hfp_hf_number_call(number)
    return True


def hdl_wid_22(_: WIDParams):
    """
    Click Ok, then place an outgoing call from the Implementation Under Test (IUT) by entering the
    memory index.
    For further clarification please see the HFP 1.5 Specification.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    stack.hfp_hf.wait_for_connection(bd_addr)
    location = "1"
    btp.hfp_hf_memory_dial(location)
    return True


def hdl_wid_23(_: WIDParams):
    """
    Click Ok, then attempt to place an outgoing call from the Implementation Under Test (IUT) by
    entering a memory index which does not equal the TSPX_phone_number_memory.
    For further clarification please see the HFP 1.5 Specification.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    stack.hfp_hf.wait_for_connection(bd_addr)
    location = "99"  # Invalid memory location
    btp.hfp_hf_memory_dial(location)
    return True


def hdl_wid_24(_: WIDParams):
    """
    Click Ok, then place an outgoing call to the last number dialed on the Implementation Under
    Test (IUT).
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    stack.hfp_hf.wait_for_connection(bd_addr)
    btp.hfp_hf_redial()
    return True


def hdl_wid_25(_: WIDParams):
    """
    Click Ok, then end the call process from the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_terminate_call(call_index)
    return True


def hdl_wid_27(params: WIDParams):
    """
    Click Ok, then end the 2nd call using the Implementation Under Test (IUT).
    """
    if params.test_case_name in ["HFP/HF/TWC/BV-01-C"]:
        btp.hfp_hf_set_udub()
        return True

    call_index = 1
    btp.hfp_hf_terminate_call(call_index)
    return True


def hdl_wid_28(_: WIDParams):
    """
    Verify that the call is disabled on the Implementation Under Test (IUT) and then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_hf.get_call_count(bd_addr) == 0:
        return True

    return False


def hdl_wid_29(_: WIDParams):
    """
    Click Ok, then make the held call active which will result in the active call being disabled.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_hf.wait_for_call_count(bd_addr, 2, timeout=30):
        return False
    btp.hfp_hf_release_active_accept_other()
    return True


def hdl_wid_30(_: WIDParams):
    """
    Click Ok, then make the held call active which will result in the active call being placed
    on hold.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_hf.wait_for_call_count(bd_addr, 2, timeout=30):
        return False
    btp.hfp_hf_hold_active_accept_other()
    return True


def hdl_wid_31(_: WIDParams):
    """
    Click Ok, then add the held call to the conversation.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_hf.wait_for_call_count(bd_addr, 2, timeout=30):
        return False
    btp.hfp_hf_join_conversation()
    return True


def hdl_wid_32(_: WIDParams):
    """
    Click Ok, then join the held and active making one conversation and disconnect the
    Implementation Under Test (IUT) from the said conversation.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_hf.wait_for_call_count(bd_addr, 2, timeout=30):
        return False
    btp.hfp_hf_explicit_call_transfer()
    return True


def hdl_wid_35(_: WIDParams):
    """
    Verify the presence of an audio connection, then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_hf.wait_for_sco_connection(bd_addr):
        return True
    return False


def hdl_wid_37(_: WIDParams):
    """
    Verify the audio is returned to the 2nd call and then click Ok. Resume action may be needed.
    If the audio is not returned to the 2nd call, click Cancel.
    """
    return True


def hdl_wid_39(_: WIDParams):
    """
    Verify the absence of an audio connection (SCO), then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if not stack.hfp_hf.sco_is_connected(bd_addr):
        return True
    return False


def hdl_wid_43(params: WIDParams):
    """
    Send the DTMF code #, then click Ok
    """
    pattern = re.compile(r"DTMF\scode\s([0-9*#]+)")
    data = pattern.findall(params.description)
    if not data:
        logging.error("%s parsing error", hdl_wid_43.__name__)
        return False

    dtmf_code = data[0]

    call_index = 0
    btp.hfp_hf_transmit_dtmf_code(call_index, ord(dtmf_code[0]))
    return True


def hdl_wid_45(_: WIDParams):
    """
    Click Ok, then disable EC/NR using the Implementation Under Test (IUT).
    """
    btp.hfp_hf_turn_off_ecnr()
    return True


def hdl_wid_47(_: WIDParams):
    """
    Mute the in-band ringtone on the Implementation Under Test (IUT) and then click OK.
    """
    return True


def hdl_wid_48(_: WIDParams):
    """
    Verify that the in-band ringtone is not audible, then click Ok.
    """
    return True


def hdl_wid_49(_: WIDParams):
    """
    Verify that the in-band ringtone is audible, then click Ok.
    """
    return True


def hdl_wid_50(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) is generating a local alert, then click Ok.
    """
    return True


def hdl_wid_51(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) is not generating a local alert.
    """
    return True


def hdl_wid_53(params: WIDParams):
    """
    Verify that the signal reported on the Implementation Under Test (IUT) is proportional
    to the value (out of 5), then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    stack.hfp_hf.wait_for_connection(bd_addr)

    signal = int(params.description[-1])
    if stack.hfp_hf.wait_for_signal(bd_addr, signal):
        return True
    return False


def hdl_wid_54(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) reports the roam status as active,
    then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    stack.hfp_hf.wait_for_connection(bd_addr)

    if stack.hfp_hf.wait_for_roam(bd_addr, 1):
        return True
    return False


def hdl_wid_55(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) reports the roam status as inactive,
    then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    stack.hfp_hf.wait_for_connection(bd_addr)

    if stack.hfp_hf.wait_for_roam(bd_addr, 0):
        return True
    return False


def hdl_wid_59(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) reports the Audio Gateway (AG) battery level as
    fully charged, then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_hf.wait_for_battery_changed(bd_addr)


def hdl_wid_60(_: WIDParams):
    """
    Click Ok, then manipulate the Implementation Under Test (IUT) so that the battery is fully
    charged.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_hf.wait_for_battery(bd_addr, 5)


def hdl_wid_61(_: WIDParams):
    """
    Manipulate the Implementation Under Test (IUT) so that the battery level is not fully charged,
    then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_hf.wait_for_unexpected_battery(bd_addr, 5)


def hdl_wid_62(params: WIDParams):
    """
    Verify the following information matches the network operator reported on the
    Implementation Under Test (IUT), then click Ok: Bluetooth SIG
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    keywork = "Ok:"
    start_idx = params.description.find(keywork) + len(keywork)
    result = params.description[start_idx:].strip()

    return stack.hfp_hf.wait_for_operator(bd_addr, result)


def hdl_wid_63(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), query the network operator, then click Ok.
    """
    btp.hfp_hf_get_operator()
    return True


def hdl_wid_64(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), query the list of currents calls on the
    Audio Gateway (AG), then click Ok.
    """
    btp.hfp_hf_query_list_current_calls()
    return True


def hdl_wid_67(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) interprets both held and active call signals,
    then click Ok. If applicable, verify that the information is correctly displayed on the IUT,
    then click Ok.
    """
    return True


def hdl_wid_68(params: WIDParams):
    """
    Click Ok, then use the Implementation Under Test (IUT) to enable private consultation with
    the specified call with index 2
    """
    call_index = int(params.description[-1]) - 1
    btp.hfp_hf_private_consultation_mode(call_index)
    return True


def hdl_wid_69(params: WIDParams):
    """
    Click OK, then use the Implementation Under Test (IUT) to release the specified call with
    index 2
    """
    call_index = int(params.description[-1]) - 1
    btp.hfp_hf_release_specified_call(call_index)
    return True


def hdl_wid_72(_: WIDParams):
    """
    Set the speaker volume of the Implementation Under Test (IUT) to less than 4, then click Ok.
    """
    gain = 3
    btp.hfp_hf_vgs(gain)
    return True


def hdl_wid_75(_: WIDParams):
    """
    Set the mic volume of the Implementation Under Test (IUT) below the default/nominal level,
    then click Ok.
    """
    gain = 3
    btp.hfp_hf_vgm(gain)
    return True


def hdl_wid_76(params: WIDParams):
    """
    Verify that the Hands Free (HF) speaker volume is displayed correctly on the
    Implementation Under Test (IUT).
    """
    gain = int(re.sub(r"\D", "", params.description[-2:]))
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_hf.wait_for_vgs(bd_addr, gain)


def hdl_wid_77(params: WIDParams):
    """
    Verify that the Hands Free (HF) mic volume is displayed correctly on the
    Implementation Under Test (IUT), then click Ok.
    """
    gain = int(re.sub(r"\D", "", params.description[-2:]))
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_hf.wait_for_vgm(bd_addr, gain)


def hdl_wid_78(_: WIDParams):
    """
    NOTE: The following rules apply for this test case:
    1. TSPX_phone_number - the 1st call
    2. TSPX_second_phone_number - the 2nd call
    """
    return True


def hdl_wid_79(params: WIDParams):
    """
    Using the Implementation Under Test (IUT), verify that the following is a valid Audio
    Gateway (AG) subscriber number, then click Ok. "1234567"
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    btp.hfp_hf_query_subscriber()

    number = re.findall(r'"([^"]+)"', params.description)[-1]
    return stack.hfp_hf.wait_for_subscriber_number(bd_addr, number)


def hdl_wid_80(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), verify that the subscriber number information is not
    supported by the PTS, then click Ok.
    """
    btp.hfp_hf_query_subscriber()
    return True


def hdl_wid_82(_: WIDParams):
    """
    Click Ok, then request a phone number to attach to a voice tag previously entered using the
    Implementation Under Test (IUT).
    """
    btp.hfp_hf_request_phone_number()
    return True


def hdl_wid_84(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), deactivate voice recognition.
    """
    activate = 0  # Deactivate
    btp.hfp_hf_voice_recognition(activate)
    return True


def hdl_wid_86(params: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow a request from the PTS
    to activate voice recognition, then click Ok.
    """
    if params.test_case_name in ["HFP/HF/VRR/BV-01-C"]:
        btp.hfp_hf_ready_to_accept_audio()
    return True


def hdl_wid_89(_: WIDParams):
    """
    Enable calling line identification using the HF (send AT+CLIP=1 to the PTS-AG), then Click Ok.
    """
    enable = 1
    btp.hfp_hf_cli(enable)
    return True


def hdl_wid_91(_: WIDParams):
    """
    Delete the pairing with the PTS using the Implementation Under Test (IUT), then click Ok.
    """
    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_94(_: WIDParams):
    """
    Click Ok, then move the PTS and the Implementation Under Test (IUT) out of range of each other
    by performing one of the following IUT specific actions:
    """
    # For automated testing, we can simulate going out of range by:
    # 1. Disconnecting the connection
    # 2. Or setting a flag to simulate out of range condition

    # Disconnect to simulate out of range
    bd_addr = btp.pts_addr_get()
    btp.hfp_hf_disconnect()
    stack = get_stack()
    stack.hfp_hf.wait_for_disconnection(bd_addr)
    btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_95(_: WIDParams):
    """
    Click Ok, then remove the Implementation Under Test (IUT) and/or the PTS from the RF shield.
    If the out of range method was used, bring the IUT and PTS back within range.
    """
    return True


def hdl_wid_98(_: WIDParams):
    """
    Click Ok, then close the audio connection (SCO) by one of the following ways:
    """
    btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_99(_: WIDParams):
    """
    Verify that the +CLCC response(s) received by the Implementation Under Test (IUT) contains
    the correct call status information, then click Ok.
    """
    return True


def hdl_wid_100(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to initiate
    a service level disconnection, then click Ok.
    """
    return True


def hdl_wid_101(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state which will allow the PTS to disconnect
    the audio (SCO), then click Ok.
    """
    return True


def hdl_wid_110(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that can receive the following AT Command,
    then click Ok: +BVRA: 0
    """
    return True


def hdl_wid_114(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in an appropriate state which will allow the PTS
    to initiate an audio connection (SCO), then click Ok.
    """
    return True


def hdl_wid_115(_: WIDParams):
    """
    Click Ok, then perform the two actions below using the Implementation Under Test (IUT):
    1. Place an outgoing call.
    2. Cancel the outgoing call once the PTS indicates that an outgoing call process has begun.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_hf.get_call_count(bd_addr) == 0:
        btp.hfp_hf_number_call("7654321")
    else:
        call_index = 0
        btp.hfp_hf_release_specified_call(call_index)
    return True


def hdl_wid_121(_: WIDParams):
    """
    Click Ok, then make a connection request to the PTS from the Implementation Under Test (IUT).
    """
    stack = get_stack()
    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.hfp_hf_connect(1)
    return True


def hdl_wid_122(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in discoverable mode, then click Ok.
    """
    btp.gap_wait_for_connection()
    return True


def hdl_wid_123(_: WIDParams):
    """
    Click Ok, then accept the pairing and connection requests on the Implementation Under
    Test (IUT), if prompted.
    """
    return True


def hdl_wid_136(_: WIDParams):
    """
    Verify that a call is being held on the Implementation Under Test (IUT).
    """
    return True


def hdl_wid_139(_: WIDParams):
    """
    Click Ok, then place the incoming call on hold using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_hold_incoming(call_index)
    return True


def hdl_wid_140(_: WIDParams):
    """
    Click Ok, then accept the held incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_accept_call(call_index)
    return True


def hdl_wid_141(_: WIDParams):
    """
    Click OK, then reject the held incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_hf_reject_call(call_index)
    return True


def hdl_wid_142(_: WIDParams):
    """
    Click OK, and then verify that the held call is rejected using the Implementation Under
    Test (IUT).
    """
    return True


def hdl_wid_144(_: WIDParams):
    """
    Power off the Implementation Under Test (IUT), then click OK.
    """
    return True


def hdl_wid_148(_: WIDParams):
    """
    Power on the Implementation Under Test (IUT), then click Ok.
    """
    return True


def hdl_wid_149(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in non-discoverable mode, then click Ok.
    """
    btp.gap_set_nonconn()
    btp.gap_set_nondiscov()
    return True


def hdl_wid_151(_: WIDParams):
    """
    Click OK, then verify on the Implementation Under Test (IUT) that the held call is accepted
    and is active, not on hold.
    """
    return True


def hdl_wid_153(_: WIDParams):
    """
    Verify that at least one of the following statements are true:
    """
    return True


def hdl_wid_159(_: WIDParams):
    """
    Click OK, and then send an AT+BIA command to the PTS to activate or deactivate any indicator.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_hf.wait_for_connection(bd_addr):
        return False

    status = 1  # Enable indicator status update
    btp.hfp_hf_indicator_status(status)
    return True


def hdl_wid_168(_: WIDParams):
    """
    Click OK, then initiate an audio connection using the Codec Connection Setup procedure.
    """
    btp.hfp_hf_audio_connect()
    return True


def hdl_wid_169(_: WIDParams):
    """
    Click OK, then initiate an audio connection with WBS codec using the Codec Connection Setup
    procedure.
    """
    btp.hfp_hf_audio_connect()
    return True


def hdl_wid_180(_: WIDParams):
    """
    After performing the following action, click OK.
    Required Action: Trigger an internal event in HF that would cause an update to the AG of the
    supported indicator with Assigned Number: 1,2
    """
    enhanced_safety_enable = 1
    btp.hfp_hf_enhanced_safety(enhanced_safety_enable)
    return True


def hdl_wid_207(params: WIDParams):
    """
    Perform corresponding action on HF to interrupt the audio output from AG to begin a new voice
    command.
    """
    if params.test_case_name in ["HFP/HF/VTA/BV-01-C"]:
        btp.hfp_hf_ready_to_accept_audio()
    return True


def hdl_wid_219(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow a voice recognition
    deactivation from PTS, then click Ok.
    """
    btp.hfp_hf_voice_recognition(0)
    return True


def hdl_wid_220(_: WIDParams):
    """
    Is the IUT capable of establishing connection to an unpaired device?
    """
    return False


def hdl_wid_222(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), activate voice recognition. Then click OK.
    """
    activate = 1  # Activate
    btp.hfp_hf_voice_recognition(activate)
    return True


def hdl_wid_223(_: WIDParams):
    """
    Verify IUT ignores unknown or unexpected indication code.
    """
    return True


def hdl_wid_232(_: WIDParams):
    """
    Please confirm IUT received RFU bit field values after Supported Features exchange and ignored
    the RFU fields.
    """
    return True


def hdl_wid_233(_: WIDParams):
    """
    Please confirm the IUT stops alerting when the incoming call process is interrupted.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_hf.get_call_count(bd_addr) == 0:
        return True
    return False


def hdl_wid_247(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) interprets either held or active call signals,
    then click Ok. If applicable, verify that the information is correctly displayed on the IUT,
    then click Ok.
    """
    return True


def hdl_wid_259(_: WIDParams):
    """
    Please confirm IUT successfully received 'No Home/Roam Network' available indicator.
    """
    return True


def hdl_wid_260(_: WIDParams):
    """
    Please confirm IUT successfully received 'Home/Roam Network' available indicator.
    """
    return True


def hdl_wid_561(_: WIDParams):
    """
    Verify that service level connection exists between the lower tester and IUT, then click Ok.
    """
    stack = get_stack()
    hfp_hf = stack.hfp_hf
    bd_addr = btp.pts_addr_get()

    return hfp_hf.wait_for_connection(addr=bd_addr)


def hdl_wid_606(_: WIDParams):
    """
    Disable service level connection, then click Ok.
    """
    btp.hfp_hf_disconnect()
    return True


def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.
    """
    return True
