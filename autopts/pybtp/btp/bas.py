#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Demant A/S.
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
from autopts.pybtp.types import addr2btp_ba

BAS = {
    'set_battery_level':    (defs.BTP_SERVICE_ID_BAS,
                             defs.BAS_SET_BATTERY_LEVEL,
                             CONTROLLER_INDEX),
    'set_battery_present':  (defs.BTP_SERVICE_ID_BAS,
                             defs.BAS_SET_BATTERY_PRESENT,
                             CONTROLLER_INDEX),
    'set_charging_state':   (defs.BTP_SERVICE_ID_BAS,
                             defs.BAS_SET_BATTERY_CHARGE_STATE,
                             CONTROLLER_INDEX),
}


def bas_command_rsp_succ(op, timeout=20.0):
    logging.debug("%s", bas_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_BAS, op)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()

    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')

    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)

    return data


def bas_set_battery_level(battery_level):
    logging.debug("%s", bas_set_battery_level.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<B", battery_level))

    iutctl.btp_socket.send(*BAS['set_battery_level'], data=data)

    bas_command_rsp_succ(BAS['set_battery_level'])


def bas_set_battery_present(battery_present):
    logging.debug("%s", bas_set_battery_present.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<B", battery_present))

    iutctl.btp_socket.send(*BAS['set_battery_present'], data=data)

    bas_command_rsp_succ(BAS['set_battery_present'])


def bas_set_charging_state(state):
    logging.debug("%s", bas_set_charging_state.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<B", state))

    iutctl.btp_socket.send(*BAS['set_charging_state'], data=data)

    bas_command_rsp_succ(BAS['set_charging_state'])
