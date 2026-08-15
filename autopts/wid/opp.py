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

import logging

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import pts_addr_get
from autopts.pybtp.types import WIDParams

log = logging.debug

# Default vCard content used for push operations in test cases.
_VCARD_CONTENT = (
    b"BEGIN:VCARD\r\n"
    b"VERSION:2.1\r\n"
    b"FN:PTS Test\r\n"
    b"N:Test;PTS;;;\r\n"
    b"TEL;CELL:+1234567890\r\n"
    b"END:VCARD\r\n"
)

# Default vCalendar content for push operations (single VEVENT).
_VCAL_CONTENT = (
    b"BEGIN:VCALENDAR\r\n"
    b"VERSION:1.0\r\n"
    b"BEGIN:VEVENT\r\n"
    b"SUMMARY:PTS Test Event\r\n"
    b"DTSTART:20260101T120000Z\r\n"
    b"DTEND:20260101T130000Z\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

# Single VCALENDAR containing two VEVENT entries, as required by test cases
# that push "two vCals in a single PUT operation" (e.g. OPP/SR/OPH/BV-24-C).
_VCAL_TWO_EVENTS = (
    b"BEGIN:VCALENDAR\r\n"
    b"VERSION:1.0\r\n"
    b"BEGIN:VEVENT\r\n"
    b"SUMMARY:PTS Test Event 1\r\n"
    b"DTSTART:20260101T120000Z\r\n"
    b"DTEND:20260101T130000Z\r\n"
    b"END:VEVENT\r\n"
    b"BEGIN:VEVENT\r\n"
    b"SUMMARY:PTS Test Event 2\r\n"
    b"DTSTART:20260102T120000Z\r\n"
    b"DTEND:20260102T130000Z\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

# Default vNote content for push operations.
_VNOTE_CONTENT = (
    b"BEGIN:VNOTE\r\n"
    b"VERSION:1.1\r\n"
    b"BODY:PTS Test Note\r\n"
    b"END:VNOTE\r\n"
)

# Two vNote objects concatenated for test cases that push two vNotes in one PUT.
_VNOTE_TWO = _VNOTE_CONTENT + (
    b"BEGIN:VNOTE\r\n"
    b"VERSION:1.1\r\n"
    b"BODY:PTS Test Note 2\r\n"
    b"END:VNOTE\r\n"
)

# Default vMessage content for push operations.
_VMSG_CONTENT = (
    b"BEGIN:VMSG\r\n"
    b"VERSION:1.1\r\n"
    b"BEGIN:VBODY\r\n"
    b"BODY:PTS Test Message\r\n"
    b"END:VBODY\r\n"
    b"END:VMSG\r\n"
)

# Two vMessage objects concatenated for test cases that push two vMsgs in one PUT.
_VMSG_TWO = _VMSG_CONTENT + (
    b"BEGIN:VMSG\r\n"
    b"VERSION:1.1\r\n"
    b"BEGIN:VBODY\r\n"
    b"BODY:PTS Test Message 2\r\n"
    b"END:VBODY\r\n"
    b"END:VMSG\r\n"
)

# Large content (> 2 MB) used by MMI_IUT_INITIATE_PUT_2MB.
_LARGE_CONTENT = b"X" * (2 * 1024 * 1024 + 1024)


def opp_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{opp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def _opp_client_push(name: bytes, mime_type: bytes, body: bytes):
    """
    name is ASCII bytes (e.g. b'test.vcf'), encoded to UTF-16BE with null
    terminator before sending as required by the OBEX Name header.
    """
    name_utf16 = name.decode('utf-8').encode('utf-16-be') + b'\x00\x00'

    btp.opp_client_push(total_length=len(body),
                        is_final=1,
                        name=name_utf16,
                        mime_type=mime_type,
                        body=body)


# wid handlers section begin
def hdl_wid_2(_: WIDParams):
    """
    Initiate a Business Card Exchange operation.
    """
    _opp_client_push(b"bcard.vcf", b"text/x-vcard", _VCARD_CONTENT)
    btp.opp_wait_for_client_push(timeout=30)
    btp.opp_client_pull_bcard()
    btp.opp_wait_for_client_pull_bcard(timeout=30)
    return True


def hdl_wid_4(_: WIDParams):
    """
    Send any type of content greater than 2 MB.
    """
    btp.opp_client_push_2mb()
    btp.opp_wait_for_client_push(timeout=10*60)
    return True


def hdl_wid_5(_: WIDParams):
    """
    Send any type of content, then abort the operation.
    """
    chunk = _LARGE_CONTENT[:100]
    name_utf16 = b"abort_test.bmp".decode('utf-8').encode('utf-16-be') + b'\x00\x00'
    btp.opp_client_push(total_length=len(_LARGE_CONTENT),
                        is_final=0,
                        name=name_utf16,
                        mime_type=b"",
                        body=chunk)
    return True


def hdl_wid_6(_: WIDParams):
    """
    Send any type of content other than vCard.
    """
    _opp_client_push(b"test.bmp", b"", b"\x00" * 64)
    return True


def hdl_wid_7(_: WIDParams):
    """
    Send any type of content other than vNote, vCard, vCal or vMsg.
    """
    _opp_client_push(b"test.bmp", b"", b"\x00" * 64)
    return True


def hdl_wid_8(_: WIDParams):
    """
    Send a vCal (PUT) to PTS (file extension .vcs).
    """
    _opp_client_push(b"test.vcs", b"text/x-vcalendar", _VCAL_CONTENT)
    return True


def hdl_wid_9(_: WIDParams):
    """
    Send a vMsg (PUT) to PTS (file extension .vmg).
    """
    _opp_client_push(b"test.vmg", b"text/x-vmsg", _VMSG_CONTENT)
    return True


def hdl_wid_10(_: WIDParams):
    """
    Send a vNote (PUT) to PTS (file extension .vnt).
    """
    _opp_client_push(b"test.vnt", b"text/x-vnote", _VNOTE_CONTENT)
    return True


def hdl_wid_11(_: WIDParams):
    """
    Send two vCals in a single PUT operation.
    """
    body_len  = len(_VCAL_TWO_EVENTS)
    part1_len = body_len // 2
    name_utf16 = b"two_vcals.vcs".decode('utf-8').encode('utf-16-be') + b'\x00\x00'

    btp.opp_client_push(total_length=body_len,
                        is_final=0,
                        name=name_utf16,
                        mime_type=b"text/x-vcalendar",
                        body=_VCAL_TWO_EVENTS[:part1_len])

    btp.opp_client_push(total_length=body_len,
                        is_final=1,
                        name=b"",
                        mime_type=b"",
                        body=_VCAL_TWO_EVENTS[part1_len:])
    return True


def hdl_wid_12(_: WIDParams):
    """
    Send two vCals using one PUT per vCal.
    """
    _opp_client_push(b"vcal1.vcs", b"text/x-vcalendar", _VCAL_CONTENT)
    _opp_client_push(b"vcal2.vcs", b"text/x-vcalendar", _VCAL_CONTENT)
    return True


def hdl_wid_13(_: WIDParams):
    """
    Send two vCards in a single PUT operation.
    """
    combined = _VCARD_CONTENT + _VCARD_CONTENT
    _opp_client_push(b"two_vcards.vcf", b"text/x-vcard", combined)
    return True


def hdl_wid_14(_: WIDParams):
    """
    Send two vCards using one PUT per vCard.
    """
    _opp_client_push(b"vcard1.vcf", b"text/x-vcard", _VCARD_CONTENT)
    _opp_client_push(b"vcard2.vcf", b"text/x-vcard", _VCARD_CONTENT)
    return True


def hdl_wid_15(_: WIDParams):
    """
    Send two vMsgs in a single PUT operation.
    """
    _opp_client_push(b"two_vmsgs.vmg", b"text/x-vmsg", _VMSG_TWO)
    return True


def hdl_wid_16(_: WIDParams):
    """
    Send two vMsgs using one PUT per vMsg.
    """
    _opp_client_push(b"vmsg1.vmg", b"text/x-vmsg", _VMSG_CONTENT)
    _opp_client_push(b"vmsg2.vmg", b"text/x-vmsg", _VMSG_CONTENT)
    return True


def hdl_wid_17(_: WIDParams):
    """
    Send two vNotes in a single PUT operation.
    """
    _opp_client_push(b"two_vnotes.vnt", b"text/x-vnote", _VNOTE_TWO)
    return True


def hdl_wid_18(_: WIDParams):
    """
    Send two vNotes using one PUT per vNote.
    """
    _opp_client_push(b"vnote1.vnt", b"text/x-vnote", _VNOTE_CONTENT)
    _opp_client_push(b"vnote2.vnt", b"text/x-vnote", _VNOTE_CONTENT)
    return True


def hdl_wid_19(params: WIDParams):
    """
    Reject the Business Card Pull operation.
    """
    if "OPP/SR/" in params.test_case_name:
        btp.opp_server_pull_bcard_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    else:
        btp.opp_client_pull_bcard()
    return True


def hdl_wid_20(_: WIDParams):
    """
    Reject the incoming PUT operation.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_UNSUPP_MEDIA_TYPE)
    return True


def hdl_wid_21(_: WIDParams):
    """
    Prepare to reject the incoming file or object.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    return True


def hdl_wid_22(_: WIDParams):
    """
    Reject the unsupported object with UNSUPPORTED_MEDIA_TYPE.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_UNSUPP_MEDIA_TYPE)
    return True


def hdl_wid_23(_: WIDParams):
    """
    Reject a new calendar entry.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    return True


def hdl_wid_24(_: WIDParams):
    """
    Reject a new contact.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    return True


def hdl_wid_25(_: WIDParams):
    """
    Reject a new message.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    return True


def hdl_wid_26(_: WIDParams):
    """
    Reject a new note.
    """
    btp.opp_server_prepare_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_FORBIDDEN)
    return True


def hdl_wid_27(_: WIDParams):
    """
    Confirm file is not present on the IUT.
    """
    return True


def hdl_wid_28(_: WIDParams):
    """
    Confirm calendar entry is not present.
    """
    return True


def hdl_wid_29(_: WIDParams):
    """
    Confirm contact is not present.
    """
    return True


def hdl_wid_30(_: WIDParams):
    """
    Confirm message is not present.
    """
    return True


def hdl_wid_31(_: WIDParams):
    """
    Confirm note is not present.
    """
    return True


def hdl_wid_32(_: WIDParams):
    """
    Remove 15 vcard entries.
    """
    return True


def hdl_wid_33(_: WIDParams):
    """
    Verify IUT contains 15 contacts.
    """
    return True


def hdl_wid_34(_: WIDParams):
    """
    Verify business card pull was rejected correctly.
    """
    return True


def hdl_wid_35(_: WIDParams):
    """
    Verify business card push rejection was notified.
    """
    return True


def hdl_wid_36(_: WIDParams):
    """
    Verify file received by the IUT.
    """
    return True


def hdl_wid_37(_: WIDParams):
    """
    Verify file pushed by the IUT.
    """
    return True


def hdl_wid_38(_: WIDParams):
    """
    Verify IUT contains specified files.
    """
    return True


def hdl_wid_39(_: WIDParams):
    """
    Verify IUT contains specified calendar entries.
    """
    return True


def hdl_wid_40(_: WIDParams):
    """
    Verify IUT contains specified contacts.
    """
    return True


def hdl_wid_41(_: WIDParams):
    """
    Verify IUT contains specified messages.
    """
    return True


def hdl_wid_42(_: WIDParams):
    """
    Verify IUT contains specified notes.
    """
    return True


def hdl_wid_43(_: WIDParams):
    """
    Verify rejection was notified correctly on the client.
    """
    return True


def hdl_wid_46(_: WIDParams):
    """
    Accept the PUT and then the ABORT from the tester.
    """
    return True


def hdl_wid_47(_: WIDParams):
    """
    Verify contacts are absent from address book.
    """
    return True


def hdl_wid_48(_: WIDParams):
    """
    Verify calendar entries are absent.
    """
    return True


def hdl_wid_49(_: WIDParams):
    """
    Verify notes are absent.
    """
    return True


def hdl_wid_50(_: WIDParams):
    """
    Verify messages are absent.
    """
    return True


def hdl_wid_51(_: WIDParams):
    """
    Verify files are absent from the IUT.
    """
    return True


def hdl_wid_90(_: WIDParams):
    """
    IUT is capable of connecting to an unpaired device.
    """
    return True


def hdl_wid_20115(_: WIDParams):
    """
    Initiate ACL disconnection to the PTS.
    """
    btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_4004(_: WIDParams):
    """
    Accept the OBEX CONNECT REQ.
    """
    btp.opp_wait_for_server_connected(timeout=30)
    btp.opp_server_connect_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS)
    return True


def hdl_wid_4007(_: WIDParams):
    """
    Accept the OBEX DISCONNECT REQ.
    """
    btp.opp_server_disconnect_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS)
    return True


def hdl_wid_4008(_: WIDParams):
    """
    Accept the GET REQUEST.
    """
    btp.opp_server_pull_bcard_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS,
                                   is_final=1,
                                   body=_VCARD_CONTENT)
    return True


def hdl_wid_4010(_: WIDParams):
    """
    Accept the GET REQUEST with SRM ENABLED header.
    """
    btp.opp_server_pull_bcard_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS,
                                   is_final=1,
                                   body=_VCARD_CONTENT)
    return True


def hdl_wid_4012(_: WIDParams):
    """
    Accept the PUT REQUEST.
    """
    btp.opp_server_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS)
    return True


def hdl_wid_4014(_: WIDParams):
    """
    Accept the PUT REQUEST with SRM ENABLED header.
    """
    btp.opp_server_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_SUCCESS)
    return True


def hdl_wid_4017(_: WIDParams):
    """
    Accept the L2CAP channel connection for an OBEX connection.
    """
    return True


def hdl_wid_4018(_: WIDParams):
    """
    Accept the RFCOMM channel connection for an OBEX connection.
    """
    return True


def hdl_wid_4019(_: WIDParams):
    """
    Accept the disconnection of the transport channel.
    """
    return True


def hdl_wid_4024(_: WIDParams):
    """
    Initiate an OBEX CONNECT REQ.
    """
    btp.opp_client_connect()
    btp.opp_wait_for_client_connected(timeout=30)
    return True


def hdl_wid_4031(_: WIDParams):
    """
    Initiate an OBEX DISCONNECT REQ.
    """
    btp.opp_client_disconnect()
    return True


def hdl_wid_4032(_: WIDParams):
    """
    Send a GET request and allow it to complete.
    """
    btp.opp_client_pull_bcard()
    return True


def hdl_wid_4037(_: WIDParams):
    """
    Send a PUT request and allow it to complete.
    """
    _opp_client_push(b"test.vcf", b"text/x-vcard", _VCARD_CONTENT)
    return True


def hdl_wid_4038(_: WIDParams):
    """
    Send a PUT request without SRM header (multi-packet).
    """
    _opp_client_push(b"large.bmp", b"", b"\xAA" * 8192)
    return True


def hdl_wid_4039(_: WIDParams):
    """
    Send a PUT request with SRM ENABLED header (multi-packet).
    """
    _opp_client_push(b"srm_test.bmp", b"", b"\xBB" * 8192)
    return True


def hdl_wid_4040(_: WIDParams):
    """
    Send a vCard (PUT) to PTS.
    """
    _opp_client_push(b"test.vcf", b"text/x-vcard", _VCARD_CONTENT)
    return True


def hdl_wid_4047(_: WIDParams):
    """
    Create a channel for an OBEX connection (RFCOMM via SDP).
    """
    btp.opp_discover()
    result = btp.opp_wait_for_discovered(timeout=30)
    if result and result.rfcomm_channel:
        btp.opp_client_transport_connect(channel=result.rfcomm_channel)
    return True


def hdl_wid_4048(_: WIDParams):
    """
    Create an RFCOMM channel for an OBEX connection.
    """
    btp.opp_discover()
    result = btp.opp_wait_for_discovered(timeout=30)
    if result and result.rfcomm_channel:
        btp.opp_client_transport_connect(channel=result.rfcomm_channel)
    return True


def hdl_wid_4049(_: WIDParams):
    """
    Disconnect the transport channel.
    """
    btp.opp_client_transport_disconnect()
    return True


def hdl_wid_4058(_: WIDParams):
    """
    Respond to PUT REQUEST with SRM ENABLED and SRMP WAIT header.
    """
    btp.opp_server_push_rsp(rsp_code=defs.BTP_OPP_RSP_CODE_CONTINUE)
    return True


def hdl_wid_4088(_: WIDParams):
    """
    Abort the current operation.
    """
    btp.opp_client_abort()
    return True


def hdl_wid_4100(_: WIDParams):
    """
    Create an RFCOMM channel for an OBEX connection.
    """
    addr = pts_addr_get()

    stack = get_stack()
    btp.gap_connect(addr, defs.BTP_BR_ADDRESS_TYPE)
    stack.gap.wait_for_connection(timeout=5, addr=addr)

    btp.opp_discover()
    result = btp.opp_wait_for_discovered(timeout=30)
    if result and result.rfcomm_channel:
        btp.opp_client_transport_connect(channel=result.rfcomm_channel)
        btp.opp_wait_for_client_transport_connected(timeout=30)
    return True


def hdl_wid_4800(_: WIDParams):
    """
    Remove pairing from the IUT.
    """
    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.
    """
    btp.opp_server_register()
    btp.gap_set_general_discoverable()
    return True
