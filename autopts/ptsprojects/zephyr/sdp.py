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

"""SDP test cases"""

from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.ptsprojects.zephyr.sdp_wid import sdp_wid_hdl


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
    pts.set_pixit("SDP", "TSPX_class_of_device_test_pts_initiator", "TRUE")
    pts.set_pixit("SDP", "TSPX_limited_inquiry_used", "FALSE")
    pts.set_pixit("SDP", "TSPX_pin_code", "0000")
    pts.set_pixit("SDP", "TSPX_time_guard", "200000")
    pts.set_pixit("SDP", "TSPX_device_search_time", "20")
    pts.set_pixit("SDP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("SDP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")

    pts.set_pixit("SDP", "TSPX_sdp_service_search_pattern", "0100")
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
    """Returns a list of SDP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()
    iut_device_name = get_unique_name(pts)
    stack.gap_init(name=iut_device_name)

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(btp.core_reg_svc_sdp),
                      TestFunc(stack.sdp_init),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SDP", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "SDP", "TSPX_delete_link_key", "TRUE")),
                      # FIXME Find better place to store PTS bdaddr
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)]

    custom_test_cases = [
        ZTestCase("SDP", "SDP/SR/SS/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SS/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SS/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SS/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BI-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-20-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-05-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-10-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-11-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-12-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-13-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-14-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-15-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-16-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-17-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-18-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-19-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SA/BV-21-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-03-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-04-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-06-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-10-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-11-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-07-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-09-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-12-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-13-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-14-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-15-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-16-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-17-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-18-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-19-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-08-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-20-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-21-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-22-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BV-23-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BI-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/SSA/BI-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/BRW/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/SR/BRW/BV-02-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/CL/SA/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(lambda: pts.update_pixit_param(
                          "SDP", "TSPX_class_of_device_test_pts_initiator", "FALSE")),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
        ZTestCase("SDP", "SDP/CL/SSA/BV-01-C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
                   TestFunc(lambda: pts.update_pixit_param(
                          "SDP", "TSPX_class_of_device_test_pts_initiator", "FALSE")),
                   TestFunc(lambda: btp.gap_set_conn()),
                   TestFunc(lambda: btp.gap_set_bondable_off()),
                   TestFunc(lambda: btp.gap_set_gendiscov()),],
                  generic_wid_hdl=sdp_wid_hdl),
    ]

    test_case_name_list = pts.get_test_case_list('SDP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase('SDP', tc_name,
                             pre_conditions +
                             [TestFunc(btp.gap_set_io_cap, IOCap.display_only)],
                             generic_wid_hdl=sdp_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
