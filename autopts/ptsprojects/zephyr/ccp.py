#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

"""CCP test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr

ccp_wid_hdl = get_wid_handler("zephyr", "cpp")


def set_pixits(ptses):
    """Setup CCP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("CCP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("CCP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("CCP", "TSPX_time_guard", "180000")
    pts.set_pixit("CCP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("CCP", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_CCP_db.xml")
    pts.set_pixit("CCP", "TSPX_mtu_size", "23")
    pts.set_pixit("CCP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("CCP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("CCP", "TSPX_pin_code", "0000")
    pts.set_pixit("CCP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("CCP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("CCP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("CCP", "TSPX_iut_GAP_connection_role", "Peripheral")
    pts.set_pixit("CCP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")


def test_cases(ptses):
    """Returns a list of CCP test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param("CCP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_ccp),
        TestFunc(stack.ccp_init)]

    test_case_name_list = pts.get_test_case_list('CCP')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("CCP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=ccp_wid_hdl)

        tc_list.append(instance)

    return tc_list
