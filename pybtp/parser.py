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
from collections import namedtuple

HDR_LEN = 5


def dec_hdr(bin):
    """Decode BTP frame header

    BTP header format
    0            8       16                 24            40
    +------------+--------+------------------+-------------+
    | Service ID | Opcode | Controller Index | Data Length |
    +------------+--------+------------------+-------------+

    """
    Header = namedtuple('Header', 'svc_id op ctrl_index data_len')

    return Header._make(struct.unpack("<BBBH", bin))


def dec_data(bin):
    data_len = len(bin)

    return struct.unpack('<%ds' % data_len, bin)


def enc_frame(svc_id, op, ctrl_index, data):
    str_data = str(bytearray(data))
    int_len = len(str_data)
    hex_len = struct.pack('h', int_len)

    return struct.pack('<BBB2s%ds' % int_len, svc_id, op, ctrl_index, hex_len,
                       str_data)
