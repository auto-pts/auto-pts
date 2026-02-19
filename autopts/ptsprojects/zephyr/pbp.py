#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Nordic Semiconductor ASA.
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
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.utils import ResultWithFlag

pbp_wid_hdl = get_wid_handler("zephyr", "pbp")

PROGRAM_INFO = '00112233445566778899AABBCCDDEEFF'
BROADCAST_CODE = '0102680553F1415AA265BBAFC6EA03B8'
BROADCAST_NAME = 'Broadcaster'


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("PBP", "TSPX_time_guard", "180000")
    pts.set_pixit("PBP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("PBP", "TSPX_broadcast_code", BROADCAST_CODE)
    pts.set_pixit("PBP", "TSPX_Program_Info", PROGRAM_INFO)
    pts.set_pixit("PBP", "TSPX_Broadcast_Name", BROADCAST_NAME)


def test_cases(ptses):
    """
    Returns a list of PBP test cases
    ptses -- list of PyPTS instances
    """

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
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_pbp),
        TestFunc(stack.pbp_init),
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(lambda: stack.bap.set_broadcast_code(BROADCAST_CODE)),
        TestFunc(lambda: stack.pbp.set_program_info(PROGRAM_INFO)),
        TestFunc(lambda: stack.pbp.set_broadcast_name(BROADCAST_NAME)),
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),

        TestFunc(lambda: pts.update_pixit_param("PBP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str()))
    ]

    test_case_name_list = pts.get_test_case_list('PBP')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('PBP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=pbp_wid_hdl)

        tc_list.append(instance)

    return tc_list
