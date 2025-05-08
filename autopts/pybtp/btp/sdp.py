#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import addr2btp_ba

log = logging.debug


SDP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_SDP,
                            defs.BTP_SDP_CMD_READ_SUPPORTED_COMMANDS,
                            defs.BTP_INDEX_NONE, ""),
    "search_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_SEARCH_REQ,
                  CONTROLLER_INDEX),
    "attr_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_ATTR_REQ,
                 CONTROLLER_INDEX),
    "search_attr_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_SEARCH_ATTR_REQ,
                  CONTROLLER_INDEX),
}


def sdp_search_req(bd_addr=None, bd_addr_type=None, uuid=0x0100):
    logging.debug("%s %r %r", sdp_search_req.__name__, bd_addr, uuid)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    if isinstance(uuid, str):
        uuid_ba = bytes.fromhex(uuid.replace("-", ""))
    elif isinstance(uuid, int):
        if (uuid > 0xFFFF):
            uuid_ba = struct.pack('<I', uuid)
        else:
            uuid_ba = struct.pack('<H', uuid)
    else:
        uuid_ba = uuid

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send_wait_rsp(*SDP['search_req'], data=data_ba)


def sdp_attr_req(bd_addr=None, bd_addr_type=None, service_record_handle=0):
    logging.debug("%s %r %r", sdp_attr_req.__name__, bd_addr, service_record_handle)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('I', service_record_handle))

    iutctl.btp_socket.send_wait_rsp(*SDP['attr_req'], data=data_ba)


def sdp_search_attr_req(bd_addr=None, bd_addr_type=None, uuid=0x0100):
    logging.debug("%s %r %r", sdp_search_attr_req.__name__, bd_addr, uuid)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = struct.pack('B', pts_addr_type_get(bd_addr_type))

    if isinstance(uuid, str):
        uuid_ba = bytes.fromhex(uuid.replace("-", ""))
    elif isinstance(uuid, int):
        if (uuid > 0xFFFF):
            uuid_ba = struct.pack('<I', uuid)
        else:
            uuid_ba = struct.pack('<H', uuid)
    else:
        uuid_ba = uuid

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
    data_ba.extend(uuid_ba)

    iutctl.btp_socket.send_wait_rsp(*SDP['search_attr_req'], data=data_ba)


def sdp_wait_for_service_record_handle(timeout=30, addr=None):
    stack = get_stack()

    return stack.sdp.sdp_wait_for_service_record_handle(timeout, addr)


def sdp_service_record_handle_ev_(sdp, data, data_len):
    logging.debug("%s %r", sdp_service_record_handle_ev_.__name__, data)

    hdr_fmt = '<B6sB'
    hdr_len = struct.calcsize(hdr_fmt)

    _, addr, count = struct.unpack_from(hdr_fmt, data)
    addr = binascii.hexlify(addr[::-1]).decode()
    handles = struct.unpack_from(f'<{count}I', data, hdr_len)

    for handle in handles:
        _sdp_add_service_record_handles(addr, handle)


SDP_EV = {
    defs.BTP_SDP_EV_SERVICE_RECORD_HANDLE: sdp_service_record_handle_ev_
}


def _sdp_add_service_record_handles(addr, handle):
    stack = get_stack()
    stack.sdp.add_service_record_handles(addr, handle)
