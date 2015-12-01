"""Wrapper around btp messages. The functions are added as needed."""

import logging
import binascii
import struct

from iutctl import get_zephyr
from collections import namedtuple
import btpdef
from itertools import count
from _struct import unpack

#Global temporary objects
PASSKEY = None

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
    "conn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_CONNECT, CONTROLLER_INDEX),
    "pair": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_PAIR, CONTROLLER_INDEX),
    "disconn": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_DISCONNECT, CONTROLLER_INDEX),
    "set_io_cap": (btpdef.BTP_SERVICE_ID_GAP, btpdef.GAP_SET_IO_CAP, CONTROLLER_INDEX),
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

GATTC = {
    "exchange_mtu": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_EXCHANGE_MTU,
                     CONTROLLER_INDEX),
    "disc_prim_uuid": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_PRIM_UUID,
                       CONTROLLER_INDEX),
    "find_included": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_FIND_INCLUDED,
                     CONTROLLER_INDEX),
    "disc_all_chrc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_CHRC,
                      CONTROLLER_INDEX),
    "disc_chrc_uuid": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_CHRC_UUID,
                       CONTROLLER_INDEX),
    "disc_all_desc": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_DESC,
                      CONTROLLER_INDEX),
    "read": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ, CONTROLLER_INDEX),
    "read_long": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_LONG,
                  CONTROLLER_INDEX),
    "read_multiple": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_MULTIPLE,
                      CONTROLLER_INDEX),
    "write_without_rsp": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE_WITHOUT_RSP,
                          CONTROLLER_INDEX),
    "signed_write": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_SIGNED_WRITE_WITHOUT_RSP,
                     CONTROLLER_INDEX),
    "write": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE, CONTROLLER_INDEX),
    "write_long": (btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE_LONG,
                   CONTROLLER_INDEX),
}

class BTPError(Exception):
    """Exception raised if BTP error occurs.

    If this exception is raised the status of the running test case is updated
    accordingly to show that BTP error has occurred.

    """
    pass

def rsp_hdr_check(rcv_hdr, exp_svc_id, exp_op):
    if rcv_hdr.svc_id != exp_svc_id:
        raise BTPError("Incorrect service ID: " + str(rcv_hdr.svc_id) +
                       ", expected: " + str(exp_svc_id) + "!")

    if rcv_hdr.op == btpdef.BTP_STATUS:
        raise BTPError("Error opcode in response!")

    if exp_op and exp_op != rcv_hdr.op:
        raise BTPError("Invalid opcode " + str(rcv_hdr.op) +
                       "in the response, expected: " + str(exp_op) + "!")

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

    #TODO Command response should be checked
    gap_command_rsp_succ()

def gap_connected_ev(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gap_connected_ev.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GAP:
        raise BTPError(
            "Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.BTP_SERVICE_ID_GAP)

    if tuple_hdr.op != btpdef.GAP_EV_DEVICE_CONNECTED:
        raise BTPError("Error opcode in response!")

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(bd_addr_type))

    if tuple_data[0] != data_ba:
        raise BTPError("Error in connected event data")

def gap_conn(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gap_conn.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['conn'], data = data_ba)

    gap_command_rsp_succ()

def gap_disconnected_ev(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gap_disconnected_ev.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GAP:
        raise BTPError(
            "Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.BTP_SERVICE_ID_GAP)

    if tuple_hdr.op == 0:
        raise BTPError("Error opcode in response!")

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(bd_addr_type))

    if tuple_data[0] != data_ba:
        raise BTPError("Error in connected event data")

def gap_disconn(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gap_disconn.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['disconn'], data = data_ba)

    gap_command_rsp_succ()

def gap_set_io_cap(io_cap = None):
    logging.debug("%s %r", gap_set_io_cap.__name__, io_cap)
    zephyrctl = get_zephyr()

    zephyrctl.btp_socket.send(*GAP['set_io_cap'], data = chr(io_cap))

    gap_command_rsp_succ()

def gap_pair(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gap_pair.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GAP['pair'], data = data_ba)

    #Expected result
    gap_command_rsp_succ()

def var_get_passkey():
    return str(PASSKEY)

def var_get_wrong_passkey():
    #Passkey is in range 0-999999
    if PASSKEY > 0:
        return str(PASSKEY - 1)
    else:
        return str(PASSKEY + 1)

def gap_passkey_disp_ev(bd_addr = None, bd_addr_type = None, store = False):
    logging.debug("%s %r %r", gap_passkey_disp_ev.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GAP:
        raise BTPError(
            "Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.BTP_SERVICE_ID_GAP)

    if tuple_hdr.op == 0:
        raise BTPError("Error opcode in response!")

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    if tuple_data[0][:7] != data_ba:
        raise BTPError("Error in address of passkey display data")

    passkey_local = struct.unpack('I', tuple_data[0][7:11])[0]
    logging.debug("passkey = %r", passkey_local)

    if store:
        global PASSKEY
        PASSKEY = passkey_local

def gap_command_rsp_succ():
    logging.debug("%s", gap_command_rsp_succ.__name__)

    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GAP:
        raise BTPError(
            "Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.BTP_SERVICE_ID_GAP)

    if tuple_hdr.op == 0:
        raise BTPError("Error opcode in response!")

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

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTS['add_inc_svc'], data = data_ba)

    gatt_command_rsp_succ()

def gatts_add_char(hdl = None, prop = None, perm = None, uuid = None):
    logging.debug("%s %r %r %r %r", gatts_add_char.__name__, hdl, prop, perm,
                  uuid)

    zephyrctl = get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

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

    if type(hdl) is str:
        hdl = int(hdl, 16)

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

    if type(hdl) is str:
        hdl = int(hdl, 16)

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

    if type(hdl) is str:
        hdl = int(hdl, 16)

    data_ba = bytearray()
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(hdl_ba)
    data_ba.extend(chr(enc_key_size))

    zephyrctl.btp_socket.send(*GATTS['set_enc_key_size'], data = data_ba)

    gatt_command_rsp_succ()

def gattc_exchange_mtu(bd_addr = None, bd_addr_type = None):
    logging.debug("%s %r %r", gattc_exchange_mtu.__name__, bd_addr, bd_addr_type)
    zephyrctl = get_zephyr()

    data_ba = bytearray()
    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)

    zephyrctl.btp_socket.send(*GATTC['exchange_mtu'], data = data_ba)

    gatt_command_rsp_succ()

def gattc_disc_prim_uuid(bd_addr_type = None, bd_addr = None, uuid = None):
    logging.debug("%s %r %r %r", gattc_disc_prim_uuid.__name__, bd_addr_type,
                  bd_addr, uuid)
    zephyrctl = get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    uuid_byte_table = [uuid[i:i+2] for i in range(0, len(uuid), 2)]
    uuid_swp = ''.join([c[1] + c[0] for c in zip(uuid_byte_table[::2], uuid_byte_table[1::2])])
    uuid_ba = binascii.unhexlify(bytearray(uuid_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_prim_uuid'], data = data_ba)

def gattc_find_included(bd_addr_type = None, bd_addr = None, start_hdl = None,
                       stop_hdl = None):
    logging.debug("%s %r %r %r %r", gattc_find_included.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    zephyrctl = get_zephyr()

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['find_included'], data = data_ba)

def gattc_disc_all_chrc(bd_addr_type = None, bd_addr = None,
                               start_hdl = None, stop_hdl = None):
    logging.debug("%s %r %r %r %r", gattc_disc_all_chrc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    zephyrctl = get_zephyr()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_all_chrc'], data = data_ba)

def gattc_disc_chrc_uuid(bd_addr_type = None, bd_addr = None,
                           start_hdl = None, stop_hdl = None, uuid = None):
    logging.debug("%s %r %r %r %r %r", gattc_disc_chrc_uuid.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl, uuid)
    zephyrctl = get_zephyr()

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)
    uuid_byte_table = [uuid[i:i+2] for i in range(0, len(uuid), 2)]
    uuid_swp = ''.join([c[1] + c[0] for c in zip(uuid_byte_table[::2], uuid_byte_table[1::2])])
    uuid_ba = binascii.unhexlify(bytearray(uuid_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_chrc_uuid'], data = data_ba)

def gattc_disc_all_desc(bd_addr_type = None, bd_addr = None, start_hdl = None,
                        stop_hdl = None):
    logging.debug("%s %r %r %r %r", gattc_disc_all_desc.__name__,
                  bd_addr_type, bd_addr, start_hdl, stop_hdl)
    zephyrctl = get_zephyr()

    if type(start_hdl) is str:
        start_hdl = int(start_hdl, 16)

    if type(stop_hdl) is str:
        stop_hdl = int(stop_hdl, 16)

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    start_hdl_ba = struct.pack('H', start_hdl)
    stop_hdl_ba = struct.pack('H', stop_hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(start_hdl_ba)
    data_ba.extend(stop_hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['disc_all_desc'], data = data_ba)

def gattc_read(bd_addr_type = None, bd_addr = None, hdl = None):
    logging.debug("%s %r %r %r", gattc_read.__name__, bd_addr_type, bd_addr, hdl)
    zephyrctl = get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    if type(hdl) is str:
        hdl = int(hdl, 16)
    hdl_ba = struct.pack('H', hdl)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)

    zephyrctl.btp_socket.send(*GATTC['read'], data = data_ba)

def gattc_read_long(bd_addr_type = None, bd_addr = None, hdl = None, off = None,
                    modif_off = None):
    logging.debug("%s %r %r %r %r %r", gattc_read_long.__name__, bd_addr_type,
                  bd_addr, hdl, off, modif_off)
    zephyrctl = get_zephyr()

    data_ba = bytearray()

    if type(off) is str:
        off = int(off, 16)
    if modif_off is not None:
        off += modif_off
    if type(hdl) is str:
        hdl = int(hdl, 16)

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    off_ba = struct.pack('H', off)

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)

    zephyrctl.btp_socket.send(*GATTC['read_long'], data = data_ba)

def gattc_read_multiple(bd_addr_type = None, bd_addr = None, hdls = None):
    logging.debug("%s %r %r %r", gattc_read_multiple.__name__, bd_addr_type,
                  bd_addr, hdls)
    zephyrctl = get_zephyr()

    data_ba = bytearray()

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdls_cnt_ba = struct.pack('H', len(hdls))
    hdls = ''.join(hdl for hdl in hdls)
    hdls_byte_table = [hdls[i:i+2] for i in range(0, len(hdls), 2)]
    hdls_swp = ''.join([c[1] + c[0] for c in zip(hdls_byte_table[::2], hdls_byte_table[1::2])])
    hdls_ba = binascii.unhexlify(bytearray(hdls_swp))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdls_cnt_ba)
    data_ba.extend(hdls_ba)

    zephyrctl.btp_socket.send(*GATTC['read_multiple'], data = data_ba)

def gattc_write_without_rsp(bd_addr_type = None, bd_addr = None, hdl = None,
                            val = None, mtp = None):
    logging.debug("%s %r %r %r %r %r", gattc_write_without_rsp.__name__,
                  bd_addr_type, bd_addr, hdl, val, mtp)
    zephyrctl = get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if mtp:
        val *= int(mtp)

    data_ba = bytearray()

    val_len = len(val) / 2

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    val_len_ba = struct.pack('H', val_len)
    val_ba = binascii.unhexlify(bytearray(val))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write_without_rsp'], data = data_ba)

    gatt_command_rsp_succ()

def gattc_signed_write(bd_addr_type = None, bd_addr = None, hdl = None,
                       val = None, mtp = None):
    logging.debug("%s %r %r %r %r %r", gattc_signed_write.__name__,
                  bd_addr_type, bd_addr, hdl, val, mtp)
    zephyrctl = get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if mtp:
        val *= int(mtp)

    data_ba = bytearray()

    val_len = len(val) / 2

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))

    hdl_ba = struct.pack('H', hdl)
    val_len_ba = struct.pack('H', val_len)
    val_ba = binascii.unhexlify(bytearray(val))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['signed_write'], data = data_ba)

    gatt_command_rsp_succ()

def gattc_write(bd_addr_type = None, bd_addr = None, hdl = None, val = None,
                mtp = None):
    logging.debug("%s %r %r %r %r %r", gattc_write.__name__, bd_addr_type,
                  bd_addr, hdl, val, mtp)
    zephyrctl = get_zephyr()

    if type(hdl) is str:
        hdl = int(hdl, 16)

    if mtp:
        val *= int(mtp)

    data_ba = bytearray()

    val_len = len(val) / 2

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    val_len_ba = struct.pack('H', val_len)
    val_ba = binascii.unhexlify(bytearray(val))

    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write'], data = data_ba)

def gattc_write_long(bd_addr_type = None, bd_addr = None, hdl = None,
                     off = None, val = None, length = None):
    logging.debug("%s %r %r %r %r %r", gattc_write_long.__name__,
                  bd_addr_type, hdl, off, val, length)

    if type(hdl) is str:
        hdl = int(hdl, 16) # convert string in hex format to int

    if type(off) is str:
        off = int(off, 16)

    if length:
        val *= int(length)

    zephyrctl = get_zephyr()

    val_len = len(val) / 2

    bd_addr_ba = binascii.unhexlify("".join(bd_addr.split(':')[::-1]))
    hdl_ba = struct.pack('H', hdl)
    val_len_ba = struct.pack('H', val_len)
    off_ba = struct.pack('H', off)
    val_ba = binascii.unhexlify(bytearray(val))

    data_ba = bytearray()
    data_ba.extend(chr(bd_addr_type))
    data_ba.extend(bd_addr_ba)
    data_ba.extend(hdl_ba)
    data_ba.extend(off_ba)
    data_ba.extend(val_len_ba)
    data_ba.extend(val_ba)

    zephyrctl.btp_socket.send(*GATTC['write_long'], data = data_ba)

def gatt_command_rsp_succ():
    logging.debug("%s", gatt_command_rsp_succ.__name__)

    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, None)

#BTP Single Service Attribute
#0             16           32            40
#+--------------+------------+-------------+------+
#| Start Handle | End Handle | UUID Length | UUID |
#+--------------+------------+-------------+------+
def gatt_dec_svc_attr(data = None):
    hdr = '<HHB'
    hdr_len = struct.calcsize(hdr)

    start_hdl, end_hdl, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (start_hdl, end_hdl, uuid), hdr_len + uuid_len

#BTP Single Included Service Attribute
#0                16
#+-----------------+-------------------+
#| Included Handle | Service Attribute |
#+-----------------+-------------------+
def gatt_dec_incl_attr(data = None):
    hdr = '<H'
    hdr_len = struct.calcsize(hdr)

    incl_hdl = struct.unpack_from(hdr, data)
    svc, svc_len = gatt_dec_svc_attr(data[hdr_len:])

    return (incl_hdl, svc), hdr_len + svc_len

#BTP Single Characteristic Attribute
#0       16             32           40            48
#+--------+--------------+------------+-------------+------+
#| Handle | Value Handle | Properties | UUID Length | UUID |
#+--------+--------------+------------+-------------+------+
def gatt_dec_chrc_attr(data = None):
    hdr = '<HHBB'
    hdr_len = struct.calcsize(hdr)

    chrc_hdl, val_hdl, props, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (chrc_hdl, val_hdl, props, uuid), hdr_len + uuid_len

#BTP Single Descriptor Attribute
#0       16            24
#+--------+-------------+------+
#| Handle | UUID Length | UUID |
#+--------+-------------+------+
def gatt_dec_desc_attr(data = None):
    hdr = '<HB'
    hdr_len = struct.calcsize(hdr)

    hdl, uuid_len = struct.unpack_from(hdr, data)
    uuid = struct.unpack_from('%ds' % uuid_len, data, hdr_len)

    return (hdl, uuid), hdr_len + uuid_len

#BTP Discovery Response frame format
#0                  8
#+------------------+------------+
#| Attributes Count | Attributes |
#+------------------+------------+
def gatt_dec_disc_rsp(data = None, attr_type = None):
    attrs_len = len(data) - 1
    attr_cnt, attrs = struct.unpack('B%ds' % attrs_len, data)

    attrs_list = []
    offset = 0

    for x in range(attr_cnt):
        if attr_type == "service":
            attr, attr_len = gatt_dec_svc_attr(attrs[offset:])
        elif attr_type == "include":
            attr, attr_len = gatt_dec_incl_attr(attrs[offset:])
        elif attr_type == "characteristic":
            attr, attr_len = gatt_dec_chrc_attr(attrs[offset:])
        else: #descriptor
            attr, attr_len = gatt_dec_desc_attr(attrs[offset:])

        attrs_list.append(attr)
        offset += attr_len

    return tuple(attrs_list)

#BTP Read Response frame format
#0              8            24
#+--------------+-------------+------+
#| ATT Response | Data Length | Data |
#+--------------+-------------+------+
def gatt_dec_read_rsp(data = None):
    hdr = '<BH'
    hdr_len = struct.calcsize(hdr)

    att_rsp, val_len = struct.unpack_from(hdr, data)
    val = struct.unpack_from('%ds' % val_len, data, hdr_len)

    return att_rsp, val

#BTP Write Response frame format
#0              8
#+--------------+
#| ATT Response |
#+--------------+
def gatt_dec_write_rsp(data = None):
    return ord(data)

def gattc_disc_prim_uuid_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_prim_uuid_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_PRIM_UUID)

    svcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "service")
    logging.debug("%s %r", gattc_disc_prim_uuid_rsp.__name__, svcs_tuple)
    #TODO Validation

def gattc_find_included_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_find_included_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_FIND_INCLUDED)

    incls_tuple = gatt_dec_disc_rsp(tuple_data[0], "include")
    logging.debug("%s %r", gattc_find_included_rsp.__name__, incls_tuple)
    #TODO Validation

def gattc_disc_all_chrc_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_chrc_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_CHRC)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_all_chrc_rsp.__name__, chrcs_tuple)
    #TODO Validation

def gattc_disc_chrc_uuid_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_chrc_uuid_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_CHRC_UUID)

    chrcs_tuple = gatt_dec_disc_rsp(tuple_data[0], "characteristic")
    logging.debug("%s %r", gattc_disc_chrc_uuid_rsp.__name__, chrcs_tuple)
    #TODO Validation

def gattc_disc_all_desc_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_disc_all_desc_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_DISC_ALL_DESC)

    descs_tuple = gatt_dec_disc_rsp(tuple_data[0], "descriptor")
    logging.debug("%s %r", gattc_disc_all_desc_rsp.__name__, descs_tuple)
    #TODO Validation

def gattc_read_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_rsp.__name__, rsp, value)
    #TODO Validation

def gattc_read_long_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_long_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_LONG)

    rsp, value = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_long_rsp.__name__, rsp, value)
    #TODO Validation

def gattc_read_multiple_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_read_multiple_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_READ_MULTIPLE)

    rsp, values = gatt_dec_read_rsp(tuple_data[0])
    logging.debug("%s %r %r", gattc_read_multiple_rsp.__name__, rsp, values)
    #TODO Validation

def gattc_write_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_rsp.__name__, rsp)
    #TODO Validation

def gattc_write_long_rsp():
    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("%s received %r %r", gattc_write_long_rsp.__name__, tuple_hdr, tuple_data)

    rsp_hdr_check(tuple_hdr, btpdef.BTP_SERVICE_ID_GATT, btpdef.GATT_WRITE_LONG)

    rsp = gatt_dec_write_rsp(tuple_data[0])
    logging.debug("%s %r", gattc_write_long_rsp.__name__, rsp)
    #TODO Validation
