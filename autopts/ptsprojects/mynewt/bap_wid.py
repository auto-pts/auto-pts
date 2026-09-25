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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams, create_lc3_ltvs_bytes

log = logging.debug


def hdl_wid_380(_: WIDParams):
    """
    Please reconfigure BASE with different settings. Then click OK when
    IUT is ready to advertise with Broadcast Audio Announcement (0x1852)
    service data.
    """
    stack = get_stack()
    broadcast_id = stack.bap.broadcast_id
    btp.bap_broadcast_adv_stop(broadcast_id)
    btp.bap_broadcast_source_stop(broadcast_id)
    btp.bap_broadcast_source_release(broadcast_id)

    coding_format = 0x06
    vid = 0x0000
    cid = 0x0000
    qos_set_name = '16_1_1'  # noqa: F841 # qos_set_name is not used

    codec_set_name, *qos_config = ('16_1', 7500, 0x00, 30, 2, 8)  # noqa: F841 # codec_set_name is not used
    audio_locations = 0x01
    frames_per_sdu = 0x01

    (sampling_freq, frame_duration, octets_per_frame) = (0x03, 0x00, 30)
    codec_ltvs_bytes = create_lc3_ltvs_bytes(sampling_freq, frame_duration,
                                             audio_locations, octets_per_frame,
                                             frames_per_sdu)

    presentation_delay = 40000
    streams_per_subgroup = 2
    subgroups = 1
    broadcast_id = btp.bap_broadcast_source_setup(
        streams_per_subgroup, subgroups, coding_format, vid, cid,
        codec_ltvs_bytes, *qos_config, presentation_delay)

    stack.bap.broadcast_id = broadcast_id

    btp.bap_broadcast_adv_start(broadcast_id)
    btp.bap_broadcast_source_start(broadcast_id)

    return True
