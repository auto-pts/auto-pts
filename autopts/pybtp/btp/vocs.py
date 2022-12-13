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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, get_iut_method as get_iut

VOCS = {
    "audio_desc":(defs.BTP_SERVICE_ID_VOCS, defs.VOCS_UPDATE_OUT_DESC,
               CONTROLLER_INDEX),
    "audio_loc":(defs.BTP_SERVICE_ID_VOCS, defs.VOCS_UPDATE_AUDIO_LOC,
               CONTROLLER_INDEX, ""),
}

VOCS_EV = {
    ### For future testing purposes ###
}

def vocs_command_rsp_succ(op=None):
    logging.debug("%s", vocs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_VOCS, op)

    return tuple_data

def vocs_audio_desc(string):
    logging.debug("%s", vocs_audio_desc.__name__)

    iutctl = get_iut()
    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

    iutctl.btp_socket.send(*VOCS['audio_desc'], data = data)
    vocs_command_rsp_succ()

def vocs_audio_loc(location):
    logging.debug("%s", vocs_audio_desc.__name__)

    iutctl = get_iut()

    data = bytearray(struct.pack("I", location))

    iutctl.btp_socket.send(*VOCS['audio_loc'], data = data)
    vocs_command_rsp_succ()
