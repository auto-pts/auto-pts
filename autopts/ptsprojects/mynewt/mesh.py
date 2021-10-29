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
from binascii import hexlify
import random
from uuid import uuid4

from autopts.pybtp import btp
from autopts.pybtp import defs
from autopts.pybtp.types import MeshVals
from autopts.client import get_unique_name
from autopts.wid import mesh_wid_hdl
from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase, ZTestCaseSlave


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
    pts.set_pixit("MESH", "TSPX_tester_database_file",
                  r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_SMPP_db.xml")
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
        ("F465E43FF23D3F1B9DC7DFC04DA8758184DBC966204796ECCF0D6CF5E16500CC"
         "0201D048BCBBD899EEEFC424164E33C201C2B010CA6B4D43A8A155CAD8ECB279"))
    pts.set_pixit("MESH", "TSPX_device_private_key",
                  "529AA0670D72CD6497502ED473502B037E8803B5C60829A5A3CAA219505530BA")
    pts.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts.set_pixit("MESH", "TSPX_vendor_model_id", "00021234")
    pts.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "10")
    pts.set_pixit("MESH", "TSPX_health_valid_test_ids", "00")
    pts.set_pixit("MESH", "TSPX_iut_comp_data_page", "0")
    pts.set_pixit("MESH", "TSPX_netkeyindex_value", "0")
    pts.set_pixit("MESH", "TSPX_iut_supports_relay", "FALSE")
    pts.set_pixit("MESH", "TSPX_application_key",
                  "3216D1509884B533248541792B877F98")
    pts.set_pixit("MESH", "TSPX_device_key",
                  "00000000000000000000000000000000")
    pts.set_pixit("MESH", "TSPX_enable_IUT_provisioner", "FALSE")
    pts.set_pixit("MESH", "TSPX_maximum_number_of_supported_subnets", "1")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]

    # PTS2
    pts2.set_pixit("MESH", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("MESH", "TSPX_bd_addr_additional_filter_accept_list", "")
    pts2.set_pixit("MESH", "TSPX_time_guard", "300000")
    pts2.set_pixit("MESH", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("MESH", "TSPX_tester_database_file",
                   r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_SMPP_db.xml")
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
        ("F465E43FF23D3F1B9DC7DFC04DA8758184DBC966204796ECCF0D6CF5E16500CC"
         "0201D048BCBBD899EEEFC424164E33C201C2B010CA6B4D43A8A155CAD8ECB279"))
    pts2.set_pixit("MESH", "TSPX_device_private_key",
                   "529AA0670D72CD6497502ED473502B037E8803B5C60829A5A3CAA219505530BA")
    pts2.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts2.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts2.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts2.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts2.set_pixit("MESH", "TSPX_vendor_model_id", "00000000")
    pts2.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "10")
    pts2.set_pixit("MESH", "TSPX_health_valid_test_ids", "00")
    pts2.set_pixit("MESH", "TSPX_iut_comp_data_page", "0")
    pts2.set_pixit("MESH", "TSPX_netkeyindex_value", "0")
    pts2.set_pixit("MESH", "TSPX_iut_supports_relay", "FALSE")
    pts2.set_pixit("MESH", "TSPX_application_key",
                   "3216D1509884B533248541792B877F98")
    pts2.set_pixit("MESH", "TSPX_device_key",
                   "00000000000000000000000000000000")
    pts2.set_pixit("MESH", "TSPX_enable_IUT_provisioner", "FALSE")
    pts2.set_pixit("MESH", "TSPX_maximum_number_of_supported_subnets", "1")


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

    oob = 16 * '00'
    out_size = random.randint(0, 2)
    rand_out_actions = random.choice(out_actions) if out_size else 0
    in_size = random.randint(0, 2)
    rand_in_actions = random.choice(in_actions) if in_size else 0
    crpl_size = 10  # Maximum capacity of the replay protection list
    auth_metod = 0x00
    pub_key = ("F465E43FF23D3F1B9DC7DFC04DA8758184DBC966204796ECCF0D6CF5E16500CC"
               "0201D048BCBBD899EEEFC424164E33C201C2B010CA6B4D43A8A155CAD8ECB279")
    priv_key = "529AA0670D72CD6497502ED473502B037E8803B5C60829A5A3CAA219505530BA"

    stack.gap_init(iut_device_name)
    stack.mesh_init(device_uuid, device_uuid2)

    common_pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_mesh),
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
        TestFunc(lambda: stack.mesh.set_iut_provisioner(True)),
        TestFunc(lambda: stack.mesh.expect_node(stack.mesh.get_dev_uuid())),
    ]

    pre_conditions_prov_pub_key = pre_conditions_prov + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
    ]

    pre_conditions_pub_priv_key = pre_conditions + [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_public_key", pub_key)),
        TestFunc(lambda: stack.mesh.pub_key_set(pub_key)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_private_key", priv_key)),
        TestFunc(lambda: stack.mesh.priv_key_set(priv_key))
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
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-04-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-20-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-23-C",
                  cmds=pre_conditions + [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(lambda: stack.mesh.set_prov_data(oob,
                            random.randint(1, 2), random.choice(out_actions),
                            in_size, rand_in_actions, crpl_size, auth_metod))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-02-C", cmds=pre_conditions +
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
                                                             random.randint(1, 2), defs.MESH_INPUT_NUMBER,
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
                                                                 1, 2), defs.MESH_INPUT_NUMBER,
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
    ]

    test_cases_lt2 = [
        ZTestCase("MESH", "MESH/SR/PROX/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BI-01-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-02-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-02-C", 361),
                             SynchPoint("MESH/SR/PROX/BV-02-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-02-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-03-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-03-C", 361),
                             SynchPoint("MESH/SR/PROX/BV-03-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-03-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-04-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-04-C", 367),
                             SynchPoint("MESH/SR/PROX/BV-04-C-LT2", 362)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-04-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-05-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-05-C", 367),
                             SynchPoint("MESH/SR/PROX/BV-05-C-LT2", 362)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-06-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-06-C", 361),
                             SynchPoint("MESH/SR/PROX/BV-06-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-06-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-08-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-08-C", 353),
                             SynchPoint("MESH/SR/PROX/BV-08-C-LT2", 17)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-08-C", 354),
                             SynchPoint("MESH/SR/PROX/BV-08-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-09-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-09-C", 361),
                             SynchPoint("MESH/SR/PROX/BV-09-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-09-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-10-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-10-C", 361),
                             SynchPoint("MESH/SR/PROX/BV-10-C-LT2", 17)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-10-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-12-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-12-C", 364),
                             SynchPoint("MESH/SR/PROX/BV-12-C-LT2", 366)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-12-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-13-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-13-C-LT2", 94, delay=5),
                             SynchPoint("MESH/SR/PROX/BV-13-C", 17, delay=20)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-13-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-14-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-14-C", 355),
                             SynchPoint("MESH/SR/PROX/BV-14-C-LT2", 356)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/PROX/BV-14-C", 357),
                             SynchPoint("MESH/SR/PROX/BV-14-C-LT2", 358)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-14-C-LT2"),

        ZTestCase("MESH", "MESH/SR/MPXS/BV-08-C", cmds=pre_conditions_lt2 +
                  [TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/SR/MPXS/BV-08-C", 12),
                             SynchPoint("MESH/SR/MPXS/BV-08-C-LT2", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/MPXS/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-05-C",
                  cmds=pre_conditions_lt2 +
                  [TestFunc(lambda: btp.mesh_lpn(True)),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 332),
                             SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 563, delay=5)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 333),
                             SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 560)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 303),
                             SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 561, delay=5)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 332),
                             SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 564, delay=5)]),
                   TestFunc(get_stack().synch.add_synch_element,
                            [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 333),
                             SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 562)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/CFG/HBP/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-05-C",
                  cmds=pre_conditions_lt2,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/CFG/HBS/BV-05-C-LT2"),
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
    ]

    test_cases_slaves = [
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-02-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-03-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-04-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-05-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-06-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-08-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-09-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-10-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-12-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-13-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-14-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BI-01-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/CFGCL/KR/BV-03-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/CFGCL/KR/BV-04-C-LT2",
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

    if len(ptses) == 2:
        tc_list += test_cases_slaves
        pts2 = ptses[1]

    return tc_list
