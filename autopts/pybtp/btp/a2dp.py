#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, nxp.
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

import logging
import struct

import numpy as np

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut

log = logging.debug


A2DP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_A2DP,
                            defs.BTP_A2DP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'register_ep': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_REGISTER_EP,
                    CONTROLLER_INDEX),
    'connect': (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_CONNECT,
                CONTROLLER_INDEX),
    "discover": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_DISCOVER,
                 CONTROLLER_INDEX),
    "configure": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_CONFIGURE,
                  CONTROLLER_INDEX),
    "establish": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_ESTABLISH,
                  CONTROLLER_INDEX),
    "start": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_START,
              CONTROLLER_INDEX),
    "suspend": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_SUSPEND,
                CONTROLLER_INDEX),
    "release": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_RELEASE,
                CONTROLLER_INDEX),
    "abort": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_ABORT,
              CONTROLLER_INDEX),
    "reconfigure": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_RECONFIGURE,
                    CONTROLLER_INDEX),
    "enable_delay_report": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_ENABLE_DELAY_REPORT,
                            CONTROLLER_INDEX),
    "send_delay_report": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_SEND_DELAY_REPORT,
                          CONTROLLER_INDEX),
    "get_config": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_GET_CONFIG,
                CONTROLLER_INDEX),
}


def a2dp_command_rsp_succ(op=None, timeout=5):
    logging.debug("%s", a2dp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_A2DP, op)

    return tuple_data


def a2dp_wait_for_command_rsp(cmd, timeout=5):
    stack = get_stack()
    stack.a2dp.wait_for_command_rsp(cmd, timeout)


def a2dp_recv_media(timeout=5):
    stack = get_stack()
    stack.a2dp.is_recv_media(timeout)


def a2dp_ev_connected(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_connected.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_CONNECTED]
    else:
        logging.error(f"Connection failed with error code: {errcode}")


def a2dp_ev_get_capabilities_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_get_capabilities_rsp.__name__, data)
    stack = get_stack()

    stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_GET_CAPABILITIES_RSP]


def a2dp_ev_set_configuration_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_set_configuration_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_SET_CONFIGURATION_RSP]
    else:
        logging.error(f"Set configuration failed with error code: {errcode}")


def a2dp_ev_establish_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_establish_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_ESTABLISH_RSP]
    else:
        logging.error(f"Establish failed with error code: {errcode}")


def a2dp_ev_release_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_release_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_RELEASE_RSP]
    else:
        logging.error(f"Release failed with error code: {errcode}")


def a2dp_ev_start_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_start_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_START_RSP]
    else:
        logging.error(f"Start failed with error code: {errcode}")


def a2dp_ev_suspend_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_suspend_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_SUSPEND_RSP]
    else:
        logging.error(f"Suspend failed with error code: {errcode}")


def a2dp_ev_disconnected(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_disconnected.__name__, data)
    stack = get_stack()

    stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_DISCONNECTED]


def a2dp_ev_abort_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_abort_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]
    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_ABORT_RSP]


def a2dp_ev_get_config_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_get_config_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)

    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_GET_CONFIG_RSP]


def a2dp_ev_recv_media(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_recv_media.__name__, data)
    stack = get_stack()

    frame_num, length = struct.unpack_from('<BB', data, 0)[0]
    media_date = list(data)[2:]
    stack.a2dp.media.append(stack.a2dp.recv_media(frame_num, length, media_date))


def a2dp_ev_send_delay_report_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_send_delay_report_rsp.__name__, data)
    stack = get_stack()
    errcode = struct.unpack_from('<B', data, 0)[0]
    if errcode == 0:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_SEND_DELAY_REPORT_RSP]


def a2dp_ev_discover_rsp(a2dp, data, data_len):
    logging.debug('%s %r', a2dp_ev_discover_rsp.__name__, data)
    stack = get_stack()

    errcode = struct.unpack_from('<b', data, 0)[0]
    if errcode != 0:
        logging.error(f"SDP Discover failed with error code: {errcode}")
    else:
        stack.a2dp.status = stack.a2dp.STATUS[defs.BTP_A2DP_EV_DISCOVER_RSP]


def a2dp_register_ep(sep_type, media_type):
    logging.debug("%s", a2dp_register_ep.__name__)
    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.append(sep_type)
    data_ba.append(media_type)
    iutctl.btp_socket.send(*A2DP['register_ep'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_REGISTER_EP)


def a2dp_connect(bd_addr=None):
    logging.debug("%s", a2dp_connect.__name__)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = btp.addr2btp_ba(btp.pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*A2DP['connect'], data=data_ba)
    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_CONNECT)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_CONNECTED)


def a2dp_discover(bd_addr=None):
    logging.debug("%s", a2dp_discover.__name__)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = btp.addr2btp_ba(btp.pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send(*A2DP['discover'], data=data_ba)
    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_DISCOVER)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_GET_CAPABILITIES_RSP, timeout=6)


def a2dp_configure():
    logging.debug("%s", a2dp_configure.__name__)
    iutctl = get_iut()

    data_ba = ""

    iutctl.btp_socket.send(*A2DP['configure'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_CONFIGURE)

    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_SET_CONFIGURATION_RSP)


def a2dp_reconfigure():
    logging.debug("%s", a2dp_reconfigure.__name__)
    iutctl = get_iut()

    data_ba = ""

    iutctl.btp_socket.send(*A2DP['reconfigure'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_RECONFIGURE)

    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_SET_CONFIGURATION_RSP)


def a2dp_establish():
    logging.debug("%s", a2dp_establish.__name__)
    iutctl = get_iut()

    data_ba = ""

    iutctl.btp_socket.send(*A2DP['establish'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_ESTABLISH)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_ESTABLISH_RSP)


def a2dp_start():
    logging.debug("%s", a2dp_start.__name__)
    iutctl = get_iut()

    data_ba = ''

    iutctl.btp_socket.send(*A2DP['start'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_START)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_START_RSP)


def a2dp_suspend():
    logging.debug("%s", a2dp_suspend.__name__)
    iutctl = get_iut()

    data_ba = ''

    iutctl.btp_socket.send(*A2DP['suspend'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_SUSPEND)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_SUSPEND_RSP)


def a2dp_release():
    logging.debug("%s", a2dp_release.__name__)
    iutctl = get_iut()

    data_ba = ''

    iutctl.btp_socket.send(*A2DP['release'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_RELEASE)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_RELEASE_RSP)


def a2dp_enable_delay_report():
    logging.debug("%s", a2dp_enable_delay_report.__name__)
    iutctl = get_iut()

    iutctl.btp_socket.send(*A2DP['enable_delay_report'], data="")

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_ENABLE_DELAY_REPORT)


def a2dp_send_delay_report(delay):
    logging.debug("%s", a2dp_send_delay_report.__name__)
    iutctl = get_iut()

    data_ba = struct.pack('<H', delay)

    iutctl.btp_socket.send(*A2DP['send_delay_report'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_SEND_DELAY_REPORT)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_SEND_DELAY_REPORT_RSP)


def a2dp_abort():
    logging.debug("%s", a2dp_abort.__name__)
    iutctl = get_iut()

    data_ba = ''

    iutctl.btp_socket.send(*A2DP['abort'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_ABORT)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_ABORT_RSP)


def a2dp_get_config():
    logging.debug("%s", a2dp_get_config.__name__)
    iutctl = get_iut()

    data_ba = ''

    iutctl.btp_socket.send(*A2DP['get_config'], data=data_ba)

    a2dp_command_rsp_succ(defs.BTP_A2DP_CMD_GET_CONFIG)
    btp.a2dp_wait_for_command_rsp(defs.BTP_A2DP_EV_GET_CONFIG_RSP)


def a2dp_get_mmi_round(key):
    logging.debug("%s", a2dp_get_mmi_round.__name__)
    stack = get_stack()
    return stack.a2dp.get_mmi_round(key)


def a2dp_increase_mmi_round(key):
    logging.debug("%s", a2dp_increase_mmi_round.__name__)
    stack = get_stack()
    stack.a2dp.increase_mmi_round(key)


A2DP_EV = {
    defs.BTP_A2DP_EV_CONNECTED: a2dp_ev_connected,
    defs.BTP_A2DP_EV_DISCOVER_RSP: a2dp_ev_discover_rsp,
    defs.BTP_A2DP_EV_GET_CAPABILITIES_RSP: a2dp_ev_get_capabilities_rsp,
    defs.BTP_A2DP_EV_SET_CONFIGURATION_RSP: a2dp_ev_set_configuration_rsp,
    defs.BTP_A2DP_EV_ESTABLISH_RSP: a2dp_ev_establish_rsp,
    defs.BTP_A2DP_EV_RELEASE_RSP: a2dp_ev_release_rsp,
    defs.BTP_A2DP_EV_START_RSP: a2dp_ev_start_rsp,
    defs.BTP_A2DP_EV_SUSPEND_RSP: a2dp_ev_suspend_rsp,
    defs.BTP_A2DP_EV_DISCONNECTED: a2dp_ev_disconnected,
    defs.BTP_A2DP_EV_ABORT_RSP: a2dp_ev_abort_rsp,
    defs.BTP_A2DP_EV_RECV_MEDIA: a2dp_ev_recv_media,
    defs.BTP_A2DP_EV_SEND_DELAY_REPORT_RSP: a2dp_ev_send_delay_report_rsp,
    defs.BTP_A2DP_EV_GET_CONFIG_RSP: a2dp_ev_get_config_rsp,
}
