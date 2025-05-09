#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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

import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, \
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba

log = logging.debug

RFCOMM = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_RFCOMM,
                            defs.BTP_RFCOMM_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'conn': (defs.BTP_SERVICE_ID_RFCOMM,
             defs.BTP_RFCOMM_CMD_CONNECT,
             CONTROLLER_INDEX),
    'register_server': (defs.BTP_SERVICE_ID_RFCOMM,
                        defs.BTP_RFCOMM_CMD_REGISTER_SERVER,
                        CONTROLLER_INDEX),
    'send_data': (defs.BTP_SERVICE_ID_RFCOMM,
                  defs.BTP_RFCOMM_CMD_SEND_DATA,
                  CONTROLLER_INDEX),
    'disconnect': (defs.BTP_SERVICE_ID_RFCOMM,
                   defs.BTP_RFCOMM_CMD_DISCONNECT,
                   CONTROLLER_INDEX),
}

rfcomm_state = {0: "BT_RFCOMM_STATE_IDLE",
                2: "BT_RFCOMM_STATE_INIT",
                4: "BT_RFCOMM_STATE_SECURITY_PENDING",
                5: "BT_RFCOMM_STATE_CONNECTING",
                6: "BT_RFCOMM_STATE_CONNECTED",
                7: "BT_RFCOMM_STATE_CONFIG",
                8: "BT_RFCOMM_STATE_USER_DISCONNECT",
                9: "BT_RFCOMM_STATE_DISCONNECTING",
                10: "BT_RFCOMM_STATE_DISCONNECTED",
                }


def rfcomm_conn(bd_addr=None, bd_addr_type=None, channel=5, flags=0):
    logging.debug("%s %r %r", rfcomm_conn.__name__, bd_addr, channel)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('B', channel))
    data_ba.extend(struct.pack('B', flags))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['conn'], data=data_ba)


def rfcomm_register_server(channel=5, flags=0):
    logging.debug("%s %r", rfcomm_register_server.__name__, channel)
    iutctl = get_iut()

    data_ba = bytearray()

    data_ba.extend(struct.pack('B', channel))
    data_ba.extend(struct.pack('B', flags))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['register_server'], data=data_ba)


def rfcomm_send_data(data, channel=5, flags=0):
    logging.debug("%s %r %r", rfcomm_send_data.__name__, data, channel)
    iutctl = get_iut()

    if not isinstance(data, bytearray):
        val_ba = bytearray(data)
    else:
        val_ba = data

    data_ba = bytearray([
        len(data),
        channel,
        flags
    ])
    data_ba.extend(val_ba)

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['send_data'], data=data_ba)


def rfcomm_disconnect(channel=5, flags=0):
    logging.debug("%s %r", rfcomm_disconnect.__name__, channel)
    iutctl = get_iut()

    data_ba = bytearray()

    data_ba.extend(struct.pack('B', channel))
    data_ba.extend(struct.pack('B', flags))

    iutctl.btp_socket.send_wait_rsp(*RFCOMM['disconnect'], data=data_ba)


def rfcomm_command_rsp_succ(timeout=20.0):
    logging.debug("%s", rfcomm_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_RFCOMM)

    return tuple_data


def rfcomm_connected_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_connected_ev.__name__, data, data_len)

    hdr_fmt = '<BHB'
    channel, mtu, state = struct.unpack_from(hdr_fmt, data)

    rfcomm.connected(channel, mtu)

    logging.debug("channel:%r, mtu:%r, state:%s", channel, mtu, rfcomm_state[state])


def rfcomm_disconnected_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_disconnected_ev.__name__, data, data_len)

    hdr_fmt = '<BB'
    channel, state = struct.unpack_from(hdr_fmt, data)

    rfcomm.disconnected(channel)

    logging.debug("channel:%r, state:%s", channel, rfcomm_state[state])


def rfcomm_data_received_ev(rfcomm, data, data_len):
    logging.debug("%s %r %r", rfcomm_data_received_ev.__name__, data, data_len)

    hdr_fmt = '<BH'
    hdr_len = struct.calcsize(hdr_fmt)

    channel, data_len = struct.unpack_from(hdr_fmt, data)
    data_rx = struct.unpack_from('%ds' % data_len, data, hdr_len)[0]

    logging.debug("id:%r, data:%s", channel, binascii.hexlify(data_rx))


RFCOMM_EV = {
    defs.BTP_RFCOMM_EV_CONNECTED: rfcomm_connected_ev,
    defs.BTP_RFCOMM_EV_DISCONNECTED: rfcomm_disconnected_ev,
    defs.BTP_RFCOMM_EV_DATA_RECEIVED: rfcomm_data_received_ev,
}
