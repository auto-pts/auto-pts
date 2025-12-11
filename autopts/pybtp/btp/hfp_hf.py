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

"""Wrapper around btp messages for HFP HF. The functions are added as needed."""

import binascii
import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import addr2btp_ba

HFP_HF = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_READ_SUPPORTED_COMMANDS, defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_CONNECT, CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_DISCONNECT, CONTROLLER_INDEX),
    "cli": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_CLI, CONTROLLER_INDEX),
    "vgm": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_VGM, CONTROLLER_INDEX),
    "vgs": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_VGS, CONTROLLER_INDEX),
    "get_operator": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_GET_OPERATOR, CONTROLLER_INDEX),
    "accept_call": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_ACCEPT_CALL, CONTROLLER_INDEX),
    "reject_call": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_REJECT_CALL, CONTROLLER_INDEX),
    "terminate_call": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_TERMINATE_CALL, CONTROLLER_INDEX),
    "hold_incoming": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_HOLD_INCOMING, CONTROLLER_INDEX),
    "query_respond_hold_status": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_QUERY_RESPOND_HOLD_STATUS, CONTROLLER_INDEX),
    "number_call": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_NUMBER_CALL, CONTROLLER_INDEX),
    "memory_dial": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_MEMORY_DIAL, CONTROLLER_INDEX),
    "redial": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_REDIAL, CONTROLLER_INDEX),
    "audio_connect": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_AUDIO_CONNECT, CONTROLLER_INDEX),
    "audio_disconnect": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_AUDIO_DISCONNECT, CONTROLLER_INDEX),
    "select_codec": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_SELECT_CODEC, CONTROLLER_INDEX),
    "set_codecs": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_SET_CODECS, CONTROLLER_INDEX),
    "turn_off_ecnr": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_TURN_OFF_ECNR, CONTROLLER_INDEX),
    "call_waiting_notify": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_CALL_WAITING_NOTIFY, CONTROLLER_INDEX),
    "release_all_held": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_RELEASE_ALL_HELD, CONTROLLER_INDEX),
    "set_udub": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_SET_UDUB, CONTROLLER_INDEX),
    "release_active_accept_other": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_RELEASE_ACTIVE_ACCEPT_OTHER,
                                    CONTROLLER_INDEX),
    "hold_active_accept_other": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_HOLD_ACTIVE_ACCEPT_OTHER, CONTROLLER_INDEX),
    "join_conversation": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_JOIN_CONVERSATION, CONTROLLER_INDEX),
    "explicit_call_transfer": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_EXPLICIT_CALL_TRANSFER, CONTROLLER_INDEX),
    "release_specified_call": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_RELEASE_SPECIFIED_CALL, CONTROLLER_INDEX),
    "private_consultation_mode": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_PRIVATE_CONSULTATION_MODE, CONTROLLER_INDEX),
    "voice_recognition": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_VOICE_RECOGNITION, CONTROLLER_INDEX),
    "ready_to_accept_audio": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_READY_TO_ACCEPT_AUDIO, CONTROLLER_INDEX),
    "request_phone_number": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_REQUEST_PHONE_NUMBER, CONTROLLER_INDEX),
    "transmit_dtmf_code": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_TRANSMIT_DTMF_CODE, CONTROLLER_INDEX),
    "query_subscriber": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_QUERY_SUBSCRIBER, CONTROLLER_INDEX),
    "indicator_status": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_INDICATOR_STATUS, CONTROLLER_INDEX),
    "enhanced_safety": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_ENHANCED_SAFETY, CONTROLLER_INDEX),
    "battery": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_BATTERY, CONTROLLER_INDEX),
    "query_list_current_calls": (defs.BTP_SERVICE_ID_HFP_HF, defs.BTP_HFP_HF_CMD_QUERY_LIST_CURRENT_CALLS, CONTROLLER_INDEX),
}


def hfp_hf_command_rsp_succ(op=None):
    logging.debug("%s", hfp_hf_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_HFP_HF, op)


def hfp_hf_connect(channel=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_connect.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", channel))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["connect"], data=data_ba)


def hfp_hf_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["disconnect"], data=data_ba)


def hfp_hf_cli(enable, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_cli.__name__, bd_addr, bd_addr_type, enable)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", enable))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["cli"], data=data_ba)


def hfp_hf_vgm(gain, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_vgm.__name__, bd_addr, bd_addr_type, gain)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", gain))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["vgm"], data=data_ba)


def hfp_hf_vgs(gain, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_vgs.__name__, bd_addr, bd_addr_type, gain)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", gain))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["vgs"], data=data_ba)


def hfp_hf_get_operator(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_get_operator.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["get_operator"], data=data_ba)


def hfp_hf_accept_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_accept_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["accept_call"], data=data_ba)


def hfp_hf_reject_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_reject_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["reject_call"], data=data_ba)


def hfp_hf_terminate_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_terminate_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["terminate_call"], data=data_ba)


def hfp_hf_hold_incoming(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_hold_incoming.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["hold_incoming"], data=data_ba)


def hfp_hf_query_respond_hold_status(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_query_respond_hold_status.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["query_respond_hold_status"], data=data_ba)


def hfp_hf_number_call(number, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_number_call.__name__, bd_addr, bd_addr_type, number)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", len(number)))
    data_ba.extend(number.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["number_call"], data=data_ba)


def hfp_hf_memory_dial(location, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_memory_dial.__name__, bd_addr, bd_addr_type, location)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", len(location)))
    data_ba.extend(location.encode("utf-8"))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["memory_dial"], data=data_ba)


def hfp_hf_redial(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_redial.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["redial"], data=data_ba)


def hfp_hf_audio_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_audio_connect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["audio_connect"], data=data_ba)


def hfp_hf_audio_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_audio_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["audio_disconnect"], data=data_ba)


def hfp_hf_select_codec(codec_id, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_select_codec.__name__, bd_addr, bd_addr_type, codec_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", codec_id))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["select_codec"], data=data_ba)


def hfp_hf_set_codecs(codec_ids, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_set_codecs.__name__, bd_addr, bd_addr_type, codec_ids)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", codec_ids))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["set_codecs"], data=data_ba)


def hfp_hf_turn_off_ecnr(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_turn_off_ecnr.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["turn_off_ecnr"], data=data_ba)


def hfp_hf_call_waiting_notify(enable, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_call_waiting_notify.__name__, bd_addr, bd_addr_type, enable)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", enable))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["call_waiting_notify"], data=data_ba)


def hfp_hf_release_all_held(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_release_all_held.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["release_all_held"], data=data_ba)


def hfp_hf_set_udub(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_set_udub.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["set_udub"], data=data_ba)


def hfp_hf_release_active_accept_other(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_release_active_accept_other.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["release_active_accept_other"], data=data_ba)


def hfp_hf_hold_active_accept_other(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_hold_active_accept_other.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["hold_active_accept_other"], data=data_ba)


def hfp_hf_join_conversation(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_join_conversation.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["join_conversation"], data=data_ba)


def hfp_hf_explicit_call_transfer(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_explicit_call_transfer.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["explicit_call_transfer"], data=data_ba)


def hfp_hf_release_specified_call(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_release_specified_call.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["release_specified_call"], data=data_ba)


def hfp_hf_private_consultation_mode(call_index, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_private_consultation_mode.__name__, bd_addr, bd_addr_type, call_index)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["private_consultation_mode"], data=data_ba)


def hfp_hf_voice_recognition(activate, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_voice_recognition.__name__, bd_addr, bd_addr_type, activate)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", activate))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["voice_recognition"], data=data_ba)


def hfp_hf_ready_to_accept_audio(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_ready_to_accept_audio.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["ready_to_accept_audio"], data=data_ba)


def hfp_hf_request_phone_number(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_request_phone_number.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["request_phone_number"], data=data_ba)


def hfp_hf_transmit_dtmf_code(call_index, code, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", hfp_hf_transmit_dtmf_code.__name__, bd_addr, bd_addr_type, call_index, code)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", call_index))
    data_ba.extend(struct.pack("B", ord(code) if isinstance(code, str) else code))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["transmit_dtmf_code"], data=data_ba)


def hfp_hf_query_subscriber(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_query_subscriber.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["query_subscriber"], data=data_ba)


def hfp_hf_indicator_status(status, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_indicator_status.__name__, bd_addr, bd_addr_type, status)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", status))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["indicator_status"], data=data_ba)


def hfp_hf_enhanced_safety(enable, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_enhanced_safety.__name__, bd_addr, bd_addr_type, enable)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", enable))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["enhanced_safety"], data=data_ba)


def hfp_hf_battery(level, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", hfp_hf_battery.__name__, bd_addr, bd_addr_type, level)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", level))

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["battery"], data=data_ba)


def hfp_hf_query_list_current_calls(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", hfp_hf_query_list_current_calls.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*HFP_HF["query_list_current_calls"], data=data_ba)


# Event handlers
def hfp_hf_connected_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_connected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF connected to addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.add_connection(bd_addr)


def hfp_hf_disconnected_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_disconnected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF disconnected from addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.remove_connection(bd_addr)


def hfp_hf_sco_connected_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_sco_connected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF SCO connected to addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.sco_connected(bd_addr)


def hfp_hf_sco_disconnected_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_sco_disconnected_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, reason = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF SCO disconnected from addr %r, reason %r", bd_addr, reason)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.sco_disconnected(bd_addr)


def hfp_hf_service_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_service_ev.__name__, data, data_len)

    hdr_fmt = "<B6sI"
    _, bd_addr, value = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF service from addr %r, value %r", bd_addr, value)


def hfp_hf_outgoing_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_outgoing_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF outgoing call from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.add_call(bd_addr, call_index, defs.BTP_HFP_AG_CALL_DIR_OUTGOING, "UNKNOWN")


def hfp_hf_remote_ringing_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_remote_ringing_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF remote ringing from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ALERTING)


def hfp_hf_incoming_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_incoming_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF incoming call from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.add_call(bd_addr, call_index, defs.BTP_HFP_AG_CALL_DIR_INCOMING, "UNKNOWN")


def hfp_hf_incoming_held_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_incoming_held_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF incoming call held from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_INCOMING_HELD)


def hfp_hf_call_accepted_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_accepted_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF call accepted from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)


def hfp_hf_call_rejected_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_rejected_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF call rejected from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.remove_call(bd_addr, call_index)


def hfp_hf_call_terminated_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_terminated_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF call terminated from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.remove_call(bd_addr, call_index)


def hfp_hf_call_held_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_held_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF call held from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_HELD)


def hfp_hf_call_retrieved_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_retrieved_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF call retrieved from addr %r, call_index %r", bd_addr, call_index)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.update_call_state(bd_addr, call_index, defs.BTP_HFP_AG_CALL_STATUS_ACTIVE)


def hfp_hf_signal_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_signal_ev.__name__, data, data_len)

    hdr_fmt = "<B6sI"
    _, bd_addr, value = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF signal from addr %r, value %r", bd_addr, value)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_signal(bd_addr, value)


def hfp_hf_roam_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_roam_ev.__name__, data, data_len)

    hdr_fmt = "<B6sI"
    _, bd_addr, value = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF roam from addr %r, value %r", bd_addr, value)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_roam(bd_addr, value)


def hfp_hf_battery_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_battery_ev.__name__, data, data_len)

    hdr_fmt = "<B6sI"
    _, bd_addr, value = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF battery from addr %r, value %r", bd_addr, value)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_battery(bd_addr, value)


def hfp_hf_ring_indication_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_ring_indication_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, call_index = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF ring indication from addr %r, call_index %r", bd_addr, call_index)


def hfp_hf_dialing_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_dialing_ev.__name__, data, data_len)

    hdr_fmt = "<B6sb"
    _, bd_addr, result = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF dialing from addr %r, result %r", bd_addr, result)


def hfp_hf_clip_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_clip_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, call_index, number_type, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug("HFP HF CLIP from addr %r, call_index %r, type %r, number %r", bd_addr, call_index, number_type, number)


def hfp_hf_vgm_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_vgm_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, gain = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF VGM from addr %r, gain %r", bd_addr, gain)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_vgm(bd_addr, gain)


def hfp_hf_vgs_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_vgs_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, gain = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF VGS from addr %r, gain %r", bd_addr, gain)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_vgs(bd_addr, gain)


def hfp_hf_inband_ring_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_inband_ring_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, inband = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF inband ring from addr %r, inband %r", bd_addr, inband)


def hfp_hf_operator_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_operator_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, mode, format_type, operator_len = struct.unpack_from(hdr_fmt, data)
    operator_name = struct.unpack_from(f"{operator_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug("HFP HF operator from addr %r, mode %r, format %r, name %r", bd_addr, mode, format_type, operator_name)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_operator(bd_addr, operator_name)


def hfp_hf_codec_negotiate_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_codec_negotiate_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, codec_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF codec negotiate from addr %r, codec_id %r", bd_addr, codec_id)


def hfp_hf_ecnr_turn_off_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_ecnr_turn_off_ev.__name__, data, data_len)

    hdr_fmt = "<B6sb"
    _, bd_addr, result = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF ECNR turn off from addr %r, result %r", bd_addr, result)


def hfp_hf_call_waiting_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_call_waiting_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, call_index, number_type, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug(
        "HFP HF call waiting from addr %r, call_index %r, type %r, number %r", bd_addr, call_index, number_type, number
    )


def hfp_hf_voice_recognition_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_voice_recognition_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, activate = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF voice recognition from addr %r, activate %r", bd_addr, activate)
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.set_voice_recognition(bd_addr, bool(activate))


def hfp_hf_vre_state_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_vre_state_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, state = struct.unpack_from(hdr_fmt, data)

    logging.debug("HFP HF VRE state from addr %r, state %r", bd_addr, state)


def hfp_hf_textual_representation_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_textual_representation_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, text_type, operation, id_len, text_len = struct.unpack_from(hdr_fmt, data)

    # Extract id_string and text_string from data
    id_string = struct.unpack_from(f"{id_len}s", data, hdr_len)[0].decode("utf-8")
    text_string = struct.unpack_from(f"{text_len}s", data, hdr_len + id_len)[0].decode("utf-8")

    logging.debug(
        "HFP HF textual representation from addr %r, type %r, operation %r, id %r, text %r",
        bd_addr,
        text_type,
        operation,
        id_string,
        text_string,
    )


def hfp_hf_request_phone_number_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_request_phone_number_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug("HFP HF request phone number from addr %r, number %r", bd_addr, number)


def hfp_hf_subscriber_number_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_subscriber_number_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, number_type, service, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug(
        "HFP HF subscriber number from addr %r, type %r, service %r, number %r", bd_addr, number_type, service, number
    )
    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().hfp_hf.add_subscriber_number(bd_addr, number)


def hfp_hf_query_call_ev(hfp_hf, data, data_len):
    logging.debug("%s %r %r", hfp_hf_query_call_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBBBBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, index, direction, status, mode, multiparty, number_type, number_len = struct.unpack_from(hdr_fmt, data)
    number = struct.unpack_from(f"{number_len}s", data, hdr_len)[0].decode("utf-8")

    logging.debug(
        "HFP HF query call from addr %r, index %r, dir %r, status %r, mode %r, multiparty %r, type %r, number %r",
        bd_addr,
        index,
        direction,
        status,
        mode,
        multiparty,
        number_type,
        number,
    )


HFP_HF_EV = {
    defs.BTP_HFP_HF_EV_CONNECTED: hfp_hf_connected_ev,
    defs.BTP_HFP_HF_EV_DISCONNECTED: hfp_hf_disconnected_ev,
    defs.BTP_HFP_HF_EV_SCO_CONNECTED: hfp_hf_sco_connected_ev,
    defs.BTP_HFP_HF_EV_SCO_DISCONNECTED: hfp_hf_sco_disconnected_ev,
    defs.BTP_HFP_HF_EV_SERVICE: hfp_hf_service_ev,
    defs.BTP_HFP_HF_EV_OUTGOING: hfp_hf_outgoing_ev,
    defs.BTP_HFP_HF_EV_REMOTE_RINGING: hfp_hf_remote_ringing_ev,
    defs.BTP_HFP_HF_EV_INCOMING: hfp_hf_incoming_ev,
    defs.BTP_HFP_HF_EV_INCOMING_HELD: hfp_hf_incoming_held_ev,
    defs.BTP_HFP_HF_EV_CALL_ACCEPTED: hfp_hf_call_accepted_ev,
    defs.BTP_HFP_HF_EV_CALL_REJECTED: hfp_hf_call_rejected_ev,
    defs.BTP_HFP_HF_EV_CALL_TERMINATED: hfp_hf_call_terminated_ev,
    defs.BTP_HFP_HF_EV_CALL_HELD: hfp_hf_call_held_ev,
    defs.BTP_HFP_HF_EV_CALL_RETRIEVED: hfp_hf_call_retrieved_ev,
    defs.BTP_HFP_HF_EV_SIGNAL: hfp_hf_signal_ev,
    defs.BTP_HFP_HF_EV_ROAM: hfp_hf_roam_ev,
    defs.BTP_HFP_HF_EV_BATTERY: hfp_hf_battery_ev,
    defs.BTP_HFP_HF_EV_RING_INDICATION: hfp_hf_ring_indication_ev,
    defs.BTP_HFP_HF_EV_DIALING: hfp_hf_dialing_ev,
    defs.BTP_HFP_HF_EV_CLIP: hfp_hf_clip_ev,
    defs.BTP_HFP_HF_EV_VGM: hfp_hf_vgm_ev,
    defs.BTP_HFP_HF_EV_VGS: hfp_hf_vgs_ev,
    defs.BTP_HFP_HF_EV_INBAND_RING: hfp_hf_inband_ring_ev,
    defs.BTP_HFP_HF_EV_OPERATOR: hfp_hf_operator_ev,
    defs.BTP_HFP_HF_EV_CODEC_NEGOTIATE: hfp_hf_codec_negotiate_ev,
    defs.BTP_HFP_HF_EV_ECNR_TURN_OFF: hfp_hf_ecnr_turn_off_ev,
    defs.BTP_HFP_HF_EV_CALL_WAITING: hfp_hf_call_waiting_ev,
    defs.BTP_HFP_HF_EV_VOICE_RECOGNITION: hfp_hf_voice_recognition_ev,
    defs.BTP_HFP_HF_EV_VRE_STATE: hfp_hf_vre_state_ev,
    defs.BTP_HFP_HF_EV_TEXTUAL_REPRESENTATION: hfp_hf_textual_representation_ev,
    defs.BTP_HFP_HF_EV_REQUEST_PHONE_NUMBER: hfp_hf_request_phone_number_ev,
    defs.BTP_HFP_HF_EV_SUBSCRIBER_NUMBER: hfp_hf_subscriber_number_ev,
    defs.BTP_HFP_HF_EV_QUERY_CALL: hfp_hf_query_call_ev,
}
