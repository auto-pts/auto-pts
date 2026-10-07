#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, NXP.
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

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import FtpInfo, get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ftp_wid import ftp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("FTP", "TSPX_time_guard", "300000")
    pts.set_pixit("FTP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("FTP", "TSPX_override_pts_folder", "FALSE")
    pts.set_pixit("FTP", "TSPX_client_class_of_device", "000000")
    pts.set_pixit("FTP", "TSPX_working_folder_path", "pts")
    pts.set_pixit("FTP", "TSPX_non_browsable_folder_path", "nonbrowsable")
    pts.set_pixit("FTP", "TSPX_server_class_of_device", "000000")
    pts.set_pixit("FTP", "TSPX_supported_file_extensions", ".txt")
    pts.set_pixit("FTP", "TSPX_auth_password", "ftp")
    pts.set_pixit("FTP", "TSPX_l2cap_psm", "1003")
    pts.set_pixit("FTP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("FTP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("FTP", "TSPX_pin_code", "1234")


def test_cases(ptses):
    """
    Returns a list of FTP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "FTP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_ftp),
        TestFunc(stack.ftp_init),
        TestFunc(btp.gap_set_connectable),
        TestFunc(btp.gap_set_general_discoverable),
    ]

    # Custom test cases that need special pre-conditions.
    custom_test_cases = [
        ZTestCase("FTP", "FTP/SR/GOEP/SRMP/BV-03-C",
                  pre_conditions +
                  [TestFunc(lambda: stack.ftp.set_pre_conditions(FtpInfo.LOCAL_SRMP, 1))],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/SR/OMA/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.ftp_set_read_only)],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/SR/OMA/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.ftp_set_read_only)],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/SR/OTR/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.ftp_set_read_only)],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/SR/OTR/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.ftp_set_read_only)],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/SR/FBR/BV-08-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.update_pixit_param("FTP", "TSPX_non_browsable_folder_path", "nonbrowsable")),
                  TestFunc(btp.ftp_create_folder, "nonbrowsable", 0x000000)],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/CL/OTR/BV-08-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("FTP", "TSPX_time_guard", "600000")),
                  TestFunc(lambda: pts.set_call_timeout(600000))],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/CL/OTR/BV-13-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("FTP", "TSPX_time_guard", "600000")),
                  TestFunc(lambda: pts.set_call_timeout(600000))],
                  generic_wid_hdl=ftp_wid_hdl),
        ZTestCase("FTP", "FTP/CL/OTR/BV-14-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("FTP", "TSPX_time_guard", "600000")),
                  TestFunc(lambda: pts.set_call_timeout(600000))],
                  generic_wid_hdl=ftp_wid_hdl),
       ZTestCase("FTP", "FTP/SR/OTR/BV-13-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("FTP", "TSPX_time_guard", "600000")),
                  TestFunc(lambda: pts.set_call_timeout(600000))],
                  generic_wid_hdl=ftp_wid_hdl),
       ZTestCase("FTP", "FTP/SR/OTR/BV-14-C",
                  pre_conditions +
                  [TestFunc(lambda: pts.set_pixit("FTP", "TSPX_time_guard", "600000")),
                  TestFunc(lambda: pts.set_call_timeout(600000))],
                  generic_wid_hdl=ftp_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('FTP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('FTP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=ftp_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
