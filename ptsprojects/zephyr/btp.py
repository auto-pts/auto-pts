"""Wrapper around btp messages. The functions are added as needed."""

import logging
import binascii
import struct

from iutctl import get_zephyr
import btpdef

CONTROLLER_INDEX = 0

CORE = {
    "gap_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_GAP),

    "gatts_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                  btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_GATT),

    "read_supp_cmds": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_READ_SUPPORTED_COMMANDS,
                       btpdef.BTP_INDEX_NONE, ""),

    "read_supp_svcs": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_READ_SUPPORTED_SERVICES,
                       btpdef.BTP_INDEX_NONE, ""),
}

GAP = {
    "read_supp_cmds": '',
    "read_ctrl_index_list": '',
    "read_ctrl_info": '',
    "reset": '',
    "set_powered": '',
    "set_connectable": '',
    "set_fast_connectable": '',
    "set_discov": '',
    "set_bond": '',
    "start_adv": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_START_ADVERTISING,
                  CONTROLLER_INDEX, ""),
    "stop_adv": '',
    "start_discov": '',
    "stop_discov": '',
}

GATTS = {
    "add_svc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_SERVICE,
                CONTROLLER_INDEX),

    "start_server": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_START_SERVER,
                     CONTROLLER_INDEX, ""),

    "add_inc_svc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_INCLUDED_SERVICE,
                    CONTROLLER_INDEX),

    "add_char": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_CHARACTERISTIC,
                 CONTROLLER_INDEX),

    "set_val": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_SET_VALUE,
                 CONTROLLER_INDEX),

    "add_desc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_ADD_DESCRIPTOR,
                 CONTROLLER_INDEX),

    "set_enc_key_size": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_SET_ENC_KEY_SIZE,
                         CONTROLLER_INDEX),
}

class BTPError(Exception):
    """Exception raised if BTP error occurs.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP error has occurred.

    """
    pass

def core_reg_svc_gap():
    logging.debug("%s", core_reg_svc_gap.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gap_reg'])

    core_reg_svc_rsp_succ()

def core_reg_svc_gatts():
    logging.debug("%s", core_reg_svc_gatts.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gatts_reg'])

    core_reg_svc_rsp_succ()

def core_reg_svc_rsp_succ():
    logging.debug("%s", core_reg_svc_rsp_succ.__name__)
    zephyrctl = get_zephyr()

    expected_frame = ((btpdef.BTP_SERVICE_ID_CORE,
                       btpdef.CORE_REGISTER_SERVICE,
                       btpdef.BTP_INDEX_NONE,
                       0),
                      ('',))

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    else:
        logging.debug("response is valid")

def gap_adv_ind_on():
    logging.debug("%s", gap_adv_ind_on.__name__)
    zephyrctl = get_zephyr()

    zephyrctl.btp_socket.send(*GAP['start_adv'])

def gatts_add_svc(svc_type = None, uuid = None):
    logging.debug("%s %r %r", gatts_add_svc.__name__, svc_type, uuid)

    zephyrctl = get_zephyr()

    data_ba = bytearray()
    uuid_byte_table = [uuid[i:i+2] for i in range(0, len(uuid), 2)]
    uuid_swp = ''.join([c[1] + c[0] for c in zip(uuid_byte_table[::2], uuid_byte_table[1::2])])
    uuid_ba = binascii.unhexlify(bytearray(uuid_swp))
    data_ba.extend(chr(svc_type))
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_svc'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_add_inc_svc(hdl = None):
    logging.debug("%s %r", gatts_add_inc_svc.__name__, hdl)

    zephyrctl = get_zephyr()

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTS['add_inc_svc'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_add_char(hdl = None, prop = None, perm = None, uuid = None):
    logging.debug("%s %r %r %r %r", gatts_add_char.__name__, hdl, prop, perm,
                  uuid)

    zephyrctl = get_zephyr()

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_byte_table = [uuid[i:i+2] for i in range(0, len(uuid), 2)]
    uuid_swp = ''.join([c[1] + c[0] for c in zip(uuid_byte_table[::2], uuid_byte_table[1::2])])
    uuid_ba = binascii.unhexlify(bytearray(uuid_swp))

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(prop))
    data_ba.extend(chr(perm))
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_char'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_set_val(hdl = None, val = None):
    logging.debug("%s %r %r ", gatts_set_val.__name__, hdl, val)

    zephyrctl = get_zephyr()

    val_len = len(val) / 2

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    val_len_ba = struct.pack('H', val_len)
    val_ba = binascii.unhexlify(bytearray(val))

    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTS['set_val'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_add_desc(hdl = None, perm = None, uuid = None):
    logging.debug("%s %r %r %r", gatts_add_desc.__name__, hdl, perm, uuid)

    zephyrctl = get_zephyr()

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    uuid_byte_table = [uuid[i:i+2] for i in range(0, len(uuid), 2)]
    uuid_swp = ''.join([c[1] + c[0] for c in zip(uuid_byte_table[::2], uuid_byte_table[1::2])])
    uuid_ba = binascii.unhexlify(bytearray(uuid_swp))

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(perm))
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_desc'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_start_server():
    logging.debug("%s", gatts_start_server.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*GATTS['start_server'])

    gatt_command_rsp_succ()

def gatts_set_enc_key_size(hdl = None, enc_key_size = None):
    logging.debug("%s %r %r", gatts_set_enc_key_size.__name__, hdl, enc_key_size)

    zephyrctl = get_zephyr()

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(enc_key_size))

    zephyrctl.btp_socket.send(*GATTS['set_enc_key_size'], data = data_ba)

    gatt_command_rsp_succ()

def gatt_command_rsp_succ():
    logging.debug("%s", gatt_command_rsp_succ.__name__)

    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GATT:
        raise BTPError(
            "Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.SERVICE_ID_GATT)

    if tuple_hdr.op != btpdef.BTP_STATUS:
        raise BTPError("Error opcode in response!")
