"""Wrapper around btp messages. The functions are added as needed."""

import logging
import binascii

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
}

def core_reg_svc_gap():
    logging.debug("%s", core_reg_svc_gap.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gap_reg'])

def core_reg_svc_gatts():
    logging.debug("%s", core_reg_svc_gatts.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*CORE['gatts_reg'])

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
        raise Exception("BTP: Unexpected response received!")
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
    uuid_ba = binascii.unhexlify(bytearray(uuid))
    data_ba.extend(chr(svc_type))
    data_ba.extend(chr(len(uuid) / 2))
    data_ba.extend(uuid_ba)

    zephyrctl.btp_socket.send(*GATTS['add_svc'], data = data_ba)

def gatts_start_server():
    logging.debug("%s", gatts_start_server.__name__)

    zephyrctl = get_zephyr()
    zephyrctl.btp_socket.send(*GATTS['start_server'])

def gatts_command_succ_rsp():
    logging.debug("%s", gatts_command_succ_rsp.__name__)

    zephyrctl = get_zephyr()

    tuple_hdr, tuple_data = zephyrctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    if tuple_hdr.svc_id != btpdef.BTP_SERVICE_ID_GATT:
        raise Exception(
            "BTP: Incorrect service ID %r  in response, should be %r!",
            tuple_hdr.svc_id, btpdef.SERVICE_ID_GATT)

    if tuple_hdr.op == 0:
        raise Exception("BTP: Error opcode in response!")
