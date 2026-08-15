#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.opp_wid import opp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp, defs
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    """Set PIXIT (parameter) values for OPP test cases.

    Args:
        ptses: List of PyPTS instances (at least one element).
    """
    pts = ptses[0]

    pts.set_pixit("OPP", "TSPX_time_guard", "300000")
    pts.set_pixit("OPP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("OPP", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("OPP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("OPP", "TSPX_no_confirmations", "FALSE")
    pts.set_pixit("OPP", "TSPX_pin_code", "0000")
    pts.set_pixit("OPP", "TSPX_auth_password", "0000")
    pts.set_pixit("OPP", "TSPX_auth_user_id", "PTS")
    pts.set_pixit("OPP", "TSPX_supported_extension", ".bmp")
    pts.set_pixit("OPP", "TSPX_unsupported_extension", ".pts")


def test_cases(ptses):
    """Return a list of OPP test cases.

    Args:
        ptses: List of PyPTS instances (at least one element).

    Returns:
        List of ZTestCase objects for all OPP test cases in the workspace.
    """
    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
            "OPP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_sdp),
        TestFunc(stack.sdp_init),
        TestFunc(btp.core_reg_svc_rfcomm),
        TestFunc(stack.rfcomm_init),
        TestFunc(btp.core_reg_svc_opp),
        TestFunc(stack.opp_init),
    ]

    pre_conditions_client = [
        TestFunc(btp.gap_unpair, pts_bd_addr, defs.BTP_BR_ADDRESS_TYPE),
    ]

    pre_conditions_server = [
        TestFunc(btp.gap_unpair, pts_bd_addr, defs.BTP_BR_ADDRESS_TYPE),
        TestFunc(btp.opp_server_register),
        TestFunc(btp.gap_set_general_discoverable),
    ]

    custom_test_cases = [
        ZTestCase("OPP", "OPP/SR/OPH/BV-22-C",
                  pre_conditions + pre_conditions_server +
                  [TestFunc(lambda: pts.set_pixit("OPP", "TSPX_time_guard", "1200000")),
                   TestFunc(lambda: pts.set_call_timeout(1200000))],
                  generic_wid_hdl=opp_wid_hdl),
        ZTestCase("OPP", "OPP/CL/OPH/BV-22-C",
                  pre_conditions + pre_conditions_client +
                  [TestFunc(lambda: pts.set_pixit("OPP", "TSPX_time_guard", "1200000")),
                   TestFunc(lambda: pts.set_call_timeout(1200000))],
                  generic_wid_hdl=opp_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('OPP')
    tc_list = []

    for tc_name in test_case_name_list:
        _pre_conditions = pre_conditions

        if tc_name.startswith('OPP/SR/OPH') or tc_name.startswith('OPP/SR/BC'):
            _pre_conditions = pre_conditions + pre_conditions_server

        if tc_name.startswith('OPP/CL'):
            _pre_conditions = pre_conditions + pre_conditions_client

        instance = ZTestCase('OPP', tc_name, cmds=_pre_conditions,
                             generic_wid_hdl=opp_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
