import struct
from msgdefs import *
from collections import namedtuple

#Service frames parsers
def parse_svc_core(op, data_len, data):
    if not op in CORE_SERVICE_OP.itervalues():
        raise Exception("Wrong Core Service OP of received frame")
    pass

def parse_svc_gap(op, data_len, data):
    pass

def parse_frame_generic(hdr, data):
    if hdr.svc_id == SERVICE_ID['SERVICE_ID_CORE']:
        parse_svc_core(hdr.op, hdr.data_len, data)
    elif hdr.svc_id == SERVICE_ID['SERVICE_ID_GAP']:
        parse_svc_gap(hdr.op, hdr.data_len, data)
    else:
        raise Exception("Wrong Service ID of received frame")

#BTP frame format
#0            8       16                 24            40
#+------------+--------+------------------+-------------+
#| Service ID | Opcode | Controller Index | Data Length |
#+------------+--------+------------------+-------------+
def dec_hdr(bin):
    header = namedtuple('header', 'svc_id op ctrl_index data_len')

    hdr = header._make(struct.unpack("<cccH", bin))

    return hdr

def dec_data(bin):
    data_len = len(bin)
    data = struct.unpack('<%ds' % data_len, bin[:data_len])

    return data

def enc_frame(svc_id, op, ctrl_index, data):
    str_data = str(bytearray(data))
    int_len = len(str_data)
    hex_len = struct.pack('h', int_len)
    bin = struct.pack('<ccc2s%ds' % int_len, svc_id, op, ctrl_index, hex_len,
                      str_data)

    return bin
