#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

from .btpdefs import defs
from .btp import get_iut_method as get_iut
from .btp import CONTROLLER_INDEX, btp_hdr_check
from .btpdefs.types import BTPError


HAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_HAP,
                            defs.HAP_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'ha_init': (defs.BTP_SERVICE_ID_HAP,
                defs.HAP_HA_INIT,
                CONTROLLER_INDEX),
    'harc_init': (defs.BTP_SERVICE_ID_HAP,
                  defs.HAP_HARC_INIT,
                  CONTROLLER_INDEX, ""),
    'hauc_init': (defs.BTP_SERVICE_ID_HAP,
                  defs.HAP_HAUC_INIT,
                  CONTROLLER_INDEX, ""),
    'iac_init': (defs.BTP_SERVICE_ID_HAP,
                 defs.HAP_IAC_INIT,
                 CONTROLLER_INDEX, ""),
    'iac_discover': (defs.BTP_SERVICE_ID_HAP,
                     defs.HAP_IAC_DISCOVER,
                     CONTROLLER_INDEX),
    'iac_set_alert': (defs.BTP_SERVICE_ID_HAP,
                      defs.HAP_IAC_SET_ALERT,
                      CONTROLLER_INDEX),
    'hauc_discover': (defs.BTP_SERVICE_ID_HAP,
                      defs.HAP_HAUC_DISCOVER,
                      CONTROLLER_INDEX),
}

def hap_command_rsp_succ(timeout=20.0, exp_op=None):
    logging.debug(f"{hap_command_rsp_succ.__name__}")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_HAP, exp_op)
    return tuple_data

def hap_read_supported_cmds():
    logging.debug(f"{hap_read_supported_cmds.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['read_supported_cmds'])

    tuple_data = hap_command_rsp_succ()
    logging.debug("supported cmds %r", tuple_data)

def hap_ha_init(type, options):
    logging.debug(f"{hap_ha_init.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', type)
    data += struct.pack('<H', options)

    iutctl.btp_socket.send(*HAP['ha_init'], data=data)

    hap_command_rsp_succ()

def hap_harc_init():
    logging.debug(f"{hap_harc_init.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['harc_init'])

    hap_command_rsp_succ()

def hap_hauc_init():
    logging.debug(f"{hap_hauc_init.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hauc_init'])

    hap_command_rsp_succ()

def hap_iac_init():
    logging.debug(f"{hap_iac_init.__name__}")

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['iac_init'])

    hap_command_rsp_succ()

def hap_iac_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_iac_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['iac_discover'], data=data)

    hap_command_rsp_succ()

def hap_iac_set_alert(bd_addr_type=None, bd_addr=None, alert=None):
    logging.debug(f"{hap_iac_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', alert)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['iac_set_alert'], data=data)

    hap_command_rsp_succ()

def hap_hauc_discover(bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_hauc_discover.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hauc_discover'], data=data)

    hap_command_rsp_succ()

def hap_ev_iac_discovery_complete_(hap, data, data_len):
    logging.debug("%s %r", hap_ev_iac_discovery_complete_.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'IAC Discovery complete: addr {addr} addr_type '
                  f'{addr_type} status {status}')

    hap.event_received(defs.HAP_EV_IAC_DISCOVERY_COMPLETE, (addr_type, addr, status))

def hap_ev_hauc_discovery_complete_(hap, data, data_len):
    logging.debug("%s %r", hap_ev_hauc_discovery_complete_.__name__, data)

    fmt = '<B6sBBHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    (addr_type, addr, status, type, hearing_aid_features_handle,
     hearing_aid_control_point_handle, active_preset_index_handle) = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'HAUC Discovery complete: addr {addr} addr_type {addr_type} '
                  f'status {status} type {type} '
                  f'has_hearing_aid_features_handle {hearing_aid_features_handle} '
                  f'has_control_point_handle {hearing_aid_control_point_handle} '
                  f'has_active_preset_index_handle {active_preset_index_handle}')

    hap.event_received(defs.HAP_EV_HAUC_DISCOVERY_COMPLETE, (addr_type, addr, status,
                                                             hearing_aid_features_handle,
                                                             hearing_aid_control_point_handle,
                                                             active_preset_index_handle))

HAP_EV = {
    defs.HAP_EV_IAC_DISCOVERY_COMPLETE: hap_ev_iac_discovery_complete_,
    defs.HAP_EV_HAUC_DISCOVERY_COMPLETE: hap_ev_hauc_discovery_complete_,
}
