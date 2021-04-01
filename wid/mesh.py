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
import re
import sys
import time

from pybtp import btp
from pybtp.types import Perm, MeshVals
from ptsprojects.stack import get_stack

# Mesh ATS ver. 1.0

log = logging.debug


def hdl_pending_mesh_wids(wid, test_case_name, description):
    log("%s, %r, %r, %s", hdl_pending_mesh_wids.__name__, wid, description,
        test_case_name)
    stack = get_stack()
    module = sys.modules[__name__]

    actions = stack.synch.perform_synch(wid, test_case_name, description)
    if not actions:
        return "WAIT"

    for action in actions:
        handler = getattr(module, "hdl_wid_%d" % action.wid)
        result = handler(action.description)
        stack.synch.prepare_pending_response(action.test_case,
                                             result, action.delay)

    return None


def mesh_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", mesh_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)

        stack = get_stack()
        if not stack.synch or not stack.synch.is_required_synch(test_case_name, wid):
            return handler(description)

        response = hdl_pending_mesh_wids(wid, test_case_name, description)

        if response == "WAIT":
            return response

        stack.synch.set_pending_responses_if_any()
        return "WAIT"

    except AttributeError as e:
        logging.exception(e)


# wid handlers section begin
def hdl_wid_6(desc):
    """
    Implements: SEND_ADV_BEACON
    :param desc: Advertising Mesh Beacon Packet. Wait for other side to be
                 ready and click OK to broadcast Mesh beacon packet, otherwise
                 click Cancel.
    :return:
    """
    stack = get_stack()
    attention_duration = 0x00

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()

        if stack.mesh.iut_is_provisioner:
            btp.mesh_prov_node()

    if stack.mesh.iut_is_provisioner:
        if not stack.mesh.is_prov_adv:
            btp.mesh_provision_adv(stack.mesh.dev_uuid, stack.mesh.addr, attention_duration)
        else:
            stack.mesh.wait_for_prov_link_close(90)
            stack.mesh.address_lt2 = stack.mesh.addr + 1
            btp.mesh_provision_adv(stack.mesh.dev_uuid, stack.mesh.address_lt2, attention_duration)

    return True


def hdl_wid_7(desc):
    """
    Implements: ENTER_NUMBER
    :param desc: Please enter the number:
    :return:
    """
    stack = get_stack()

    ret = stack.mesh.oob_data.data

    # cleanup
    stack.mesh.oob_data.data = None
    stack.mesh.oob_action.data = None
    return ret


def hdl_wid_8(desc):
    """
    Implements: ENTER_STRING
    :param desc: Please enter string:
    :return:
    """
    stack = get_stack()

    ret = stack.mesh.oob_data.data.decode('UTF-8')

    # cleanup
    stack.mesh.oob_data.data = None
    stack.mesh.oob_action.data = None
    return ret


def hdl_wid_12(desc):
    """
    Implements: RE_PROVISIONING_NODE
    :param desc: There is no shared security information. Please start
                 provisioning from a remote or an additional provisioner side.
                 Remove the remote side's security information if any.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()

        if stack.mesh.iut_is_provisioner:
            btp.mesh_prov_node()

    return True


def hdl_wid_13(desc):
    """
    Implements: RE_PROVISIONING_PROVISIONER
    :param desc: There is no shared security information. Please remove any
                 security information if any. PTS is waiting for beacon to
                 start provisioning from IUT with UUID value indicated in 'TSPX_device_uuid'
    :return:
    """
    stack = get_stack()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()

    return True


def hdl_wid_15(desc):
    return True


def hdl_wid_17(desc):
    """
    Implements: RECEIVED_NETWORK_DATA
    :param desc: PTS will send a packet to the IUT. Please click OK when ready
                 to receive a packet.
    :return:
    """
    btp.mesh_store_net_data()
    return True


def hdl_wid_18(desc):
    """
    Implements: CONFIRM_NETWORK_DATA
    :param desc: Please confirm the following network packet was received: %s
    :return:
    """
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = False

    if stack.mesh.net_recv_ev_data.data is None:
        logging.error("Network Packet not received!")
        return False

    # This pattern is matching Time to Live (TTL) value, Control (CTL),
    # Source (SRC) Destination (DST) and Payload of the network packet
    # to be received
    pattern = re.compile(r'(TTL|CTL|SRC|DST|TransportPDU):'
                         r'\s+\[([0][xX][0-9a-fA-F]+)]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_18.__name__)
        return False

    params = dict(params)
    pdu = hex(int(params['TransportPDU'], 16))
    ttl = int(params.get('TTL'), 16)
    ctl = int(params.get('CTL'), 16)
    src = int(params.get('SRC'), 16)
    dst = int(params.get('DST'), 16)

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data
    recv_pdu = hex(int(recv_pdu, 16))

    if pdu == recv_pdu and ttl == recv_ttl and ctl == recv_ctl \
            and src == recv_src and dst == recv_dst:
        return True
    return False


def hdl_wid_19(desc):
    """
    Implements: SEND_NETWORK_DATA
    :param desc: Please send a network packet with maximum TransportPDU size
                 with the following network header: %s
    :return:
    """

    # This pattern is matching Time to Live (TTL) value, Source (SRC) and
    # Destination (DST) of the network packet to be sent
    pattern = re.compile(r'(TTL|SRC|DST):\s+\[([0][xX][0-9a-fA-F]+)]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_19.__name__)
        return False

    params = dict(params)

    btp.mesh_net_send(params.get('TTL', None), params.get('SRC'),
                      params.get('DST'), '01020304')
    return True


def hdl_wid_20(desc):
    """
    Implements: ENTER_GROUP_ADDRESS
    :param desc: Please enter a valid group address the IUT knows
    :return:
    """
    return 'C000'


def hdl_wid_21(desc):
    """
    Implements: ENTER_VIRTUAL_ADDRESS
    :param desc: Please enter a valid virtual address the IUT knows
    :return:
    """
    return '8000'


def hdl_wid_22(desc):
    """
    Implements:
    :param desc: Please bind an AppKey to a Model Id = %d for the testing.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    pattern = re.compile(
        r'(Model\sId)\s=\s+([0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_22.__name__)
        return

    params = dict(params)

    model_id = int(params.get('Model Id'), 16)
    app_key_idx = 0x0000

    if stack.mesh.address_lt2:
        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.address_lt2, stack.mesh.el_address, app_key_idx,
                                    model_id)
    else:
        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, app_key_idx,
                                model_id)

        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.address, stack.mesh.el_address, app_key_idx,
                                model_id)

    return True


def hdl_wid_23(desc):
    """
    Implements: SEND_SEGMENTED_DATA
    :param desc: Please send a segmented message encrypted with an application
                 key with source address 0x%04X and destination address 0x%04X
    :return:
    """

    # This pattern is matching source and destination addresses
    pattern = re.compile(
        r'(source\saddress|destination\saddress)\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_23.__name__)
        return False

    params = dict(params)

    btp.mesh_model_send(int(params.get('source address'), 16),
                        int(params.get('destination address'), 16),
                        'ff' * 16)
    return True


def hdl_wid_24(desc):
    """
    Implements: CONFIRM_CLOSE_LINK
    :param desc: Please confirm Link Close was received
    :return:
    """
    stack = get_stack()

    if stack.mesh.last_seen_prov_link_state.data is None:
        logging.error("The link state is None")
        return False

    (state, bearer) = stack.mesh.last_seen_prov_link_state.data

    if state == 'closed':
        return True
    return False


def hdl_wid_26(desc):
    """
    Implements: CONFIRM_RFU_BEARER_OPCODE
    :param desc: Please confirm invalid bearer opcode
    :return:
    """
    stack = get_stack()

    rsp = bool(stack.mesh.prov_invalid_bearer_rcv.data)
    # Cleanup
    stack.mesh.prov_invalid_bearer_rcv.data = False
    return rsp


def hdl_wid_30(desc):
    """
    Implements: CONFIRM_NOT_NETWORK_DATA
    :param desc: Please confirm the IUT has ignored the following network
                 packet = %s
    :return:
    """
    stack = get_stack()

    stack.mesh.net_recv_ev_store.data = False

    if stack.mesh.net_recv_ev_data.data is None:
        return True

    # This pattern is matching Time to Live (TTL) value, Control (CTL),
    # Source (SRC) Destination (DST) and Payload of the network packet
    # to be received
    pattern = re.compile(r'(TTL|CTL|SRC|DST|TransportPDU)\\:'
                         r'\s+\[([0][xX][0-9a-fA-F]+)\\]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_30.__name__)
        return False

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

    if pdu == recv_pdu and ttl == recv_ttl and ctl == recv_ctl \
            and src == recv_src and dst == recv_dst:
        logging.error("%s Network Packet received!", hdl_wid_30.__name__)
        return False
    return True


def hdl_wid_31(desc):
    """
    Implements: CONFIRM_TIMER_EXPIRED
    :param desc: Please confirm that IUT's incomplete timer is expired.
                 Click OK to proceed. Otherwise click Cancel.
    :return:
    """
    stack = get_stack()

    if stack.mesh.wait_for_incomp_timer_exp(90):
        return True
    return False


def hdl_wid_33(desc):
    """
    Implements:
    :param desc: 'Please start create link and provisioning.
                  PTS will broadcast unprovisioned device beacon with UUID = TSPX_device_uuid value"
    :return:
    """
    stack = get_stack()
    uuid = stack.mesh.dev_uuid
    addr = 0x0002
    attention_duration = 0x00

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()

        if stack.mesh.iut_is_provisioner:
            btp.mesh_prov_node()

    btp.mesh_provision_adv(uuid, addr, attention_duration)
    return True


def hdl_wid_34(desc):
    """
    Implements:
    :param desc: 'Please confirm IUT did not receive link ack so it will fail. Click Yes if it is not received. Otherwise click No.'
    :return:
    """
    return True


def hdl_wid_35(desc):
    """
    Implements: CONFIRM_TRANSPORT_DATA
    :param desc: Please confirm the following transport packet was received: %s
    :return:
    """
    stack = get_stack()

    # FIXME: stack.mesh.net_recv_ev_store.data = False

    if stack.mesh.net_recv_ev_data.data is None:
        return False

    # This pattern is matching Time to Live (TTL) value, Control (CTL),
    # Source (SRC) and Destination (DST)
    pattern = re.compile(r'(TTL|CTL|SRC|DST):\s+\[([0][xX][0-9a-fA-F]+)]')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_35.__name__)
        return False

    params = dict(params)

    # Normalize parameters for comparison
    ttl = int(params.get('TTL'), 16)
    ctl = int(params.get('CTL'), 16)
    src = int(params.get('SRC'), 16)
    dst = int(params.get('DST'), 16)

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data

    if ttl == recv_ttl and ctl == recv_ctl and src == recv_src \
            and dst == recv_dst:
        return True
    return False


def hdl_wid_36(desc):
    """
    Implements: SEND_UNSEGMENTED_DATA
    :param desc: Please send the unsegmented packet encrypted with application
                 key with source address 0x%04X and destination address 0x%04X
    :return:
    """

    # This pattern is matching source and destination addresses
    pattern = re.compile(
        r'(source\saddress|destination\saddress)\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_36.__name__)
        return False

    params = dict(params)

    btp.mesh_model_send(int(params.get('source address'), 16),
                        int(params.get('destination address'), 16),
                        'ff' * 2)
    return True


def hdl_wid_37(desc):
    """
    Implements: IUT_CONFIRM_ATTENTION_TIMER_STATE
    :param desc: Please confirm IUT Attention Timer state of its primary
                 Element is 0x00.
    :return:
    """
    stack = get_stack()

    return stack.mesh.wait_for_prov_link_close(90)


def hdl_wid_38(desc):
    """
    Implements: ENTER_REPLAY_PROTECTION_SIZE
    :param desc: Please clear replay protection list. Please enter size of
                 replay protection in decimal format.
    :return:
    """
    stack = get_stack()
    btp.mesh_rpl_clear()

    return str(stack.mesh.crpl_size)


def hdl_wid_39(desc):
    """
    Implements: CONFIRM_TRANSPORT_SEGMENTDATA
    :param desc: Please confirm you can decrypt the transport packet with
                 destination address : 0x%04X
    :return:
    """
    stack = get_stack()

    # This pattern is destination addresses
    pattern = re.compile(r'(address)\s+:\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_39.__name__)
        return False

    params = dict(params)

    if not stack.mesh.net_recv_ev_data.data:
        logging.error("No data received")
        return False

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data

    if int(params.get('address'), 16) != recv_dst:
        logging.error("Destination address does not match")
        return False
    return True


def hdl_wid_40(desc):
    """
    Implements: ASK_MODEL_SUPPORT
    :param desc: Please click Yes if Configuration model and Health model are
                 supported.
    :return:
    """
    return True


def hdl_wid_43(desc):
    """
    Implements: SEND_DATA_INVALID_KEY
    :param desc: PTS will send a message with invalid key. No response is
                 expected.
    :return:
    """
    return True


def hdl_wid_44(desc):
    """
    Implements: SEND_SEGMENTED_DATA_VIRTUAL
    :param desc: Please send a segmented message encrypted with an application
                 key with source address 0x%04X and destination label %s
                 (address 0x%04X)
    :return:
    """

    # This pattern is matching source and destination label addresses
    pattern = re.compile(
        r'(source\saddress|\(address)\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_44.__name__)
        return False

    params = dict(params)

    btp.mesh_model_send(int(params.get('source address'), 16),
                        int(params.get('(address'), 16),
                        'ff' * 16)
    return True


def hdl_wid_45(desc):
    """
    Implements: IUT_CLEAR_REPLAY_PROTECTION_CACHE
    :param desc: Please clear replay protection list cache.
    :return:
    """
    btp.mesh_rpl_clear()
    return True


def hdl_wid_46(desc):
    """
    Implements: IUT_SEND_UNPROVISONED_BEACONS
    :param desc: Please order IUT to send unprovisioned device beacons with
                 UUID set to TSPX_device_uuid.
    :return:
    """
    stack = get_stack()

    if stack.mesh.is_provisioned.data:
        btp.mesh_reset()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()
    return True


def hdl_wid_51(desc):
    """
    :param desc: Please confirm you can decode the control transport packet with
                 destination address : 0x%04X
    :return:
    """
    stack = get_stack()

    # This pattern is destination addresses
    pattern = re.compile(r'(address)\s+:\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_39.__name__)
        return False

    params = dict(params)

    if not stack.mesh.net_recv_ev_data.data:
        logging.error("No data received")
        return False

    (recv_ttl, recv_ctl, recv_src, recv_dst, recv_pdu) = \
        stack.mesh.net_recv_ev_data.data

    if int(params.get('address'), 16) != recv_dst:
        logging.error("Destination address does not match")
        return False
    return True


def hdl_wid_81(desc):
    """
    Implements: IUT_ADVERTISE_UNPROVISIONED_STATE
    :param desc: Please order IUT to advertise Connectable Advertising PDU for
                 Mesh Provisioning Service.
    :return:
    """
    stack = get_stack()
    if stack.mesh.is_provisioned.data:
        btp.mesh_reset()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()
    return True


def hdl_wid_85(desc):
    return True


def hdl_wid_90(desc):
    """
    Implements: IUT_SEND_SECURE_NETWORK_BEACON
    :param desc: Please order IUT to send secure network beacon to the PTS.
                 PTS will wait for
    :return:
    """
    stack = get_stack()

    return bool(stack.mesh.is_provisioned.data)


def hdl_wid_94(desc):
    """
    Implements: IUT_SEND_SECURE_NETWORK_BEACON_WITH_FLAGS
    :param desc: Please order IUT to send a secure network beacon with Key
                 Refresh Flag set to %d and IV Update Flag set to %d
    :return:
    """
    return True


def hdl_wid_103(desc):
    """
    Implements: CONFIRM_INVALID_DATA
    :param desc: Please confirm the invalid data is not written to handle = %s.
    :return:
    """
    # Mesh Provisioning data in
    attr = btp.gatts_get_attrs(type_uuid='2adb')
    if not attr:
        return False

    (handle, permission, type_uuid) = attr.pop()
    if not permission & Perm.write:
        return False

    # Mesh Provisioning data out
    attr = btp.gatts_get_attrs(type_uuid='2adc')
    if not attr:
        return False

    (handle, permission, type_uuid) = attr.pop()
    if permission & Perm.write:
        return False
    return True


def hdl_wid_104(desc):
    stack = get_stack()

    ret = stack.gap.wait_for_connection(30)
    if ret:
        time.sleep(5)

    return ret


def hdl_wid_201(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON
    :param desc: Order IUT to generate a non-connectable Secure Network beacon
                 (Mesh Beacon with Beacon type = 0x01).
    :return:
    """
    stack = get_stack()

    return bool(stack.mesh.is_provisioned.data)


def hdl_wid_202(desc):
    """
    Implements: IUT_GENERATE_UPDATE_IN_PROGRESS_SECURE_NETWORK_BEACON
    :param desc: Order IUT to enter the 'IV Update in Progress' state and set
                 the 'IV Update in progress' flag in the secure network beacon.
                 Click OK when ready.
    :return:
    """

    btp.mesh_iv_update_test_mode(True)
    btp.mesh_iv_update_toggle()
    return True


def hdl_wid_203(desc):
    """
    Implements: IUT_ACCEPT_AND_SEND_IV_INDEX42_SECURE_NETWORK_BEACON
    :param desc: Order IUT to power up and accept secure network beacon with IV
                 index = n+42 and the IV update flag set to 0, and to transmit
                 secure network beacons with the received IV values. Click OK
                 when IUT is ready.
    :return:
    """
    stack = get_stack()

    return bool(stack.mesh.is_provisioned.data)


def hdl_wid_204(desc):
    """
    Implements: IUT_ACCEPT_MESH_MESSAGE_IN_PROGRESS_STATE
    :param desc: Click OK when IUT is ready to accept Mesh messages with old IV
                 Index (m - 1) and new IV index (m).
    :return:
    """
    return True


def hdl_wid_205(desc):
    """
    Implements: IUT_SEND_SEGMENTATION_MESH_MESSAGE_IN_PROGRESS_STATE
    :param desc: Order IUT to prepare large size of composition data that can
                 be sent as fragmented packets to the PTS. During IV Update in
                 Progress state PTS will hold acknowledgment response and
                 beacon IV update in progress flag on. Click OK when it is
                 ready.
    :return:
    """
    return True


def hdl_wid_210(desc):
    """
    Implements: IUT_REMOVE_SECURITY_INFO
    :param desc: Order IUT to remove all shared security information since this
                 test case is run on different network other than primary
                 network. PTS will start provisioning IUT to different subnet.
                 Click OK when ready.
    :return:
    """
    stack = get_stack()

    if stack.mesh.is_provisioned.data is False:
        btp.mesh_config_prov()
        btp.mesh_init()
        return True
    return False


def hdl_wid_212(desc):
    """
    Implements:
    :param desc: This is Lower Tester 2 which is in the reject list filter and
                 should not receive any update. Click OK to continue monitoring
                 for any beacon until timeout.
    :return:
    """
    return True


def hdl_wid_216(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_LESS96
    :param desc: Please make sure IUT has performed an IV Update procedure less
                 than 96 hours ago. PTS will verify IUT does not perform
                 another update. Order IUT to generate non-connectable Secure
                 Network beacons (Mesh Beacon with Beacon type = 0x01).
    :return:
    """

    btp.mesh_iv_update_test_mode(False)

    return True


def hdl_wid_217(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_MORE96_INDEX_42
    :param desc: Please make sure IUT has been in Normal Operation state for
                 more than 96 hours. PTS will verify IUT can ignore Secure
                 Network beacons with an IV Index greater than last known IV
                 Index plus 42. Order IUT to generate Secure Network beacons.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.is_iv_test_mode_enabled.data:
        btp.mesh_iv_update_test_mode(True)
    return True


def hdl_wid_218(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_WRONG_INDEX
    :param desc: Please make sure IUT has been in Normal Operation state for
                 more than 96 hours. PTS will verify IUT can ignore Secure
                 Network beacons with an abnormal IV Index value. Order IUT to
                 generate Secure Network beacons.
    :return:
    """
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)
    return True


def hdl_wid_219(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_WRONG_SUBNET
    :param desc: PTS will verify IUT, on a primary subnet, can ignore Secure
                 Network beacons from other subnets. Order IUT to generate
                 Secure Network beacons.
    :return:
    """
    stack = get_stack()

    if stack.mesh.is_provisioned.data:
        return True
    return False


def hdl_wid_220(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_INVALID_INDEX
    :param desc: PTS will verify IUT can ignore Secure Network beacons with IV
                 Index values that cannot be accepted. Order IUT to generate
                 Secure Network beacons.
    :return:
    """
    return True


def hdl_wid_221(desc):
    """
    Implements: IUT_READY_FOR_UPDATE_IN_PROGRESS_SECURE_NETWORK_BEACON
    :param desc: The Lower Tester will advertise a new Secure Network beacon
                 with the IV Update Flag set to 1, IV Index incremented by 1
                 (new IV Index m = n + 1). Click OK when IUT is ready
    :return:
    """
    stack = get_stack()

    if not stack.mesh.is_iv_test_mode_enabled.data:
        btp.mesh_iv_update_test_mode(True)
    return True


def hdl_wid_222(desc):
    """
    Implements: IUT_GENERATE_NORMAL_STATE_NETWORK_BEACON
    :param desc: Order IUT to send a Secure Network beacon from the IUT showing
                 it is in Normal Operation state with the IV Update flag set to
                 0 and the IV Index set to the new IV Index (m). Click OK when
                 ready
    :return:
    """

    btp.mesh_iv_update_toggle()

    return True


def hdl_wid_223(desc):
    """
    Implements: IUT_DEACTIVIATE_IV_UPDATE_TEST_MODE
    :param desc: Please order IUT to deactivate IV update test mode in oder to
                 set it to a state where it cannot accept a new IV Update
                 procedure for at least 96 hours
    :return:
    """

    btp.mesh_iv_update_test_mode(False)
    return True


def hdl_wid_255(desc):
    """
    Implements:
    :param desc: Press OK to send a Secure Network Beacon with the Key Refresh
                 Flag (Flags bit 0) set to 0, the IV Update Flag (Flags bit 1)
                 set to 0, the Network ID set to the current Network ID, the
                 IV Index set to the current IV Index, and the Authentication
                 Value calculated with the new NetKey
    :return:
    """
    return True


def hdl_wid_260(desc):
    """
    Implements:
    :param desc: Please start another PTS and run Lower Tester 2 test case which
                 is the node that has been rejected and set the correct TSPX_device_uuid
                 value for tester 2 which is different than the Lower Tester 1.
                 Please have the IUT provision both testers to share the same network
                 security credentials. Click OK when ready.
    :return:
    """
    return True


def hdl_wid_261(desc):
    """
    Implements:
    :param desc: This is Lower Tester 2 acting as a node that has been rejected.
                 Please set the correct TSPX_device_uuid value before running this
                 test case for IUT to start provisioning these two testers to share
                 the same network security credential. Click OK when ready.
    :return:
    """
    return True


def hdl_wid_262(desc):
    """
    Implements: KEY_REFRESH_READY_FOR_ROUND2
    :param desc: Press OK when tester and IUT is ready to go to the second
                 round of key refresh
    :return:
    """
    return True


def hdl_wid_267(desc):
    """
    Implements:
    :param desc: Please click OK after friendship is established between Low
                 Power Node (Lower Tester 1) and Friend Node (IUT).
    :return:
    """
    return True


def hdl_wid_268(desc):
    """
    Implements: KEY_REFRESH_READY
    :param desc: Press OK when IUT is ready for Key Refresh Procedure
    :return:
    """
    return True


def hdl_wid_269(desc):
    """
    Implements:
    :param desc: This is Lower Tester 2 which will not receive any update.
                 Please wait until IUT finishes the Key Refresh procedure with Lower Tester 1,
                 and then click OK for Lower Tester 2 to send a Mesh message.
    :return:
    """
    return True


def hdl_wid_270(desc):
    """
    Implements:
    :param desc: Please confirm that IUT ignores the sent Mesh message
    :return:
    """
    return True


def hdl_wid_271(desc):
    """
    Implements:
    :param desc: Please confirm that Lower Tester 2 did not receive any secure beacons
    :return:
    """
    stack = get_stack()
    return True


def hdl_wid_272(desc):
    """
    Implements:
    :param desc: Please send a Mesh message from Lower Tester 2 to IUT.
                 Confirm that IUT ignores the message from Lower Tester 2
    :return:
    """
    stack = get_stack()
    return True


def hdl_wid_273(desc):
    """
    Implements:
    :param desc: Please confirm that IUT received a Mesh message, NID: 0x37
    :return:
    """
    stack = get_stack()
    return True

def hdl_wid_274(desc):
    """
    Implements: KEY_REFRESH_WAIT_FOR_INVALID_MSG
    :param desc: Lower Tester will send an invalid Mesh message in 5 sec.
                 See Output Log for details
    :return:
    """
    return True


def hdl_wid_275(desc):
    """
    Implements:
    :param desc: Please send Config Key Refresh Phase Get.
    :return:
    """
    stack = get_stack()

    btp.mesh_cfg_krp_get(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index)

    return stack.mesh.status == 0x00 and stack.mesh.data == 0x00


def hdl_wid_276(desc):
    """
    Implements:
    :param desc: Please send NetKey Update.
    :return:
    """
    stack = get_stack()

    net_key_idx = 0x0000
    net_key = '00000000000000000000000000000001'

    btp.mesh_cfg_netkey_update(stack.mesh.net_idx, stack.mesh.addr, net_key, net_key_idx)
    btp.mesh_cfg_netkey_update(stack.mesh.net_idx, stack.mesh.address, net_key, net_key_idx)

    return stack.mesh.status == 0x00


def hdl_wid_277(desc):
    """
    Implements:
    :param desc: Please send AppKey Update.
    :return:
    """
    stack = get_stack()

    app_key_up = '00000000000000000000000000000001'
    app_key_idx = 0x0000

    btp.mesh_cfg_appkey_update(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key_up,
                               app_key_idx)
    btp.mesh_cfg_appkey_update(stack.mesh.net_idx, stack.mesh.address, stack.mesh.net_key_index, app_key_up,
                               app_key_idx)

    return stack.mesh.status == 0x00


def hdl_wid_278(desc):
    """
    Implements:
    :param desc: Waiting for Secure Network Beacon with Key Refresh On and Iv Update Off.
    :return:
    """
    stack = get_stack()
    phase = 0x02
    net_key_index = 0x0000
    net_idx = 0x0000

    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, phase)
    btp.mesh_cfg_krp_set(net_idx, stack.mesh.address, net_key_index, phase)

    return True


def hdl_wid_279(desc):
    """
    Implements:
    :param desc: Waiting for Secure Network Beacon with Key Refresh Off and Iv Update Off.
    :return:
    """
    stack = get_stack()
    phase = 0x03
    net_key_index = 0x0000
    net_idx = 0x0000

    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, phase)
    btp.mesh_cfg_krp_set(net_idx, stack.mesh.address, net_key_index, phase)

    return True


def hdl_wid_280(desc):
    """
    Implements:
    :param desc: Waiting 5 seconds to initiate phase 1 to Friend Node.
    :return:
    """
    return True


def hdl_wid_281(desc):
    """
    Implements:
    :param desc: Waiting 15 seconds to initiate phase 2.
    :return:
    """
    return True


def hdl_wid_282(desc):
    """
    Implements:
    :param desc: Please order Lower Tester 1 to initiate friend poll.
                 Waiting 15 seconds to initiate phase 3.
    :return:
    """
    return True


def hdl_wid_283(desc):
    """
    Implements:
    :param desc: Waiting LPN's response from NetKey Update Message.
                 Please order Lower Tester 1 to initiate friend poll.
    :return:
    """
    return True


def hdl_wid_284(desc):
    """
    Implements:
    :param desc: Waiting 5 seconds to initiate phase 1 to Low Power Node.
    :return:
    """
    return True


def hdl_wid_285(desc):
    """
    Implements: KEY_REFRESH_READY_SKIP_PAHSE_2
    :param desc: Press OK when IUT is ready for Key Refresh Procedure with
                 skipping phase 2
    :return:
    """
    return True


def hdl_wid_286(desc):
    """
    Implements:
    :param desc: Waiting for Config Key Refresh Phase Set message with Phase Set to 0x02.
    :return:
    """
    stack = get_stack()
    pattern = re.compile(
        r'(Phase)\sSet\sto\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_286.__name__)
        return
    params = dict(params)

    phase = int(params.get('Phase'), 16)
    net_key_index = 0x0000

    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.addr, net_key_index, phase)
    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.address, net_key_index, phase)

    return stack.mesh.status == 0x00


def hdl_wid_287(desc):
    """
    Implements:
    :param desc: Waiting for Config Key Refresh Phase Set message with Phase Set to 0x03.
    :return:
    """
    stack = get_stack()
    pattern = re.compile(
        r'(Phase)\sSet\sto\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_286.__name__)
        return
    params = dict(params)

    phase = int(params.get('Phase'), 16)
    net_key_index = 0x0000

    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.addr, net_key_index, phase)
    btp.mesh_cfg_krp_set(stack.mesh.net_idx, stack.mesh.address, net_key_index, phase)

    return stack.mesh.status == 0x00


def hdl_wid_302(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll to receive the messages
                 Lower Tester 2 sent.
    :return:
    """
    return True


def hdl_wid_303(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn(True)
    return True


def hdl_wid_306(desc):
    """
    Implements:
    :param desc: Waiting for Lower Tester 1 to establish Friendship with IUT
                 so Lower Tester 2 will know the Friend Cache size.
    :return:
    """
    return True


def hdl_wid_305(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll after Lower Tester 2
                 sends Secure Network Beacons with a different Key Refresh
                 flag.
    :return:
    """
    return True


def hdl_wid_308(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn_poll()
    return True


def hdl_wid_310(desc):
    """
    Implements:
    :param desc: Send Mesh message to Friend Node from Lower Tester 2.
                 Lower Tester 1 will not send the Friend Poll Message to the
                 IUT for twice the PollTimeout time. IUT should remove the
                 Lower Tester 1 as a Friend
    :return:
    """
    return True


def hdl_wid_311(desc):
    """
    Implements:
    :param desc: Press OK to send a Secure Network Beacon with the Key Refresh
                 Flag (Flags bit 0) set to 0, the IV Update Flag (Flags bit 1)
                 set to 1.
    :return:
    """
    return True


def hdl_wid_312(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn_poll()
    return True


def hdl_wid_313(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn_poll()
    return True


def hdl_wid_314(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn_poll()
    return True


def hdl_wid_315(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    btp.mesh_lpn(True)
    return True


def hdl_wid_317(desc):
    """
    Implements:
    :param desc: Please click OK to send a message with TTL field set to
                 value = 3.
    :return:
    """
    return True


def hdl_wid_318(desc):
    """
    Implements:
    :param desc: Please click OK to send partial segments of segmented
                 messages to IUT.
    :return:
    """
    return True


def hdl_wid_319(desc):
    """
    Implements:
    :param desc: Click OK to send Mesh messages to IUT(Friend Node).
    :return:
    """
    return True


def hdl_wid_324(desc):
    """
    Implements:
    :param desc: Lower Tester 2 is waiting for IUT to send Friend Clear
                 message.
    :return:
    """
    return True


def hdl_wid_326(desc):
    """
    Implements:
    :param desc:
    :return:
    """

    btp.mesh_lpn(False)
    return True


def hdl_wid_327(desc):
    """
    Implements:
    :param desc: Click OK button after friendship is established between
                 Lower Tester 1 and IUT
    :return:
    """
    return True


def hdl_wid_329(desc):
    """
    Implements:
    :param desc: Click OK to send Friend Timeout Get Message after Lower
                 Tester 1 and IUT established friendship.
    :return:
    """
    return True


def hdl_wid_330(desc):
    """
    Implements:
    :param desc: Click OK to send Friend Clear Message.
    :return:
    """
    return True


def hdl_wid_332(desc):
    """
    Implements:
    :param desc: Please send Heartbeat Publication Set message from Lower
                 Tester 2 to IUT, and then send Friend Poll from IUT to Lower Tester 1.
    :return:
    """
    return True


def hdl_wid_333(desc):
    """
    Implements:
    :param desc: Lower Tester 1 will now stop responding to Friend Poll from IUT.
                 Please click OK when friendship is terminated.
    :return:
    """
    stack = get_stack()
    assert stack.mesh.wait_for_lpn_terminated(timeout=60)

    return True


def hdl_wid_335(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll message after Lower
                 Tester 2 sends out Friend Clear message.
    :return:
    """
    return True


def hdl_wid_336(desc):
    """
    Implements:
    :param desc: If Lower Tester 1 and IUT are not previously provisioned,
                 please use a second instance of PTS to perform provisioning
                 first by executing MESH/NODE/FRND/TWO_NODES_PROVISIONER test
                 case.
    :return:
    """
    return True


def hdl_wid_337(desc):
    """
    Implements:
    :param desc: Please start Lower Tester 2 first before establishing
                 friendship between Lower Tester 1 and IUT.
    :return:
    """
    return True


def hdl_wid_339(desc):
    """
    Implements:
    :param desc: Friendship is established successfully.
    :return:
    """
    return True


def hdl_wid_340(desc):
    """
    Implements:
    :param desc: Lower Tester 1 is a Low Power Node, and IUT is Friend Node.
                 If Lower Tester 1 and IUT are not previously provisioned,
                 please use a second instance of PTS to perform provisioning
                 first by executing MESH/NODE/FRND/TWO_NODES_PROVISIONER test
                 case.
    :return:
    """
    return hdl_wid_336(desc)


def hdl_wid_341(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll message after Lower
                 Tester 2 sends Mesh message(s) and config friend set message.
    :return:
    """
    return True


def hdl_wid_342(desc):
    """
    Implements:
    :param desc: Please wait for IUT and Lower Tester 1 to establish
                 friendship. Click OK to send Mesh messages to IUT
                 (Friend Node).
    :return:
    """
    return True


def hdl_wid_344(desc):
    """
    Implements:
    :param desc: Please click OK to send Mesh packet(s) after Lower Tester 1
                 adds subscription address to IUT.
    :return:
    """
    return True


def hdl_wid_345(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll message after IUT receives
                 beacon from Lower Tester 1
    :return:
    """
    return True


def hdl_wid_346(desc):
    """
    Implements: IUT_SEND_FRIEND_SUBSCRIPTION_LIST_ADD
    :param desc: Please send Friend Subscription List Add message to Lower
                 Tester.
    :return:
    """
    stack = get_stack()
    group_address = MeshVals.subscription_addr_list1

    btp.mesh_lpn_subscribe(group_address)
    stack.mesh.lpn_subscriptions.append(group_address)
    return True


def hdl_wid_347(desc):
    """
    Implements: IUT_SEND_FRIEND_SUBSCRIPTION_LIST_REMOVE
    :param desc: Please send Friend Subscription List Remove message to Lower
                 Tester.
    :return:
    """
    stack = get_stack()
    group_address = MeshVals.subscription_addr_list1

    # Subscribe if not
    if group_address not in stack.mesh.lpn_subscriptions:
        btp.mesh_lpn_subscribe(group_address)
        stack.mesh.lpn_subscriptions.append(group_address)
        time.sleep(10)  # Give some time to subscribe

    btp.mesh_lpn_unsubscribe(group_address)
    stack.mesh.lpn_subscriptions.remove(group_address)
    return True


def hdl_wid_348(desc):
    """
    Implements:
    :param desc: Please click OK to send Friend Poll message after IUT caches
                 netkey update message.
    :return:
    """
    return True


def hdl_wid_353(desc):
    return True


def hdl_wid_354(desc):
    return True


def hdl_wid_355(desc):
    return True


def hdl_wid_356(desc):
    return True


def hdl_wid_357(desc):
    return True


def hdl_wid_358(desc):
    return True


def hdl_wid_361(desc):
    return True


def hdl_wid_362(desc):
    return True


def hdl_wid_364(desc):
    return True


def hdl_wid_366(desc):
    return True


def hdl_wid_367(desc):
    return True


def hdl_wid_368(desc):
    """
    Implements:
    :param desc: Please confirm that IUT received the mesh packet to LT1.
    :return:
    """
    return True


def hdl_wid_372(desc):
    """
    Implements:
    :param desc: Please confirm that IUT ignores Proxy Configuration message.
    :return:
    """
    return True


def hdl_wid_373(desc):
    """
    Implements:
    :param desc: Received Node Identity.Wait for 60 seconds.After that, IUT expect to stop advertising Node Identity
    :return:
    """
    return True


def hdl_wid_500(desc):
    """
    Implements:
    :param desc: Waiting for Composition Data Get Request.
    :return:
    """
    stack = get_stack()
    page = 0x00

    if not stack.mesh.iut_is_provisioner:
        return True

    if stack.mesh.address_lt2:
        btp.mesh_composition_data_get(stack.mesh.net_idx, stack.mesh.address_lt2, page)
    else:
        btp.mesh_composition_data_get(stack.mesh.net_idx, stack.mesh.addr, page)

    return True


def hdl_wid_501(desc):
    """
    Implements:
    :param desc: Send Config Beacon Get.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_beacon_get(stack.mesh.net_idx, stack.mesh.addr)

    return True


def hdl_wid_502(desc):
    """
    Implements:
    :param desc: Please send Config Beacon Set with 0.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    pattern = re.compile(r'with\s+([0-9a-fA-F]+)')
    val = pattern.findall(desc)
    if not val:
        logging.error("%s parsing error", hdl_wid_502.__name__)
        return False

    btp.mesh_cfg_beacon_set(stack.mesh.net_idx, stack.mesh.addr, int(val[0], 16))

    return stack.mesh.status == int(val[0], 16)


def hdl_wid_503(desc):
    """
    Implements:
    :param desc: Please send Config Beacon Set with 1.
    :return:
    """
    return hdl_wid_502(desc)


def hdl_wid_504(desc):
    """
    Implements:
    :param desc: Please send Config Default TTL Get.
    :return:mesh_model_send
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_default_ttl_get(stack.mesh.net_idx, stack.mesh.addr)

    return True


def hdl_wid_505(desc):
    """
    Implements:
    :param desc: Please send Config Default TTL Set.
    :return:mesh_model_send
    """
    stack = get_stack()
    val = 0x00

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_default_ttl_set(stack.mesh.net_idx, stack.mesh.addr, val)
    return True


def hdl_wid_506(desc):
    """
    Implements:
    :param desc: Please confirm the TTL value = 0x0.
    :return:mesh_model_send
    """
    stack = get_stack()

    return stack.mesh.status == 0x00


def hdl_wid_507(desc):
    """
    Implements:
    :param desc: Please send Config Friend Get.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_friend_get(stack.mesh.net_idx, stack.mesh.addr)
    return True


def hdl_wid_508(desc):
    """
    Implements:
    :param desc: Please send Config Friend Set.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    val = 0x00

    btp.mesh_cfg_friend_set(stack.mesh.net_idx, stack.mesh.addr, val)
    return stack.mesh.status == 0x00


def hdl_wid_509(desc):
    """
    Implements:
    :param desc: Please confirm the [...] value = 0x0.
    :return:
    """
    stack = get_stack()

    pattern = re.compile(r'value\s=\s+([0-9a-fA-F]+)')
    val = pattern.findall(desc)
    if not val:
        logging.error("%s parsing error", hdl_wid_509.__name__)
        return False

    return stack.mesh.status == int(val[0], 16)


def hdl_wid_510(desc):
    """
    Implements:
    :param desc: Heartbeat Publication Set
    :return:
    """

    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    pattern = re.compile(r'(Destination|CountLog|PeriodLog|TTL|Features)\sfield set to\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_510.__name__)
        return False
    params = dict(params)

    destination = int(params.get('Destination'), 16)
    count_log = int(params.get('CountLog'), 16)
    period_log = int(params.get('PeriodLog'), 16)
    ttl = int(params.get('TTL'), 16)
    features = int(params.get('Features'), 16)

    btp.mesh_cfg_heartbeat_pub_set(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, destination,
                                   count_log, period_log, ttl, features)

    return stack.mesh.status == 0x00


def hdl_wid_511(desc):
    """
    Implements:
    :param desc: Heartbeat Publication Get
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_heartbeat_pub_get(stack.mesh.net_idx, stack.mesh.addr)

    return stack.mesh.status == 0x00


def hdl_wid_514(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    if "Config GATT Proxy Get" in desc:
        btp.mesh_cfg_gatt_proxy_get(stack.mesh.net_idx, stack.mesh.addr)
        return True

    if "Config GATT Proxy Set" in desc:
        val = 0x00
        btp.mesh_cfg_gatt_proxy_set(stack.mesh.net_idx, stack.mesh.addr, val)
        return True

    if "Config Model Subscription" in desc:
        sub_address = 0x0002
        model_id = 0x0000

        if "Virtual Address Add" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, int(stack.mesh.dev_uuid, 16), model_id]

            btp.mesh_cfg_model_sub_va_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id,
                                          stack.mesh.dev_uuid)
            return stack.mesh.status == 0x00

        if "Virtual Address Delete" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, int(stack.mesh.dev_uuid, 16), model_id]

            btp.mesh_cfg_model_sub_va_del(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id,
                                          stack.mesh.dev_uuid)
            return stack.mesh.status == 0x00

        if "Virtual Address Overwrite" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, int(stack.mesh.dev_uuid, 16), model_id]

            btp.mesh_cfg_model_sub_va_ovw(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id,
                                          stack.mesh.dev_uuid)
            return stack.mesh.status == 0x00

        if "Add" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, sub_address, model_id]

            btp.mesh_cfg_model_sub_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, sub_address,
                                       model_id)
            return stack.mesh.status == 0x00

        if "Delete All" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, model_id]

            btp.mesh_cfg_model_sub_del_all(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id)
            return stack.mesh.status == 0x00

        if "Delete" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, sub_address, model_id]

            btp.mesh_cfg_model_sub_del(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, sub_address,
                                       model_id)
            return stack.mesh.status == 0x00

        if "Overwrite" in desc:
            stack.mesh.model_data = [stack.mesh.el_address, sub_address, model_id]

            btp.mesh_cfg_model_sub_ovw(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, sub_address,
                                       model_id)
            return stack.mesh.status == 0x00

    if "Config Vendor Model Subscription Get" in desc:
        model_id = 0x1234
        cid = 0x05F1
        el_address = 0x0001
        stack.mesh.model_data = [el_address, cid | model_id << 16]

        btp.mesh_cfg_model_sub_vnd_get(stack.mesh.net_idx, stack.mesh.addr, el_address, model_id, cid)
        return stack.mesh.status == 0x00

    if "Config SIG Model Subscription Get " in desc:
        model_id = 0x0001
        el_address = 0x0001
        stack.mesh.model_data = [el_address, model_id]

        btp.mesh_cfg_model_sub_get(stack.mesh.net_idx, stack.mesh.addr, el_address, model_id)
        return stack.mesh.status == 0x00

    if "AppKey Add" in desc:
        app_key = '0123456789abcdef0123456789fedcba'
        app_key_idx = 0x0001

        stack.mesh.model_data = [stack.mesh.net_key_index, app_key_idx, hex(int(app_key, 16))]
        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key, app_key_idx)
        return stack.mesh.status == 0x00

    if "AppKey Update" in desc:
        app_key = '0123456789abcdef0123456789fedcba'
        app_key_up = '0123456789abcdef0123456789fedcbc'
        app_key_idx = 0x0001

        stack.mesh.model_data = [stack.mesh.net_key_index, app_key_idx, int(app_key_up, 16)]
        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key, app_key_idx)
        btp.mesh_cfg_appkey_update(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key_up,
                                   app_key_idx)
        logging.debug("Status = 0x%2x", stack.mesh.status)
        return True  # status is not checked because PTS returned status != 0x00

    if "AppKey Delete" in desc:
        pattern = re.compile(r'(NetKey\sindex|AppKey\sindex)\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_514.__name__)
            return False
        params = dict(params)

        net_key_idx = int(params.get('NetKey index'), 16)
        app_key_idx = int(params.get('AppKey index'), 16)

        btp.mesh_cfg_appkey_del(stack.mesh.net_idx, stack.mesh.addr, net_key_idx, app_key_idx)

        logging.debug("Status = 0x%2x", stack.mesh.status)
        return True  # status is not checked because PTS returned status != 0x00

    if "AppKey Get" in desc:
        pattern = re.compile(r'(NetKey\sindex)\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_514.__name__)
            return False
        params = dict(params)

        net_key_idx = int(params.get('NetKey index'), 16)

        btp.mesh_cfg_appkey_get(stack.mesh.net_idx, stack.mesh.addr, net_key_idx)
        logging.debug("Status = 0x%2x", stack.mesh.status)
        return True  # status is not checked because PTS returned status != 0x00

    if "Model App Bind" in desc:
        app_key_idx = 0x0000
        model_id = 0x0002
        app_key = '0123456789abcdef0123456789fedcba'

        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key, app_key_idx)

        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, app_key_idx,
                                       model_id)

        stack.mesh.model_data = [stack.mesh.el_address, app_key_idx, model_id]

        return stack.mesh.status == 0x00

    if "Model App Unbind" in desc:
        app_key_idx = 0x0000
        model_id = 0x0002
        app_key = '0123456789abcdef0123456789fedcba'

        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key, app_key_idx)
        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, app_key_idx,
                                       model_id)
        stack.mesh.model_data = [stack.mesh.el_address, app_key_idx, model_id]

        btp.mesh_cfg_model_app_unbind(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, app_key_idx,
                                         model_id)

        return stack.mesh.status == 0x00

    if "SIG Model App Get" in desc:
        model_id = 0x0002
        stack.mesh.model_data = [stack.mesh.el_address, model_id]

        btp.mesh_cfg_model_app_get(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id)

        return stack.mesh.status == 0x00

    if "Vendor Model App Get" in desc:
        model_id = 0x1234
        cid = 0x05F1
        stack.mesh.model_data = [stack.mesh.el_address, model_id, cid]

        btp.mesh_cfg_model_app_vnd_get(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.el_address, model_id, cid)

        return True

    if "Network Transmit Get" in desc:
        btp.mesh_cfg_net_transmit_get(stack.mesh.net_idx, stack.mesh.addr)

        return True

    if "Network Transmit Set" in desc:
        transmit = 0x01

        btp.mesh_cfg_net_transmit_set(stack.mesh.net_idx, stack.mesh.addr, transmit)

        return True

    if "Node Identity Set" in desc:
        pattern = re.findall(r'\s+([0-9a-fA-F]+)', desc)
        identity = int(pattern[0], 16)

        btp.mesh_cfg_node_idt_set(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, identity)

        return stack.mesh.status == 0x00 and stack.mesh.model_data == identity

    if "Node Identity Get" in desc:
        identity = 0x01

        btp.mesh_cfg_node_idt_get(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index)

        return stack.mesh.status == 0x00 and stack.mesh.model_data == identity

    if "Low Power Node PollTimeout Get" in desc:
        pattern = re.compile(r'(address)\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_514.__name__)
            return False
        params = dict(params)

        unicast_addr = int(params.get('address'), 16)

        btp.mesh_cfg_lpn_polltimeout_get(stack.mesh.net_idx, stack.mesh.addr, unicast_addr)

        return True

    else:
        return False


def hdl_wid_515(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    if "Model App Bind" in desc or r"Model App Unbind" in desc:
        pattern = re.compile(r'(Element\sAddress|AppKey\sIndex|SIG\sModel\sID)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_515.__name__)
            return False
        params = dict(params)

        el_address = int(params.get('Element Address'), 16)
        mod_app_idx = int(params.get('AppKey Index'), 16)
        model_id = int(params.get('SIG Model ID'), 16)

        return stack.mesh.model_data == [el_address, mod_app_idx, model_id]

    if "SIG Model App Get" in desc:
        pattern = re.compile(r'(Element\sAddress|SIG\sModel\sID)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_515.__name__)
            return False
        params = dict(params)

        el_address = int(params.get('Element Address'))
        model_id = int(params.get('SIG Model ID'))

        return stack.mesh.model_data == [el_address, model_id]

    if "AppKey Add" in desc:
        pattern = re.compile(r'(NetKeyIndex|AppKeyIndex|AppKey)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_515.__name__)
            return False
        params = dict(params)

        net_key_idx = int(params.get('NetKeyIndex'), 16)
        app_key_idx = int(params.get('AppKeyIndex'), 16)
        app_key = hex(int(params.get('AppKey'), 16))

        return [net_key_idx, app_key_idx, app_key] == stack.mesh.model_data

    if "Vendor Model App Get" in desc:
        pattern = re.compile(r'(Element\sAddress|Vendor\sModel\sID)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_515.__name__)
            return False
        params = dict(params)

        el_addr = int(params.get('Element Address'))
        cid = int(params.get('Vendor Model ID')[4:], 16)
        model_id = int(params.get('Vendor Model ID')[:4], 16)

        return [el_addr, model_id, cid] == stack.mesh.model_data

    if "AppKey Update" in desc:
        pattern = re.compile(r'(NetKeyIndex|AppKeyIndex|AppKey)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_515.__name__)
            return False
        params = dict(params)

        net_key_index = int(params.get('NetKeyIndex'))
        app_key_idx = int(params.get('AppKeyIndex'), 16)
        app_key_up = int(params.get('AppKey'), 16)

        return [net_key_index, app_key_idx, app_key_up] == stack.mesh.model_data


def parse_params(desc):
    field_dict = {}
    txt = desc.splitlines()[1:]
    for line in txt:
        line = line.strip()
        fields = line.split(': ', 1)
        if len(fields) < 2:
            continue
        field_name = fields[0]
        m = re.search(r"\[([\-A-Fa-f0-9x\(\) ]+)\]", fields[1])
        if not m:
            field_dict[field_name] = None
            continue
        value = m.group(1)

        m = re.search(r"\(([A-Fa-f0-9x]+)\)", value)
        if not m:
            field_dict[field_name] = int(value, 16)
            continue

        hex_value = m.group(1)
        field_dict[field_name] = int(hex_value, 16)

    return field_dict


def confirm_cfg_model_subscription_add(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    sub_address = params['Address']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, sub_address, model_id]


def confirm_cfg_model_subscription_del(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    sub_address = params['Address']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, sub_address, model_id]


def confirm_cfg_model_subscription_overwrite(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    sub_address = params['Address']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, sub_address, model_id]


def confirm_cfg_model_subscription_del_all(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, model_id]


def confirm_cfg_model_subscription_get(params):
    model_id = params['SIG Model Identifier']
    el_address = params['ElementAddress']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, model_id]


def confirm_cfg_model_subscription_va_add(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    address_uuid = params['AddressUUID']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, address_uuid, model_id]


def confirm_cfg_model_subscription_va_del(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    address_uuid = params['AddressUUID']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, address_uuid, model_id]


def confirm_cfg_model_subscription_va_ovw(params):
    model_id = params['Model Identifier']
    el_address = params['ElementAddress']
    address_uuid = params['AddressUUID']

    stack = get_stack()

    return stack.mesh.model_data == [el_address, address_uuid, model_id]


def confirm_cfg_model_subscription_get_vnd(params):
    el_address = params['ElementAddress']
    vnd_model_id = int(params.get('Vendor Model Identifier'))

    stack = get_stack()

    return stack.mesh.model_data == [el_address, vnd_model_id]


def parse_send(params):
    opcode = params['Op Code']
    cmds = {
        0x801B: confirm_cfg_model_subscription_add,
        0x801C: confirm_cfg_model_subscription_del,
        0x801E: confirm_cfg_model_subscription_overwrite,
        0x801D: confirm_cfg_model_subscription_del_all,
        0x8029: confirm_cfg_model_subscription_get,
        0x8020: confirm_cfg_model_subscription_va_add,
        0x8021: confirm_cfg_model_subscription_va_del,
        0x8022: confirm_cfg_model_subscription_va_ovw,
        0x802B: confirm_cfg_model_subscription_get_vnd,
    }

    if opcode not in cmds:
        return False

    return cmds[opcode](params)


def hdl_wid_516(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    params = parse_params(desc)
    log("%r", params)

    return parse_send(params)


def hdl_wid_517(desc):
    """
    Implements:
    :param desc: Please confirm the received messages are correct.
    :return:
    """
    return True


def hdl_wid_518(desc):
    """
    Implements:
    :param desc: Please send AppKey Add.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    app_key = '0123456789abcdef0123456789fedcba'
    app_key_idx = 0x0000
    if stack.mesh.address_lt2:
        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.address_lt2, stack.mesh.net_key_index, app_key,
                                app_key_idx)
    else:
        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key, app_key_idx)
        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.address, stack.mesh.net_key_index, app_key, app_key_idx)
    return stack.mesh.status == 0x00


def hdl_wid_519(desc):
    """
    Implements: CONFIRM_DEVICE_RESET
    :param desc: Click OK to put the IUT back into an unprovisioned state.
    :return:
    """

    btp.mesh_reset()
    return True


def hdl_wid_520(desc):
    """
    Implements: NODE_IDENTITY_START_AD
    :param desc: Please configure the IUT to start advertising on all networks.
    :return:
    """

    btp.mesh_proxy_identity()
    return True


def hdl_wid_521(desc):
    """
    Implements: NODE_IDENTITY_STOP_AD
    :param desc: Please configure the IUT to stop advertising on all networks.
    :return:
    """

    time.sleep(60)
    return True


def hdl_wid_527(desc):
    """
    Implements:
    :param desc: Please click Yes if TSPX_iut_model_id_used supports periodic publishing.
    :return:
    """
    return True


def hdl_wid_528(desc):
    """
    Implements:
    :param desc: Please click Yes if Please click Yes if TSPX_iut_model_id_used supports publishing on state change.
    :return:
    """
    return True


def hdl_wid_529(desc):
    """
    Implements:
    :param desc: Please triggered state change that will generate publish message.
    :return:
    """
    return True


def hdl_wid_522(desc):
    """
    Implements:
    :param desc:Please send a Composition Data Get Request for page 0xff or the highest supported page number
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    pattern = re.compile(r'page\s+([0][xX][0-9a-fA-F]+)')
    val = pattern.findall(desc)
    if not val:
        logging.error("%s parsing error", hdl_wid_522.__name__)
        return False
    page = int(val[0], 16)

    btp.mesh_composition_data_get(stack.mesh.net_idx, stack.mesh.addr, page)

    return True


def hdl_wid_550(desc):
    """
    Implements:
    :param desc: Please send Heartbeat Subscription Set message to the Lower Tester
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    pattern = re.compile(r'(Source|Destination)=+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_550.__name__)
        return False
    params = dict(params)

    source = int(params.get('Source'), 16)
    destination = int(params.get('Destination'), 16)

    pattern = re.compile(r'(PeriodLog)\sset to\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_550.__name__)
        return False
    params = dict(params)

    period_log = int(params.get('PeriodLog'), 16)

    btp.mesh_cfg_heartbeat_sub_set(stack.mesh.net_idx, stack.mesh.addr, source, destination, period_log)

    return stack.mesh.status == 0x00


def hdl_wid_551(desc):
    """
    Implements:
    :param desc: Please send Heartbeat Subscription Get to the Lower Tester - PTS.
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    btp.mesh_cfg_heartbeat_sub_get(stack.mesh.net_idx, stack.mesh.addr)

    return stack.mesh.status == 0x00


def hdl_wid_552(desc):
    """
    Implements:
    :param desc: This test require two instances of PTS running. This is Lower
                 Tester 1. Please start another PTS instance and run
                 TESTCASE_LT2 test case. Prepare the IUT for provisioning by
                 Lower Tester 2. Click OK when Lower Tester 1 is ready.
                 Lower Tester 2 will provision, establish friendship and add
                 subscription list to the IUT.
    :return:
    """
    return True


def hdl_wid_555(desc):
    """
    Implements:
    :param desc: Please send Heartbeat Subscription Set message to the Lower Tester
    :return:
    """
    return hdl_wid_550(desc)


def hdl_wid_556(desc):
    """
    Implements:
    :param desc:  Please send Heartbeat Subscription Set message to the Lower Tester
    :return:
    """
    return hdl_wid_550(desc)


def hdl_wid_557(desc):
    """
    Implements:
    :param desc: Please send Heartbeat message to Low Power Node address
    :return:
    """
    return True


def hdl_wid_560(desc):
    """
    Implements:
    :param desc: Lower Tester 2 is waiting for IUT's heartbeat triggered by friendship termination.
    :return:
    """
    stack = get_stack()
    assert stack.mesh.wait_for_lpn_terminated(timeout=60)

    return True


def hdl_wid_561(desc):
    """
    Implements:
    :param desc: Lower Tester 2 is waiting for IUT's heartbeat triggered by friendship establishment.
    :return:
    """
    stack = get_stack()
    assert stack.mesh.wait_for_lpn_established(timeout=60)

    return True


def hdl_wid_562(desc):
    """
    Implements:
    :param desc: Friendship will be terminated between Lower Tester 1 and IUT.
                 Verifying no heartbeat is triggered by the termination...
    :return:
    """
    return True


def hdl_wid_563(desc):
    """
    Implements:
    :param desc: Please wait until Friendship is established between Lower Tester
                 1 and IUT. Click OK to send Heartbeat Subscription Set message
                 to IUT (Low Power Node).
    :return:
    """
    return True


def hdl_wid_564(desc):
    """
    Implements:
    :param desc: Please wait until Friendship is reestablished between Lower Tester
                 1 and IUT. Click OK to send Heartbeat Subscription Set message
                 to IUT (Low Power Node).
    :return:
    """
    stack = get_stack()
    assert stack.mesh.wait_for_lpn_established(timeout=60)

    return True


def hdl_wid_600(desc):
    """
    Implements: CONFIGURE_FAULT_ARRAY
    :param desc: Please generate faults on the IUT.
    :return:
    """
    stack = get_stack()

    test_id, cur_faults, reg_faults = btp.mesh_health_generate_faults()

    stack.mesh.health_test_id.data = test_id
    stack.mesh.health_current_faults.data = cur_faults
    stack.mesh.health_registered_faults.data = reg_faults
    return True


def hdl_wid_601(desc):
    """
    Implements: CONFIRM_HEALTH_CURRENT_STATUS
    :param desc: Please confirm the fault array = %s.
    :return:
    """
    stack = get_stack()

    # This pattern is matching fault array
    pattern = re.compile(r'array\s=\s([0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_601.__name__)
        return False

    current_faults = stack.mesh.health_current_faults.data.decode('UTF-8')

    if params[0].upper() != current_faults.upper():
        logging.error("Fault array does not match %r vs %r", params[0],
                      current_faults)
        return False
    return True


def hdl_wid_603(desc):
    """
    Implements: CONFIRM_HEALTH_FAULT_STATUS_STATUS_1
    :param desc: Please confirm the test ID %x and no registered faults.
    :return:
    """
    stack = get_stack()

    # Pattern looking for test ID
    pattern = re.compile(r"(ID)\s+([0-9a-fA-F]+)", re.IGNORECASE)
    found = pattern.findall(desc)
    if not found:
        logging.error("%s Parsing error!", hdl_wid_603.__name__)
        return False

    found = dict(found)

    # Fail if test ID does not match or IUT has faults
    if int(stack.mesh.health_test_id.data) != int(found.get('ID')) or \
            stack.mesh.health_registered_faults.data:
        return False
    return True


def hdl_wid_604(desc):
    """
    Implements: CONFIRM_HEALTH_FAULT_STATUS_STATUS_2
    :param desc: Please confirm the test ID %x and the registered fault array
                 %s.
    :return:
    """
    stack = get_stack()

    # Pattern looking for fault array and test ID
    pattern = re.compile(r"(array|ID)\s+([0-9a-fA-F]+)", re.IGNORECASE)
    found = pattern.findall(desc)
    if not found:
        logging.error("%s Parsing error!", hdl_wid_604.__name__)
        return False

    found = dict(found)

    if int(stack.mesh.health_test_id.data) != int(found.get('ID')) or \
            stack.mesh.health_registered_faults.data != found.get('array'):
        return False
    return True


def hdl_wid_605(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    if "Health Fault Get" in desc:
        pattern = re.compile(r'(Company\sID)\s=\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_605.__name__)
            return False
        params = dict(params)

        cid = int(params.get('Company ID'), 16)

        btp.mesh_health_fault_get(stack.mesh.addr, stack.mesh.app_idx, cid)
        return True

    if "Health Fault Clear" in desc:
        pattern = re.compile(r'(Company\sID)\s=\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_605.__name__)
            return False
        params = dict(params)

        cid = int(params.get('Company ID'), 16)
        ack = True

        if "Unreliable" in desc:
            ack = False

        btp.mesh_health_fault_clear(stack.mesh.addr, stack.mesh.app_idx, cid, ack)

        return (not ack) or (ack and stack.mesh.model_data == 0x00)

    if "Health Fault Test" in desc:
        pattern = re.compile(r'(Test\sID|Company\sID)\s=\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_605.__name__)
            return False
        params = dict(params)

        cid = int(params.get('Company ID'), 16)

        pattern = re.compile(r'(Test\sID|Company\sID)\s=\s+([0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_605.__name__)
            return False
        params = dict(params)

        test_id = int(params.get("Test ID"))

        ack = True
        if "Unreliable" in desc:
            ack = False

        btp.mesh_health_fault_test(stack.mesh.addr, stack.mesh.app_idx, cid, test_id, ack)

        return (not ack) or (ack and stack.mesh.model_data == [test_id, cid])

    if "Health Period Get" in desc:
        btp.mesh_health_period_get(stack.mesh.addr, stack.mesh.app_idx)
        return True

    if "Health Period Set" in desc:
        devisor = 0x01
        ack = True

        if "Unreliable" in desc:
            ack = False

        btp.mesh_health_period_set(stack.mesh.addr, stack.mesh.app_idx, devisor, ack)

        return (not ack) or (ack and stack.mesh.model_data == devisor)

    if "Attention Get" in desc:
        btp.mesh_health_attention_get(stack.mesh.addr, stack.mesh.app_idx)
        return True

    if "Attention Set" in desc:
        attention = 0x01
        ack = True

        if "Unreliable" in desc:
            ack = False

        btp.mesh_health_attention_set(stack.mesh.addr, stack.mesh.app_idx, attention, ack)
        return True


def hdl_wid_606(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    return stack.mesh.model_data == 1

def hdl_wid_625(desc):
    """
    Implements: NETKEY_REDUCE_RESOURCES
    :param desc: Reduce resources to only allow one NetKey Index. Press OK when
                 done.
    :return:
    """

    logging.debug("CONFIG_BT_MESH_SUBNET_COUNT=1")
    return True


def hdl_wid_626(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    return True


def hdl_wid_650(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    if not stack.mesh.iut_is_provisioner:
        return True

    if "Config Relay Get" in desc:
        btp.mesh_cfg_relay_get(stack.mesh.net_idx, stack.mesh.addr)
        return True

    if "Config Relay Set" in desc:
        new_relay = 0x00
        new_transmit = 0x00
        btp.mesh_cfg_relay_set(stack.mesh.net_idx, stack.mesh.addr, new_relay, new_transmit)
        return True

    if "Config Model Publication GET" in desc:
        pattern = re.compile(r'(Element\sAddress|Model\sId)\s=\s+([0][xX][0-9a-fA-F]+)')
        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_650.__name__)
            return False
        params = dict(params)

        el_address = int(params.get('Element Address'), 16)
        model_id = int(params.get('Model Id'), 16)

        btp.mesh_cfg_model_publication_get(stack.mesh.net_idx, stack.mesh.addr, el_address, model_id)
        return stack.mesh.status == 0x00

    if "Config Model Publication SET" in desc:
        pattern = re.compile(r'(Element\sAddress|Publish\sAddress|AppKey\sIndex|Credential\sFlag|RFU|Publish\sTTL|Publish\sPeriod|'
                             r'ModelId)\s=\s+([0-9a-fA-F]+)')

        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_650.__name__)
            return False
        params = dict(params)

        el_address = int(params.get('Element Address'), 16)
        pub_addr = int(params.get('Publish Address'), 16)
        appkey_index = int(params.get('AppKey Index'), 16)
        cred_flag = int(params.get('Credential Flag'), 16)
        ttl = int(params.get('Publish TTL'), 16)
        period = int(params.get('Publish Period'), 16)
        model_id = int(params.get('ModelId'), 16)
        transmit = 0x00

        if "Publish Address = a group address" in desc:
            pub_addr = 0xC000

        btp.mesh_cfg_model_publication_set(stack.mesh.net_idx, stack.mesh.addr, el_address, model_id, pub_addr,
                                              appkey_index, cred_flag, ttl, period, transmit)
        return stack.mesh.status == 0x00

    if 'Config Model Publication VIRTUAL ADDRESS SET' in desc:
        pattern = re.compile(
            r'(Element\sAddress|Publish\sAddress|AppKey\sIndex|Credential\sFlag|RFU|Publish\sTTL|Publish\s'
            r'Period|ModelId)\s=\s+([0-9a-fA-F]+)')

        params = pattern.findall(desc)

        if not params:
            logging.error("%s parsing error", hdl_wid_650.__name__)
            return False
        params = dict(params)

        el_address = int(params.get('Element Address'), 16)
        appkey_index = int(params.get('AppKey Index'), 16)
        cred_flag = int(params.get('Credential Flag'), 16)
        ttl = int(params.get('Publish TTL'), 16)
        period = int(params.get('Publish Period'), 16)
        model_id = int(params.get('ModelId'), 16)
        transmit = 0x00
        app_key = '0123456789abcdef0123456789fedcba'

        btp.mesh_cfg_appkey_add(stack.mesh.net_idx, stack.mesh.addr, stack.mesh.net_key_index, app_key,
                                appkey_index)
        btp.mesh_cfg_model_app_bind(stack.mesh.net_idx, stack.mesh.addr, el_address, appkey_index,
                                    +                                    model_id)


        btp.mesh_cfg_model_pub_va_set(stack.mesh.net_idx, stack.mesh.addr, el_address, model_id, stack.mesh.dev_uuid,
                                      appkey_index, cred_flag, ttl, period, transmit)
        logging.debug("Status = 0x%2x", stack.mesh.status)
        return stack.mesh.status == 0x00

    if "NetKey Add" in desc:
        net_key_idx = 0x0001
        net_key = '00000000000000000000000000000001'

        btp.mesh_cfg_netkey_add(stack.mesh.net_idx, stack.mesh.addr, net_key, net_key_idx)

        return stack.mesh.status == 0x00

    if "NetKey Update" in desc:
        net_key = '00000000000000000000000000000001'

        btp.mesh_cfg_netkey_update(stack.mesh.net_idx, stack.mesh.addr, net_key, stack.mesh.net_key_index)

        return stack.mesh.status == 0x00

    if "NetKey Get" in desc:
        btp.mesh_cfg_netkey_get(stack.mesh.net_idx, stack.mesh.addr)

        return True

    if "NetKey Delete" in desc:
        pattern = re.compile(r'index\s+([0-9a-fA-F]+)')
        val = pattern.findall(desc)
        if not val:
            logging.error("%s parsing error", hdl_wid_650.__name__)
            return False
        net_key_idx = int(val[0], 16)
        btp.mesh_cfg_netkey_del(stack.mesh.net_idx, stack.mesh.addr, net_key_idx)

        return stack.mesh.status == 0x00

    if "Node Reset" in desc:
        btp.mesh_cfg_node_reset(stack.mesh.net_idx, stack.mesh.addr)

        return stack.mesh.status == 0x01


def hdl_wid_652(desc):
    """
    Implements: CONFIRM_GENERIC
    :param desc: Please confirm the %s = %s.
    :return:
    """

    # TODO: Confirm composition data
    return True
