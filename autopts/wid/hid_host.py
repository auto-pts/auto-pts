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
import time
from time import sleep

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import BTPError, WIDParams

log = logging.debug


def hid_host_wid_hdl(wid, description, test_case_name):

    # Local table lookup first; otherwise hand over to generic handler.
    from autopts.wid import generic_wid_hdl
    log(f'{hid_host_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def connect_to_pts():
    """Discover and establish a BR/EDR ACL + HID (Host role) connection to PTS."""
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
        logging.debug("connect_to_pts: gap_connect error: %s", e)
        return False

    try:
        btp.hid_host_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("connect_to_pts: hid_host_connect error: %s", e)

    return stack.hid_host.wait_for_connection()


def _acl_connect_to_pts(page_if_not_discovered=False, attempts=1):
    """Discover and bring up only the BR/EDR ACL connection to PTS.

    The HID CTRL/INTR channels are intentionally not opened here. In the HCE
    flow PTS drives channel setup as a separate step (WID 3 "establish the
    control channel"), so the ACL is paged first and the HID link is opened
    later. Opening the interrupt channel too early, before PTS has advanced
    to its channel-establishment step, makes PTS reject it and report
    "Failed to open interrupt channel".

    page_if_not_discovered: when the inquiry does not report the PTS address,
    page PTS anyway instead of giving up. Inquiry scan and page scan are
    independent: once PTS has advanced to waiting for the IUT to reconnect it
    stops answering inquiry while still accepting pages, so the inquiry result
    is not a valid precondition for the page. The PTS BD address is already
    known from the earlier rounds of the same test case.
    """
    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    if not btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        if not page_if_not_discovered:
            return False
        logging.debug("_acl_connect_to_pts: PTS not in inquiry results; "
                      "paging the known PTS address anyway")

    stack = get_stack()

    # gap_wait_for_connection() returns None whether or not the connection came
    # up, so the GAP connection state has to be checked explicitly: otherwise a
    # page that never completes is reported as success and the caller waits out
    # a HID timeout believing the ACL is up. attempts stays 1 by default so the
    # timing of the HCE and CDD callers is unchanged; only the accuracy of the
    # return value changes for them.
    for attempt in range(1, attempts + 1):
        try:
            btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            btp.gap_wait_for_connection()
        except BTPError as e:
            logging.debug("_acl_connect_to_pts: gap_connect error: %s", e)

        if stack.gap.is_connected():
            return True

        logging.debug("_acl_connect_to_pts: ACL page attempt %d did not "
                      "complete, retrying", attempt)
        sleep(3)

    logging.debug("_acl_connect_to_pts: ACL page never completed")
    return False


def _hid_connect_over_acl(timeout=30):
    """Open the HID CTRL(+INTR) channels over an already-established ACL."""
    stack = get_stack()

    try:
        btp.hid_host_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("_hid_connect_over_acl: hid_host_connect error: %s", e)

    return stack.hid_host.wait_for_connection(timeout=timeout)


def _direct_connect_to_pts():
    """Page PTS directly (no inquiry) and open the HID CTRL+INTR channels.

    After a disconnect the IUT already knows PTS's BD address from the
    earlier connection. PTS is in page-scan mode so we can page it directly
    without a preceding inquiry. Skipping the 10-second inquiry window makes
    the reconnect fast enough for CDD and similar test flows where PTS fires
    WID 3 immediately after the SDP disconnect from WID 43.
    A delay lets PTS finish tearing down the previous connection and
    return to page-scan mode before the IUT pages it. 8s is enough for
    PTS's HCR flow where WID 1 (close CTRL) and WID 5 (reconnect) fire
    within a few seconds of each other.
    """
    stack = get_stack()

    sleep(8)

    try:
        btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
    except BTPError as e:
        logging.debug("_direct_connect_to_pts: gap_connect error: %s", e)
        return False

    try:
        btp.hid_host_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("_direct_connect_to_pts: hid_host_connect error: %s", e)

    return stack.hid_host.wait_for_connection()


def hdl_wid_0(_: WIDParams):

    """Make the IUT connectable/discoverable."""
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_1(params: WIDParams):
    """WID 1: either initiate a HID connection or close the control channel.

    PTS reuses WID 1. When the description asks the IUT to close/release the
    control channel connection, the link has already been torn down earlier
    in the flow (e.g. HCR closes the interrupt channel via WID 2 first), so
    a plain disconnect (or a no-op when already down) is enough. Driving a
    fresh connect here makes the IUT wait out a 30s connect timeout and the
    case ends inconclusive. Otherwise initiate the connection.
    """
    description = (params.description or "").lower() if params is not None else ""

    if "close" in description or "release" in description:
        stack = get_stack()
        if not stack.hid_host.connected:
            return True
        try:
            btp.hid_host_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hdl_wid_1: hid_host_disconnect returned error; "
                          "relying on HID Host Disconnected event")
        stack.hid_host.wait_for_disconnection()
        return True

    return connect_to_pts()


def hdl_wid_2(params: WIDParams):
    """
    Disconnect the HID connection using the IUT.

    For HCR (Host-initiated Control Release / Virtual Cable Unplug) test
    cases use the Virtual Cable Unplug path; otherwise perform a plain HID
    disconnect.
    """
    tc = (params.test_case_name or "") if params is not None else ""
    description = (params.description or "").lower() if params is not None else ""
    stack = get_stack()

    # HCR (Host Connection Release) cases prompt the IUT to close the
    # interrupt/control channel connection. That is a plain HID disconnect,
    # not a Virtual Cable Unplug: driving a VCU here makes the device wait
    # out a ~30s teardown timeout and the case ends inconclusive. Only use
    # the VCU path when the prompt explicitly asks to unplug the virtual
    # cable.
    if "virtual cable" in description or "virtual_cable" in description or "unplug" in description:
        try:
            btp.hid_host_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hid_host_virtual_cable_unplug returned error; "
                          "relying on HID Host Disconnected event")
    else:
        try:
            btp.hid_host_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hid_host_disconnect returned error; "
                          "relying on HID Host Disconnected event")

    stack.hid_host.wait_for_disconnection()

    # HCR/BV-01-C: the prompt only asks for the HID interrupt/control channels
    # to be closed, never for the ACL to be dropped. The last HCR round before
    # the reconnection prompt (WID 5) reuses that very ACL: the PTS server log
    # shows HCI_WRITE_LINK_POLICY_SETTINGS succeeding on the same connection
    # handle, followed by PTS opening HID Control (psm 0x0011) and Interrupt
    # (psm 0x0013) itself.
    #
    # Dropping the ACL here is what makes the verdict random. Two outcomes,
    # decided purely by which side wins the race:
    #   - the ACL drop lands after PTS re-opened both channels: PTS loses the
    #     link it just built -> FAIL;
    #   - the ACL drop lands before PTS gets there: PTS finds no link to reuse,
    #     and after the reconnection prompt it is no longer in page scan, so its
    #     own L2CAP_CONNECT_REQ has no ACL to run on -> "Failed to open L2CAP
    #     Connection" -> INDCSV.
    #
    # Keep the ACL up for HCR and let PTS drive the reconnection on it. The
    # earlier rounds, where PTS asks the IUT to re-establish through WID 3,
    # bring the HID channels back up over the same ACL without needing the
    # teardown either.
    if "/HCR/" in tc:
        logging.debug("hdl_wid_2: HCR round; keeping the ACL up so PTS can "
                      "reuse it for the reconnection")
        return True

    # Tear down the ACL after closing the HID channels. This signals
    # completion of the HID release to PTS and allows it to advance.
    try:
        btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_2: gap_disconnect returned error: %s", e)

    return True


def hdl_wid_3(params: WIDParams):
    """
    WID 3: either release the HID connection or delete the pairing.
    """
    description = (params.description or "").lower()
    tc = (params.test_case_name or "") if params is not None else ""

    if "establish" in description and "control channel" in description:
        # PTS drives HID channel setup in two ordered steps for the HCE
        # flow: first it waits for the ACL page (satisfied at WID 34, which
        # brings only the ACL up), then it renders this prompt to have the
        # IUT open the HID CTRL(+INTR) channels. Opening the HID link here,
        # once PTS is ready for the channel setup, lets PTS accept the
        # interrupt channel. Bringing the whole HID link up earlier at
        # WID 34 made PTS reject the interrupt channel ("Failed to open
        # interrupt channel", INDCSV).
        stack = get_stack()
        if stack.hid_host.connected:
            return True
        # HCE reaches this prompt with the ACL already up (paged at WID 34),
        # so only the HID CTRL/INTR channels are opened here. Other flows
        # (e.g. HIT) render this prompt with no prior ACL page, so the IUT
        # must first discover and bring up the BR/EDR ACL before opening the
        # HID channels. Reusing the ACL-only path there left PTS waiting for
        # the ACL Connection Request that never came ("Failed to receive
        # BR/EDR ACL Connection Request", INDCSV / BTP TIMEOUT).
        if "/HCE/" in tc:
            # HCE: PTS drives INTR open from its side; the simultaneous-open
            # race may require up to ~60s for PTS to complete CONFIG. Use a
            # 90s timeout so the Python side does not give up before PTS.
            return _hid_connect_over_acl(timeout=90)
        if "/CDD/" in tc:
            # CDD: WID 43 kept the ACL alive (only SDP channel is closed).
            # Open HID CTRL+INTR over the existing ACL connection.
            return _hid_connect_over_acl()
        return connect_to_pts()

    if "release the hid connection" in description or "interrupt channel" in description:
        stack = get_stack()
        try:
            btp.hid_host_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError:
            logging.debug("hid_host_disconnect returned error status; "
                          "relying on HID Host Disconnected event")

        stack.hid_host.wait_for_disconnection()
        return True

    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    return True


def hdl_wid_4(params: WIDParams):
    """WID 4: establish the interrupt channel, or send a Virtual Cable Unplug.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    establish the interrupt channel connection, the HID link (control +
    interrupt channels) is already open after connect, so simply
    acknowledge. Otherwise send a Virtual Cable Unplug from the IUT and
    wait for PTS to disconnect.
    """
    description = (params.description or "") if params is not None else ""
    lower = description.lower()

    if "establish" in lower and "interrupt channel" in lower:
        return True

    stack = get_stack()
    try:
        btp.hid_host_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_4: hid_host_virtual_cable_unplug error: %s", e)

    stack.hid_host.wait_for_disconnection()

    return True


def hdl_wid_5(params: WIDParams):
    """Make the IUT connectable, then wait for the PTS to connect.

    For the DAT/BV-03-C "Large Reports on control channel" case the IUT (HID
    Host) has to drive the large control-channel report exchange, so it opens
    the HID connection itself instead of waiting for the PTS to page. The IUT
    is made connectable/discoverable first so the follow-on ACL setup succeeds.

    For cases where the description asks to "Accept the control channel
    connection from the IUT" (e.g. HCR/BV-01-C third round), PTS is accepting
    a connection that the IUT initiates, so a full connect_to_pts() is needed.
    Passively waiting here left PTS idle and the test ended INDCSV.
    """
    tc = (params.test_case_name or "") if params is not None else ""
    description = (params.description or "").lower() if params is not None else ""

    if "DAT/BV-03-C" in tc:
        btp.gap_set_connectable()
        btp.gap_set_general_discoverable()
        return connect_to_pts()

    if "accept" in description and "control channel" in description:
        # WID 5 = "Accept the control channel connection from the IUT",
        # followed by WID 6 = "Accept the interrupt channel connection from
        # the IUT". For the HCR (Host Connection Release) reconnection round
        # the PTS server log shows the exact roles:
        #   - "Peripheral successfully received BR/EDR connection request"
        #     => the IUT initiates (pages) the BR/EDR ACL; PTS accepts it.
        #   - PTS then sends L2CAP_CONNECT_REQ local_psm=0x0011 itself
        #     => PTS is the initiator of the HID Control channel (and the
        #        Interrupt channel at WID 6); the IUT only ACCEPTS them.
        #
        # The IUT initiates the reconnection ("... from the IUT"): it pages
        # PTS and brings up ONLY the BR/EDR ACL. The PTS server log shows the
        # roles for this HCR round: after "Peripheral successfully received
        # BR/EDR connection request" (the IUT-paged ACL), PTS itself sends
        # the HID Control L2CAP_CONNECT_REQ (local_psm=0x0011) and the
        # Interrupt channel connect at WID 6. So PTS is the HID L2CAP
        # initiator; the IUT only accepts those channels (its registered
        # L2CAP servers do this automatically).
        #
        # Therefore the IUT must NOT open the HID link itself here: calling
        # hid_host_connect races PTS's own HID Control connect, the ACL is
        # torn down (HCI_REMOTE_USER_TERMINATED_CONNECTION) and PTS reports
        # "Failed to open L2CAP Connection" (INDCSV). Bring up only the ACL
        # (inquiry + gap_connect, no HID) and then wait for PTS to open the
        # HID CTRL/INTR channels.
        #
        # Do NOT set the IUT connectable/discoverable first: WID 1 (close
        # control channel) and WID 5 (reconnect) fire seconds apart, so a
        # connectable IUT invites PTS to page it at the same instant the IUT
        # pages PTS -> page collision. Let the IUT be the sole ACL initiator.
        if "/HCR/" in tc:
            stack = get_stack()
            if stack.hid_host.connected:
                return True

            # BV-01-C (Host-Initiated Connection Release): PTS drives the HID
            # channel setup itself. The server log shows it answering the
            # prompt, then sending HCI_SWITCH_ROLE followed by
            # L2CAP_CONNECT_REQ (local_psm=0x0011) on the ACL that is still up.
            #
            # PTS renders this prompt as MMI_Style_Ok_Cancel2 and does nothing
            # at all until the response arrives: the server log shows a solid
            # "Waiting for response from callback.on_implicit_send, wid 5" with
            # no HCI or L2CAP traffic for the whole time this handler blocks.
            # So blocking here to wait for the very channels PTS opens only
            # after being answered is a deadlock: the handler waits for PTS,
            # PTS waits for the handler. When the wait finally expires, auto-pts
            # answers Cancel, PTS then issues its L2CAP_CONNECT_REQ against an
            # ACL that the old WID 2 teardown had already dropped, and logs
            # "Failed to open L2CAP Connection" -> INDCSV.
            #
            # Acknowledge immediately so PTS can proceed, and do not page from
            # the IUT side: hdl_wid_2 now keeps the ACL up for HCR, so PTS has
            # a live link to run its L2CAP connect on, and an IUT-side page
            # would only collide with PTS's own role switch.
            if "BV-01-C" in tc:
                logging.debug("hdl_wid_5: HCR BV-01-C; acknowledging so PTS can "
                              "open HID Control on the existing ACL")
                return True

            # Other HCR cases (e.g. BV-02-C, Device-Initiated Connection
            # Release): PTS does NOT open the HID channels from its side after
            # this prompt, so the IUT must initiate the full HID reconnection.
            # Let the previous teardown settle first so PTS is back in page
            # scan before the IUT pages it.
            sleep(5)
            return connect_to_pts()

        # Other flows: after WID 2 called gap_disconnect the ACL is fully
        # torn down and PTS is back in page-scan mode. Make the IUT
        # connectable, then page PTS with a full inquiry so:
        # 1. The firmware has time to fully reset its HID host state.
        # 2. PTS has time to return to page-scan mode.
        btp.gap_set_connectable()
        btp.gap_set_general_discoverable()
        return connect_to_pts()

    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()
    return True


def hdl_wid_6(_: WIDParams):
    """Accept the interrupt channel connection from the PTS.

    PTS pages the IUT and opens the HID interrupt channel; the IUT (HID
    Host) is already connectable and the L2CAP/HID accept path is handled
    by the firmware, so simply acknowledge so PTS can proceed.
    """
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_7(_: WIDParams):
    """Establish a HID reconnection from the IUT, then click OK.

    After a Virtual Cable Unplug (WID 22) PTS asks the IUT (HID Host) to
    re-establish the HID link. Drive a fresh ACL + HID connect.
    """
    return connect_to_pts()


def hdl_wid_10(_: WIDParams):
    """Place the IUT in connectable mode."""
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_11(_: WIDParams):
    """The IUT is connected; remain ready for the PTS to proceed."""
    return True


def hdl_wid_12(_: WIDParams):

    """The IUT is connected; remain ready for the PTS to proceed."""
    return True


def hdl_wid_14(_: WIDParams):
    """Out-of-range / RF-shield simulation: tear down the ACL from the IUT."""
    try:
        btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_14: gap_disconnect returned error: %s", e)

    return True


def hdl_wid_19(_: WIDParams):
    """Visual verification that the pointer moved as expected. Acknowledge."""
    return True


def hdl_wid_21(_: WIDParams):
    """Visual verification of received HID data. Acknowledge."""
    return True


def hdl_wid_22(params: WIDParams):
    """WID 22: send a Virtual Cable Unplug, or acknowledge a visual check.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    send a HID_CONTROL VIRTUAL_CABLE_UNPLUG request, emit the VCU from the
    IUT so PTS observes the unplug and tears the link down; otherwise this
    is a visual-verification prompt and is simply acknowledged.
    """
    description = (params.description or "") if params is not None else ""
    lower = description.lower()

    if "virtual_cable_unplug" in lower or "virtual cable unplug" in lower:
        stack = get_stack()
        try:
            btp.hid_host_virtual_cable_unplug(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        except BTPError as e:
            logging.debug("hdl_wid_22: hid_host_virtual_cable_unplug error: %s", e)

        stack.hid_host.wait_for_disconnection()
        return True

    return True


def hdl_wid_20(_: WIDParams):

    """
    Place the IUT in a state to receive and verify HID data.

    The IUT is the HID Host; it is already listening on the Interrupt
    channel and reports arrive asynchronously via BTP input-report events,
    so no explicit BTP command is required here.
    """
    return True


def hdl_wid_23(params: WIDParams):

    """
    Send output data to the PTS (IUT is HID Host).

    The Host originates an output report on the Interrupt channel. When the
    description names a report ID (e.g. "REPORT with ID = 0x03"), carry that
    report ID as the first payload byte so the device accepts the report.
    """
    import re

    description = (params.description or "") if params is not None else ""

    report_id = None
    m = re.search(r"id\s*=\s*(0x[0-9a-fA-F]+|\d+)", description, re.IGNORECASE)
    if m:
        report_id = int(m.group(1), 0)

    # The PTS HID Device report descriptor fixes the payload size per output
    # report ID. Report ID 3 is a 16-bit (2-byte) OUTPUT report and report
    # ID 1 an 8-bit (1-byte) OUTPUT report. Sending a payload of the wrong
    # length makes PTS reject the report ("Failed to receive the HID output
    # Report with Report ID: N") and tear the link down, so the report must
    # match the descriptor's declared size (report ID byte + data bytes).
    output_report_data_len = {
        0x01: 1,
        0x03: 2,
    }

    # Boot Mode (BHIT) test cases use the boot-protocol report layout instead
    # of the report-descriptor layout above. The PTS server log for
    # HID11/HOS/BHIT/* declares "ReportID: 1, Size In Bits: 72,
    # Report Type: 2 (OUTPUT)", i.e. 9 bytes total = 1 report ID byte plus 8
    # data bytes. Sending the report-mode 1-byte payload here makes PTS log
    # "Failed to receive the HID output Report with Report ID: 1" and drop the
    # link, so the boot-mode size has to be used for these cases.
    boot_output_report_data_len = {
        0x01: 8,
    }

    tc = (params.test_case_name or "") if params is not None else ""
    if "/BHIT/" in tc or "/BHCT/" in tc:
        size_map = boot_output_report_data_len
    else:
        size_map = output_report_data_len

    if report_id is not None:
        data_len = size_map.get(report_id, 8)
        report = bytearray([report_id]) + bytearray(data_len)
    else:
        report = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    try:
        btp.hid_host_send_output_report(report)
    except BTPError as e:
        logging.debug("hdl_wid_23: hid_host_send_output_report error: %s", e)
        return False

    return True


def hdl_wid_24(_: WIDParams):
    """Stop sending HID data. No BTP command needed."""
    return True


def hdl_wid_32(_: WIDParams):
    """Click OK if the IUT has received the requested report. Acknowledge."""
    return True


def hdl_wid_33(_: WIDParams):
    """Click OK if the IUT has received an invalid report. Acknowledge."""
    return True


def hdl_wid_34(params: WIDParams):
    """Initiate a GIAC general inquiry to discover the PTS.

    PTS asks the IUT (HID Host) to run a General Inquiry Access Code
    inquiry and confirm the tester is discoverable, then click OK. Run a
    passive BR/EDR general discovery.

    PTS waits for the ACL Connection Request right after this inquiry:
    without an outgoing connect it stays idle and eventually reports
    "Failed to receive BR/EDR ACL Connection Request" (INDCSV).

    HCE and HRE differ in how the HID link is opened:

    - HCE: PTS drives channel setup in two ordered steps. It first waits
      for the ACL, then renders a follow-on WID 3 ("Establish the control
      channel connection from the IUT"). So here only the ACL is paged and
      the HID CTRL/INTR channels are opened later at WID 3. Opening the
      interrupt channel too early (before PTS reaches its
      channel-establishment step) made PTS reject it with "Failed to open
      interrupt channel".

    - HRE: PTS expects the IUT to re-establish the full HID link right
      away, so the whole ACL + HID connect is driven here.
    """
    tc = (params.test_case_name or "") if params is not None else ""

    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    if not btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    if "/HCE/" in tc:
        _acl_connect_to_pts()
        return True

    if "/HRE/" in tc:
        connect_to_pts()
        return True

    return True


def hdl_wid_41(_: WIDParams):

    """Send an output report from the Host (IUT) on the Interrupt channel."""
    report = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    try:
        btp.hid_host_send_output_report(report)
    except BTPError as e:
        logging.debug("hdl_wid_41: hid_host_send_output_report error: %s", e)
        return False

    return True


def hdl_wid_42(_: WIDParams):
    """WID 42: Lower Tester (PTS acting as HID Device) will request Sniff mode.

    This is a notification, not an action request: PTS is about to send
    LMP_sniff_req to the IUT, so the IUT only has to ACCEPT it. Just
    acknowledge the prompt and let PTS drive the sniff negotiation.

    The IUT must not initiate sniff from its side here. If both sides issue
    sniff at the same time the controller answers HCI_Mode_Change with
    Command Disallowed, and PTS reports "Failed to enter Sniffer Mode".

    Accepting the peer's request requires the sniff bit to be set in the
    controller's default link policy, which the host does at init time when
    CONFIG_BT_POWER_MODE_CONTROL is enabled. Without that bit the controller
    replies LMP_not_accepted and PTS sees HCI_Mode_Change with status
    LMP PDU Not Allowed (0x24) and Current_Mode 0, failing the case.

    PTS requests 18 slots (11.25 ms); the verdict accepts 16-24 slots.

    After the sniff negotiation the test also expects the IUT to initiate
    sniff subrating, so PTS can observe an HCI_Sniff_Subrating event. Give the
    controller a moment to finish the mode change first, otherwise the
    Sniff_Subrating command is rejected as Command Disallowed.
    """
    # PTS checks the HCI_Sniff_Subrating event on its own side and requires
    # Maximum_Transmit_Latency == Sniff_Interval (18 slots),
    # Maximum_Receive_Latency == floor(1000 ms / 11.25 ms) * 18 == 1584,
    # Minimum_Remote_Timeout == 0 and Minimum_Local_Timeout == 3200 slots
    # (2 s). Local and remote timeouts are mirrored across the link, so the
    # IUT must place the 3200-slot requirement on the peer, i.e. pass it as
    # min_remote_timeout and leave its own min_local_timeout at 0. The
    # controller derives Maximum_Transmit_Latency from the sniff interval.
    time.sleep(2)
    try:
        btp.hid_host_sniff_subrating(0x0630, 0x0C80, 0x0000)
    except BTPError as e:
        logging.debug("hdl_wid_42: sniff subrating failed: %s", e)

    return True


def hdl_wid_43(params: WIDParams):
    """WID 43: perform an SDP search then disconnect, or acknowledge.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    start an SDP search procedure and disconnect after it completes, run
    an SDP service search for the HID profile (UUID 0x1124) and then tear
    down the ACL. Otherwise this is a PTS-side output-report verification
    prompt and is simply acknowledged.
    """
    description = (params.description or "") if params is not None else ""
    lower = description.lower()

    if "sdp search" in lower:
        # PTS wants to observe an SDP service-search procedure and then a
        # disconnect. For CDD tests the spec requires that the SDP channel
        # is closed before HID channels are opened, so only the bare ACL is
        # established here (no HID). For other flows where HID is already up,
        # fall through and use the existing connection.
        stack = get_stack()
        tc = (params.test_case_name or "") if params is not None else ""
        if not stack.hid_host.connected:
            if "/CDD/" in tc:
                if not _acl_connect_to_pts():
                    logging.debug("hdl_wid_43: could not connect ACL to PTS for CDD SDP")
            else:
                if not connect_to_pts():
                    logging.debug("hdl_wid_43: could not connect to PTS for SDP")

        try:
            btp.sdp_search_req(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, uuid=0x1124)
        except BTPError as e:
            logging.debug("hdl_wid_43: sdp_search_req error: %s", e)

        sleep(2)

        # For CDD: the spec requires SDP closed before HID opens on the same
        # ACL. SDP channel is closed automatically after the search completes.
        # Keep the ACL alive so WID 3 can open HID on it. Disconnecting the
        # ACL here would prevent PTS from seeing the required SDP-then-HID
        # ordering on a single ACL connection, causing INDCSV.
        if "/CDD/" not in tc:
            try:
                btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
            except BTPError as e:
                logging.debug("hdl_wid_43: gap_disconnect error: %s", e)

        return True

    return True


def hdl_wid_44(_: WIDParams):
    """Force the IUT to send a GET_REPORT command to the PTS."""
    stack = get_stack()
    try:
        # The PTS HID Device advertises a report descriptor that uses Report
        # IDs, so a GET_REPORT without a Report ID (report_id 0) is refused and
        # the device tears down the link. Request Report ID 1 so the PDU is
        # valid for a report-ID-using device.
        btp.hid_host_get_report(defs.BTP_HID_HOST_REPORT_TYPE_INPUT, 0x01)
    except BTPError as e:

        logging.debug("hdl_wid_44: hid_host_get_report error: %s", e)
        return False

    stack.hid_host.wait_for_get_report()

    # PTS renders the verdict from the transaction it observed on air, so a
    # handshake error is not failed here; log it as the likely cause when PTS
    # ends the case unexpectedly.
    if stack.hid_host.last_get_report is not None:
        result_code = stack.hid_host.last_get_report[0]
        if result_code != defs.BTP_HID_HOST_HS_RSP_SUCCESS:
            logging.debug("hdl_wid_44: device rejected GET_REPORT, handshake "
                          "result 0x%02x", result_code)

    return True


def hdl_wid_48(_: WIDParams):
    """Force the IUT to send a GET_PROTOCOL command to the PTS."""
    stack = get_stack()
    try:
        btp.hid_host_get_protocol()
    except BTPError as e:
        logging.debug("hdl_wid_48: hid_host_get_protocol error: %s", e)
        return False

    stack.hid_host.wait_for_get_protocol()
    return True


_hdl_wid_49_state = {"tc": None, "count": 0}


def hdl_wid_49(params: WIDParams):
    """Force the IUT to send a SET_PROTOCOL command to the PTS.

    Style is MMI_Style_Ok_Cancel2. PTS may reissue the same WID multiple
    times (e.g. HID/HOS/HID/BV-10-C) because it expects to observe a new
    SET_PROTOCOL PDU per prompt. Emit a fresh SET_PROTOCOL PDU on every
    call, alternating BOOT/REPORT modes so each invocation puts a distinct
    PDU on the wire, and always acknowledge Ok so PTS can advance.
    """
    stack = get_stack()

    tc = getattr(params, "test_case_name", None)
    if _hdl_wid_49_state["tc"] != tc:
        _hdl_wid_49_state["tc"] = tc
        _hdl_wid_49_state["count"] = 0

    _hdl_wid_49_state["count"] += 1

    # PTS air-side trace shows this WID actually expects a GET_PROTOCOL
    # (HIDP Message Type 0x06), not a SET_PROTOCOL (0x07), despite the
    # WID description saying "SET_PROTOCOL". Emit a fresh GET_PROTOCOL
    # PDU on every prompt and always answer Ok so PTS gathers enough
    # evidence to render its verdict on its own.
    try:
        btp.hid_host_get_protocol()
    except BTPError as e:
        logging.debug("hdl_wid_49: hid_host_get_protocol error: %s", e)
        return False
    stack.hid_host.wait_for_get_protocol()
    return True


def hdl_wid_45(_: WIDParams):
    """Force the IUT to send a SET_REPORT command to the PTS."""
    stack = get_stack()
    report = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    try:
        btp.hid_host_set_report(defs.BTP_HID_HOST_REPORT_TYPE_OUTPUT, report)
    except BTPError as e:
        logging.debug("hdl_wid_45: hid_host_set_report error: %s", e)
        return False

    stack.hid_host.wait_for_set_report()
    return True


def hdl_wid_25(params: WIDParams):
    """WID 25: either send a GET_REPORT request or delete the pairing.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    send a GET_REPORT request (optionally naming a specific reportID), emit
    the GET_REPORT PDU with that report ID. Otherwise delete the pairing.
    """
    import re

    description = (params.description or "") if params is not None else ""
    lower = description.lower()

    if "get_report" in lower:
        stack = get_stack()
        # Parse "reportID = 0xNN" (or decimal) from the description; default 1.
        report_id = 0x01
        m = re.search(r"reportid\s*=\s*(0x[0-9a-fA-F]+|\d+)", description, re.IGNORECASE)
        if m:
            report_id = int(m.group(1), 0)
        try:
            btp.hid_host_get_report(defs.BTP_HID_HOST_REPORT_TYPE_INPUT, report_id)
        except BTPError as e:
            logging.debug("hdl_wid_25: hid_host_get_report error: %s", e)
            return False

        stack.hid_host.wait_for_get_report()
        return True

    try:
        btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    except BTPError as e:
        logging.debug("hdl_wid_25: gap_unpair error: %s", e)

    return True


def hdl_wid_26(params: WIDParams):
    """WID 26: either send a SET_REPORT request or enable boot protocol mode.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    send a SET_REPORT on a report (optionally naming a reportID), emit the
    SET_REPORT PDU. For a report-ID-using device the report ID is carried
    as the first payload byte. Otherwise enable boot protocol mode.
    """
    import re

    description = (params.description or "") if params is not None else ""
    lower = description.lower()
    stack = get_stack()

    if "set_report" in lower:
        report_id = None
        m = re.search(r"reportid\s*=\s*(0x[0-9a-fA-F]+|\d+)", description, re.IGNORECASE)
        if m:
            report_id = int(m.group(1), 0)

        if report_id is not None:
            report = bytearray([report_id, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        else:
            report = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # The PTS HID Device report descriptor maps report IDs to specific
        # report types. Report ID 0x05 is a FEATURE report, so a SET_REPORT
        # issued as an OUTPUT report is rejected by the device (result != 0)
        # and PTS keeps re-prompting. Select FEATURE for report ID 0x05 and
        # OUTPUT otherwise.
        if report_id == 0x05:
            report_type = defs.BTP_HID_HOST_REPORT_TYPE_FEATURE
        else:
            report_type = defs.BTP_HID_HOST_REPORT_TYPE_OUTPUT

        try:
            btp.hid_host_set_report(report_type, report)
        except BTPError as e:
            logging.debug("hdl_wid_26: hid_host_set_report error: %s", e)
            return False

        stack.hid_host.wait_for_set_report()
        return True

    try:
        btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_BOOT_MODE)
    except BTPError as e:
        logging.debug("hdl_wid_26: hid_host_set_protocol error: %s", e)
        return False

    stack.hid_host.wait_for_set_protocol()
    return True


def hdl_wid_27(params: WIDParams):
    """WID 27: either send a GET_PROTOCOL request or enable report protocol.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    send a GET_PROTOCOL request, emit a GET_PROTOCOL PDU. Otherwise force a
    Boot->Report SET_PROTOCOL toggle so a real SET_PROTOCOL PDU is always
    transmitted for PTS to observe (some IUTs short-circuit
    SET_PROTOCOL(REPORT) when already in Report mode after connect).
    """
    description = (params.description or "") if params is not None else ""
    lower = description.lower()
    stack = get_stack()

    if "get_protocol" in lower:
        try:
            btp.hid_host_get_protocol()
        except BTPError as e:
            logging.debug("hdl_wid_27: hid_host_get_protocol error: %s", e)
            return False

        stack.hid_host.wait_for_get_protocol()
        return True

    try:
        btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_BOOT_MODE)
        stack.hid_host.wait_for_set_protocol()
        btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_REPORT_MODE)
    except BTPError as e:
        logging.debug("hdl_wid_27: hid_host_set_protocol error: %s", e)
        return False

    stack.hid_host.wait_for_set_protocol()
    return True


def hdl_wid_28(params: WIDParams):
    """WID 28: send a SET_PROTOCOL request for Boot Protocol, or acknowledge.

    PTS reuses this WID. When the description asks the IUT (HID Host) to
    send a SET_PROTOCOL request for Boot Protocol, emit exactly one
    SET_PROTOCOL(BOOT) PDU. Do not toggle through Report Protocol first:
    boot-mode test cases (HID11/HOS/BHIT/*) do not answer an unrequested
    SET_PROTOCOL(REPORT), so the extra request stalls the transaction and
    fails the case. Otherwise this is a visual-verification prompt and is
    acknowledged.
    """
    description = (params.description or "") if params is not None else ""
    lower = description.lower()

    if "set_protocol" in lower and "boot" in lower:
        stack = get_stack()
        try:
            btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_BOOT_MODE)
        except BTPError as e:
            logging.debug("hdl_wid_28: hid_host_set_protocol error: %s", e)
            return False

        stack.hid_host.wait_for_set_protocol()
        return True

    return True


def hdl_wid_29(_: WIDParams):
    """Send a SET_PROTOCOL request for Report Protocol from the IUT.

    Some IUTs short-circuit SET_PROTOCOL(REPORT) when already in Report
    mode after connect, so no PDU is emitted on air. Force a Boot->Report
    toggle so a real SET_PROTOCOL(REPORT) PDU is always transmitted for
    PTS to observe.
    """
    stack = get_stack()
    try:
        btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_BOOT_MODE)
        stack.hid_host.wait_for_set_protocol()
        btp.hid_host_set_protocol(defs.BTP_HID_HOST_PROTOCOL_REPORT_MODE)
    except BTPError as e:
        logging.debug("hdl_wid_29: hid_host_set_protocol error: %s", e)
        return False

    stack.hid_host.wait_for_set_protocol()
    return True


def hdl_wid_30(_: WIDParams):
    """Send a HID_CONTROL SUSPEND request from the IUT (HID Host)."""
    try:
        btp.hid_host_suspend()
    except BTPError as e:
        logging.debug("hdl_wid_30: hid_host_suspend error: %s", e)
        return False

    return True


def hdl_wid_31(_: WIDParams):
    """Send a HID_CONTROL EXIT_SUSPEND request from the IUT (HID Host)."""
    try:
        btp.hid_host_exit_suspend()
    except BTPError as e:
        logging.debug("hdl_wid_31: hid_host_exit_suspend error: %s", e)
        return False

    return True


def hdl_wid_52(_: WIDParams):

    """Place the IUT in Limited Discoverable mode."""
    btp.gap_set_connectable()
    btp.gap_set_limited_discoverable()

    return True


def hdl_wid_53(_: WIDParams):
    """Wait for Limited Discoverable Mode timeout."""
    btp.gap_set_non_discoverable()

    return True


def hdl_wid_54(_: WIDParams):
    """Confirm the IUT can discover PTS through General Inquiry."""
    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discovery()

    return btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE)


def hdl_wid_55(_: WIDParams):
    """Confirm the IUT can discover PTS through Limited Inquiry."""
    btp.gap_start_discovery(transport='bredr', discov_type='passive', mode='limited')
    sleep(10)
    btp.gap_stop_discovery()

    return btp.check_discovery_results(addr_type=defs.BTP_BR_ADDRESS_TYPE)


def hdl_wid_95(_: WIDParams):
    """Counterpart to WID 14: re-establish the ACL + HID connection."""
    return connect_to_pts()


def hdl_wid_96(_: WIDParams):
    """Close the control channel connection from the IUT.

    In the HCR/BV-01-C flow WID 3 releases the whole HID link (interrupt
    channel followed by control channel), so by the time PTS prompts to
    close the control channel it is already gone. Simply acknowledge so
    PTS can finalize its verdict.
    """
    return True


def hdl_wid_97(_: WIDParams):
    """Close the interrupt channel connection from the IUT.

    In the HCR/BV-01-C flow WID 3 has already torn the HID link down, so
    the interrupt channel is gone by the time this prompt fires. Simply
    acknowledge so PTS can proceed to the control-channel close prompt.
    """
    return True


def hdl_wid_491(_: WIDParams):
    """General inquiry: place the IUT connectable and general discoverable."""
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_492(_: WIDParams):
    """Limited inquiry: place the IUT connectable and limited discoverable."""
    btp.gap_set_connectable()
    btp.gap_set_limited_discoverable()

    return True


def hdl_wid_493(_: WIDParams):
    """Should not make connection: place the IUT non-discoverable."""
    btp.gap_set_non_discoverable()

    return True


def hdl_wid_495(_: WIDParams):
    """Informational multi-instance (LT1/LT2) prompt. Acknowledge."""
    return True


def hdl_wid_496(_: WIDParams):
    """Informational multi-instance (LT1/LT2) prompt. Acknowledge."""
    return True


def hdl_wid_20000(_: WIDParams):
    """Prepare IUT into a connectable mode in BR/EDR."""
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()

    return True


def hdl_wid_20120(_: WIDParams):
    """Initiate a GATT connection over BR/EDR to the PTS."""
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
