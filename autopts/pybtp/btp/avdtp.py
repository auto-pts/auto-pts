#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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


AVDTP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_AVDTP,
                            defs.BTP_AVDTP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
}


def avdtp_command_rsp_succ(timeout=20.0):
    logging.debug("%s", avdtp_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_AVDTP)

    return tuple_data


# An example event, to be changed or deleted
def avdtp_ev_dummy_completed(avdtp, data, data_len):
    logging.debug('%s %r', avdtp_ev_dummy_completed.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AVDTP Dummy event completed: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    avdtp.event_received(defs.BTP_AVDTP_EV_DUMMY_COMPLETED, (addr_type, addr, status))


AVDTP_EV = {
    defs.BTP_AVDTP_EV_DUMMY_COMPLETED: avdtp_ev_dummy_completed,
}
