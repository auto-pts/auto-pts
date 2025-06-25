#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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
from autopts.pybtp.types import WIDParams
from autopts.wid.bap import create_lc3_ltvs_bytes

log = logging.debug


def hdl_wid_200(_: WIDParams):
    btp.ascs_release(1)
    return True


def hdl_wid_201(params: WIDParams):
    """
    Please configure the CODEC parameters on ASE ID %d
    in Audio Stream Endpoint Characteristic.
    """

    ase_id = int(re.findall(r'\d', params.description)[0])
    coding_format = 0x06
    sampling_freq = 0x06
    frame_duration = 0x01
    audio_locations = 0x01
    octets_per_frame = 0x0028
    frames_per_sdu = 0x01

    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)
    btp.ascs_config_codec(ase_id, coding_format, 0x00, 0x00, codec_ltvs_bytes)

    return True


def hdl_wid_204(params: WIDParams):
    """
    Please initiate DISABLE operation on ASE ID %d
    in Audio Stream Endpoint Characteristic.
    """
    ase_id = int(re.findall(r'\d', params.description)[0])
    btp.ascs_disable(ase_id)
    return True


def hdl_wid_206(params: WIDParams):
    """
    Please initiate RELEASE operation on ASE ID %d
    in Audio Stream Endpoint Characteristic.
    """
    ase_id = int(re.findall(r'\d', params.description)[0])
    btp.ascs_release(ase_id)
    return True


def hdl_wid_208(_: WIDParams):
    return True


def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True
