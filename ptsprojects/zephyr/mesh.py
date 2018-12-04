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

"""MESH test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave

except ImportError:  # running this module as script
    import sys
    import os
    # to be able to locate the following imports
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../..")

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase, ZTestCaseSlave


from pybtp import defs, btp
from pybtp.types import MeshVals
from ptsprojects.stack import get_stack
from ptsprojects.zephyr.mesh_wid import mesh_wid_hdl
from uuid import uuid4
from binascii import hexlify
import random


def test_cases(ptses):
    """Returns a list of MESH test cases
    pts -- Instance of PyPTS"""

    pts = ptses[0]
    pts2 = ptses[1]

    stack = get_stack()
    pts_bd_addr = pts.q_bd_addr

    out_actions = [defs.MESH_OUT_DISPLAY_NUMBER,
                   defs.MESH_OUT_DISPLAY_STRING,
                   defs.MESH_OUT_DISPLAY_NUMBER | defs.MESH_OUT_DISPLAY_STRING]
    in_actions = [defs.MESH_IN_ENTER_NUMBER,
                  defs.MESH_IN_ENTER_STRING,
                  defs.MESH_IN_ENTER_NUMBER | defs.MESH_IN_ENTER_STRING]

    device_uuid = hexlify(uuid4().bytes)
    device_uuid2 = hexlify(uuid4().bytes)
    oob = 16 * '0'
    out_size = random.randint(0, 2)
    rand_out_actions = random.choice(out_actions) if out_size else 0
    in_size = random.randint(0, 2)
    rand_in_actions = random.choice(in_actions) if in_size else 0
    crpl_size = 10  # Maximum capacity of the replay protection list

    stack.gap_init()
    stack.mesh_init(device_uuid, oob, out_size, rand_out_actions, in_size,
                    rand_in_actions, crpl_size)

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.core_reg_svc_mesh),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid", device_uuid)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_subscription_address_list",
            MeshVals.subscription_addr_list1)),
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_device_uuid2", device_uuid2))]

    pre_conditions_slave = [
        TestFunc(lambda: pts.update_pixit_param(
            "MESH", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts2.update_pixit_param(
            "MESH", "TSPX_device_uuid", device_uuid2))]

    test_cases = [
        ZTestCase("MESH", "MESH/NODE/BCN/SNB/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/AKL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGF/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGF/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGR/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/CFGR/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/COMP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/DTTL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/DTTL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/GPXY/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBP/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/HBS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MAKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/MP/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NID/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NKL/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/NTX/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/RST/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BI-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SL/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SNBP/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/CFG/SNBP/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/FRND/LPN/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BI-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/IVU/BV-05-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_iv_test_mode_autoinit)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BI-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/KR/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/MPS/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/NET/BV-14-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BI-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PBADV/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/UPD/BV-01-C",
                  cmds=pre_conditions +
                  [TestFunc(stack.mesh_init, device_uuid, oob,
                            random.randint(1, 2), random.choice(out_actions),
                            in_size, rand_in_actions, crpl_size)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/UPD/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/UPD/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/UPD/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/PROV/UPD/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/RLY/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-06-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-07-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-08-C", cmds=pre_conditions +
                  [TestFunc(btp.mesh_store_net_data)],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-12-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/NODE/TNPT/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/ATS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/CFS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/CFS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/HPS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BI-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/HM/RFS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/MPXS/BV-09-C", cmds=pre_conditions +
                  [TestFunc(lambda: get_stack().mesh.proxy_identity_enable())],
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BI-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-01-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-02-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-03-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-04-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-05-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-06-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-07-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-08-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-09-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-10-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-11-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-12-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-13-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
        ZTestCase("MESH", "MESH/SR/PROX/BV-14-C", cmds=pre_conditions,
                  generic_wid_hdl=mesh_wid_hdl),
    ]

    additional_test_cases = [
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-02-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-02-C", 361),
                                  ("MESH/SR/PROX/BV-02-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-03-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-03-C", 361),
                                  ("MESH/SR/PROX/BV-03-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-04-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-04-C", 367),
                                  ("MESH/SR/PROX/BV-04-C-LT2", 362)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-05-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-05-C", 367),
                                  ("MESH/SR/PROX/BV-05-C-LT2", 362)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-06-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-06-C", 361),
                                  ("MESH/SR/PROX/BV-06-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-08-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-08-C", 353),
                                  ("MESH/SR/PROX/BV-08-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-09-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-09-C", 361),
                                  ("MESH/SR/PROX/BV-09-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-10-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-10-C", 361),
                                  ("MESH/SR/PROX/BV-10-C-LT2", 17)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-12-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-12-C", 364),
                                  ("MESH/SR/PROX/BV-12-C-LT2", 366)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-13-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BV-14-C-LT2",
                       cmds=pre_conditions_slave +
                       [TestFunc(get_stack().synch.add_synch_element,
                                 (("MESH/SR/PROX/BV-14-C", 355),
                                  ("MESH/SR/PROX/BV-14-C-LT2", 356)))],
                       generic_wid_hdl=mesh_wid_hdl),
        ZTestCaseSlave("MESH", "MESH/SR/PROX/BI-01-C-LT2",
                       cmds=pre_conditions_slave,
                       generic_wid_hdl=mesh_wid_hdl),
    ]

    return test_cases, additional_test_cases


def main():
    """Main."""
    import ptsprojects.zephyr.iutctl as iutctl

    class pts:
        pass

    pts.q_bd_addr = "AB:CD:EF:12:34:56"

    iutctl.init_stub()

    test_cases_ = test_cases(pts)

    for test_case in test_cases_:
        print
        print test_case

        if test_case.edit1_wids:
            print "edit1_wids: %r" % test_case.edit1_wids

        if test_case.verify_wids:
            print "verify_wids: %r" % test_case.verify_wids

        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)


if __name__ == "__main__":
    main()
