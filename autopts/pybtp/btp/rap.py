#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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
    btp_hdr_check, pts_addr_type_get, pts_addr_get
from autopts.pybtp.types import BTPError, le_bytes_to_hex_str, addr_str_to_le_bytes

log = logging.debug


RAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_RAP,
                            defs.BTP_RAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'set_test_method': (defs.BTP_SERVICE_ID_RAP,
                        defs.BTP_RAP_CMD_SET_TEST_METHOD,
                        CONTROLLER_INDEX),
    'start_ranging': (defs.BTP_SERVICE_ID_RAP,
                      defs.BTP_RAP_CMD_START_RANGING,
                      CONTROLLER_INDEX),
    'stop_ranging': (defs.BTP_SERVICE_ID_RAP,
                     defs.BTP_RAP_CMD_STOP_RANGING,
                     CONTROLLER_INDEX),
    'set_test_cs_subevent_data': (defs.BTP_SERVICE_ID_RAP,
                                  defs.BTP_RAP_CMD_SET_TEST_CS_SUBEVENT_DATA,
                                  CONTROLLER_INDEX),
}


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def rap_command_rsp_succ(timeout=20.0):
    logging.debug("%s", rap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_RAP)

    return tuple_data


def rap_set_test_method(test_method, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{rap_set_test_method.__name__}")

    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', test_method)

    iutctl = get_iut()
    iutctl.btp_socket.send(*RAP['set_test_method'], data=data)

    rap_command_rsp_succ()


def rap_start_ranging(flags, local_role, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{rap_start_ranging.__name__}")

    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', flags)
    data += struct.pack('B', local_role)

    iutctl = get_iut()
    iutctl.btp_socket.send(*RAP['start_ranging'], data=data)

    rap_command_rsp_succ()


def rap_stop_ranging(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{rap_stop_ranging.__name__}")

    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*RAP['stop_ranging'], data=data)

    rap_command_rsp_succ()


def rap_set_test_cs_subevent_data(data_ba, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{rap_set_test_cs_subevent_data.__name__}")

    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', len(data_ba))
    data += data_ba

    iutctl = get_iut()
    iutctl.btp_socket.send(*RAP['set_test_cs_subevent_data'], data=data)

    rap_command_rsp_succ()


# An example event, to be changed or deleted
def rap_ev_ranging_complete(rap, data, data_len):
    logging.debug('%s %r', rap_ev_ranging_complete.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug(f'RAP Ranging complete event: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    rap.event_received(defs.BTP_RAP_EV_RANGING_COMPLETE, (addr_type, addr, status))


RAP_EV = {
    defs.BTP_RAP_EV_RANGING_COMPLETE: rap_ev_ranging_complete,
}
