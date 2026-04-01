#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes, le_bytes_to_hex_str

log = logging.debug


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


TMAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_TMAP,
                            defs.BTP_TMAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_TMAP,
                      defs.BTP_TMAP_CMD_DISCOVER,
                      CONTROLLER_INDEX),
}


def tmap_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_TMAP)

    return tuple_data


def tmap_read_supported_cmds():
    logging.debug("")

    iutctl = get_iut()
    iutctl.btp_socket.send(*TMAP['read_supported_cmds'])

    tuple_data = tmap_command_rsp_succ()
    logging.debug("supported cmds %r", tuple_data)


def tmap_discover(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*TMAP['discover'], data=data)

    tmap_command_rsp_succ()


def tmap_ev_discovery_completed(tmap, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sBH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, role = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("TMAP Discovery completed: addr %r, addr_type %r, status %r, role %r",
                  addr, addr_type, status, role)

    tmap.event_received(defs.BTP_TMAP_EV_DISCOVERY_COMPLETED, (addr_type, addr, status, role))


TMAP_EV = {
    defs.BTP_TMAP_EV_DISCOVERY_COMPLETED: tmap_ev_discovery_completed,
}
