"""Wrapper around btp messages. The functions are added as needed."""

from iutctl import get_zephyr
from msgdefs import SERVICE_ID, CORE_SERVICE_OP, GAP_SERVICE_OP, BTP_INDEX_NONE, CONTROLLER_INDEX

def gap_reg_svc():
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(SERVICE_ID['SERVICE_ID_CORE'], CORE_SERVICE_OP['CORE_REGISTER_SERVICE'],
                        BTP_INDEX_NONE, (SERVICE_ID['SERVICE_ID_GAP'],))

def gap_adv_ind_on():
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(SERVICE_ID['SERVICE_ID_GAP'], GAP_SERVICE_OP['GAP_START_ADVERTISING'],
                        CONTROLLER_INDEX, ())

def gap_reg_svc_rsp_succ():
    zephyrctl = get_zephyr()

    zephyrctl.sock_read(SERVICE_ID['SERVICE_ID_CORE'], CORE_SERVICE_OP['CORE_REGISTER_SERVICE'],
                        BTP_INDEX_NONE, None)
