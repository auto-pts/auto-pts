#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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

"""TBS/GTBS test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap
from autopts.utils import ResultWithFlag

tbs_wid_hdl = get_wid_handler("zephyr", "tbs")


def set_pixits(ptses):
    """Setup TBS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("TBS", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("TBS", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("TBS", "TSPX_time_guard", "180000")
    pts.set_pixit("TBS", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("TBS", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("TBS", "TSPX_mtu_size", 23)
    pts.set_pixit("TBS", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("TBS", "TSPX_pin_code", "0000")
    pts.set_pixit("TBS", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("TBS", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("TBS", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("TBS", "TSPX_Signal_Strength_Reporting_Interval", 10)
    pts.set_pixit("TBS", "TSPX_Incoming_Call_Target_Caller_ID", "tel:+19991111234")
    pts.set_pixit("TBS", "TSPX_Incoming_friendly_name", "tel:+19991110011")
    pts.set_pixit("TBS", "TSPX_Outgoing_uri", "tel:+19991111234")
    pts.set_pixit("TBS", "TSPX_Outgoing_uri2", "tel:+19991111235")


def test_cases(ptses):
    """Returns a list of TBS Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "TBS", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: set_addr(
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.gap_set_io_cap, IOCap.display_only),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_tbs),
        TestFunc(lambda: pts.update_pixit_param(
            "TBS", "TSPX_iut_device_name_in_adv_packet_for_random_address", iut_device_name)),
        TestFunc(stack.tbs_init)
    ]

    test_case_name_list = pts.get_test_case_list('TBS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("TBS", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=tbs_wid_hdl)
        tc_list.append(instance)

    return tc_list
