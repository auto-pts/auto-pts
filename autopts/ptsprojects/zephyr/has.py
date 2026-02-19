#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

"""HAS test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.defs import (
    HAS_TSPX_available_presets_indices,
    HAS_TSPX_unavailable_presets_indices,
    HAS_TSPX_unwritable_preset_indices,
    HAS_TSPX_writable_preset_indices,
)
from autopts.pybtp.types import Addr
from autopts.wid.has import PresetProperty

has_wid_hdl = get_wid_handler("zephyr", "has")


def set_pixits(ptses):
    """Setup HAS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    available_presets_str = ','.join(str(_) for _ in HAS_TSPX_available_presets_indices)
    unavailable_presets_str = ','.join(str(_) for _ in HAS_TSPX_unavailable_presets_indices)
    writable_presets_str = ','.join(str(_) for _ in HAS_TSPX_writable_preset_indices)
    unwritable_presets_str = ','.join(str(_) for _ in HAS_TSPX_unwritable_preset_indices)

    preset_indices = HAS_TSPX_available_presets_indices + HAS_TSPX_unavailable_presets_indices
    max_index = max([0] + preset_indices)
    num_presets = len(preset_indices)

    pts = ptses[0]

    pts.set_pixit("HAS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("HAS", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("HAS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("HAS", "TSPX_time_guard", "180000")
    pts.set_pixit("HAS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("HAS", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_HAS_db.xml")
    pts.set_pixit("HAS", "TSPX_mtu_size", "49")
    pts.set_pixit("HAS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("HAS", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("HAS", "TSPX_pin_code", "0000")
    pts.set_pixit("HAS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("HAS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("HAS", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("HAS", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("HAS", "TSPX_Connection_Interval", "120")
    pts.set_pixit("HAS", "TSPX_largest_preset_index", str(max_index))
    pts.set_pixit("HAS", "TSPX_num_presets", str(num_presets))
    pts.set_pixit("HAS", "TSPX_available_preset_index", available_presets_str)
    pts.set_pixit("HAS", "TSPX_unavailable_preset_index", unavailable_presets_str)
    pts.set_pixit("HAS", "TSPX_writable_preset_index", writable_presets_str)
    pts.set_pixit("HAS", "TSPX_unwritable_preset_index", unwritable_presets_str)


def test_cases(ptses):
    """ Returns a list of HAS test cases """

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    add_conditions = []

    for index in HAS_TSPX_available_presets_indices + HAS_TSPX_unavailable_presets_indices:
        properties = PresetProperty.BT_HAS_PROP_NONE
        if index in HAS_TSPX_available_presets_indices:
            properties |= PresetProperty.BT_HAS_PROP_AVAILABLE
        if index in HAS_TSPX_writable_preset_indices:
            properties |= PresetProperty.BT_HAS_PROP_WRITABLE
        add_conditions += [TestFunc(btp.has_add_preset, index, properties, 'PRESET_' + str(index))]

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param("HAS", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_has)
    ]

    test_case_name_list = pts.get_test_case_list('HAS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("HAS", tc_name,
                             cmds=pre_conditions + add_conditions,
                             generic_wid_hdl=has_wid_hdl)
        tc_list.append(instance)

    return tc_list
