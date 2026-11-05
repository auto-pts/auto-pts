#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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
import copy
import logging
import random
import re
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import defs
from autopts.pybtp.btp import btp
from autopts.pybtp.types import WIDParams, UUID, uuid_to_le_hex_str, AdType, AdFlags, gap_settings_btp2txt

log = logging.debug


CS_ROLE_INITIATOR = 0
CS_ROLE_REFLECTOR = 1


def rap_wid_hdl(wid, description, test_case_name):
    log(f'{rap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    from autopts.wid import generic_wid_hdl
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def disc_full(svc_uuid=None, ch_uuid=None):
    attrs = {}
    bd_addr = btp.pts_addr_get()
    bd_addr_type = btp.pts_addr_type_get()
    stack = get_stack()

    if svc_uuid:
        btp.gatt_cl_disc_prim_uuid(bd_addr_type, bd_addr, svc_uuid)
        stack.gatt_cl.wait_for_prim_svcs()
    else:
        btp.gatt_cl_disc_all_prim(bd_addr_type, bd_addr)
        stack.gatt_cl.wait_for_prim_svcs()

    if not stack.gatt_cl.prim_svcs:
        return attrs

    for svc in stack.gatt_cl.prim_svcs:
        attrs[svc] = {}
        start_handle, end_handle, uuid = svc

        if ch_uuid:
            btp.gatt_cl_disc_chrc_uuid(bd_addr_type, bd_addr, start_handle, end_handle, ch_uuid)
            stack.gatt_cl.wait_for_chrcs()
        else:
            btp.gatt_cl_disc_all_chrc(bd_addr_type, bd_addr, start_handle, end_handle)
            stack.gatt_cl.wait_for_chrcs()

        if not stack.gatt_cl.chrcs:
            continue

        for i in range(0, len(stack.gatt_cl.chrcs)):
            chrc = stack.gatt_cl.chrcs[i]
            value_handle, uuid = chrc
            start_hdl = value_handle + 1
            value_handle = f'{value_handle:04X}'.upper()

            btp.gatt_cl_disc_all_desc(btp.pts_addr_type_get(),
                                      btp.pts_addr_get(),
                                      start_hdl, start_hdl + 1)

            stack.gatt_cl.wait_for_descs()
            attrs[svc][(value_handle, uuid)] = copy.deepcopy(stack.gatt_cl.dscs)

    log(attrs)

    stack.gatt_cl.last_full_disc_attrs = attrs

    return attrs


def hdl_wid_1(params: WIDParams):
    """Waiting for Ranging Data Ready message. (Please induce IUT to generate Ranging Data)"""

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    btp.rap_start_ranging(0, CS_ROLE_REFLECTOR, addr_type, addr)

    config_id = 0
    start_acl_conn_event_counter = 1234
    procedure_counter = 0
    frequency_compensation = 0xC000  # Frequency compensation value is not available, or the role is not initiator
    reference_power_level = 0x00  # Reference power level is not applicable
    # procedure_done_status = 0x1  # Partial results with more to follow for the CS procedure
    procedure_done_status = 0x0  # All results complete for the CS procedure
    subevent_done_status = 0x0  # All results complete for the CS subevent
    abort_reason = 0x0  # Report with no abort
    num_antenna_paths = 0x1
    num_steps_reported = 8
    data = struct.pack('B', config_id)
    data += struct.pack('<H', start_acl_conn_event_counter)
    data += struct.pack('<H', procedure_counter)
    data += struct.pack('<H', frequency_compensation)
    data += struct.pack('B', reference_power_level)
    data += struct.pack('B', procedure_done_status)
    data += struct.pack('B', subevent_done_status)
    data += struct.pack('B', abort_reason)
    data += struct.pack('B', num_antenna_paths)
    data += struct.pack('B', num_steps_reported)

    excluded = {0, 1, 23, 24, 25, 77, 78, 79}
    allowed_channels = [ch for ch in range(80) if ch not in excluded]

    for i in range(3):
        step_mode = 0x00
        step_channel = random.choice(allowed_channels)
        packet_quality = 0x00
        packet_rssi = 0x00
        packet_antenna = 0x01
        data += struct.pack('B', step_mode)
        data += struct.pack('B', step_channel)
        data += struct.pack('B', 3)  # Step data len
        data += struct.pack('B', packet_quality)
        data += struct.pack('B', packet_rssi)
        data += struct.pack('B', packet_antenna)

    pct_bits = 24
    pct_min_value = -(1 << (pct_bits - 1))
    pct_max_value = (1 << (pct_bits - 1)) - 1

    for i in range(5):
        step_mode = 0x02
        step_channel = random.choice(allowed_channels)
        antenna_permutation_index = 0x00
        tone_pct = random.randint(pct_min_value, pct_max_value)
        tone_quality_ind = 0x00
        data += struct.pack('B', step_mode)
        data += struct.pack('B', step_channel)
        data += struct.pack('B', 9)  # Step data len
        data += struct.pack('B', antenna_permutation_index)
        data += tone_pct.to_bytes(3, "little", signed=True)
        data += struct.pack('B', tone_quality_ind)
        data += tone_pct.to_bytes(3, "little", signed=True)  # Ext tone
        data += struct.pack('B', tone_quality_ind)

    btp.rap_set_test_cs_subevent_data(data, addr_type, addr)

    return True


def hdl_wid_3(params: WIDParams):
    """Waiting for On-Demand Ranging Data and sending data completed."""

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
        # remove_ev = False
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()
    remove_ev = True

    stack = get_stack()
    stack.rap.wait_ranging_complete_ev(addr_type, addr, 10, remove=remove_ev)

    return True


def hdl_wid_8(params: WIDParams):
    """Waiting for Real-Time Ranging Data to receive and store completed."""

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    btp.rap_start_ranging(0, CS_ROLE_REFLECTOR, addr_type, addr)

    config_id = 0
    start_acl_conn_event_counter = 1234
    procedure_counter = 0
    frequency_compensation = 0xC000  # Frequency compensation value is not available, or the role is not initiator
    reference_power_level = 0x00  # Reference power level is not applicable
    # procedure_done_status = 0x1  # Partial results with more to follow for the CS procedure
    procedure_done_status = 0x0  # All results complete for the CS procedure
    subevent_done_status = 0x0  # All results complete for the CS subevent
    abort_reason = 0x0  # Report with no abort
    num_antenna_paths = 0x1
    num_steps_reported = 8
    data = struct.pack('B', config_id)
    data += struct.pack('<H', start_acl_conn_event_counter)
    data += struct.pack('<H', procedure_counter)
    data += struct.pack('<H', frequency_compensation)
    data += struct.pack('B', reference_power_level)
    data += struct.pack('B', procedure_done_status)
    data += struct.pack('B', subevent_done_status)
    data += struct.pack('B', abort_reason)
    data += struct.pack('B', num_antenna_paths)
    data += struct.pack('B', num_steps_reported)

    excluded = {0, 1, 23, 24, 25, 77, 78, 79}
    allowed_channels = [ch for ch in range(80) if ch not in excluded]

    for i in range(3):
        step_mode = 0x00
        step_channel = random.choice(allowed_channels)
        packet_quality = 0x00
        packet_rssi = 0x00
        packet_antenna = 0x01
        data += struct.pack('B', step_mode)
        data += struct.pack('B', step_channel)
        data += struct.pack('B', 3)  # Step data len
        data += struct.pack('B', packet_quality)
        data += struct.pack('B', packet_rssi)
        data += struct.pack('B', packet_antenna)

    pct_bits = 24
    pct_min_value = -(1 << (pct_bits - 1))
    pct_max_value = (1 << (pct_bits - 1)) - 1

    for i in range(5):
        step_mode = 0x02
        step_channel = random.choice(allowed_channels)
        antenna_permutation_index = 0x00
        tone_pct = random.randint(pct_min_value, pct_max_value)
        tone_quality_ind = 0x00
        data += struct.pack('B', step_mode)
        data += struct.pack('B', step_channel)
        data += struct.pack('B', 9)  # Step data len
        data += struct.pack('B', antenna_permutation_index)
        data += tone_pct.to_bytes(3, "little", signed=True)
        data += struct.pack('B', tone_quality_ind)
        data += tone_pct.to_bytes(3, "little", signed=True)  # Ext tone
        data += struct.pack('B', tone_quality_ind)

    btp.rap_set_test_cs_subevent_data(data, addr_type, addr)

    stack = get_stack()
    stack.rap.wait_ranging_complete_ev(addr_type, addr, 10)

    return True


def hdl_wid_28(params: WIDParams):
    """Click OK when LT2 finished test case."""

    addr_type = btp.lt2_addr_type_get()
    addr = btp.lt2_addr_get()

    stack = get_stack()
    stack.rap.wait_ranging_complete_ev(addr_type, addr, 10, remove=True)

    return True


def hdl_wid_1000(params: WIDParams):
    """Please have IUT enter GAP Discoverable Mode and generate Advertising Packets."""
    stack = get_stack()

    ad = {
        AdType.name_full: stack.gap.name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: uuid_to_le_hex_str(UUID.RAS),
    }

    btp.gap_set_extended_advertising_on()
    btp.gap_start_advertising(ad=ad)

    return True


def hdl_wid_20001(params: WIDParams):
    """Please prepare IUT into a connectable mode.
    Description: Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.
    """
    stack = get_stack()

    if 'LT2' in params.test_case_name:
        addr_type = btp.lt2_addr_type_get()
        addr = btp.lt2_addr_get()
    else:
        addr_type = btp.pts_addr_type_get()
        addr = btp.pts_addr_get()

    ad = {
        AdType.name_full: stack.gap.name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: uuid_to_le_hex_str(UUID.RAS),
    }

    btp.gap_set_connectable()
    btp.gap_set_non_discoverable()
    btp.gap_start_advertising(ad=ad)

    stack.gap.wait_for_connection(timeout=10, addr=addr)

    if not stack.gap.is_connected():
        return False

    return True


def hdl_wid_20100(params: WIDParams):
    """MMI:  Please initiate a GATT connection to the PTS...Description: Verify that
     the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    stack = get_stack()

    addr_type = btp.pts_addr_type_get()
    addr = btp.pts_addr_get()

    btp.gap_connect(addr, addr_type)

    stack.gap.wait_for_connection(timeout=10, addr=addr)

    if not stack.gap.is_connected():
        return False

    return True


def hdl_wid_20103(params: WIDParams):
    """
    Please take action to discover the RAS Features characteristic from the Ranging.
    Discover the primary service if needed.
    Description: Verify that the Implementation Under Test (IUT) can send Discover All Characteristics command.
    """
    disc_full(svc_uuid=UUID.RAS)

    return True


def hdl_wid_20107(params: WIDParams):
    """Please send Read Request to read RAS Features characteristic with handle = 0xXXXX."""

    MMI.reset()
    MMI.parse_description(params.description)
    handle = MMI.args[0]
    stack = get_stack()

    btp.gatt_cl_read(btp.pts_addr_type_get(), btp.pts_addr_get(), handle)
    stack.gatt_cl.wait_for_read()

    return True


def hdl_wid_20116(params: WIDParams):
    """MMI:  Please send command to the PTS to discover all mandatory characteristics of
    the Ranging supported by the IUT. Discover primary service if needed...
    """
    disc_full(svc_uuid=UUID.RAS)

    return True


def hdl_wid_20206(params: WIDParams):
    """Please verify that for each supported characteristic, attribute handle/UUID pair(s)
     is returned to the upper tester.
    """

    stack = get_stack()
    attrs = stack.gatt_cl.last_full_disc_attrs

    service = None
    for service in attrs:
        _, _, svc_uuid = service
        if svc_uuid.upper() == UUID.RAS.upper():
            break

    if service is None:
        return False

    expected = {
        (chrc_handle, chrc_uuid.upper())
        for chrc_handle, chrc_uuid in re.findall(
            r"Handle\s*=\s*0x([0-9A-F]+)\s*UUID\s*=\s*0x([0-9A-F]+)",
            params.description,
            flags=re.MULTILINE,
        )
    }

    actual = set(attrs[service].keys())

    return expected == actual
