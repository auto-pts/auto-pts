#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

"""BASS test cases"""

from queue import Queue

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import SynchPoint, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.pybtp.btp import lt2_addr_get
from autopts.pybtp.types import UUID, Addr, AdFlags, AdType

broadcast_code = '0102680553F1415AA265BBAFC6EA03B8'
bass_wid_hdl = get_wid_handler("zephyr", "bass")


def set_pixits(ptses):
    """Setup BASS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("BASS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("BASS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("BASS", "TSPX_time_guard", "180000")
    pts.set_pixit("BASS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("BASS", "TSPX_mtu_size", "64")
    pts.set_pixit("BASS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("BASS", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("BASS", "TSPX_pin_code", "0000")
    pts.set_pixit("BASS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("BASS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("BASS", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("BASS", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("BASS", "TSPX_broadcast_code", broadcast_code)
    pts.set_pixit("BASS", "TSPX_Sync_Timeout", "8000")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]
    pts2.set_pixit("BASS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("BASS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("BASS", "TSPX_time_guard", "180000")
    pts2.set_pixit("BASS", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("BASS", "TSPX_mtu_size", "64")
    pts2.set_pixit("BASS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts2.set_pixit("BASS", "TSPX_delete_link_key", "FALSE")
    pts2.set_pixit("BASS", "TSPX_pin_code", "0000")
    pts2.set_pixit("BASS", "TSPX_use_dynamic_pin", "FALSE")
    pts2.set_pixit("BASS", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("BASS", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("BASS", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts2.set_pixit("BASS", "TSPX_broadcast_code", broadcast_code)
    pts.set_pixit("BASS", "TSPX_Sync_Timeout", "8000")


def test_cases(ptses):
    """Returns a list of BASS Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # The Unicast Server shall transmit connectable extended advertising PDUs
    # that contain the Service Data AD data type, including additional
    # service data defined in BAP_v1.0.1, 3.5.3, Table 3.7.
    ad = {
        AdType.name_full: iut_device_name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: bytes.fromhex(UUID.ASCS)[::-1].hex(),
        AdType.uuid16_svc_data: '4e1801ff0fff0f00',
    }

    queue = Queue()

    def set_addr(addr):
        # LT2 awaits the address before starting preconditions
        queue.put(addr)

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BASS", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
                      TestFunc(stack.gatt_init),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.gap_set_gendiscov),
                      TestFunc(btp.core_reg_svc_pacs),
                      TestFunc(btp.core_reg_svc_ascs),
                      TestFunc(btp.core_reg_svc_bap),
                      TestFunc(stack.ascs_init),
                      TestFunc(stack.bap_init),
                      TestFunc(lambda: stack.bap.set_broadcast_code(broadcast_code)),
                      TestFunc(btp.bap_broadcast_sink_setup),
                      TestFunc(lambda: set_addr(
                          stack.gap.iut_addr_get_str())),
                      ]

    custom_test_cases = [
        ZTestCase("BASS", "BASS/SR/CP/BV-10-C", cmds=pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("BASS", "TSPX_Public_bd_addr_LT2", lt2_addr_get())),],
                  generic_wid_hdl=bass_wid_hdl,
                  lt2="BASS/SR/CP/BV-10-C_LT2"),
        ZTestCase("BASS", "BASS/SR/CP/BV-11-C", cmds=pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("BASS", "TSPX_Public_bd_addr_LT2", lt2_addr_get())),],
                  generic_wid_hdl=bass_wid_hdl,
                  lt2="BASS/SR/CP/BV-11-C_LT2"),
    ]

    test_case_name_list = pts.get_test_case_list('BASS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("BASS", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=bass_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
        TestFunc(lambda: pts2.update_pixit_param(
                        "BASS", "TSPX_bd_addr_iut", queue.get())),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("BASS", "BASS/SR/CP/BV-10-C_LT2",
                       cmds=pre_conditions_lt2 + [
                           TestFunc(get_stack().synch.add_synch_element, [
                            SynchPoint("BASS/SR/CP/BV-10-C_LT2", 100),
                            SynchPoint("BASS/SR/CP/BV-10-C", 101)])],
                       generic_wid_hdl=bass_wid_hdl),
        ZTestCaseSlave("BASS", "BASS/SR/CP/BV-11-C_LT2",
                       cmds=pre_conditions_lt2 + [
                           TestFunc(get_stack().synch.add_synch_element, [
                            SynchPoint("BASS/SR/CP/BV-11-C_LT2", 100),
                            SynchPoint("BASS/SR/CP/BV-11-C", 101)])],
                       generic_wid_hdl=bass_wid_hdl),
    ]

    return tc_list + test_cases_lt2
