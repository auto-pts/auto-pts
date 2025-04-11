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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut

VCS = {
    "set_vol": (defs.BTP_SERVICE_ID_VCS, defs.BTP_VCS_CMD_SET_VOL,
               CONTROLLER_INDEX),
    "vol_up": (defs.BTP_SERVICE_ID_VCS, defs.BTP_VCS_CMD_VOL_UP,
               CONTROLLER_INDEX, ""),
    "vol_down": (defs.BTP_SERVICE_ID_VCS, defs.BTP_VCS_CMD_VOL_DOWN,
               CONTROLLER_INDEX, ""),
    "mute": (defs.BTP_SERVICE_ID_VCS, defs.BTP_VCS_CMD_MUTE,
               CONTROLLER_INDEX, ""),
    "unmute": (defs.BTP_SERVICE_ID_VCS, defs.BTP_VCS_CMD_UNMUTE,
               CONTROLLER_INDEX, "")
}

VCS_EV = {
    # For future testing purposes ###
}


def vcs_command_rsp_succ(op=None):
    logging.debug("%s", vcs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_VCS, op)

    return tuple_data


def vcs_set_vol(vol):
    logging.debug("%s %r", vcs_set_vol.__name__, vol)

    iutctl = get_iut()

    if isinstance(vol, str):
        vol = int(vol)

    data = bytearray(struct.pack("<B", vol))

    iutctl.btp_socket.send(*VCS['set_vol'], data=data)
    vcs_command_rsp_succ()


def vcs_mute():
    logging.debug("%s", vcs_mute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['mute'])
    vcs_command_rsp_succ()


def vcs_unmute():
    logging.debug("%s", vcs_unmute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['unmute'])
    vcs_command_rsp_succ()


def vcs_vol_down():
    logging.debug("%s", vcs_vol_down.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['vol_down'])
    vcs_command_rsp_succ()


def vcs_vol_up():
    logging.debug("%s", vcs_vol_up.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*VCS['vol_up'])
    vcs_command_rsp_succ()
