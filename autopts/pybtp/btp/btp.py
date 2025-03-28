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

from collections import namedtuple
from uuid import UUID
import logging
import re
import struct
import math

from autopts.pybtp.common import supported_svcs_cmds, reg_unreg_service
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from .. import defs
from autopts.pybtp.types import BTPError, att_rsp_str

#  get IUT global method from iutctl
get_iut = None

#loading as CORE to maintain backward compatibility with older code snippet
CORE = reg_unreg_service

# Address
LeAddress = namedtuple('LeAddress', 'addr_type addr')
PTS_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')
LT2_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')
LT3_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')

# Devices found
LeAdv = namedtuple('LeAdv', 'addr_type addr rssi flags eir')

CONTROLLER_INDEX = 0
CONTROLLER_INDEX_NONE = 0xff


def read_supp_svcs():
    logging.debug("%s", read_supp_svcs.__name__)
    iutctl = get_iut()
    stack = get_stack()

    iutctl.btp_socket.send(*CORE['read_supp_svcs'])

    # Expected result
    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    btp_hdr_check(tuple_hdr,
                  defs.BTP_SERVICE_ID_CORE,
                  defs.BTP_CORE_CMD_READ_SUPPORTED_SERVICES)
    logging.debug("%s received %r %r", read_supp_svcs.__name__,
                  tuple_hdr, tuple_data)

    stack.supported_svcs = int.from_bytes(tuple_data[0], 'little')

def read_supported_commands(service):
    iutctl = get_iut()
    stack = get_stack()
    svc_key = service.upper()

    entry = supported_svcs_cmds.get(svc_key)
    if entry is None:
        logging.warning("Service %s is not registered", svc_key)
        return

    if "supported_commands" not in entry:
        logging.warning("No READ_SUPPORTED_COMMANDS for %s", svc_key)
        return

    service_bitmask = entry.get("service")
    if service_bitmask is None:
        logging.warning("No service bitmask for %s", svc_key)
        return

    try:
        service_id = int(math.log2(service_bitmask))
    except Exception as err:
        logging.error("Invalid mask for %s: %s", svc_key, err)
        return

    opcode_supp_cmd = entry["supported_commands"]

    cmd_tuple = (service_id, opcode_supp_cmd, defs.BTP_INDEX_NONE, "")
    iutctl.btp_socket.send(*cmd_tuple)
    tuple_hdr, tuple_data = iutctl.btp_socket.read()

    btp_hdr_check(tuple_hdr, exp_svc_id=service_id, exp_op=opcode_supp_cmd)

    data_bytes = tuple_data[0] if isinstance(tuple_data, tuple) and tuple_data else tuple_data
    supported_cmds_value = int.from_bytes(data_bytes, 'little')

    if not isinstance(stack.supported_cmds, dict):
        stack.supported_cmds = {}
    stack.supported_cmds[svc_key] = supported_cmds_value


def core_reg_svc_univ(service_key: str, service_name: str):
    """
    Universal service registration.
    Registers a BTP service via CORE and reads supported commands if service_name is set.
    Usage:
    TestFunc(lambda: core_reg_svc_univ("gap_reg", "GAP"))
    TestFunc(lambda: core_reg_svc_univ("ias_reg", ""))  # skip reading commands
    """
    logging.debug("core_reg_svc_univ: %s (%s)", service_key, service_name)
    iutctl = get_iut()

    try:
        iutctl.btp_socket.send(*CORE[service_key])
    except KeyError:
        logging.error("CORE key %s not found", service_key)
        return

    core_reg_svc_rsp_succ(service_name)


def clear_verify_values():
    stack = get_stack()
    stack.gatt_cl.verify_values = []


def add_to_verify_values(item):
    stack = get_stack()
    stack.gatt_cl.verify_values.append(item)


def get_verify_values():
    stack = get_stack()
    return stack.gatt_cl.verify_values


def extend_verify_values(item):
    stack = get_stack()
    stack.gatt_cl.verify_values.extend(item)


def verify_att_error(description):
    logging.debug("description=%r", description)

    description_values = []

    for err_code, err_string in att_rsp_str.items():
        if err_string and err_string in description:
            description_values.append(err_string)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    logging.debug("Description values: %r", description_values)

    for value in description_values:
        logging.debug("Verifying: %r", value)

        try:
            if value not in verify_values:
                logging.debug("Verification failed, value not in verify values")
                return False
        except TypeError:
            logging.debug("Value under verification is not string")

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_description(description):
    """A function to verify that values are in PTS MMI description

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description_values = re.findall(r"(?:'|=\s+)([0-9-xA-Fa-f]{2,})", description)
    logging.debug("Description values: %r", description_values)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    converted_verify = []

    # convert small values to int to simplify verification.
    # Some values are displayed with leading zeros
    for verify in verify_values:
        verify = verify.upper()
        if len(verify) < 8:
            converted_verify.append(int(verify, 16))
        else:
            converted_verify.append(verify)

    for value in description_values:
        logging.debug("Verifying: %r", value)

        value = value.upper()

        if len(value) < 8:
            value = int(value, 16)

        try:
            if value not in converted_verify:
                logging.debug("Verification failed, value not in verify values")
                return False
        except TypeError:
            logging.debug("Value under verification is not string")

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_description_truncated(description):
    """A function to verify that truncated values are in PTS MMI description.

    Verification is successful if the PTS MMI description contains a value
    starting with the value under verification.

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description_values = re.findall(r"(?:'|=\s+)([0-9-xA-Fa-f]{2,})", description)
    logging.debug("Description values: %r", description_values)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    verify_values = list(map(str.upper, verify_values))
    description_values = list(map(str.upper, description_values))

    unverified_desc = [x for x in description_values if x not in verify_values]
    if unverified_desc:
        logging.debug("Verifying for partial matches: %r", unverified_desc)

        for desc_value in unverified_desc:
            matches = [x for x in verify_values if desc_value.startswith(x) and len(x) > 8]
            if not matches:
                logging.debug("Verification failed, %r not in verify values", desc_value)
                return False

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_multiple_read_description(description):
    """A function to verify that merged multiple read att values are in

    PTS MMI description.

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    MMI.reset()
    MMI.parse_description(description)
    description_values = MMI.args
    logging.debug("Description values: %r", description_values)

    got_mtp_read = [''.join(description_values)]

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    exp_mtp_read = ""
    for value in verify_values:
        try:
            exp_mtp_read = exp_mtp_read.join(value)
        except TypeError:
            value = value.decode("utf-8")
            exp_mtp_read = exp_mtp_read.join(value)

    if exp_mtp_read not in got_mtp_read:
        logging.debug("Verification failed, value not in description")
        return False

    logging.debug("Multiple read verifications passed")

    clear_verify_values()

    return True


def parse_passkey_description(description):
    """A function to parse passkey from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\b[0-9]+\b", description)
    if match:
        pk = match.group(0)
        logging.debug("passkey=%r", pk)
        return int(pk)

    return None


def parse_handle_description(description):
    """A function to parse handle from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\bhandle (?:0x)?([0-9A-Fa-f]+)\b", description)
    if match:
        handle = match.group(1)
        logging.debug("handle=%r", handle)
        return int(handle)

    return None


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


def bd_addr_convert(bdaddr):
    """ Remove colons from address and convert to lower case """
    if isinstance(bdaddr, bytes):
        bdaddr = bdaddr.decode("utf-8")
    return "".join(bdaddr.split(':')).lower()


def pts_addr_get(bd_addr=None):
    """" If address provided, convert, otherwise, use stored address. """
    if bd_addr is None:
        return PTS_BD_ADDR.addr
    return bd_addr_convert(bd_addr)


def pts_addr_type_get(bd_addr_type=None):
    """"
    If address type provided, return it, otherwise,
    use stored address.
    """
    if bd_addr_type is None:
        return PTS_BD_ADDR.addr_type
    return bd_addr_type


def set_pts_addr(addr, addr_type):
    global PTS_BD_ADDR
    PTS_BD_ADDR = LeAddress(addr_type=addr_type, addr=bd_addr_convert(addr))


def lt2_addr_get(bd_addr=None):
    """" If address provided, convert, otherwise, use stored address. """
    if bd_addr is None:
        return LT2_BD_ADDR.addr
    return bd_addr_convert(bd_addr)


def lt2_addr_type_get(bd_addr_type=None):
    """"
    If address type provided, return it, otherwise,
    use stored address.
    """
    if bd_addr_type is None:
        return LT2_BD_ADDR.addr_type
    return bd_addr_type


def lt3_addr_get(bd_addr=None):
    """" If address provided, convert, otherwise, use stored address. """
    if bd_addr is None:
        return LT3_BD_ADDR.addr
    return bd_addr_convert(bd_addr)


def lt3_addr_type_get(bd_addr_type=None):
    """"
    If address type provided, return it, otherwise,
    use stored address.
    """
    if bd_addr_type is None:
        return LT3_BD_ADDR.addr_type
    return bd_addr_type


def set_lt2_addr(addr, addr_type):
    global LT2_BD_ADDR
    LT2_BD_ADDR = LeAddress(addr_type=addr_type, addr=bd_addr_convert(addr))


def set_lt3_addr(addr, addr_type):
    global LT3_BD_ADDR
    LT3_BD_ADDR = LeAddress(addr_type=addr_type, addr=bd_addr_convert(addr))


def core_reg_svc_gap():
    core_reg_svc_univ("gap_reg", "GAP")


def core_unreg_svc_gap():
    logging.debug("%s", core_unreg_svc_gap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['gap_unreg'])

    core_unreg_svc_rsp_succ()


def core_reg_svc_gatt():
    core_reg_svc_univ("gatt_reg", "GATT")


def core_unreg_svc_gatt():
    logging.debug("%s", core_unreg_svc_gatt.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gatt_unreg'])


def core_reg_svc_l2cap():
    core_reg_svc_univ("l2cap_reg", "L2CAP")


def core_unreg_svc_l2cap():
    logging.debug("%s", core_unreg_svc_l2cap.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['l2cap_unreg'])


def core_reg_svc_mesh():
    core_reg_svc_univ("mesh_reg", "MESH")


def core_unreg_svc_mesh():
    logging.debug("%s", core_unreg_svc_mesh.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mesh_unreg'])


def core_reg_svc_mmdl():
    core_reg_svc_univ("mmdl_reg", "MESH_MMDL")


def core_unreg_svc_mmdl():
    logging.debug("%s", core_unreg_svc_mmdl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['mmdl_unreg'])


def core_reg_svc_gatt_cl():
    core_reg_svc_univ("gatt_cl_reg", "GATT_CL")


def core_unreg_svc_gatt_cl():
    logging.debug("%s", core_unreg_svc_gatt_cl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*CORE['gatt_cl_unreg'])


def core_reg_svc_vcs():
    core_reg_svc_univ("vcs_reg", "VCS")

def core_reg_svc_vocs():
    core_reg_svc_univ("vocs_reg", "VOCS")


def core_reg_svc_aics():
    core_reg_svc_univ("aics_reg", "AICS")


def core_reg_svc_ias():
    core_reg_svc_univ("ias_reg", "")


def core_reg_svc_pacs():
    core_reg_svc_univ("pacs_reg", "PACS")


def core_reg_svc_ascs():
    core_reg_svc_univ("ascs_reg", "ASCS")


def core_reg_svc_has():
    core_reg_svc_univ("has_reg", "HAS")


def core_reg_svc_bap():
    core_reg_svc_univ("bap_reg", "BAP")


def core_reg_svc_csis():
    core_reg_svc_univ("csis_reg", "CSIS")


def core_reg_svc_micp():
    core_reg_svc_univ("micp_reg", "MICP")


def core_reg_svc_mics():
    core_reg_svc_univ("mics_reg", "MICS")


def core_reg_svc_ccp():
    core_reg_svc_univ("ccp_reg", "CCP")

    
def core_reg_svc_cas():
    core_reg_svc_univ("cas_reg", "CAS")


def core_reg_svc_vcp():
    core_reg_svc_univ("vcp_reg", "VCP")


def core_reg_svc_mcp():
    core_reg_svc_univ("mcp_reg", "MCP")


def core_reg_svc_gmcs():
    core_reg_svc_univ("gmcs_reg", "GMCS")


def core_reg_svc_hap():
    core_reg_svc_univ("hap_reg", "HAP")


def core_reg_svc_cap():
    core_reg_svc_univ("cap_reg", "CAP")


def core_reg_svc_csip():
    core_reg_svc_univ("csip_reg", "CSIP")


def core_reg_svc_tmap():
    core_reg_svc_univ("tmap_reg", "TMAP")
    

def core_reg_svc_tbs():
    core_reg_svc_univ("tbs_reg", "TBS")


def core_reg_svc_ots():
    core_reg_svc_univ("ots_reg", "OTS")


def core_reg_svc_pbp():
    core_reg_svc_univ("pbp_reg", "PBP")


# GENERATOR append 1

def core_reg_svc_rsp_succ(service_name):
    logging.debug("%s", core_reg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.BTP_CORE_CMD_REGISTER_SERVICE,
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
    service_name = service_name.strip()
    if service_name:
        logging.debug("Reading supported commands for service: %s", service_name)
        try:
            read_supported_commands(service_name)
        except Exception as e:
            logging.warning("No read supported commands for %s: %s", service_name, e)


def core_unreg_svc_rsp_succ():
    logging.debug("%s", core_unreg_svc_rsp_succ.__name__)
    iutctl = get_iut()

    expected_frame = ((defs.BTP_SERVICE_ID_CORE,
                       defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
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

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_LOG_MESSAGE)


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
    set_event_handler(event_handler)


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
from .tbs import TBS_EV
from .tmap import TMAP_EV
from .ots import OTS_EV
from .pbp import PBP_EV
# GENERATOR append 2

from autopts.pybtp.iutctl_common import set_event_handler


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
        defs.BTP_SERVICE_ID_TBS: (TBS_EV, stack.tbs),
        defs.BTP_SERVICE_ID_TMAP: (TMAP_EV, stack.tmap),
        defs.BTP_SERVICE_ID_OTS: (OTS_EV, stack.ots),
        defs.BTP_SERVICE_ID_PBP: (PBP_EV, stack.pbp),
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
