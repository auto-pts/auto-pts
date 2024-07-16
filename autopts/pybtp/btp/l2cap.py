#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.types import addr2btp_ba, L2CAPConnectionResponse, BTPError
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get, get_iut_method as get_iut
from autopts.pybtp.btp.gap import gap_wait_for_connection

L2CAP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_L2CAP,
                       defs.BTP_L2CAP_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CONNECT,
                CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_DISCONNECT,
                   CONTROLLER_INDEX),
    "send_data": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_SEND_DATA,
                  CONTROLLER_INDEX),
    "listen": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_LISTEN,
               CONTROLLER_INDEX),
    "reconfigure": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_RECONFIGURE,
                    CONTROLLER_INDEX),
    "disconnect_eatt_chans": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_DISCONNECT_EATT_CHANS,
                              CONTROLLER_INDEX),
    "credits": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CREDITS,
                CONTROLLER_INDEX),
    "connect_with_sec_level": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CONNECT_WITH_SEC_LEVEL,
                               CONTROLLER_INDEX),
    "echo": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_ECHO,
             CONTROLLER_INDEX),
    "cls_listen": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CLS_LISTEN,
                   CONTROLLER_INDEX),
    "cls_send": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CLS_SEND,
                 CONTROLLER_INDEX),
    "listen_with_mode": (defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_LISTEN_WITH_MODE,
                         CONTROLLER_INDEX),
}


def l2cap_command_rsp_succ(op=None):
    logging.debug("%s", l2cap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, op)


def l2cap_conn(bd_addr, bd_addr_type, psm, mtu=0, num=1, ecfc=0, hold_credit=0):
    logging.debug("%s %r %r %r", l2cap_conn.__name__, bd_addr, bd_addr_type,
                  psm)
    iutctl = get_iut()
    gap_wait_for_connection()

    if isinstance(psm, str):
        psm = int(psm, 16)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', num))

    opts = 0
    if ecfc:
        opts |= defs.L2CAP_CONNECT_OPT_ECFC

    if hold_credit:
        opts |= defs.L2CAP_CONNECT_OPT_HOLD_CREDIT

    data_ba.extend(struct.pack('B', opts))

    iutctl.btp_socket.send(*L2CAP['connect'], data=data_ba)

    chan_ids = l2cap_conn_rsp()
    logging.debug("id %r", chan_ids)


def l2cap_conn_with_mode(bd_addr, bd_addr_type, psm, mtu=0, num=1, mode=defs.L2CAP_CONNECT_OPT_NONE, ecfc=0, hold_credit=0):
    logging.debug("%s %r %r %r", l2cap_conn_with_mode.__name__, bd_addr, bd_addr_type,
                  psm)
    iutctl = get_iut()
    gap_wait_for_connection()

    if isinstance(psm, str):
        psm = int(psm, 16)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', num))

    opts = 0
    if ecfc:
        opts |= defs.L2CAP_CONNECT_OPT_ECFC

    if hold_credit:
        opts |= defs.L2CAP_CONNECT_OPT_HOLD_CREDIT

    opts |= mode

    data_ba.extend(struct.pack('B', opts))

    iutctl.btp_socket.send(*L2CAP['connect'], data=data_ba)

    chan_ids = l2cap_conn_with_mode_rsp()
    logging.debug("id %r", chan_ids)


l2cap_result_str = {0: "Success",
                    2: "LE_PSM not supported",
                    4: "Insufficient Resources",
                    5: "insufficient authentication",
                    6: "insufficient authorization",
                    7: "insufficient encryption key size",
                    8: "insufficient encryption",
                    9: "Invalid Source CID",
                    10: "Source CID already allocated",
                    }


def l2cap_conn_with_mode_rsp():
    logging.debug("%s", l2cap_conn_rsp.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    try:
        btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, defs.L2CAP_CONNECT)
        num = struct.unpack_from('<B', tuple_data[0])[0]
        channels = struct.unpack_from('%ds' % num, tuple_data[0], 1)[0]
        return list(channels)
    except BTPError as err:
        if tuple_hdr.op == defs.BTP_STATUS:
            error = struct.unpack_from('<B', tuple_data[0])[0]
            if error == defs.BTP_STATUS_NOT_SUPPORT:
                logging.debug("The mode is unsupported")
                return None
        raise

def l2cap_conn_rsp():
    logging.debug("%s", l2cap_conn_rsp.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CONNECT)
    num = struct.unpack_from('<B', tuple_data[0])[0]
    channels = struct.unpack_from('%ds' % num, tuple_data[0], 1)[0]
    return list(channels)


def l2cap_disconn(chan_id):
    logging.debug("%s %r", l2cap_disconn.__name__, chan_id)

    stack = get_stack()
    l2cap = stack.l2cap
    if not l2cap.is_connected(chan_id):
        return

    iutctl = get_iut()

    data_ba = bytearray(chr(chan_id).encode('utf-8'))

    iutctl.btp_socket.send(*L2CAP['disconnect'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_DISCONNECT)


def l2cap_send_data(chan_id, val, val_mtp=None):
    logging.debug("%s %r %r %r", l2cap_send_data.__name__, chan_id, val,
                  val_mtp)

    iutctl = get_iut()

    if val_mtp:
        val *= int(val_mtp)

    val_ba = bytes.fromhex(val)
    val_len_ba = struct.pack('H', len(val_ba))

    data_ba = bytearray(chr(chan_id).encode('utf-8'))
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*L2CAP['send_data'], data=data_ba)

    stack = get_stack()
    stack.l2cap.tx(chan_id, val)


def l2cap_listen(psm, transport, mtu=0, response=L2CAPConnectionResponse.success):
    logging.debug("%s %r %r %r %r", l2cap_le_listen.__name__, psm, transport, mtu, response)

    iutctl = get_iut()

    if isinstance(psm, str):
        psm = int(psm, 16)

    data_ba = bytearray(struct.pack('H', psm))
    data_ba.extend(struct.pack('B', transport))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('H', response))

    iutctl.btp_socket.send(*L2CAP['listen'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_LISTEN)


def l2cap_disconn_eatt_chans(bd_addr, bd_addr_type, channel_count):
    logging.debug("%s %r", l2cap_disconn_eatt_chans.__name__, channel_count)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(bytearray(chr(channel_count).encode('utf-8')))

    iutctl.btp_socket.send(*L2CAP['disconnect_eatt_chans'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_DISCONNECT_EATT_CHANS)


def l2cap_le_listen(psm, mtu=0, response=0):
    l2cap_listen(psm, defs.L2CAP_TRANSPORT_LE, mtu, response)


def l2cap_reconfigure(bd_addr, bd_addr_type, mtu, channels):
    logging.debug("%s %r %r %r %r", l2cap_reconfigure.__name__,
                  bd_addr, bd_addr_type, mtu, channels)

    iutctl = get_iut()

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', len(channels)))
    for chan in channels:
        data_ba.extend(struct.pack('B', chan))

    iutctl.btp_socket.send(*L2CAP['reconfigure'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_RECONFIGURE)


def l2cap_credits(chan_id):
    logging.debug("%s %r", l2cap_credits.__name__, chan_id)

    iutctl = get_iut()

    data_ba = bytearray(chr(chan_id).encode('utf-8'))

    iutctl.btp_socket.send(*L2CAP['credits'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_CREDITS)


def l2cap_conn_with_sec_level_rsp():
    logging.debug("%s", l2cap_conn_with_sec_level_rsp.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_L2CAP, defs.BTP_L2CAP_CMD_CONNECT_WITH_SEC_LEVEL)
    num = struct.unpack_from('<B', tuple_data[0])[0]
    channels = struct.unpack_from('%ds' % num, tuple_data[0], 1)[0]
    return list(channels)


def l2cap_conn_with_sec_level(bd_addr, bd_addr_type, psm, mtu=0, num=1, ecfc=0, hold_credit=0, sec_level=defs.L2CAP_CONNECT_SEC_LEVEL_0):
    logging.debug("%s %r %r %r %r", l2cap_conn.__name__, bd_addr, bd_addr_type,
                  psm, sec_level)
    iutctl = get_iut()
    gap_wait_for_connection()

    if isinstance(psm, str):
        psm = int(psm, 16)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)
    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('B', num))

    opts = 0
    if ecfc:
        opts |= defs.L2CAP_CONNECT_OPT_ECFC

    if hold_credit:
        opts |= defs.L2CAP_CONNECT_OPT_HOLD_CREDIT

    data_ba.extend(struct.pack('B', opts))
    data_ba.extend(struct.pack('B', sec_level))

    iutctl.btp_socket.send(*L2CAP['connect_with_sec_level'], data=data_ba)

    chan_ids = l2cap_conn_with_sec_level_rsp()
    logging.debug("id %r", chan_ids)


def l2cap_echo(bd_addr, bd_addr_type, val=None, val_mtp=None):
    logging.debug("%s %r %r %r %r", l2cap_echo.__name__, bd_addr, bd_addr_type,
                  val, val_mtp)

    iutctl = get_iut()

    if val_mtp:
        val *= int(val_mtp)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)

    if val:
        val_ba = bytes.fromhex(val)
        val_len_ba = struct.pack('H', len(val_ba))
    else:
        val_len_ba = struct.pack('H', 0)

    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(val_len_ba)
    if val:
        data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*L2CAP['echo'], data=data_ba)


def l2cap_cls_listen(psm):
    logging.debug("%s %r", l2cap_cls_listen.__name__, psm)

    iutctl = get_iut()

    if isinstance(psm, str):
        psm = int(psm, 16)

    data_ba = bytearray(struct.pack('H', psm))

    iutctl.btp_socket.send_wait_rsp(*L2CAP['cls_listen'], data=data_ba)


def l2cap_cls_send(bd_addr, bd_addr_type, psm, val=None, val_mtp=None):
    logging.debug("%s %r %r %r %r %r", l2cap_cls_send.__name__, bd_addr, bd_addr_type,
                  psm, val, val_mtp)

    iutctl = get_iut()

    if val_mtp:
        val *= int(val_mtp)

    bd_addr = pts_addr_get(bd_addr)
    bd_addr_type = pts_addr_type_get(bd_addr_type)

    bd_addr_ba = addr2btp_ba(bd_addr)

    if isinstance(psm, str):
        psm = int(psm, 16)

    if val:
        val_ba = bytes.fromhex(val)
        val_len_ba = struct.pack('H', len(val_ba))
    else:
        val_len_ba = struct.pack('H', 0)

    data_ba = bytearray(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', psm))
    data_ba.extend(val_len_ba)
    if val:
        data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*L2CAP['cls_send'], data=data_ba)


def l2cap_listen_with_mode(psm, transport, opt=defs.L2CAP_LISTEN_OPT_NONE, mtu=0, response=L2CAPConnectionResponse.success):
    logging.debug("%s %r %r %r %r %r", l2cap_listen_with_mode.__name__, psm, transport, opt, mtu, response)

    iutctl = get_iut()

    if isinstance(psm, str):
        psm = int(psm, 16)

    data_ba = bytearray(struct.pack('H', psm))
    data_ba.extend(struct.pack('B', transport))
    data_ba.extend(struct.pack('B', opt))
    data_ba.extend(struct.pack('H', mtu))
    data_ba.extend(struct.pack('H', response))

    iutctl.btp_socket.send(*L2CAP['listen_with_mode'], data=data_ba)

    l2cap_command_rsp_succ(defs.BTP_L2CAP_CMD_LISTEN_WITH_MODE)


def l2cap_connected_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_connected_ev.__name__, data, data_len)

    hdr_fmt = '<BHHHHHB6s'
    chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps, \
        bd_addr_type, bd_addr = struct.unpack_from(hdr_fmt, data)
    l2cap.connected(chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                    bd_addr_type, bd_addr)

    logging.debug("id:%r on psm:%r, peer_mtu:%r, peer_mps:%r, our_mtu:%r, "
                  "our_mps:%r, addr %r type %r",
                  chan_id, psm, peer_mtu, peer_mps, our_mtu, our_mps,
                  bd_addr, bd_addr_type)


def l2cap_disconnected_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_disconnected_ev.__name__, data, data_len)

    hdr_fmt = '<HBHB6s'
    res, chan_id, psm, bd_addr_type, bd_addr = struct.unpack_from(hdr_fmt, data)
    result_str = l2cap_result_str[res]
    l2cap.disconnected(chan_id, psm, bd_addr_type, bd_addr, result_str)

    logging.debug("id:%r on psm:%r, addr %r type %r, res %r",
                  chan_id, psm, bd_addr, bd_addr_type, result_str)


def l2cap_data_rcv_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_data_rcv_ev.__name__, data, data_len)

    hdr_fmt = '<BH'
    hdr_len = struct.calcsize(hdr_fmt)

    chan_id, data_len = struct.unpack_from(hdr_fmt, data)
    data_rx = struct.unpack_from('%ds' % data_len, data, hdr_len)[0]
    l2cap.rx(chan_id, data_rx)

    logging.debug("id:%r, data:%s", chan_id, binascii.hexlify(data_rx))


def l2cap_reconfigured_ev(l2cap, data, data_len):
    logging.debug("%s %r %r", l2cap_reconfigured_ev.__name__, data, data_len)

    hdr_fmt = '<BHHHH'
    chan_id, peer_mtu, peer_mps, our_mtu, our_mps = \
        struct.unpack_from(hdr_fmt, data)
    l2cap.reconfigured(chan_id, peer_mtu, peer_mps, our_mtu, our_mps)
    logging.debug("id:%r, peer_mtu:%r, peer_mps:%r our_mtu:%r our_mps:%r",
                  chan_id, peer_mtu, peer_mps, our_mtu, our_mps)


L2CAP_EV = {
    defs.BTP_L2CAP_EV_CONNECTED: l2cap_connected_ev,
    defs.BTP_L2CAP_EV_DISCONNECTED: l2cap_disconnected_ev,
    defs.BTP_L2CAP_EV_DATA_RECEIVED: l2cap_data_rcv_ev,
    defs.BTP_L2CAP_EV_RECONFIGURED: l2cap_reconfigured_ev,
}
