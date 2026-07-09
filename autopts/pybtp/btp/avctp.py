#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError

log = logging.debug


AVCTP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_AVCTP,
                            defs.BTP_AVCTP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
}


def avctp_command_rsp_succ(timeout=20.0):
    logging.debug("%s", avctp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_AVCTP)

    return tuple_data


# An example event, to be changed or deleted
def avctp_ev_dummy_completed(avctp, data, data_len):
    logging.debug('%s %r', avctp_ev_dummy_completed.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AVCTP Dummy event completed: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    avctp.event_received(defs.BTP_AVCTP_EV_DUMMY_COMPLETED, (addr_type, addr, status))


AVCTP_EV = {
    defs.BTP_AVCTP_EV_DUMMY_COMPLETED: avctp_ev_dummy_completed,
}
