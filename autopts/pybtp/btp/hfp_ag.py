#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP.
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

"""Wrapper around btp messages for HFP AG. The functions are added as needed."""

import binascii
import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import addr2btp_ba

HFP_AG = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_READ_SUPPORTED_COMMANDS, defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_CONNECT, CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_DISCONNECT, CONTROLLER_INDEX),
    "remote_incoming": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REMOTE_INCOMING, CONTROLLER_INDEX),
    "outgoing": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_OUTGOING, CONTROLLER_INDEX),
    "remote_ringing": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REMOTE_RINGING, CONTROLLER_INDEX),
    "remote_accept": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REMOTE_ACCEPT, CONTROLLER_INDEX),
    "remote_reject": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REMOTE_REJECT, CONTROLLER_INDEX),
    "remote_terminate": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REMOTE_TERMINATE, CONTROLLER_INDEX),
    "accept_call": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_ACCEPT_CALL, CONTROLLER_INDEX),
    "reject_call": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_REJECT_CALL, CONTROLLER_INDEX),
    "terminate_call": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_TERMINATE_CALL, CONTROLLER_INDEX),
    "hold_call": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_HOLD_CALL, CONTROLLER_INDEX),
    "retrieve_call": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_RETRIEVE_CALL, CONTROLLER_INDEX),
    "hold_incoming": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_HOLD_INCOMING, CONTROLLER_INDEX),
    "explicit_call_transfer": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_EXPLICIT_CALL_TRANSFER, CONTROLLER_INDEX),
    "audio_connect": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_AUDIO_CONNECT, CONTROLLER_INDEX),
    "audio_disconnect": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_AUDIO_DISCONNECT, CONTROLLER_INDEX),
    "set_vgm": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_VGM, CONTROLLER_INDEX),
    "set_vgs": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_VGS, CONTROLLER_INDEX),
    "set_operator": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_OPERATOR, CONTROLLER_INDEX),
    "set_inband_ringtone": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_INBAND_RINGTONE, CONTROLLER_INDEX),
    "voice_recognition": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_VOICE_RECOGNITION, CONTROLLER_INDEX),
    "vre_state": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_VRE_STATE, CONTROLLER_INDEX),
    "vre_text": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_VRE_TEXT, CONTROLLER_INDEX),
    "set_signal_strength": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_SIGNAL_STRENGTH, CONTROLLER_INDEX),
    "set_roaming_status": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_ROAMING_STATUS, CONTROLLER_INDEX),
    "set_battery_level": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_BATTERY_LEVEL, CONTROLLER_INDEX),
    "set_service_availability": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_SERVICE_AVAILABILITY, CONTROLLER_INDEX),
    "set_hf_indicator": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_HF_INDICATOR, CONTROLLER_INDEX),
    "set_ongoing_calls": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_ONGOING_CALLS, CONTROLLER_INDEX),
    "set_last_number": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_LAST_NUMBER, CONTROLLER_INDEX),
    "set_default_indicator_value": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_DEFAULT_INDICATOR_VALUE,
                                    CONTROLLER_INDEX),
    "set_memory_dial_mapping": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_MEMORY_DIAL_MAPPING, CONTROLLER_INDEX),
    "set_subscriber_number": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_SUBSCRIBER_NUMBER, CONTROLLER_INDEX),
    "set_voice_tag_number": (defs.BTP_SERVICE_ID_HFP_AG, defs.BTP_HFP_AG_CMD_SET_VOICE_TAG_NUMBER, CONTROLLER_INDEX),
}


def hfp_ag_command_rsp_succ(op=None):
    logging.debug("%s", hfp_ag_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_HFP_AG, op)


def hfp_ag_connect(channel=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_connect.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", channel))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["connect"], data=data_ba)


def hfp_ag_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_ag_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["disconnect"], data=data_ba)


def hfp_ag_remote_incoming(number, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_remote_incoming.__name__, bd_addr, bd_addr_type, number)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", len(number)))
    data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["remote_incoming"], data=data_ba)


def hfp_ag_outgoing(number, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_outgoing.__name__, bd_addr, bd_addr_type, number)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", len(number)))
    data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["outgoing"], data=data_ba)


def hfp_ag_remote_ringing(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_remote_ringing.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["remote_ringing"], data=data_ba)


def hfp_ag_remote_accept(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_remote_accept.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["remote_accept"], data=data_ba)


def hfp_ag_remote_reject(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_remote_reject.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["remote_reject"], data=data_ba)


def hfp_ag_remote_terminate(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_remote_terminate.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["remote_terminate"], data=data_ba)


def hfp_ag_accept_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_accept_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["accept_call"], data=data_ba)


def hfp_ag_reject_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_reject_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["reject_call"], data=data_ba)


def hfp_ag_terminate_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_terminate_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["terminate_call"], data=data_ba)


def hfp_ag_hold_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_hold_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["hold_call"], data=data_ba)


def hfp_ag_retrieve_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_retrieve_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["retrieve_call"], data=data_ba)


def hfp_ag_hold_incoming(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_hold_incoming.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["hold_incoming"], data=data_ba)


def hfp_ag_explicit_call_transfer(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_ag_explicit_call_transfer.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["explicit_call_transfer"], data=data_ba)


def hfp_ag_audio_connect(codec_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_audio_connect.__name__, bd_addr, bd_addr_type, codec_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", codec_id))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["audio_connect"], data=data_ba)


def hfp_ag_audio_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_ag_audio_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["audio_disconnect"], data=data_ba)


def hfp_ag_set_vgm(gain, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_vgm.__name__, bd_addr, bd_addr_type, gain)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", gain))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_vgm"], data=data_ba)


def hfp_ag_set_vgs(gain, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_vgs.__name__, bd_addr, bd_addr_type, gain)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", gain))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_vgs"], data=data_ba)


def hfp_ag_set_operator(mode, name, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", hfp_ag_set_operator.__name__, bd_addr, bd_addr_type, mode, name)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", mode))
    data_ba.extend(struct.pack("B", len(name)))
    data_ba.extend(name.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_operator"], data=data_ba)


def hfp_ag_set_inband_ringtone(enable, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_inband_ringtone.__name__, bd_addr, bd_addr_type, enable)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", enable))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_inband_ringtone"], data=data_ba)


def hfp_ag_voice_recognition(activate, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_voice_recognition.__name__, bd_addr, bd_addr_type, activate)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", activate))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["voice_recognition"], data=data_ba)


def hfp_ag_vre_state(state, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_vre_state.__name__, bd_addr, bd_addr_type, state)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", state))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["vre_state"], data=data_ba)


def hfp_ag_vre_text(state, text_id, text_type, text_operation, text, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug(
        "%s %r %r %r %r %r %r %r",
        hfp_ag_vre_text.__name__,
        bd_addr,
        bd_addr_type,
        state,
        text_id,
        text_type,
        text_operation,
        text,
    )

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", state))
    data_ba.extend(struct.pack("H", text_id))
    data_ba.extend(struct.pack("B", text_type))
    data_ba.extend(struct.pack("B", text_operation))
    data_ba.extend(struct.pack("B", len(text)))
    data_ba.extend(text.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["vre_text"], data=data_ba)


def hfp_ag_set_signal_strength(strength, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_signal_strength.__name__, bd_addr, bd_addr_type, strength)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", strength))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_signal_strength"], data=data_ba)


def hfp_ag_set_roaming_status(status, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_roaming_status.__name__, bd_addr, bd_addr_type, status)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", status))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_roaming_status"], data=data_ba)


def hfp_ag_set_battery_level(level, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_battery_level.__name__, bd_addr, bd_addr_type, level)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", level))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_battery_level"], data=data_ba)


def hfp_ag_set_service_availability(available, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_ag_set_service_availability.__name__, bd_addr, bd_addr_type, available)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", available))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_service_availability"], data=data_ba)


def hfp_ag_set_hf_indicator(indicator, enable, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", hfp_ag_set_hf_indicator.__name__, bd_addr, bd_addr_type, indicator, enable)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", indicator))
    data_ba.extend(struct.pack("B", enable))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_hf_indicator"], data=data_ba)


def hfp_ag_set_ongoing_calls(calls):
    logging.debug("%s %r", hfp_ag_set_ongoing_calls.__name__, calls)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", len(calls)))

    for call in calls:
        number = call.get("number", "")
        call_type = call.get("type", 0)
        direction = call.get("direction", 0)
        status = call.get("status", 0)

        data_ba.extend(struct.pack("B", len(number)))
        data_ba.extend(struct.pack("B", call_type))
        data_ba.extend(struct.pack("B", direction))
        data_ba.extend(struct.pack("B", status))
        data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_ongoing_calls"], data=data_ba)


def hfp_ag_set_last_number(number, number_type):
    logging.debug("%s %r %r", hfp_ag_set_last_number.__name__, number, number_type)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", number_type))
    data_ba.extend(struct.pack("B", len(number)))
    data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_last_number"], data=data_ba)


def hfp_ag_set_default_indicator_value(service, signal, roam, battery):
    logging.debug("%s %r %r %r %r", hfp_ag_set_default_indicator_value.__name__, service, signal, roam, battery)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", service))
    data_ba.extend(struct.pack("B", signal))
    data_ba.extend(struct.pack("B", roam))
    data_ba.extend(struct.pack("B", battery))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_default_indicator_value"], data=data_ba)


def hfp_ag_set_memory_dial_mapping(location, number):
    logging.debug("%s %r %r", hfp_ag_set_memory_dial_mapping.__name__, location, number)

    iutctl = get_iut()

    data_ba = bytearray()
    if location is None or location == "":
        return

    len_location = len(location)

    if number is None or number == "":
        len_number = 0
    else:
        len_number = len(number)

    data_ba.extend(struct.pack("B", len_location))
    data_ba.extend(struct.pack("B", len_number))
    if len_location != 0:
        data_ba.extend(location.encode("utf-8"))
    if len_number != 0:
        data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_memory_dial_mapping"], data=data_ba)


def hfp_ag_set_subscriber_number(numbers):
    logging.debug("%s %r", hfp_ag_set_subscriber_number.__name__, numbers)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", len(numbers)))

    for num_info in numbers:
        number = num_info.get("number", "")
        num_type = num_info.get("type", 0)
        service = num_info.get("service", 0)

        data_ba.extend(struct.pack("B", num_type))
        data_ba.extend(struct.pack("B", service))
        data_ba.extend(struct.pack("B", len(number)))
        data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_subscriber_number"], data=data_ba)


def hfp_ag_set_voice_tag_number(number):
    logging.debug("%s %r", hfp_ag_set_voice_tag_number.__name__, number)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", len(number)))
    data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_AG["set_voice_tag_number"], data=data_ba)


# Event handlers
def hfp_ag_connected_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_connected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG connected to addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.add_connection(bd_addr)


def hfp_ag_disconnected_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_disconnected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG disconnected from addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.remove_connection(bd_addr)


def hfp_ag_sco_connected_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_sco_connected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG SCO connected to addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.sco_connected(bd_addr)


def hfp_ag_sco_disconnected_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_sco_disconnected_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, reason = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG SCO disconnected from addr %r, reason %r", bd_addr, reason)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.sco_disconnected(bd_addr)


def hfp_ag_outgoing_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_outgoing_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, call_index, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug("HFP AG outgoing call from addr %r, call_index %r, number %r", bd_addr, call_index, number)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.add_call(bd_addr, call_index, defs.BTP_HFP_AG_CALL_DIR_OUTGOING, number)


def hfp_ag_incoming_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_incoming_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, call_index, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug("HFP AG incoming call from addr %r, call_index %r, number %r", bd_addr, call_index, number)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.add_call(bd_addr, call_index, defs.BTP_HFP_AG_CALL_DIR_INCOMING, number)


def hfp_ag_incoming_held_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_incoming_held_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG incoming call held from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD)


def hfp_ag_ringing_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_ringing_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, call_index, in_band = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG ringing from addr %r, call_index %r, in_band %r", bd_addr, call_index, in_band)

    stack = get_stack()
    if stack.hfp_ag.get_call(bd_addr, call_index) is None:
        return

    direction = stack.hfp_ag.get_call_dir(bd_addr, call_index)
    if direction == defs.BTP_HFP_AG_CALL_DIR_INCOMING:
        state = defs.BTP_HFP_AG_CALL_STATUS_WAITING
    elif direction == defs.BTP_HFP_AG_CALL_DIR_OUTGOING:
        state = defs.BTP_HFP_AG_CALL_STATUS_ALERTING
    else:
        return
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    stack.hfp_ag.update_call_state(bd_addr, call_index, state)


def hfp_ag_call_accepted_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_call_accepted_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG call accepted from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)


def hfp_ag_call_held_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_call_held_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG call held from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_HELD)


def hfp_ag_call_retrieved_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_call_retrieved_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG call retrieved from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)


def hfp_ag_call_rejected_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_call_rejected_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG call rejected from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.remove_call(bd_addr, call_index)


def hfp_ag_call_terminated_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_call_terminated_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG call terminated from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.remove_call(bd_addr, call_index)


def hfp_ag_codec_ids_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_codec_ids_ev.__name__, data, data_len)

    hdr_fmt = "<B6sI"
    _, bd_addr, codec_ids = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG codec IDs from addr %r, codec_ids 0x%x", bd_addr, codec_ids)


def hfp_ag_codec_negotiated_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_codec_negotiated_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBb"
    _, bd_addr, codec_id, result = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG codec negotiated from addr %r, codec_id %r, result %r", bd_addr, codec_id, result)


def hfp_ag_audio_connect_req_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_audio_connect_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG audio connect request from addr %r", bd_addr)


def hfp_ag_vgm_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_vgm_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, gain = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG VGM from addr %r, gain %r", bd_addr, gain)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.set_vgm(bd_addr, gain)


def hfp_ag_vgs_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_vgs_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, gain = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG VGS from addr %r, gain %r", bd_addr, gain)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.set_vgs(bd_addr, gain)


def hfp_ag_ecnr_turn_off_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_ecnr_turn_off_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG ECNR turn off from addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.set_ecnr(bd_addr, False)


def hfp_ag_explicit_call_transfer_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_explicit_call_transfer_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG explicit call transfer from addr %r", bd_addr)


def hfp_ag_voice_recognition_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_voice_recognition_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, activate = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG voice recognition from addr %r, activate %r", bd_addr, activate)


def hfp_ag_ready_accept_audio_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_ready_accept_audio_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG ready to accept audio from addr %r", bd_addr)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_ag.set_ready_accept_audio(bd_addr, True)


def hfp_ag_transmit_dtmf_code_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_transmit_dtmf_code_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, code = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG transmit DTMF code from addr %r, code %r", bd_addr, chr(code))


def hfp_ag_hf_indicator_value_ev(hfp_ag, data, data_len):
    logging.debug("%s %r %r", hfp_ag_hf_indicator_value_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBI"
    _, bd_addr, indicator, value = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP AG HF indicator value from addr %r, indicator %r, value %r", bd_addr, indicator, value)


HFP_AG_EV = {
    defs.BTP_HFP_AG_EV_CONNECTED: hfp_ag_connected_ev,
    defs.BTP_HFP_AG_EV_DISCONNECTED: hfp_ag_disconnected_ev,
    defs.BTP_HFP_AG_EV_SCO_CONNECTED: hfp_ag_sco_connected_ev,
    defs.BTP_HFP_AG_EV_SCO_DISCONNECTED: hfp_ag_sco_disconnected_ev,
    defs.BTP_HFP_AG_EV_OUTGOING: hfp_ag_outgoing_ev,
    defs.BTP_HFP_AG_EV_INCOMING: hfp_ag_incoming_ev,
    defs.BTP_HFP_AG_EV_INCOMING_HELD: hfp_ag_incoming_held_ev,
    defs.BTP_HFP_AG_EV_RINGING: hfp_ag_ringing_ev,
    defs.BTP_HFP_AG_EV_CALL_ACCEPTED: hfp_ag_call_accepted_ev,
    defs.BTP_HFP_AG_EV_CALL_HELD: hfp_ag_call_held_ev,
    defs.BTP_HFP_AG_EV_CALL_RETRIEVED: hfp_ag_call_retrieved_ev,
    defs.BTP_HFP_AG_EV_CALL_REJECTED: hfp_ag_call_rejected_ev,
    defs.BTP_HFP_AG_EV_CALL_TERMINATED: hfp_ag_call_terminated_ev,
    defs.BTP_HFP_AG_EV_CODEC_IDS: hfp_ag_codec_ids_ev,
    defs.BTP_HFP_AG_EV_CODEC_NEGOTIATED: hfp_ag_codec_negotiated_ev,
    defs.BTP_HFP_AG_EV_AUDIO_CONNECT_REQ: hfp_ag_audio_connect_req_ev,
    defs.BTP_HFP_AG_EV_VGM: hfp_ag_vgm_ev,
    defs.BTP_HFP_AG_EV_VGS: hfp_ag_vgs_ev,
    defs.BTP_HFP_AG_EV_ECNR_TURN_OFF: hfp_ag_ecnr_turn_off_ev,
    defs.BTP_HFP_AG_EV_EXPLICIT_CALL_TRANSFER: hfp_ag_explicit_call_transfer_ev,
    defs.BTP_HFP_AG_EV_VOICE_RECOGNITION: hfp_ag_voice_recognition_ev,
    defs.BTP_HFP_AG_EV_READY_ACCEPT_AUDIO: hfp_ag_ready_accept_audio_ev,
    defs.BTP_HFP_AG_EV_TRANSMIT_DTMF_CODE: hfp_ag_transmit_dtmf_code_ev,
    defs.BTP_HFP_AG_EV_HF_INDICATOR_VALUE: hfp_ag_hf_indicator_value_ev,
}
