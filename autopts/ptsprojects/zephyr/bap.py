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

"""BAP test cases"""

from queue import Queue

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.bap_wid import bap_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp.types import Addr, AdType, UUID, AdFlags


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
    pts.set_pixit("BAP", "TSPX_Step_Size", "1")
    pts.set_pixit("BAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("BAP", "TSPX_VS_Codec_ID", "ffff")
    pts.set_pixit("BAP", "TSPX_VS_Company_ID", "ffff")


def test_cases(ptses):
    """Returns a list of BAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # The Unicast Server shall transmit connectable extended advertising PDUs
    # that contain the Service Data AD data type, including additional
    # service data defined in BAP_v1.0.1, 3.5.3, Table 3.7.
    ad = {
        AdType.name_full: iut_device_name[::1].hex(),
        AdType.flags: format(AdFlags.br_edr_not_supp |
                             AdFlags.le_gen_discov_mode, '02x'),
        AdType.uuid16_all: bytes.fromhex(UUID.ASCS)[::-1].hex(),
        AdType.uuid16_svc_data: '4e1801ff0fff0f00',
    }

    queue = Queue()

    def set_addr(addr):
        queue.put(addr)

    pre_conditions = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(stack.gap_init, iut_device_name),
                      TestFunc(btp.gap_read_ctrl_info),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_bd_addr_iut",
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: set_addr(
                          stack.gap.iut_addr_get_str())),
                      TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_iut_use_dynamic_bd_addr",
                          "TRUE" if stack.gap.iut_addr_is_random()
                          else "FALSE")),
                      TestFunc(btp.core_reg_svc_gatt),
                      TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
                      TestFunc(stack.gatt_init),
                      TestFunc(btp.gap_set_conn),
                      TestFunc(btp.gap_set_gendiscov),
                      TestFunc(btp.core_reg_svc_pacs),
                      TestFunc(btp.core_reg_svc_ascs),
                      TestFunc(btp.core_reg_svc_bap),
                      TestFunc(stack.ascs_init),
                      TestFunc(stack.bap_init), ]

    pre_conditions_server = pre_conditions + [
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(lambda: btp.gap_adv_ind_on(ad=ad)),
    ]

    custom_test_cases = [
        # Errata in progress since the PTS should use
        # TSPX_VS_Company_ID and TSPX_VS_Codec_ID instead.
        ZTestCase("BAP", "BAP/UCL/SCC/BV-033-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/UCL/SCC/BV-034-C",
                  cmds=pre_conditions +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-033-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-034-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-067-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-068-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-133-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/USR/SCC/BV-134-C",
                  cmds=pre_conditions_server +
                         [TestFunc(lambda: pts.update_pixit_param(
                          "BAP", "TSPX_Codec_ID", "ffffffffff"))],
                  generic_wid_hdl=bap_wid_hdl),
        ZTestCase("BAP", "BAP/UCL/STR/BV-526-C", cmds=pre_conditions,
                  generic_wid_hdl=bap_wid_hdl,
                  lt2="BAP/UCL/STR/BV-526-C_LT2"),
    ]

    test_case_name_list = pts.get_test_case_list('BAP')
    tc_list = []

    for tc_name in test_case_name_list:
        if tc_name.startswith('BAP/USR'):
            # Missing MMI 20001, errata in progress
            _pre_conditions = pre_conditions_server
        else:
            _pre_conditions = pre_conditions

        instance = ZTestCase("BAP", tc_name,
                             cmds=_pre_conditions,
                             generic_wid_hdl=bap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
                        TestFunc(lambda: pts2.update_pixit_param(
                                "BAP", "TSPX_bd_addr_iut", queue.get())),
                        TestFunc(lambda: pts2.update_pixit_param(
                                "BAP", "TSPX_iut_use_dynamic_bd_addr",
                                "TRUE" if stack.gap.iut_addr_is_random() else "FALSE"))
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("BAP", "BAP/UCL/STR/BV-526-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=bap_wid_hdl),
    ]

    return tc_list + test_cases_lt2
