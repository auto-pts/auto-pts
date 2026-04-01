import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.common import aics_btp
from autopts.pybtp.types import BTPError, addr_str_to_le_bytes, le_bytes_to_hex_str

AICS = aics_btp


def aics_command_rsp_succ(op=None):
    logging.debug("")

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_AICS, op)

    return tuple_data


def aics_mute(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute'], data=data)

    aics_command_rsp_succ()


def aics_unmute(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['unmute'], data=data)
    aics_command_rsp_succ()


def aics_auto_gain_set(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain'], data=data)
    aics_command_rsp_succ()


def aics_man_gain_set(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain'], data=data)
    aics_command_rsp_succ()


def aics_man_gain_only():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain_only'])
    aics_command_rsp_succ()


def aics_auto_gain_only():
    logging.debug("")

    data_ba = bytearray()
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain_only'])
    aics_command_rsp_succ()


def aics_change_desc(string):
    logging.debug("")

    iutctl = get_iut()
    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

    iutctl.btp_socket.send(*AICS['desc_set'], data=data)
    aics_command_rsp_succ()


def aics_state_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['aics_state'], data=data)

    aics_command_rsp_succ()


def aics_status_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['status'], data=data)

    aics_command_rsp_succ()


def aics_type_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['type'], data=data)

    aics_command_rsp_succ()


def aics_gain_setting_prop_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['gain_setting_prop'], data=data)

    aics_command_rsp_succ()


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def aics_set_gain(gain, bd_addr_type=None, bd_addr=None):
    logging.debug("%r", gain)

    iutctl = get_iut()

    if isinstance(gain, str):
        gain = int(gain)
    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("<b", gain))

    iutctl.btp_socket.send(*AICS['set_gain'], data=data)
    aics_command_rsp_succ()


def aics_mute_disable():
    logging.debug("")

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute_disable'])
    aics_command_rsp_succ()


def aics_description_get(bd_addr_type=None, bd_addr=None):
    logging.debug("")

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['description'], data=data)
    aics_command_rsp_succ()


def aics_state_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbBbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, gain, mute, mode = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("Audio Input Control State: addr %r, addr_type %r, att_status %r, gain %r, mute %r, mode %r",
                  addr, addr_type, att_status, gain, mute, mode)

    aics.event_received(defs.BTP_AICS_EV_STATE, (addr_type, addr, att_status, gain, mute, mode))


def aics_gain_setting_prop_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbbBB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, units, minimum, maximum = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("AICS Gain Setting Properties: addr %r, addr_type %r, units %r, minimum %r, maximum %r, att_status %r",
                  addr, addr_type, units, minimum, maximum, att_status)

    aics.event_received(defs.BTP_AICS_EV_GAIN_SETTING_PROP, (addr_type, addr, units,
                                                         minimum, maximum, att_status))


def aics_input_type_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, input_type, att_status = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("AICS Input type ev: addr %r, addr_type %r, input type %r, att_status %r",
                  addr, addr_type, input_type, att_status)

    aics.event_received(defs.BTP_AICS_EV_INPUT_TYPE, (addr_type, addr, input_type, att_status))


def aics_status_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, att_status = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("AICS Status ev: addr %r, addr_type %r, status %r, att_status %r",
                  addr, addr_type, status, att_status)

    aics.event_received(defs.BTP_AICS_EV_STATUS, (addr_type, addr, status, att_status))


def aics_description_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, att_status = struct.unpack_from(fmt, data)
    addr = le_bytes_to_hex_str(addr)

    description = struct.unpack_from(f'<{len(data) - fmt_size - 1}s', data, offset=fmt_size)
    description = binascii.hexlify(description[0]).decode('utf-8')

    logging.debug("AICS Description ev: addr %r, addr_type %r, att_status %r, description %r",
                  addr, addr_type, att_status, description)

    aics.event_received(defs.BTP_AICS_EV_DESCRIPTION, (addr_type, addr, att_status, description))


def aics_procedure_ev(aics, data, data_len):
    logging.debug('%r', data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, opcode = struct.unpack_from(fmt, data)

    addr = le_bytes_to_hex_str(addr)

    logging.debug("AICS Procedure ev: addr %r, addr_type %r, att status %r, opcode %r",
                  addr, addr_type, att_status, opcode)

    aics.event_received(defs.BTP_AICS_EV_PROCEDURE, (addr_type, addr, att_status, opcode))


AICS_EV = {
    defs.BTP_AICS_EV_STATE: aics_state_ev,
    defs.BTP_AICS_EV_GAIN_SETTING_PROP: aics_gain_setting_prop_ev,
    defs.BTP_AICS_EV_INPUT_TYPE: aics_input_type_ev,
    defs.BTP_AICS_EV_STATUS: aics_status_ev,
    defs.BTP_AICS_EV_DESCRIPTION: aics_description_ev,
    defs.BTP_AICS_EV_PROCEDURE: aics_procedure_ev,
}
