#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025-2026 NXP
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.pybtp.types import addr2btp_ba

RFCOMM = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_RFCOMM,
                       defs.BTP_RFCOMM_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_CONNECT,
                CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_DISCONNECT,
                   CONTROLLER_INDEX),
    "send_data": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_SEND_DATA,
                  CONTROLLER_INDEX),
    "listen": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_LISTEN,
               CONTROLLER_INDEX),
    "send_rpn": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_SEND_RPN,
                 CONTROLLER_INDEX),
    "get_dlc_info": (defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_GET_DLC_INFO,
                     CONTROLLER_INDEX),
}


def rfcomm_command_rsp_succ(op=None):
    logging.debug("%s", rfcomm_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_RFCOMM, op)


def rfcomm_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=5):
    logging.debug("%s %r %r %r", rfcomm_connect.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()
    gap_wait_for_connection()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_type_ba = struct.pack('B', bd_addr_type)
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['connect'], data=data_ba)


def rfcomm_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=5):
    logging.debug("%s %r %r %r", rfcomm_disconnect.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_type_ba = struct.pack('B', bd_addr_type)
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['disconnect'], data=data_ba)


def rfcomm_send_data(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=5, val='00',
                     val_mtp=None):
    logging.debug("%s %r %r %r %r %r", rfcomm_send_data.__name__, bd_addr, bd_addr_type,
                  channel, val, val_mtp)

    iutctl = get_iut()

    if val_mtp:
        val *= int(val_mtp)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_type_ba = struct.pack('B', bd_addr_type)
    bd_addr_ba = addr2btp_ba(bd_addr)
    val_ba = bytes.fromhex(val)
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['send_data'], data=data_ba)


def rfcomm_listen(channel=5):
    logging.debug("%s %r", rfcomm_listen.__name__, channel)

    iutctl = get_iut()

    data_ba = bytearray(struct.pack('B', channel))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['listen'], data=data_ba)


def rfcomm_send_rpn(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=5, baud_rate=0,
                    line_settings=0, flow_control=0, xon_char=0, xoff_char=0, param_mask=0):
    logging.debug("%s %r %r %r %r %r %r %r %r %r", rfcomm_send_rpn.__name__,
                  bd_addr, bd_addr_type, channel, baud_rate, line_settings,
                  flow_control, xon_char, xoff_char, param_mask)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_type_ba = struct.pack('B', bd_addr_type)
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))
    data_ba.extend(struct.pack('B', baud_rate))
    data_ba.extend(struct.pack('B', line_settings))
    data_ba.extend(struct.pack('B', flow_control))
    data_ba.extend(struct.pack('B', xon_char))
    data_ba.extend(struct.pack('B', xoff_char))
    data_ba.extend(struct.pack('H', param_mask))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['send_rpn'], data=data_ba)


def rfcomm_get_dlc_info(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=5):
    logging.debug("%s %r %r %r", rfcomm_get_dlc_info.__name__, bd_addr, bd_addr_type, channel)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_type_ba = struct.pack('B', bd_addr_type)
    bd_addr_ba = addr2btp_ba(bd_addr)

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))

    iutctl.btp_socket.send(*RFCOMM['get_dlc_info'], data=data_ba)

    return rfcomm_get_dlc_info_rsp()


def rfcomm_get_dlc_info_rsp():
    logging.debug("%s", rfcomm_get_dlc_info_rsp.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_RFCOMM, defs.BTP_RFCOMM_CMD_GET_DLC_INFO)

    hdr_fmt = '<HB'
    mtu, state = struct.unpack_from(hdr_fmt, tuple_data[0])

    logging.debug("mtu:%r, state:%r", mtu, state)

    return mtu, state


def rfcomm_connected_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_connected_ev.__name__, data, data_len)

    hdr_fmt = '<B6sBH'
    _, bd_addr, channel, mtu = struct.unpack_from(hdr_fmt, data)

    logging.debug("addr:%r, channel:%r, mtu:%r", bd_addr, channel, mtu)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    rfcomm.add_channel(bd_addr, channel, mtu)


def rfcomm_disconnected_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_disconnected_ev.__name__, data, data_len)

    hdr_fmt = '<B6sB'
    _, bd_addr, channel = struct.unpack_from(hdr_fmt, data)

    logging.debug("addr:%r, channel:%r", bd_addr, channel)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    rfcomm.remove_channel(bd_addr, channel)


def rfcomm_data_received_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_data_received_ev.__name__, data, data_len)

    hdr_fmt = '<B6sBH'
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, channel, data_length = struct.unpack_from(hdr_fmt, data)
    data_rx = struct.unpack_from(f"{data_length}s", data, hdr_len)[0]

    logging.debug("addr:%r, channel:%r, data:%s", bd_addr, channel, binascii.hexlify(data_rx))

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    rfcomm.rx(bd_addr, channel, data_rx)


def rfcomm_data_sent_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_data_sent_ev.__name__, data, data_len)

    hdr_fmt = '<B6sBb'
    _, bd_addr, channel, err = struct.unpack_from(hdr_fmt, data)

    logging.debug("addr:%r, channel:%r, err:%r", bd_addr, channel, err)


RFCOMM_EV = {
    defs.BTP_RFCOMM_EV_CONNECTED: rfcomm_connected_ev,
    defs.BTP_RFCOMM_EV_DISCONNECTED: rfcomm_disconnected_ev,
    defs.BTP_RFCOMM_EV_DATA_RECEIVED: rfcomm_data_received_ev,
    defs.BTP_RFCOMM_EV_DATA_SENT: rfcomm_data_sent_ev,
}
