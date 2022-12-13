import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

AICS = {
    "set_gain":(defs.BTP_SERVICE_ID_AICS, defs.AICS_SET_GAIN,
               CONTROLLER_INDEX),
    "mute":(defs.BTP_SERVICE_ID_AICS, defs.AICS_MUTE,
               CONTROLLER_INDEX, ""),
    "unmute":(defs.BTP_SERVICE_ID_AICS, defs.AICS_UNMUTE,
               CONTROLLER_INDEX, ""),
    "auto_gain":(defs.BTP_SERVICE_ID_AICS, defs.AICS_AUTO_GAIN,
               CONTROLLER_INDEX, ""),
    "man_gain":(defs.BTP_SERVICE_ID_AICS, defs.AICS_MAN_GAIN,
               CONTROLLER_INDEX, ""),
    "man_gain_only":(defs.BTP_SERVICE_ID_AICS, defs.AICS_MAN_GAIN_ONLY,
               CONTROLLER_INDEX, ""),
    "auto_gain_only":(defs.BTP_SERVICE_ID_AICS, defs.AICS_AUTO_GAIN_ONLY,
               CONTROLLER_INDEX, ""),
    "desc":(defs.BTP_SERVICE_ID_AICS, defs.AICS_DESC,
               CONTROLLER_INDEX, ""),
}

def aics_mute():
    logging.debug("%s", aics_mute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute'])

def aics_unmute():
    logging.debug("%s", aics_unmute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['unmute'])

def aics_auto_gain():
    logging.debug("%s", aics_auto_gain.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain'])

def aics_man_gain():
    logging.debug("%s", aics_man_gain.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain'])

def aics_man_gain_only():
    logging.debug("%s", aics_man_gain_only.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain_only'])

def aics_auto_gain_only():
    logging.debug("%s", aics_auto_gain_only.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain_only'])

def aics_change_desc():
    logging.debug("%s", aics_change_desc.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['desc'])
