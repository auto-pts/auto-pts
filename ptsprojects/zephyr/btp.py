"""Wrapper around btp messages. The functions are added as needed."""

from iutctl import get_zephyr
from msgdefs import SERVICE_ID, CORE_SERVICE_OP, GAP_SERVICE_OP, ADV_TYPE

def gap_reg_svc():
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(SERVICE_ID['SERVICE_ID_CORE'], CORE_SERVICE_OP['OP_REGISTER_SERVICE'],
                     (SERVICE_ID['SERVICE_ID_GAP'],))

def gap_adv_ind_on():
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(SERVICE_ID['SERVICE_ID_GAP'], GAP_SERVICE_OP['OP_GAP_START_ADV'],
                     (ADV_TYPE['ADV_IND'],))

def gap_adv_ind_nonconn_on():
    zephyrctl = get_zephyr()

    zephyrctl.sock_send(SERVICE_ID['SERVICE_ID_GAP'], GAP_SERVICE_OP['OP_GAP_START_ADV'],
                     (ADV_TYPE['ADV_NONCONN_IND'],))

def gap_reg_svc_rsp_succ():
    zephyrctl = get_zephyr()

    zephyrctl.sock_read(SERVICE_ID['SERVICE_ID_CORE'], CORE_SERVICE_OP['OP_REGISTER_SERVICE'],
                     None)
