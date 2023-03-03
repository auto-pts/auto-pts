import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, get_iut_method as get_iut

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
               CONTROLLER_INDEX),
    "mute_disable":(defs.BTP_SERVICE_ID_AICS, defs.AICS_MUTE_DISABLE,
               CONTROLLER_INDEX, ""),
}

AICS_EV = {
    ### For future testing purposes ###
}

def aics_command_rsp_succ(op=None):
    logging.debug("%s", aics_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_AICS, op)

    return tuple_data

def aics_mute():
    logging.debug("%s", aics_mute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute'])
    aics_command_rsp_succ()

def aics_unmute():
    logging.debug("%s", aics_unmute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['unmute'])
    aics_command_rsp_succ()

def aics_auto_gain():
    logging.debug("%s", aics_auto_gain.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain'])
    aics_command_rsp_succ()

def aics_man_gain():
    logging.debug("%s", aics_man_gain.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain'])
    aics_command_rsp_succ()

def aics_man_gain_only():
    logging.debug("%s", aics_man_gain_only.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain_only'])
    aics_command_rsp_succ()

def aics_auto_gain_only():
    logging.debug("%s", aics_auto_gain_only.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain_only'])
    aics_command_rsp_succ()

def aics_change_desc(string):
    logging.debug("%s", aics_change_desc.__name__)

    iutctl = get_iut()
    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

    iutctl.btp_socket.send(*AICS['desc'], data = data)
    aics_command_rsp_succ()

def aics_set_gain(gain):
    logging.debug("%s %r", aics_set_gain.__name__, gain)

    iutctl = get_iut()

    if isinstance(gain, str):
        gain = int(gain)

    data = bytearray(struct.pack("<b", gain))

    iutctl.btp_socket.send(*AICS['set_gain'], data=data)
    aics_command_rsp_succ()

def aics_mute_disable():
    logging.debug("%s", aics_mute.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute_disable'])
    aics_command_rsp_succ()
