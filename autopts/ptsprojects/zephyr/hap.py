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

"""HAP test cases"""
from enum import IntEnum
import struct

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.hap_wid import hap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp.types import Addr, AdType, Context
from autopts.pybtp.defs import PACS_AUDIO_DIR_SINK, PACS_AUDIO_LOCATION_FRONT_LEFT, \
                               HAS_TSPX_available_presets_indices, \
                               HAS_TSPX_unavailable_presets_indices

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853


def set_pixits(ptses):
    """Setup HAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    preset_indices = HAS_TSPX_available_presets_indices + HAS_TSPX_unavailable_presets_indices
    max_index = max([0] + preset_indices)
    num_presets = len(preset_indices)

    pts = ptses[0]

    pts.set_pixit("HAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("HAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("HAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("HAP", "TSPX_time_guard", "180000")
    pts.set_pixit("HAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("HAP", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_HAS_db.xml")
    pts.set_pixit("HAP", "TSPX_mtu_size", "64")
    pts.set_pixit("HAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("HAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("HAP", "TSPX_pin_code", "0000")
    pts.set_pixit("HAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("HAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("HAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("HAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("HAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("HAP", "TSPX_Connection_Interval", "120")
    pts.set_pixit("HAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("HAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("HAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("HAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("HAP", "TSPX_TARGET_LATENCY", "TARGET_LOWER_LATENCY")
    pts.set_pixit("HAP", "TSPX_TARGET_PHY", "LE_2M_PHY")
    pts.set_pixit("HAP", "TSPX_largest_preset_index", str(max_index))
    pts.set_pixit("HAP", "TSPX_num_presets", str(num_presets))


def announcements(advData, targeted):
    """
        CAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] = [ struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]
    """
        BAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] += [ struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, \
        Context.LIVE | Context.MEDIA, Context.LIVE, 0) ]
    """
        RSI
    """
    rsi = btp.cas_get_member_rsi()
    advData[AdType.rsi] = struct.pack('<6B', *rsi)


def test_cases(ptses):
    """Returns a list of HAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    advData = {}

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_aics),
        TestFunc(stack.aics_init),
        TestFunc(btp.core_reg_svc_mics),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(stack.pacs_init),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(stack.ascs_init),
        TestFunc(btp.core_reg_svc_has),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.core_reg_svc_ias),
        TestFunc(stack.ias_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.pacs_set_location, PACS_AUDIO_DIR_SINK, PACS_AUDIO_LOCATION_FRONT_LEFT)
    ]
    adv_conditions = [
        TestFunc(announcements, advData, True),
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(btp.gap_adv_ind_on, ad=advData),
        TestFunc(lambda: pts.update_pixit_param("HAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
    ]

    test_case_name_list = pts.get_test_case_list('HAP')
    tc_list = []

    for tc_name in test_case_name_list:
        if tc_name == 'HAP/HA/STR/BV-02-C':
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions,
                                 generic_wid_hdl=hap_wid_hdl)
        else:
            instance = ZTestCase("HAP", tc_name,
                        cmds=pre_conditions + adv_conditions,
                        generic_wid_hdl=hap_wid_hdl)

        tc_list.append(instance)

    return tc_list
