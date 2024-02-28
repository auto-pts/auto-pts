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

from .btpdefs import defs
from .btp import CONTROLLER_INDEX, get_iut_method as get_iut, \
    btp_hdr_check, address_to_ba


log = logging.debug


CSIP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_CSIP,
                            defs.CSIP_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_CSIP, defs.CSIP_DISCOVER,
                 CONTROLLER_INDEX),
    'start_ordered_access': (defs.BTP_SERVICE_ID_CSIP,
                             defs.CSIP_START_ORDERED_ACCESS,
                             CONTROLLER_INDEX),
}


def csip_command_rsp_succ(timeout=20.0):
    logging.debug("%s", csip_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CSIP)

    return tuple_data


def csip_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{csip_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['discover'], data=data)

    csip_command_rsp_succ()


def csip_start_ordered_access(flags=0x00):
    logging.debug(f"{csip_start_ordered_access.__name__}")

    # RFU
    data = struct.pack('B', flags)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['start_ordered_access'], data=data)

    csip_command_rsp_succ()


CSIP_EV = {
}
