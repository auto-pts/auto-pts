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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.types import BTPError
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

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
    "composition_data_get": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_COMP_DATA_GET,
                             CONTROLLER_INDEX),
    "cfg_beacon_get": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_BEACON_GET,
                       CONTROLLER_INDEX),
    "cfg_beacon_set": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_BEACON_SET,
                       CONTROLLER_INDEX),
    "cfg_default_ttl_get": (defs.BTP_SERVICE_ID_MESH,
                            defs.MESH_CFG_DEFAULT_TTL_GET,
                            CONTROLLER_INDEX),
    "cfg_default_ttl_set": (defs.BTP_SERVICE_ID_MESH,
                            defs.MESH_CFG_DEFAULT_TTL_SET,
                            CONTROLLER_INDEX),
    "cfg_gatt_proxy_get": (defs.BTP_SERVICE_ID_MESH,
                           defs.MESH_CFG_GATT_PROXY_GET,
                           CONTROLLER_INDEX),
    "cfg_gatt_proxy_set": (defs.BTP_SERVICE_ID_MESH,
                           defs.MESH_CFG_GATT_PROXY_SET,
                           CONTROLLER_INDEX),
    "cfg_friend_get": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_FRIEND_GET,
                       CONTROLLER_INDEX),
    "cfg_friend_set": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_FRIEND_SET,
                       CONTROLLER_INDEX),
    "cfg_relay_get": (defs.BTP_SERVICE_ID_MESH,
                      defs.MESH_CFG_RELAY_GET,
                      CONTROLLER_INDEX),
    "cfg_relay_set": (defs.BTP_SERVICE_ID_MESH,
                      defs.MESH_CFG_RELAY_SET,
                      CONTROLLER_INDEX),
    "cfg_model_pub_get": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_PUB_GET,
                          CONTROLLER_INDEX),
    "cfg_model_pub_set": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_PUB_SET,
                          CONTROLLER_INDEX),
    "cfg_model_sub_add": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_SUB_ADD,
                          CONTROLLER_INDEX),
    "cfg_model_sub_del": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_SUB_DEL,
                          CONTROLLER_INDEX),
    "cfg_netkey_add": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_NETKEY_ADD,
                       CONTROLLER_INDEX),
    "cfg_netkey_get": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_NETKEY_GET,
                       CONTROLLER_INDEX),
    "cfg_netkey_del": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_NETKEY_DEL,
                       CONTROLLER_INDEX),
    "cfg_appkey_add": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_APPKEY_ADD,
                       CONTROLLER_INDEX),
    "cfg_appkey_del": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_APPKEY_DEL,
                       CONTROLLER_INDEX),
    "cfg_appkey_get": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_APPKEY_GET,
                       CONTROLLER_INDEX),
    "cfg_model_app_bind": (defs.BTP_SERVICE_ID_MESH,
                           defs.MESH_CFG_MODEL_APP_BIND,
                           CONTROLLER_INDEX),
    "cfg_model_app_unbind": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_MODEL_APP_UNBIND,
                             CONTROLLER_INDEX),
    "cfg_model_app_get": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_APP_GET,
                          CONTROLLER_INDEX),
    "cfg_model_app_vnd_get": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_MODEL_APP_VND_GET,
                              CONTROLLER_INDEX),
    "cfg_heartbeat_pub_set": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_HEARTBEAT_PUB_SET,
                              CONTROLLER_INDEX),
    "cfg_heartbeat_pub_get": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_HEARTBEAT_PUB_GET,
                              CONTROLLER_INDEX),
    "cfg_heartbeat_sub_set": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_HEARTBEAT_SUB_SET,
                              CONTROLLER_INDEX),
    "cfg_heartbeat_sub_get": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_HEARTBEAT_SUB_GET,
                              CONTROLLER_INDEX),
    "cfg_net_transmit_get": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_NET_TRANSMIT_GET,
                             CONTROLLER_INDEX),
    "cfg_net_transmit_set": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_NET_TRANSMIT_SET,
                             CONTROLLER_INDEX),
    "cfg_model_sub_ovw": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_SUB_OVW,
                          CONTROLLER_INDEX),
    "cfg_model_sub_del_all": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_MODEL_SUB_DEL_ALL,
                              CONTROLLER_INDEX),
    "cfg_model_sub_get": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_MODEL_SUB_GET,
                          CONTROLLER_INDEX),
    "cfg_model_sub_vnd_get": (defs.BTP_SERVICE_ID_MESH,
                              defs.MESH_CFG_MODEL_SUB_VND_GET,
                              CONTROLLER_INDEX),
    "cfg_model_sub_va_add": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_MODEL_SUB_VA_ADD,
                             CONTROLLER_INDEX),
    "cfg_model_sub_va_del": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_MODEL_SUB_VA_DEL,
                             CONTROLLER_INDEX),
    "cfg_model_sub_va_ovw": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_MODEL_SUB_VA_OVW,
                             CONTROLLER_INDEX),
    "cfg_netkey_update": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_NETKEY_UPDATE,
                          CONTROLLER_INDEX),
    "cfg_appkey_update": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_CFG_APPKEY_UPDATE,
                          CONTROLLER_INDEX),
    "cfg_node_idt_set": (defs.BTP_SERVICE_ID_MESH,
                         defs.MESH_CFG_NODE_IDT_SET,
                         CONTROLLER_INDEX),
    "cfg_node_idt_get": (defs.BTP_SERVICE_ID_MESH,
                         defs.MESH_CFG_NODE_IDT_GET,
                         CONTROLLER_INDEX),
    "cfg_node_reset": (defs.BTP_SERVICE_ID_MESH,
                       defs.MESH_CFG_NODE_RESET,
                       CONTROLLER_INDEX),
    "cfg_lpn_polltimeout_get": (defs.BTP_SERVICE_ID_MESH,
                                defs.MESH_CFG_LPN_POLLTIMEOUT_GET,
                                CONTROLLER_INDEX),
    "cfg_model_pub_va_set": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_CFG_MODEL_PUB_VA_SET,
                             CONTROLLER_INDEX),
    "cfg_model_app_bind_vnd": (defs.BTP_SERVICE_ID_MESH,
                               defs.MESH_CFG_MODEL_APP_BIND_VND,
                               CONTROLLER_INDEX),
    "cfg_krp_get": (defs.BTP_SERVICE_ID_MESH,
                    defs.MESH_CFG_KRP_GET,
                    CONTROLLER_INDEX),
    "cfg_krp_set": (defs.BTP_SERVICE_ID_MESH,
                    defs.MESH_CFG_KRP_SET,
                    CONTROLLER_INDEX),
    "health_fault_get": (defs.BTP_SERVICE_ID_MESH,
                         defs.MESH_HEALTH_FAULT_GET,
                         CONTROLLER_INDEX),
    "health_fault_clear": (defs.BTP_SERVICE_ID_MESH,
                           defs.MESH_HEALTH_FAULT_CLEAR,
                           CONTROLLER_INDEX),
    "health_fault_test": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_HEALTH_FAULT_TEST,
                          CONTROLLER_INDEX),
    "health_period_get": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_HEALTH_PERIOD_GET,
                          CONTROLLER_INDEX),
    "health_period_set": (defs.BTP_SERVICE_ID_MESH,
                          defs.MESH_HEALTH_PERIOD_SET,
                          CONTROLLER_INDEX),
    "health_attention_get": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_HEALTH_ATTENTION_GET,
                             CONTROLLER_INDEX),
    "health_attention_set": (defs.BTP_SERVICE_ID_MESH,
                             defs.MESH_HEALTH_ATTENTION_SET,
                             CONTROLLER_INDEX),
    "provision_adv": (defs.BTP_SERVICE_ID_MESH,
                      defs.MESH_PROVISION_ADV,
                      CONTROLLER_INDEX),
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
    auth_method = stack.mesh.auth_metod

    data = bytearray(struct.pack("<16s16sBHBHB", uuid, static_auth, output_size,
                                 output_actions, input_size, input_actions, auth_method))

    pub_key = stack.mesh.pub_key_get()
    priv_key = stack.mesh.priv_key_get()

    if pub_key and priv_key:
        data.extend(struct.pack("<64s", binascii.unhexlify(pub_key)))
        data.extend(struct.pack("<32s", binascii.unhexlify(priv_key)))

    iutctl.btp_socket.send_wait_rsp(*MESH['config_prov'], data=data)


def mesh_prov_node():
    logging.debug("%s", mesh_prov_node.__name__)

    stack = get_stack()

    net_key = binascii.unhexlify(stack.mesh.net_key)
    dev_key = binascii.unhexlify(stack.mesh.dev_key)

    data = bytearray(struct.pack("<16sHBIIH16s", net_key,
                                 stack.mesh.net_key_idx, stack.mesh.flags,
                                 stack.mesh.iv_idx, stack.mesh.seq_num,
                                 stack.mesh.address_iut, dev_key))
    pub_key = stack.mesh.pub_key_get()
    if pub_key:
        data.extend(struct.pack("<64s", binascii.unhexlify(pub_key)))

    iutctl = get_iut()

    iutctl.btp_socket.send_wait_rsp(*MESH['prov_node'], data=data)


def mesh_provision_adv(uuid, addr, attention_duration):
    logging.debug("%s %r %r %r", mesh_provision_adv.__name__, uuid, addr, attention_duration)

    iutctl = get_iut()
    stack = get_stack()
    uuid = binascii.unhexlify(uuid)
    net_key = binascii.unhexlify(stack.mesh.net_key)

    data = bytearray(struct.pack("<16sHHB16s", uuid, stack.mesh.net_key_idx, addr, attention_duration, net_key))

    iutctl.btp_socket.send_wait_rsp(*MESH['provision_adv'], data=data)

    stack.mesh.provisioning_in_progress.data = True


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

    string_len = len(string)

    data = bytearray(struct.pack("<B", string_len))
    data.extend(string.encode('UTF-8'))

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
    stack = get_stack()

    (bearer,) = struct.unpack('<B', data)

    mesh.last_seen_prov_link_state.data = ('closed', bearer)

    stack.mesh.provisioning_in_progress.data = False


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


def mesh_cfg_beacon_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_beacon_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_beacon_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_beacon_set(net_idx, addr, val):
    logging.debug("%s", mesh_cfg_beacon_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_beacon_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_composition_data_get(net_idx, addr, page):
    logging.debug("%s", mesh_composition_data_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, page))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['composition_data_get'], data)

    (status,) = struct.unpack_from('<B', rsp)


def mesh_cfg_krp_get(net_idx, addr, net_key_idx):
    logging.debug("%s", mesh_cfg_krp_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", net_idx, addr, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_krp_get'], data)

    (status, phase) = struct.unpack_from('<BB', rsp)
    stack.mesh.status = status
    stack.mesh.data = phase


def mesh_cfg_krp_set(net_idx, addr, net_key_idx, phase):
    logging.debug("%s", mesh_cfg_krp_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHB", net_idx, addr, net_key_idx, phase))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_krp_set'], data)

    (status, phase) = struct.unpack_from('<BB', rsp)
    stack.mesh.status = status
    stack.mesh.data = phase


def mesh_cfg_default_ttl_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_default_ttl_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_default_ttl_get'], data)

    (ttl,) = struct.unpack_from('<B', rsp)


def mesh_cfg_default_ttl_set(net_idx, addr, val):
    logging.debug("%s", mesh_cfg_default_ttl_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_default_ttl_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_gatt_proxy_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_gatt_proxy_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_gatt_proxy_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_gatt_proxy_set(net_idx, addr, val):
    logging.debug("%s", mesh_cfg_gatt_proxy_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_gatt_proxy_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_friend_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_friend_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH",net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_friend_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_friend_set(net_idx, addr, val):
    logging.debug("%s", mesh_cfg_friend_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_friend_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_relay_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_relay_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_relay_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_relay_set(net_idx, addr, new_relay, new_transmit):
    logging.debug("%s", mesh_cfg_relay_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHBB", net_idx, addr, new_relay, new_transmit))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_relay_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.value = status


def mesh_cfg_model_publication_get(net_idx, addr, el_address, model_id):
    logging.debug("%s", mesh_cfg_model_publication_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHH", net_idx, addr, el_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_pub_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_publication_set(net_idx, addr, el_address, model_id, pub_addr, appkey_index,
                                      cred_flag, ttl, period, transmit):
    logging.debug("%s", mesh_cfg_model_publication_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHHHBBBB", net_idx, addr, el_address, model_id, pub_addr,
                                 appkey_index, cred_flag, ttl, period, transmit))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_pub_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_pub_va_set(net_idx, addr, el_address, model_id, uuid, appkey_index,
                                 cred_flag, ttl, period, transmit):
    logging.debug("%s", mesh_cfg_model_pub_va_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    uuid = binascii.unhexlify(uuid)

    data = bytearray(struct.pack("<HHHHHBBBB16s", net_idx, addr, el_address, model_id, appkey_index,
                                 cred_flag, ttl, period, transmit, uuid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_pub_va_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_add(net_idx, addr, el_address, sub_address, model_id):
    logging.debug("%s", mesh_cfg_model_sub_add.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, sub_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_add'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_del(net_idx, addr, el_address, sub_address, model_id):
    logging.debug("%s", mesh_cfg_model_sub_del.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, sub_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_del'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_ovw(net_idx, addr, el_address, sub_address, model_id):
    logging.debug("%s", mesh_cfg_model_sub_ovw.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, sub_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_ovw'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_del_all(net_idx, addr, el_address, model_id):
    logging.debug("%s", mesh_cfg_model_sub_del_all.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHH", net_idx, addr, el_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_del_all'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_get(net_idx, addr, el_address, model_id):
    logging.debug("%s", mesh_cfg_model_sub_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHH", net_idx, addr, el_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_vnd_get(net_idx, addr, el_address, model_id, cid):
    logging.debug("%s", mesh_cfg_model_sub_vnd_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, model_id, cid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_vnd_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_va_add(net_idx, addr, el_address, model_id, uuid):
    logging.debug("%s", mesh_cfg_model_sub_va_add.__name__)

    stack = get_stack()
    iutctl = get_iut()

    uuid = binascii.unhexlify(uuid)

    data = bytearray(struct.pack("<HHHH16s", net_idx, addr, el_address, model_id, uuid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_va_add'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_va_del(net_idx, addr, el_address, model_id, uuid):
    logging.debug("%s", mesh_cfg_model_sub_va_del.__name__)

    stack = get_stack()
    iutctl = get_iut()

    uuid = binascii.unhexlify(uuid)

    data = bytearray(struct.pack("<HHHH16s", net_idx, addr, el_address, model_id, uuid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_va_del'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_sub_va_ovw(net_idx, addr, el_address, model_id, uuid):
    logging.debug("%s", mesh_cfg_model_sub_va_ovw.__name__)

    stack = get_stack()
    iutctl = get_iut()

    uuid = binascii.unhexlify(uuid)

    data = bytearray(struct.pack("<HHHH16s", net_idx, addr, el_address, model_id, uuid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_sub_va_ovw'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_netkey_add(net_idx, addr, net_key, net_key_idx):
    logging.debug("%s", mesh_cfg_netkey_add.__name__)

    stack = get_stack()
    iutctl = get_iut()

    net_key = binascii.unhexlify(net_key)

    data = bytearray(struct.pack("<HH16sH", net_idx, addr, net_key, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_netkey_add'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_netkey_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_netkey_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_netkey_get'], data)

    (key,) = struct.unpack_from('<B', rsp)
    stack.mesh.model_data = key


def mesh_cfg_netkey_update(net_idx, addr, net_key, net_key_idx):
    logging.debug("%s", mesh_cfg_netkey_update.__name__)

    stack = get_stack()
    iutctl = get_iut()

    net_key = binascii.unhexlify(net_key)

    data = bytearray(struct.pack("<HH16sH", net_idx, addr, net_key, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_netkey_update'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_netkey_del(net_idx, addr, net_key_idx):
    logging.debug("%s", mesh_cfg_netkey_del.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", net_idx, addr, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_netkey_del'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_appkey_add(net_idx, addr, net_key_idx, app_key, app_key_idx):
    logging.debug("%s", mesh_cfg_appkey_add.__name__)

    stack = get_stack()
    iutctl = get_iut()

    app_key = binascii.unhexlify(app_key)

    data = bytearray(struct.pack("<HHH16sH", net_idx, addr, net_key_idx, app_key, app_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_appkey_add'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_appkey_update(net_idx, addr, net_key_idx, app_key, app_key_idx):
    logging.debug("%s", mesh_cfg_appkey_update.__name__)

    stack = get_stack()
    iutctl = get_iut()

    app_key = binascii.unhexlify(app_key)

    data = bytearray(struct.pack("<HHH16sH", net_idx, addr, net_key_idx, app_key, app_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_appkey_update'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_appkey_del(net_idx, addr, net_key_idx, app_key_idx):
    logging.debug("%s", mesh_cfg_appkey_del.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHH", net_idx, addr, net_key_idx, app_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_appkey_del'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_appkey_get(net_idx, addr, net_key_idx):
    logging.debug("%s", mesh_cfg_appkey_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", net_idx, addr, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_appkey_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_app_bind(net_idx, addr, el_address, app_key_idx, model_id):
    logging.debug("%s", mesh_cfg_model_app_bind.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, app_key_idx, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_app_bind'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_config_model_app_bind_vnd(net_idx, addr, el_address, app_key_idx, model_id, cid):
    logging.debug("%s", mesh_config_model_app_bind_vnd.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHHH", net_idx, addr, el_address, app_key_idx, model_id, cid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_app_bind_vnd'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_app_unbind(net_idx, addr, el_address, app_key_idx, model_id):
    logging.debug("%s", mesh_cfg_model_app_unbind.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, app_key_idx, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_app_unbind'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_app_get(net_idx, addr, el_address, model_id):
    logging.debug("%s", mesh_cfg_model_app_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHH",net_idx, addr, el_address, model_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_app_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_model_app_vnd_get(net_idx, addr, el_address, model_id, cid):
    logging.debug("%s", mesh_cfg_model_app_vnd_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHH", net_idx, addr, el_address, model_id, cid))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_model_app_vnd_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_heartbeat_pub_set(net_idx, addr, net_key_idx, destination, count_log, period_log, ttl, features):
    logging.debug("%s", mesh_cfg_heartbeat_pub_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(
        struct.pack("<HHHHBBBH", net_idx, addr, net_key_idx, destination, count_log, period_log, ttl, features))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_heartbeat_pub_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_heartbeat_pub_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_heartbeat_pub_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_heartbeat_pub_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_heartbeat_sub_set(net_idx, addr, source, destination, period_log):
    logging.debug("%s", mesh_cfg_heartbeat_sub_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHHB", net_idx, addr, source, destination, period_log))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_heartbeat_sub_set'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_heartbeat_sub_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_heartbeat_sub_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_heartbeat_sub_get'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_net_transmit_get(net_idx, addr):
    logging.debug("%s", mesh_cfg_net_transmit_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_net_transmit_get'], data)

    (transmit,) = struct.unpack_from('<B', rsp)
    stack.mesh.model_data = transmit


def mesh_cfg_net_transmit_set(net_idx, addr, transmit):
    logging.debug("%s", mesh_cfg_net_transmit_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHB", net_idx, addr, transmit))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_net_transmit_set'], data)

    (transmit,) = struct.unpack_from('<B', rsp)
    stack.mesh.model_data = transmit


def mesh_cfg_node_idt_set(net_idx, addr, net_key_idx, identity):
    logging.debug("%s", mesh_cfg_node_idt_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHB", net_idx, addr, net_key_idx, identity))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_node_idt_set'], data)

    (status, identity) = struct.unpack_from('<BB', rsp)
    stack.mesh.status = status
    stack.mesh.model_data = identity
    logging.debug("%d  %d", status, identity)


def mesh_cfg_node_idt_get(net_idx, addr, net_key_idx):
    logging.debug("%s", mesh_cfg_node_idt_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", net_idx, addr, net_key_idx))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_node_idt_get'], data)

    (status, identity) = struct.unpack_from('<BB', rsp)
    stack.mesh.status = status
    stack.mesh.model_data = identity


def mesh_cfg_node_reset(net_idx, addr):
    logging.debug("%s", mesh_cfg_node_reset.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", net_idx, addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_node_reset'], data)

    (status,) = struct.unpack_from('<B', rsp)
    stack.mesh.status = status


def mesh_cfg_lpn_polltimeout_get(net_idx, addr, unicast_addr):
    logging.debug("%s", mesh_cfg_lpn_polltimeout_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", net_idx, addr, unicast_addr))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['cfg_lpn_polltimeout_get'], data)

    (timeout,) = struct.unpack_from('<3s', rsp)
    timeout = int(binascii.hexlify(timeout))
    stack.mesh.model_data = timeout


def mesh_health_fault_get(addr, app_idx, cid):
    logging.debug("%s", mesh_health_fault_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHH", addr, app_idx, cid))

    iutctl.btp_socket.send_wait_rsp(*MESH['health_fault_get'], data)


def mesh_health_fault_clear(addr, app_idx, cid, ack):
    logging.debug("%s", mesh_health_fault_clear.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHB", addr, app_idx, cid, ack))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_fault_clear'], data)

    if ack:
        (test_id,) = struct.unpack_from('<B', rsp)
        stack.mesh.model_data = test_id

def mesh_health_fault_test(addr, app_idx, cid, test_id, ack):
    logging.debug("%s", mesh_health_fault_test.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHHBB", addr, app_idx, cid, test_id, ack))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_fault_test'], data)

    if ack:
        (test_id, cid) = struct.unpack_from('<BH', rsp)
        stack.mesh.model_data = [test_id, cid]


def mesh_health_period_get(addr, app_idx):
    logging.debug("%s", mesh_health_period_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", addr, app_idx))

    iutctl.btp_socket.send_wait_rsp(*MESH['health_period_get'], data)


def mesh_health_period_set(addr, app_idx, divisor, ack):
    logging.debug("%s", mesh_health_period_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHBB", addr, app_idx, divisor, ack))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_period_set'], data)

    if ack:
        (status,) = struct.unpack_from('<B', rsp)
        stack.mesh.model_data = status


def mesh_health_attention_get(addr, app_idx):
    logging.debug("%s", mesh_health_attention_get.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HH", addr, app_idx))

    iutctl.btp_socket.send_wait_rsp(*MESH['health_attention_get'], data)


def mesh_health_attention_set(addr, app_idx, attention, ack):
    logging.debug("%s", mesh_health_attention_set.__name__)

    stack = get_stack()
    iutctl = get_iut()

    data = bytearray(struct.pack("<HHBB", addr, app_idx, attention, ack))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MESH['health_attention_set'], data)

    if ack:
        (status,) = struct.unpack_from('<B', rsp)
        stack.mesh.model_data = status


def mesh_lpn_polled_ev(mesh, data, data_len):
    logging.debug("%s", mesh_lpn_polled_ev.__name__)

    hdr_fmt = '<HHB'

    (net_idx, frnd_addr, retry) = struct.unpack_from(hdr_fmt, data, 0)


def mesh_prov_node_added_ev(mesh, data, data_len):
    logging.debug("%s", mesh_prov_node_added_ev.__name__)

    stack = get_stack()
    hdr_fmt = '<HH16sB'
    (net_idx, addr, uuid, num_elems) = struct.unpack_from(hdr_fmt, data, 0)
    uuid = binascii.hexlify(uuid)

    logging.debug("0x%04x 0x%04x %r %u", net_idx, addr, uuid, num_elems)
    stack.mesh.node_added(net_idx, addr, uuid, num_elems)


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
