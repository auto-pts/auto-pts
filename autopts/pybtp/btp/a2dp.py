from autopts.pybtp.types import AVDTPServiceCategory

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

"""Wrapper around btp messages for A2DP. The functions are added as needed."""

import binascii
import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import addr2btp_ba

A2DP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_READ_SUPPORTED_COMMANDS, defs.BTP_INDEX_NONE, ""),
    "connect": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_CONNECT, CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_DISCONNECT, CONTROLLER_INDEX),
    "register_endpoint": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_REGISTER_ENDPOINT, CONTROLLER_INDEX),
    "discover": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_DISCOVER, CONTROLLER_INDEX),
    "get_capabilities": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_GET_CAPABILITIES, CONTROLLER_INDEX),
    "get_all_capabilities": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_GET_ALL_CAPABILITIES, CONTROLLER_INDEX),
    "config": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_CONFIG, CONTROLLER_INDEX),
    "establish": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_ESTABLISH, CONTROLLER_INDEX),
    "release": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_RELEASE, CONTROLLER_INDEX),
    "start": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_START, CONTROLLER_INDEX),
    "suspend": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_SUSPEND, CONTROLLER_INDEX),
    "reconfig": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_RECONFIG, CONTROLLER_INDEX),
    "abort": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_ABORT, CONTROLLER_INDEX),
    "get_config": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_GET_CONFIG, CONTROLLER_INDEX),
    "delay_report": (defs.BTP_SERVICE_ID_A2DP, defs.BTP_A2DP_CMD_DELAY_REPORT, CONTROLLER_INDEX),
}


def a2dp_command_rsp_succ(op=None):
    logging.debug("%s", a2dp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_A2DP, op)


def a2dp_connect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", a2dp_connect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP["connect"], data=data_ba)


def a2dp_disconnect(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", a2dp_disconnect.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    iutctl.btp_socket.send_wait_rsp(*A2DP["disconnect"], data=data_ba)


def a2dp_register_endpoint(media_type, tsep, codec_type, delay_report, codec_ie=None):
    logging.debug("%s %r %r %r %r %r", a2dp_register_endpoint.__name__,
                  media_type, tsep, codec_type, delay_report, codec_ie)

    iutctl = get_iut()

    data_ba = bytearray()
    data_ba.extend(struct.pack("B", media_type))
    data_ba.extend(struct.pack("B", tsep))
    data_ba.extend(struct.pack("B", codec_type))
    data_ba.extend(struct.pack("B", delay_report))
    if codec_ie is None:
        data_ba.extend(struct.pack("B", 0))
        data_ba.extend(struct.pack("B", 0))
    else:
        data_ba.extend(struct.pack("B", len(codec_ie)))
        data_ba.extend(codec_ie)

    iutctl.btp_socket.send_wait_rsp(*A2DP["register_endpoint"], data=data_ba)


def a2dp_discover(bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r", a2dp_discover.__name__, bd_addr, bd_addr_type)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)

    get_stack().a2dp.set_discover_state(bd_addr_ba, False)
    iutctl.btp_socket.send_wait_rsp(*A2DP["discover"], data=data_ba)


def a2dp_get_capabilities(ep_id=1, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_get_capabilities.__name__, bd_addr, bd_addr_type, ep_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", ep_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["get_capabilities"], data=data_ba)


def a2dp_get_all_capabilities(ep_id=1, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_get_all_capabilities.__name__, bd_addr, bd_addr_type, ep_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", ep_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["get_all_capabilities"], data=data_ba)


def a2dp_stream_config(local_ep_id=1, remote_ep_id=1, delay_report=0, codec_ie=None,
                       bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r %r %r", a2dp_stream_config.__name__,
                  bd_addr, bd_addr_type, local_ep_id, remote_ep_id, delay_report, codec_ie)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", local_ep_id))
    data_ba.extend(struct.pack("B", remote_ep_id))
    data_ba.extend(struct.pack("B", delay_report))
    if codec_ie is None:
        data_ba.extend(struct.pack("B", 0))
        data_ba.extend(struct.pack("B", 0))
    else:
        data_ba.extend(struct.pack("B", len(codec_ie)))
        data_ba.extend(codec_ie)

    iutctl.btp_socket.send_wait_rsp(*A2DP["config"], data=data_ba)


def a2dp_stream_establish(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_establish.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["establish"], data=data_ba)


def a2dp_stream_release(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_release.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["release"], data=data_ba)


def a2dp_stream_start(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_start.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["start"], data=data_ba)


def a2dp_stream_suspend(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_suspend.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["suspend"], data=data_ba)


def a2dp_stream_reconfig(stream_id=0, delay_report=0, codec_ie=None,
                         bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r %r", a2dp_stream_reconfig.__name__,
                  bd_addr, bd_addr_type, stream_id, delay_report, codec_ie)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))
    data_ba.extend(struct.pack("B", delay_report))
    if codec_ie is None:
        data_ba.extend(struct.pack("B", 0))
        data_ba.extend(struct.pack("B", 0))
    else:
        data_ba.extend(struct.pack("B", len(codec_ie)))
        data_ba.extend(codec_ie)

    iutctl.btp_socket.send_wait_rsp(*A2DP["reconfig"], data=data_ba)


def a2dp_stream_abort(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_abort.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["abort"], data=data_ba)


def a2dp_stream_get_config(stream_id=0, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r", a2dp_stream_get_config.__name__, bd_addr, bd_addr_type, stream_id)

    iutctl = get_iut()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))

    iutctl.btp_socket.send_wait_rsp(*A2DP["get_config"], data=data_ba)


def a2dp_stream_delay_report(stream_id=0, delay=1, bd_addr=None, bd_addr_type=defs.BTP_BR_ADDRESS_TYPE):
    logging.debug("%s %r %r %r %r", a2dp_stream_delay_report.__name__,
                  bd_addr, bd_addr_type, stream_id, delay)

    iutctl = get_iut()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba = bytearray()
    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack("B", stream_id))
    data_ba.extend(struct.pack("<H", delay))

    bd_addr = binascii.hexlify(bd_addr_ba[::-1]).decode()

    get_stack().a2dp.set_delay_report(bd_addr, stream_id, delay)

    iutctl.btp_socket.send_wait_rsp(*A2DP["delay_report"], data=data_ba)


# Event handlers
def a2dp_connected_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_connected_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, result = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP connected to addr %r, result %r", bd_addr, result)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    if result == 0:
        get_stack().a2dp.add_connection(bd_addr)


def a2dp_disconnected_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_disconnected_ev.__name__, data, data_len)

    hdr_fmt = "<B6s"
    _, bd_addr = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP disconnected from addr %r", bd_addr)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.remove_connection(bd_addr)


def a2dp_discovered_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_discovered_ev.__name__, data, data_len)

    a2dp = get_stack().a2dp

    hdr_fmt = "<B6sBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, result, sep_len = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP discovered: addr %r, result %r, sep_len %r",
                  bd_addr, result, sep_len)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    # struct bt_avdtp_sep_info {
    #     uint8_t id:6;      // SEID (6 bits)
    #     uint8_t inuse:1;   // In use flag (1 bit)
    #     uint8_t rfa0:1;    // Reserved (1 bit)
    #     uint8_t media_type:4;  // Media type (4 bits)
    #     uint8_t tsep:1;    // TSEP (1 bit)
    #     uint8_t rfa1:3;    // Reserved (3 bits)
    # };
    # Total: 2 bytes per SEP
    sep_fmt = "<BB"
    sep_size = struct.calcsize(sep_fmt)
    offset = hdr_len

    if result == 0:
        for i in range(sep_len):
            if offset + sep_size <= data_len:
                byte0, byte1 = struct.unpack_from(sep_fmt, data, offset)

                ep_id = byte0 & 0x3F
                in_use = (byte0 >> 6) & 0x01
                # rfa0 = (byte0 >> 7) & 0x01

                media_type = byte1 & 0x0F
                tsep = (byte1 >> 4) & 0x01
                # rfa1 = (byte1 >> 5) & 0x07

                logging.debug("  SEP %d: ep_id=%r, in_use=%r, media_type=%r, tsep=%r",
                                        i, ep_id, in_use, media_type, tsep)

                ep = a2dp.get_endpoint(bd_addr, ep_id)
                if ep:
                    ep.media_type = media_type
                    ep.tsep = tsep
                    ep.in_use = in_use
                else:
                    a2dp.add_endpoint(bd_addr, ep_id, media_type, tsep, in_use, capabilities=[])
                offset += sep_size
        get_stack().a2dp.set_discover_state(bd_addr, True)


def a2dp_get_capabilities_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_get_capabilities_ev.__name__, data, data_len)

    # New format: address (7 bytes) + ep_id (1 byte) + service category capabilities (variable)
    # struct btp_a2dp_get_capabilities_ev {
    #     bt_addr_le_t address;
    #     uint8_t ep_id;
    #     struct bt_a2dp_service_category_capabilties cap[0];
    # }

    a2dp = get_stack().a2dp
    hdr_fmt = "<B6sB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, ep_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP endpoint discovered: addr %r, ep_id %r", bd_addr, ep_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()

    # Parse service category capabilities
    # Each capability has: service_category (1 byte) + losc (1 byte) + capability_info (losc bytes)
    offset = hdr_len

    capability_list = []
    while offset < data_len:
        if offset + 2 <= data_len:
            service_category, losc = struct.unpack_from("<BB", data, offset)
            offset += 2

            capability_info = b''
            if losc > 0 and offset + losc <= data_len:
                capability_info = struct.unpack_from(f"{losc}s", data, offset)[0]
                offset += losc

            capability_list.append({
                'service_category': service_category,
                'losc': losc,
                'capability_info': capability_info
            })

            logging.debug("  Capability: category=%r, losc=%r", service_category, losc)
        end_points = a2dp.get_endpoint(bd_addr, ep_id)
        if end_points:
            a2dp.set_cap_to_endpoint(bd_addr, ep_id, capability_list)
        else:
            a2dp.add_endpoint(bd_addr, ep_id, 0, 0, 0, capabilities=capability_list)


def a2dp_config_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_config_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, result, stream_id, delay_report, codec_ie_len = struct.unpack_from(hdr_fmt, data)
    codec_ie = struct.unpack_from(f"{codec_ie_len}s", data, hdr_len)[0]

    logging.debug("A2DP config request: addr %r, local_ep %r, delay_report %r",
                  bd_addr, stream_id, delay_report)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_config_request(bd_addr, result, stream_id, delay_report, codec_ie)


def a2dp_config_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_config_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP config response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_config_response(bd_addr, stream_id, rsp_err_code)


def a2dp_reconfig_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_reconfig_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, result, stream_id, delay_report, codec_ie_len = struct.unpack_from(hdr_fmt, data)
    codec_ie = struct.unpack_from(f"{codec_ie_len}s", data, hdr_len)[0]

    logging.debug("A2DP reconfig request: addr %r, stream_id %r, delay_report %r",
                  bd_addr, stream_id, delay_report)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_reconfig_request(bd_addr, result, stream_id, delay_report, codec_ie)


def a2dp_establish_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_establish_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP establish request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_establish_request(bd_addr, result, stream_id)


def a2dp_establish_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_establish_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP establish response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_establish_response(bd_addr, stream_id, rsp_err_code)


def a2dp_release_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_release_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP release request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_release_request(bd_addr, result, stream_id)


def a2dp_release_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_release_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP release response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_release_response(bd_addr, stream_id, rsp_err_code)


def a2dp_start_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_start_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP start request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_start_request(bd_addr, result, stream_id)


def a2dp_start_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_start_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP start response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_start_response(bd_addr, stream_id, rsp_err_code)


def a2dp_suspend_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_suspend_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP suspend request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_suspend_request(bd_addr, result, stream_id)


def a2dp_suspend_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_suspend_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP suspend response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_suspend_response(bd_addr, stream_id, rsp_err_code)


def a2dp_abort_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_abort_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP abort request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_abort_request(bd_addr, result, stream_id)


def a2dp_abort_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_abort_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP abort response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_abort_response(bd_addr, stream_id, rsp_err_code)


def a2dp_get_config_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_get_config_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, result, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP get config request: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_get_config_request(bd_addr, result, stream_id)


def a2dp_get_config_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_get_config_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBBB"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, stream_id, rsp_err_code, delay_report, codec_ie_len = \
        struct.unpack_from(hdr_fmt, data)
    codec_ie = struct.unpack_from(f"{codec_ie_len}s", data, hdr_len)[0] if codec_ie_len > 0 else b''

    logging.debug("A2DP get config response: addr %r, stream_id %r, err %r, delay_report %r",
                  bd_addr, stream_id, rsp_err_code, delay_report)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_get_config_response(bd_addr, stream_id, rsp_err_code,
                                              delay_report, codec_ie)


def a2dp_stream_recv_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_stream_recv_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBHIH"
    hdr_len = struct.calcsize(hdr_fmt)

    _, bd_addr, stream_id, seq_num, timestamp, data_len_field = struct.unpack_from(hdr_fmt, data)
    stream_data = struct.unpack_from(f"{data_len_field}s", data, hdr_len)[0]

    logging.debug("A2DP stream recv: addr %r, stream_id %r, seq %r, ts %r, len %r",
                  bd_addr, stream_id, seq_num, timestamp, data_len_field)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.add_received_data(bd_addr, stream_id, seq_num, timestamp, stream_data)


def a2dp_stream_sent_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_stream_sent_ev.__name__, data, data_len)

    hdr_fmt = "<B6sB"
    _, bd_addr, stream_id = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP stream sent: addr %r, stream_id %r", bd_addr, stream_id)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_stream_sent(bd_addr, stream_id)


def a2dp_delay_report_req_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_delay_report_req_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBBH"
    _, bd_addr, result, stream_id, delay = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP delay report request: addr %r, stream_id %r, delay %r",
                  bd_addr, stream_id, delay)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_delay_report_request(bd_addr, result, stream_id, delay)


def a2dp_delay_report_rsp_ev(a2dp, data, data_len):
    logging.debug("%s %r %r", a2dp_delay_report_rsp_ev.__name__, data, data_len)

    hdr_fmt = "<B6sBB"
    _, bd_addr, stream_id, rsp_err_code = struct.unpack_from(hdr_fmt, data)

    logging.debug("A2DP delay report response: addr %r, stream_id %r, err %r",
                  bd_addr, stream_id, rsp_err_code)

    bd_addr = binascii.hexlify(bd_addr[::-1]).decode()
    get_stack().a2dp.set_delay_report_response(bd_addr, stream_id, rsp_err_code)


def a2dp_wait_for_delay_reported(addr=None, stream_id=0, expected_delay=1, timeout=5):
    logging.debug("%s %r %r", a2dp_wait_for_delay_reported.__name__, addr, stream_id)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()

    return get_stack().a2dp.wait_for_delay_report(bd_addr_ba, stream_id, expected_delay, timeout)


def a2dp_wait_for_stream_state(addr=None, stream_id=0, expected_state='idle', timeout=5):
    logging.debug("%s %r %r %r", a2dp_wait_for_stream_state.__name__, addr, stream_id, expected_state)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    a2dp = get_stack().a2dp

    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return a2dp.wait_for_stream_state(bd_addr_ba, stream_id, expected_state, timeout)


def a2dp_wait_for_stream_released(addr=None, stream_id=0, timeout=5):
    logging.debug("%s %r %r", a2dp_wait_for_stream_released.__name__, addr, stream_id)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().a2dp.wait_for_stream_released(bd_addr_ba, stream_id, timeout)


def a2dp_wait_for_aborted(addr=None, stream_id=0, timeout=5):
    logging.debug("%s %r %r", a2dp_wait_for_aborted.__name__, addr, stream_id)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().a2dp.wait_for_aborted(bd_addr_ba, stream_id, timeout)


def a2dp_wait_for_discovered(addr=None, timeout=5):
    logging.debug("%s %r", a2dp_wait_for_discovered.__name__, addr)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().a2dp.wait_for_discovered(bd_addr_ba, timeout)


def a2dp_wait_for_get_capabilities_finished(addr=None, ep_id=None, timeout=5):
    logging.debug("%s %r", a2dp_wait_for_get_capabilities_finished.__name__, addr)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    a2dp = get_stack().a2dp
    ep = a2dp.get_endpoints(bd_addr_ba)
    if len(ep):
        if ep_id is None:
            ep_id = len(ep)
        return get_stack().a2dp.wait_for_get_capabilities_finished(bd_addr_ba, ep_id, timeout=timeout)
    else:
        return False


def a2dp_get_endpoints(addr=None):
    logging.debug("%s %r", a2dp_get_endpoints.__name__, addr)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()

    return get_stack().a2dp.get_endpoints(bd_addr_ba)


def a2dp_get_endpoints_media_type(addr=None, endpoint_id=1):
    logging.debug("%s %r %r", a2dp_get_endpoints_media_type.__name__, addr, endpoint_id)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()

    cap = get_stack().a2dp.get_service_cap(bd_addr_ba, endpoint_id, AVDTPServiceCategory.MEDIA_CODEC)
    if cap is None:
        return None
    cap = cap['capability_info']
    hdr_fmt = "<BB"
    hdr_len = struct.calcsize(hdr_fmt)
    media_type, codec_type = struct.unpack_from(hdr_fmt, cap)
    codec_ie = cap[2:]
    return {
        'media_type': media_type,
        'codec_type': codec_type,
        'codec_ie': codec_ie
    }


def a2dp_get_recv_stream_data(addr=None, stream_id=0):
    logging.debug("%s %r %r", a2dp_get_recv_stream_data.__name__, addr, stream_id)

    bd_addr_ba = addr2btp_ba(pts_addr_get(addr))
    bd_addr_ba = binascii.hexlify(bd_addr_ba[::-1]).decode()
    return get_stack().a2dp.get_received_data(bd_addr_ba, stream_id)


def a2dp_get_mmi_round(key):
    logging.debug("%s", a2dp_get_mmi_round.__name__)
    stack = get_stack()
    return stack.a2dp.get_mmi_round(key)


def a2dp_increase_mmi_round(key):
    logging.debug("%s", a2dp_increase_mmi_round.__name__)
    stack = get_stack()
    stack.a2dp.increase_mmi_round(key)


A2DP_EV = {
    defs.BTP_A2DP_EV_CONNECTED: a2dp_connected_ev,
    defs.BTP_A2DP_EV_DISCONNECTED: a2dp_disconnected_ev,
    defs.BTP_A2DP_EV_DISCOVERED: a2dp_discovered_ev,
    defs.BTP_A2DP_EV_GET_CAPABILITIES: a2dp_get_capabilities_ev,
    defs.BTP_A2DP_EV_CONFIG_REQ: a2dp_config_req_ev,
    defs.BTP_A2DP_EV_CONFIG_RSP: a2dp_config_rsp_ev,
    defs.BTP_A2DP_EV_RECONFIG_REQ: a2dp_reconfig_req_ev,
    defs.BTP_A2DP_EV_ESTABLISH_REQ: a2dp_establish_req_ev,
    defs.BTP_A2DP_EV_ESTABLISH_RSP: a2dp_establish_rsp_ev,
    defs.BTP_A2DP_EV_RELEASE_REQ: a2dp_release_req_ev,
    defs.BTP_A2DP_EV_RELEASE_RSP: a2dp_release_rsp_ev,
    defs.BTP_A2DP_EV_START_REQ: a2dp_start_req_ev,
    defs.BTP_A2DP_EV_START_RSP: a2dp_start_rsp_ev,
    defs.BTP_A2DP_EV_SUSPEND_REQ: a2dp_suspend_req_ev,
    defs.BTP_A2DP_EV_SUSPEND_RSP: a2dp_suspend_rsp_ev,
    defs.BTP_A2DP_EV_ABORT_REQ: a2dp_abort_req_ev,
    defs.BTP_A2DP_EV_ABORT_RSP: a2dp_abort_rsp_ev,
    defs.BTP_A2DP_EV_GET_CONFIG_REQ: a2dp_get_config_req_ev,
    defs.BTP_A2DP_EV_GET_CONFIG_RSP: a2dp_get_config_rsp_ev,
    defs.BTP_A2DP_EV_STREAM_RECV: a2dp_stream_recv_ev,
    defs.BTP_A2DP_EV_STREAM_SENT: a2dp_stream_sent_ev,
    defs.BTP_A2DP_EV_DELAY_REPORT_REQ: a2dp_delay_report_req_ev,
    defs.BTP_A2DP_EV_DELAY_REPORT_RSP: a2dp_delay_report_rsp_ev,
}
