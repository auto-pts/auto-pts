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
import sys
import btp
import time
import re
from ptsprojects.stack import get_stack

log = logging.debug

def mesh_wid_hdl(wid, description):
    log("%s, %r, %r", mesh_wid_hdl.__name__, wid, description)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        log("wid nb: %d, not implemented!", wid)


# wid handlers section begin
def hdl_wid_8(desc):
    stack = get_stack()

    ret = stack.mesh.oob_data.data

    # cleanup
    stack.mesh.oob_data.data = None
    stack.mesh.oob_data.action = None

    return str(ret)

def hdl_wid_12(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_13(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_17(desc):
    btp.mesh_store_net_data()

    return 'Ok'

def hdl_wid_18(desc):
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = False

    if stack.mesh.net_recv_ev_data.data is None:
        logging.error("Network Packet not received!")
        return 'No'

    # This pattern is matching Time to Live (TTL) value, Control (CTL),
    # Source (SRC) Destination (DST) and Payload of the network packet
    # to be received
    pattern = re.compile('(TTL|CTL|SRC|DST|TransportPDU)\\:\s+\\[([0][xX][0-9a-fA-F]+)\\]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_18.__name__)
        return 'No'

    params = dict(params)
    pdu = hex(int(params['TransportPDU'], 16))
    ttl = int(params.get('TTL'), 16)
    ctl = int(params.get('CTL'), 16)
    src = int(params.get('SRC'), 16)
    dst = int(params.get('DST'), 16)

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data
    recv_pdu = hex(int(recv_pdu, 16))

    if pdu == recv_pdu and ttl == recv_ttl and ctl == recv_ctl and \
                    src == recv_src and dst == recv_dst:
        return 'Yes'

    return 'No'

def hdl_wid_19(desc):
    stack = get_stack()

    # This pattern is matching Time to Live (TTL) value, Source (SRC) and
    # Destination (DST) of the network packet to be sent
    pattern = re.compile('(TTL|SRC|DST)\\:\s+\\[([0][xX][0-9a-fA-F]+)\\]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_19.__name__)
        return 'Cancel'

    params = dict(params)

    btp.mesh_net_send(params.get('TTL', None), params.get('SRC'),
                      params.get('DST'), '01020304')

    return 'Ok'

def hdl_wid_20(desc):
    stack = get_stack()

    return 'C000'

def hdl_wid_21(desc):
    stack = get_stack()

    return '8000'

def hdl_wid_24(desc):
    stack = get_stack()

    if stack.mesh.last_seen_prov_link_state.data is None:
        logging.error("The link state is None")
        return 'No'

    (state, bearer) = stack.mesh.last_seen_prov_link_state.data

    if state == 'closed':
        return 'Yes'
    return 'No'

def hdl_wid_30(desc):
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = False

    if stack.mesh.net_recv_ev_data.data is None:
        return 'Yes'

    # This pattern is matching Time to Live (TTL) value, Control (CTL),
    # Source (SRC) Destination (DST) and Payload of the network packet
    # to be received
    pattern = re.compile('(TTL|CTL|SRC|DST|TransportPDU)\\:\s+\\[([0][xX][0-9a-fA-F]+)\\]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_30.__name__)
        return 'No'

    params = dict(params)

    # Normalize parameters for comparison
    pdu = hex(int(params['TransportPDU'], 16))
    ttl = int(params.get('TTL'), 16)
    ctl = int(params.get('CTL'), 16)
    src = int(params.get('SRC'), 16)
    dst = int(params.get('DST'), 16)

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data
    recv_pdu = hex(int(recv_pdu, 16))

    if pdu == recv_pdu and ttl == recv_ttl and ctl == recv_ctl and \
                    src == recv_src and dst == recv_dst:
        logging.error("%s Network Packet received!", hdl_wid_30.__name__)
        return 'No'

    return 'Yes'

def hdl_wid_81(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_90(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_201(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_202(desc):
    stack = get_stack()

    btp.mesh_iv_update_test_mode(True)
    btp.mesh_iv_update_toggle()

    return 'OK'

def hdl_wid_203(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_204(desc):
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_210(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == False:
        btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
        btp.mesh_init()
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_216(desc):
    stack = get_stack()

    if not stack.mesh.is_iv_test_mode_enabled.data:
        return 'OK'
    return 'Cancel'

def hdl_wid_217(desc):
    stack = get_stack()

    if not stack.mesh.is_iv_test_mode_enabled.data:
        btp.mesh_iv_update_test_mode(True)

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_218(desc):
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_219(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data:
        return 'OK'
    return 'Cancel'

def hdl_wid_220(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data:
        return 'OK'
    return 'Cancel'

def hdl_wid_221(desc):
    stack = get_stack()

    if not stack.mesh.is_iv_test_mode_enabled.data:
        btp.mesh_iv_update_test_mode(True)

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_222(desc):
    stack = get_stack()

    btp.mesh_iv_update_toggle()

    return 'OK'

def hdl_wid_262(desc):
    return 'Yes'

def hdl_wid_268(desc):
    stack = get_stack()

    return 'OK'

def hdl_wid_274(desc):
    stack = get_stack()

    return 'OK'

def hdl_wid_285(desc):
    stack = get_stack()

    return 'Yes'

def hdl_wid_303(desc):
    stack = get_stack()

    return 'Ok'

def hdl_wid_308(desc):
    stack = get_stack()

    btp.mesh_lpn_poll()
    return 'Ok'

def hdl_wid_312(desc):
    stack = get_stack()

    btp.mesh_lpn_poll()
    return 'Ok'

def hdl_wid_313(desc):
    stack = get_stack()

    btp.mesh_lpn_poll()
    return 'Ok'

def hdl_wid_314(desc):
    stack = get_stack()

    btp.mesh_lpn_poll()
    return 'Ok'

def hdl_wid_315(desc):
    stack = get_stack()

    return 'Ok'

def hdl_wid_326(desc):
    stack = get_stack()

    btp.mesh_lpn(False)
    return "Ok"

def hdl_wid_519(desc):
    stack = get_stack()

    btp.mesh_reset()
    return 'OK'

def hdl_wid_600(desc):
    stack = get_stack()

    test_id, cur_faults, reg_faults = btp.mesh_health_generate_faults()

    stack.mesh.health_test_id.data = test_id
    stack.mesh.health_current_faults.data = cur_faults
    stack.mesh.health_registered_faults.data = reg_faults

    return 'OK'

def hdl_wid_601(desc):
    stack = get_stack()

    # This pattern is matching fault array
    pattern = re.compile('array\s=\s([0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_601.__name__)
        return 'Cancel'

    current_faults = stack.mesh.health_current_faults.data

    if params[0].upper() != current_faults.upper():
        logging.error("Fault array does not match %r vs %r", params[0],
                      current_faults)
        return 'Cancel'

    return 'Ok'

def hdl_wid_603(desc):
    stack = get_stack()

    # Pattern looking for test ID
    pattern = re.compile(r"(ID)\s+([0-9a-fA-F]+)", re.IGNORECASE)
    found = pattern.findall(desc)
    if not found:
        logging.error("%s Parsing error!", hdl_wid_603.__name__)
        return 'Cancel'

    found = dict(found)

    # Fail if test ID does not match or IUT has faults
    if int(stack.mesh.health_test_id.data) != int(found.get('ID')) or \
            stack.mesh.health_registered_faults.data:
        return 'Cancel'

    return 'OK'

def hdl_wid_604(desc):
    stack = get_stack()

    # Pattern looking for fault array and test ID
    pattern = re.compile(r"(array|ID)\s+([0-9a-fA-F]+)", re.IGNORECASE)
    found = pattern.findall(desc)
    if not found:
        logging.error("%s Parsing error!", hdl_wid_604.__name__)
        return 'Cancel'

    found = dict(found)

    if int(stack.mesh.health_test_id.data) != int(found.get('ID')) or \
            stack.mesh.health_registered_faults.data != found.get('array'):
        return 'Cancel'

    return 'OK'
