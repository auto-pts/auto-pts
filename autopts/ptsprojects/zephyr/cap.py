#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

"""CAP test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import SynchPoint, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.cap_wid import cap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.pybtp.btp.cap import announcements
from autopts.pybtp.defs import PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL
from autopts.pybtp.types import Addr, Context
from autopts.utils import ResultWithFlag


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
    pts.set_pixit("CAP", "TSPX_Sync_Timeout", "20000")
    pts.set_pixit("CAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CAP", "TSPX_STREAMING_DATA_CONFIRMATION_METHOD", "By Playing")
    pts.set_pixit("CAP", "TSPX_CONTEXT_TYPE", "0002")
    pts.set_pixit("CAP", "TSPX_Connection_Interval", "80")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("CAP", "TSPX_BST_CODEC_CONFIG", "16_2_1")


SINK_CONTEXTS = Context.LIVE | Context.CONVERSATIONAL | Context.MEDIA | Context.RINGTONE
SOURCE_CONTEXTS = Context.LIVE | Context.CONVERSATIONAL

def test_cases(ptses):
    """Returns a list of CAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    adv_data, rsp_data = {}, {}

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

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
        # Enable GMCS and TBS to have 2 CCIDs in Zephyr stack which is required by some tests
        TestFunc(btp.core_reg_svc_gmcs),
        TestFunc(btp.core_reg_svc_tbs),
        TestFunc(stack.gmcs_init),
        # Enable CSIP to have access to Start Ordered Access
        # procedure BTP command
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(stack.cap_init),
        TestFunc(stack.micp_init),
        TestFunc(stack.vcp_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.core_reg_svc_micp),
        TestFunc(btp.core_reg_svc_vcp),
        TestFunc(btp.gap_set_extended_advertising_on),
        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param("CAP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str()))
    ]

    general_conditions = [
        TestFunc(announcements, adv_data, rsp_data, False, SINK_CONTEXTS, SOURCE_CONTEXTS),
        TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data),
    ]

    targeted_conditions = [
        TestFunc(announcements, adv_data, rsp_data, True, SINK_CONTEXTS, SOURCE_CONTEXTS),
        TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data),
    ]

    custom_test_cases = [
        ZTestCase("CAP", "CAP/CL/ADV/BV-01-C", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/CL/ADV/BV-03-C", cmds=pre_conditions + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-01-C", cmds=pre_conditions + [
            TestFunc(btp.pacs_set_available_contexts,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL)] + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-02-C", cmds=pre_conditions + [
            TestFunc(btp.pacs_set_available_contexts,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL)] + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-03-C", cmds=pre_conditions + [
            TestFunc(btp.pacs_set_available_contexts,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL)] + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-04-C", cmds=pre_conditions + [
            TestFunc(btp.pacs_set_available_contexts,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                     PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL)] + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-01-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 405),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 400),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-01-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-02-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 405),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 400),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-02-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-03-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 405),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 400),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-03-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-04-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 405),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 400),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-04-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-05-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 405),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 400),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-05-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-06-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 405),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 400),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-06-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-07-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 405),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 400),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-07-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-08-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 405),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 400),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-08-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-09-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 405),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 400),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-09-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-10-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 405),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 400),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-10-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-11-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 405),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 400),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-11-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-12-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 405),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 400),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-12-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-13-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 405),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 400),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-13-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-14-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 405),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 400),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-14-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-29-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 405),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 400),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-29-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-30-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 405),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 400),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-30-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-31-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 405),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 400),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-31-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-32-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 405),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 419),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 310),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-32-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-33-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 405),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 419),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 310),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-33-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-34-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 405),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 419),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-34-C", 310),
                       SynchPoint("CAP/INI/UST/BV-34-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-34-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-35-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 405),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 419),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-35-C", 310),
                       SynchPoint("CAP/INI/UST/BV-35-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-35-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-36-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 405),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 419),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-36-C", 310),
                       SynchPoint("CAP/INI/UST/BV-36-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-36-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-37-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 405),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 419),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 310),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-37-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-40-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 405),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 400),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 312),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 309),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 309)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-40-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-41-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 405),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 400),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 312),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-41-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-42-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 405),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 400),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 312),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 309),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 309)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-42-C_LT2"),
    ]

    test_case_name_list = pts.get_test_case_list('CAP')
    tc_list = []

    for tc_name in test_case_name_list:

        instance = ZTestCase("CAP", tc_name,
                             cmds=pre_conditions + (targeted_conditions if "CAP/ACC" in tc_name else []),
                             generic_wid_hdl=cap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
        TestFunc(lambda: pts2.update_pixit_param(
            "CAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90, clear=True))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-06-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-07-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-08-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-09-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-10-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-11-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-12-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-13-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-14-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-29-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-30-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-31-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-32-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-33-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-34-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-35-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-36-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-37-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-40-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-41-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-42-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
    ]

    return tc_list + test_cases_lt2
