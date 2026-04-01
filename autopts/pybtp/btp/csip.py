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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes, le_bytes_to_hex_str

log = logging.debug


CSIP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_CSIP,
                            defs.BTP_CSIP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'discover': (defs.BTP_SERVICE_ID_CSIP, defs.BTP_CSIP_CMD_DISCOVER,
                 CONTROLLER_INDEX),
    'start_ordered_access': (defs.BTP_SERVICE_ID_CSIP,
                             defs.BTP_CSIP_CMD_START_ORDERED_ACCESS,
                             CONTROLLER_INDEX),
    'set_coordinator_lock': (defs.BTP_SERVICE_ID_CSIP,
                             defs.BTP_CSIP_CMD_SET_COORDINATOR_LOCK,
                             CONTROLLER_INDEX),
    'set_coordinator_release': (defs.BTP_SERVICE_ID_CSIP,
                                defs.BTP_CSIP_CMD_SET_COORDINATOR_RELEASE,
                                CONTROLLER_INDEX),
}


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def csip_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CSIP)

    return tuple_data


def csip_discover(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['discover'], data=data)

    csip_command_rsp_succ()


def csip_set_coordinator_lock(addr_list=None):
    logging.debug("")

    iutctl = get_iut()
    data = bytearray()
    addr_cnt = len(addr_list) if addr_list else 0

    data.extend(struct.pack('b', addr_cnt))

    if addr_cnt != 0:
        # Perform lock request procedure on subset of set members
        for addr_type, addr in addr_list:
            bd_addr_type_ba = chr(addr_type).encode('utf-8')
            bd_addr_ba = addr_str_to_le_bytes(addr)
            data.extend(bd_addr_type_ba)
            data.extend(bd_addr_ba)

    iutctl.btp_socket.send(*CSIP['set_coordinator_lock'], data=data)

    csip_command_rsp_succ()


def csip_set_coordinator_release(addr_list=None):
    logging.debug("")

    iutctl = get_iut()
    data = bytearray()
    addr_cnt = len(addr_list) if addr_list else 0

    data.extend(struct.pack('b', addr_cnt))

    if addr_cnt != 0:
        # Perform lock release procedure on subset of set members
        for addr_type, addr in addr_list:
            bd_addr_type_ba = chr(addr_type).encode('utf-8')
            bd_addr_ba = addr_str_to_le_bytes(addr)
            data.extend(bd_addr_type_ba)
            data.extend(bd_addr_ba)

    iutctl.btp_socket.send(*CSIP['set_coordinator_release'], data=data)

    csip_command_rsp_succ()


def csip_start_ordered_access(flags=0x00):
    logging.debug("")

    # RFU
    data = struct.pack('B', flags)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CSIP['start_ordered_access'], data=data)

    csip_command_rsp_succ()


def csip_ev_discovery_completed(csip, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbHHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, sirk_handle, size_handle, lock_handle,\
        rank_handle = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)

    logging.debug(
        "CSIP Discovery Completed: addr %r, addr_type %r, status %r, Set Sirk Handle %r,"
        "Set Size Handle %r, Set Lock Handle %r, Rank Handle %r",
        addr, addr_type, status, sirk_handle, size_handle, lock_handle, rank_handle)

    csip.event_received(defs.BTP_CSIP_EV_DISCOVERED, (addr_type, addr, status,
                                                  sirk_handle, size_handle,
                                                  lock_handle, rank_handle))


def csip_sirk_ev(csip, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6s'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)
    sirk_bytes = data[7:]
    sirk_hex = le_bytes_to_hex_str(sirk_bytes)

    logging.debug("CSIP Sirk event: addr %r, addr_type %r, sirk %r", addr, addr_type, sirk_hex)

    csip.event_received(defs.BTP_CSIP_EV_SIRK, (addr_type, addr, sirk_hex))


def csip_lock_ev(csip, data, data_len):
    logging.debug('%r', data)

    fmt = '<b'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    lock_val = struct.unpack_from(fmt, data)

    logging.debug("CSIP Set Lock status %r", lock_val)

    csip.event_received(defs.BTP_CSIP_EV_LOCK, lock_val)


CSIP_EV = {
    defs.BTP_CSIP_EV_DISCOVERED: csip_ev_discovery_completed,
    defs.BTP_CSIP_EV_SIRK: csip_sirk_ev,
    defs.BTP_CSIP_EV_LOCK: csip_lock_ev,
}
