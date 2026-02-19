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
import struct

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.btp.gap import gap_set_uuid16_svc_data
from autopts.pybtp.defs import HAS_TSPX_available_presets_indices, HAS_TSPX_unavailable_presets_indices
from autopts.pybtp.types import UUID, Addr, AdType, BAPAnnouncement, CAPAnnouncement, Context

hap_wid_hdl = get_wid_handler("zephyr", "hap")

# Options aligned with the overlay-le-audio.conf options
BTP_HAP_HA_OPTS_DEFAULT = (btp.defs.HAP_HA_OPT_PRESETS_DYNAMIC |
                           btp.defs.HAP_HA_OPT_PRESETS_WRITABLE)
BTP_HAP_HA_OPTS_BINAURAL = (btp.defs.HAP_HA_OPT_PRESETS_INDEPENDENT |
                            btp.defs.HAP_HA_OPT_PRESETS_DYNAMIC |
                            btp.defs.HAP_HA_OPT_PRESETS_WRITABLE)


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
    pts.set_pixit("HAP", "TSPX_TARGET_LATENCY", "TARGET_BALANCED_LATENCY_RELIABILITY")
    pts.set_pixit("HAP", "TSPX_TARGET_PHY", "LE_2M_PHY")
    pts.set_pixit("HAP", "TSPX_largest_preset_index", str(max_index))
    pts.set_pixit("HAP", "TSPX_num_presets", str(num_presets))


def set_member_rsi(advData, targeted):
    """
        RSI
    """
    rsi = btp.cas_get_member_rsi()
    advData[AdType.rsi] = struct.pack('<6B', *rsi)


test_cases_binaural = [
    'HAP/HA/DISC/BV-01-C',
    'HAP/HA/DISC/BV-05-C',
]

test_cases_banded = [
    'HAP/HA/DISC/BV-02-C',
    'HAP/HA/DISC/BV-06-C',
]


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
        TestFunc(btp.core_reg_svc_vcs),
        TestFunc(btp.vcs_register, 1, False, 100),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.core_reg_svc_ias),
        TestFunc(stack.ias_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_hap),
        # TODO: This list is getting quite long. Consider some refactor.
        TestFunc(stack.hap_init),
        TestFunc(lambda: pts.update_pixit_param("HAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
    ]

    adv_conditions = [
        TestFunc(gap_set_uuid16_svc_data, advData, UUID.CAS, struct.pack('<B', CAPAnnouncement.TARGETED)),
        TestFunc(gap_set_uuid16_svc_data, advData, UUID.ASCS, struct.pack('<BHHB', BAPAnnouncement.TARGETED,
                Context.LIVE | Context.MEDIA, Context.LIVE, 0)),
        TestFunc(set_member_rsi, advData, True),
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(btp.gap_adv_ind_on, ad=advData),
    ]

    pre_conditions_ha_binaural = pre_conditions + adv_conditions + [
        TestFunc(btp.hap_ha_init,
                 btp.defs.HAP_HA_TYPE_BINAURAL,
                 BTP_HAP_HA_OPTS_BINAURAL),
    ]

    pre_conditions_ha_banded = pre_conditions + [
        TestFunc(btp.hap_ha_init,
                 btp.defs.HAP_HA_TYPE_BANDED,
                 BTP_HAP_HA_OPTS_DEFAULT),
    ]

    pre_conditions_harc = pre_conditions + [
        TestFunc(btp.hap_harc_init),
    ]

    pre_conditions_hauc = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(stack.pacs_init),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(stack.ascs_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_hap),
        TestFunc(stack.hap_init),
        TestFunc(lambda: pts.update_pixit_param("HAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(btp.hap_hauc_init),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(stack.cap_init),
    ]

    pre_conditions_iac = pre_conditions + [
        TestFunc(btp.hap_iac_init),
    ]

    test_case_name_list = pts.get_test_case_list('HAP')
    tc_list = []

    for tc_name in test_case_name_list:
        if tc_name.startswith('HAP/HA/'):
            if tc_name == 'HAP/HA/STR/BV-02-C':
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions + [
                                         TestFunc(btp.hap_ha_init,
                                                  btp.defs.HAP_HA_TYPE_BINAURAL,
                                                  BTP_HAP_HA_OPTS_BINAURAL),
                                     ],
                                     generic_wid_hdl=hap_wid_hdl)
            elif tc_name in test_cases_banded:
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions_ha_banded,
                                     generic_wid_hdl=hap_wid_hdl)
            else:
                # fallback to binaural
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions_ha_binaural,
                                     generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/HARC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_harc,
                                 generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/HAUC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_hauc,
                                 generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/IAC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_iac,
                                 generic_wid_hdl=hap_wid_hdl)
        else:
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions,
                                 generic_wid_hdl=hap_wid_hdl)

        tc_list.append(instance)

    return tc_list
