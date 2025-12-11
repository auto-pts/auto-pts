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
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug


def hfp_ag_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl

    log(f"{hfp_ag_wid_hdl.__name__}, {wid}, {description}, {test_case_name}")
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_0(params: WIDParams):
    """
    Make the Implementation Under Test (IUT) connectable, then click Ok.
    """
    if params.test_case_name in [
        "HFP/AG/SLC/BV-01-C",
        "HFP/AG/SLC/BV-02-C",
        "HFP/AG/SLC/BV-04-C",
        "HFP/AG/SLC/BV-05-C",
        "HFP/AG/SLC/BV-07-C",
        "HFP/AG/SLC/BV-11-C",
    ]:
        return True

    if params.test_case_name.find("HFP/AG/") >= 0:
        stack = get_stack()
        if not stack.gap.is_connected():
            btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            btp.gap_wait_for_connection()

        btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        if params.test_case_name in ["HFP/AG/SLC/BV-0", "HFP/AG/OOR/BV-02-C"]:
            return True

        btp.hfp_ag_connect(1)

    return True


def hdl_wid_1(params: WIDParams):
    """
    Click Ok, then initiate a service level connection from the Implementation Under Test (IUT) to
    the PTS.
    """

    stack = get_stack()
    stack.gap.set_passkey(None)

    stack.hfp_ag.increase_mmi_round(1)

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
        if not stack.gap.is_connected():
            return False

    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    if params.test_case_name in ["HFP/AG/SLC/BV-11-C", "HFP/AG/SLC/BI-01-C"]:
        return True

    bd_addr = btp.pts_addr_get()
    call_index = 0

    if params.test_case_name in ["HFP/AG/CGSIT/SFC/BV-01-C"]:
        if stack.hfp_ag.get_mmi_round(1) < 2:
            return True

    if not stack.hfp_ag.wait_for_connection(bd_addr):
        btp.hfp_ag_connect(1)

    if params.test_case_name in [
        "HFP/AG/RHH/BV-04-C",
        "HFP/AG/RHH/BV-05-C",
        "HFP/AG/RHH/BV-06-C",
        "HFP/AG/RHH/BV-07-C",
        "HFP/AG/RHH/BV-08-C",
    ]:
        stack.hfp_ag.wait_for_connection(bd_addr)
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index,
                                         defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD)
    return True


def hdl_wid_2(_: WIDParams):
    """
    Click Ok, then disable the service level connection using the Implementation Under Test (IUT).
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_ag.is_connected(bd_addr):
        btp.hfp_ag_disconnect()
    return True


def hdl_wid_3(params: WIDParams):
    """
    Click Ok, then initiate an audio connection (SCO) from the Implementation Under Test (IUT) to
    the PTS.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_ag.sco_is_connected(bd_addr):
        return True

    if params.test_case_name in ["HFP/AG/ACC/BV-17-C"]:
        btp.hfp_ag_audio_connect(2)
        return True
    # Use CVSD codec (codec_id = 1)
    btp.hfp_ag_audio_connect(1)
    return True


def hdl_wid_4(_: WIDParams):
    """
    Click Ok, then close the audio connection (SCO) between the Implementation Under Test (IUT) and
    the PTS.
    Do not close the service level connection (SLC) or power-off the IUT.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_ag.sco_is_disconnected(bd_addr):
        return True

    btp.hfp_ag_audio_disconnect()
    return True


def hdl_wid_5(params: WIDParams):
    """
    Place a call from an external line to the Implementation Under Test (IUT).
    When the call is active, click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if params.test_case_name in ["HFP/AG/ATH/BV-03-C", "HFP/AG/ATH/BV-05-C", "HFP/AG/TWC/BV-04-C",
                                 "HFP/AG/ATH/BV-09-C"]:
        return True

    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
        if not stack.gap.is_connected():
            return False

    if not stack.hfp_ag.wait_for_connection(bd_addr):
        btp.hfp_ag_connect(1)

    if not stack.hfp_ag.wait_for_connection(bd_addr):
        return False

    number = "1234567"
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        number = "7654321"
    btp.hfp_ag_remote_incoming(number)
    return True


def hdl_wid_7(params: WIDParams):
    """
    Click Ok, then answer the incoming call on the external terminal.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0

    if params.test_case_name in ["HFP/AG/OCL/BV-01-C", "HFP/AG/OCM/BV-01-C", "HFP/AG/OCN/BV-01-C"]:
        btp.hfp_ag_remote_ringing(call_index)

    if params.test_case_name in ["HFP/AG/TWC/BV-05-C"]:
        call_index = 1
        btp.hfp_ag_remote_ringing(call_index)
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ALERTING)

    btp.hfp_ag_remote_accept(call_index)
    return True


def hdl_wid_8(_: WIDParams):
    """
    Click Ok, then answer the incoming call on the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_ag_accept_call(call_index)
    return True


def hdl_wid_10(_: WIDParams):
    """
    Click Ok, then reject the incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_ag_reject_call(call_index)
    return True


def hdl_wid_11(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a mode that will allow an outgoing call initiated
    by the PTS,
    and click Ok.
    """
    return True


def hdl_wid_12(params: WIDParams):
    """
    Click Ok, then place a call from an external line to the Implementation Under Test (IUT).
    Do not answer the call unless prompted to do so.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if params.test_case_name in ["HFP/AG/ICA/BV-07-C"]:
        return True

    stack.hfp_ag.wait_for_connection(bd_addr, timeout=30)
    number = "1234567"
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        number = "7654321"
    btp.hfp_ag_remote_incoming(number)
    return True


def hdl_wid_13(_: WIDParams):
    """
    Click Ok, then place a second call from an external line to the Implementation Under Test (IUT).
    Do not answer the call unless prompted to do so.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    number = "1234567"
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        number = "7654321"
    btp.hfp_ag_remote_incoming(number)
    return True


def hdl_wid_14(_: WIDParams):
    """
    Click Ok, then end the call using the Implementation Under Test (IUT).
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    for call_index in stack.hfp_ag.get_calls_index(bd_addr):
        state = stack.hfp_ag.get_call_state(bd_addr, call_index)

        if state == defs.BTP_HFP_AG_CALL_STATUS_ACTIVE or state == defs.BTP_HFP_AG_CALL_STATUS_HELD:
            btp.hfp_ag_remote_terminate(call_index)
            continue

        if state == defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD:
            btp.hfp_ag_terminate_call(call_index)
            continue

        if stack.hfp_ag.get_call_dir(bd_addr, call_index) == defs.BTP_HFP_AG_CALL_DIR_INCOMING:
            btp.hfp_ag_reject_call(call_index)
            continue
        else:
            btp.hfp_ag_remote_reject(call_index)
            continue
    return True


def hdl_wid_15(_: WIDParams):
    """
    Click Ok, then end the call using the external terminal.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    for call_index in stack.hfp_ag.get_calls_index(bd_addr):
        state = stack.hfp_ag.get_call_state(bd_addr, call_index)

        if state == defs.BTP_HFP_AG_CALL_STATUS_ACTIVE or state == defs.BTP_HFP_AG_CALL_STATUS_HELD:
            btp.hfp_ag_remote_terminate(call_index)
            continue

        if state == defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD:
            btp.hfp_ag_terminate_call(call_index)
            continue

        if stack.hfp_ag.get_call_dir(bd_addr, call_index) == defs.BTP_HFP_AG_CALL_DIR_INCOMING:
            btp.hfp_ag_reject_call(call_index)
            continue
        else:
            btp.hfp_ag_remote_reject(call_index)
            continue
    return True


def hdl_wid_18(_: WIDParams):
    """
    Clear the call history on the Implementation Under Test (IUT) such that there are zero records
    of any numbers dialed, then click Ok.
    """
    return True


def hdl_wid_25(_: WIDParams):
    """
    Click Ok, then end the call process from the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_ag_terminate_call(call_index)
    return True


def hdl_wid_33(_: WIDParams):
    """
    Click Ok, then disable the in-band ringtone using the Implementation Under Test (IUT).
    """
    state = 0  # Disable
    btp.hfp_ag_set_inband_ringtone(state)
    return True


def hdl_wid_34(_: WIDParams):
    """
    Click Ok, then enable the in-band ringtone using the Implementation Under Test (IUT).
    """
    state = 1  # Enable
    btp.hfp_ag_set_inband_ringtone(state)
    return True


def hdl_wid_35(_: WIDParams):
    """
    Verify the presence of an audio connection, then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_ag.wait_for_sco_connection(bd_addr):
        return True
    return False


def hdl_wid_36(_: WIDParams):
    """
    Verify the audio is returned to the 1st call and click Ok. Resume action may be needed.
    If the audio is not present in the 1st call, click Cancel.
    """
    return True


def hdl_wid_37(params: WIDParams):
    """
    Verify the audio is returned to the 2nd call and then click Ok. Resume action may be needed.
    If the audio is not returned to the 2nd call, click Cancel.
    """
    if params.test_case_name in ["HFP/AG/ECS/BV-03-C"]:
        call_index = 1
        btp.hfp_ag_hold_call(call_index)
    return True


def hdl_wid_38(_: WIDParams):
    """
    Verify each of the following test conditions are true:
    """
    return True


def hdl_wid_39(_: WIDParams):
    """
    Verify the absence of an audio connection (SCO), then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_ag.sco_is_connected(bd_addr):
        return False
    return True


def hdl_wid_40(_: WIDParams):
    """
    Verify the absence of the following audio paths:
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_ag.sco_is_connected(bd_addr):
        return False
    return True


def hdl_wid_41(_: WIDParams):
    """
    Click Ok, then disable the network using the Implementation Under Test (IUT) by performing
    one of the below actions:
    """
    state = 0  # Network unavailable
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_42(_: WIDParams):
    """
    Click Ok, then enable the network using the Implementation Under Test (IUT).
    """
    state = 1  # Network available
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_44(_: WIDParams):
    """
    Verify the DTMF code #, then click Ok.
    """
    return True


def hdl_wid_46(_: WIDParams):
    """
    Verify that EC and NR functionality is disabled, then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    if stack.hfp_ag.wait_for_ecnr_off(bd_addr):
        return True
    return False


def hdl_wid_53(params: WIDParams):
    """
    Verify that the signal reported on the Implementation Under Test (IUT) is proportional
    to the value (out of 5), then click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    stack.hfp_ag.wait_for_connection(bd_addr)

    value = int(params.description[-1])
    if value > 0:
        btp.hfp_ag_set_signal_strength(value)
    else:
        btp.hfp_ag_set_signal_strength(5)
    return True


def hdl_wid_56(_: WIDParams):
    """
    Enable roaming on the Implementation Under Test (IUT), then click Ok.
    """
    state = 1  # Roaming
    btp.hfp_ag_set_roaming_status(state)
    return True


def hdl_wid_57(_: WIDParams):
    """
    Disable roaming on the Implementation Under Test (IUT), then click Ok.
    """
    state = 0  # Not roaming
    btp.hfp_ag_set_roaming_status(state)
    return True


def hdl_wid_60(_: WIDParams):
    """
    Click Ok, then manipulate the Implementation Under Test (IUT) so that the battery is fully
    charged.
    """
    level = 5  # Fully charged
    btp.hfp_ag_set_battery_level(level)
    return True


def hdl_wid_61(_: WIDParams):
    """
    Manipulate the Implementation Under Test (IUT) so that the battery level is not fully charged,
    then click Ok.
    """
    level = 3  # Medium level
    btp.hfp_ag_set_battery_level(level)
    return True


def hdl_wid_62(_: WIDParams):
    """
    Verify the following information matches the network operator reported on the
    Implementation Under Test (IUT), then click Ok: "UNKNOWN"
    """
    return True


def hdl_wid_70(_: WIDParams):
    """
    Set the speaker volume of the Implementation Under Test (IUT) to the default/nominal level,
    then click Ok.
    """
    gain = 7  # Default/nominal level (0-15 range)
    btp.hfp_ag_set_vgs(gain)
    return True


def hdl_wid_71(_: WIDParams):
    """
    Set the speaker volume of the Implementation Under Test (IUT) to a level that is greater
    to the default/nominal level, then click Ok.
    """
    gain = 12  # Higher than default
    btp.hfp_ag_set_vgs(gain)
    return True


def hdl_wid_73(params: WIDParams):
    """
    Set the mic volume of the Implementation Under Test (IUT) to the default/nominal level,
    then click Ok.
    """
    gain = 7  # Default/nominal level
    if params.test_case_name in ["HFP/AG/RSV/BV-01-C"]:
        btp.hfp_ag_set_vgs(gain)
    else:
        btp.hfp_ag_set_vgm(gain)
    return True


def hdl_wid_74(_: WIDParams):
    """
    Set the mic volume of the Implementation Under Test (IUT) above the default/nominal level,
    then click Ok.
    """
    gain = 12  # Higher than default
    btp.hfp_ag_set_vgm(gain)
    return True


def hdl_wid_76(params: WIDParams):
    """
    Verify that the Hands Free (HF) speaker volume is displayed correctly on the
    Implementation Under Test (IUT).
    """
    gain = int(re.sub(r"\D", "", params.description[-2:]))
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_ag.wait_for_vgs(bd_addr, gain)


def hdl_wid_77(params: WIDParams):
    """
    Verify that the Hands Free (HF) mic volume is displayed correctly on the
    Implementation Under Test (IUT), then click Ok.
    """
    gain = int(re.sub(r"\D", "", params.description[-2:]))
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    return stack.hfp_ag.wait_for_vgm(bd_addr, gain)


def hdl_wid_78(params: WIDParams):
    """
    NOTE: The following rules apply for this test case:
    1. TSPX_phone_number - the 1st call
    2. TSPX_second_phone_number - the 2nd call
    """
    if params.test_case_name in ["HFP/AG/TWC/BV-02-C", "HFP/AG/TWC/BV-03-C", "HFP/AG/TWC/BV-04-C",
                                 "HFP/AG/TWC/BV-05-C", "HFP/AG/TWC/BV-06-C"]:
        return True

    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    number = "1234567"
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        number = "7654321"
    btp.hfp_ag_remote_incoming(number)
    return True


def hdl_wid_79(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), verify that the following is a valid Audio Gateway
    (AG) subscriber number, then click Ok."1234"
    """
    return True


def hdl_wid_81(params: WIDParams):
    """
    Verify that the following number is a valid number in the Audio Gateway (AG) to use as
    a voice tag in the Hands Free (HF), then click Ok. NP:"+8613812345678"
    """
    if params.test_case_name in ["HFP/AG/VTG/BV-01-C"]:
        stack = get_stack()
        bd_addr = btp.pts_addr_get()
        if stack.hfp_ag.is_connected(bd_addr):
            btp.hfp_ag_disconnect()
    return True


def hdl_wid_84(_: WIDParams):
    """
    Using the Implementation Under Test (IUT), deactivate voice recognition.
    """
    activate = 0  # Deactivate
    btp.hfp_ag_voice_recognition(activate)
    return True


def hdl_wid_85(_: WIDParams):
    """
    Clear the memory indexed by TSPX_phone_number_memory on the AG such that the memory slot
    becomes empty, then Click OK.
    """
    btp.hfp_ag_set_memory_dial_mapping("1", None)
    return True


def hdl_wid_86(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow a request from the PTS
    to activate voice recognition, then click Ok.
    """
    return True


def hdl_wid_87(params: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow the PTS to request
    a voice tag number, then click Ok.
    """
    if params.test_case_name in ["HFP/AG/VTG/BV-01-C"]:
        stack = get_stack()
        bd_addr = btp.pts_addr_get()
        if stack.hfp_ag.sco_is_connected(bd_addr):
            return True

        btp.hfp_ag_audio_connect(1)
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
    btp.hfp_ag_disconnect()
    stack = get_stack()
    stack.hfp_ag.wait_for_disconnection(bd_addr)
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


def hdl_wid_105(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to initiate
    a AT+CHLD=1 operation, then click Ok.
    """
    return True


def hdl_wid_106(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to initiate
    a AT+CHLD=2 operation, then click Ok.
    """
    return True


def hdl_wid_107(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to initiate
    a AT+CHLD=4 operation, then click OK.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0
    stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_HELD)
    btp.hfp_ag_retrieve_call(call_index)
    stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)
    return True


def hdl_wid_108(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to answer
    the call being set up, then click Ok.
    """
    return True


def hdl_wid_109(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that will allow the PTS to initiate
    an outgoing call, then click Ok.
    """
    return True


def send_vre_text(bd_addr):
    btp.hfp_ag_vre_text(1, 2, 0, 1, "1")


def release_audio_connection(bd_addr):
    btp.hfp_ag_audio_disconnect()


def hdl_wid_110(params: WIDParams):
    """
    Set the Implementation Under Test (IUT) in a state that can receive the following AT Command,
    then click Ok: AT+BVRA=2
    """
    bd_addr = btp.pts_addr_get()
    stack = get_stack()

    if params.test_case_name in ["HFP/AG/VTA/BV-02-C"]:
        stack.hfp_ag.register_ready_accept_audio_callback(bd_addr, release_audio_connection)

    if stack.hfp_ag.sco_is_connected(bd_addr):
        return True

    btp.hfp_ag_audio_connect(1)

    if params.test_case_name in ["HFP/AG/VRT/BV-01-C"]:
        stack.hfp_ag.register_ready_accept_audio_callback(bd_addr, send_vre_text)

    return True


def hdl_wid_114(_: WIDParams):
    """
    Set the Implementation Under Test (IUT) in an appropriate state which will allow the PTS
    to initiate an audio connection (SCO), then click Ok.
    """
    return True


def hdl_wid_117(_: WIDParams):
    """
    End the call using the external terminal, then click Ok.
    """
    call_index = 0
    btp.hfp_ag_reject_call(call_index)
    return True


def hdl_wid_119(_: WIDParams):
    """
    Verify that the last number dialed on the Implementation Under Test (IUT) matches
    the TSPX_Second_phone_number entered in the IXIT settings.
    """
    return True


def hdl_wid_121(params: WIDParams):
    """
    Click Ok, then make a connection request to the PTS from the Implementation Under Test (IUT).
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

        if params.test_case_name in ["HFP/AG/SLC/BV-02-C", "HFP/AG/SLC/BV-04-C"]:
            return True

        btp.gap_wait_for_connection()

    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    btp.hfp_ag_connect(1)
    if params.test_case_name in ["HFP/AG/RHH/BV-08-C"]:
        stack.hfp_ag.wait_for_connection(bd_addr)
        call_index = 0
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index,
                                         defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD)
    return True


def hdl_wid_124(_: WIDParams):
    """
    Verify that the audio (SCO) is removed from the 1st call, then click OK.
    Please note that the audio may or may not be returned to the 2nd call.
    """
    return True


def hdl_wid_126(_: WIDParams):
    """
    The PTS will send a call request containing an invalid/out of range memory index from
    the TSPX_phone_number_memory_invalid_index found in the IXIT settings.
    """
    return True


def hdl_wid_130(_: WIDParams):
    """
    Click Ok, then place the current call on hold and make the incoming/held call active
    using the Implementation Under Test (IUT).
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0
    if stack.hfp_ag.get_call_state(bd_addr, call_index) == defs.BTP_HFP_AG_CALL_STATUS_ACTIVE:
        btp.hfp_ag_hold_call(call_index)
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_HELD)
    call_index = 1
    btp.hfp_ag_accept_call(call_index)
    return True


def hdl_wid_133(_: WIDParams):
    """
    Click OK, then integrate the held call to the conversation using the Implementation Under
    Test (IUT).
    Both external calls will be joined in the conversation.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0
    if stack.hfp_ag.get_call_state(bd_addr, call_index) == defs.BTP_HFP_AG_CALL_STATUS_HELD:
        btp.hfp_ag_retrieve_call(call_index)
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)
    return True


def hdl_wid_135(params: WIDParams):
    """
    Place a call from an external line to the Implementation Under Test (IUT).
    Place the call on hold after accepting, then click Ok.
    """
    if params.test_case_name in ["HFP/AG/RHH/BV-01-C"]:
        return True

    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.gap.is_connected():
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    btp.gap_pair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    if not stack.hfp_ag.is_connected(bd_addr):
        btp.hfp_ag_connect(1)
    return True


def hdl_wid_136(_: WIDParams):
    """
    Verify that a call is being held on the Implementation Under Test (IUT).
    """
    return True


def hdl_wid_140(_: WIDParams):
    """
    Click Ok, then accept the held incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_ag_accept_call(call_index)
    return True


def hdl_wid_141(_: WIDParams):
    """
    Click OK, then reject the held incoming call using the Implementation Under Test (IUT).
    """
    call_index = 0
    btp.hfp_ag_reject_call(call_index)
    return True


def hdl_wid_143(_: WIDParams):
    """
    Verify that the call is still active and audio (SCO) is returned to the
    Implementation Under Test (IUT).
    """
    return True


def hdl_wid_145(_: WIDParams):
    """
    Verify that there is an incoming call on the Implementation Under Test (IUT).
    """
    return True


def hdl_wid_146(_: WIDParams):
    """
    Verify that there is an incoming call on the Implementation Under Test (IUT).
    """
    return True


def hdl_wid_147(params: WIDParams):
    """
    Place an outgoing call using the Implementation Under Test (IUT). When the call is active
    click Ok.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    number = "7654321"
    call_index = 0
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        call_index = 1
    btp.hfp_ag_outgoing(number)
    if params.test_case_name in ["HFP/AG/OCA/BV-01-C"]:
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_DIALING)
        btp.hfp_ag_remote_ringing(call_index)
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ALERTING)
        btp.hfp_ag_remote_accept(call_index)

    return True


def hdl_wid_150(_: WIDParams):
    """
    Click OK, then place a call from an external line to the Implementation Under Test (IUT).
    Accept and then place the call on hold using the IUT.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    call_index = 0
    number = "1234567"
    if stack.hfp_ag.get_call_count(bd_addr) > 0:
        number = "7654321"
        call_index = 1

    btp.hfp_ag_remote_incoming(number)
    if stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_INCOMING):
        btp.hfp_ag_hold_incoming(call_index)
        return True
    return False


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


def hdl_wid_154(_: WIDParams):
    """
    After the test verdict is given, end all active calls using the external line or the
    Implementation Under Test (IUT). Click OK to continue.
    """
    return True


def hdl_wid_155(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will accept an outgoing call
    set-up request from the PTS, then click OK.
    """
    return True


def hdl_wid_156(_: WIDParams):
    """
    Verify that the Implementation Under Test (IUT) has called the last dialed number and
    the bi-directional conversation is available between the external line and the HF.
    """
    return True


def hdl_wid_158(_: WIDParams):
    """
    Place a second call from an external line to the Audio Gateway (AG) or place an outgoing call
    from the AG, putting the currently active call on hold using the AG.
    When the second call is active on the AG, and the first is on hold, click OK.
    """
    return True


def hdl_wid_160(_: WIDParams):
    """
    Impair the signal to the AG so that a reduction in signal strength can be observed. Then,
    click OK.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_ag.wait_for_connection(bd_addr):
        return False
    strength = 2  # Reduced signal strength
    btp.hfp_ag_set_signal_strength(strength)
    return True


def hdl_wid_161(_: WIDParams):
    """
    Click OK. Then register AG on a Roam network.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_ag.wait_for_connection(bd_addr):
        return False
    state = 1  # Roaming
    btp.hfp_ag_set_roaming_status(state)
    return True


def hdl_wid_162(_: WIDParams):
    """
    Click OK. Then register AG on the Home network.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if not stack.hfp_ag.wait_for_connection(bd_addr):
        return False
    state = 0  # Not roaming
    btp.hfp_ag_set_roaming_status(state)
    return True


def hdl_wid_163(_: WIDParams):
    """
    Adjust the battery level on the AG to a level that should cause a battery level indication
    to be sent to HF. Then, click OK.
    """
    level = 3  # Medium battery level
    btp.hfp_ag_set_battery_level(level)
    return True


def hdl_wid_164(_: WIDParams):
    """
    Click OK. Then, use a test device to simulate the presence of a control channel of a network,
    such that the AG is registered.
    """
    state = 1  # Network available
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_165(_: WIDParams):
    """
    Click OK. Then, disable the control channel, such that the AG is de-registered.
    """
    state = 0  # Network unavailable
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_168(params: WIDParams):
    """
    Click OK, then initiate an audio connection using the Codec Connection Setup procedure.
    """
    if params.test_case_name in ["HFP/AG/ACC/BV-22-C", "HFP/AG/ACC/BV-24-C", "HFP/AG/ACC/BV-25-C"]:
        return True

    if params.test_case_name in ["HFP/AG/TDS/BV-01-C"]:
        codec_id = 2  # mSBC codec (WBS)
    else:
        codec_id = 1  # CVSD codec
    btp.hfp_ag_audio_connect(codec_id)
    return True


def hdl_wid_169(_: WIDParams):
    """
    Click OK, then initiate an audio connection with WBS codec using the Codec Connection Setup
    procedure.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    if stack.hfp_ag.wait_for_sco_connection(bd_addr, timeout=5):
        return True

    codec_id = 2  # mSBC codec (WBS)
    btp.hfp_ag_audio_connect(codec_id)
    return True


def hdl_wid_170(_: WIDParams):
    """
    Click OK. Then take action so that the network becomes unavailable to the IUT.
    """
    stack = get_stack()
    bd_addr = btp.pts_addr_get()

    for call_index in stack.hfp_ag.get_calls_index(bd_addr):
        stack.hfp_ag.wait_for_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)
        btp.hfp_ag_terminate_call(call_index)

    state = 0  # Network unavailable
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_172(_: WIDParams):
    """
    Click OK. Then take action to make a change that normally would trigger a change in a
    non-mandatory indicator, e.g., force the AG to disable the presence of a network.
    """
    state = 0  # Network unavailable
    btp.hfp_ag_set_service_availability(state)
    return True


def hdl_wid_173(_: WIDParams):
    """
    Click OK. Then adjust the battery level on the AG to a level that should cause a battery level
    indication to be sent to HF.
    """
    level = 4  # High battery level
    btp.hfp_ag_set_battery_level(level)
    return True


def hdl_wid_175(_: WIDParams):
    """
    Click OK. Then, impair the signal to the AG so that a reduction in signal strength can be
    observed.
    """
    strength = 1  # Low signal strength
    btp.hfp_ag_set_signal_strength(strength)
    return True


def hdl_wid_177(_: WIDParams):
    """
    Disable the control channel, such that the AG is de-registered. Then, click OK.
    """
    return True


def hdl_wid_187(_: WIDParams):
    """
    Prepare the IUT for a PTS-initiated AT+CHLD=3 operation, where the PTS will request the AG-IUT
    join the active and held calls into a conference, then Click OK
    """
    return True


def hdl_wid_188(_: WIDParams):
    """
    Set the mic volume of the Implementation Under Test (IUT) to the maximum level, then click Ok.
    """
    gain = 15  # Maximum level
    btp.hfp_ag_set_vgm(gain)
    return True


def hdl_wid_189(params: WIDParams):
    """
    Set the mic volume on the Implementation Under Test (IUT) to zero (0), then click Ok.
    """
    gain = 0  # Minimum level
    if params.test_case_name in ["HFP/AG/RSV/BV-02-C"]:
        btp.hfp_ag_set_vgs(gain)
    else:
        btp.hfp_ag_set_vgm(gain)
    return True


def hdl_wid_190(_: WIDParams):
    """
    Set the speaker volume of the Implementation Under Test (IUT) to the maximum level, then
    click Ok.
    """
    gain = 15  # Maximum level
    btp.hfp_ag_set_vgs(gain)
    return True


def hdl_wid_191(_: WIDParams):
    """
    Set the speaker volume of the Implementation Under Test (IUT) to the maximum level, then
    click Ok.
    """
    gain = 0  # Maximum level
    btp.hfp_ag_set_vgs(gain)
    return True


def hdl_wid_193(_: WIDParams):
    """
    Perform the action in the IUT(AG) such that its Voice Recognition audio input is activated.
    """
    activate = 1  # the AG is ready to accept audio input
    btp.hfp_ag_vre_state(activate)
    return True


def hdl_wid_194(_: WIDParams):
    """
    Perform the action in the IUT(AG) such that its Voice Recognition wants to send an audio output.
    """
    state = 2  # the AG is sending audio to the HF
    btp.hfp_ag_vre_state(state)
    return True


def hdl_wid_195(_: WIDParams):
    """
    Perform the action in the IUT(AG) such that its Voice Recognition processes VR audio input from
    HF.
    """
    state = 4  # the AG is processing the audio input
    btp.hfp_ag_vre_state(state)
    return True


def hdl_wid_196(_: WIDParams):
    """
    Perform the action such that the AG's Voice Recognition audio input is activated and that the AG
    processes the audio input.
    """
    activate = 5  # Activate
    btp.hfp_ag_vre_state(activate)
    return True


def hdl_wid_197(params: WIDParams):
    """
    Perform the Test Procedure:
    1. Perform the action such that AG sends +BVRA with a valid 'textType' and any 'textID' value.
    2. Perform the action such that AG sends another +BVRA with a valid 'textType' other than
    before.
    """
    if params.test_case_name in ["HFP/AG/VRT/BV-02-C"]:
        btp.hfp_ag_vre_text(1, 11, 0, 1, "1")
        sleep(0.5)
        btp.hfp_ag_vre_text(2, 12, 1, 1, "1")
        return True

    btp.hfp_ag_vre_text(1, 1, 1, 1, "1")
    sleep(0.5)
    btp.hfp_ag_vre_text(1, 1, 2, 1, "1")
    sleep(0.5)
    btp.hfp_ag_vre_text(1, 1, 3, 1, "1")
    return True


def hdl_wid_198(_: WIDParams):
    """
    Perform the Test Procedure:
    1. Perform the action such that AG sends +BVRA with a valid 'textType' and any 'textID' value.
    2. Perform the action such that AG sends another +BVRA with a valid 'textType' other than
    before, the 'textID' other than before, and the 'textOperation' ID value 1.
    """
    btp.hfp_ag_vre_text(1, 11, 0, 1, "1")
    sleep(0.5)
    btp.hfp_ag_vre_text(1, 12, 1, 1, "1")
    return True


def hdl_wid_199(_: WIDParams):
    """
    Perform the Test Procedure:
    1. Perform the action such that AG sends +BVRA with a valid 'textType' and any 'textID' value.
    2. Perform the action such that AG sends another +BVRA with a valid 'textType' and 'textID'
    from before, and the 'textOperation' ID value 2.
    """
    btp.hfp_ag_vre_text(1, 11, 0, 1, "1")
    sleep(0.5)
    btp.hfp_ag_vre_text(1, 11, 0, 2, "1")
    return True


def hdl_wid_200(_: WIDParams):
    """
    Perform the Test Procedure:
    1. Perform the action such that AG sends +BVRA with a valid 'textType' and any 'textID' value.
    2. Perform the action such that AG sends another +BVRA with a valid 'textType' and 'textID'
    from before, and the 'textOperation' ID value 3.
    """
    btp.hfp_ag_vre_text(1, 11, 0, 1, "1")
    sleep(0.5)
    btp.hfp_ag_vre_text(1, 11, 0, 3, "1")
    return True


def hdl_wid_201(_: WIDParams):
    """
    Perform the action such that IUT it sends the result code +BVRA with 'vrect' value 1, a valid
    'vrectstate', a valid 'textID', the 'textType' ID value 0, a valid 'textOperation' ID, and the
    well formatted string with a textual representation of the input sentence.
    """
    btp.hfp_ag_vre_text(1, 11, 0, 1, "test")
    return True


def hdl_wid_202(_: WIDParams):
    """
    Perform the action such that IUT it sends the result code +BVRA with 'vrect' value 1, a valid
    'vrectstate', a valid 'textID', the 'textType' ID value 1, a valid 'textOperation' ID, and the
    well formatted string with a textual representation of the input sentence.
    """
    btp.hfp_ag_vre_text(1, 11, 1, 1, "test")
    return True


def hdl_wid_203(_: WIDParams):
    """
    Perform the action such that IUT it sends the result code +BVRA with 'vrect' value 1, a valid
    'vrectstate', a valid 'textID', the 'textType' ID value 2, a valid 'textOperation' ID, and the
    well formatted string with a textual representation of the input sentence.
    """
    btp.hfp_ag_vre_text(1, 11, 2, 1, "test")
    return True


def hdl_wid_204(_: WIDParams):
    """
    Perform the action such that IUT it sends the result code +BVRA with 'vrect' value 1, a valid
    'vrectstate', a valid 'textID', the 'textType' ID value 3, a valid 'textOperation' ID, and the
    well formatted string with a textual representation of the input sentence.
    """
    btp.hfp_ag_vre_text(1, 11, 3, 1, "test")
    return True


def hdl_wid_219(params: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow a voice recognition
    deactivation from PTS, then click Ok.
    """
    if params.test_case_name in ["HFP/AG/VRA/BV-03-C", "HFP/AG/VRA/BV-04-C", "HFP/AG/VRT/BV-01-C"]:
        return True
    activate = 0  # Activate
    btp.hfp_ag_voice_recognition(activate)
    return True


def hdl_wid_220(_: WIDParams):
    """
    Is the IUT capable of establishing connection to an unpaired device?
    """
    return False


def hdl_wid_222(params: WIDParams):
    """
    Using the Implementation Under Test (IUT), activate voice recognition. Then click OK.
    """
    if params.test_case_name in ["HFP/AG/VRT/BV-01-C", "HFP/AG/VRT/BV-02-C"]:
        return True
    activate = 1  # Activate
    btp.hfp_ag_voice_recognition(activate)
    return True


def hdl_wid_230(_: WIDParams):
    """
    Click OK, then initiate an audio connection using the CVSD Codec and Connection Setup procedure.
    """
    codec_id = 1  # CVSD codec
    btp.hfp_ag_audio_connect(codec_id)
    return True


def hdl_wid_231(_: WIDParams):
    """
    Click OK, then initiate an audio connection using the CVSD Codec and Connection Setup procedure.
    """
    codec_id = 2  # SWB codec
    btp.hfp_ag_audio_connect(codec_id)
    return True


def hdl_wid_246(params: WIDParams):
    """
    Place a call from an external line to the Implementation Under Test (IUT), or putting the
    current active call on hold. When the call is active or hold, click Ok.
    """
    if params.test_case_name in ["HFP/AG/ECS/BV-02-C"]:
        return True

    stack = get_stack()
    number = "1234567"
    if stack.hfp_ag.get_call_count() > 0:
        number = "7654321"
    btp.hfp_ag_remote_incoming(number)
    return True


def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.
    """
    return True
