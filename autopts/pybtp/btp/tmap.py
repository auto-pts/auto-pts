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

import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr2btp_ba

log = logging.debug

def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
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
    logging.debug("%s", tmap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_TMAP)

    return tuple_data

def tmap_read_supported_cmds():
    logging.debug(f"{tmap_read_supported_cmds.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*TMAP['read_supported_cmds'])

    tuple_data = tmap_command_rsp_succ()
    logging.debug("supported cmds %r", tuple_data)


def tmap_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{tmap_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*TMAP['discover'], data=data)

    tmap_command_rsp_succ()

def tmap_ev_discovery_completed(tmap, data, data_len):
    logging.debug('%s %r', tmap_ev_discovery_completed.__name__, data)

    fmt = '<B6sBH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, role = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'TMAP Discovery completed: addr {addr} addr_type '
                  f'{addr_type} status {status}'
                  f'role {role}')

    tmap.event_received(defs.BTP_TMAP_EV_DISCOVERY_COMPLETED, (addr_type, addr, status, role))


TMAP_EV = {
    defs.BTP_TMAP_EV_DISCOVERY_COMPLETED: tmap_ev_discovery_completed,
}
