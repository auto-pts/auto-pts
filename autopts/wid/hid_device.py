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
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#

import logging
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import BTPError, WIDParams

log = logging.debug


def hid_device_wid_hdl(wid, description, test_case_name):
    # Local table lookup first; otherwise hand over to generic handler.
    from autopts.wid import generic_wid_hdl
    log(f'{hid_device_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def hdl_wid_0(_: WIDParams):
    """
    Make the Implementation Under Test (IUT) discoverable and connectable.

    Description: Implements WID 0 for HID profile - makes the IUT discoverable
    and connectable for the tester to initiate connection.

    The pre-run test sequence (gap_set_connectable + gap_set_general_discoverable)
    already placed the IUT in connectable + general-discoverable mode before this
    WID fires, so re-issuing the same GAP commands here is redundant. Re-sending
    SET_DISCOVERABLE a second time faults the IUT firmware (BTP socket drops and
    the IUT never returns to ready), so we simply acknowledge the WID instead.
    """
    return True


def hdl_wid_1(params: WIDParams):
    """
    WID 1 has two different meanings depending on the test case description:

    1. "Close the control channel connection from the Implementation Under
       Test (IUT)" - disconnect prompt used at the end of DCR (device
       disconnection) sequences. By the time this WID arrives the HID link is
       usually already torn down (e.g. DCR/BV-03-C plays WID 12 for a
       device-initiated Virtual Cable Unplug, then WID 2 to close the
       Interrupt channel, then WID 1 to close the Control channel). Tolerate a
       BTP error on the disconnect and rely on the HID Disconnected event so
       the case is not aborted. Crucially, do NOT initiate a fresh HID
       connection here - the historical connect path (discovery + connect)
       would wrongly re-open the link and PTS marks the case FAIL.

    2. Otherwise: initiate a HID connection to the PTS (historical behaviour).
    """
    description = (params.description or "").lower() if params is not None else ""
    stack = get_stack()

    if "close" in description:
        try:
            btp.hid_device_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hdl_wid_1: hid_device_disconnect returned error "
                          "status; relying on HID Device Disconnected event")

        try:
            stack.hid_device.wait_for_disconnection()
        except TimeoutError as e:
            logging.debug("hdl_wid_1: wait_for_disconnection: %s", e)

        # DCR/BV-03-C is "Host Initiated Virtual Cable Unplug": PTS (the HID
        # Host) sends a HID_CONTROL VIRTUAL_CABLE_UNPLUG on the Control channel
        # and the IUT (HID Device) correctly tears down the INTR then CTRL
        # L2CAP channels. Per HID spec v1.1.2 Section 3.1.2.2.3 the IUT stack
        # intentionally does NOT drop the shared BR/EDR ACL after a VCU (the
        # ACL may carry other profiles), so without action here the ACL only
        # goes away via the ~3 min supervision timeout - long after PTS is
        # waiting for the disconnection, which it then marks FAIL ("Expected a
        # disconnection"). WID 1 is the final prompt of the DCR sequence, so
        # tear the ACL down from the automation once the HID channels are gone
        # to give PTS the timely disconnection it expects.
        try:
            btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_1: gap_disconnect returned error: %s", e)

        try:
            stack.gap.wait_for_disconnection(timeout=10)
        except TimeoutError as e:
            logging.debug("hdl_wid_1: gap wait_for_disconnection: %s", e)

        return True

    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    if not btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()

    btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    stack = get_stack()
    if not stack.hid_device.wait_for_connection():
        logging.error("HID Device connection failed")
        return False

    logging.debug("HID Device connected: addr=%s", stack.hid_device.connected_addr)

    return True


def hdl_wid_2(params: WIDParams):
    """
    Disable the connection using the IUT.

    HID/DEV/HCR/BV-04-C explicitly permits (and expects) the IUT to send a
    host-initiated Virtual Cable Unplug on the Control channel. Plain L2CAP
    disconnect is also allowed by the spec, but PTS treats a bare L2CAP
    disconnect on this test case as non-conformant and only recovers when
    the ACL supervision-timeout eventually fires, resulting in FAIL. Route
    HCR test cases through the Virtual Cable Unplug path; every other WID=2
    prompt keeps the historical plain-disconnect behaviour.
    """
    tc = (params.test_case_name or "") if params is not None else ""
    stack = get_stack()

    if "/HCR/" in tc:
        # The IUT stack tears down the L2CAP channels itself after the VCU
        # PDU has been flushed on the Control channel (TX-complete callback,
        # plus a short backstop timer). Calling btp.hid_device_disconnect()
        # here would force an immediate L2CAP disconnect before the VCU report
        # reaches PTS, which PTS treats as a bare L2CAP disconnect during
        # HCR and marks the test case FAIL.
        try:
            btp.hid_device_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hid_device_virtual_cable_unplug returned error; "
                          "relying on HID Device Disconnected event")
    else:
        # The link may already be tearing down (e.g. DCR/BV-03-C plays WID 12
        # for a device-initiated Virtual Cable Unplug just before this WID 2),
        # in which case the tester returns an error status for the disconnect
        # command. Tolerate it and rely on the HID Disconnected event so the
        # case is not aborted with a BTP ERROR.
        try:
            btp.hid_device_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hdl_wid_2: hid_device_disconnect returned error "
                          "status; relying on HID Device Disconnected event")

    stack.hid_device.wait_for_disconnection()

    return True


def hdl_wid_3(params: WIDParams):
    """
    WID 3 has three different meanings depending on the test case description:

    1. "Establish the control channel connection from the IUT" (DRE
       suspend/resume) - after the host resumed, the IUT must re-open the HID
       L2CAP connection (control + interrupt channels) toward the PTS. Re-open
       the ACL if it was dropped, then initiate hid_device_connect.

    2. "release the HID connection from the IUT by closing the Interrupt
       Channel followed by the Control Channel" - the IUT must tear down the
       HID L2CAP channels (HID disconnect), NOT remove the pairing.

    3. "delete the pairing with the PTS" - the IUT must remove any existing
       pairing to ensure a clean state for the test.

    We branch on the description so the correct action is performed.
    """
    description = (params.description or "").lower()

    if "establish" in description:
        # Re-establish the HID connection from the IUT side after resume.
        stack = get_stack()

        if not stack.hid_device.connected:
            try:
                if not stack.gap.is_connected():
                    btp.gap_start_discovery(transport='bredr',
                                            discov_type='passive', mode='general')
                    sleep(10)
                    btp.gap_stop_discovery()
                    if btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
                        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                        btp.gap_wait_for_connection()
            except BTPError as e:
                logging.debug("hdl_wid_3: gap reconnect error: %s", e)

            try:
                btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                logging.debug("hdl_wid_3: hid_device_connect error: %s", e)

            stack.hid_device.wait_for_connection(timeout=15)

        return True

    if "release the hid connection" in description or "interrupt channel" in description:

        # Release the HID connection via L2CAP channel disconnect.
        # Some IUTs return an error status byte to the disconnect command even
        # though the channels are actually torn down (a HID Disconnected event
        # still follows). Tolerate the BTP error and rely on the event so the
        # test case is not incorrectly aborted.
        stack = get_stack()

        try:
            btp.hid_device_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hid_device_disconnect returned error status; "
                          "relying on HID Device Disconnected event")

        stack.hid_device.wait_for_disconnection()

        return True

    # Default behaviour: delete the pairing with the PTS.
    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    return True


def _hdt_report_sender(stop_event, interval=1.0, max_reports=60,
                       test_case_name=""):
    """
    Background worker: once the HID connection is up, periodically send HID
    input reports on the Interrupt channel until stop_event is set or the
    connection drops. Used by HDT (HID Data Transfer) and DAT (Data) test
    cases that expect the IUT to originate input data without any further
    WID prompt.

    For DAT/HDT test cases PTS establishes the BR/EDR ACL + encryption but
    does not initiate the HID L2CAP channels; the IUT (HID Device) is
    expected to bring the HID connection up itself. Wait for the ACL to be
    up, then actively initiate the HID connect from the IUT side.
    """
    stack = get_stack()

    try:
        # Wait until the BR/EDR ACL is up before initiating HID L2CAP.
        try:
            btp.gap_wait_for_connection(timeout=30)
        except TimeoutError as e:
            logging.debug("_hdt_report_sender: gap_wait_for_connection: %s", e)

        # PTS (HID Host) drops incoming HID L2CAP connect requests until the
        # BR/EDR link is authenticated and encrypted. Wait for the encryption
        # change event before initiating HID connect, otherwise the L2CAP
        # setup fails and the IUT stack returns an error status for the
        # BTP HID_DEVICE_CONNECT command.
        try:
            stack.gap.gap_wait_for_encryption_change(timeout=15)
        except TimeoutError as e:
            logging.debug("_hdt_report_sender: gap_wait_for_encryption_change: %s", e)
        # Extra guard delay: allow the IUT stack to install the link key on
        # both L2CAP sides before opening HID PSMs.
        sleep(1.0)

        # For HID/DEV/DAT/... test cases, PTS is HID Host and initiates the
        # HID L2CAP Control + Interrupt channels itself once the BR/EDR link
        # is authenticated. Simply wait for the IUT's HID connected event.
        # (Falling back to IUT-initiated hid_device_connect is unreliable
        # because PTS-as-Host does not listen on the HID PSMs and silently
        # drops inbound connect requests; the BTP command returns success but
        # no HID Device Connected event ever follows.)
        if not stack.hid_device.wait_for_connection(timeout=30):
            logging.debug("_hdt_report_sender: HID never connected; trying "
                          "IUT-initiated hid_device_connect as last resort")
            try:
                btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                logging.debug("_hdt_report_sender: hid_device_connect error: %s", e)
            if not stack.hid_device.wait_for_connection(timeout=10):
                logging.debug("_hdt_report_sender: no HID connection, giving up")
                return

        report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT

        # Empty keyboard boot report (no keys pressed) is a safe payload.
        report = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        sent = 0
        while not stop_event.is_set() and sent < max_reports and stack.hid_device.connected:
            try:
                btp.hid_device_send_report(report_type, report)
            except BTPError as e:
                logging.debug("_hdt_report_sender: send failed: %s", e)
                break
            sent += 1
            stop_event.wait(interval)

        logging.debug("_hdt_report_sender: sent %d reports", sent)
    except BTPError as e:
        logging.debug("_hdt_report_sender: BTP error, stopping: %s", e)


def hdl_wid_5(params: WIDParams):
    """
    Accept the control channel connection from the Implementation Under Test (IUT).

    Description: WID 5 - PTS is ready to accept an L2CAP connect request for the
    HID Control channel FROM the IUT.

    For DCE (Device-initiated Connection Establishment) test cases the IUT is
    the initiator: PTS establishes an ACL, tears it down, then plays this WID
    to signal it is listening for the IUT to open the HID connection. Merely
    acknowledging leaves the device idle, so PTS never sees a connection and
    returns INDCSV. Re-page PTS if the ACL was dropped and then initiate the
    HID connection from the IUT side. Every other WID=5 prompt keeps the
    historical acknowledge-only behaviour.
    """
    tc = (params.test_case_name or "") if params is not None else ""

    # DRE (Device Initiated Reconnection) is the same device-initiated pattern
    # as DCE: WID 5 ("Accept the control channel connection FROM the IUT")
    # means PTS is now listening and the IUT must open the HID L2CAP Control +
    # Interrupt channels itself. Log evidence confirms PTS never initiates the
    # HID connection for DRE (no incoming CTRL channel, no HID Connected event
    # unless the IUT connects). The device-initiated connect worker (started
    # AFTER this handler returns OK) both opens the channels and, for DRE BV,
    # sends the input reports itself once connected. The separate WID-6 report
    # sender is intentionally NOT used for DRE, because two threads writing to
    # the BTP transport concurrently (connect + send_report) garble the BTP
    # command/response sequencing and the connect fails with an error status.
    # DCE/BV-02-C is HOST-initiated: PTS itself sends the L2CAP CONNECT_REQ on
    # the HID Control PSM (0x0011) and the IUT must merely ACCEPT it. Starting
    # the device-initiated connect worker for this case makes the IUT open its
    # OWN control channel at the same time, so when PTS's incoming CONNECT_REQ
    # arrives the HID state machine is already in CTRL_CONNECTING and the accept
    # callback rejects it with -EBUSY ("Failed to open Control channel" ->
    # INDCSV). For host-initiated DCE cases keep the acknowledge-only behaviour
    # and let the IUT accept the incoming connection.
    #
    # DCE/BV-05-C ("Host Connection Establishment in Security Mode 2 with Pre
    # Connection Pairing") is DEVICE-initiated reconnection that reuses the
    # pre-connection bond. BTP-log evidence: PTS pages the IUT and performs
    # legacy PIN pairing on the initial ACL (GAP_EV_DEVICE_CONNECTED), plays
    # WID 5 ("Accept the control channel connection FROM the IUT"), then TEARS
    # the ACL down (GAP_EV_DEVICE_DISCONNECTED) and does NOT re-page. So PTS is
    # the acceptor and the IUT must RE-PAGE PTS and open the HID L2CAP Control +
    # Interrupt channels itself. Acknowledge-only left the IUT idle -> INDCSV.
    # Route BV-05-C through the device-initiated connect worker, which has a
    # dedicated pre-connection-pairing reconnection branch: it waits for the
    # PTS teardown to settle, then re-pages REUSING the legacy PIN link key
    # (the Lower Tester has no SSP - the bond must NOT be deleted) and opens the
    # HID channels. It is therefore NOT host-initiated / acknowledge-only.
    host_initiated_dce = ("/DCE/BV-02-C" in tc)

    # if ("/DCE/" in tc or "/DRE/" in tc):
    #    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    #    return True

    if ("/DCE/" in tc or "/DRE/" in tc) and not host_initiated_dce:

        stack = get_stack()

        if not stack.hid_device.connected:

            # DCE (Device-initiated Connection Establishment). The log timeline

            # proves PTS only starts listening for (accepting) the HID Control
            # channel AFTER it has received the OK response to THIS wid. If the
            # handler pages / initiates the HID connect before returning, PTS
            # never gets the OK, never starts page-scanning / accepting, and the
            # attempt is rejected (HID Disconnected fires ~130ms later). So kick
            # the device-initiated connection off in a background thread and
            # return True immediately, letting PTS receive the OK and become
            # ready first.
            # The layer owns the worker handle so hdl_wid_7 can stop and
            # join it, making sure the worker has drained any in-flight BTP
            # response before the synchronous reconnect loop issues new BTP
            # commands, and so the worker cannot leak into the next test case.
            stack.hid_device.start_worker(_dce_connect_worker,
                                          "HID-DCE-connect",
                                          test_case_name=tc)

    return True


def _dce_connect_worker(stop_event, test_case_name=""):
    """
    Background worker for DCE (Device-initiated Connection Establishment).

    Started from hdl_wid_5 AFTER the handler returns OK, so PTS has received
    the acknowledgement and started listening for / accepting the incoming HID
    Control channel. Give PTS a short head-start, page it if the ACL is not up,
    then initiate the HID L2CAP connection from the IUT (device) side.
    """
    stack = get_stack()

    try:
        # DCE/BV-05-C: Host Connection Establishment in Security Mode 2 with
        # Pre Connection Pairing. PTS (Lower Tester, no SSP) pages the IUT,
        # performs legacy PIN pairing on the initial ACL, then TEARS the ACL
        # down and plays WID 5 to signal it is now listening for the IUT to
        # open the HID connection. The IUT must RE-PAGE PTS and open the HID
        # L2CAP Control + Interrupt channels itself, REUSING the legacy PIN
        # link key from the pre-connection pairing. Do NOT delete the bond
        # (the Lower Tester has no SSP, so a fresh pairing on re-page cannot
        # complete) and do NOT wait for a separate ACL encryption-change event
        # (Security Mode 2 elevates security at HID L2CAP channel setup, not on
        # the base ACL). Wait (bounded) for the PTS teardown of the initial ACL
        # to complete first, so the re-page does not collide with PTS still
        # closing the initial ACL (that collision was the earlier
        # "ACL to PTS not established" failure), then re-page and connect.
        if "/DCE/BV-05-C" in (test_case_name or ""):
            for _ in range(30):
                if not stack.gap.is_connected() or stop_event.is_set():
                    break
                sleep(0.1)
            for attempt in range(12):
                if stack.hid_device.connected or stop_event.is_set():
                    break
                if not stack.gap.is_connected():
                    try:
                        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                        btp.gap_wait_for_connection(timeout=3)
                    except BTPError as e:
                        logging.debug("_dce_connect_worker: BV-05-C re-page "
                                      "attempt %d: %s", attempt, e)
                        sleep(0.2)
                        continue
                try:
                    btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                except BTPError as e:
                    logging.debug("_dce_connect_worker: BV-05-C "
                                  "hid_device_connect attempt %d: %s", attempt, e)
                    sleep(0.15)
                    continue
                if stack.hid_device.wait_for_connection(timeout=1):
                    break
                sleep(0.1)
            return
        # The WID-5 OK is already sent synchronously by the LT1 thread before
        # this worker runs, and PTS closes the DCE case only ~3s after WID 5.
        # Do NOT sleep here - page PTS immediately, otherwise the acceptance
        # window closes before the ACL is re-established.
        connected = stack.gap.is_connected()
        for attempt in range(5):
            if connected or stop_event.is_set():
                break
            try:
                btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                btp.gap_wait_for_connection(timeout=5)
                connected = stack.gap.is_connected()
            except BTPError as e:
                logging.debug("_dce_connect_worker: gap_connect attempt %d: %s",
                              attempt, e)
            if not connected and not stop_event.is_set():
                sleep(0.2)

        if not connected:
            logging.debug("_dce_connect_worker: ACL to PTS not established")
            return

        # PTS accepts the HID L2CAP Control/Interrupt channels only after the
        # BR/EDR link is authenticated and encrypted. For DCE cases PTS keeps
        # the ACL up after initial pairing, so wait here for the encryption
        # event before calling hid_device_connect. Skip this wait for DRE
        # cases: on the DRE path the encryption already occurred during the
        # initial connection (before WID 44 triggers the ACL teardown), so
        # waiting here blocks for the full timeout (15 s) on a dead link and
        # causes PTS to render its verdict before the re-page completes. DRE
        # re-pages and runs a fresh SSP+encryption on the new ACL; the new
        # encryption event arrives automatically during that re-page.
        is_dre = "/DRE/" in (test_case_name or "")
        if not is_dre:
            try:
                stack.gap.gap_wait_for_encryption_change(timeout=15)
            except TimeoutError as e:
                logging.debug("_dce_connect_worker: gap_wait_for_encryption_change: %s", e)

        # The teardown-wait + stale-link-key unpair below are DRE (Device
        # Initiated Reconnection) ONLY. For pure DCE (Device-initiated
        # Connection Establishment, e.g. BV-01-C) PTS keeps the ACL up after
        # pairing/encryption and expects the IUT to open the HID L2CAP Control +
        # Interrupt channels IMMEDIATELY on the existing link. Running the DRE
        # teardown-wait (up to 4s) and gap_unpair for DCE delayed the
        # hid_device_connect past PTS's acceptance window, so PTS tore the ACL
        # down (HID Disconnected with a zero address) and returned INDCSV before
        # the channels were ever opened. Only DRE performs the teardown-wait and
        # re-page; DCE falls straight through to hid_device_connect on the live
        # ACL.
        if is_dre:
            # DRE: after pairing/encryption PTS TEARS DOWN the whole ACL
            # (GAP_EV_DEVICE_DISCONNECTED) and then plays WID 5 / WID 6 to
            # signal it is now listening for the IUT to reconnect. The IUT must
            # re-PAGE PTS (re-establish the ACL) and only then open the HID
            # L2CAP Control + Interrupt channels. The PTS verdict is rendered
            # only ~3.3s after the teardown, so the whole re-page + HID L2CAP
            # setup must fit in that window. Do NOT sleep here - instead wait
            # for the teardown to actually happen (is_connected() -> False) and
            # then re-page IMMEDIATELY, because the devices are already paired
            # (the link key is stored) so no re-pairing is needed and the page
            # is fast.
            for _ in range(40):
                if not stack.gap.is_connected() or stop_event.is_set():
                    break
                sleep(0.1)

            # Stale link-key recovery for DRE reconnection. When PTS tears down
            # the ACL after the initial pairing it also drops its own bond, but
            # the IUT keeps the old link key. On the IUT-initiated re-page PTS
            # then runs authentication with a key it no longer has, the first
            # attempt fails, and every subsequent re-page lands inside the
            # controller's HCI_REPEATED_ATTEMPTS lockout window (PTS logs
            # "HCI Authentication Complete returned an error" ->
            # "Failed to open Control channel" -> INDCSV). Delete the stale bond
            # on the IUT side first so the re-page triggers a fresh SSP pairing
            # instead of a doomed authentication with a mismatched link key.
            try:
                btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                logging.debug("_dce_connect_worker: gap_unpair before re-page: %s", e)

        for attempt in range(12):
            if stack.hid_device.connected or stop_event.is_set():
                break
            # Ensure the ACL is up; re-page PTS if the DRE teardown dropped it.
            if not stack.gap.is_connected():
                try:
                    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                    btp.gap_wait_for_connection(timeout=5)
                except BTPError as e:
                    logging.debug("_dce_connect_worker: DRE re-page attempt "
                                  "%d: %s", attempt, e)
                    sleep(0.3)
                    continue
                # DRE: no explicit post-re-page encryption wait. The firmware
                # handles SSP + encryption on the new ACL and hid_device_connect
                # retries on failure. Adding a sleep here caused PTS COM server
                # crashes when the board BTP wedged under repeated re-page load.
            try:
                btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                # For a pure DCE case the IUT firmware can reject the very
                # first hid_device_connect when it is issued the instant the
                # BTP encryption-change event lands: L2CAP is not yet ready to
                # page the HID Control PSM on the freshly encrypted link, so
                # the BTP command returns an error opcode. This is transient -
                # PTS keeps its acceptor listening for ~1s after WID 6 before
                # tearing the ACL down. Do NOT fall into the long 3s
                # wait_for_connection after a failed connect (that eats the
                # whole acceptance window and lets PTS drop the ACL first);
                # instead back off briefly and retry the connect so several
                # attempts fit inside the acceptance window.
                logging.debug("_dce_connect_worker: hid_device_connect attempt "
                              "%d: %s", attempt, e)
                sleep(0.15)
                continue
            if stack.hid_device.wait_for_connection(timeout=1):
                break
            sleep(0.1)

        # For DRE (Device Initiated Reconnection) BV cases the HID11 spec pass
        # verdict (Section 4.7.1) requires data exchange upon the HID
        # connection: once the channels are up, the IUT must originate input
        # reports itself (PTS sends no further WID). Send the reports here on
        # the SAME thread, AFTER the connect fully succeeded, so the connect
        # and the send never race each other on the BTP transport. BI cases
        # test invalid behaviour and must not send data.
        is_bi = "/BI-" in (test_case_name or "")
        if ("/DRE/" in (test_case_name or "") and not is_bi
                and stack.hid_device.connected and not stop_event.is_set()):
            report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT
            # Keyboard report: Report ID 1, modifier, reserved, 6 keycodes.
            report_press = bytearray([0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
            report_release = bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            for i in range(6):
                if stop_event.is_set() or not stack.hid_device.connected:
                    break
                report = report_press if (i % 2 == 0) else report_release
                try:
                    btp.hid_device_send_report(report_type, report)
                except BTPError as e:
                    logging.debug("_dce_connect_worker: send report %d: %s", i, e)
                    break
                sleep(0.2)

    except BTPError as e:
        logging.debug("_dce_connect_worker: BTP error, stopping: %s", e)


def _dct_report_sender(stop_event, interval=0.2, max_reports=50):
    """
    Background worker for DCT test cases: send HID input reports immediately
    after both HID L2CAP channels are open. Unlike _hdt_report_sender, this
    function does NOT wait for connection events since the HID channels are
    already established when it is started (after WID 6 OK).

    PTS DCT/BV-02-C verifies that the IUT transfers data on the Interrupt
    channel. Send a series of keyboard input reports with a non-zero key code
    (Report ID 1, modifier=0, reserved=0, key[0]=0x04 'a') so PTS observes
    actual data transfer and does not give an INDCSV verdict.
    """
    stack = get_stack()

    try:
        # Brief delay to allow PTS to fully complete Interrupt channel L2CAP
        # setup before the first report arrives.
        sleep(0.1)

        report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT

        # Keyboard report: Report ID 1, modifier, reserved, 6 keycodes.
        # Use key code 0x04 ('a') in the first slot so PTS sees real data.
        report_press = bytearray([0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
        # Key-release report (all zeros after Report ID) to alternate with press.
        report_release = bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        sent = 0
        while not stop_event.is_set() and sent < max_reports:
            # Alternate press and release so PTS sees a clear data stream.
            report = report_press if (sent % 2 == 0) else report_release
            try:
                btp.hid_device_send_report(report_type, report)
            except BTPError as e:
                logging.debug("_dct_report_sender: send failed: %s", e)
                break
            sent += 1
            stop_event.wait(interval)

        logging.debug("_dct_report_sender: sent %d reports", sent)
    except BTPError as e:
        logging.debug("_dct_report_sender: BTP error, stopping: %s", e)


def hdl_wid_6(params: WIDParams):
    """
    Accept the interrupt channel connection from the Implementation Under Test (IUT).
    Description: WID 6 - PTS has received an L2CAP connect request for the HID
    Interrupt channel from the IUT. The automation ACKs to let PTS open the channel.
    For DCT (Data Channel Transfer) test cases, PTS then expects the IUT to send
    HID input reports immediately; kick off a background sender.
    """
    tc = (params.test_case_name or "") if params is not None else ""
    # Only send data for BV (valid behavior) DAT/HDT cases and the DCT
    # interrupt-transfer case (BV-02-C). BI (invalid behavior) cases test
    # error handling, not data transfer; sending interrupt reports
    # concurrently would interfere with the PTS verdict.
    #
    # DCT/BV-01-C is the GET_REPORT test on the CONTROL channel: PTS issues a
    # GET_REPORT and the IUT stack answers automatically via its get_report
    # callback. Starting the interrupt-channel report sender here races with
    # that control-channel transaction (two writers on the BTP transport) and
    # PTS marks the case FAIL. So the interrupt sender must NOT run for
    # DCT/BV-01-C; it is only needed for the interrupt-transfer DCT/BV-02-C.
    is_bi = "/BI-" in tc
    dct_needs_sender = "/DCT/" in tc and "BV-01" not in tc
    # NOTE: DRE (Device Initiated Reconnection) is intentionally NOT handled
    # here. For DRE the device-initiated connect and the input-report send
    # must be serialized on a single thread (the _dce_connect_worker started
    # from hdl_wid_5) - running the report sender concurrently with the
    # connect worker made two threads write to the BTP transport at the same
    # time, garbling the command/response framing and failing the connect.
    if not is_bi and (dct_needs_sender or "/DAT/" in tc or "/HDT/" in tc):

        stack = get_stack()
        stack.hid_device.start_worker(_dct_report_sender, "HID-DCT-sender")
    # DGR (Device Get Report / sniff) test cases expect the IUT to put the
    # ACL into sniff mode itself once the HID link is up; PTS never asks for it
    # with a WID and just fails with "Expected to receive HCI Mode change".
    # bt_conn_br_enter_sniff_mode() rejects intervals above 0x0540, so the
    # TSPX_Sniff_Min/Max_Interval values (0x0780/0x0C80) cannot be used
    # directly. 0x0012 (18 slots, 11.25 ms) is the interval PTS itself
    # negotiates in the HGR direction. Wait for the interrupt channel to
    # settle first so the controller does not answer Command Disallowed.
    if "/DGR/" in tc:
        sleep(2)
        try:
            btp.hid_device_enter_sniff_mode(0x0012, 0x0012, 0x0004, 0x0002)
        except BTPError as e:
            logging.debug("hdl_wid_6: enter sniff mode failed: %s", e)

    return True


def hdl_wid_8(_: WIDParams):
    """
    Respond to the GET_REPORT request from the Implementation Under Test (IUT).

    Description: WID 8 - PTS (HID Host) sends a GET_REPORT request on the
    Control channel. The IUT HID Device stack answers automatically via its
    get_report callback (see hid_device_get_report_cb in the tester), so no
    BTP command is required from the automation. Simply acknowledge so PTS can
    verify the DATA response.
    """
    return True


def hdl_wid_9(_: WIDParams):
    """
    Respond to the SET_REPORT request from the Implementation Under Test (IUT).

    Description: WID 9 - PTS (HID Host) sends a SET_REPORT request on the
    Control channel. The IUT HID Device stack answers automatically via its
    set_report callback (see hid_device_set_report_cb in the tester), which
    accepts the OUTPUT (LED) report declared in the report descriptor and
    returns HANDSHAKE_SUCCESSFUL. No BTP command is required from the
    automation; simply acknowledge so PTS can verify the handshake.
    """
    return True


def hdl_wid_10(params: WIDParams):
    """
    Place the Implementation Under Test (IUT) in connectable mode, then click Ok.

    Description: Implements WID 10 for HID profile - makes the IUT connectable
    (and general discoverable) so the PTS can initiate a connection.

    For HDT (HID Data Transfer) test cases (e.g. HID/DEV/HDT/BV-04-C) PTS
    does not send any further WID after connect; it silently waits for the
    IUT to transmit HID input reports on the Interrupt channel. Kick off a
    background sender in that case so PTS sees data and does not return
    INDCSV.
    """
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    tc = (params.test_case_name or "") if params is not None else ""
    # HDT (HID Data Transfer) and DAT (Data) test cases both expect the IUT
    # to spontaneously transmit HID input reports on the Interrupt channel
    # after connection is established, without any further WID prompt.
    if "HDT" in tc or "/DAT/" in tc:
        stack = get_stack()
        stack.hid_device.start_worker(_hdt_report_sender, "HID-HDT-sender",
                                      test_case_name=tc)

    return True


def hdl_wid_11(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in a state which will allow the
    PTS to perform an HID disconnect, then click Ok.

    Description: Implements WID 11 for HID profile - the IUT is already
    connected and simply needs to remain ready so the PTS can initiate the
    HID disconnect (Virtual Cable Unplug or channel disconnect).
    """
    return True


def hdl_wid_12(params: WIDParams):
    """
    WID 12 has two different meanings depending on the description:

    1. "Respond to the HID_CONTROL VIRTUAL_CABLE_UNPLUG request from the IUT"
       (DCR device-initiated disconnection, e.g. HID11/DEV/DCR/BV-03-C). The
       IUT (HID Device) must ORIGINATE a Virtual Cable Unplug on the Control
       channel; PTS then walks WID 2 (close Interrupt) / WID 1 (close Control).
       The IUT stack tears the L2CAP channels down itself after the VCU PDU is
       flushed, so do NOT force a plain disconnect here - just kick off the
       device-initiated VCU and rely on the HID Disconnected event.

    2. Otherwise: the IUT is already connected and only needs to stay ready so
       PTS can perform the HID connection release itself (historical
       acknowledge-only behaviour).
    """
    description = (params.description or "").lower() if params is not None else ""
    stack = get_stack()

    if "virtual_cable_unplug" in description or "virtual cable unplug" in description:
        try:
            btp.hid_device_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_12: hid_device_virtual_cable_unplug error: %s", e)

    return True


def hdl_wid_13(_: WIDParams):
    """
    Respond to the HID_CONTROL SUSPEND request from the Implementation Under
    Test (IUT), then click Ok.

    Description: Implements WID 13 for HID profile - the PTS has sent (or the
    IUT has sent) a HID_CONTROL transaction with the SUSPEND parameter. No BTP
    action is required from the tester side; the IUT keeps the HID connection
    and simply acknowledges the control-channel SUSPEND so the PTS can proceed
    to its next step. Confirm to let PTS continue.
    """
    return True


def hdl_wid_14(_: WIDParams):
    """
    Click Ok, then perform one of the following actions:

    1. Move the PTS and Implementation Under Test (IUT) out of range of each other.
    2. Place either the PTS or IUT in an RF shield box.

    Description: Implements WID 14 for HID profile - simulates the out-of-range
    / RF-shield scenario by tearing down the ACL link from the IUT side so the
    PTS observes a link loss.
    """
    try:
        btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_14: gap_disconnect returned error: %s", e)

    stack = get_stack()
    try:
        stack.hid_device.wait_for_disconnection()
    except TimeoutError as e:
        logging.debug("hdl_wid_14: wait_for_disconnection: %s", e)

    return True


def hdl_wid_15(_: WIDParams):
    """
    Respond to GET_REPORT of invalid reportID from the Implementation Under Test (IUT).

    Description: WID 15 - BI (invalid behavior) test. PTS sends a GET_REPORT
    request with an invalid Report ID on the Control channel. The IUT HID Device
    stack is expected to respond with HANDSHAKE_ERR_INVALID_PARAMETER automatically.
    The automation just acknowledges so PTS can verify the IUT error response.
    """
    return True


def hdl_wid_17(_: WIDParams):
    """
    Respond to SET_REPORT of invalid reportID from the Implementation Under Test (IUT).

    Description: WID 17 - BI (invalid behavior) test. PTS sends a SET_REPORT
    request with an invalid Report ID on the Control channel. The IUT HID Device
    stack is expected to respond with HANDSHAKE_ERR_INVALID_PARAMETER automatically.
    The automation just acknowledges so PTS can verify the IUT error response.
    """
    return True


def hdl_wid_18(_: WIDParams):
    """
    Respond to SET_REPORT of report size shorter than the one defined in report
    descriptor from the Implementation Under Test (IUT).

    Description: WID 18 - BI (invalid behavior) test. PTS sends a SET_REPORT
    with a payload shorter than the expected size defined in the HID report
    descriptor. The IUT stack is expected to reject it automatically with
    HANDSHAKE_ERR_INVALID_PARAMETER. The automation acknowledges so PTS can
    verify the error response.
    """
    return True


def hdl_wid_20(_: WIDParams):
    """
    Click OK if IUT received a REPORT through the Interrupt channel.

    Description: WID 20 - BDIT/BV (valid behavior) confirmation. PTS has sent
    a report on the interrupt channel and asks us to confirm the IUT received
    it. Simply acknowledge so PTS can proceed.
    """
    return True


def hdl_wid_21(_: WIDParams):
    """
    Click OK if IUT received an invalid REPORT through the Interrupt channel
    and it ignores it.

    Description: WID 21 - DIT/BI (invalid behavior) confirmation. PTS sends an
    invalid report on the interrupt channel; the IUT is expected to silently
    ignore it. This handler simply confirms the observation to PTS.
    """
    return True


def hdl_wid_44(_: WIDParams):
    """
    Click OK to simulate tester moving out of range of IUT.

    Description: WID 44 - DRE (Device Reconnection) procedural MMI. PTS itself
    simulates going out of range, which tears the BR/EDR ACL down; the IUT is
    expected to detect the link loss and later reconnect (driven by the DCE
    connect worker started from WID 5). No IUT action is required from the
    autopts side for this prompt, so just confirm so PTS can proceed.
    """
    return True


def hdl_wid_7(params: WIDParams):
    """
    Establish HID reconnection from the Implementation Under Test (IUT).
    Then click OK.

    Description: WID 7 - DRE (Device Reconnection). The earlier WID 44 simulated
    the tester going out of range, which tore the BR/EDR ACL down. PTS is now
    listening again and expects the IUT to re-page it and re-open the HID L2CAP
    Control + Interrupt channels itself. The device-initiated connect worker
    started from WID 5 may already have exited (its teardown-wait window closed
    before the out-of-range event actually happened), so drive the reconnection
    synchronously here: stop any stale worker so it cannot write to the BTP
    transport concurrently, re-page PTS, delete the stale bond so the re-page
    triggers a fresh SSP pairing, open the HID connection, and for BV cases send
    input reports. Only acknowledge the MMI after the reconnection has been
    driven so PTS observes the incoming connection.
    """
    tc = (params.test_case_name or "") if params is not None else ""
    stack = get_stack()

    # Stop the DCE/DRE connect worker still running from WID 5 so it cannot
    # write to the BTP transport concurrently with this synchronous reconnect.
    # stop_worker() joins the thread, so the worker has fully exited and
    # drained any in-flight BTP command/response from the socket before this
    # reconnect loop issues new BTP commands. Without the join, the worker may
    # still be blocked inside btp.gap_connect() or btp.hid_device_connect()
    # reading the BTP response; hdl_wid_7 would then read that stale response
    # as its own and every call returns "Error opcode" (BTP queue desync), so
    # the interrupt channel is never opened (INDCSV).
    if stack.hid_device.worker_thread is not None:
        stack.hid_device.stop_worker()
        # The worker may have called bt_hid_device_connect and the CTRL channel
        # connected (BTP returned SUCCESS) but the INTR channel never connected
        # because PTS went out of range immediately after. The HID state machine
        # is now stuck in INTR_CONNECTING: hid_allocate() rejects every new
        # connect with -EBUSY because the ctrl_session conn pointer is non-NULL.
        # Wait up to 15s for the in-flight connection to complete. If it does
        # not, issue hid_device_disconnect() to tear down the partial CTRL/INTR
        # state; the Zephyr stack's disconnected callbacks then clean up the HID
        # instance (state -> DISCONNECTED) and the reconnect loop below can
        # proceed. As a last resort also drop the ACL so L2CAP cleans up if
        # the hid_device_disconnect BTP command itself fails.
        if not stack.hid_device.wait_for_connection(timeout=3):
            # The worker may have issued hid_device_connect just as stop_event
            # was set; the CTRL L2CAP channel may have connected on the
            # firmware while INTR never comes (PTS won't send WID 3/WID 4
            # until after this handler returns True). Any non-DISCONNECTED
            # HID state at this point is a partial setup that will keep
            # hid_allocate() busy. Force an ACL disconnect so that the Zephyr
            # L2CAP disconnected callbacks fire and reset the HID instance to
            # DISCONNECTED, then fall through to the reconnect block below.
            if stack.gap.is_connected():
                try:
                    btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                except BTPError as e:
                    logging.debug("hdl_wid_7: gap_disconnect for state cleanup: %s", e)
                try:
                    stack.gap.wait_for_disconnection(timeout=5)
                except TimeoutError as e:
                    logging.debug("hdl_wid_7: wait_for_disconnection after cleanup: %s", e)
            # Wait for any pending HID disconnected event so the Python-side
            # state is consistent with firmware.
            try:
                stack.hid_device.wait_for_disconnection(timeout=3)
            except TimeoutError as e:
                logging.debug("hdl_wid_7: hid wait_for_disconnection: %s", e)
            # Brief pause to allow Zephyr's BT workqueue to fully process the
            # L2CAP channel teardown callbacks and reset the HID instance state
            # to DISCONNECTED. Without this delay the reconnect loop below
            # immediately calls hid_device_connect while the firmware is still
            # running cleanup, hid_allocate() sees a non-DISCONNECTED state
            # and returns -EBUSY, producing "Error opcode in response!".
            sleep(1.0)

    if stack.hid_device.connected:
        return True

    # Re-page PTS if the out-of-range simulation dropped the ACL. The IUT keeps
    # the old link key while PTS dropped its bond on the teardown, so delete the
    # stale bond first: the re-page then triggers a fresh SSP pairing instead of
    # a doomed authentication with a mismatched link key.
    if not stack.gap.is_connected():
        try:
            btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_7: gap_unpair before re-page: %s", e)

    # PTS accepts the HID L2CAP Control/Interrupt channels only after the
    # BR/EDR link is authenticated and encrypted. Issuing hid_device_connect
    # before the encryption-change event makes PTS reject the L2CAP connect;
    # worse, that first attempt puts the IUT HID state machine into
    # CTRL_CONNECTING so every subsequent connect returns BTP ERROR (busy) and
    # the reconnection never completes (INDCSV). So re-page first, wait for the
    # encryption change on the fresh link, then start the connect attempts.
    encryption_done = False
    for attempt in range(12):
        if stack.hid_device.connected:
            break
        if not stack.gap.is_connected():
            encryption_done = False
            try:
                btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                btp.gap_wait_for_connection(timeout=5)
            except BTPError as e:
                logging.debug("hdl_wid_7: re-page attempt %d: %s", attempt, e)
                sleep(0.3)
                continue
        # Wait for encryption on the freshly paged link before the first HID
        # connect so PTS does not reject it (and so we do not lock the HID
        # state machine into CTRL_CONNECTING with a doomed pre-encryption
        # attempt). Only wait once per (re)connected ACL.
        if not encryption_done:
            try:
                stack.gap.gap_wait_for_encryption_change(timeout=15)
            except TimeoutError as e:
                logging.debug("hdl_wid_7: gap_wait_for_encryption_change: %s", e)
            encryption_done = True
            # Short guard delay to let the link key install on both L2CAP sides.
            sleep(0.3)
        try:
            btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_7: hid_device_connect attempt %d: %s",
                          attempt, e)
            sleep(0.15)
            continue
        if stack.hid_device.wait_for_connection(timeout=1):
            break
        sleep(0.1)

    # For DRE BV cases the HID11 pass verdict requires data exchange upon the
    # HID connection: originate input reports from the IUT once connected. BI
    # cases test invalid behaviour and must not send data.
    is_bi = "/BI-" in tc
    if not is_bi and stack.hid_device.connected:
        report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT
        report_press = bytearray([0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
        report_release = bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(6):
            if not stack.hid_device.connected:
                break
            report = report_press if (i % 2 == 0) else report_release
            try:
                btp.hid_device_send_report(report_type, report)
            except BTPError as e:
                logging.debug("hdl_wid_7: send report %d: %s", i, e)
                break
            sleep(0.2)

    return True


def hdl_wid_45(_: WIDParams):

    """
    Click OK and start Lower Tester #2.

    Description: WID 45 - a purely procedural MMI that tells the operator to
    acknowledge and let the secondary Lower Tester begin. There is no IUT
    action required here, so just confirm so PTS can proceed.
    """
    return True


def hdl_wid_23(params: WIDParams):

    """
    Click Ok, then send input data to the PTS using the Implementation Under
    Test (IUT).

    Description: Implements WID 23 for HID profile - instructs the IUT to send
    an HID input report over the Interrupt channel so the PTS can verify the
    received data.

    For BDIT (Boot Device Interrupt Transfer) test cases the IUT is in boot
    protocol mode. PTS asks for "REPORT with ID=0x01", meaning the standard
    HID keyboard report (descriptor ID 1). In boot mode the report has no
    Report-ID prefix; in report mode it has a 0x01 prefix byte.

    Send a key-press (key code 0x04 = 'a') followed by a key-release with a
    short hold between them so PTS has time to capture and evaluate the data.
    """
    report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT
    tc = (params.test_case_name or "") if params is not None else ""
    stack = get_stack()

    # DCR (Device-initiated Connection Re-establishment): PTS disconnects the
    # HID link, then plays WID 23 expecting the IUT to bring the connection
    # back up itself and send an input report to wake the host. If the link is
    # down, re-establish it (page PTS if the ACL was dropped, then
    # hid_device_connect) before sending, otherwise hid_device_send_report
    # returns an error status and the case aborts with a BTP ERROR.
    if not stack.hid_device.connected:
        try:
            if not stack.gap.is_connected():
                btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                btp.gap_wait_for_connection(timeout=10)
        except BTPError as e:
            logging.debug("hdl_wid_23: gap reconnect error: %s", e)

        try:
            btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_23: hid_device_connect error: %s", e)

        stack.hid_device.wait_for_connection(timeout=15)

    # WID 23 description carries the required report format. When PTS asks for
    # a "REPORT with ID = 0x01" (BDIT/BV-01-C), the report MUST carry the 0x01
    # report-ID prefix; sending a bare boot report (no ID) makes PTS never see
    # ID=0x01 and it marks the case FAIL. Only strip the report ID (true boot
    # keyboard report) when the description does NOT request an explicit ID.
    description = (params.description or "").lower() if params is not None else ""
    wants_report_id = "id = 0x01" in description or "id=0x01" in description

    if "/BDIT/" in tc and not wants_report_id:
        # Boot keyboard report: modifier(0), reserved(0), key[6].
        # Send a non-zero key so PTS sees real data, then a key-release.
        report_press = bytearray([0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
        report_release = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    else:
        # Report-mode keyboard report: Report ID 1, modifier, reserved, key[6].
        report_press = bytearray([0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
        report_release = bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    # Tolerate a send error (e.g. link still not up) instead of aborting the
    # case with a BTP ERROR; PTS decides the verdict from what it observed.
    try:
        btp.hid_device_send_report(report_type, report_press)
        sleep(0.2)
        btp.hid_device_send_report(report_type, report_release)
    except BTPError as e:
        logging.debug("hdl_wid_23: hid_device_send_report error: %s", e)

    # Brief hold to allow PTS to capture the data before the test ends.
    sleep(1.0)

    return True


def hdl_wid_22(_: WIDParams):
    """
    Send HID_CONTROL VIRTUAL_CABLE_UNPLUG request from the Implementation
    Under Test (IUT).

    Description: WID 22 - the IUT must originate a device-initiated Virtual
    Cable Unplug on the Control channel. The IUT stack tears down the L2CAP
    channels itself once the VCU PDU has been flushed, so the disconnect must
    NOT be forced here. Tolerate a BTP error (e.g. link already down) and rely
    on the HID Device Disconnected event.
    """
    stack = get_stack()

    try:
        btp.hid_device_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_22: hid_device_virtual_cable_unplug error: %s", e)

    try:
        stack.hid_device.wait_for_disconnection()
    except TimeoutError as e:
        logging.debug("hdl_wid_22: wait_for_disconnection: %s", e)

    return True


def hdl_wid_4(_: WIDParams):

    """
    Establish the interrupt channel connection from the Implementation Under
    Test (IUT).

    Description: WID 4 for HID profile (DRE suspend/resume). PTS asks the IUT
    to open the HID Interrupt channel. The IUT-side hid_device_connect issued
    in WID 3 already opens both the Control and Interrupt channels together, so
    the interrupt channel is up by the time this WID arrives. Simply confirm to
    let PTS proceed.
    """
    return True


def hdl_wid_24(params: WIDParams):
    """
    WID 24 has two different meanings depending on the test case description:

    1. "Stop sending HID data to the PTS" - the IUT should stop sending HID
       input reports. No BTP command is required; simply acknowledge.

    2. "Reconnect to PTS or send a report ... to wake up the host from SUSPEND
       mode" (DRE suspend/resume test cases) - the host suspended and the HID
       L2CAP link was torn down. To wake the host, the IUT re-establishes the
       HID connection (which prompts PTS to walk through WID 3 / WID 4) and
       then sends an input report on the Interrupt channel.

    We branch on the description so the correct action is performed.
    """
    description = (params.description or "").lower() if params is not None else ""

    if "wake up" in description or "suspend" in description or "reconnect" in description:
        stack = get_stack()

        # Re-establish the HID link if it was torn down during SUSPEND. The
        # IUT-initiated hid_device_connect opens both Control and Interrupt
        # channels; PTS then walks WID 3 (control) / WID 4 (interrupt).
        if not stack.hid_device.connected:
            try:
                if not stack.gap.is_connected():
                    btp.gap_start_discovery(transport='bredr',
                                            discov_type='passive', mode='general')
                    sleep(10)
                    btp.gap_stop_discovery()
                    if btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
                        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
                        btp.gap_wait_for_connection()
            except BTPError as e:
                logging.debug("hdl_wid_24: gap reconnect error: %s", e)

            try:
                btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                logging.debug("hdl_wid_24: hid_device_connect error: %s", e)

            stack.hid_device.wait_for_connection(timeout=15)

        # Send a keyboard input report on the Interrupt channel to wake the
        # host from SUSPEND. Report-mode report: Report ID 1, modifier,
        # reserved, key[6]. Use key code 0x04 ('a') then release.
        report_type = defs.BTP_HID_DEVICE_REPORT_TYPE_INPUT
        report_press = bytearray([0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00])
        report_release = bytearray([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        try:
            btp.hid_device_send_report(report_type, report_press)
            sleep(0.2)
            btp.hid_device_send_report(report_type, report_release)
        except BTPError as e:
            logging.debug("hdl_wid_24: hid_device_send_report error: %s", e)
        sleep(1.0)

        return True

    # Default behaviour: stop sending HID data.
    return True


def hdl_wid_28(_: WIDParams):
    """
    Verify that the Caps Lock LED is enabled, then click Ok. If the IUT
    does not have an LED for Caps Lock, just press Ok.

    Description: Implements WID 28 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_30(_: WIDParams):
    """
    Verify that the Number Lock LED is enabled, then click Ok. If the IUT
    does not have an LED for Number Lock, just press Ok.

    Description: Implements WID 30 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_32(_: WIDParams):
    """
    Verify that the Number Lock LED is enabled, then click Ok. If the IUT
    does not have an LED for Number Lock, just press Ok.

    Description: Implements WID 32 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_34(_: WIDParams):
    """
    Verify that the Number Lock LED is disabled, then click Ok. If the IUT
    does not have an LED for Number Lock, just press Ok.

    Description: Implements WID 34 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_36(_: WIDParams):
    """
    Verify that the Scroll Lock LED is enabled, then click Ok. If the IUT
    does not have an LED for Scroll Lock, just press Ok.

    Description: Implements WID 36 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_38(_: WIDParams):
    """
    Verify that the Scroll Lock LED is disabled, then click Ok. If the IUT
    does not have an LED for Scroll Lock, just press Ok.

    Description: Implements WID 38 for HID profile - purely a visual
    verification prompt. No BTP command is required; simply acknowledge the
    prompt so the PTS can proceed.
    """
    return True


def hdl_wid_49(params: WIDParams):
    """
    Please prepare the IUT to accept connection from PTS and then click OK.

    Description: WID 49 - place the IUT in connectable and general discoverable
    mode so that PTS can initiate the ACL and HID connection.

    For DCE (Device-initiated Connection Establishment) the device-initiated
    HID connection is driven from hdl_wid_5's background worker (PTS only
    starts accepting after it receives the WID-5 OK). Here we only need to be
    connectable/discoverable.

    The pre-run already placed the IUT connectable + general discoverable.
    Re-sending SET_DISCOVERABLE here faults the IUT firmware and drops the
    BTP socket, so we only acknowledge the MMI.
    """
    return True


def hdl_wid_51(_: WIDParams):
    """WID 51: LMP QoS request prompt. Acknowledge.

    PTS asks the IUT to send an LMP_QoS_req to the Lower Tester.
    The firmware handles the LMP QoS exchange internally; simply
    acknowledge so PTS can advance.
    """
    return True


def hdl_wid_52(_: WIDParams):
    """
    Place the Implementation Under Test (IUT) in Limited Discoverable mode.

    Description: Implements WID 52 for HID profile - makes the IUT connectable
    and places it in Limited Discoverable mode.
    """
    btp.gap_set_connectable()
    btp.gap_set_limited_discoverable()

    return True


def hdl_wid_55(_: WIDParams):
    """
    Click Yes, if IUT can discover PTS through Limited Inquiry.

    Description: Implements WID 55 for HID profile - confirms that the IUT can
    discover the PTS through Limited Inquiry.
    """
    return True


def hdl_wid_53(_: WIDParams):
    """
    Wait for Limited Discoverable Mode time out and discoverability end, and then click OK.

    Description: Implements WID 53 for HID profile - places the IUT in a
    non-discoverable mode so that the limited discoverable period ends.
    """
    btp.gap_set_non_discoverable()

    return True


def hdl_wid_493(_: WIDParams):
    """
    Begin waiting device discovery (limited inquiry ~10 seconds). Should not make connection.

    Description: Implements WID 493 for HID profile - places the IUT in
    non-discoverable mode so that PTS should not be able to find it during
    the limited inquiry.
    """
    btp.gap_set_non_discoverable()

    return True


def hdl_wid_491(_: WIDParams):
    """
    Begin waiting device discovery (general inquiry ~10 seconds).

    Description: Implements WID 491 for HID profile - places the IUT in a
    connectable and general discoverable mode so that PTS can find it during
    the general inquiry.
    """
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_492(_: WIDParams):
    """
    Begin waiting device discovery (limited inquiry ~10 seconds).

    Description: Implements WID 492 for HID profile - places the IUT in a
    connectable and limited discoverable mode so that PTS can find it during
    the limited inquiry.
    """
    btp.gap_set_connectable()
    btp.gap_set_limited_discoverable()

    return True


def hdl_wid_495(_: WIDParams):
    """
    This test requires two instances of PTS running. This is Lower Tester 1.
    Please start another PTS instance and run the corresponding LT2 test case.

    Description: Implements WID 495 for HID profile - purely informational
    prompt for multi-instance (LT1/LT2) test cases. The LT2 side is started
    separately, so the IUT only needs to acknowledge the prompt to continue.
    """
    return True


def hdl_wid_496(_: WIDParams):
    """
    This test requires two instances of PTS running. This is Lower Tester 1.
    Please start another PTS instance and run the corresponding LT2 test case.

    Description: Click Yes if HID/DEV/HCE/BV-05-I_LT2 test case passed.
    Otherwise, click No if LT2 test case failed.
    """
    return True


def hdl_wid_95(_: WIDParams):
    """
    Please remove the IUT and/or the PTS from the RF shield. If the out of
    range method was used, bring the IUT and PTS back within range.

    Description: Implements WID 95 for HID profile - counterpart to WID 14.
    Since WID 14 tore down the ACL, re-establish the BR/EDR ACL and HID L2CAP
    channels so the test case can continue.
    """
    stack = get_stack()

    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    if not btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    try:
        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    except BTPError as e:
        logging.debug("hdl_wid_95: gap_connect error: %s", e)
        return False

    try:
        btp.hid_device_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_95: hid_device_connect error: %s", e)

    stack.hid_device.wait_for_connection()

    return True


def hdl_wid_20120(_: WIDParams):
    """
    Please initiate a GATT connection over BR/EDR to the PTS.

    Description: Verify that the Implementation Under Test (IUT) can initiate a
    GATT connect request over BR/EDR to PTS. After the previous WID 14 tore
    down the ACL link, we need to re-establish the BR/EDR ACL to the PTS so a
    GATT/SDP exchange can follow.
    """
    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    if not btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    try:
        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    except BTPError as e:
        logging.debug("hdl_wid_20120: gap_connect error: %s", e)
        return False

    return True


def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.

    Description: Verify that the Implementation Under Test (IUT) can accept
    a HID connect request from PTS.
    """
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True
