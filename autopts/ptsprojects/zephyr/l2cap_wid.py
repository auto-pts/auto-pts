#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

import logging

from autopts.wid import generic_wid_hdl
from autopts.pybtp.types import WIDParams, gap_settings_btp2txt, IOCap

from autopts.pybtp import btp, defs

from autopts.ptsprojects.stack import get_stack

from time import sleep

from threading import Timer, Event

import re
import binascii

log = logging.debug


def l2cap_wid_hdl(wid, description, test_case_name):
    log(f'{l2cap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.l2cap'])

send_times = 0

def hdl_wid_113(params: WIDParams):
    global send_times
    if (params.test_case_name.startswith("L2CAP/COS/CED/BV-10-C")):
        if send_times == 0:
            stack = get_stack()
            l2cap = stack.l2cap
            l2cap.wait_for_connection(0)
            channel = l2cap.chan_lookup_id(0)
            if not channel:
                return False
            btp.l2cap_send_data(0, 'FF' * 256)
            send_times += 1
    return True

def hdl_wid_116(params: WIDParams):
    if params.test_case_name.startswith("L2CAP/EWC/BV-02-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET)
    return True

def hdl_wid_118(_: WIDParams):
    return True

def hdl_wid_49(params: WIDParams):
    btp.gap_conn_br()
    btp.gap_wait_for_connection()
    if not get_stack().gap.is_connected():
        return False
    if (params.test_case_name.startswith("L2CAP/CLS/CLR/BV-01-C") or
        params.test_case_name.startswith("L2CAP/CLS/UCD/BV-02-C") or
        params.test_case_name.startswith("L2CAP/CLS/UCD/BV-03-C")):
        return True
    stack = get_stack()
    l2cap = stack.l2cap
    if (params.test_case_name.startswith("L2CAP/COS/CFD/BV-10-C")
        or params.test_case_name.startswith("L2CAP/COS/RTX/BV-01-C")
        or params.test_case_name.startswith("L2CAP/COS/RTX/BV-02-C")
        or params.test_case_name.startswith("L2CAP/COS/RTX/BV-03-C")
        ):
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_RET)
    elif (params.test_case_name.startswith("L2CAP/COS/CED/BV-10-C")
        # or params.test_case_name.startswith("L2CAP/COS/FLC/BV-01-C")
        or params.test_case_name.startswith("L2CAP/COS/FLC/BV-02-C")
        or params.test_case_name.startswith("L2CAP/COS/FLC/BV-03-C")
        or params.test_case_name.startswith("L2CAP/COS/FLC/BV-04-C")
        or params.test_case_name.startswith("L2CAP/COS/CFD/BV-13-C")
        ):
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_FC)
        pass
    else:
        btp.l2cap_conn(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=l2cap.initial_mtu)
    return True

def hdl_wid_23(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF' * channel.peer_mtu)
    return True

def hdl_wid_26(_: WIDParams):
    btp.l2cap_echo(bd_addr=None, bd_addr_type=None)
    return True

def hdl_wid_50(_: WIDParams):
    btp.l2cap_cls_send(bd_addr=None, bd_addr_type=None, psm=0x1001, val='FF', val_mtp=10)
    return True

def hdl_wid_1(params: WIDParams):
    if (params.test_case_name.startswith("L2CAP/ERM/BV-13-C") or
        params.test_case_name.startswith("L2CAP/ECF/BV-05-C")):
        return True
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False
    if (params.test_case_name.startswith("L2CAP/ERM/BV-23-C") or
        params.test_case_name.startswith("L2CAP/STM/BV-03-C")):
        btp.l2cap_send_data(0, 'FF' * l2cap.initial_mtu)
    else:
        btp.l2cap_send_data(0, 'FF')
    return True

def hdl_wid_134(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False
    btp.l2cap_send_data(0, 'FF' * 256)
    return True

def hdl_wid_114(_: WIDParams):
    return True

def hdl_wid_7(_: WIDParams):
    return True

def hdl_wid_35(params: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap

    pattern = r' [\d]+ '
    length = re.search(pattern, params.description)[0]

    data = l2cap.rx_data_get(0, 10)
    if length and data[0]:
        if int(length) == len(data[0]):
            return True

    return False

def hdl_wid_128(_: WIDParams):
    return True

def hdl_wid_15(params: WIDParams):
    """
    Implements: TSC_MMI_tester_enable_connection
    description: Action: Place the IUT in connectable mode.
    """
    stack = btp.get_stack()
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    if params.test_case_name.startswith("L2CAP/ERM/BV-08-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET)
    elif params.test_case_name.startswith("L2CAP/ERM/BV-07-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET|defs.L2CAP_CONNECT_OPT_HOLD_CREDIT)
    return True

def hdl_wid_9(_: WIDParams):
    return True

def hdl_wid_130(_: WIDParams):
    return True

def hdl_wid_129(_: WIDParams):
    return True

def hdl_wid_32(_: WIDParams):
    return True

def hdl_wid_34(params: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap

    pattern = r' [\d]+ '
    length = re.search(pattern, params.description)[0]

    data = l2cap.rx_data_get(0, 10)
    if length and data[0]:
        if int(length) == len(data[0]):
            l2cap.clear_data()
            return True

    return False

def hdl_wid_17(_: WIDParams):
    return True

def hdl_wid_8(_: WIDParams):
    return True

def hdl_wid_19(_: WIDParams):
    return True

def hdl_wid_18(_: WIDParams):
    btp.l2cap_credits(0)
    return True

def hdl_wid_10(_: WIDParams):
    return True

def hdl_wid_131(_: WIDParams):
    return True

def hdl_wid_121(params: WIDParams):
    if params.test_case_name.startswith("L2CAP/CMC/BV-12-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET)
    if params.test_case_name.startswith("L2CAP/CMC/BI-03-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_STREAM)
    return True

def hdl_wid_6(params: WIDParams):
    if (params.test_case_name.startswith("L2CAP/CMC/BV-12-C") or
        params.test_case_name.startswith("L2CAP/CMC/BI-03-C")):
        stack = get_stack()
        l2cap = stack.l2cap
        if l2cap.wait_for_connection(10):
            return False
    return True

def hdl_wid_115(_: WIDParams):
    return True

def hdl_wid_119(params: WIDParams):
    if params.test_case_name.startswith("L2CAP/CMC/BV-10-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET|defs.L2CAP_CONNECT_OPT_MODE_OPTIONAL)
    if params.test_case_name.startswith("L2CAP/CMC/BV-11-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_STREAM|defs.L2CAP_CONNECT_OPT_MODE_OPTIONAL)
    if params.test_case_name.startswith("L2CAP/EWC/BV-03-C"):
        stack = get_stack()
        l2cap = stack.l2cap
        btp.gap_wait_for_connection()
        sleep(2)
        btp.l2cap_conn_with_mode(bd_addr=None, bd_addr_type=None, psm=0x1001, mtu=l2cap.initial_mtu, mode=defs.L2CAP_CONNECT_OPT_ERET)
    return True

def hdl_wid_20(_: WIDParams):
    return True


def hdl_wid_2(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    btp.l2cap_send_data(0, 'FF' * channel.peer_mtu)
    return True

def hdl_wid_3(params: WIDParams):
    if (params.test_case_name.startswith("L2CAP/ERM/BV-14-C")):
        stack = get_stack()
        l2cap = stack.l2cap
        l2cap.wait_for_connection(0)
        channel = l2cap.chan_lookup_id(0)
        if not channel:
            return False

        pattern = r'[\d]+'
        length = re.search(pattern, params.description)[0]
        for i in range(0, int(length)):
            btp.l2cap_send_data(0, 'FF')
    return True

def hdl_wid_124(_: WIDParams):
    return True

def hdl_wid_125(_: WIDParams):
    return True

def hdl_wid_4(params: WIDParams):
    if (params.test_case_name.startswith("L2CAP/ECF/BV-02-C") or
        params.test_case_name.startswith("L2CAP/ECF/BV-04-C")):
        stack = get_stack()
        l2cap = stack.l2cap
        l2cap.wait_for_connection(0)
        channel = l2cap.chan_lookup_id(0)
        if not channel:
            return False
        btp.l2cap_send_data(0, 'FF')
    if (params.test_case_name.startswith("L2CAP/ECF/BV-08-C")):
        stack = get_stack()
        l2cap = stack.l2cap
        l2cap.wait_for_connection(0)
        channel = l2cap.chan_lookup_id(0)
        if not channel:
            return False
        btp.l2cap_send_data(0, 'FF' * l2cap.initial_mtu)
    return True


def hdl_wid_24(params: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    pattern = r'[\d]+'
    length = re.search(pattern, params.description)[0]
    for i in range(0, int(length)):
        btp.l2cap_send_data(0, 'FF')
    return True

def hdl_wid_25(params: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    l2cap.wait_for_connection(0)
    channel = l2cap.chan_lookup_id(0)
    if not channel:
        return False

    pattern = r'[\d]+'
    length = re.search(pattern, params.description)[0]
    for i in range(0, int(length)):
        btp.l2cap_send_data(0, 'FF')
    return True

def hdl_wid_263(_: WIDParams):
    stack = get_stack()
    l2cap = stack.l2cap
    btp.l2cap_conn(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=l2cap.initial_mtu)
    return True

def hdl_wid_265(_: WIDParams):
    return True

def hdl_wid_62(_: WIDParams):
    btp.l2cap_cls_send(bd_addr=None, bd_addr_type=None, psm=0x1001, val='FF', val_mtp=10)
    return True

def hdl_wid_33(_: WIDParams):
    btp.gap_wait_for_sec_lvl_change(level=2, timeout=10)
    btp.gap_pair()
    btp.gap_wait_for_sec_lvl_change(level=2, timeout=10)
    btp.l2cap_cls_send(bd_addr=None, bd_addr_type=None, psm=0x1001, val='FF', val_mtp=10)
    return True
