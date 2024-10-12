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


def gap_wid_hdl(wid, description, test_case_name):
    log(f'{gap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.gap'])


def hdl_wid_104(_: WIDParams):
    return True


def hdl_wid_114(_: WIDParams):
    return True


def hdl_wid_162(_: WIDParams):
    return True


def hdl_wid_224(_: WIDParams):
    return True

def hdl_wid_31(_: WIDParams):
    return True

def hdl_wid_32(_: WIDParams):
    btp.gap_set_limdiscov()
    return True

def hdl_wid_160(_: WIDParams):
    btp.gap_set_limdiscov()
    return True

def hdl_wid_145(_: WIDParams):
    stack = get_stack()
    if not stack.gap.current_settings_get(
        gap_settings_btp2txt[defs.GAP_SETTINGS_DISCOVERABLE]):
        return True
    return False

gap_connect_times = 0
def hdl_wid_33(params: WIDParams):
    global gap_connect_times
    gap_connect_times += 1
    btp.gap_wait_for_disconnection()
    btp.gap_set_gendiscov()
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-10-C")):
        btp.gap_wait_for_connection()
        btp.gap_pair()
        return True
    if gap_connect_times > 1:
        if (params.test_case_name.startswith("GAP/SEC/SEM/BI-24-C")):
            btp.gap_wait_for_connection()
            btp.gap_pair()
            return True
    return True

def hdl_wid_34(_: WIDParams):
    btp.gap_set_gendiscov()
    btp.gap_set_nonconn()
    return True

def hdl_wid_105(_: WIDParams):
    btp.gap_set_gendiscov()
    return True

def hdl_wid_222(_: WIDParams):
    return True

def hdl_wid_146(_: WIDParams):
    btp.gap_start_discov(transport='bredr')
    return True

def hdl_wid_147(_: WIDParams):
    btp.gap_start_discov(transport='bredr', mode='limited')
    return True

def hdl_wid_164(_: WIDParams):
    btp.gap_start_discov(transport='bredr')
    return True

def hdl_wid_165(params: WIDParams):
    sleep(30)  # Give some time to discover devices
    pts_name = re.findall(r'name\s*\'(.*)\'', params.description)
    if len(pts_name) > 0:
        pts_name = pts_name[0].encode('utf-8')
        pts_name = str(binascii.hexlify(pts_name)).lstrip('b\'').rstrip('\'').upper()
        return btp.check_scan_rep_and_rsp(pts_name, pts_name)
    return False

def hdl_wid_102(params: WIDParams):
    btp.gap_wait_for_disconnection()
    btp.gap_start_discov(transport='bredr')
    sleep(30)  # Give some time to discover devices
    if btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        btp.gap_conn_br()
        btp.gap_wait_for_connection()
        if (params.test_case_name.startswith("GAP/SEC/SEM/BV-20-C")):
            btp.gap_pair_with_sec_level(sec_level=defs.GAP_PAIR_LEVEL_4)
        elif not (params.test_case_name.startswith("GAP/IDLE/BON/BV-05-C")
             or params.test_case_name.startswith("GAP/IDLE/BON/BV-06-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BV-17-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-05-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-12-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-02-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-06-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-03-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-07-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-14-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-17-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-15-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-18-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-16-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-19-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-04-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-08-C")
             or params.test_case_name.startswith("GAP/SEC/SEM/BI-31-C")
             or params.test_case_name.startswith("GAP/DM/LEP/BV-12-C")
             or params.test_case_name.startswith("GAP/DM/LEP/BV-15-C")
             or params.test_case_name.startswith("GAP/DM/LEP/BV-13-C")
             ):
            btp.gap_pair()
        elif params.test_case_name.startswith("GAP/DM/LEP/BV-15-C"):
            wait_for_confirm_passkey()
        return True
    return False

def hdl_wid_264(_: WIDParams):
    btp.l2cap_conn(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23)
    return True

def hdl_wid_2001(params: WIDParams):
    """
    The secureId is [passkey]
    """
    pattern = '[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if "verify the passKey is correct" in params.description:
        btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
    else:
        btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    stack.gap.set_passkey(None)
    return True

def hdl_wid_166(_: WIDParams):
    return True

def hdl_wid_251(params: WIDParams):
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-13-C")):
        wait_for_confirm_passkey()
    return True

def hdl_wid_167(_: WIDParams):
    return True

def timeout_cb(flag):
    flag.clear()

def wait_for_confirm_passkey(timeout=30):
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    flag = Event()
    flag.set()

    t = Timer(timeout, timeout_cb, [flag])
    t.start()

    if stack.gap.get_passkey() is not None:
        btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, stack.gap.get_passkey())
        stack.gap.set_passkey(None)
        return True

    while flag.is_set():
        if stack.gap.get_passkey() is not None:
            btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, stack.gap.get_passkey())
            t.cancel()
            stack.gap.set_passkey(None)
            return True

    return False

l2cal_connect_count = 0

def hdl_wid_103(params: WIDParams):
    global l2cal_connect_count
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-07-C")):
        btp.gap_wait_for_connection()
        btp.l2cap_conn_with_sec_level(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23, sec_level=defs.L2CAP_CONNECT_SEC_LEVEL_3)
        return True
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-08-C")):
        btp.gap_conn_br()
        btp.gap_wait_for_connection()
        btp.l2cap_conn(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23)
        return True
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-09-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-53-C")):
        if l2cal_connect_count == 0:
            btp.gap_set_io_cap(IOCap.no_input_output)
            btp.l2cap_conn_with_sec_level(bd_addr=None, bd_addr_type=None, psm=0x2001,mtu=23,sec_level=defs.L2CAP_CONNECT_SEC_LEVEL_2)
        else:
            btp.gap_set_io_cap(IOCap.display_yesno)
            btp.l2cap_conn_with_sec_level(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23,sec_level=defs.L2CAP_CONNECT_SEC_LEVEL_3)
        l2cal_connect_count = l2cal_connect_count + 1
        return True
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-18-C")):
        btp.l2cap_conn_with_sec_level(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23, sec_level=defs.L2CAP_CONNECT_SEC_LEVEL_4)
        return True
    btp.l2cap_conn(bd_addr=None, bd_addr_type=None, psm=0x1001,mtu=23)
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")):
        wait_for_confirm_passkey()
    return True

def hdl_wid_231(_: WIDParams):
    btp.gap_pair()
    btp.gap_wait_for_sec_lvl_change(level=2)
    btp.gap_disconn()
    return True

def hdl_wid_108(params: WIDParams):
    if (params.test_case_name.startswith("GAP/DM/BON/BV-01-C")):
        return True
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")):
        btp.gap_pair_with_sec_level(sec_level=defs.GAP_PAIR_LEVEL_3)
        wait_for_confirm_passkey()
        return True
    btp.gap_pair()
    return True

def hdl_wid_151(_: WIDParams):
    return True

def hdl_wid_20117(_: WIDParams):
    btp.gap_wait_for_sec_lvl_change(level=2)
    return True

def hdl_wid_36(_: WIDParams):
    btp.clear_discov_results()
    btp.gap_start_discov(transport='le')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    if False == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    btp.clear_discov_results()
    btp.gap_start_discov(transport='bredr')
    sleep(30)  # Give some time to discover devices
    if False == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    return True

def hdl_wid_7(_: WIDParams):
    btp.gap_start_discov(transport='le', mode='limited')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    if False == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    btp.clear_discov_results()
    btp.gap_start_discov(transport='bredr', mode='limited')
    sleep(30)  # Give some time to discover devices
    if False == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    return True

def hdl_wid_123(_: WIDParams):
    btp.clear_discov_results()
    btp.gap_start_discov(transport='le', mode='limited')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    if True == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    btp.clear_discov_results()
    btp.gap_start_discov(transport='bredr', mode='limited')
    sleep(30)  # Give some time to discover devices
    if True == btp.check_discov_results(btp.pts_addr_type_get(), btp.pts_addr_get()):
        return False
    return True

def hdl_wid_86(_: WIDParams):
    btp.gap_start_discov(transport='bredr')
    sleep(30)  # Give some time to discover devices
    pts_name = 'PTS'.encode('utf-8')
    pts_name = str(binascii.hexlify(pts_name)).lstrip('b\'').rstrip('\'').upper()
    return btp.check_scan_rep_and_rsp(pts_name, pts_name)

def hdl_wid_252(_: WIDParams):
    return True

def hdl_wid_220(_: WIDParams):
    btp.gap_wait_for_disconnection()
    return not get_stack().gap.is_connected()

def hdl_wid_255(_: WIDParams):
    return True

def hdl_wid_266(params: WIDParams):
    if (params.test_case_name.startswith("GAP/SEC/SEM/BI-28-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BI-29-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BI-30-C")):
        return btp.gap_wait_for_encryption_fail()
    if params.test_case_name.startswith("GAP/SEC/SEM/BI-33-C"):
        return btp.gap_wait_for_sec_lvl_change(defs.GAP_PAIR_LEVEL_4)
    btp.gap_wait_for_disconnection()
    return not get_stack().gap.is_connected()

def hdl_wid_256(_: WIDParams):
    return True

def hdl_wid_260(_: WIDParams):
    return True

def hdl_wid_257(_: WIDParams):
    return True

def hdl_wid_261(_: WIDParams):
    return True

def hdl_wid_258(_: WIDParams):
    return True

def hdl_wid_262(_: WIDParams):
    return True

def hdl_wid_259(_: WIDParams):
    return True

def hdl_wid_263(_: WIDParams):
    return True

def hdl_wid_20100(params: WIDParams):
    btp.gap_conn()
    if (params.test_case_name.startswith("GAP/DM/LEP/BV-20-C")
        or params.test_case_name.startswith("GAP/DM/LEP/BV-17-C")
        or params.test_case_name.startswith("GAP/DM/LEP/BV-18-C")
        ):
        btp.gap_wait_for_connection()
        btp.gap_pair()
    return True

def hdl_wid_213(params: WIDParams):
    if (params.test_case_name.startswith("GAP/DM/LEP/BV-13-C")
        ):
        btp.gap_set_io_cap(IOCap.keyboard_display)
        btp.gap_pair_with_sec_level(sec_level=defs.GAP_PAIR_LEVEL_3)

    return True

def hdl_wid_221(_: WIDParams):
    return True

def hdl_wid_216(_: WIDParams):
    return True

def hdl_wid_217(_: WIDParams):
    return True

def hdl_wid_208(params: WIDParams):
    if (params.test_case_name.startswith("GAP/DM/LEP/BV-18-C")
        ):
        btp.gap_set_io_cap(IOCap.keyboard_display)
        btp.gap_pair_with_sec_level(sec_level=defs.GAP_PAIR_LEVEL_4)
        return True
    btp.gap_pair()
    return True

def hdl_wid_274(_: WIDParams):
    return True
