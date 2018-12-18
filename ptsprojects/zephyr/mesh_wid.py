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
from pybtp import btp
from pybtp.types import Perm, MeshVals
import re
import time
from ptsprojects.stack import get_stack

# Mesh ATS ver. 1.0

log = logging.debug


def hdl_pending_mesh_wids(wid, test_case_name, description):
    stack = get_stack()
    module = sys.modules[__name__]

    if stack.synch.is_required_synch(test_case_name, wid):
        actions = stack.synch.perform_synch(wid, test_case_name, description)

        if actions:
            for action in actions:
                action_wid = action[0]
                action_description = action[1]
                action_test_case_name = action[2]
                action_response_cb = action[3]

                handler = getattr(module, "hdl_wid_%d" % action_wid)
                result = handler(action_description)

                # Register pending response handler
                stack.synch.prepare_pending_response(action_test_case_name,
                                                     result)

            return None

        # wid is on synchronise list but has to wait for other
        return "WAIT"

    return None


def mesh_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", mesh_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]
    pending_responses = None

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        current_response = handler(description)

        stack = get_stack()
        if stack.synch:
            response = hdl_pending_mesh_wids(wid, test_case_name, description)

            if response == "WAIT":
                return response

        if stack.synch:
            stack.synch.set_pending_responses_if_any()

        return current_response

    except AttributeError as e:
        logging.exception(e.message)


# wid handlers section begin
def hdl_wid_6(desc):
    """
    Implements: SEND_ADV_BEACON
    :param desc: Advertising Mesh Beacon Packet. Wait for other side to be
                 ready and click OK to broadcast Mesh beacon packet, otherwise
                 click Cancel.
    :return:
    """
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

    ret = stack.mesh.oob_data.data

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
    else:
        if stack.mesh.is_provisioned.data:
            return True
        else:
            return True

    return True


def hdl_wid_13(desc):
    """
    Implements: RE_PROVISIONING_PROVISIONER
    :param desc: There is no shared security information. Please remove any
                 security information if any. PTS is waiting for beacon to
                 start provisioning from
    :return:
    """
    stack = get_stack()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_init()
    else:
        if stack.mesh.is_provisioned.data:
            return True
        else:
            return True

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
    pattern = re.compile(r'(TTL|CTL|SRC|DST|TransportPDU)\:'
                         r'\s+\[([0][xX][0-9a-fA-F]+)\]')
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
    stack = get_stack()

    # This pattern is matching Time to Live (TTL) value, Source (SRC) and
    # Destination (DST) of the network packet to be sent
    pattern = re.compile(r'(TTL|SRC|DST)\:\s+\[([0][xX][0-9a-fA-F]+)\]')
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
    stack = get_stack()
    return 'C000'


def hdl_wid_21(desc):
    """
    Implements: ENTER_VIRTUAL_ADDRESS
    :param desc: Please enter a valid virtual address the IUT knows
    :return:
    """
    stack = get_stack()
    return '8000'


def hdl_wid_23(desc):
    """
    Implements: SEND_SEGMENTED_DATA
    :param desc: Please send a segmented message encrypted with an application
                 key with source address 0x%04X and destination address 0x%04X
    :return:
    """
    stack = get_stack()

    # This pattern is matching source and destination addresses
    pattern = re.compile(
        r'(source\saddress|destination\saddress)\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_23.__name__)
        return

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

    if stack.mesh.prov_invalid_bearer_rcv.data:
        rsp = True
    else:
        rsp = False

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
                         r'\s+\\[([0][xX][0-9a-fA-F]+)\\]')
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
    pattern = re.compile(r'(TTL|CTL|SRC|DST)\:\s+\[([0][xX][0-9a-fA-F]+)\]')
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
    recv_pdu = hex(int(recv_pdu, 16))

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
    stack = get_stack()

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

    if not stack.mesh.last_seen_prov_link_state.data:
        return False

    state, bearer = stack.mesh.last_seen_prov_link_state.data
    if state is 'closed':
        return True
    return False


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
    pattern = re.compile(r'(address)\s+\:\s+([0][xX][0-9a-fA-F]+)')
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
    stack = get_stack()
    return True


def hdl_wid_43(desc):
    """
    Implements: SEND_DATA_INVALID_KEY
    :param desc: PTS will send a message with invalid key. No response is
                 expected.
    :return:
    """
    stack = get_stack()
    return True


def hdl_wid_44(desc):
    """
    Implements: SEND_SEGMENTED_DATA_VIRTUAL
    :param desc: Please send a segmented message encrypted with an application
                 key with source address 0x%04X and destination label %s
                 (address 0x%04X)
    :return:
    """
    stack = get_stack()

    # This pattern is matching source and destination label addresses
    pattern = re.compile(
        r'(source\saddress|\(address)\s+([0][xX][0-9a-fA-F]+)')
    params = pattern.findall(desc)
    if not params:
        logging.error("%s parsing error", hdl_wid_44.__name__)
        return

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
    stack = get_stack()
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


def hdl_wid_81(desc):
    """
    Implements: IUT_ADVERTISE_UNPROVISIONED_STATE
    :param desc: Please order IUT to advertise Connectable Advertising PDU for
                 Mesh Provisioning Service.
    :return:
    """
    stack = get_stack()
    btp.mesh_config_prov()
    btp.mesh_init()
    return True


def hdl_wid_85(desc):
    stack = get_stack()
    btp.gap_disconn()

    return True


def hdl_wid_90(desc):
    """
    Implements: IUT_SEND_SECURE_NETWORK_BEACON
    :param desc: Please order IUT to send secure network beacon to the PTS.
                 PTS will wait for
    :return:
    """
    stack = get_stack()

    if stack.mesh.is_provisioned.data is True:
        return True
    else:
        return False


def hdl_wid_94(desc):
    """
    Implements: IUT_SEND_SECURE_NETWORK_BEACON_WITH_FLAGS
    :param desc: Please order IUT to send a secure network beacon with Key
                 Refresh Flag set to %d and IV Update Flag set to %d
    :return:
    """
    stack = get_stack()
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
        return

    (handle, permission, type_uuid) = attr.pop()
    if not permission & Perm.write:
        return False

    # Mesh Provisioning data out
    attr = btp.gatts_get_attrs(type_uuid='2adc')
    if not attr:
        return

    (handle, permission, type_uuid) = attr.pop()
    if permission & Perm.write:
        return False
    return True


def hdl_wid_201(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON
    :param desc: Order IUT to generate a non-connectable Secure Network beacon
                 (Mesh Beacon with Beacon type = 0x01).
    :return:
    """
    stack = get_stack()

    if stack.mesh.is_provisioned.data is True:
        return True
    else:
        return False


def hdl_wid_202(desc):
    """
    Implements: IUT_GENERATE_UPDATE_IN_PROGRESS_SECURE_NETWORK_BEACON
    :param desc: Order IUT to enter the 'IV Update in Progress' state and set
                 the 'IV Update in progress' flag in the secure network beacon.
                 Click OK when ready.
    :return:
    """
    stack = get_stack()

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

    if stack.mesh.is_provisioned.data is True:
        return True
    else:
        return False


def hdl_wid_204(desc):
    """
    Implements: IUT_ACCEPT_MESH_MESSAGE_IN_PROGRESS_STATE
    :param desc: Click OK when IUT is ready to accept Mesh messages with old IV
                 Index (m - 1) and new IV index (m).
    :return:
    """
    stack = get_stack()
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
    btp.mesh_iv_update_test_mode(True)
    btp.mesh_iv_update_toggle()
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
    else:
        return False


def hdl_wid_216(desc):
    """
    Implements: IUT_GENERATE_SECURE_NETWORK_BEACON_LESS96
    :param desc: Please make sure IUT has performed an IV Update procedure less
                 than 96 hours ago. PTS will verify IUT does not perform
                 another update. Order IUT to generate non-connectable Secure
                 Network beacons (Mesh Beacon with Beacon type = 0x01).
    :return:
    """
    stack = get_stack()

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
    stack = get_stack()
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
        btp.mesh_iv_update_toggle()
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
    stack = get_stack()

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
    stack = get_stack()

    btp.mesh_iv_update_test_mode(False)
    return True


def hdl_wid_262(desc):
    """
    Implements: KEY_REFRESH_READY_FOR_ROUND2
    :param desc: Press OK when tester and IUT is ready to go to the second
                 round of key refresh
    :return:
    """
    return True


def hdl_wid_268(desc):
    """
    Implements: KEY_REFRESH_READY
    :param desc: Press OK when IUT is ready for Key Refresh Procedure
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
    stack = get_stack()
    return True


def hdl_wid_285(desc):
    """
    Implements: KEY_REFRESH_READY_SKIP_PAHSE_2
    :param desc: Press OK when IUT is ready for Key Refresh Procedure with
                 skipping phase 2
    :return:
    """
    stack = get_stack()
    return True


def hdl_wid_303(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn(True)
    return True


def hdl_wid_308(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn_poll()
    return True


def hdl_wid_312(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn_poll()
    return True


def hdl_wid_313(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn_poll()
    return True


def hdl_wid_314(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn_poll()
    return True


def hdl_wid_315(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()
    btp.mesh_lpn(True)
    return True


def hdl_wid_326(desc):
    """
    Implements:
    :param desc:
    :return:
    """
    stack = get_stack()

    btp.mesh_lpn(False)
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


def hdl_wid_353(desc):
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


def hdl_wid_519(desc):
    """
    Implements: CONFIRM_DEVICE_RESET
    :param desc: Click OK to put the IUT back into an unprovisioned state.
    :return:
    """
    stack = get_stack()

    btp.mesh_reset()
    return True


def hdl_wid_520(desc):
    """
    Implements: NODE_IDENTITY_START_AD
    :param desc: Please configure the IUT to start advertising on all networks.
    :return:
    """
    stack = get_stack()

    btp.mesh_proxy_identity()
    return True


def hdl_wid_521(desc):
    """
    Implements: NODE_IDENTITY_STOP_AD
    :param desc: Please configure the IUT to stop advertising on all networks.
    :return:
    """
    stack = get_stack()

    time.sleep(60)
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

    current_faults = stack.mesh.health_current_faults.data

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


def hdl_wid_625(desc):
    """
    Implements: NETKEY_REDUCE_RESOURCES
    :param desc: Reduce resources to only allow one NetKey Index. Press OK when
                 done.
    :return:
    """
    stack = get_stack()

    logging.debug("CONFIG_BT_MESH_SUBNET_COUNT=1")
    return True


def hdl_wid_652(desc):
    """
    Implements: CONFIRM_GENERIC
    :param desc: Please confirm the %s = %s.
    :return:
    """
    stack = get_stack()

    # TODO: Confirm composition data
    return True
