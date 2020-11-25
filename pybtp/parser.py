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

import binascii
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
    if isinstance(data, str):
        data = bytes(data, 'utf-8')
    elif isinstance(data, int):
        data = data.to_bytes(1, "little")
    int_len = len(data)

    return struct.pack('<3Bh%ds' % int_len, svc_id, op, ctrl_index, int_len, data)
