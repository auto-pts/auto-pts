#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
from autopts.pybtp import btp
from autopts.pybtp.types import (
    FRAME_DURATION_STR_TO_CODE,
    QOS_CONFIG_SETTINGS,
    SAMPLING_FREQ_STR_TO_CODE,
    AudioDir,
    WIDParams,
    create_lc3_ltvs_bytes,
)
from autopts.wid import generic_wid_hdl
from autopts.wid.bap import create_default_config

log = logging.debug


def bap_wid_hdl(wid, description, test_case_name):
    log(f'{bap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.bap'])


def hdl_wid_302(params: WIDParams):
    """
    Please configure ASE state to CODEC configured with SINK/SOURCE ASE,
    Freq: X KHz, Frame Duration: X ms
    """

    numbers = re.findall(r'\d+(?:\.\d+)?', params.description)
    sampling_freq = numbers[0]
    frame_duration = numbers[1]

    if 'SINK' in params.description:
        audio_dir = AudioDir.SINK
    else:
        audio_dir = AudioDir.SOURCE

    addr = btp.pts_addr_get()
    addr_type = btp.pts_addr_type_get()
    stack = get_stack()

    # Get supported capabilities
    ev = stack.bap.wait_codec_cap_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, coding_format, frequencies, frame_durations, frame_lens, channel_counts = ev

    # Find ID of the ASE
    ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30)
    if ev is None:
        return False

    _, _, _, ase_id = ev

    sampling_freq = SAMPLING_FREQ_STR_TO_CODE[sampling_freq]
    frame_duration = FRAME_DURATION_STR_TO_CODE[frame_duration]
    octets_per_frame = frame_lens & 0xffff
    audio_locations = 0x01
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x0000, 0x0000, codec_ltvs_bytes)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    # Codec and QoS configuration are triggered automatically by BlueZ as soon as a
    # local audio endpoint can be used, i.e. before PTS has requested the WID 302.
    # To prevent this BlueZ's btpclient only registers the audio endpoint after receiving
    # the QoS configuration.
    # As this WID is meant to verify that the IUT can be configured with the requested Codec
    # only this calls the QoS configuration with fake parameters to trigger the endpoint
    # registration after the Codec configuration has been stored.
    qos_config = QOS_CONFIG_SETTINGS['8_1_1']
    btp.ascs_config_qos(ase_id, 0, 0, *qos_config, 0)
    stack.ascs.wait_ascs_operation_complete_ev(addr_type, addr, ase_id, 30)

    config = create_default_config()
    config.addr = addr
    config.addr_type = addr_type
    config.ase_id = ase_id
    config.audio_dir = audio_dir
    stack.bap.ase_configs.clear()
    stack.bap.ase_configs.append(config)

    return True
