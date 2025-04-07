import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get
from autopts.pybtp.types import BTPError, addr2btp_ba


AICS = {
    "read_supported_cmds": (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX, ""),
    "set_gain":            (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_SET_GAIN,
                            CONTROLLER_INDEX),
    "mute":                (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_MUTE,
                            CONTROLLER_INDEX),
    "unmute":              (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_UNMUTE,
                            CONTROLLER_INDEX),
    "auto_gain":           (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_AUTO_GAIN_SET,
                            CONTROLLER_INDEX),
    "man_gain":            (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_MAN_GAIN_SET,
                            CONTROLLER_INDEX),
    "man_gain_only":       (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_SET_MAN_GAIN_ONLY,
                            CONTROLLER_INDEX, ""),
    "auto_gain_only":      (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_SET_AUTO_GAIN_ONLY,
                            CONTROLLER_INDEX, ""),
    "desc_set":            (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_AUDIO_DESC_SET,
                            CONTROLLER_INDEX),
    "mute_disable":        (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_MUTE_DISABLE,
                            CONTROLLER_INDEX, ""),
    "aics_state":          (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_STATE_GET,
                            CONTROLLER_INDEX),
    "status":              (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_STATUS_GET,
                            CONTROLLER_INDEX),
    "type":                (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_TYPE_GET,
                            CONTROLLER_INDEX),
    "gain_setting_prop":   (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_GAIN_SETTING_PROP_GET,
                            CONTROLLER_INDEX),
    "description":         (defs.BTP_SERVICE_ID_AICS,
                            defs.BTP_AICS_CMD_DESCRIPTION_GET,
                            CONTROLLER_INDEX)
}


def aics_command_rsp_succ(op=None):
    logging.debug("%s", aics_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_AICS, op)

    return tuple_data


def aics_mute(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_mute.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute'], data=data)

    aics_command_rsp_succ()


def aics_unmute(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_unmute.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['unmute'], data=data)
    aics_command_rsp_succ()


def aics_auto_gain_set(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_auto_gain_set.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain'], data=data)
    aics_command_rsp_succ()


def aics_man_gain_set(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_man_gain_set.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain'], data=data)
    aics_command_rsp_succ()


def aics_man_gain_only():
    logging.debug("%s", aics_man_gain_only.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['man_gain_only'])
    aics_command_rsp_succ()


def aics_auto_gain_only():
    logging.debug("%s", aics_auto_gain_only.__name__)

    data_ba = bytearray()
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['auto_gain_only'])
    aics_command_rsp_succ()


def aics_change_desc(string):
    logging.debug("%s", aics_change_desc.__name__)

    iutctl = get_iut()
    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

    iutctl.btp_socket.send(*AICS['desc_set'], data=data)
    aics_command_rsp_succ()


def aics_state_get(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_state_get.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['aics_state'], data=data)

    aics_command_rsp_succ()


def aics_status_get(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_status_get.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['status'], data=data)

    aics_command_rsp_succ()


def aics_type_get(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_type_get.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['type'], data=data)

    aics_command_rsp_succ()


def aics_gain_setting_prop_get(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_gain_setting_prop_get.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['gain_setting_prop'], data=data)

    aics_command_rsp_succ()


def address_to_ba(bd_addr_type=None, bd_addr=None):
    data = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def aics_set_gain(gain, bd_addr_type=None, bd_addr=None):
    logging.debug("%s %r", aics_set_gain.__name__, gain)

    iutctl = get_iut()

    if isinstance(gain, str):
        gain = int(gain)
    data = address_to_ba(bd_addr_type, bd_addr)
    data.extend(struct.pack("<b", gain))

    iutctl.btp_socket.send(*AICS['set_gain'], data=data)
    aics_command_rsp_succ()


def aics_mute_disable():
    logging.debug("%s", aics_mute_disable.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['mute_disable'])
    aics_command_rsp_succ()


def aics_description_get(bd_addr_type=None, bd_addr=None):
    logging.debug("%s", aics_description_get.__name__)

    data = address_to_ba(bd_addr_type, bd_addr)
    iutctl = get_iut()

    iutctl.btp_socket.send(*AICS['description'], data=data)
    aics_command_rsp_succ()


def aics_state_ev(aics, data, data_len):
    logging.debug('%s %r', aics_state_ev.__name__, data)

    fmt = '<B6sbBbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, gain, mute, mode = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'Audio Input Control State: addr {addr} addr_type '
                  f'{addr_type}, att_status {att_status}, gain {gain}, mute {mute}, mode {mode}')

    aics.event_received(defs.BTP_AICS_EV_STATE, (addr_type, addr, att_status, gain, mute, mode))


def aics_gain_setting_prop_ev(aics, data, data_len):
    logging.debug('%s %r', aics_gain_setting_prop_ev.__name__, data)

    fmt = '<B6sbbBB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, units, minimum, maximum = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AICS Gain Setting Properties: addr {addr} addr_type '
                  f'{addr_type}, units {units}, minimum {minimum}, maximum {maximum},'
                  f' att_status {att_status}')

    aics.event_received(defs.BTP_AICS_EV_GAIN_SETTING_PROP, (addr_type, addr, units,
                                                         minimum, maximum, att_status))


def aics_input_type_ev(aics, data, data_len):
    logging.debug('%s %r', aics_input_type_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, input_type, att_status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AICS Input type ev: addr {addr} addr_type '
                  f'{addr_type}, input type {input_type}, att_status {att_status}')

    aics.event_received(defs.BTP_AICS_EV_INPUT_TYPE, (addr_type, addr, input_type, att_status))


def aics_status_ev(aics, data, data_len):
    logging.debug('%s %r', aics_status_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status, att_status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AICS Status ev: addr {addr} addr_type '
                  f'{addr_type}, status {status}, att_status {att_status}')

    aics.event_received(defs.BTP_AICS_EV_STATUS, (addr_type, addr, status, att_status))


def aics_description_ev(aics, data, data_len):
    logging.debug('%s %r', aics_description_ev.__name__, data)

    fmt = '<B6sb'

    fmt_size = struct.calcsize(fmt)
    if len(data) < fmt_size:
        raise BTPError('Invalid data length')

    addr_type, addr, att_status = struct.unpack_from(fmt, data)
    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    description = struct.unpack_from(f'<{len(data) - fmt_size - 1}s', data, offset=fmt_size)
    description = binascii.hexlify(description[0]).decode('utf-8')

    logging.debug(f'AICS Description ev: addr {addr} addr_type '
                  f'{addr_type}, att_status {att_status}, description {description}')

    aics.event_received(defs.BTP_AICS_EV_DESCRIPTION, (addr_type, addr, att_status, description))


def aics_procedure_ev(aics, data, data_len):
    logging.debug('%s %r', aics_procedure_ev.__name__, data)

    fmt = '<B6sbb'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, att_status, opcode = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'AICS Procedure ev: addr {addr} addr_type '
                  f'{addr_type}, att status {att_status}, opcode {opcode}')

    aics.event_received(defs.BTP_AICS_EV_PROCEDURE, (addr_type, addr, att_status, opcode))


AICS_EV = {
    defs.BTP_AICS_EV_STATE: aics_state_ev,
    defs.BTP_AICS_EV_GAIN_SETTING_PROP: aics_gain_setting_prop_ev,
    defs.BTP_AICS_EV_INPUT_TYPE: aics_input_type_ev,
    defs.BTP_AICS_EV_STATUS: aics_status_ev,
    defs.BTP_AICS_EV_DESCRIPTION: aics_description_ev,
    defs.BTP_AICS_EV_PROCEDURE: aics_procedure_ev,
}
