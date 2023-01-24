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
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut,\
    btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import addr2btp_ba, BTPError

ASCS = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_ASCS,
                            defs.ASCS_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'config_codec': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_CONFIGURE_CODEC,
                     CONTROLLER_INDEX),
    'config_qos': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_CONFIGURE_QOS,
                   CONTROLLER_INDEX),
    'enable': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_ENABLE,
               CONTROLLER_INDEX),
    'start_ready': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_RECEIVER_START_READY,
                    CONTROLLER_INDEX),
    'stop_ready': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_RECEIVER_STOP_READY,
                   CONTROLLER_INDEX),
    'disable': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_DISABLE,
                CONTROLLER_INDEX),
    'release': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_RELEASE,
                CONTROLLER_INDEX),
    'update_metadata': (defs.BTP_SERVICE_ID_ASCS, defs.ASCS_UPDATE_METADATA,
                        CONTROLLER_INDEX),
}


def ascs_command_rsp_succ(timeout=20.0):
    logging.debug("%s", ascs_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_ASCS)

    return tuple_data


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def ascs_config_codec(ase_id, coding_format, sampling_freq, frame_duration,
                      audio_locations, octets_per_frame,
                      bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_config_codec.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', coding_format)
    data += struct.pack('B', sampling_freq)
    data += struct.pack('B', frame_duration)
    data += struct.pack('<I', audio_locations)
    data += struct.pack('<H', octets_per_frame)

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['config_codec'], data=data)

    ascs_command_rsp_succ()


def ascs_config_qos(ase_id, cig_id, cis_id, sdu_interval, framing, max_sdu,
                    retransmission_number, max_transport_latency,
                    bd_addr_type=None, bd_addr=None):

    logging.debug(f"{ascs_config_qos.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)
    data += struct.pack('B', cig_id)
    data += struct.pack('B', cis_id)
    data += struct.pack('<H', sdu_interval)
    data += struct.pack('B', framing)
    data += struct.pack('<H', max_sdu)
    data += struct.pack('B', retransmission_number)
    data += struct.pack('B', max_transport_latency)

    iutctl = get_iut()
    iutctl.btp_socket.send(*ASCS['config_qos'], data=data)

    ascs_command_rsp_succ()


def ascs_enable(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_enable.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['enable'], data=data)


def ascs_receiver_start_ready(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_receiver_start_ready.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['start_ready'], data=data)


def ascs_receiver_stop_ready(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_receiver_stop_ready.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['stop_ready'], data=data)


def ascs_disable(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_disable.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['disable'], data=data)


def ascs_release(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_release.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['release'], data=data)


def ascs_update_metadata(ase_id, bd_addr_type=None, bd_addr=None):
    logging.debug(f"{ascs_update_metadata.__name__}")

    data = address_to_ba(bd_addr_type, bd_addr)
    data += struct.pack('B', ase_id)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*ASCS['update_metadata'], data=data)


def ascs_ev_operation_completed_(ascs, data, data_len):
    logging.debug('%s %r', ascs_ev_operation_completed_.__name__, data)

    fmt = '<B6sBBBB'
    header_size = struct.calcsize(fmt)
    if len(data) < header_size:
        raise BTPError('Invalid data length')

    addr_type, addr, ase_id, opcode, status, flags = \
        struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'ASE operation completed event: addr {addr} addr_type '
                  f'{addr_type} ase_id {ase_id} opcode {opcode} '
                  f'status {status} flags {flags}')

    ascs.ascs_operation_complete_ev_recv((addr_type, addr, ase_id, opcode,
                                          status, flags))


ASCS_EV = {
    defs.ASCS_EV_OPERATION_COMPLETED: ascs_ev_operation_completed_,
}
