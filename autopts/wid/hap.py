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

from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp.types import *
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.wid import generic_wid_hdl

log = logging.debug


def hap_wid_hdl(wid, description, test_case_name):
    log(f'{hap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_477(_: WIDParams):
    """
        Please verify that the IUT starts alerting with a High Alert.
    """
    stack = get_stack()

    stack.ias.wait_for_high_alert()

    return stack.ias.alert_lvl == 2


def hdl_wid_482(_: WIDParams):
    """
        Please configure to Streaming state.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # TODO: Rewrite this test to use CAP API instead

    audio_dir = AudioDir.SINK
    coding_format = 0x06
    audio_location_list = [defs.PACS_AUDIO_LOCATION_FRONT_LEFT, defs.PACS_AUDIO_LOCATION_FRONT_RIGHT]
    ase_ids = []

    for audio_location in audio_location_list:
        # Find ID of the ASE
        ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
        if ev is None:
            return False

        _, _, _, ase_id = ev

        logging.debug(f"About to configure ASE_ID: {ase_id} Location: {audio_location}")

        # 24_1
        sampling_freq = SAMPLING_FREQ_STR_TO_CODE['24']
        frame_duration = FRAME_DURATION_STR_TO_CODE['7.5']
        octets_per_frame = 45
        audio_locations = audio_location
        frames_per_sdu = 0x01

        # Perform Codec Config operation
        codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                                 audio_locations, octets_per_frame,
                                                 frames_per_sdu)
        btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

        ase_ids.append(ase_id)

    cig_id = 0x00
    cis_id = 0x00
    for ase_id in ase_ids:
        btp.ascs_add_ase_to_cis(ase_id, cis_id, cig_id)
        cis_id += 1

    # Perform Config QOS operation
    presentation_delay = 40000
    qos_config = QOS_CONFIG_SETTINGS['24_1_1']
    btp.ascs_config_qos(ase_ids[0], cig_id, 0x00, *qos_config, presentation_delay)

    for ase_id in ase_ids:
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    for ase_id in ase_ids:
        # Enable streams
        btp.ascs_enable(ase_id)
        stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    return True


def hdl_wid_489(_: WIDParams):
    """
        Please click OK after IUT sync to BIS.
    """
    addr, addr_type = btp.pts_addr_get(), btp.pts_addr_type_get()
    stack = get_stack()

    btp.bap_broadcast_sink_setup()
    btp.bap_broadcast_scan_start()
    ev = stack.bap.wait_baa_found_ev(addr_type, addr, 30)
    btp.bap_broadcast_scan_stop()
    if ev:
        id, sid, addr_type, addr = ev['broadcast_id'], ev['advertiser_sid'], ev['addr_type'], ev['addr']
        btp.bap_broadcast_sink_sync(id, sid, 5, 600, False, 0, addr_type, addr)
        ev = stack.bap.wait_bis_found_ev(id, 50)

    return not ev is None


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(_: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    stack = get_stack()

    btp.gap_conn()
    stack.gap.gap_wait_for_sec_lvl_change(30)

    return True


def hdl_wid_20103(_: WIDParams):
    """
        Please take action to discover the Alert Level characteristic from the Immediate Alert.
        Discover the primary service if needed.
        Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.hap_iac_discover(addr_type, addr)
    stack.hap.wait_iac_discovery_complete_ev(addr_type, addr, 30)

    return True


def hdl_wid_20106(_: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor of ASE
        Control Point characteristic to enable notification.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    peer = stack.bap.get_peer(addr_type, addr)
    if peer.discovery_completed:
        # Skip if discovery has been done already
        return True

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    return True


def hdl_wid_20116(_: WIDParams):
    """
        Please send command to the PTS to discover all mandatory characteristics of the
        Hearing Access supported by the IUT. Discover primary service if needed.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    btp.hap_hauc_discover(addr_type, addr)
    stack.hap.wait_hauc_discovery_complete_ev(addr_type, addr, 30)

    return True


def hdl_wid_20121(params: WIDParams):
    """
        Please write value with write command (without response) to handle 0x01E2 with following value.
        Any attribute value
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    # XXX: The description is quite general, thus let's make this handler conditional
    if params.test_case_name == 'HAP/IAC/CGGIT/CHA/BV-01-C':
        btp.hap_iac_set_alert(addr_type, addr, btp.defs.HAP_IAC_ALERT_LEVEL_MILD)

    return True


def hdl_wid_20128(_: WIDParams):
    """
        Please remove LTK from IUT before proceeding.
    """
    btp.gap_unpair()
    return True


def hdl_wid_20144(_: WIDParams):
    """
        Please click Yes if IUT support Write Command(without response), otherwise click No.
    """
    return True


def hdl_wid_20206(params: WIDParams):
    """
        Please verify that for each supported characteristic, attribute handle/UUID pair(s)
        is returned to the upper tester. (...)
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    MMI.reset()
    MMI.parse_description(params.description)

    if not MMI.args:
        return False

    # split MMI args into dict[uuid] = val_hdl
    val_hdl_dict = {}
    for i in range(0, len(MMI.args), 4):
        uuid = MMI.args[i + 3].upper().replace("0X", "")
        value_hdl = int(MMI.args[i + 2], 16)

        val_hdl_dict[uuid] = value_hdl

    stack = get_stack()

    try:
        peer = stack.hap.get_peer(addr_type, addr)

        return (val_hdl_dict[UUID.HAS_HEARING_AID_FEATUES] == peer.hearing_aid_features_handle and
                val_hdl_dict[UUID.HAS_HEARING_AID_CONTROL_POINT] == peer.hearing_aid_control_point_handle and
                val_hdl_dict[UUID.HAS_ACTIVE_PRESET_INDEX] == peer.active_preset_index_handle)
    except KeyError:
        return False
