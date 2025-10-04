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
import re
import struct
from argparse import Namespace

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp, defs
from autopts.pybtp.btp.btp import lt2_addr_get, lt2_addr_type_get, pts_addr_get, pts_addr_type_get
from autopts.pybtp.defs import AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS
from autopts.pybtp.types import (
    CODEC_CONFIG_SETTINGS,
    QOS_CONFIG_SETTINGS,
    UUID,
    ASCSState,
    AudioDir,
    WIDParams,
    create_lc3_ltvs_bytes,
)

log = logging.debug


def create_default_config():
    return Namespace(addr=pts_addr_get(),
                     addr_type=pts_addr_type_get(),
                     vid=0x0000,
                     cid=0x0000,
                     coding_format=0x06,
                     frames_per_sdu=0x01,
                     audio_locations=0x01,
                     cig_id=0x00,
                     cis_id=0x00,
                     presentation_delay=40000,
                     qos_config=None,
                     codec_set_name=None,
                     codec_ltvs=None,
                     metadata_ltvs=None,
                     mono=None)


def hap_start_hap_discovery(addr_type, addr):
    stack = get_stack()
    peer = stack.hap.get_peer(addr_type, addr)
    if peer.discover_started:
        log('Skip HAP discovery, discovery started before')
        return

    peer.discover_started = True
    btp.hap_hauc_discover(addr_type, addr)
    stack.hap.wait_hauc_discovery_complete_ev(addr_type, addr, 30)


# wid handlers section begin
def hdl_wid_462(params: WIDParams):
    """
    Please write Set Active Preset opcode with index: X.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    preset_index = int(re.search(r'\d+', params.description).group())
    btp.hap_set_active_preset(preset_index, 0, addr_type, addr)

    return True


def hdl_wid_463(params: WIDParams):
    """
    Please write Set Next Preset opcode
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.hap_set_next_preset(0, addr_type, addr)

    return True


def hdl_wid_464(params: WIDParams):
    """
    Please write Set Previous Preset opcode
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.hap_set_previous_preset(0, addr_type, addr)

    return True


def hdl_wid_465(params: WIDParams):
    """
    Please write Read Preset opcode with index 0x01 and num presets to 0xff.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    numbers = re.findall(r'0x[0-9a-fA-F]+', params.description)
    start_index = int(numbers[0], 16)
    num_presets = int(numbers[1], 16)
    btp.hap_read_presets(start_index, num_presets, addr_type, addr)

    return True


def hdl_wid_466(params: WIDParams):
    """
    Please write Read Preset Index opcode with index: 2, numPresets: 1.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    numbers = re.findall(r'\d+', params.description)
    start_index = int(numbers[0])
    num_presets = int(numbers[0])
    btp.hap_read_presets(start_index, num_presets, addr_type, addr)

    return True


def hdl_wid_467(params: WIDParams):
    """
    Please confirm that new preset record was added to IUT's internal list.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    preset_change_received = stack.hap.wait_preset_changed_ev(addr_type, addr, 0, 30)

    return preset_change_received


def hdl_wid_468(params: WIDParams):
    """
    Please update Index: 2 with new name in "New Preset Name"
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    match = re.search(r'Index:\s*(\d+)\s*with new name in\s*"([^"]+)"', params.description)
    if not match:
        return False

    preset_index = int(match.group(1))
    name = match.group(2)
    btp.hap_write_preset_name(preset_index, name, addr_type, addr)

    return True


def hdl_wid_469(params: WIDParams):
    """
    Please write Set Active Preset Synchronized Locally opcode with index: X.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    preset_index = int(re.search(r'\d+', params.description).group())
    btp.hap_set_active_preset(preset_index, 1, addr_type, addr)

    return True


def hdl_wid_470(params: WIDParams):
    """
    Please write Set Next Preset Synchronized Locally opcode
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.hap_set_next_preset(1, addr_type, addr)

    return True


def hdl_wid_471(params: WIDParams):
    """
    Please write Set Previous Preset Synchronized Locally opcode.
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.hap_set_previous_preset(1, addr_type, addr)

    return True


def hdl_wid_472(params: WIDParams):
    """
    Please write Set Active Preset opcode with index: 2. Do not expect to receive the message
    """

    # similar to 'Please write Set Active Preset opcode with index: X'
    return hdl_wid_462(params)


def hdl_wid_473(params: WIDParams):
    """
    Please update Index: 1 with new name in random 40 characters
    """

    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    # Extract index and new name
    match = re.search(r'Index: (\d+) with new name in random (\d+) characters', params.description)
    if not match:
        return False

    preset_index = int(match.group(1))
    num_characters = int(match.group(2))
    name = 'r' * num_characters
    btp.hap_write_preset_name(preset_index, name, addr_type, addr)

    return True


def hdl_wid_474(_: WIDParams):
    """
        Please click OK when both lower testers are performed operation (MMI poped up both Lower testers)
    """

    # Synchronized in ptsproject/hap.py

    return True


def hdl_wid_476(_: WIDParams):
    """
        Please send exchange MTU command to the PTS with MTU size greater than 49.
    """

    # BTstack exchanges MTU before any GATT Client requests, so just discover something
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    hap_start_hap_discovery(addr_type, addr)
    return True


def hdl_wid_477(_: WIDParams):
    """
        Please verify that the IUT starts alerting with a High Alert.
    """
    stack = get_stack()

    stack.ias.wait_for_high_alert()

    return stack.ias.alert_lvl == 2


def hdl_wid_478(params: WIDParams):
    """
     Please write preset name to index: 1 with random string.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    preset_index = int(re.search(r'\d+', params.description).group())
    name = "random string"
    btp.hap_write_preset_name(preset_index, name, addr_type, addr)

    return True


def hdl_wid_479(_: WIDParams):
    """
        Please read Set Size Characteristic.
    """
    # Set Size is read during CSIP discovery

    return True


def hdl_wid_480(_: WIDParams):
    """
        Please read Set Member Rank Characteristic.
    """
    # Set Member Rank is read during CSIP discovery

    return True


def hdl_wid_481(params: WIDParams):
    """
        Please read SIRK Characteristic.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    # SIRK is read during CSIP discovery
    stack = get_stack()
    btp.csip_discover(addr_type, addr)
    ev = stack.csip.wait_discovery_completed_ev(addr_type, addr, 30)

    if ev is None:
        return False

    return True


def hdl_wid_482(_: WIDParams):
    """
        Please configure to Streaming state.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    audio_dir = AudioDir.SINK
    coding_format = 0x06
    audio_location_list = [defs.PACS_AUDIO_LOCATION_FRONT_LEFT, defs.PACS_AUDIO_LOCATION_FRONT_RIGHT]
    ase_ids = []

    default_config = create_default_config()
    default_config.codec_set_name = '24_1'
    default_config.qos_set_name = '24_1_1'
    default_config.metadata_ltvs = struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0200)

    (default_config.sampling_freq,
     default_config.frame_duration,
     default_config.octets_per_frame) = CODEC_CONFIG_SETTINGS[default_config.codec_set_name]

    (default_config.sdu_interval,
     default_config.framing,
     default_config.max_sdu_size,
     default_config.retransmission_number,
     default_config.max_transport_latency) = QOS_CONFIG_SETTINGS[default_config.qos_set_name]

    ases = []
    cig_id = 0x00
    cis_id = 0x00

    for audio_location in audio_location_list:
        # Find ID of the ASE
        ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
        if ev is None:
            return False

        _, _, _, ase_id = ev

        logging.debug(f"Using ASE_ID: {ase_id} for Location: {audio_location}")

        # 24_1
        config = Namespace(**vars(default_config))
        config.audio_dir = audio_dir
        audio_locations = audio_location

        # Perform Codec Config operation
        config.ase_id = ase_id
        config.cig_id = cig_id
        config.cis_id = cis_id
        config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq, config.frame_duration,
                                                 audio_locations, config.octets_per_frame,
                                                 config.frames_per_sdu)

        btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
        stack.bap.ase_configs.append(config)

        ases.append(config)

        cis_id += 1

    btp.cap_unicast_audio_start(cig_id, defs.CAP_UNICAST_AUDIO_START_SET_TYPE_AD_HOC)
    ev = stack.cap.wait_unicast_start_completed_ev(cig_id, 10)
    if ev is None:
        return False

    # We could wait for this, but Zephyr controller has issue with the second CIS,
    # so PTS does not send Streaming notification.
    for config in ases:
        # Wait for the ASE states to be changed to streaming
        ev = stack.ascs.wait_ascs_ase_state_changed_ev(config.addr_type,
                                                       config.addr,
                                                       config.ase_id,
                                                       ASCSState.STREAMING,
                                                       20)
        if ev is None:
            log('hdl_wid_482 exit, not streaming')
            return False

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
        broadcast_id, sid, addr_type, addr = ev['broadcast_id'], ev['advertiser_sid'], ev['addr_type'], ev['addr']
        btp.bap_broadcast_sink_sync(broadcast_id, sid, 5, 600, False, 0, addr_type, addr)
        ev = stack.bap.wait_bis_found_ev(broadcast_id, 50)

    return ev is not None


def hdl_wid_490(_: WIDParams):
    """
    Please click OK after IUT discovered and configured.
    """
    # no idea what this means, but we can click OK for sure
    return True


def hdl_wid_491(_: WIDParams):
    """
    Please update Index: 2 with new name in LT2. Do not expect IUT to send command to LT2.
    """
    addr = lt2_addr_get()
    addr_type = lt2_addr_type_get()

    # as we're not supposed to actually send this, the values don't matter
    btp.hap_write_preset_name(2, "New Name", addr_type, addr)

    return True


def hdl_wid_493(_: WIDParams):
    """
    Please click OK when IUT is ready to receive Preset Changed message
    """
    return True


def hdl_wid_20001(_: WIDParams):
    """
        Please prepare IUT into a connectable mode.
        Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20100(params: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    btp.gap_conn(addr, addr_type)
    stack.gap.wait_for_connection(timeout=10, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30, addr=addr)

    return True


def hdl_wid_20103(params: WIDParams):
    """
        Please take action to discover the X Control Point characteristic from the Y.
        Discover the primary service if needed.
        Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    # Pick Service to discover by description text
    if 'Alert Level' in params.description:
        btp.hap_iac_discover(addr_type, addr)
        stack.hap.wait_iac_discovery_complete_ev(addr_type, addr, 30)
    else:
        hap_start_hap_discovery(addr_type, addr)
    return True


def hdl_wid_20105(params: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor of Hearing Aid Preset
        Control Point characteristic to enable indication.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    hap_start_hap_discovery(addr_type, addr)
    return True


def hdl_wid_20106(params: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor of ASE
        Control Point characteristic to enable notification.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    peer = stack.bap.get_peer(addr_type, addr)
    if peer.discovery_completed:
        log('Skip BAP discovery, discovery completed before')

        # Skip if discovery has been done already
        return True

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    return True


def hdl_wid_20107(params: WIDParams):
    """
       Please send Read Request to read X characteristic with handle = Y.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()
    stack = get_stack()

    MMI.reset()
    MMI.parse_description(params.description)

    value_handle = MMI.args[0]

    if not value_handle:
        logging.debug("parsing error")
        return False

    # Read Characteristic Value and wait for response
    btp.gattc_read(addr_type, addr, value_handle)
    btp.gattc_read_rsp()

    return True


def hdl_wid_20116(_: WIDParams):
    """
        Please send command to the PTS to discover all mandatory characteristics of the
        Hearing Access supported by the IUT. Discover primary service if needed.
    """
    addr = pts_addr_get()
    addr_type = pts_addr_type_get()

    hap_start_hap_discovery(addr_type, addr)
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


def hdl_wid_20137(params: WIDParams):
    """
        Please initiate an L2CAP Credit Based Connection to the PTS.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    btp.gatt.eatt_conn(addr, addr_type, 5)
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
