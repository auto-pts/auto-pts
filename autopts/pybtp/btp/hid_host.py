#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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

import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, btp_hdr_check, pts_addr_get, pts_addr_type_get
from autopts.pybtp.btp.btp import get_iut_method as get_iut
from autopts.pybtp.btp.gap import gap_wait_for_connection
from autopts.pybtp.types import addr_str_to_le_bytes, le_bytes_to_hex_str

HID_HOST = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_HID_HOST,
                       defs.BTP_HID_HOST_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "register": (defs.BTP_SERVICE_ID_HID_HOST,
                 defs.BTP_HID_HOST_CMD_REGISTER,
                 CONTROLLER_INDEX),
    "unregister": (defs.BTP_SERVICE_ID_HID_HOST,
                   defs.BTP_HID_HOST_CMD_UNREGISTER,
                   CONTROLLER_INDEX),
    "connect": (defs.BTP_SERVICE_ID_HID_HOST,
                defs.BTP_HID_HOST_CMD_CONNECT,
                CONTROLLER_INDEX),
    "disconnect": (defs.BTP_SERVICE_ID_HID_HOST,
                   defs.BTP_HID_HOST_CMD_DISCONNECT,
                   CONTROLLER_INDEX),
    "get_report": (defs.BTP_SERVICE_ID_HID_HOST,
                   defs.BTP_HID_HOST_CMD_GET_REPORT,
                   CONTROLLER_INDEX),
    "set_report": (defs.BTP_SERVICE_ID_HID_HOST,
                   defs.BTP_HID_HOST_CMD_SET_REPORT,
                   CONTROLLER_INDEX),
    "get_protocol": (defs.BTP_SERVICE_ID_HID_HOST,
                     defs.BTP_HID_HOST_CMD_GET_PROTOCOL,
                     CONTROLLER_INDEX),
    "set_protocol": (defs.BTP_SERVICE_ID_HID_HOST,
                     defs.BTP_HID_HOST_CMD_SET_PROTOCOL,
                     CONTROLLER_INDEX),
    "send_output_report": (defs.BTP_SERVICE_ID_HID_HOST,
                           defs.BTP_HID_HOST_CMD_SEND_OUTPUT_REPORT,
                           CONTROLLER_INDEX),
    "suspend": (defs.BTP_SERVICE_ID_HID_HOST,
                defs.BTP_HID_HOST_CMD_SUSPEND,
                CONTROLLER_INDEX),
    "exit_suspend": (defs.BTP_SERVICE_ID_HID_HOST,
                     defs.BTP_HID_HOST_CMD_EXIT_SUSPEND,
                     CONTROLLER_INDEX),
    "virtual_cable_unplug": (defs.BTP_SERVICE_ID_HID_HOST,
                             defs.BTP_HID_HOST_CMD_VIRTUAL_CABLE_UNPLUG,
                             CONTROLLER_INDEX),
    "sniff_subrating": (defs.BTP_SERVICE_ID_HID_HOST,
                        defs.BTP_HID_HOST_CMD_SNIFF_SUBRATING,
                        CONTROLLER_INDEX),
}


def hid_host_command_rsp_succ(op=None):
    logging.debug("%s", hid_host_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_HID_HOST, op)


def hid_host_register():
    """Register the HID Host so it accepts/initiates HID connections."""
    logging.debug("%s", hid_host_register.__name__)

    data = bytearray([0x00])  # unused byte

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['register'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_REGISTER)


def hid_host_unregister():
    """Unregister the HID Host."""
    logging.debug("%s", hid_host_unregister.__name__)

    data = bytearray([0x00])  # unused byte

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['unregister'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_UNREGISTER)


def hid_host_connect(bd_addr_type=None, bd_addr=None):
    """Establish a HID Host connection to the remote HID Device."""
    logging.debug("%s %r %r", hid_host_connect.__name__, bd_addr_type, bd_addr)

    if bd_addr_type is None:
        bd_addr_type = pts_addr_type_get()
    if bd_addr is None:
        bd_addr = pts_addr_get()

    gap_wait_for_connection()

    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    data.extend([bd_addr_type])
    data.extend(bd_addr_ba)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['connect'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_CONNECT)


def hid_host_disconnect(bd_addr_type=None, bd_addr=None):
    """Disconnect the HID Host connection from the remote HID Device."""
    logging.debug("%s %r %r", hid_host_disconnect.__name__, bd_addr_type, bd_addr)

    if bd_addr_type is None:
        bd_addr_type = pts_addr_type_get()
    if bd_addr is None:
        bd_addr = pts_addr_get()

    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    data.extend([bd_addr_type])
    data.extend(bd_addr_ba)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['disconnect'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_DISCONNECT)


def hid_host_get_report(report_type, report_id, buffer_size=0):
    """Send a GET_REPORT request to the connected HID Device.

    :param report_type: HID report type (input/output/feature)
    :param report_id: HID report id
    :param buffer_size: max response buffer size (0 for default)
    """
    logging.debug("%s report_type=%d report_id=%d",
                  hid_host_get_report.__name__, report_type, report_id)

    # Drop any response cached by an earlier transaction so a following
    # wait_for_get_report() blocks for THIS request instead of returning
    # immediately on the stale value.
    get_stack().hid_host.clear_get_report()

    data = bytearray()

    data.extend(struct.pack('B', report_type))
    data.extend(struct.pack('B', report_id))
    data.extend(struct.pack('H', buffer_size))

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['get_report'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_GET_REPORT)


def hid_host_set_report(report_type, report):
    """Send a SET_REPORT request to the connected HID Device.

    :param report_type: HID report type (input/output/feature)
    :param report: bytes/bytearray with the report payload
    """
    logging.debug("%s report_type=%d", hid_host_set_report.__name__, report_type)

    # Drop the previous transaction result so wait_for_set_report() blocks
    # for the response to THIS request.
    get_stack().hid_host.clear_set_report()

    report = bytearray(report)

    data = bytearray()
    data.extend(struct.pack('B', report_type))
    data.extend(struct.pack('H', len(report)))
    data.extend(report)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['set_report'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_SET_REPORT)


def hid_host_get_protocol():
    """Send a GET_PROTOCOL request to the connected HID Device."""
    logging.debug("%s", hid_host_get_protocol.__name__)

    # Drop the previous transaction result so wait_for_get_protocol() blocks
    # for the response to THIS request.
    get_stack().hid_host.clear_get_protocol()

    data = bytearray([0x00])  # unused byte

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['get_protocol'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_GET_PROTOCOL)


def hid_host_set_protocol(protocol):
    """Send a SET_PROTOCOL request to the connected HID Device.

    :param protocol: BTP_HID_HOST_PROTOCOL_BOOT_MODE or REPORT_MODE
    """
    logging.debug("%s protocol=%d", hid_host_set_protocol.__name__, protocol)

    # Drop the previous transaction result so wait_for_set_protocol() blocks
    # for the response to THIS request. Without this, a toggle sequence such
    # as SET_PROTOCOL(REPORT) followed by SET_PROTOCOL(BOOT) lets the second
    # wait return instantly on the first result, and the next BTP command is
    # issued while the control channel transaction is still outstanding.
    get_stack().hid_host.clear_set_protocol()

    data = bytearray()
    data.extend(struct.pack('B', protocol))

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['set_protocol'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_SET_PROTOCOL)


def hid_host_send_output_report(report):
    """Send an interrupt-channel output report to the connected HID Device.

    :param report: bytes/bytearray with the report payload
    """
    logging.debug("%s", hid_host_send_output_report.__name__)

    # Drop the previously received input report so a following
    # wait_for_input_report() blocks for a new one.
    get_stack().hid_host.clear_input_report()

    report = bytearray(report)

    data = bytearray()
    data.extend(struct.pack('H', len(report)))
    data.extend(report)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['send_output_report'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_SEND_OUTPUT_REPORT)


def hid_host_suspend():
    """Send a SUSPEND control operation to the connected HID Device."""
    logging.debug("%s", hid_host_suspend.__name__)

    data = bytearray([0x00])  # unused byte

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['suspend'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_SUSPEND)


def hid_host_exit_suspend():
    """Send an EXIT_SUSPEND control operation to the connected HID Device."""
    logging.debug("%s", hid_host_exit_suspend.__name__)

    data = bytearray([0x00])  # unused byte

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['exit_suspend'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_EXIT_SUSPEND)


def hid_host_virtual_cable_unplug(bd_addr_type=None, bd_addr=None):
    """Send a HID Virtual Cable Unplug to the connected HID Device."""
    logging.debug("%s %r %r", hid_host_virtual_cable_unplug.__name__,
                  bd_addr_type, bd_addr)

    if bd_addr_type is None:
        bd_addr_type = pts_addr_type_get()
    if bd_addr is None:
        bd_addr = pts_addr_get()

    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    data.extend([bd_addr_type])
    data.extend(bd_addr_ba)

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['virtual_cable_unplug'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_VIRTUAL_CABLE_UNPLUG)


def hid_host_sniff_subrating(max_latency, min_remote_timeout, min_local_timeout,
                             bd_addr_type=None, bd_addr=None):
    """Request BR/EDR sniff subrating on the ACL link to the peer.

    All three timing parameters are in baseband slots of 0.625 ms and are
    passed straight to HCI_Sniff_Subrating by the IUT.
    """
    logging.debug("%s %r %r %r %r %r", hid_host_sniff_subrating.__name__,
                  max_latency, min_remote_timeout, min_local_timeout,
                  bd_addr_type, bd_addr)

    if bd_addr_type is None:
        # BR/EDR-only command: pts_addr_type_get() would hand back the LE
        # address type and the tester would reject the request.
        bd_addr_type = defs.BTP_BR_ADDRESS_TYPE
    if bd_addr is None:
        bd_addr = pts_addr_get()

    data = bytearray()
    bd_addr_ba = addr_str_to_le_bytes(bd_addr)
    data.extend([bd_addr_type])
    data.extend(bd_addr_ba)
    data.extend(struct.pack('<HHH', max_latency, min_remote_timeout,
                            min_local_timeout))

    iutctl = get_iut()
    iutctl.btp_socket.send(*HID_HOST['sniff_subrating'], data=data)

    hid_host_command_rsp_succ(defs.BTP_HID_HOST_CMD_SNIFF_SUBRATING)


def hid_host_ev_connected(hid_host, data, data_len):
    """Decode HID Host Connected Event.

    BTP HID Host Connected Event format:
    0        6
    +--------+
    | Addr   |
    | (6B)   |
    +--------+
    """
    logging.debug("%s %r", hid_host_ev_connected.__name__, data)

    fmt = '<6s'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for HID Host Connected Event")

    (addr,) = struct.unpack(fmt, data)
    addr = le_bytes_to_hex_str(addr).upper()

    logging.debug("HID Host Connected: addr=%s", addr)

    hid_host.set_connected(addr)
    return True


def hid_host_ev_disconnected(hid_host, data, data_len):
    """Decode HID Host Disconnected Event.

    BTP HID Host Disconnected Event format:
    0        6
    +--------+
    | Addr   |
    | (6B)   |
    +--------+
    """
    logging.debug("%s %r", hid_host_ev_disconnected.__name__, data)

    fmt = '<6s'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for HID Host Disconnected Event")

    (addr,) = struct.unpack(fmt, data)
    addr = le_bytes_to_hex_str(addr).upper()

    logging.debug("HID Host Disconnected: addr=%s", addr)

    hid_host.set_disconnected(addr)
    return True


def hid_host_ev_input_report(hid_host, data, data_len):
    """Decode HID Host Input Report Event.

    BTP HID Host Input Report Event format:
    0          2
    +----------+---------------+
    | DataLen  | Data          |
    | (2B)     | (DataLen B)   |
    +----------+---------------+
    """
    logging.debug("%s %r", hid_host_ev_input_report.__name__, data)

    fmt = '<H'
    hdr_len = struct.calcsize(fmt)
    if len(data) < hdr_len:
        raise ValueError("Invalid data length for HID Host Input Report Event")

    (report_len,) = struct.unpack_from(fmt, data)
    report = bytes(data[hdr_len:hdr_len + report_len])

    logging.debug("HID Host Input Report: len=%d data=%r", report_len, report)

    hid_host.set_input_report(report)
    return True


def hid_host_ev_get_report(hid_host, data, data_len):
    """Decode HID Host Get Report Event.

    BTP HID Host Get Report Event format:
    0            1            2          4
    +------------+------------+----------+---------------+
    | ResultCode | ReportType | DataLen  | Data          |
    | (1B)       | (1B)       | (2B)     | (DataLen B)   |
    +------------+------------+----------+---------------+
    """
    logging.debug("%s %r", hid_host_ev_get_report.__name__, data)

    fmt = '<BBH'
    hdr_len = struct.calcsize(fmt)
    if len(data) < hdr_len:
        raise ValueError("Invalid data length for HID Host Get Report Event")

    result_code, report_type, report_len = struct.unpack_from(fmt, data)
    report = bytes(data[hdr_len:hdr_len + report_len])

    logging.debug("HID Host Get Report: result=%d type=%d len=%d data=%r",
                  result_code, report_type, report_len, report)

    hid_host.set_get_report(result_code, report_type, report)
    return True


def hid_host_ev_set_report(hid_host, data, data_len):
    """Decode HID Host Set Report Event.

    BTP HID Host Set Report Event format:
    0            1
    +------------+
    | ResultCode |
    | (1B)       |
    +------------+
    """
    logging.debug("%s %r", hid_host_ev_set_report.__name__, data)

    fmt = '<B'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for HID Host Set Report Event")

    (result_code,) = struct.unpack(fmt, data)

    logging.debug("HID Host Set Report: result=%d", result_code)

    hid_host.set_set_report(result_code)
    return True


def hid_host_ev_get_protocol(hid_host, data, data_len):
    """Decode HID Host Get Protocol Event.

    BTP HID Host Get Protocol Event format:
    0            1            2
    +------------+------------+
    | ResultCode | Protocol   |
    | (1B)       | (1B)       |
    +------------+------------+
    """
    logging.debug("%s %r", hid_host_ev_get_protocol.__name__, data)

    fmt = '<BB'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for HID Host Get Protocol Event")

    result_code, protocol = struct.unpack(fmt, data)

    logging.debug("HID Host Get Protocol: result=%d protocol=%d",
                  result_code, protocol)

    hid_host.set_get_protocol(result_code, protocol)
    return True


def hid_host_ev_set_protocol(hid_host, data, data_len):
    """Decode HID Host Set Protocol Event.

    BTP HID Host Set Protocol Event format:
    0            1
    +------------+
    | ResultCode |
    | (1B)       |
    +------------+
    """
    logging.debug("%s %r", hid_host_ev_set_protocol.__name__, data)

    fmt = '<B'
    if len(data) != struct.calcsize(fmt):
        raise ValueError("Invalid data length for HID Host Set Protocol Event")

    (result_code,) = struct.unpack(fmt, data)

    logging.debug("HID Host Set Protocol: result=%d", result_code)

    hid_host.set_set_protocol(result_code)
    return True


HID_HOST_EV = {
    defs.BTP_HID_HOST_EV_CONNECTED: hid_host_ev_connected,
    defs.BTP_HID_HOST_EV_DISCONNECTED: hid_host_ev_disconnected,
    defs.BTP_HID_HOST_EV_INPUT_REPORT: hid_host_ev_input_report,
    defs.BTP_HID_HOST_EV_GET_REPORT: hid_host_ev_get_report,
    defs.BTP_HID_HOST_EV_SET_REPORT: hid_host_ev_set_report,
    defs.BTP_HID_HOST_EV_GET_PROTOCOL: hid_host_ev_get_protocol,
    defs.BTP_HID_HOST_EV_SET_PROTOCOL: hid_host_ev_set_protocol,
}
