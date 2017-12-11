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

import struct
import btpdef
from collections import namedtuple
import logging

HDR_LEN = 5


# Service frames parsers
def parse_svc_core(op, data_len, data):
    if op not in CORE_SERVICE_OP.itervalues():
        raise Exception("Wrong Core Service OP of received frame")
    pass


def parse_svc_gap(op, data_len, data):
    pass


def parse_frame_generic(hdr, data):
    if hdr.svc_id == btpdef.BTP_SERVICE_ID_CORE:
        parse_svc_core(hdr.op, hdr.data_len, data)
    elif hdr.svc_id == btpdef.BTP_SERVICE_ID_GAP:
        parse_svc_gap(hdr.op, hdr.data_len, data)
    else:
        raise Exception("Wrong Service ID of received frame")


def dec_hdr(bin):
    """Decode BTP frame header

    BTP header format
    0            8       16                 24            40
    +------------+--------+------------------+-------------+
    | Service ID | Opcode | Controller Index | Data Length |
    +------------+--------+------------------+-------------+

    """
    logging.debug("%s, %r", dec_hdr.__name__, bin)

    Header = namedtuple('Header', 'svc_id op ctrl_index data_len')

    hdr = Header._make(struct.unpack("<BBBH", bin))

    return hdr


def dec_data(bin):
    logging.debug("%s, %r", dec_data.__name__, bin)

    data_len = len(bin)
    data = struct.unpack('<%ds' % data_len, bin)

    return data


def enc_frame(svc_id, op, ctrl_index, data):
    logging.debug("%s, %r %r %r %r",
                  enc_frame.__name__, svc_id, op, ctrl_index, data)

    str_data = str(bytearray(data))
    int_len = len(str_data)
    hex_len = struct.pack('h', int_len)
    bin = struct.pack('<BBB2s%ds' % int_len, svc_id, op, ctrl_index, hex_len,
                      str_data)

    return bin
