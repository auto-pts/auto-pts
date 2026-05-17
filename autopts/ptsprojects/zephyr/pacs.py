#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

"""PACS test cases"""

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.pacs_wid import pacs_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp


def set_pixits(ptses):
    """Setup PACS profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    """" Set only IXITs that require non-default value """
    pts.set_pixit("PACS", "TSPX_mtu_size", "60")
    pts.set_pixit("PACS", "TSPX_delete_ltk", "TRUE")


def test_cases(ptses):
    """Returns a list of PACS Server test cases"""

    pts = ptses[0]

    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "PACS", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.gap_set_gendiscov),
                      TestFunc(btp.core_reg_svc_pacs)]

    test_case_name_list = pts.get_test_case_list('PACS')
    tc_list = []

    for tc_name in test_case_name_list:
        instance = ZTestCase("PACS", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=pacs_wid_hdl)
        tc_list.append(instance)

    return tc_list
