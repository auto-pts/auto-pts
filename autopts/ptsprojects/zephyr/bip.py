#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, nxp.
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
from autopts.ptsprojects.zephyr.bip_wid import bip_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp, types
from autopts.pybtp.types import Addr

TSPX_supported_encodings = "JPEG"
TSPX_supported_pixels = "1280*1024"


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("BIP", "TSPX_security_enabled", "FALSE")
    pts.set_pixit("BIP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("BIP", "TSPX_time_guard", "180000")
    pts.set_pixit("BIP", "TSPX_sender_class_of_device", "100104")
    pts.set_pixit("BIP", "TSPX_receiver_class_of_device", "100104")
    pts.set_pixit("BIP", "TSPX_auth_password", "0000")
    pts.set_pixit("BIP", "TSPX_l2cap_psm", "1003")
    pts.set_pixit("BIP", "TSPX_rfcomm_channel", "8")
    pts.set_pixit("BIP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("BIP", "TSPX_pin_code", "0000")
    pts.set_pixit("BIP", "TSPX_use_implicit_send", "False")
    pts.set_pixit("BIP", "TSPX_supported_encodings", TSPX_supported_encodings)
    pts.set_pixit("BIP", "TSPX_supported_pixels", TSPX_supported_pixels)
    pts.set_pixit("BIP", "TSPX_PutLinkedAttachment_Formats", "text/plain")
    pts.set_pixit("BIP", "TSPX_use_implicit_send", "FALSE")
    pts.set_pixit("BIP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")



def test_cases(ptses):
    """
    Returns a list of BIP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "BIP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_bip),
        TestFunc(stack.bip_init),
        TestFunc(lambda: stack.bip.image_db.ds.preferred_format.update({
            "encoding": TSPX_supported_encodings,
            "pixel": TSPX_supported_pixels,
        })),
    ]

    # Connection type to use when registering the BIP server for a test case.
    PUSH = types.BIPConnType.PRIM_IMAGE_PUSH
    PULL = types.BIPConnType.PRIM_IMAGE_PULL
    DISPLAY = types.BIPConnType.PRIM_REMOTE_DISPLAY
    CAMERA = types.BIPConnType.PRIM_REMOTE_CAMERA
    PRINTING = types.BIPConnType.PRIM_ADVANCED_IMAGE_PRINTING
    ARCHIVE = types.BIPConnType.PRIM_AUTO_ARCHIVE

    # Extra setup steps that a few test cases need in addition to registering
    # the BIP server. Referenced by the custom test case table below.
    def set_partial_content():
        setattr(stack.bip.image_db, 'put_image_final_partial_content', True)

    def set_srmp_wait_count():
        setattr(stack.bip, 'default_srmp_wait_count', 1)

    # Custom test cases described as (name, conn_type, extra_setup) tuples.
    # extra_setup is optional and, when present, runs after the server is
    # registered.
    custom_test_case_defs = [
        ("BIP/IPSR/PSH/BV-01-C", PUSH, None),
        ("BIP/IPSR/MFS/BV-02-C", PUSH, None),
        ("BIP/IPSR/FFC/BV-02-C", PUSH, None),
        ("BIP/IPSR/FFC/BV-10-C", PUSH, None),
        ("BIP/IPSR/FFC/BV-11-C", PUSH, set_partial_content),
        ("BIP/SR/GOEP/SRM/BI-03-C", PUSH, None),
        ("BIP/SR/GOEP/SRM/BV-04-C", PUSH, None),
        ("BIP/SR/GOEP/SRM/BI-02-C", PUSH, None),
        ("BIP/SR/GOEP/ROB/BV-01-C", PUSH, None),
        ("BIP/IPSR/PSH/BV-02-C", PUSH, None),
        ("BIP/IPSR/PSH/BV-02-C", PUSH, None),
        ("BIP/IPSR/MFS/BV-06-C", PUSH, None),
        ("BIP/IPSR/PSH/BI-01-C", PUSH, None),
        ("BIP/RDR/MFS/BV-26-C", DISPLAY, None),
        ("BIP/RCR/MFS/BV-23-C", CAMERA, None),
        ("BIP/AIPR/MFS/BV-18-C", PRINTING, None),
        ("BIP/IPLR/MFS/BV-16-C", PULL, None),
        ("BIP/IPLR/MFS/BV-14-C", PULL, None),
        ("BIP/IPLR/MFS/BV-12-C", PULL, None),
        ("BIP/AAR/MFS/BV-15-C", ARCHIVE, None),
        ("BIP/AAR/MFS/BV-11-C", ARCHIVE, None),
        ("BIP/AAR/MFS/BV-13-C", ARCHIVE, None),
        ("BIP/AAR/FFC/BV-03-C", ARCHIVE, None),
        ("BIP/SR/GOEP/SRMP/BV-03-C", PUSH, set_srmp_wait_count),
        ("BIP/SR/GOEP/ROB/BV-02-C", PUSH, None),
        ("BIP/SR/GOEP/BC/BV-01-C", PUSH, None),
        ("BIP/RDI/RMD/BV-01-C", PUSH, None),
        ("BIP/AAI/MFS/BV-12-C", PUSH, None),
        ("BIP/RDR/FFC/BV-10-C", DISPLAY, None),
        ("BIP/RDR/FSF/BV-11-C", DISPLAY, None),
        ("BIP/RDR/FSF/BV-12-C", DISPLAY, None),
        ("BIP/RDR/RMD/BV-01-C", DISPLAY, None),
        ("BIP/RDR/FFC/BV-11-C", DISPLAY, set_partial_content),
        ("BIP/AAR/MFS/BV-10-C", ARCHIVE, None),
        ("BIP/RCR/RMC/BV-02-C", CAMERA, None),
        ("BIP/IPLR/PLL/BV-01-C", PULL, None),
        ("BIP/AIPR/ADP/BV-01-C", PRINTING, None),
        ("BIP/AAR/MFS/BV-09-C", ARCHIVE, None),
        ("BIP/AAI/FSF/BV-07-C", ARCHIVE, None),
        ("BIP/AIPR/FSF/BV-06-C", PRINTING, None),
        ("BIP/RCR/FSF/BV-04-C", CAMERA, None),
        ("BIP/RCR/FSF/BV-03-C", CAMERA, None),
        ("BIP/IPLR/FFC/BV-08-C", PULL, None),
        ("BIP/AAR/FFC/BV-07-C", ARCHIVE, None),
        ("BIP/IPLR/FFC/BV-06-C", PULL, None),
        ("BIP/AAR/FFC/BV-05-C", ARCHIVE, None),
        ("BIP/RDR/FFC/BV-08-C", DISPLAY, None),
        ("BIP/RDR/FFC/BV-06-C", DISPLAY, None),
        ("BIP/RDR/FFC/BV-04-C", DISPLAY, None),
        ("BIP/IPLR/FFC/BV-04-C", PULL, None),
        ("BIP/RDR/FFC/BV-02-C", DISPLAY, None),
        ("BIP/AIPR/FFC/BV-02-C", PRINTING, None),
        ("BIP/IPLR/FFC/BV-02-C", PULL, None),
        ("BIP/AAR/FFC/BV-01-C", ARCHIVE, None),
        ("BIP/AAI/ACH/BV-01-C", ARCHIVE, None),
        ("BIP/AAR/MFS/BV-08-C", ARCHIVE, None),
        ("BIP/AAR/MFS/BV-07-C", ARCHIVE, None),
        ("BIP/IPSR/MFS/BV-04-C", PUSH, set_partial_content),
    ]

    def build_custom_cmds(conn_type, extra_setup):
        cmds = pre_conditions + [
            TestFunc(btp.bip_server_register, conn_type=conn_type),
        ]
        if extra_setup is not None:
            cmds.append(TestFunc(extra_setup))
        return cmds

    custom_test_cases = {
        name: ZTestCase(
            "BIP", name,
            cmds=build_custom_cmds(conn_type, extra_setup),
            generic_wid_hdl=bip_wid_hdl,
        )
        for name, conn_type, extra_setup in custom_test_case_defs
    }

    # Use the same preconditions and MMI/WID handler for all test cases of the
    # profile, overriding with a custom test case when one is defined.
    tc_list = []
    for tc_name in pts.get_test_case_list('BIP'):
        instance = custom_test_cases.get(tc_name) or ZTestCase(
            'BIP', tc_name, cmds=pre_conditions, generic_wid_hdl=bip_wid_hdl)
        tc_list.append(instance)

    return tc_list


