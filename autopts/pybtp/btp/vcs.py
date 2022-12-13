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

import logging
import struct

from autopts.pybtp import defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

VCS = {
    "set_vol":(defs.BTP_SERVICE_ID_VCS, defs.VCS_SET_VOL,
               CONTROLLER_INDEX),
    "vol_up":(defs.BTP_SERVICE_ID_VCS, defs.VCS_VOL_UP,
               CONTROLLER_INDEX, ""),
    "vol_down":(defs.BTP_SERVICE_ID_VCS, defs.VCS_VOL_DOWN,
               CONTROLLER_INDEX, ""),
    "mute":(defs.BTP_SERVICE_ID_VCS, defs.VCS_MUTE,
               CONTROLLER_INDEX, ""),
    "unmute":(defs.BTP_SERVICE_ID_VCS, defs.VCS_UNMUTE,
               CONTROLLER_INDEX, ""),
    "init":(defs.BTP_SERVICE_ID_VCS, defs.VCS_INIT,
               CONTROLLER_INDEX)
}

def vcs_init():
    logging.debug("%s", vcs_init.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*VCS['init'])

    stack = get_stack()


def vcs_set_vol(vol):
    logging.debug("%s %r", vcs_set_vol.__name__, vol)

    iutctl = get_iut()

    if isinstance(vol, str):
        vol = int(vol)

    data = bytearray(struct.pack("<I", vol))

    iutctl.btp_socket.send_wait_rsp(*VCS['set_vol'], data=data)

def vcs_mute():
    logging.debug("%s", vcs_mute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*VCS['mute'])

def vcs_unmute():
    logging.debug("%s", vcs_unmute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['unmute'])

def vcs_vol_down():
    logging.debug("%s", vcs_vol_down.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['vol_down'])

def vcs_vol_up():
    logging.debug("%s", vcs_vol_up.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['vol_up'])
