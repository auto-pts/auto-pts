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

from ptsprojects.stack import get_stack
from pybtp import defs
from pybtp.types import BTPError

#  get IUT global method from iutctl
get_iut = None

# Address
LeAddress = namedtuple('LeAddress', 'addr_type addr')
PTS_BD_ADDR = LeAddress(addr_type=0, addr='000000000000')

# Devices found
LeAdv = namedtuple('LeAdv', 'addr_type addr rssi flags eir')

CONTROLLER_INDEX = 0

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
    "read_supp_cmds": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "read_supp_svcs": (defs.BTP_SERVICE_ID_CORE,
                       defs.CORE_READ_SUPPORTED_SERVICES,
                       defs.BTP_INDEX_NONE, ""),
    "log_message": (defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE,
                    defs.BTP_INDEX_NONE),
}


def clear_verify_values():
    stack = get_stack()
    stack.gatt.verify_values = []


def add_to_verify_values(item):
    stack = get_stack()
    stack.gatt.verify_values.append(item)


def get_verify_values():
    stack = get_stack()
    return stack.gatt.verify_values


def extend_verify_values(item):
    stack = get_stack()
    stack.gatt.verify_values.extend(item)


def verify_description(description):
    """A function to verify that values are in PTS MMI description

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description = description.upper()

    verify_values = get_verify_values()

    logging.debug("Verifying values: %r", verify_values)

    if not verify_values:
        return True

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    for value in verify_values:
        logging.debug("Verifying: %r", value)

        value = value.upper()

        try:
            if value not in description:
                logging.debug("Verification failed, value not in description")
                return False
        except TypeError:
            logging.debug("Value under verification is not string")

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

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    if not verify_values:
        return True

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"
    exp_mtp_read = ""
    for value in verify_values:
        try:
            exp_mtp_read = exp_mtp_read.join(value)
        except TypeError:
            value = value.decode("utf-8")
            exp_mtp_read = exp_mtp_read.join(value)

    got_mtp_read = "".join(re.findall(r"\b[0-9A-Fa-f]+\b", description))

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

    message_data = bytearray(message)
    data = bytearray(struct.pack('H', len(message_data)))
    data.extend(message_data)

    iutctl = get_iut()
    iutctl.btp_socket.send(*CORE['log_message'], data=data)

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_CORE, defs.CORE_LOG_MESSAGE)


def btp2uuid(uuid_len, uu):
    if uuid_len == 2:
        (uu,) = struct.unpack("H", uu)
        return format(uu, 'x').upper()
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
from pybtp.iutctl_common import set_event_handler


def event_handler(hdr, data):
    logging.debug("%s %r %r", event_handler.__name__, hdr, data)

    stack = get_stack()
    if not stack:
        logging.info("Stack not initialized")
        return False

    if hdr.svc_id == defs.BTP_SERVICE_ID_MESH:
        if hdr.op in MESH_EV and stack.mesh:
            cb = MESH_EV[hdr.op]
            cb(stack.mesh, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_L2CAP:
        if hdr.op in L2CAP_EV and stack.l2cap:
            cb = L2CAP_EV[hdr.op]
            cb(stack.l2cap, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_GAP:
        if hdr.op in GAP_EV and stack.gap:
            cb = GAP_EV[hdr.op]
            cb(stack.gap, data[0], hdr.data_len)
            return True

    elif hdr.svc_id == defs.BTP_SERVICE_ID_GATT:
        if hdr.op in GATT_EV and stack.gatt:
            cb = GATT_EV[hdr.op]
            cb(stack.gatt, data[0], hdr.data_len)
            return True

    # TODO: Raise BTP error instead of logging
    logging.error("Unhandled event! svc_id %s op %s", hdr.svc_id, hdr.op)
    return False
