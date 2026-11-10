#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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

"""HID11 Device and Host test cases (PTS workspace project HID11)."""

import logging
import threading

from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.zephyr.hid_device_wid import hid_device_wid_hdl
from autopts.ptsprojects.zephyr.hid_host_wid import hid_host_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp, defs
from autopts.pybtp.types import Addr
from autopts.wid.hid_host import connect_to_pts

# PTS builds the HIDDeviceSubclass attribute of its emulated HID device from
# TSPX_Tester_DID_ProductID. HID1.1 requires bits 1 and 0 of HIDDeviceSubclass
# to be zero, so the PTS default of 1 makes IOPT/HID11/HOS/CGSIT/SFC/BV-01-I
# end as Indecisive right after the SDP records are registered, before any WID
# is sent to the IUT. 0xC0 selects the keyboard subclass and keeps bits 1:0
# zero.
TSPX_TESTER_DID_PRODUCT_ID = 0xC0


def set_pixits(ptses):
    """Setup HID11 profile PIXITS for workspace.

    Those values are used for the test case if not updated within the test
    case itself.  Always keep them in sync with the project and the newest
    version of PTS.

    ptses -- list of PyPTS instances
    """
    pts = ptses[0]

    pts.set_pixit("HID11", "TSPX_time_guard", "180000")
    pts.set_pixit("HID11", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("HID11", "TSPX_delete_link_key", "TRUE")
    pts.set_pixit("HID11", "TSPX_Tester_DID_ProductID",
                  str(TSPX_TESTER_DID_PRODUCT_ID))


def test_cases(ptses):
    """Return a list of HID11 Device and Host test cases.

    The HID11 PTS project contains both HID Device (/DEV/) and HID Host
    (/HOS/) test cases.  This module produces all HID11 cases and picks the
    correct role pre-conditions and WID handler per test case name.

    ptses -- list of PyPTS instances
    """
    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Common GAP pre-conditions shared by both roles.
    gap_pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_controller_info),
        TestFunc(lambda: pts.update_pixit_param(
            "HID11", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
    ]

    # HID Device role registration.
    # Also make the IUT connectable and general-discoverable so PTS can page
    # the IUT for test cases (e.g. DEV/DCT) where PTS initiates the BR/EDR
    # connection without sending an explicit WID first.
    # Set IO cap to NO_INPUT_OUTPUT so that the pincode_entry callback is
    # registered in btp_gap.c.  Without this the IUT sends PIN_CODE_NEG_REPLY
    # for legacy PIN pairing (e.g. DCE/BV-05-C pre-connection pairing with a
    # legacy-only Lower Tester), causing HCI_PAIRING_NOT_ALLOWED and INDCSV.
    device_pre_conditions = gap_pre_conditions + [
        TestFunc(btp.gap_set_io_capability, defs.GAP_IO_CAP_NO_INPUT_OUTPUT),
        TestFunc(btp.core_reg_svc_hid_device),
        TestFunc(stack.hid_device_init),
        TestFunc(btp.gap_set_connectable),
        TestFunc(btp.gap_set_general_discoverable),
    ]

    # HID Host role registration.
    host_pre_conditions = gap_pre_conditions + [
        TestFunc(btp.gap_set_io_capability, defs.GAP_IO_CAP_NO_INPUT_OUTPUT),
        TestFunc(btp.core_reg_svc_sdp),
        TestFunc(btp.core_reg_svc_hid_host),
        TestFunc(stack.hid_host_init),
    ]

    def _hgr_connect_worker():
        """Inquire, page and open the HID link to PTS from a worker thread.

        Retries the whole discover-and-connect sequence a few times because
        PTS needs a moment after Start Test Case before its page scan and
        HID L2CAP servers are up. Each connect_to_pts attempt spends a
        10-second inquiry window, so 6 attempts cover about a minute.
        """
        for attempt in range(1, 7):
            if connect_to_pts():
                logging.debug("_hgr_connect_worker: HID link up on attempt %d",
                              attempt)
                return
            logging.debug("_hgr_connect_worker: attempt %d did not bring the "
                          "HID link up, retrying", attempt)

        logging.debug("_hgr_connect_worker: gave up bringing the HID link up")

    def _hgr_connect():
        """Start the HGR connect sequence without blocking the pre-conditions.

        Pre-condition TestFuncs run BEFORE the client calls run_test_case(),
        so PTS has not yet executed its own Start Test Case setup: at that
        point it has not sent HCI_WRITE_SCAN_ENABLE and has not registered
        the HID L2CAP PSMs 0x0011/0x0013. A blocking connect here therefore
        inquires into a silent tester, finds nothing, and the pre-conditions
        return before the IUT ever pages PTS. PTS then renders no WID at all
        and ends the case with "Failed to receive BR/EDR ACL Connection
        Request" (INDCSV).

        Run the sequence in a daemon thread instead. The pre-conditions
        complete immediately, run_test_case() starts PTS, and the worker's
        retries page PTS once it is scanning.
        """
        threading.Thread(target=_hgr_connect_worker,
                         name="hgr-connect",
                         daemon=True).start()
        return True

    # HGR (HID Host-initiated Get Report / Sniff Mode) test cases:
    # The IUT must proactively inquire, connect, and read SDP records from PTS.
    # The connect runs asynchronously so it overlaps PTS's own test-case
    # startup instead of racing ahead of it. Make the IUT connectable and
    # general-discoverable so PTS can page it back if needed (e.g. after
    # Sniff mode negotiation).
    hgr_pre_conditions = host_pre_conditions + [
        TestFunc(btp.gap_set_connectable),
        TestFunc(btp.gap_set_general_discoverable),
        TestFunc(_hgr_connect),
    ]

    # CDD (Connection Disconnect) test cases:

    # PTS initiates the ACL connection to the IUT.  Make the IUT connectable
    # and general-discoverable so PTS can page it.  WID 43 fires once PTS has
    # opened the ACL link and the IUT can issue sdp_search_req on that conn.
    cdd_pre_conditions = host_pre_conditions + [
        TestFunc(btp.gap_set_connectable),
        TestFunc(btp.gap_set_general_discoverable),
    ]

    test_case_name_list = pts.get_test_case_list('HID11')
    tc_list = []

    for tc_name in test_case_name_list:
        if '/HOS/CDD/' in tc_name:
            instance = ZTestCase('HID11', tc_name, cmds=cdd_pre_conditions,
                                 generic_wid_hdl=hid_host_wid_hdl)
        elif '/HOS/HGR/' in tc_name:
            instance = ZTestCase('HID11', tc_name, cmds=hgr_pre_conditions,
                                 generic_wid_hdl=hid_host_wid_hdl)
        elif '/HOS/' in tc_name:
            instance = ZTestCase('HID11', tc_name, cmds=host_pre_conditions,
                                 generic_wid_hdl=hid_host_wid_hdl)
        else:
            instance = ZTestCase('HID11', tc_name, cmds=device_pre_conditions,
                                 generic_wid_hdl=hid_device_wid_hdl)

        tc_list.append(instance)

    return tc_list
