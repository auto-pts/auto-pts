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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, CONTROLLER_INDEX_NONE, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut

log = logging.debug


OTS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_OTS,
                            defs.BTP_OTS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX_NONE),
    'register_object': (defs.BTP_SERVICE_ID_OTS,
                        defs.BTP_OTS_CMD_REGISTER_OBJECT,
                        CONTROLLER_INDEX),
}


def otc_register_object(index, name, flags=0, props=0, alloc_size=0, current_size=0):
    logging.debug(f"{otc_register_object.__name__}")

    data_ba = bytearray(struct.pack('<BIIIB', flags, props, alloc_size, current_size, len(name)))
    data_ba.extend(name.encode())

    iutctl = get_iut()
    iutctl.btp_socket.send(*OTS['register_object'], data=data_ba)

    ots_command_rsp_succ()


def ots_command_rsp_succ(timeout=20.0):
    logging.debug("%s", ots_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_OTS)

    return tuple_data

OTS_EV = {}
