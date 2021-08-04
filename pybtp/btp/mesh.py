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

"""Wrapper around btp messages. The functions are added as needed."""

import binascii
import logging
import struct
from ptsprojects.stack import get_stack
from pybtp import defs
from .btp import CONTROLLER_INDEX, get_iut_method as get_iut
from pybtp.types import BTPError

MESH = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "config_prov": (defs.BTP_SERVICE_ID_MESH,
                    defs.MESH_CONFIG_PROVISIONING,
                    CONTROLLER_INDEX),
    "prov_node": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_PROVISION_NODE,
                  CONTROLLER_INDEX),
    "init": (defs.BTP_SERVICE_ID_MESH,
             defs.MESH_INIT,
             CONTROLLER_INDEX, ""),
    "reset": (defs.BTP_SERVICE_ID_MESH,
              defs.MESH_RESET,
              CONTROLLER_INDEX, ""),
    "input_num": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_INPUT_NUMBER,
                  CONTROLLER_INDEX),
    "input_str": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_INPUT_STRING,
                  CONTROLLER_INDEX),
    "iv_update_test_mode": (defs.BTP_SERVICE_ID_MESH,
                            defs.MESH_IV_UPDATE_TEST_MODE,
                            CONTROLLER_INDEX),
    "iv_update_toggle": (defs.BTP_SERVICE_ID_MESH,
                         defs.MESH_IV_UPDATE_TOGGLE,
                         CONTROLLER_INDEX, ""),
    "net_send": (defs.BTP_SERVICE_ID_MESH,
                 defs.MESH_NET_SEND,
                 CONTROLLER_INDEX),
    "health_generate_faults": (defs.BTP_SERVICE_ID_MESH,
                               defs.MESH_HEALTH_ADD_FAULTS,
                               CONTROLLER_INDEX, ""),
    "mesh_clear_faults": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_HEALTH_CLEAR_FAULTS,
                          CONTROLLER_INDEX, ""),
    "lpn": (defs.BTP_SERVICE_ID_MESH,
            defs.MESH_LPN_SET,
            CONTROLLER_INDEX),
    "lpn_poll": (defs.BTP_SERVICE_ID_MESH,
                 defs.MESH_LPN_POLL,
                 CONTROLLER_INDEX, ""),
    "model_send": (defs.BTP_SERVICE_ID_MESH,
                   defs.MESH_MODEL_SEND,
                   CONTROLLER_INDEX),
    "lpn_subscribe": (defs.BTP_SERVICE_ID_MESH,
                      defs.MESH_LPN_SUBSCRIBE,
                      CONTROLLER_INDEX),
    "lpn_unsubscribe": (defs.BTP_SERVICE_ID_MESH,
                        defs.MESH_LPN_UNSUBSCRIBE,
                        CONTROLLER_INDEX),
    "rpl_clear": (defs.BTP_SERVICE_ID_MESH,
                  defs.MESH_RPL_CLEAR,
                  CONTROLLER_INDEX, ""),
    "proxy_identity": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_PROXY_IDENTITY,
                       CONTROLLER_INDEX, ""),
}


def mesh_config_prov():
    logging.debug("%s", mesh_config_prov.__name__)

    iutctl = get_iut()

    stack = get_stack()

    uuid = binascii.unhexlify(stack.mesh.dev_uuid)
    static_auth = binascii.unhexlify(stack.mesh.static_auth)
    output_size = stack.mesh.output_size
    output_actions = stack.mesh.output_actions
    input_size = stack.mesh.input_size
    input_actions = stack.mesh.input_actions

    data = bytearray(struct.pack("<16s16sBHBH", uuid, static_auth, output_size,
                                 output_actions, input_size, input_actions))

    iutctl.btp_socket.send_wait_rsp(*MESH['config_prov'], data=data)


def mesh_prov_node():
    logging.debug("%s", mesh_config_prov.__name__)

    stack = get_stack()

    net_key = binascii.unhexlify(stack.mesh.net_key)
    dev_key = binascii.unhexlify(stack.mesh.dev_key)

    data = bytearray(struct.pack("<16sHBIIH16s", net_key,
                                 stack.mesh.net_key_idx, stack.mesh.flags,
                                 stack.mesh.iv_idx, stack.mesh.seq_num,
                                 stack.mesh.addr, dev_key))

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['prov_node'], data=data)


def mesh_init():
    logging.debug("%s", mesh_init.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['init'])

    stack = get_stack()

    stack.mesh.is_initialized = True
    if stack.mesh.iv_test_mode_autoinit:
        mesh_iv_update_test_mode(True)


def mesh_reset():
    logging.debug("%s", mesh_reset.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['reset'])

    stack = get_stack()

    stack.mesh.is_provisioned.data = False
    stack.mesh.is_initialized = True


def mesh_input_number(number):
    logging.debug("%s %r", mesh_input_number.__name__, number)

    iutctl = get_iut()

    if isinstance(number, str):
        number = int(number)

    data = bytearray(struct.pack("<I", number))

    iutctl.btp_socket.send_wait_rsp(*MESH['input_num'], data=data)


def mesh_input_string(string):
    logging.debug("%s %s", mesh_input_string.__name__, string)

    iutctl = get_iut()

    data = bytearray(string)

    iutctl.btp_socket.send_wait_rsp(*MESH['input_str'], data=data)


def mesh_iv_update_test_mode(enable):
    logging.debug("%s", mesh_iv_update_test_mode.__name__)

    iutctl = get_iut()

    if enable:
        data = bytearray(struct.pack("<B", 0x01))
    else:
        data = bytearray(struct.pack("<B", 0x00))

    iutctl.btp_socket.send_wait_rsp(*MESH['iv_update_test_mode'], data=data)

    stack = get_stack()
    stack.mesh.is_iv_test_mode_enabled.data = True


def mesh_iv_update_toggle():
    logging.debug("%s", mesh_iv_update_toggle.__name__)

    iutctl = get_iut()

    iutctl.btp_socket.send(*MESH['iv_update_toggle'])
    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    if tuple_hdr.op == defs.BTP_STATUS:
        logging.info("IV Update in progress")


def mesh_net_send(ttl, src, dst, payload):
    logging.debug("%s %r %r %r %r", mesh_net_send.__name__, ttl, src, dst,
                  payload)

    if ttl is None:
        ttl = 0xff  # Use default TTL
    elif isinstance(ttl, str):
        ttl = int(ttl, 16)

    if isinstance(src, str):
        src = int(src, 16)

    if isinstance(dst, str):
        dst = int(dst, 16)

    payload = binascii.unhexlify(payload)
    payload_len = len(payload)

    if payload_len > 0xff:
        raise BTPError("Payload exceeds PDU")

    data = bytearray(struct.pack("<BHHB", ttl, src, dst, payload_len))
    data.extend(payload)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['net_send'], data=data)


def mesh_health_generate_faults():
    logging.debug("%s", mesh_health_generate_faults.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_generate_faults'])

    hdr_fmt = '<BBB'
    hdr_len = struct.calcsize(hdr_fmt)

    (test_id, cur_faults_cnt, reg_faults_cnt) = \
        struct.unpack_from(hdr_fmt, rsp)
    (cur_faults,) = struct.unpack_from('<%ds' % cur_faults_cnt, rsp, hdr_len)
    (reg_faults,) = struct.unpack_from('<%ds' % reg_faults_cnt, rsp,
                                       hdr_len + cur_faults_cnt)

    cur_faults = binascii.hexlify(cur_faults)
    reg_faults = binascii.hexlify(reg_faults)

    return test_id, cur_faults, reg_faults


def mesh_health_clear_faults():
    logging.debug("%s", mesh_health_clear_faults.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['mesh_clear_faults'])


def mesh_lpn(enable):
    logging.debug("%s %r", mesh_lpn.__name__, enable)

    if enable:
        enable = 0x01
    else:
        enable = 0x00

    data = bytearray(struct.pack("<B", enable))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn'], data=data)


def mesh_lpn_poll():
    logging.debug("%s", mesh_lpn_poll.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_poll'])


def mesh_model_send(src, dst, payload):
    logging.debug("%s %r %r %r", mesh_model_send.__name__, src, dst, payload)

    if isinstance(src, str):
        src = int(src, 16)

    if isinstance(dst, str):
        dst = int(dst, 16)

    payload = binascii.unhexlify(payload)
    payload_len = len(payload)

    if payload_len > 0xff:
        raise BTPError("Payload exceeds PDU")

    data = bytearray(struct.pack("<HHB", src, dst, payload_len))
    data.extend(payload)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['model_send'], data=data)


def mesh_lpn_subscribe(address):
    logging.debug("%s %r", mesh_lpn_subscribe.__name__, address)

    if isinstance(address, str):
        address = int(address, 16)

    data = bytearray(struct.pack("<H", address))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_subscribe'], data=data)


def mesh_lpn_unsubscribe(address):
    logging.debug("%s %r", mesh_lpn_unsubscribe.__name__, address)

    if isinstance(address, str):
        address = int(address, 16)

    data = bytearray(struct.pack("<H", address))

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['lpn_unsubscribe'], data=data)


def mesh_rpl_clear():
    logging.debug("%s", mesh_rpl_clear.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['rpl_clear'])


def mesh_proxy_identity():
    logging.debug("%s", mesh_proxy_identity.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*MESH['proxy_identity'])


def mesh_out_number_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_out_number_action_ev.__name__, data)

    action, number = struct.unpack_from('<HI', data)

    mesh.oob_action.data = action
    mesh.oob_data.data = number


def mesh_out_string_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_out_string_action_ev.__name__, data)

    hdr_fmt = '<B'
    hdr_len = struct.calcsize(hdr_fmt)

    (str_len,) = struct.unpack_from(hdr_fmt, data)
    (string,) = struct.unpack_from('<%ds' % str_len, data, hdr_len)

    mesh.oob_data.data = string


def mesh_in_action_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_in_action_ev.__name__, data)

    action, size = struct.unpack('<HB', data)


def mesh_provisioned_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_provisioned_ev.__name__, data)
    stack = get_stack()

    mesh.is_provisioned.data = True

    if stack.mesh.proxy_identity:
        mesh_proxy_identity()


def mesh_prov_link_open_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_open_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('open', bearer)


def mesh_prov_link_closed_ev(mesh, data, data_len):
    logging.debug("%s %r", mesh_prov_link_closed_ev.__name__, data)

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('closed', bearer)


def mesh_store_net_data():
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = True


def mesh_iv_test_mode_autoinit():
    stack = get_stack()

    stack.mesh.iv_test_mode_autoinit = True


def mesh_net_rcv_ev(mesh, data, data_len):
    stack = get_stack()

    if not stack.mesh.net_recv_ev_store.data:
        return

    logging.debug("%s %r %r", mesh_net_rcv_ev.__name__, data, data_len)

    hdr_fmt = '<BBHHB'
    hdr_len = struct.calcsize(hdr_fmt)

    (ttl, ctl, src, dst, payload_len) = struct.unpack_from(hdr_fmt, data, 0)
    (payload,) = struct.unpack_from('<%ds' % payload_len, data, hdr_len)
    payload = binascii.hexlify(payload)

    stack.mesh.net_recv_ev_data.data = (ttl, ctl, src, dst, payload)


def mesh_invalid_bearer_ev(mesh, data, data_len):
    stack = get_stack()

    logging.debug("%s %r %r", mesh_invalid_bearer_ev.__name__, data, data_len)

    hdr_fmt = '<B'
    (opcode,) = struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.prov_invalid_bearer_rcv.data = True


def mesh_incomp_timer_exp_ev(mesh, data, data_len):
    logging.debug("%s", mesh_incomp_timer_exp_ev.__name__)

    stack = get_stack()

    stack.mesh.incomp_timer_exp.data = True


def mesh_frnd_established_ev(mesh, data, data_len):
    logging.debug("%s", mesh_frnd_established_ev.__name__)

    stack = get_stack()

    hdr_fmt = '<HHBI'

    (net_idx, lpn_addr, recv_delay, polltimeout) = \
        struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.friendship.data = True


def mesh_frnd_terminated_ev(mesh, data, data_len):
    logging.debug("%s", mesh_frnd_terminated_ev.__name__)

    stack = get_stack()

    hdr_fmt = '<HH'

    (net_idx, lpn_addr) = struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.friendship.data = False


def mesh_lpn_established_ev(mesh, data, data_len):
    logging.debug("%s", mesh_lpn_established_ev.__name__)

    stack = get_stack()

    hdr_fmt = '<HHBB'

    (net_idx, frnd_addr, queue_size, recv_win) = \
        struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.lpn.data = True


def mesh_lpn_terminated_ev(mesh, data, data_len):
    logging.debug("%s", mesh_lpn_terminated_ev.__name__)

    stack = get_stack()

    hdr_fmt = '<HH'

    (net_idx, frnd_addr) = struct.unpack_from(hdr_fmt, data, 0)

    stack.mesh.lpn.data = False


def mesh_lpn_polled_ev(mesh, data, data_len):
    logging.debug("%s", mesh_lpn_polled_ev.__name__)

    hdr_fmt = '<HHB'

    (net_idx, frnd_addr, retry) = struct.unpack_from(hdr_fmt, data, 0)


def mesh_prov_node_added_ev(mesh, data, data_len):
    logging.debug("%s", mesh_prov_node_added_ev.__name__)

    hdr_fmt = '<HH16sB'

    (net_idx, addr, uuid, num_elems) = struct.unpack_from(hdr_fmt, data, 0)

    logging.debug("0x%04x 0x%04x %r %u", net_idx, addr, uuid, num_elems)


MESH_EV = {
    defs.MESH_EV_OUT_NUMBER_ACTION: mesh_out_number_action_ev,
    defs.MESH_EV_OUT_STRING_ACTION: mesh_out_string_action_ev,
    defs.MESH_EV_IN_ACTION: mesh_in_action_ev,
    defs.MESH_EV_PROVISIONED: mesh_provisioned_ev,
    defs.MESH_EV_PROV_LINK_OPEN: mesh_prov_link_open_ev,
    defs.MESH_EV_PROV_LINK_CLOSED: mesh_prov_link_closed_ev,
    defs.MESH_EV_NET_RECV: mesh_net_rcv_ev,
    defs.MESH_EV_INVALID_BEARER: mesh_invalid_bearer_ev,
    defs.MESH_EV_INCOMP_TIMER_EXP: mesh_incomp_timer_exp_ev,
    defs.MESH_EV_FRND_ESTABLISHED: mesh_frnd_established_ev,
    defs.MESH_EV_FRND_TERMINATED: mesh_frnd_terminated_ev,
    defs.MESH_EV_LPN_ESTABLISHED: mesh_lpn_established_ev,
    defs.MESH_EV_LPN_TERMINATED: mesh_lpn_terminated_ev,
    defs.MESH_EV_LPN_POLLED: mesh_lpn_polled_ev,
    defs.MESH_EV_PROV_NODE_ADDED: mesh_prov_node_added_ev,
}
