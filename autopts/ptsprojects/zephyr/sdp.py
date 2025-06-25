#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2025 NXP
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

"""SDP test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap

sdp_wid_hdl = get_wid_handler("zephyr", "sdp")


def set_pixits(ptses):
    """Setup SDP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    # Set SDP common PIXIT values
    pts.set_pixit("SDP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("SDP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("SDP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("SDP", "TSPX_class_of_device_pts", "200404")
    pts.set_pixit("SDP", "TSPX_pin_code", "0000")
    pts.set_pixit("SDP", "TSPX_time_guard", "200000")
    pts.set_pixit("SDP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("SDP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")

    pts.set_pixit("SDP", "TSPX_sdp_service_search_pattern", "0100")
    pts.set_pixit("SDP", "TSPX_sdp_unsupported_service", "EEEE")
    pts.set_pixit("SDP", "TSPX_sdp_additional_protocol_descriptor_list", "")
    pts.set_pixit("SDP", "TSPX_sdp_bluetooth_profile_descriptor_list", "")
    pts.set_pixit("SDP", "TSPX_sdp_browse_group_list", "")
    pts.set_pixit("SDP", "TSPX_sdp_client_exe_url", "")
    pts.set_pixit("SDP", "TSPX_sdp_documentation_url", "")
    pts.set_pixit("SDP", "TSPX_sdp_icon_url", "")
    pts.set_pixit("SDP", "TSPX_sdp_language_base_attribute_id_list", "")
    pts.set_pixit("SDP", "TSPX_sdp_protocol_descriptor_list", "")
    pts.set_pixit("SDP", "TSPX_sdp_provider_name", "")
    pts.set_pixit("SDP", "TSPX_sdp_service_availability", "")
    pts.set_pixit("SDP", "TSPX_sdp_service_data_base_state", "0100")
    pts.set_pixit("SDP", "TSPX_sdp_service_description", "")
    pts.set_pixit("SDP", "TSPX_sdp_service_id", "")
    pts.set_pixit("SDP", "TSPX_sdp_service_info_time_to_live", "")
    pts.set_pixit("SDP", "TSPX_sdp_version_number_list", "0100")
    pts.set_pixit("SDP", "TSPX_sdp_service_name", "")
    pts.set_pixit("SDP", "TSPX_sdp_service_record_state", "")
    pts.set_pixit("SDP", "TSPX_sdp_unsupported_attribute_id", "EEEE")


def test_cases(ptses):
    """
    Returns a list of SDP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()
    stack.gap_init(name=iut_device_name)

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.core_reg_svc_sdp),
        TestFunc(stack.sdp_init),
        TestFunc(lambda: pts.update_pixit_param(
                 "SDP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param("SDP", "TSPX_delete_link_key", "TRUE")),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
    ]

    custom_test_cases = [
    ]

    test_case_name_list = pts.get_test_case_list('SDP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('SDP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=sdp_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
