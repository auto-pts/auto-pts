#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2022, Codecoup.
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

"""MMDL test cases"""

import random
from binascii import hexlify
from uuid import uuid4

from autopts.client import get_test_data_path, get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp, defs
from autopts.wid import mmdl_wid_hdl


def set_pixits(ptses):
    """Setup MMDL profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("MBTM", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("MBTM", "TSPX_time_guard", "300000")
    pts.set_pixit("MBTM", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("MBTM", "TSPX_tester_database_file",
                  r"C:\Program Files\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_SMPP_db.xml")
    pts.set_pixit("MBTM", "TSPX_mtu_size", "23")
    pts.set_pixit("MBTM", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("MBTM", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("MBTM", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("MBTM", "TSPX_iut_setup_att_over_br_edr", "FALSE")
    pts.set_pixit("MBTM", "TSPX_scan_interval", "30")
    pts.set_pixit("MBTM", "TSPX_scan_window", "30")
    pts.set_pixit("MBTM", "TSPX_scan_filter", "00")
    pts.set_pixit("MBTM", "TSPX_advertising_interval_min", "160")
    pts.set_pixit("MBTM", "TSPX_advertising_interval_max", "160")
    pts.set_pixit("MBTM", "TSPX_tester_OOB_information", "F87F")
    pts.set_pixit("MBTM", "TSPX_device_uuid", "00000000000000000000000000000000")
    pts.set_pixit("MBTM", "TSPX_device_uuid2", "001BDC0810210B0E0A0C000B0E0A0C00")
    pts.set_pixit("MBTM", "TSPX_use_pb_gatt_bearer", "FALSE")
    pts.set_pixit("MBTM", "TSPX_iut_comp_data_page", "2")
    pts.set_pixit("MBTM", "TSPX_oob_state_change", "FALSE")
    pts.set_pixit("MBTM", "TSPX_enable_IUT_provisioner", "FALSE")
    pts.set_pixit("MBTM", "TSPX_Procedure_Timeout", "60")
    pts.set_pixit("MBTM", "TSPX_Client_BLOB_ID", "1100000000000011")
    pts.set_pixit("MBTM", "TSPX_Client_BLOB_Data", r"data.txt")
    pts.set_pixit("MBTM", "TSPX_Server_Timeout_Base", "5")
    pts.set_pixit("MBTM", "TSPX_Client_Timeout_Base", "5")
    pts.set_pixit("MBTM", "TSPX_Transfer_TTL", "3")
    pts.set_pixit("MBTM", "TSPX_Firmware_ID", "11000011")
    pts.set_pixit("MBTM", "TSPX_Firmware_Metadata", "1100000000000011")
    pts.set_pixit("MBTM", "TSPX_Firmware_Update_URI", "http://www.dummy.com")
    pts.set_pixit("MBTM", "TSPX_New_Firmware_Image", r"data2.txt")
    pts.set_pixit("MBTM", "TSPX_Update_Firmware_Image_Index", "0")


def test_cases(ptses):
    """Returns a list of MBTM test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    if 'MBTM' not in pts.get_project_list():
        return []

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
    auth_method = 0x00
    iut_device_name = get_unique_name(pts)
    timeout_base = 5
    transfer_ttl = 3
    FD_timeout = 80

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_mesh),
        TestFunc(btp.mesh_init),
        TestFunc(btp.core_reg_svc_mmdl),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(stack.mesh_init, device_uuid, device_uuid2),
        TestFunc(lambda: stack.mesh.set_prov_data(oob, out_size, rand_out_actions, in_size,
                                                  rand_in_actions, crpl_size, auth_method)),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_device_uuid", stack.mesh.get_dev_uuid())),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_device_uuid2", stack.mesh.get_dev_uuid_lt2())),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_Client_BLOB_Data",
            get_test_data_path(pts) + "sample_data_1.txt")),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_New_Firmware_Image",
            get_test_data_path(pts) + "sample_data_1.txt")),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_Server_Timeout_Base", timeout_base)),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_Client_Timeout_Base", timeout_base)),
        TestFunc(lambda: stack.mesh.timeout_base_set(timeout_base)),
        TestFunc(lambda: pts.update_pixit_param(
            "MBTM", "TSPX_Transfer_TTL", transfer_ttl)),
        TestFunc(lambda: stack.mesh.transfer_ttl_set(transfer_ttl))]

    custom_test_cases = []

    test_case_name_list = pts.get_test_case_list('MBTM')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('MBTM', tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=mmdl_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
