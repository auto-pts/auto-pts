#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba

log = logging.debug


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


GMAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_GMAP,
                            defs.GMAP_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_GMAP,
                 defs.GMAP_DISCOVER,
                 CONTROLLER_INDEX),
}


def gmap_command_rsp_succ(timeout=20.0):
    logging.debug("%s", gmap_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GMAP)

    return tuple_data


def gmap_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{gmap_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*GMAP['discover'], data=data)

    gmap_command_rsp_succ()

def gmap_ev_discovery_completed(tmap, data, data_len):
    logging.debug('%s %r', gmap_ev_discovery_completed.__name__, data)

    fmt = '<B6sBBBBBB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, gmap_role, ugg_features, ugt_features, bgs_features, bgr_features = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'GMAP Discovery completed: addr {addr} addr_type '
                  f'{addr_type} status {status}'
                  f'role {gmap_role}'
                  f'ugg_features {ugg_features}'
                  f'ugt_features {ugt_features}'
                  f'bgs_features {bgs_features}'
                  f'bgr_features {bgr_features}'
                  )

    tmap.event_received(defs.TMAP_EV_DISCOVERY_COMPLETED, (addr_type, addr, status, gmap_role, ugg_features, ugt_features, bgs_features, bgr_features))


GMAP_EV = {
    defs.GMAP_EV_DISCOVERY_COMPLETED: gmap_ev_discovery_completed,
}
