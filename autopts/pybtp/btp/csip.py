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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, \
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import addr2btp_ba, BTPError

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
    'set_coordinator_lock': (defs.BTP_SERVICE_ID_CSIP,
                             defs.CSIP_SET_COORDINATOR_LOCK,
                             CONTROLLER_INDEX),
    'set_coordinator_release': (defs.BTP_SERVICE_ID_CSIP,
                                defs.CSIP_SET_COORDINATOR_RELEASE,
                                CONTROLLER_INDEX),
}


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


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


def csip_set_coordinator_lock(count):
    logging.debug(f"{csip_set_coordinator_lock.__name__}")

    data = bytearray()
    data.extend(struct.pack('b', count))

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['set_coordinator_lock'], data=data)

    csip_command_rsp_succ()


def csip_set_coordinator_release(count):
    logging.debug(f"{csip_set_coordinator_release.__name__}")

    data = bytearray()
    data.extend(struct.pack('b', count))

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['set_coordinator_release'], data=data)

    csip_command_rsp_succ()


def csip_start_ordered_access(flags=0x00):
    logging.debug(f"{csip_start_ordered_access.__name__}")

    # RFU
    data = struct.pack('B', flags)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['start_ordered_access'], data=data)

    csip_command_rsp_succ()


def csip_ev_discovery_completed(csip, data, data_len):
    logging.debug('%s %r', csip_ev_discovery_completed.__name__, data)

    fmt = '<B6sbHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, sirk_handle, size_handle, lock_handle,\
        rank_handle = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'CSIP Discovery Completed: addr {addr},'
                  f' addr_type {addr_type},'
                  f' status {status}, Set Sirk Handle {sirk_handle},'
                  f' Set Size Handle {size_handle}, Set Lock Handle {lock_handle},'
                  f' Rank Handle {rank_handle}')

    csip.event_received(defs.CSIP_DISCOVERED_EV, (addr_type, addr, status,
                                                  sirk_handle, size_handle,
                                                  lock_handle, rank_handle))


def csip_sirk_ev(csip, data, data_len):
    logging.debug('%s %r', csip_sirk_ev.__name__, data)

    fmt = '<B6s'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')
    sirk_bytes = data[7:]
    sirk_hex = binascii.hexlify(sirk_bytes[::-1]).lower().decode('utf-8')

    logging.debug(f'CSIP Sirk event: addr {addr}, addr_type {addr_type},'
                  f' sirk {sirk_hex}')

    csip.event_received(defs.CSIP_SIRK_EV, (addr_type, addr, sirk_hex))


def csip_lock_ev(csip, data, data_len):
    logging.debug('%s %r', csip_lock_ev.__name__, data)

    fmt = '<b'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    lock_val = struct.unpack_from(fmt, data)

    logging.debug(f'CSIP Set Lock status {lock_val}')

    csip.event_received(defs.CSIP_LOCK_EV, lock_val)


CSIP_EV = {
    defs.CSIP_DISCOVERED_EV: csip_ev_discovery_completed,
    defs.CSIP_SIRK_EV: csip_sirk_ev,
    defs.CSIP_LOCK_EV: csip_lock_ev,
}
