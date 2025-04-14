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

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr2btp_ba


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


HAP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_HAP,
                            defs.BTP_HAP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    'ha_init': (defs.BTP_SERVICE_ID_HAP,
                defs.BTP_HAP_CMD_HA_INIT,
                CONTROLLER_INDEX),
    'harc_init': (defs.BTP_SERVICE_ID_HAP,
                  defs.BTP_HAP_CMD_HARC_INIT,
                  CONTROLLER_INDEX, ""),
    'hauc_init': (defs.BTP_SERVICE_ID_HAP,
                  defs.BTP_HAP_CMD_HAUC_INIT,
                  CONTROLLER_INDEX, ""),
    'iac_init': (defs.BTP_SERVICE_ID_HAP,
                 defs.BTP_HAP_CMD_IAC_INIT,
                 CONTROLLER_INDEX, ""),
    'iac_discover': (defs.BTP_SERVICE_ID_HAP,
                     defs.BTP_HAP_CMD_IAC_DISCOVER,
                     CONTROLLER_INDEX),
    'iac_set_alert': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_IAC_SET_ALERT,
                      CONTROLLER_INDEX),
    'hauc_discover': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_HAUC_DISCOVER,
                      CONTROLLER_INDEX),
    'hap_read_presets': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_READ_PRESETS,
                      CONTROLLER_INDEX),
    'hap_write_preset_name': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_WRITE_PRESET_NAME,
                      CONTROLLER_INDEX),
    'hap_set_active_preset': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_SET_ACTIVE_PRESET,
                      CONTROLLER_INDEX),
    'hap_set_next_preset': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_SET_NEXT_PRESET,
                      CONTROLLER_INDEX),
    'hap_set_previous_preset': (defs.BTP_SERVICE_ID_HAP,
                      defs.BTP_HAP_CMD_SET_PREVIOUS_PRESET,
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


def hap_ha_init(hap_type, options):
    logging.debug(f"{hap_ha_init.__name__}")

    iutctl = get_iut()
    data = bytearray()
    data += struct.pack('B', hap_type)
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
    logging.debug(f"{hap_iac_set_alert.__name__}")

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


def hap_read_presets(start_index, num_presets, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_read_presets.__name__}, start_index {start_index}, num_presets {num_presets}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', start_index)
    data += struct.pack('B', num_presets)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hap_read_presets'], data=data)

    hap_command_rsp_succ()


def hap_write_preset_name(index, name, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_write_preset_name.__name__}, index {index}, name {name}")
    encoded_name = name.encode()
    size = len(encoded_name)

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', index)
    data += struct.pack('B', size)
    data += encoded_name

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hap_write_preset_name'], data=data)

    hap_command_rsp_succ()


def hap_set_active_preset(index, synchronize_locally=0, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_set_active_preset.__name__}, index {index}, synchronize_locally {synchronize_locally}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', index)
    data += struct.pack('B', synchronize_locally)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hap_set_active_preset'], data=data)

    hap_command_rsp_succ()


def hap_set_next_preset(synchronize_locally=0, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_set_next_preset.__name__}, synchronize_locally {synchronize_locally}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', synchronize_locally)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hap_set_next_preset'], data=data)

    hap_command_rsp_succ()


def hap_set_previous_preset(synchronize_locally=0, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{hap_set_previous_preset.__name__}, synchronize_locally {synchronize_locally}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', synchronize_locally)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HAP['hap_set_previous_preset'], data=data)

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

    hap.event_received(defs.BTP_HAP_EV_IAC_DISCOVERY_COMPLETE, (addr_type, addr, status))


def hap_ev_hauc_discovery_complete_(hap, data, data_len):
    logging.debug("%s %r", hap_ev_hauc_discovery_complete_.__name__, data)

    fmt = '<B6sbHHH'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, hearing_aid_features_handle, \
        hearing_aid_control_point_handle, \
        active_preset_index_handle = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'HAUC Discovery complete: addr {addr} addr_type {addr_type} '
                  f'status {status} '
                  f'has_hearing_aid_features_handle {hearing_aid_features_handle} '
                  f'has_control_point_handle {hearing_aid_control_point_handle} '
                  f'has_active_preset_index_handle {active_preset_index_handle}')

    hap.event_received(defs.BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE, (addr_type, addr, status,
                                                             hearing_aid_features_handle,
                                                             hearing_aid_control_point_handle,
                                                             active_preset_index_handle))


def hap_ev_preset_changed_(hap, data, data_len):
    logging.debug("%s %r", hap_ev_preset_changed_.__name__, data)

    fmt = '<B6sBBBBBB'
    fixed_size = struct.calcsize(fmt)
    if len(data) < fixed_size:
        raise BTPError('Invalid data length')

    addr_type, addr, change_id, is_last, preset_index, prev_index, \
            properties, name_len = struct.unpack_from(fmt, data)
    name = data[fixed_size:].decode('utf-8')
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'Preset Changed: addr {addr} addr_type {addr_type} '
                  f'change_id {change_id} '
                  f'is_last {is_last} '
                  f'preset_index {preset_index} '
                  f'prev_index {prev_index}'
                  f'prev_index {properties}'
                  f'name {name}')

    hap.event_received(defs.BTP_HAP_EV_PRESET_READ, (addr_type, addr, change_id,
                                                is_last, preset_index,
                                                prev_index, properties, name))


HAP_EV = {
    defs.BTP_HAP_EV_IAC_DISCOVERY_COMPLETE: hap_ev_iac_discovery_complete_,
    defs.BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE: hap_ev_hauc_discovery_complete_,
    defs.BTP_HAP_EV_PRESET_CHANGED: hap_ev_preset_changed_,
}
