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

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave

except ImportError:  # running this module as script
    import sys
    import os
    # to be able to locate the following imports
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../..")

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave


from pybtp import defs, btp
from pybtp.types import MeshVals
from ptsprojects.stack import get_stack
from ptsprojects.stack import SynchPoint
from wid import mesh_wid_hdl
from uuid import uuid4
from binascii import hexlify
import random
from time import sleep


device_uuid = hexlify(uuid4().bytes)
device_uuid2 = hexlify(uuid4().bytes)


def set_pixits(ptses):
    """Setup MESH profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    pts -- Instance of PyPTS"""

    pts = ptses[0]

    pts.set_pixit("MESH", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("MESH", "TSPX_bd_addr_additional_whitelist", "")
    pts.set_pixit("MESH", "TSPX_time_guard", "300000")
    pts.set_pixit("MESH", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("MESH", "TSPX_tester_database_file",
                  "C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_SMPP_db.xml")
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
    pts.set_pixit("MESH", "TSPX_device_uuid", device_uuid)
    pts.set_pixit("MESH", "TSPX_device_uuid2", device_uuid2)
    pts.set_pixit("MESH", "TSPX_device_public_key",
                  "F465E43FF23D3F1B9DC7DFC04DA8758184DBC966204796ECCF0D6CF5E16500CC0201D048BCBBD899EEEFC424164E33C201C2B010CA6B4D43A8A155CAD8ECB279")
    pts.set_pixit("MESH", "TSPX_device_private_key",
                  "529AA0670D72CD6497502ED473502B037E8803B5C60829A5A3CAA219505530BA")
    pts.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts.set_pixit("MESH", "TSPX_vendor_model_id", "ffff1234")
    pts.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "2")
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
    pts2.set_pixit("MESH", "TSPX_bd_addr_additional_whitelist", "")
    pts2.set_pixit("MESH", "TSPX_time_guard", "300000")
    pts2.set_pixit("MESH", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("MESH", "TSPX_tester_database_file",
                   "C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_SMPP_db.xml")
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
    pts2.set_pixit("MESH", "TSPX_device_uuid", device_uuid2)
    pts2.set_pixit("MESH", "TSPX_device_uuid2", device_uuid)
    pts2.set_pixit("MESH", "TSPX_device_public_key",
                   "F465E43FF23D3F1B9DC7DFC04DA8758184DBC966204796ECCF0D6CF5E16500CC0201D048BCBBD899EEEFC424164E33C201C2B010CA6B4D43A8A155CAD8ECB279")
    pts2.set_pixit("MESH", "TSPX_device_private_key",
                   "529AA0670D72CD6497502ED473502B037E8803B5C60829A5A3CAA219505530BA")
    pts2.set_pixit("MESH", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts2.set_pixit("MESH", "TSPX_iut_model_id_used", "0002")
    pts2.set_pixit("MESH", "TSPX_OOB_code", "00000000000000000102030405060708")
    pts2.set_pixit("MESH", "TSPX_subscription_address_list", "C302")
    pts2.set_pixit("MESH", "TSPX_vendor_model_id", "00000000")
    pts2.set_pixit("MESH", "TSPX_maximum_network_message_cache_entries", "2")
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
    pts -- Instance of PyPTS"""

    pts = ptses[0]

    stack = get_stack()
    pts_bd_addr = pts.q_bd_addr

    out_actions = [defs.MESH_OUT_DISPLAY_NUMBER,
                   defs.MESH_OUT_DISPLAY_STRING,
                   defs.MESH_OUT_DISPLAY_NUMBER | defs.MESH_OUT_DISPLAY_STRING]
    in_actions = [defs.MESH_IN_ENTER_NUMBER,
                  defs.MESH_IN_ENTER_STRING,
                  defs.MESH_IN_ENTER_NUMBER | defs.MESH_IN_ENTER_STRING]

    oob = 16 * '0'
    out_size = random.randint(0, 2)
    rand_out_actions = random.choice(out_actions) if out_size else 0
    in_size = random.randint(0, 2)
    rand_in_actions = random.choice(in_actions) if in_size else 0
    crpl_size = 10  # Maximum capacity of the replay protection list

    stack.gap_init()
    stack.mesh_init(device_uuid, oob, out_size, rand_out_actions, in_size,
                    rand_in_actions, crpl_size)

    pre_conditions = [
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
            MeshVals.subscription_addr_list1))]

    pre_conditions_slave = [
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str()))]

    test_cases = [
        ZTestCase("MESH", "MESH/NODE/BCN/SNB/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGF/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGF/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGR/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGR/BV-01-C", cmds=pre_conditions +
                  [TestFunc(lambda: pts.update_pixit_param(
                   "MESH", "TSPX_iut_supports_relay", "TRUE"))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/COMP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/DTTL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/DTTL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NTX/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/RST/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SNBP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SNBP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/LPNPT/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-02-C", cmds=pre_conditions,
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
        ZTestCase("MESH", "MESH/NODE/KR/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-12-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-14-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-15-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(stack.mesh_init, device_uuid, oob,
                            random.randint(1, 2), random.choice(out_actions),
                            in_size, rand_in_actions, crpl_size)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BV-12-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-05-C", cmds=pre_conditions,
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
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-12-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/ATS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/CFS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/CFS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/HPS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-09-C", cmds=pre_conditions +
                  [TestFunc(lambda: get_stack().mesh.proxy_identity_enable())],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-15-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
    ]

    if len(ptses) < 2:
        return test_cases

    pts2 = ptses[1]

    test_cases_lt2 = [
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-05-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                           "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(lambda: btp.mesh_lpn(True)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 332),
                                  SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 563, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 333),
                                  SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 560, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 303),
                                  SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 561, delay=20)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 332),
                                  SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 564, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/CFG/HBP/BV-05-C", 333),
                                  SynchPoint("MESH/NODE/CFG/HBP/BV-05-C-LT2", 562, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/CFG/HBP/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-05-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                           "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid))],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/CFG/HBS/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BI-01-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-02-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-03-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-04-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-06-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-09-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-10-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-12-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-12-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-13-C-LT2"),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-08-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                           "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid))],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/MPXS/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/SR/PROX/BV-14-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/SR/PROX/BV-14-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BI-01-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BI-01-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BI-02-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BI-02-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BI-03-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BI-03-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-01-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-01-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-02-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 342, delay=10)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 319, delay=15),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-02-C", 302)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 319, delay=15),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-02-C", 302)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 319, delay=15),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-02-C", 302)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-02-C-LT2", 319, delay=15),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-02-C", 302)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-02-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-03-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-03-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-03-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-03-C-LT2", 319),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-03-C", 302, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-03-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-04-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.mesh_iv_test_mode_autoinit),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-04-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-04-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-04-C-LT2", 311),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-04-C", 305, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-04-C-LT2", 255),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-04-C", 305, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-04-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-05-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-05-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-05-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-05-C-LT2", 342),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-05-C", 302, delay=2)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-05-C-LT2", 344),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-05-C", 302, delay=2)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-05-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-06-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-06-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-06-C-LT2", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-06-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-07-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-07-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-08-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-08-C-LT2", 15),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-08-C", 337, 1)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-08-C-LT2", 319, delay=1),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-08-C", 302, 30)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-08-C-LT2", 319, delay=2),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-08-C", 302, 30)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-08-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-09-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-09-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-09-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-09-C", 310),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-09-C-LT2", 319)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-09-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-10-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-10-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-10-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-10-C-LT2", 319),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-10-C", 341, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-10-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-11-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-11-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-11-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-11-C-LT2", 324),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-11-C", 337)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-11-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-12-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-12-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-12-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-12-C-LT2", 330),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-12-C", 335, delay=10)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-12-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-13-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-13-C", 6),
                                  SynchPoint("MESH/NODE/FRND/TWO_NODES_PROVISIONER", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/TWO_NODES_PROVISIONER"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-14-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-14-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-14-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-14-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-14-C-LT2", 283)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-14-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-14-C-LT2", 282)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-14-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-14-C-LT2", 339)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-14-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-15-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.mesh_iv_test_mode_autoinit),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-15-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-15-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-15-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-15-C-LT2", 283)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-15-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-15-C-LT2", 282)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-15-C", 339),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-15-C-LT2", 339)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-15-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-16-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-16-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-16-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-16-C-LT2", 319),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-16-C", 302, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-16-C-LT2", 319),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-16-C", 302, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-16-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-17-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(sleep, 10, start_wid=318),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-17-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-17-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-17-C-LT2", 319),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-17-C", 302, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-17-C-LT2", 318),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-17-C", 302, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-17-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-18-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-18-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-18-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-18-C-LT2", 317),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-18-C", 302, delay=2)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-18-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-19-C",
                  cmds=pre_conditions +
                       [TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-19-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-19-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-19-C", 302),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-19-C-LT2", 318, delay=10)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-19-C", 302),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-19-C-LT2", 318, delay=10)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-19-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-20-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.mesh_iv_test_mode_autoinit),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-20-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-20-C-LT2", 13)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-20-C-LT2", 267),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-20-C", 348, delay=5)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-20-C-LT2", 311),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-20-C", 345, delay=5)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-20-C-LT2"),
        ZTestCase("MESH", "MESH/NODE/FRND/FN/BV-21-C",
                  cmds=pre_conditions +
                       [TestFunc(btp.mesh_iv_test_mode_autoinit),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid", device_uuid2)),
                        TestFunc(lambda: pts.update_pixit_param(
                            "MESH", "TSPX_device_uuid2", device_uuid)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/NODE/FRND/FN/BV-21-C", 6),
                                  SynchPoint("MESH/NODE/FRND/FN/BV-21-C-LT2", 13)])],
                  generic_wid_hdl=mesh_wid_hdl,
                  lt2="MESH/NODE/FRND/FN/BV-21-C-LT2"),
    ]

    test_cases_slaves = [
        ZTestCaseSlave("MESH", "MESH/SR/MPXS/BV-08-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                        TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2)),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/MPXS/BV-08-C", 12),
                                  SynchPoint("MESH/SR/MPXS/BV-08-C-LT2", 13)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-02-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-02-C", 361),
                                  SynchPoint("MESH/SR/PROX/BV-02-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-03-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-03-C", 361),
                                  SynchPoint("MESH/SR/PROX/BV-03-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-04-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-04-C", 367),
                                  SynchPoint("MESH/SR/PROX/BV-04-C-LT2", 362)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-05-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-05-C", 367),
                                  SynchPoint("MESH/SR/PROX/BV-05-C-LT2", 362)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-06-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-06-C", 361),
                                  SynchPoint("MESH/SR/PROX/BV-06-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-08-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-08-C", 353),
                                  SynchPoint("MESH/SR/PROX/BV-08-C-LT2", 17)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-08-C", 354),
                                  SynchPoint("MESH/SR/PROX/BV-08-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-09-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-09-C", 361),
                                  SynchPoint("MESH/SR/PROX/BV-09-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-10-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-10-C", 361),
                                  SynchPoint("MESH/SR/PROX/BV-10-C-LT2", 17)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-12-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-12-C", 364),
                                  SynchPoint("MESH/SR/PROX/BV-12-C-LT2", 366)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-13-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-13-C-LT2", 94, delay=5),
                                  SynchPoint("MESH/SR/PROX/BV-13-C", 17, delay=20)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-14-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-14-C", 355),
                                  SynchPoint("MESH/SR/PROX/BV-14-C-LT2", 356)]),
                        TestFunc(get_stack().synch.add_synch_element,
                                 [SynchPoint("MESH/SR/PROX/BV-14-C", 357),
                                  SynchPoint("MESH/SR/PROX/BV-14-C-LT2", 358)])],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BI-01-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/CFG/HBP/BV-05-C-LT2",
                  cmds=pre_conditions_slave +
                       [TestFunc(lambda: pts2.update_pixit_param(
                           "MESH", "TSPX_device_uuid", device_uuid)),
                        TestFunc(lambda: pts2.update_pixit_param(
                           "MESH", "TSPX_device_uuid2", device_uuid2))],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/CFG/HBS/BV-05-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-02-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-03-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-04-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-05-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-06-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-08-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-09-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-10-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-11-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-12-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-14-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-15-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-16-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-17-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-18-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-19-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-20-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/FN/BV-21-C-LT2",
                       cmds=pre_conditions_slave +
                            [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                             TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/NODE/FRND/TWO_NODES_PROVISIONER",
                       cmds=pre_conditions_slave +
                       [TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid", device_uuid)),
                        TestFunc(lambda: pts2.update_pixit_param(
                                 "MESH", "TSPX_device_uuid2", device_uuid2))],
                       generic_wid_hdl=mesh_wid_hdl),
    ]

    return test_cases + test_cases_lt2 + test_cases_slaves


def main():
    """Main."""
    import ptsprojects.zephyr.iutctl as iutctl

    class pts:
        pass

    pts.q_bd_addr = "AB:CD:EF:12:34:56"

    iutctl.init_stub()

    test_cases_ = test_cases(pts)

    for test_case in test_cases_:
        print()
        print(test_case)

        if test_case.edit1_wids:
            print(("edit1_wids: %r" % test_case.edit1_wids))

        if test_case.verify_wids:
            print(("verify_wids: %r" % test_case.verify_wids))

        for index, cmd in enumerate(test_case.cmds):
            print(("%d) %s" % (index, cmd)))


if __name__ == "__main__":
    main()
