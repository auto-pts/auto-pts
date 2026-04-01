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
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes, le_bytes_to_hex_str

ASCS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_ASCS,
                            defs.BTP_ASCS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'config_codec': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_CONFIGURE_CODEC,
                     CONTROLLER_INDEX),
    'config_qos': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_CONFIGURE_QOS,
                   CONTROLLER_INDEX),
    'enable': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_ENABLE,
               CONTROLLER_INDEX),
    'start_ready': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_RECEIVER_START_READY,
                    CONTROLLER_INDEX),
    'stop_ready': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_RECEIVER_STOP_READY,
                   CONTROLLER_INDEX),
    'disable': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_DISABLE,
                CONTROLLER_INDEX),
    'release': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_RELEASE,
                CONTROLLER_INDEX),
    'update_metadata': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_UPDATE_METADATA,
                        CONTROLLER_INDEX),
    'add_ase_to_cis': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_ADD_ASE_TO_CIS,
                       CONTROLLER_INDEX),
    'preconfig_qos': (defs.BTP_SERVICE_ID_ASCS, defs.BTP_ASCS_CMD_PRECONFIG_QOS,
                      CONTROLLER_INDEX),
}


def ascs_command_rsp_succ(timeout=20.0):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_ASCS)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def ascs_config_codec(ase_id, coding_format, vid, cid, codec_ltvs,
                      bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', coding_format)
    data += struct.pack('<H', vid)
    data += struct.pack('<H', cid)

    codec_ltvs_len = len(codec_ltvs)
    data += struct.pack('B', codec_ltvs_len)

    if codec_ltvs_len:
        data += codec_ltvs

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['config_codec'], data=data)

    ascs_command_rsp_succ()


def ascs_add_ase_to_cis(ase_id, cis_id, cig_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', cig_id)
    data += struct.pack('B', cis_id)

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['add_ase_to_cis'], data=data)

    ascs_command_rsp_succ()


def ascs_config_qos(ase_id, cig_id, cis_id, sdu_interval, framing, max_sdu,
                    retransmission_number, max_transport_latency,
                    presentation_delay, bd_addr_type=None, bd_addr=None):

    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', cig_id)
    data += struct.pack('B', cis_id)
    data += int.to_bytes(sdu_interval, 3, 'little')
    data += struct.pack('B', framing)
    data += struct.pack('<H', max_sdu)
    data += struct.pack('B', retransmission_number)
    data += struct.pack('<H', max_transport_latency)
    data += int.to_bytes(presentation_delay, 3, 'little')

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['config_qos'], data=data)

    ascs_command_rsp_succ()


def ascs_enable(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['enable'], data=data)


def ascs_receiver_start_ready(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['start_ready'], data=data)


def ascs_receiver_stop_ready(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['stop_ready'], data=data)


def ascs_disable(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['disable'], data=data)


def ascs_release(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['release'], data=data)


def ascs_update_metadata(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['update_metadata'], data=data)


def ascs_preconfig_qos(cig_id, cis_id, sdu_interval, framing, max_sdu,
                       retransmission_number, max_transport_latency,
                       presentation_delay):
    logging.debug("")

    data = bytearray()
    data += struct.pack('B', cig_id)
    data += struct.pack('B', cis_id)
    data += int.to_bytes(sdu_interval, 3, 'little')
    data += struct.pack('B', framing)
    data += struct.pack('<H', max_sdu)
    data += struct.pack('B', retransmission_number)
    data += struct.pack('<H', max_transport_latency)
    data += int.to_bytes(presentation_delay, 3, 'little')

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['preconfig_qos'], data=data)

    ascs_command_rsp_succ()


def ascs_ev_operation_completed_(ascs, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sBBBB'
    header_size = struct.calcsize(fmt)
    if len(data) < header_size:
        raise BTPError('Invalid data length')

    addr_type, addr, ase_id, opcode, status, flags = \
        struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("ASE operation completed event: addr %r, addr_type %r, ase_id %r, opcode %r, status %r, flags %r",
                  addr, addr_type, ase_id, opcode, status, flags)

    ascs.event_received(defs.BTP_ASCS_EV_OPERATION_COMPLETED,
                        (addr_type, addr, ase_id, opcode, status, flags))


def ascs_ev_characteristic_subscribed_(ascs, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sB'
    header_size = struct.calcsize(fmt)
    if len(data) < header_size:
        raise BTPError('Invalid data length')

    addr_type, addr, handle = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("ASCS characteristic with handle %r subscribed", handle)

    ascs.event_received(defs.BTP_ASCS_EV_CHARACTERISTIC_SUBSCRIBED,
                        (addr_type, addr, handle))


def ascs_ev_ase_state_changed_(ascs, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sBB'
    header_size = struct.calcsize(fmt)
    if len(data) < header_size:
        raise BTPError('Invalid data length')

    addr_type, addr, ase_id, state = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("ASE state: ase_id %r, state %r", ase_id, state)

    ascs.event_received(defs.BTP_ASCS_EV_ASE_STATE_CHANGED,
                        (addr_type, addr, ase_id, state))


def ascs_ev_cis_connected_(ascs, data, data_len):
    logging.debug("%r", data)

    fmt = "<B6sBB"
    header_size = struct.calcsize(fmt)
    if len(data) != header_size:
        raise BTPError(f"Invalid data length ({len(data)} != {header_size})")

    addr_type, addr, ase_id, cis_id = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("CIS connected: ase_id %r, cis_id %r", ase_id, cis_id)

    ascs.event_received(defs.BTP_ASCS_EV_CIS_CONNECTED, (addr_type, addr, ase_id, cis_id))


def ascs_ev_cis_disconnected_(ascs, data, data_len):
    logging.debug("%r", data)

    fmt = "<B6sBBB"
    header_size = struct.calcsize(fmt)
    if len(data) != header_size:
        raise BTPError(f"Invalid data length ({len(data)} != {header_size})")

    addr_type, addr, ase_id, cis_id, reason = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("CIS disconnected: ase_id %r, cis_id %r, reason %r", ase_id, cis_id, reason)

    ascs.event_received(
        defs.BTP_ASCS_EV_CIS_DISCONNECTED, (addr_type, addr, ase_id, cis_id, reason)
    )


ASCS_EV = {
    defs.BTP_ASCS_EV_OPERATION_COMPLETED: ascs_ev_operation_completed_,
    defs.BTP_ASCS_EV_CHARACTERISTIC_SUBSCRIBED: ascs_ev_characteristic_subscribed_,
    defs.BTP_ASCS_EV_ASE_STATE_CHANGED: ascs_ev_ase_state_changed_,
    defs.BTP_ASCS_EV_CIS_CONNECTED: ascs_ev_cis_connected_,
    defs.BTP_ASCS_EV_CIS_DISCONNECTED: ascs_ev_cis_disconnected_,
}
