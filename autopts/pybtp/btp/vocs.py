#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup.
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

"""Wrapper around btp messages. The functions are added as needed."""

import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

VOCS = {
    "audio_desc":(defs.BTP_SERVICE_ID_VOCS, defs.VOCS_AUDIO_OUT_DESC_UPDATE,
               CONTROLLER_INDEX, ""),
    "audio_loc":(defs.BTP_SERVICE_ID_VOCS, defs.VOCS_UPDATE_AUDIO_LOC,
               CONTROLLER_INDEX, ""),
}

def vocs_audio_desc():
    logging.debug("%s", vocs_audio_desc.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VOCS['audio_desc'])

def vocs_audio_loc():
    logging.debug("%s", vocs_audio_desc.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VOCS['audio_loc'])


