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

from uuid import UUID
import logging
import struct

from .btpdefs import defs
from .btpdefs.types import BTPError, att_rsp_str, addr2btp_ba

CONTROLLER_INDEX = 0


def raise_stack_getter_exception():
    raise Exception('stack_getter() has not been set!')


# Depending on the project, the Stack instance can
# be implemented as global one or each Tester thread
# can have its own Stack instance.
stack_getter = raise_stack_getter_exception


def get_stack():
    return stack_getter()


def set_stack_getter(_stack_getter):
    global stack_getter

    stack_getter = _stack_getter


def address_to_ba(bd_addr_type=None, bd_addr=None):
    """Get Bluetooth address in bytearray format"""
    stack = get_stack()
    data = bytearray()
    bd_addr_ba = addr2btp_ba(stack.pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(stack.pts_addr_type_get(bd_addr_type)).encode('utf-8')
    data.extend(bd_addr_type_ba)
    data.extend(bd_addr_ba)
    return data


def pts_addr_type_get(bd_addr=None):
    return get_stack().pts_addr_type_get(bd_addr=bd_addr, lt=1)


def pts_addr_get(bd_addr_type=None):
    return get_stack().pts_addr_get(bd_addr_type=bd_addr_type, lt=1)


def lt2_addr_type_get(bd_addr_type=None):
    return get_stack().pts_addr_type_get(bd_addr_type=bd_addr_type, lt=2)


def lt2_addr_get(bd_addr=None):
    return get_stack().pts_addr_get(bd_addr=bd_addr, lt=2)


def btp_hdr_check(rcv_hdr, exp_svc_id, exp_op=None):
    if rcv_hdr.svc_id != exp_svc_id:
        raise BTPError("Incorrect service ID %s in the response, expected %s!"
                       % (rcv_hdr.svc_id, exp_svc_id))

    if rcv_hdr.op == defs.BTP_STATUS:
        raise BTPError("Error opcode in response!")

    if exp_op and exp_op != rcv_hdr.op:
        raise BTPError(
            "Invalid opcode 0x%.2x in the response, expected 0x%.2x!" %
            (rcv_hdr.op, exp_op))


def read_supp_svcs():
    logging.debug("%s", read_supp_svcs.__name__)
    iutctl = get_iut()
    stack = get_stack()

    iutctl.btp_socket.send(*CORE['read_supp_svcs'])

    # Expected result
    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    btp_hdr_check(tuple_hdr,
                  defs.BTP_SERVICE_ID_CORE,
                  defs.CORE_READ_SUPPORTED_SERVICES)
    logging.debug("%s received %r %r", read_supp_svcs.__name__,
                  tuple_hdr, tuple_data)

    stack.supported_svcs = int.from_bytes(tuple_data[0], 'little')


CORE = {
    "gap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gatt_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "gatt_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "l2cap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "l2cap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                    defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "mesh_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "mesh_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "mmdl_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MMDL),
    "mmdl_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MMDL),
    "gatt_cl_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                    defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATTC),
    "gatt_cl_unreg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_UNREGISTER_SERVICE,
                      defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATTC),
    "vcs_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VCS),
    "vocs_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VOCS),
    "aics_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_AICS),
    "ias_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_IAS),
    "pacs_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_PACS),
    "ascs_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_ASCS),
    "bap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_BAP),
    "has_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_HAS),
    "csis_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CSIS),
    "micp_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MICP),
    "mics_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MICS),
    "ccp_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CCP),
    "vcp_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VCP),
    "cas_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CAS),
    "mcp_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MCP),
    "gmcs_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GMCS),
    "hap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_HAP),
    "cap_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CAP),
    "csip_reg": (defs.BTP_SERVICE_ID_CORE, defs.CORE_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CSIP),
    # GENERATOR append 4
    "read_supp_cmds": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "read_supp_svcs": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_SERVICES,
                       defs.BTP_INDEX_NONE, ""),
    "log_message": (defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE,
                    defs.BTP_INDEX_NONE),
}


def btp_hdr_check(rcv_hdr, exp_svc_id, exp_op=None):
    if rcv_hdr.svc_id != exp_svc_id:
        raise BTPError("Incorrect service ID %s in the response, expected %s!"
                       % (rcv_hdr.svc_id, exp_svc_id))

    if rcv_hdr.op == defs.BTP_STATUS:
        raise BTPError("Error opcode in response!")

    if exp_op and exp_op != rcv_hdr.op:
        raise BTPError(
            "Invalid opcode 0x%.2x in the response, expected 0x%.2x!" %
            (rcv_hdr.op, exp_op))


def core_reg_svc_gap():
    logging.debug("%s", core_reg_svc_gap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gap_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_gap():
    logging.debug("%s", core_unreg_svc_gap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gap_unreg'])

    core_unreg_svc_rsp_succ()


def core_reg_svc_gatt():
    logging.debug("%s", core_reg_svc_gatt.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gatt_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_gatt():
    logging.debug("%s", core_unreg_svc_gatt.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gatt_unreg'])


def core_reg_svc_l2cap():
    logging.debug("%s", core_reg_svc_l2cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['l2cap_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_l2cap():
    logging.debug("%s", core_unreg_svc_l2cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['l2cap_unreg'])


def core_reg_svc_mesh():
    logging.debug("%s", core_reg_svc_mesh.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['mesh_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_mesh():
    logging.debug("%s", core_unreg_svc_mesh.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mesh_unreg'])


def core_reg_svc_mmdl():
    logging.debug("%s", core_reg_svc_mmdl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['mmdl_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_mmdl():
    logging.debug("%s", core_unreg_svc_mmdl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mmdl_unreg'])


def core_reg_svc_gatt_cl():
    logging.debug("%s", core_reg_svc_gatt_cl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gatt_cl_reg'])

    core_reg_svc_rsp_succ()


def core_unreg_svc_gatt_cl():
    logging.debug("%s", core_unreg_svc_gatt_cl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gatt_cl_unreg'])


def core_reg_svc_vcs():
    logging.debug("%s", core_reg_svc_vcs.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['vcs_reg'])


def core_reg_svc_vocs():
    logging.debug("%s", core_reg_svc_vocs.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['vocs_reg'])


def core_reg_svc_aics():
    logging.debug("%s", core_reg_svc_aics.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['aics_reg'])


def core_reg_svc_ias():
    logging.debug("%s", core_reg_svc_ias.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['ias_reg'])


def core_reg_svc_pacs():
    logging.debug("%s", core_reg_svc_pacs.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['pacs_reg'])


def core_reg_svc_ascs():
    logging.debug("%s", core_reg_svc_ascs.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['ascs_reg'])


def core_reg_svc_has():
    logging.debug("%s", core_reg_svc_has.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['has_reg'])


def core_reg_svc_bap():
    logging.debug("%s", core_reg_svc_bap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['bap_reg'])


def core_reg_svc_csis():
    logging.debug("%s", core_reg_svc_csis.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['csis_reg'])


def core_reg_svc_micp():
    logging.debug("%s", core_reg_svc_micp.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['micp_reg'])


def core_reg_svc_mics():
    logging.debug("%s", core_reg_svc_mics.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mics_reg'])


def core_reg_svc_ccp():
    logging.debug("%s", core_reg_svc_ccp.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['ccp_reg'])

    
def core_reg_svc_cas():
    logging.debug("%s", core_reg_svc_cas.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['cas_reg'])


def core_reg_svc_vcp():
    logging.debug("%s", core_reg_svc_vcp.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['vcp_reg'])


def core_reg_svc_mcp():
    logging.debug("%s", core_reg_svc_mcp.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mcp_reg'])


def core_reg_svc_gmcs():
    logging.debug("%s", core_reg_svc_gmcs.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gmcs_reg'])


def core_reg_svc_hap():
    logging.debug("%s", core_reg_svc_hap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['hap_reg'])


def core_reg_svc_cap():
    logging.debug("%s", core_reg_svc_cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['cap_reg'])


def core_reg_svc_csip():
    logging.debug("%s", core_reg_svc_csip.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['csip_reg'])


# GENERATOR append 1

def core_reg_svc_rsp_succ():
    logging.debug("%s", core_reg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_REGISTER_SERVICE,
                       defs.BTP_INDEX_NONE,
                       0),
                      (b'',))

    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    logging.debug("response is valid")


def core_unreg_svc_rsp_succ():
    logging.debug("%s", core_unreg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_UNREGISTER_SERVICE,
                       defs.BTP_INDEX_NONE,
                       0),
                      (b'',))

    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    logging.debug("received %r %r", tuple_hdr, tuple_data)
    logging.debug("expected %r", expected_frame)

    if (tuple_hdr, tuple_data) != expected_frame:
        logging.error("frames mismatch")
        raise BTPError("Unexpected response received!")
    logging.debug("response is valid")


def core_log_message(message):
    logging.debug("%s", core_log_message.__name__)

    data = bytearray(struct.pack('H', len(message)) + message.encode('utf-8'))

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['log_message'], data=data)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE)


def btp2uuid(uuid_len, uu):
    if uuid_len == 2:
        (uu,) = struct.unpack("H", uu)
        return format(uu, 'x').upper().rjust(4, '0')
    return UUID(bytes=uu[::-1]).urn[9:].replace('-', '').upper()


def get_iut_method():
    return get_iut()


def init(get_iut_method):
    global get_iut

    get_iut = get_iut_method


from .gap import GAP_EV
from .gatt import GATT_EV
from .l2cap import L2CAP_EV
from .mesh import MESH_EV
from .gatt_cl import GATTC_EV
from .aics import AICS_EV
from .vocs import VOCS_EV
from .vcs import VCS_EV
from .ias import IAS_EV
from .pacs import PACS_EV
from .ascs import ASCS_EV
from .bap import BAP_EV
from .core import CORE_EV
from .micp import MICP_EV
from .mics import MICS_EV
from .ccp import CCP_EV
from .vcp import VCP_EV
from .mcp import MCP_EV
from .gmcs import GMCS_EV
from .hap import HAP_EV
from .cap import CAP_EV
from .csip import CSIP_EV
# GENERATOR append 2


def event_handler(hdr, data):
    logging.debug("%s %r %r", event_handler.__name__, hdr, data)

    stack = get_stack()
    if not stack:
        logging.info("Stack not initialized")
        return False

    service_map = {
        defs.BTP_SERVICE_ID_MESH: (MESH_EV, stack.mesh),
        defs.BTP_SERVICE_ID_L2CAP: (L2CAP_EV, stack.l2cap),
        defs.BTP_SERVICE_ID_GAP: (GAP_EV, stack.gap),
        defs.BTP_SERVICE_ID_GATT: (GATT_EV, stack.gatt),
        defs.BTP_SERVICE_ID_GATTC: (GATTC_EV, stack.gatt_cl),
        defs.BTP_SERVICE_ID_IAS: (IAS_EV, stack.ias),
        defs.BTP_SERVICE_ID_VCS: (VCS_EV, stack.vcs),
        defs.BTP_SERVICE_ID_AICS: (AICS_EV, stack.aics),
        defs.BTP_SERVICE_ID_VOCS: (VOCS_EV, stack.vocs),
        defs.BTP_SERVICE_ID_PACS: (PACS_EV, stack.pacs),
        defs.BTP_SERVICE_ID_ASCS: (ASCS_EV, stack.ascs),
        defs.BTP_SERVICE_ID_BAP: (BAP_EV, stack.bap),
        defs.BTP_SERVICE_ID_CORE: (CORE_EV, stack.core),
        defs.BTP_SERVICE_ID_MICP: (MICP_EV, stack.micp),
        defs.BTP_SERVICE_ID_MICS: (MICS_EV, stack.mics),
        defs.BTP_SERVICE_ID_CCP: (CCP_EV, stack.ccp),
        defs.BTP_SERVICE_ID_VCP: (VCP_EV, stack.vcp),
        defs.BTP_SERVICE_ID_MCP: (MCP_EV, stack.mcp),
        defs.BTP_SERVICE_ID_GMCS: (GMCS_EV, stack.gmcs),
        defs.BTP_SERVICE_ID_HAP: (HAP_EV, stack.hap),
        defs.BTP_SERVICE_ID_CAP: (CAP_EV, stack.cap),
        defs.BTP_SERVICE_ID_CSIP: (CSIP_EV, stack.csip),
        # GENERATOR append 3
    }

    if hdr.svc_id in service_map:
        event_dict, stack_obj = service_map[hdr.svc_id]
        if hdr.op in event_dict and stack_obj:
            cb = event_dict[hdr.op]
            cb(stack_obj, data[0], hdr.data_len)
            return True

    # TODO: Raise BTP error instead of logging
    logging.error("Unhandled event! svc_id %s op %s", hdr.svc_id, hdr.op)
    return False
