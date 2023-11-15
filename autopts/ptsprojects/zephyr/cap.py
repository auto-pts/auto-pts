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

"""CAP test cases"""
from enum import IntEnum, IntFlag
import struct

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.cap_wid import cap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp.types import Addr, AdType, Context
from autopts.pybtp import defs

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853


def set_pixits(ptses):
    """Setup CAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("CAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("CAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("CAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("CAP", "TSPX_time_guard", "180000")
    pts.set_pixit("CAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("CAP", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_BASS_db.xml")
    pts.set_pixit("CAP", "TSPX_mtu_size", "64")
    pts.set_pixit("CAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("CAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("CAP", "TSPX_pin_code", "0000")
    pts.set_pixit("CAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("CAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("CAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("CAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("CAP", "TSPX_TARGET_ASE_CHARACTERISTIC", "SINK_ASE")
    pts.set_pixit("CAP", "TSPX_TARGET_LATENCY", "TARGET_BALANCED_LATENCY_RELIABILITY")
    pts.set_pixit("CAP", "TSPX_TARGET_PHY", "LE_2M_PHY")
    pts.set_pixit("CAP", "TSPX_Codec_ID", "0600000000")
    pts.set_pixit("CAP", "TSPX_VS_Codec_Specific_Configuration", "0001")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Framing", "UNFRAMING")
    pts.set_pixit("CAP", "TSPX_VS_QoS_PHY", "2M_PHY")
    pts.set_pixit("CAP", "TSPX_VS_QoS_SDU_Interval", "64")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Max_SDU", "10000")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Retransmission_Number", "2")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Max_Transport_Latency", "40")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Presentation_Delay", "40000")
    pts.set_pixit("CAP", "TSPX_VS_Company_ID", "0000")
    pts.set_pixit("CAP", "TSPX_VS_Codec_ID", "0000")
    pts.set_pixit("CAP", "TSPX_METADATA_SELECTION", "USE_IXIT_VALUE_FOR_METADATA")
    pts.set_pixit("CAP", "TSPX_METADATA_SINK", "03020200")
    pts.set_pixit("CAP", "TSPX_METADATA_SOURCE", "03020200")
    pts.set_pixit("CAP", "TSPX_broadcast_code", "0102680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CAP", "TSPX_Sync_Timeout", "3000")
    pts.set_pixit("CAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CAP", "TSPX_STREAMING_DATA_CONFIRMATION_METHOD", "By Playing")
    pts.set_pixit("CAP", "TSPX_CONTEXT_TYPE", "0002")
    pts.set_pixit("CAP", "TSPX_Connection_Interval", "80")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("CAP", "TSPX_BST_CODEC_CONFIG", "8_1_1")
    

sink_contexts = Context.LIVE | Context.CONVERSATIONAL | Context.MEDIA | Context.RINGTONE
source_contexts = Context.LIVE | Context.CONVERSATIONAL


def announcements(advData, rspData, targeted):
    """
        CAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] = [ struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]
    """
        BAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] += [ struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, sink_contexts, source_contexts, 0) ]
    """
        RSI
    """
    rsi = btp.cas_get_member_rsi()
    advData[AdType.rsi] = struct.pack('<6B', *rsi)


def test_cases(ptses):
    """Returns a list of CAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    advData, rspData = {}, {}

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_mics),
        TestFunc(btp.core_reg_svc_vcs),
        TestFunc(stack.vcs_init),
        TestFunc(btp.core_reg_svc_aics),
        TestFunc(stack.aics_init),
        TestFunc(btp.core_reg_svc_vocs),
        TestFunc(stack.vocs_init),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(btp.pacs_set_available_contexts, sink_contexts, source_contexts),
        TestFunc(btp.pacs_set_supported_contexts, sink_contexts, source_contexts),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.gap_set_extended_advertising_on)
    ]

    general_conditions = [
        TestFunc(announcements, advData, rspData, False),
        TestFunc(btp.gap_adv_ind_on, ad=advData, sd=rspData),
        TestFunc(lambda: pts.update_pixit_param("CAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str()))
    ]

    targeted_conditions = [
        TestFunc(announcements, advData, rspData, True),
        TestFunc(btp.gap_adv_ind_on, ad=advData, sd=rspData),
        TestFunc(lambda: pts.update_pixit_param("CAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str()))
    ]

    test_case_name_list = pts.get_test_case_list('CAP')
    general_name_list = [ "CAP/CL/ADV/BV-01-C" ]
    tc_list = []

    for tc_name in test_case_name_list:

        if tc_name in general_name_list:
            instance = ZTestCase("CAP", tc_name,
                        cmds=pre_conditions + general_conditions,
                        generic_wid_hdl=cap_wid_hdl)
        else:
            instance = ZTestCase("CAP", tc_name,
                        cmds=pre_conditions + targeted_conditions,
                        generic_wid_hdl=cap_wid_hdl)

        tc_list.append(instance)

    return tc_list
