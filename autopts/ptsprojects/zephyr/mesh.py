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

"""MESH test cases"""
import random
import time
from binascii import hexlify
from uuid import uuid4

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import SynchPoint, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp, defs
from autopts.pybtp.types import Addr, MeshVals
from autopts.wid import (
    mesh_wid_hdl_rpr_2ptses,
    mesh_wid_hdl_rpr_persistent_storage,
    mesh_wid_hdl_rpr_persistent_storage_alt,
)

mesh_wid_hdl = get_wid_handler("zephyr", "mesh")


def set_pixits(ptses):
    """Setup MESH profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("MESH", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("MESH", "TSPX_bd_addr_additional_filter_accept_list", "")
    pts.set_pixit("MESH", "TSPX_time_guard", "300000")
    pts.set_pixit("MESH", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("MESH", "TSPX_mtu_size", "23")
    pts.set_pixit("MESH", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("MESH", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("MESH", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("MESH", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("MESH", "TSPX_scan_interval", "30")
    pts.set_pixit("MESH", "TSPX_scan_window", "30")
    pts.set_pixit("MESH", "TSPX_scan_filter", "00")
    pts.set_pixit("MESH", "TSPX_advertising_interval_min", "160")
    pts.set_pixit("MESH", "TSPX_advertising_interval_max", "160")
    pts.set_pixit("MESH", "TSPX_tester_OOB_information", "F87F")
    pts.set_pixit("MESH", "TSPX_device_uuid", "001BDC0810210B0E0A0C000B0E0A0C00")
    pts.set_pixit("MESH", "TSPX_device_uuid2", "00000000000000000000000000000000")
    pts.set_pixit(
        "MESH",
        "TSPX_device_public_key",
        ("5B2AD8B034D80743536E7F1B2354FE0869F50E8F085BEA047119590F4E74AC67"
         "F0151EFBC531FBAB2673B1D1ADF78931F400D950E466D026FC2E7D090E2A1A0C"))
    pts.set_pixit("MESH", "TSPX_device_private_key",
                  "A60179DE5010F30CD8B8B173E2A7F945724D3AEF43A411909920FFF8108EED00")
    pts.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts.set_pixit("MESH", "TSPX_vendor_model_id", "05f11234")
    pts.set_pixit("MESH", "TSPX_list_of_optional_ad_types", "")
    pts.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "2")
    pts.set_pixit("MESH", "TSPX_health_valid_test_ids", "00")
    pts.set_pixit("MESH", "TSPX_iut_comp_data_page", "130")
    pts.set_pixit("MESH", "TSPX_iut_supports_relay", "FALSE")
    pts.set_pixit("MESH", "TSPX_device_key",
                  "00000000000000000000000000000000")
    pts.set_pixit("MESH", "TSPX_enable_IUT_provisioner", "FALSE")
    pts.set_pixit("MESH", "TSPX_maximum_number_of_supported_subnets", "1")
    pts.set_pixit("MESH", "TSPX_Beacon_Observation_Period", "30")
    pts.set_pixit("MESH", "TSPX_pt_addr", "0300")
    pts.set_pixit("MESH", "TSPX_pt2_addr", "0310")
    pts.set_pixit("MESH", "TSPX_po_addr", "0200")
    pts.set_pixit("MESH", "TSPX_po2_addr", "0210")
    pts.set_pixit("MESH", "TSPX_oob_certificates", "")
    pts.set_pixit("MESH", "TSPX_Max_Number_Of_Paths", "1")
    pts.set_pixit("MESH", "Max_Number_Of_Dependent_Nodes_Per_Path", "1")
    pts.set_pixit("MESH", "TSPX_iut_model_id_publish_not_supported", "0000")
    pts.set_pixit("MESH", "TSPX_mdf_label_uuid_for_virtual_address", "112233445566778899AABBCCDDEEFFEE")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]

    # PTS2
    pts2.set_pixit("MESH", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("MESH", "TSPX_bd_addr_additional_filter_accept_list", "")
    pts2.set_pixit("MESH", "TSPX_time_guard", "300000")
    pts2.set_pixit("MESH", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("MESH", "TSPX_mtu_size", "23")
    pts2.set_pixit("MESH", "TSPX_delete_link_key", "TRUE")
    pts2.set_pixit("MESH", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("MESH", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("MESH", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts2.set_pixit("MESH", "TSPX_scan_interval", "30")
    pts2.set_pixit("MESH", "TSPX_scan_window", "30")
    pts2.set_pixit("MESH", "TSPX_scan_filter", "00")
    pts2.set_pixit("MESH", "TSPX_advertising_interval_min", "160")
    pts2.set_pixit("MESH", "TSPX_advertising_interval_max", "160")
    pts2.set_pixit("MESH", "TSPX_tester_OOB_information", "F87F")
    pts2.set_pixit("MESH", "TSPX_device_uuid", "00000000000000000000000000000000")
    pts2.set_pixit("MESH", "TSPX_device_uuid2", "001BDC0810210B0E0A0C000B0E0A0C00")
    pts2.set_pixit(
        "MESH",
        "TSPX_device_public_key",
        ("5B2AD8B034D80743536E7F1B2354FE0869F50E8F085BEA047119590F4E74AC67"
         "F0151EFBC531FBAB2673B1D1ADF78931F400D950E466D026FC2E7D090E2A1A0C"))
    pts2.set_pixit("MESH", "TSPX_device_private_key",
                   "A60179DE5010F30CD8B8B173E2A7F945724D3AEF43A411909920FFF8108EED00")
    pts2.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts2.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts2.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts2.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts2.set_pixit("MESH", "TSPX_vendor_model_id", "00000000")
    pts2.set_pixit("MESH", "TSPX_list_of_optional_ad_types", "")
    pts2.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "2")
    pts2.set_pixit("MESH", "TSPX_health_valid_test_ids", "00")
    pts2.set_pixit("MESH", "TSPX_iut_supports_relay", "FALSE")
    pts2.set_pixit("MESH", "TSPX_device_key",
                   "00000000000000000000000000000000")
    pts2.set_pixit("MESH", "TSPX_enable_IUT_provisioner", "FALSE")
    pts2.set_pixit("MESH", "TSPX_maximum_number_of_supported_subnets", "1")
    pts2.set_pixit("MESH", "TSPX_Beacon_Observation_Period", "30")
    pts.set_pixit("MESH", "TSPX_pt_addr", "0300")
    pts.set_pixit("MESH", "TSPX_pt2_addr", "0310")
    pts.set_pixit("MESH", "TSPX_po_addr", "0200")
    pts.set_pixit("MESH", "TSPX_po2_addr", "0210")
    pts.set_pixit("MESH", "TSPX_oob_certificates", "")
    pts.set_pixit("MESH", "TSPX_Max_Number_Of_Paths", "1")
    pts.set_pixit("MESH", "Max_Number_Of_Dependent_Nodes_Per_Path", "1")
    pts.set_pixit("MESH", "TSPX_iut_model_id_publish_not_supported", "0000")
    pts.set_pixit("MESH", "TSPX_mdf_label_uuid_for_virtual_address", "112233445566778899AABBCCDDEEFFEE")


def test_cases(ptses):
    """Returns a list of MESH test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    device_uuid = hexlify(uuid4().bytes)
    device_uuid2 = hexlify(uuid4().bytes)

    out_actions = [defs.MESH_OUT_DISPLAY_NUMBER,
                   defs.MESH_OUT_DISPLAY_STRING,
                   defs.MESH_OUT_DISPLAY_NUMBER | defs.MESH_OUT_DISPLAY_STRING]
    in_actions = [defs.MESH_IN_ENTER_NUMBER,
                  defs.MESH_IN_ENTER_STRING,
                  defs.MESH_IN_ENTER_NUMBER | defs.MESH_IN_ENTER_STRING]

    oob = "000102030405060708090A0B0C0D0E0F"
    oob_sha256 = "000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C1D1E1F"
    out_size = random.randint(0, 2)
    rand_out_actions = random.choice(out_actions) if out_size else 0
    in_size = random.randint(0, 2)
    rand_in_actions = random.choice(in_actions) if in_size else 0
    crpl_size = 10  # Maximum capacity of the replay protection list
    auth_metod = 0x00
    pub_key = ("5B2AD8B034D80743536E7F1B2354FE0869F50E8F085BEA047119590F4E74AC67"
               "F0151EFBC531FBAB2673B1D1ADF78931F400D950E466D026FC2E7D090E2A1A0C")
    priv_key = "A60179DE5010F30CD8B8B173E2A7F945724D3AEF43A411909920FFF8108EED00"

    stack.gap_init(iut_device_name)
    stack.mesh_init(device_uuid, device_uuid2)

    common_pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.core_reg_svc_mesh),
        TestFunc(btp.mesh_init),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_maximum_network_message_cache_entries", "10")),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_maximum_number_of_supported_subnets", "2")),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_subscription_address_list",
            MeshVals.subscription_addr_list1)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_enable_IUT_provisioner", "FALSE")),
    ]

    pre_conditions = common_pre_conditions + [
        TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions, in_size,
                                                  rand_in_actions, crpl_size, auth_metod)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid", stack.mesh.get_dev_uuid())),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid2", stack.mesh.get_dev_uuid_lt2())),
    ]

    pre_conditions_slave = [
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_device_uuid", stack.mesh.get_dev_uuid_lt2())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_device_uuid2", stack.mesh.get_dev_uuid())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob)),
    ]

    # Some test cases require device_uuid and device_uuid2 to be swapped
    pre_conditions_lt2 = common_pre_conditions + [
        TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions, in_size,
                                                  rand_in_actions, crpl_size, auth_metod)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid", stack.mesh.get_dev_uuid_lt2())),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid2", stack.mesh.get_dev_uuid())),
    ]

    pre_conditions_lt2_slave = [
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_device_uuid", stack.mesh.get_dev_uuid())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_device_uuid2", stack.mesh.get_dev_uuid_lt2())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob)),
    ]

    pre_conditions_prov = pre_conditions + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_enable_IUT_provisioner", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob)),
        TestFunc(lambda: stack.mesh.set_iut_provisioner(True)),
        TestFunc(lambda: stack.mesh.expect_node(stack.mesh.get_dev_uuid())),
    ]

    pre_conditions_prov_sha256 = pre_conditions + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_enable_IUT_provisioner", "TRUE")),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob_sha256)),
        TestFunc(lambda: stack.mesh.set_iut_provisioner(True)),
        TestFunc(lambda: stack.mesh.expect_node(stack.mesh.get_dev_uuid())),
    ]

    pre_conditions_node = pre_conditions + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob)),
    ]

    pre_conditions_node_sha256 = pre_conditions + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_OOB_code", oob_sha256)),
    ]

    pre_conditions_prov_pub_key = pre_conditions_prov + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
    ]

    pre_conditions_prov_pub_key_sha256 = pre_conditions_prov_sha256 + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
    ]

    pre_conditions_pub_priv_key = pre_conditions_node + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_private_key", priv_key)),
        TestFunc(lambda: stack.mesh.priv_key_set(priv_key))
    ]

    pre_conditions_pub_priv_key_sha256 = pre_conditions_node_sha256 + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_private_key", priv_key)),
        TestFunc(lambda: stack.mesh.priv_key_set(priv_key))
    ]

    pre_conditions_comp_change = pre_conditions + [
        TestFunc(btp.mesh_start),
        TestFunc(btp.mesh_reset),
        TestFunc(btp.mesh_comp_change_prepare),
        TestFunc(time.sleep, 5),
        TestFunc(btp.get_iut_method().wait_iut_ready_event),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_mesh),
        TestFunc(btp.mesh_init),
        TestFunc(stack.mesh.reset_state)
    ]

    pre_conditions_comp_change_alt = pre_conditions + [
        TestFunc(btp.mesh_start),
        TestFunc(btp.mesh_reset),
        TestFunc(btp.mesh_comp_change_prepare),
        TestFunc(time.sleep, 5),
        TestFunc(btp.get_iut_method().wait_iut_ready_event),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_mesh),
        TestFunc(btp.mesh_init, comp=1),
        TestFunc(stack.mesh.reset_state)
    ]

    custom_test_cases = [
        ZTestCase("MESH", "MESH/NODE/CFG/CFGR/BV-01-C", cmds=pre_conditions +
                  [TestFunc(lambda: pts.update_pixit_param(
                   "MESH", "TSPX_iut_supports_relay", "TRUE"))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-03-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-04-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-05-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-09-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-10-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-04-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-20-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-23-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-12-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-14-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-05-C",
                  cmds=pre_conditions + [TestFunc(lambda: btp.mesh_lpn(True))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-01-C",
                  cmds=pre_conditions_node +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob,
                            random.randint(1, 2), random.choice(out_actions),
                            in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-02-C", cmds=pre_conditions_node +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-04-C", cmds=pre_conditions_pub_priv_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob,
                                                             1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-05-C", cmds=pre_conditions_pub_priv_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob,
                            out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-06-C", cmds=pre_conditions_pub_priv_key,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-08-C", cmds=pre_conditions_pub_priv_key,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-13-C",
                  cmds=pre_conditions_node_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256,
                            random.randint(1, 2), random.choice(out_actions),
                            in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-14-C", cmds=pre_conditions_node_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-15-C", cmds=pre_conditions_node_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-16-C", cmds=pre_conditions_pub_priv_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256,
                                                             1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-17-C", cmds=pre_conditions_pub_priv_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256,
                            out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-18-C", cmds=pre_conditions_pub_priv_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                            random.randint(1, 2), random.choice(in_actions), crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-20-C", cmds=pre_conditions_pub_priv_key_sha256,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-06-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-07-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-08-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-05-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/SNBP/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/COMP/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/DTTL/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/GPXY/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/CFGF/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/CFGR/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/MP/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/SL/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/SL/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/NKL/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/NKL/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/NKL/BV-03-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/AKL/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/AKL/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/AKL/BV-03-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/AKL/BV-04-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/MAKL/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/MAKL/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/MAKL/BV-03-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/MAKL/BV-04-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/NID/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/RST/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/HBP/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/HBS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/NTX/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CFGCL/CFG/LPNPT/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-01-C", cmds=pre_conditions_prov +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, 1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             random.randint(1, 2), defs.BTP_MESH_CMD_INPUT_NUMBER,
                                                             crpl_size, defs.MESH_OUTPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-02-C", cmds=pre_conditions_prov +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, 8, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             8, defs.MESH_IN_TWIST, crpl_size,
                                                             defs.MESH_INPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-03-C", cmds=pre_conditions_prov +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size,
                                                             defs.MESH_STATIC_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-04-C", cmds=pre_conditions_prov_pub_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, 1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             random.randint(
                                                                 1, 2), defs.BTP_MESH_CMD_INPUT_NUMBER,
                                                             crpl_size, defs.MESH_OUTPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-05-C", cmds=pre_conditions_prov_pub_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, 8, defs.MESH_OUT_DISPLAY_STRING,
                                                             8, defs.MESH_IN_ENTER_STRING, crpl_size, defs.MESH_INPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-06-C", cmds=pre_conditions_prov_pub_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size, defs.MESH_STATIC_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-07-C", cmds=pre_conditions_prov +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions,
                            in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-08-C", cmds=pre_conditions_prov_pub_key +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-11-C", cmds=pre_conditions_prov_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, 1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             random.randint(1, 2), defs.BTP_MESH_CMD_INPUT_NUMBER,
                                                             crpl_size, defs.MESH_OUTPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-12-C", cmds=pre_conditions_prov_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, 8, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             8, defs.MESH_IN_TWIST, crpl_size,
                                                             defs.MESH_INPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-13-C", cmds=pre_conditions_prov_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size,
                                                             defs.MESH_STATIC_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-14-C", cmds=pre_conditions_prov_pub_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, 1, defs.MESH_OUT_DISPLAY_NUMBER,
                                                             random.randint(
                                                                 1, 2), defs.BTP_MESH_CMD_INPUT_NUMBER,
                                                             crpl_size, defs.MESH_OUTPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-15-C", cmds=pre_conditions_prov_pub_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, 8, defs.MESH_OUT_DISPLAY_STRING,
                                                             8, defs.MESH_IN_ENTER_STRING, crpl_size, defs.MESH_INPUT_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-16-C", cmds=pre_conditions_prov_pub_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size, defs.MESH_STATIC_OOB))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-17-C", cmds=pre_conditions_prov_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                            in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-18-C", cmds=pre_conditions_prov_pub_key_sha256 +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob_sha256, out_size, rand_out_actions,
                                                             in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-09-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BV-10-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BI-14-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BI-16-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PROV/BI-18-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PBADV/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PBADV/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PBADV/BV-03-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/PVNR/PBADV/BI-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-02-C", cmds=pre_conditions_prov +
                  [TestFunc(stack.gatt_init),
                   TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-03-C", cmds=pre_conditions_prov +
                  [TestFunc(stack.gatt_init),
                   TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-04-C", cmds=pre_conditions_prov +
                  [TestFunc(stack.gatt_init),
                   TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-05-C", cmds=pre_conditions_prov +
                  [TestFunc(stack.gatt_init),
                   TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-06-C", cmds=pre_conditions_prov +
                  [TestFunc(stack.gatt_init),
                   TestFunc(btp.set_pts_addr, pts.q_bd_addr, Addr.le_public)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-14-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-15-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-16-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-17-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-18-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-19-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-20-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-21-C", cmds=pre_conditions +
                  [TestFunc(lambda: btp.mesh_store_net_data()),
                   TestFunc(lambda: btp.mesh_store_model_data())],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-06-C", cmds=pre_conditions +
                  [TestFunc(stack.mesh.set_iut_addr, 2)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/SAR/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/SAR/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/SAR/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/SAR/BV-02-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),

        ZTestCase("MESH", "MESH/SR/LCD/LCMP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/LCD/MMD/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/LCD/LCMP/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/LCD/MMD/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),

        ZTestCase("MESH", "MESH/SR/AGG/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/AGG/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/AGG/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/AGG/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/RPR/SCN/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/RPR/LNK/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/RPR/PDU/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/PRB/PBS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/PRB/PGPXY/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/PRB/PNID/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/PROX/BV-11-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BV-02-C",
                  cmds=pre_conditions_comp_change_alt,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage_alt),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BV-03-C",
                  cmds=pre_conditions_comp_change_alt,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage_alt),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BV-04-C",
                  cmds=pre_conditions_comp_change_alt,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage_alt),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-25-C",
                  cmds=pre_conditions_comp_change,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage_alt),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BI-01-C",
                  cmds=pre_conditions_comp_change,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BI-02-C",
                  cmds=pre_conditions_comp_change,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BI-03-C",
                  cmds=pre_conditions_comp_change,
                  generic_wid_hdl=mesh_wid_hdl_rpr_persistent_storage),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-24-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-26-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-20-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-22-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/ODP/BV-01-C",
                  cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/MPXS/BV-09-C",
                  cmds=pre_conditions_prov +
                  [TestFunc(time.sleep, 10, post_wid=500),
                   TestFunc(btp.mesh_proxy_solicit, post_wid=500)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/BCM/SBS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/BCM/BDS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/CL/BCM/BTS/BV-01-C", cmds=pre_conditions_prov,
                  generic_wid_hdl=mesh_wid_hdl),
    ]

    test_cases_lt2 = [
        ZTestCase("MESH", "MESH/SR/MPXS/BV-08-C", cmds=pre_conditions_lt2 +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/MPXS/BV-08-C", 12),
                             SynchPoint("MESH/SR/MPXS/BV-08-C-LT2", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/MPXS/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-03-C",
                  cmds=pre_conditions_prov +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit),
                   TestFunc(lambda: stack.mesh.expect_node(
                       stack.mesh.get_dev_uuid_lt2())),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/CFGCL/KR/BV-03-C", 272),
                             SynchPoint("MESH/CFGCL/KR/BV-03-C-LT2", 269)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/CFGCL/KR/BV-03-C-LT2"),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-04-C",
                  cmds=pre_conditions_prov +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit),
                   TestFunc(lambda: stack.mesh.expect_node(
                       stack.mesh.get_dev_uuid_lt2())),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/CFGCL/KR/BV-04-C", 276),
                             SynchPoint("MESH/CFGCL/KR/BV-04-C-LT2", 212)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/CFGCL/KR/BV-04-C-LT2"),
        ZTestCase("MESH", "MESH/CFGCL/KR/BV-06-C",
                  cmds=pre_conditions_prov +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit),
                   TestFunc(lambda: stack.mesh.expect_node(
                       stack.mesh.get_dev_uuid_lt2())),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/CFGCL/KR/BV-06-C", 276),
                             SynchPoint("MESH/CFGCL/KR/BV-06-C-LT2", 212)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/CFGCL/KR/BV-06-C-LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-01-C",
                  cmds=pre_conditions +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/RPR/LNK/BV-01-C", 713),
                                  SynchPoint("MESH/SR/RPR/LNK/BV-01-C_LT2", 714)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-01-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-02-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-03-C",
                  cmds=pre_conditions +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/RPR/LNK/BV-03-C", 713),
                                  SynchPoint("MESH/SR/RPR/LNK/BV-03-C_LT2", 714)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-03-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-04-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-04-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-05-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-05-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-06-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-06-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-07-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-07-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-09-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-09-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-10-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-10-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-11-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-11-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BI-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BI-01-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-13-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-13-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-14-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-14-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-15-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-15-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-17-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-17-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BV-19-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BV-19-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BI-02-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BI-02-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/LNK/BI-05-C",
                  cmds=pre_conditions +
                  [TestFunc(btp.mesh_start, post_wid=715)],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/LNK/BI-05-C_LT2"),
        ZTestCase("MESH", "MESH/SR/RPR/PDU/BV-01-C",
                  cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/RPR/PDU/BV-01-C_LT2"),
    ]

    test_cases_slaves = [
        ZTestCaseSlave("MESH", "MESH/CFGCL/KR/BV-03-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/CFGCL/KR/BV-04-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/CFGCL/KR/BV-06-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),

        ZTestCaseSlave("MESH", "MESH/SR/MPXS/BV-08-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/CFG/HBP/BV-05-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/CFG/HBS/BV-05-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-02-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-03-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-04-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-05-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-06-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-08-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-09-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-10-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-11-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-12-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-14-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-15-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-16-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-17-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-18-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-19-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-20-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-21-C-LT2",
                       cmds=pre_conditions_lt2_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-01-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-02-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-03-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-04-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-05-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-06-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-07-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-09-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-10-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-11-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BI-01-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-13-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-14-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-15-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-17-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BV-19-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BI-02-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/PDU/BV-01-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
        ZTestCaseSlave("MESH", "MESH/SR/RPR/LNK/BI-05-C_LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl_rpr_2ptses),
    ]

    test_case_name_list = pts.get_test_case_list('MESH')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('MESH', tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=mesh_wid_hdl)

        for custom_tc in custom_test_cases + test_cases_lt2:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    tc_list += test_cases_slaves
    pts2 = ptses[1]

    return tc_list
