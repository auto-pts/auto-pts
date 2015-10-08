"""Wrapper around btp messages. The functions are added as needed."""

from iutctl import get_zephyr
import logging
import btpdef

CONTROLLER_INDEX = 0

CORE = {
    "gap_reg": (btpdef.BTP_SERVICE_ID_CORE, btpdef.CORE_REGISTER_SERVICE,
                btpdef.BTP_INDEX_NONE, btpdef.BTP_SERVICE_ID_GAP),
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

def gap_reg_svc():
    logging.debug("%s", gap_reg_svc.__name__)
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(*CORE['gap_reg'])

def gap_adv_ind_on():
    logging.debug("%s", gap_adv_ind_on.__name__)
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(*GAP['start_adv'])

def gap_reg_svc_rsp_succ():
    logging.debug("%s", gap_reg_svc_rsp_succ.__name__)
    zephyrctl = get_zephyr()

    zephyrctl.sock_read(btpdef.BTP_SERVICE_ID_CORE,
                        btpdef.CORE_REGISTER_SERVICE,
                        btpdef.BTP_INDEX_NONE,
                        None)
