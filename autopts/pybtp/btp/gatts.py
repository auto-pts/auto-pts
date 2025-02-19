#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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
from autopts.pybtp.btp import dec_gatts_get_attrs_rp
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, \
    btp_hdr_check
from autopts.pybtp.types import BTPError, addr2btp_ba

log = logging.debug


GATTS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_GATTS,
                            defs.BTP_GATTS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'get_attrs': (defs.BTP_SERVICE_ID_GATTS, defs.BTP_GATTS_CMD_GET_ATTRIBUTES,
                  CONTROLLER_INDEX),
    'get_attr_val': (defs.BTP_SERVICE_ID_GATTS,
                     defs.BTP_GATTS_CMD_GET_ATTRIBUTE_VALUE, CONTROLLER_INDEX),
    'set_values': (defs.BTP_SERVICE_ID_GATTS,
                   defs.BTP_GATTS_CMD_SET_VALUES, CONTROLLER_INDEX),
    'change_database': (defs.BTP_SERVICE_ID_GATTS,
                        defs.BTP_GATTS_CMD_CHANGE_DATABASE, CONTROLLER_INDEX),
}


def gatts_command_rsp_succ(timeout=20.0):
    logging.debug("%s", gatts_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATTS)

    return tuple_data


def gatts_get_attrs(start_handle=0x0001, end_handle=0xffff, type_uuid=None):
    logging.debug("%s %r %r %r", gatts_get_attrs.__name__, start_handle,
                  end_handle, type_uuid)

    iutctl = get_iut()

    data_ba = bytearray()

    if isinstance(start_handle, str):
        start_handle = int(start_handle, 16)

    start_hdl_ba = struct.pack('H', start_handle)
    data_ba.extend(start_hdl_ba)

    if isinstance(end_handle, str):
        end_handle = int(end_handle, 16)

    end_hdl_ba = struct.pack('H', end_handle)
    data_ba.extend(end_hdl_ba)

    if type_uuid:
        uuid_ba = bytes.fromhex(type_uuid.replace("-", ""))
        # uuid_ba has bytes in reverse order, must bew swapped
        uuid_ba = uuid_ba[::-1]
        data_ba.extend(chr(len(uuid_ba)).encode('utf-8'))
        data_ba.extend(uuid_ba)
    else:
        data_ba.extend(chr(0).encode('utf-8'))

    iutctl.btp_socket.send(*GATTS['get_attrs'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.BTP_GATT_CMD_GET_ATTRIBUTES)

    return dec_gatts_get_attrs_rp(tuple_data[0], tuple_hdr.data_len)


def gatts_get_attr_val(bd_addr_type, bd_addr, handle):
    logging.debug("%s %r", gatts_get_attr_val.__name__, handle)

    iutctl = get_iut()

    data_ba = bytearray()

    bd_addr_ba = addr2btp_ba(bd_addr)
    if isinstance(handle, str):
        handle = int(handle, 16)

    hdl_ba = struct.pack('H', handle)

    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    iutctl.btp_socket.send(*GATTS['get_attr_val'], data=data_ba)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_GATT,
                  defs.BTP_GATT_CMD_GET_ATTRIBUTE_VALUE)

    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)
    data_len = tuple_hdr.data_len - hdr_len

    return struct.unpack(hdr + '%ds' % data_len, tuple_data[0])


def gatts_set_val(bd_addr_type, bd_addr, hdl=[], values=()):
    logging.debug("%s %r %r ", gatts_set_val.__name__, hdl, values)

    iutctl = get_iut()
    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(bd_addr)

    # addr
    data_ba.extend(chr(bd_addr_type).encode('utf-8'))
    data_ba.extend(bd_addr_ba)
    # count
    data_ba.extend(struct.pack('H', len(hdl)))
    for i, handle in enumerate(hdl):
        if isinstance(hdl, str):
            handle = int(hdl, 16)
        data_ba.extend(struct.pack('H', handle))
        data_ba.extend(struct.pack('H', len(values[i])))

    for val in values:
        if isinstance(val, str):
            val_ba = binascii.unhexlify(bytearray(val, 'utf-8'))
        elif isinstance(val, bytes):
            val_ba = val
        else:
            val_ba = binascii.unhexlify(bytearray(val.encode('utf-8')))

        data_ba.extend(val_ba)

    iutctl.btp_socket.send(*GATTS['set_values'], data=data_ba)

    gatts_command_rsp_succ()


def gatts_change_database(start_hdl, end_hdl, vis):
    logging.debug("%s %r %r %r", gatts_change_database.__name__, start_hdl, end_hdl, vis)

    iutctl = get_iut()

    if isinstance(start_hdl, str):
        start_hdl = int(start_hdl, 16)

    if isinstance(end_hdl, str):
        end_hdl = int(end_hdl, 16)

    data_ba = bytearray()
    start_hdl_ba = struct.pack('H', start_hdl)
    end_hdl_ba = struct.pack('H', end_hdl)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(end_hdl_ba)
    data_ba.extend(chr(vis).encode('utf-8'))

    iutctl.btp_socket.send(*GATTS['change_database'], data=data_ba)

    gatts_command_rsp_succ()


def gatts_attr_value_changed_ev(gatts, data, data_len):
    logging.debug('%s %r', gatts_attr_value_changed_ev.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    status = struct.unpack_from(fmt, data)

    logging.debug(f'GATTS Attr Value changed ev: status {status}')

    gatts.event_received(defs.BTP_GATTS_EV_ATTR_VALUE_CHANGED, (status))


GATTS_EV = {
    defs.BTP_GATTS_EV_ATTR_VALUE_CHANGED: gatts_attr_value_changed_ev,
}
