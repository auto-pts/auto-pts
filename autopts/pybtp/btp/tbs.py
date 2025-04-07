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

"""Wrapper around btp messages. The functions are added as needed."""
import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba


TBS = {
    'read_supported_cmds':   (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_READ_SUPPORTED_COMMANDS,
                              CONTROLLER_INDEX, ""),
    'remote_incoming':       (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_REMOTE_INCOMING,
                              CONTROLLER_INDEX),
    'set_bearer_name':       (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_SET_BEARER_NAME,
                              CONTROLLER_INDEX),
    'set_bearer_technology': (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_SET_BEARER_TECHNOLOGY,
                              CONTROLLER_INDEX),
    'set_uri_scheme_list':   (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_SET_URI_SCHEME_LIST,
                              CONTROLLER_INDEX),
    'set_status_flags':      (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_SET_STATUS_FLAGS,
                              CONTROLLER_INDEX),
    'hold_call':             (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_HOLD_CALL,
                              CONTROLLER_INDEX),
    'remote_hold_call':      (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_REMOTE_HOLD_CALL,
                              CONTROLLER_INDEX),
    'originate_call':        (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_ORIGINATE_CALL,
                              CONTROLLER_INDEX),
    'set_signal_strength':   (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_SIGNAL_STRENGTH,
                              CONTROLLER_INDEX),
    'terminate_call':        (defs.BTP_SERVICE_ID_TBS,
                              defs.BTP_TBS_CMD_TERMINATE_CALL,
                              CONTROLLER_INDEX),
}


def tbs_command_rsp_succ(timeout=20.0):
    logging.debug("%s", tbs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_TBS)
    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def tbs_remote_incoming(index, receiver_uri, caller_uri, friendly_name):
    logging.debug(f"{tbs_remote_incoming.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", index))
    uri_str = receiver_uri + caller_uri + friendly_name
    encoded_uri_str = uri_str.encode("utf-8")
    data.extend(struct.pack("b", len(receiver_uri)))
    data.extend(struct.pack("b", len(caller_uri)))
    data.extend(struct.pack("b", len(friendly_name)))
    data.extend(struct.pack("b", len(encoded_uri_str)))
    fmt = str(len(encoded_uri_str)) + "s"
    data.extend(struct.pack(fmt, encoded_uri_str))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['remote_incoming'], data=data)

    tbs_command_rsp_succ()


def tbs_originate_call(index, uri):
    logging.debug(f"{tbs_originate_call.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", index))
    uri_len = len(uri)
    data.extend(struct.pack('b', uri_len))
    encoded_uri = uri.encode('utf-8')
    fmt = str(uri_len) + 's'
    data.extend(struct.pack(fmt, encoded_uri))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['originate_call'], data=data)

    tbs_command_rsp_succ()


def tbs_set_bearer_name(index, name):
    logging.debug(f"{tbs_set_bearer_name.__name__}")

    data = bytearray()
    data.extend(struct.pack("B", index))
    name_len = len(name)
    data.extend(struct.pack("b", name_len))
    encoded_name = name.encode("utf-8")
    name_fmt = str(name_len) + "s"
    data.extend(struct.pack(name_fmt, encoded_name))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['set_bearer_name'], data=data)

    tbs_command_rsp_succ()


def tbs_set_bearer_technology(index, technology):
    logging.debug(f"{tbs_set_bearer_technology.__name__}")

    data = bytearray()
    data.extend(struct.pack("Bb", index, technology))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['set_bearer_technology'], data=data)

    tbs_command_rsp_succ()


def tbs_hold_call(index):
    logging.debug(f"{tbs_hold_call.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", index))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['hold_call'], data=data)

    tbs_command_rsp_succ()


def tbs_remote_hold_call(index):
    logging.debug(f"{tbs_remote_hold_call.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", index))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['remote_hold_call'], data=data)

    tbs_command_rsp_succ()


def tbs_set_signal_strength(index, strength):
    logging.debug(f"{tbs_set_signal_strength.__name__}")

    data = bytearray()
    data.extend(struct.pack("Bb", index, strength))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['set_signal_strength'], data=data)

    tbs_command_rsp_succ()


def tbs_set_uri_scheme_list(index, uri):
    logging.debug(f"{tbs_set_uri_scheme_list.__name__}")

    data = bytearray()
    data.extend(struct.pack("B", index))
    uri_len = len(uri)
    data.extend(struct.pack("b", uri_len))
    encoded_name = uri.encode("utf-8")
    name_fmt = str(uri_len) + "s"
    data.extend(struct.pack("b", 1))
    # URI count = 1, currently supporting only 1 URI
    data.extend(struct.pack(name_fmt, encoded_name))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['set_uri_scheme_list'], data=data)

    tbs_command_rsp_succ()


def tbs_set_status_flags(index, flags):
    logging.debug(f"{tbs_set_status_flags.__name__}")

    data = bytearray()
    data.extend(struct.pack("B", index))
    data.extend(struct.pack("H", flags))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['set_status_flags'], data=data)

    tbs_command_rsp_succ()

def tbs_terminate_call(index):
    logging.debug(f"{tbs_terminate_call.__name__}")

    data = bytearray()
    data.extend(struct.pack("b", index))

    iutctl = get_iut()
    iutctl.btp_socket.send(*TBS['terminate_call'], data=data)

    tbs_command_rsp_succ()

TBS_EV = {
}