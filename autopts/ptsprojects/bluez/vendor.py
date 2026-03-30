#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Collabora Ltd.
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError

BTP_VENDOR_CMD_ASCS_SETUP = 0x02
BTP_VENDOR_EV_OPERATION_COMPLETED = 0x80

VENDOR = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_VENDOR,
                            defs.BTP_VENDOR_CMD_READ_SUPPORTED_COMMANDS,
                            defs.BTP_INDEX_NONE),
    'ascs_setup': (defs.BTP_SERVICE_ID_VENDOR, BTP_VENDOR_CMD_ASCS_SETUP, CONTROLLER_INDEX),
}


def vendor_command_rsp_succ(op=None, timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_VENDOR, op)

    return tuple_data


def vendor_ascs_setup(target_latency):
    logging.debug("")

    if not (0 <= target_latency <= 3):
        raise BTPError('Invalid target latency, must be between 0 and 3')

    data = struct.pack('B', target_latency)

    iutctl = get_iut()
    iutctl.btp_socket.send(*VENDOR['ascs_setup'], data=data)

    vendor_command_rsp_succ(BTP_VENDOR_CMD_ASCS_SETUP)
