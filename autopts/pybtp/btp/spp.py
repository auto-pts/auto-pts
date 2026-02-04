#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026, NXP.
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

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.pybtp.types import addr2btp_ba

SPP = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_SPP,
                       defs.BTP_SPP_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "discover": (defs.BTP_SERVICE_ID_SPP,
                 defs.BTP_SPP_CMD_DISCOVER,
                 CONTROLLER_INDEX),
    "register_server": (defs.BTP_SERVICE_ID_SPP,
                        defs.BTP_SPP_CMD_REGISTER_SERVER,
                        CONTROLLER_INDEX),
}

def spp_command_rsp_succ(op=None):
    logging.debug("%s", spp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_SPP, op)

def spp_discover(bd_addr_type=None, bd_addr=None):
    """
    Discover SPP services on the remote device.
    """
    logging.debug("%s %r %r", spp_discover.__name__, bd_addr_type, bd_addr)

    if bd_addr_type is None:
        bd_addr_type = pts_addr_type_get()
    if bd_addr is None:
        bd_addr = pts_addr_get()

    gap_wait_for_connection()

    data = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)
    data.extend([bd_addr_type])
    data.extend(bd_addr_ba)

    iutctl = get_iut()
    iutctl.btp_socket.send(*SPP['discover'], data=data)

    spp_command_rsp_succ(defs.BTP_SPP_CMD_DISCOVER)

def spp_register_server(channel):
    """
    Register SPP server on the specified RFCOMM channel.

    :param channel: RFCOMM channel number (1-31)
    """
    logging.debug("%s channel=%d", spp_register_server.__name__, channel)

    data = bytearray(struct.pack('B', channel))

    iutctl = get_iut()
    iutctl.btp_socket.send(*SPP['register_server'], data=data)

    spp_command_rsp_succ(defs.BTP_SPP_CMD_REGISTER_SERVER)

def spp_ev_discovered(spp, data, data_len):
    """Decode SPP Discovered Event.

    BTP SPP Discovered Event format:
    0        6      7
    +--------+---------+
    | Addr   | Channel |
    | (6B)   | (1B)    |
    +--------+---------+

    """
    logging.debug("%s %r", spp_ev_discovered.__name__, data)

    fmt = '<6sB'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for SPP Discovered Event")

    addr, channel = struct.unpack(fmt, data)
    addr = binascii.hexlify(addr[::-1]).decode('utf-8').upper()

    logging.debug("SPP Discovered: addr=%s, channel=%d",
                  addr, channel)

    spp.discovered_channel = channel
    spp.discovered_addr = addr
    spp.discovered_addr_type = defs.BTP_BR_ADDRESS_TYPE
    spp.set_discovered()
    return True

SPP_EV = {
    defs.BTP_SPP_EV_DISCOVERED: spp_ev_discovered,
}
