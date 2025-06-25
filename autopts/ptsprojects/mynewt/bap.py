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

"""BAP test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.common_wid import get_wid_handler
from autopts.ptsprojects.mynewt.ztestcase import ZTestCase
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.pybtp import btp
from autopts.pybtp.types import Addr
from autopts.utils import ResultWithFlag

bap_wid_hdl = get_wid_handler("mynewt", "bap")
broadcast_code = '0102680553F1415AA265BBAFC6EA03B8'


def set_pixits(ptses):
    """Setup BAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("BAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("BAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("BAP", "TSPX_time_guard", "180000")
    pts.set_pixit("BAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("BAP", "TSPX_mtu_size", "64")
    pts.set_pixit("BAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("BAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("BAP", "TSPX_pin_code", "0000")
    pts.set_pixit("BAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("BAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("BAP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("BAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("BAP", "TSPX_VS_Codec_ID", "ffff")
    pts.set_pixit("BAP", "TSPX_VS_Company_ID", "ffff")
    pts.set_pixit("BAP", "TSPX_broadcast_code", broadcast_code)

    if len(ptses) < 2:
        return

    pts2 = ptses[1]
    pts2.set_pixit("BAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts2.set_pixit("BAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts2.set_pixit("BAP", "TSPX_time_guard", "180000")
    pts2.set_pixit("BAP", "TSPX_use_implicit_send", "TRUE")
    pts2.set_pixit("BAP", "TSPX_mtu_size", "64")
    pts2.set_pixit("BAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts2.set_pixit("BAP", "TSPX_delete_link_key", "FALSE")
    pts2.set_pixit("BAP", "TSPX_pin_code", "0000")
    pts2.set_pixit("BAP", "TSPX_use_dynamic_pin", "FALSE")
    pts2.set_pixit("BAP", "TSPX_delete_ltk", "TRUE")
    pts2.set_pixit("BAP", "TSPX_security_enabled", "FALSE")
    pts2.set_pixit("BAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts2.set_pixit("BAP", "TSPX_VS_Codec_ID", "ffff")
    pts2.set_pixit("BAP", "TSPX_VS_Company_ID", "ffff")
    pts2.set_pixit("BAP", "TSPX_broadcast_code", broadcast_code)


def test_cases(ptses):
    """Returns a list of BAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
                      TestFunc(stack.gatt_init),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.core_reg_svc_bap),
                      TestFunc(stack.bap_init),
                      TestFunc(lambda: stack.bap.set_broadcast_code(broadcast_code)),
                      TestFunc(lambda: set_addr(
                          stack.gap.iut_addr_get_str())),
                      ]

    test_case_name_list = pts.get_test_case_list('BAP')
    tc_list = []
    custom_test_cases = [

        ]

    for tc_name in test_case_name_list:
        instance = ZTestCase("BAP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=bap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
