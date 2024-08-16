#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant.
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
    btp_hdr_check
from autopts.pybtp.types import addr2btp_ba, BTPError

log = logging.debug


BAS = {
	'read_supported_cmds': 	( defs.BTP_SERVICE_ID_HAS,
				  defs.BAS_READ_SUPPORTED_COMMANDS,
                             	  CONTROLLER_INDEX),
    	'remove_battery': 	( defs.BTP_SERVICE_ID_BAS,
                            	  defs.BAS_READ_SUPPORTED_COMMANDS,
                            	  CONTROLLER_INDEX),
}


def bas_command_rsp_succ(timeout=20.0):
    logging.debug("%s", bas_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_BAS)

    return tuple_data

def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data

def bas_remove_battery(index):
    logging.debug(f"{bas_remove_battery.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*BAS['set_active_index'], data=data)

    bas_command_rsp_succ()

