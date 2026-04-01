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

"""DFU test cases"""

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

    """" Set only IXITs that require non-default value """
    pts.set_pixit("DFUM", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("DFUM", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("DFUM", "TSPX_device_uuid", "00000000000000000000000000000000")
    pts.set_pixit("DFUM", "TSPX_device_uuid2", "001BDC0810210B0E0A0C000B0E0A0C00")
    pts.set_pixit("DFUM", "TSPX_Client_BLOB_Data", r"data.txt")
    pts.set_pixit("DFUM", "TSPX_New_Firmware_Image", r"data2.txt")


def test_cases(ptses):
    """Returns a list of DFUM test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    if 'DFUM' not in pts.get_project_list():
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
    FD_timeout = 8
    timeout_base = 5

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
            "DFUM", "TSPX_device_uuid", stack.mesh.get_dev_uuid())),
        TestFunc(lambda: pts.update_pixit_param(
            "DFUM", "TSPX_device_uuid2", stack.mesh.get_dev_uuid_lt2())),
        TestFunc(lambda: pts.update_pixit_param(
            "DFUM", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "DFUM", "TSPX_Client_BLOB_Data",
            get_test_data_path(pts) + "sample_data_1.txt")),
        TestFunc(lambda: pts.update_pixit_param(
            "DFUM", "TSPX_New_Firmware_Image",
            get_test_data_path(pts) + "sample_data_1.txt")),
        TestFunc(lambda: pts.update_pixit_param(
            "DFUM", "TSPX_Server_Timeout_Base", timeout_base)),
        TestFunc(lambda: stack.mesh.timeout_base_set(timeout_base))]

    custom_test_cases = [
        ZTestCase("DFUM", "DFUM/SR/FD/BV-05-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_New_Firmware_Image",
                get_test_data_path(pts) + "sample_data_2.txt"))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FD/BV-07-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_Server_Timeout_Base", FD_timeout))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FD/BV-19-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_Server_Timeout_Base", FD_timeout))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FD/BV-48-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_Firmware_ID", "010000000100000000000000"))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FU/BV-24-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_New_Firmware_Image",
                get_test_data_path(pts) + "sample_data_2.txt"))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FU/BV-27-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_New_Firmware_Image",
                get_test_data_path(pts) + "sample_data_2.txt"))],
                  generic_wid_hdl=mmdl_wid_hdl),
        ZTestCase("DFUM", "DFUM/SR/FD/BV-13-C", cmds=pre_conditions + [
            TestFunc(lambda: pts.update_pixit_param(
                "DFUM", "TSPX_Server_Timeout_Base", FD_timeout))],
                 generic_wid_hdl=mmdl_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('DFUM')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('DFUM', tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=mmdl_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
