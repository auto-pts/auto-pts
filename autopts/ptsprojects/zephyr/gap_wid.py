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

import binascii
import logging
import threading
from threading import Lock, Timer, Event
from time import sleep

import re

from autopts.wid import generic_wid_hdl
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams, UUID, gap_settings_btp2txt, AdType, AdFlags, IOCap
from autopts.pybtp.types import L2CAPConnectionResponse

log = logging.debug


def gap_wid_hdl(wid, description, test_case_name):
    log(f'{gap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.gap'])


def hdl_wid_104(params: WIDParams):
    if (params.test_case_name.startswith("GAP/DM/NBON/BV-01-C")):
        btp.gap_set_bondable_off()
    return True


def hdl_wid_114(_: WIDParams):
    return True


def hdl_wid_162(_: WIDParams):
    return True


def hdl_wid_224(_: WIDParams):
    return True

def hdl_wid_7(params: WIDParams):
    stack = get_stack()
    stack.gap.reset_discovery()
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='limited')
    sleep(20)  # Give some time to discover devices
    # btp.gap_stop_discov()
    ret = btp.check_discov_results(discovered=True)
    if False == ret:
        return False
    stack.gap.reset_discovery()
    btp.gap_start_discov(mode='limited')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    ret = btp.check_discov_results(discovered=True)
    if False == ret:
        return False
    return True

# Please make IUT not discoverable. Press OK to continue.
def hdl_wid_31(_: WIDParams):
    btp.gap_set_nonconn()
    return True

def hdl_wid_32(_: WIDParams):
    btp.gap_set_limdiscov()
    return True

l2cal_server_count = 0

def hdl_wid_33(params: WIDParams):
    global l2cal_server_count
    if (params.test_case_name.startswith("GAP/MOD/NBON/BV-03-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BI-24-C")):
        btp.gap_set_io_cap(IOCap.no_input_output)
    if params.test_case_name.startswith("GAP/SEC/SEM/BV-02-C"):
        btp.gap_set_io_cap(IOCap.keyboard_display)
        btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
    if params.test_case_name.startswith("GAP/SEC/SEM/BV-10-C"):
        btp.gap_set_io_cap(IOCap.no_input_output)
        btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
    if params.test_case_name.startswith("GAP/SEC/SEM/BI-24-C"):
        btp.gap_set_io_cap(IOCap.no_input_output)
        if (0 == l2cal_server_count):
            btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
            l2cal_server_count += 1
    btp.gap_set_gendiscov()
    return True

def hdl_wid_34(_: WIDParams):
    btp.gap_set_nonconn()
    return True

def hdl_wid_36(_: WIDParams):
    btp.gap_set_gendiscov()
    return True

def hdl_wid_145(_: WIDParams):
    timeout = 0
    while True:
        stack = get_stack()
        if not stack.gap.current_settings_get(
            gap_settings_btp2txt[defs.GAP_SETTINGS_DISCOVERABLE]):
            return True
        else:
            sleep(5)
            timeout += 5
        if timeout >= 60:
            break
    return False

def hdl_wid_78(params: WIDParams):
    if params.test_case_name.startswith("GAP/CONN/ACEP"):
        # Use LE ANY addr to trigger auto connection establishment procedure
        btp.gap_conn(b"00:00:00:00:00:00", 0)
    elif params.test_case_name.startswith("GAP/DM/NBON/BV-01-C"):
        # btp.gap_start_discov(transport='le', discov_type='active', mode='observe')
        sleep(3)  # Give some time to discover devices
        # btp.gap_stop_discov()
        btp.gap_conn()
    else:
        btp.gap_conn()

    return True

def hdl_wid_86(params: WIDParams):
    stack = get_stack()
    stack.gap.reset_discovery()
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='general')
    sleep(20)  # Give some time to discover devices
    # btp.gap_stop_discov()
    ret = btp.check_discov_results(discovered=True)
    if False == ret:
        return False
    return True

def hdl_wid_102(params: WIDParams):
    if (params.test_case_name.startswith("GAP/IDLE/BON/BV-03-C")
        or params.test_case_name.startswith("GAP/IDLE/BON/BV-05-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-05-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-50-C")
        or params.test_case_name.startswith("GAP/DM/BON/BV-01-C")):
        btp.gap_set_io_cap(IOCap.no_input_output)
    elif (params.test_case_name.startswith("GAP/IDLE/BON/BV-04-C")
          or params.test_case_name.startswith("GAP/IDLE/BON/BV-06-C")
          or params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")
          or params.test_case_name.startswith("GAP/SEC/SEM/BV-07-C")
          or params.test_case_name.startswith("GAP/SEC/SEM/BV-51-C")
          or params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")):
        btp.gap_set_io_cap(IOCap.display_yesno)
    elif (params.test_case_name.startswith("GAP/SEC/SEM/BV-08-C")):
        btp.gap_set_io_cap(IOCap.no_input_output)
    else:
        btp.gap_set_io_cap(IOCap.keyboard_display)
    btp.gap_set_gendiscov()
    sleep(15)
    btp.gap_conn(transport=defs.GAP_CONNECT_BREDR)
    btp.gap_wait_for_connection()
    if params.test_case_name.startswith("GAP/IDLE/BON/BV-04-C") or params.test_case_name.startswith("GAP/IDLE/BON/BV-06-C"):
        btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.insufficient_authentication)
    if not (params.test_case_name.startswith("GAP/IDLE/BON/BV-05-C")
        or params.test_case_name.startswith("GAP/IDLE/BON/BV-06-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-05-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-07-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-08-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-09-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-50-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-51-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")):
        btp.gap_pair()
    if params.test_case_name.startswith("GAP/IDLE/BON/BV-02-C"):
        btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
        btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
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

def hdl_wid_103(params: WIDParams):
    global l2cal_server_count
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-05-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-07-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-51-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")):
        btp.gap_set_bondable_off()

    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-50-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")
        or params.test_case_name.startswith("GAP/SEC/SEM/BV-51-C")):
        btp.gap_pair()
    if params.test_case_name.startswith("GAP/SEC/SEM/BV-08-C"):
        # btp.gap_set_io_cap(IOCap.no_input_output)
        # btp.gap_set_gendiscov()
        # sleep(15)
        btp.gap_conn(transport=defs.GAP_CONNECT_BREDR)
        btp.gap_wait_for_connection()
    else:
        if (params.test_case_name.startswith("GAP/SEC/SEM/BV-06-C")
            or params.test_case_name.startswith("GAP/SEC/SEM/BV-07-C")
            or params.test_case_name.startswith("GAP/SEC/SEM/BV-51-C")
            or params.test_case_name.startswith("GAP/SEC/SEM/BV-52-C")):
            btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.insufficient_authentication)
        elif (params.test_case_name.startswith("GAP/SEC/SEM/BV-09-C")):
            if l2cal_server_count == 0:
                btp.l2cap_listen(psm=0x2001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.success)
            else:
                btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.insufficient_authentication)
        else:
            btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.success)
    if (params.test_case_name.startswith("GAP/SEC/SEM/BV-09-C")):
        stack = get_stack()
        if l2cal_server_count == 0:
            stack.l2cap_init(psm=0x2001, initial_mtu=60)
            btp.l2cap_conn(None, None, psm=0x2001,mtu=60)
            wait_for_confirm_passkey()
        else:
            stack.l2cap_init(psm=0x1001, initial_mtu=60)
            btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    else:
        btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    if params.test_case_name.startswith("GAP/SEC/SEM/BV-09-C"):
        l2cal_server_count += 1
    return True

def hdl_wid_105(_: WIDParams):
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True

def hdl_wid_108(params: WIDParams):
    if not (params.test_case_name.startswith("GAP/DM/BON/BV-01-C")):
        btp.gap_pair()
    return True

def hdl_wid_123(_: WIDParams):
    stack = get_stack()
    stack.gap.reset_discovery()
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='limited')
    sleep(20)  # Give some time to discover devices
    # btp.gap_stop_discov()
    ret = btp.check_discov_results(discovered=False)
    if False == ret:
        return False
    stack.gap.reset_discovery()
    btp.gap_start_discov(mode='limited')
    sleep(10)  # Give some time to discover devices
    btp.gap_stop_discov()
    ret = btp.check_discov_results(discovered=False)
    if False == ret:
        return False
    return True

def hdl_wid_146(_: WIDParams):
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='general')
    return True

def hdl_wid_147(_: WIDParams):
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='limited')
    return True

def hdl_wid_151(_:WIDParams):
    btp.gap_set_bondable_on()
    return True

def hdl_wid_160(_: WIDParams):
    btp.gap_set_limdiscov()
    return True

def hdl_wid_164(_: WIDParams):
    return True

def hdl_wid_165(params: WIDParams):
    btp.gap_start_discov(transport='bredr', discov_type='active', mode='general')
    sleep(20)  # Give some time to discover devices
    # btp.gap_stop_discov()
    pts_name = re.findall(r'\'(.*)\'', params.description)
    if len(pts_name) > 0:
        pts_name = pts_name[0].encode('utf-8')
        pts_name = str(binascii.hexlify(pts_name)).lstrip('b\'').rstrip('\'').upper()
        return btp.check_scan_rep_and_rsp(pts_name, pts_name)
    else:
        return False

def hdl_wid_166(_: WIDParams):
    return True

def hdl_wid_167(_: WIDParams):
    return True

def hdl_wid_222(_: WIDParams):
    btp.gap_pair()
    return True

def hdl_wid_231(params: WIDParams):
    #case GAP/SEC/SEM/BV-08-C
    btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.success)
    btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    btp.gap_wait_for_sec_lvl_change(1)
    btp.gap_disconn()
    return True

def hdl_wid_251(params: WIDParams):
    btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
    btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    return True

def hdl_wid_264(params: WIDParams):
    sleep(2)
    if params.test_case_name.startswith("GAP/IDLE/BON/BV-04-C") or params.test_case_name.startswith("GAP/IDLE/BON/BV-06-C"):
        pass
    else:
        btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120)
    btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    return True

def hdl_wid_1301(_: WIDParams):
    return True

def hdl_wid_1302(_: WIDParams):
    return False

def hdl_wid_2001(params: WIDParams):
    """
    The secureId is [passkey]
    """
    pattern = '[\d]{6}'
    passkey = re.search(pattern, params.description)[0]
    stack = get_stack()
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()

    if stack.gap.get_passkey() is None:
        return False
    else:
        if "verify" in params.description:
            btp.gap_passkey_confirm_rsp(bd_addr, bd_addr_type, passkey)
        else:
            btp.gap_passkey_entry_rsp(bd_addr, bd_addr_type, passkey)
    return True

def hdl_wid_20117(_: WIDParams):
    btp.gap_pair()
    btp.l2cap_listen(psm=0x1001, transport=defs.L2CAP_TRANSPORT_BREDR, mtu=120, response=L2CAPConnectionResponse.success)
    btp.l2cap_conn(None, None, psm=0x1001,mtu=60)
    return True