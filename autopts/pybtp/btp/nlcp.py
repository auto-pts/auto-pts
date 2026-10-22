#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Nordic Semiconductor ASA.
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
import struct
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.types import BTPError

log = logging.debug


NLCP = {
    'read_supported_cmds': (defs.BTP_SERVICE_ID_NLCP,
                            defs.BTP_NLCP_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
    'exec_node_reset': (defs.BTP_SERVICE_ID_NLCP,
                        defs.BTP_NLCP_CMD_EXEC_NODE_RESET,
                        CONTROLLER_INDEX, ""),
    'read_identity_report': (defs.BTP_SERVICE_ID_NLCP,
                             defs.BTP_NLCP_CMD_READ_IDENTITY_REPORT,
                             CONTROLLER_INDEX, ""),
    'read_profile_elem_addr': (defs.BTP_SERVICE_ID_NLCP,
                               defs.BTP_NLCP_CMD_READ_PROFILE_ELEM_ADDR,
                               CONTROLLER_INDEX),
    'read_scene_number': (defs.BTP_SERVICE_ID_NLCP,
                          defs.BTP_NLCP_CMD_READ_SCENE_NUMBER,
                          CONTROLLER_INDEX, ""),
    'exec_scene_select': (defs.BTP_SERVICE_ID_NLCP,
                          defs.BTP_NLCP_CMD_EXEC_SCENE_SELECT,
                          CONTROLLER_INDEX),
    'exec_dimming_ctrl': (defs.BTP_SERVICE_ID_NLCP,
                          defs.BTP_NLCP_CMD_EXEC_DIMMING_CONTROL,
                          CONTROLLER_INDEX, ""),
}


def _nlcp_data_rsp(ret):
    return ret[0] if isinstance(ret, tuple) else ret


def _nlcp_data_unpack(name, fmt, rsp):
    if len(rsp) != struct.calcsize(fmt):
        raise BTPError(f"NLCP {name}: {len(rsp)} B, expected {struct.calcsize(fmt)}")
    return struct.unpack_from(fmt, rsp)


def nlcp_process_node_reset(await_dur_s=30.0, delay=0.2):
    """Reset the Node to the unprovisioned state, and wait the IUT ready event.

    The IUT transmits the IUT ready event after the response in both cases:
    the Node is reset, or the Node is not provisioned (nothing to reset).
    Raises BTPError if the IUT does not accept the request within await_dur_s.
    """
    logging.debug("%s", nlcp_process_node_reset.__name__)

    # Before starting transmitting of the reset request need to clean up the
    # queue to prevent false positives.
    ready_ev = get_stack().core.event_queues[defs.BTP_CORE_EV_IUT_READY]
    last_error = None

    iutctl = get_iut()

    timeout = time.monotonic() + await_dur_s
    while True:
        ready_ev.clear()
        try:
            iutctl.btp_socket.send_wait_rsp(*NLCP['exec_node_reset'])
            break
        except BTPError as error:
            # NOT_READY: the Mesh state is not restored yet, retry.
            last_error = error
        if time.monotonic() >= timeout:
            raise BTPError(f"NLCP: IUT is not ready for Node reset ({last_error})")
        time.sleep(delay)

    # No board reset via the probe: the IUT reports the completion by itself.
    iutctl.wait_iut_ready_event(reset=False)


def nlcp_read_identity_report(retries=20, delay=0.5):
    """Read the identity report, with base device information."""
    logging.debug("%s", nlcp_read_identity_report.__name__)

    iutctl = get_iut()

    for _ in range(retries):
        try:
            rsp = iutctl.btp_socket.send_wait_rsp(*NLCP['read_identity_report'])
            break
        except BTPError:
            time.sleep(delay)
    else:
        raise BTPError("NLCP: identity is not ready.")

    identity_fmt = '<16s'
    (uuid,) = _nlcp_data_unpack("identity", identity_fmt, _nlcp_data_rsp(rsp))

    logging.debug("NLCP identity: uuid=%s", uuid.hex())

    get_stack().nlcp.set_identity_report(uuid)


def nlcp_read_profile_elem_addr(profile_id):
    """Read the Unicast Address of the Element, which hosts the NLC Profile."""
    logging.debug("%s", nlcp_read_profile_elem_addr.__name__)

    iutctl = get_iut()
    ret = iutctl.btp_socket.send_wait_rsp(*NLCP['read_profile_elem_addr'],
                                          struct.pack('<H', profile_id))

    (elem_addr,) = _nlcp_data_unpack("Profile Element Address", '<H', _nlcp_data_rsp(ret))

    logging.debug("NLCP ID 0x%04x: Element Address 0x%04x", profile_id, elem_addr)

    return elem_addr


def nlcp_read_scene_number():
    """Request the Scene Number N from the IUT.

    In the BSSNLCP/SSD/SPEC/PUB/BV-01-C Test Case, PTS requests the IUT to
    recall the Scene Number 1 first, and then the Scene Number N.
    """
    logging.debug("%s", nlcp_read_scene_number.__name__)

    iutctl = get_iut()
    ret = iutctl.btp_socket.send_wait_rsp(*NLCP['read_scene_number'])

    (scene_number,) = _nlcp_data_unpack("Scene Number", '<H', _nlcp_data_rsp(ret))

    logging.debug("NLCP Scene Number N: %d", scene_number)

    return scene_number


def nlcp_exec_scene_select(scene_number):
    """Request the IUT to recall a Scene with the given Number.

    The IUT responds once the Scene is recalled.
    """
    logging.debug("%s %d", nlcp_exec_scene_select.__name__, scene_number)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*NLCP['exec_scene_select'],
                                    data=struct.pack('<H', scene_number))


def nlcp_exec_dimming_ctrl():
    """Request the IUT to perform the Dimming Control function.

    The IUT responds once the function is performed.
    """
    logging.debug("%s", nlcp_exec_dimming_ctrl.__name__)

    iutctl = get_iut()
    iutctl.btp_socket.send_wait_rsp(*NLCP['exec_dimming_ctrl'])


NLCP_EV = {}
