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
import re
import struct
from random import randint

from autopts.ptsprojects.stack import get_stack, ConnParams
from autopts.pybtp import defs
from autopts.pybtp.types import BTPError, gap_settings_btp2txt, addr2btp_ba, Addr, OwnAddrType, AdDuration, AdType
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get, lt2_addr_get, lt2_addr_type_get, btp_hdr_check, \
    CONTROLLER_INDEX, CONTROLLER_INDEX_NONE, set_pts_addr, set_lt2_addr, LeAdv, get_iut_method as get_iut, lt3_addr_type_get, lt3_addr_get, \
    set_lt3_addr

SDP = {
    "search_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_SEARCH_REQ,
                  CONTROLLER_INDEX_NONE),
    "attr_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_ATTR_REQ,
                 CONTROLLER_INDEX_NONE),
    "search_attr_req": (defs.BTP_SERVICE_ID_SDP, defs.BTP_SDP_CMD_SEARCH_ATTR_REQ,
                  CONTROLLER_INDEX_NONE),
}

def sdp_search_req(bd_addr=None, uuid=0x0100):
    logging.debug("%s %r %r", sdp_search_req.__name__, bd_addr, uuid)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', uuid))

    iutctl.btp_socket.send_wait_rsp(*SDP['search_req'], data=data_ba)


def sdp_attr_req(bd_addr=None, service_record_handle=0):
    logging.debug("%s %r %r", sdp_search_attr_req.__name__, bd_addr, service_record_handle)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('I', service_record_handle))

    iutctl.btp_socket.send_wait_rsp(*SDP['attr_req'], data=data_ba)

def sdp_search_attr_req(bd_addr=None, uuid=0x0100):
    logging.debug("%s %r %r", sdp_search_attr_req.__name__, bd_addr, uuid)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))

    data_ba.extend(bd_addr_ba)
    data_ba.extend(struct.pack('H', uuid))

    iutctl.btp_socket.send_wait_rsp(*SDP['search_attr_req'], data=data_ba)

def sdp_wait_for_service_record_handle(timeout=30, addr=None):
    stack = get_stack()

    return stack.sdp.sdp_wait_for_service_record_handle(timeout, addr)

def sdp_service_record_handle_ev_(sdp, data, data_len):
    logging.debug("%s %r", sdp_service_record_handle_ev_.__name__, data)

    data_fmt = '<6sI'

    print(data)
    addr, handle, = struct.unpack_from(data_fmt, data)
    addr = binascii.hexlify(addr[::-1]).decode()

    _sdp_add_service_record_handles(addr, handle)

SDP_EV = {
    defs.BTP_SDP_EV_SERVICE_RECORD_HANDLE: sdp_service_record_handle_ev_
}

def _sdp_add_service_record_handles(addr, handle):
    stack = get_stack()
    stack.sdp.add_service_record_handles(addr, handle)