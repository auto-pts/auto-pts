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
import re
from datetime import datetime

from autopts.ptsprojects.stack import (
    MAP_FILLER_BYTE,
    MAPChatState,
    MAPConversation,
    MAPEvent,
    MAPEventType,
    MAPInfo,
    MAPMsg,
    MAPMsgStatusInd,
    MAPMsgType,
    MAPParticipant,
    MAPPresenceAvailability,
    MAPSupportedFeatures,
    MAPType,
    get_stack,
)
from autopts.pybtp import btp, defs
from autopts.pybtp.btp.btp import pts_addr_get
from autopts.pybtp.types import MAPAppParam, OBEXHdr, OBEXRspCode, WIDParams

log = logging.debug


def default_mce_mas(bd_addr=None):
    stack = get_stack()
    return stack.map.default_mce_mas.get(pts_addr_get(bd_addr))


def default_mse_mas(bd_addr=None):
    stack = get_stack()
    return stack.map.default_mse_mas.get(pts_addr_get(bd_addr))


def set_folder(folder_path: str = 'inbox'):
    btp.map_mce_mas_set_folder(default_mce_mas(), '/')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), 'telecom')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), 'msg')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), folder_path)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())


def get_msg_listing(folder_path: str = 'inbox'):
    set_folder(folder_path)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    result = btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    if result is None:
        return None, None

    rsp_code, dct = result
    if rsp_code == OBEXRspCode.SUCCESS:
        if folder_path == 'inbox':
            prev_inbox = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
            btp.map_set_info(MAPInfo.PREV_INBOX, prev_inbox, default_mce_mas())
        btp.map_set_info(folder_path, dct, default_mce_mas())

    return rsp_code, dct


def get_convo_listing():
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_CONVO_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_convo_listing(default_mce_mas(), True, encoded_hdr)
    result = btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, default_mce_mas())
    if result is None:
        return None, None

    rsp_code, dct = result
    if rsp_code == OBEXRspCode.SUCCESS:
        btp.map_set_info(MAPInfo.CONVO_LISTING, dct, default_mce_mas())

    return rsp_code, dct


def create_msg(msg_type: str, folder: str = '') -> MAPMsg:
    if msg_type == MAPMsgType.EMAIL:
        sender_name = 'PTS'
        sender_addressing = 'pts@example.com'
        recipient_name = 'IUT'
        recipient_addressing = 'iut@example.com'
    elif msg_type == MAPMsgType.IM:
        sender_name = "PTS"
        sender_addressing = "im:pts@example.com"
        recipient_name = "IUT"
        recipient_addressing = "im:iut@example.com"
    else:
        sender_name = 'PTS'
        sender_addressing = '+1234567890'
        recipient_name = 'IUT'
        recipient_addressing = '+9876543210'

    text = ("This is a message for Bluetooth MAP test.\n"
    "\n"
    "Features being tested:\n"
    "- UTF-8 character encoding\n"
    "- Multi-line message content\n"
    "- Special characters: @#$%&*()_+-=[]{{}}|;:',.<>?/\n"
    "- Numbers: 0123456789\n"
    "\n"
    "This test message has been designed to thoroughly test the MAP\n"
    "implementation's ability to handle large messages that require\n"
    "fragmentation across multiple OBEX packets. The message includes\n"
    "various character types, formatting, and structured content to\n"
    "ensure comprehensive testing coverage.\n"
    "\n"
    "The Message Access Profile (MAP) enables remote devices to access\n"
    "messages stored on a Message Server Equipment (MSE). This includes\n"
    "SMS, MMS, EMAIL, and IM message types. The profile supports various\n"
    "operations such as listing messages, retrieving message content,\n"
    "sending new messages, and managing message status.\n"
    "\n"
    "End of message.")

    msg = MAPMsg(
        handle='',
        subject=text[:50],
        datetime=datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z"),
        sender_name=sender_name,
        sender_addressing=sender_addressing,
        recipient_name=recipient_name,
        recipient_addressing=recipient_addressing,
        msg_type=msg_type,
        text=text,
        read=False,
        sent=False,
        priority=False,
        folder=folder
    )

    return msg


def parse_msg_listing(xml_data: str | bytes) -> list[dict[str, str]]:
    """
    Parse MAP message listing XML

    Args:
        xml_data: XML message listing data (string or bytes)

    Returns:
        List of message dictionaries with parsed attributes
    """
    try:
        import xml.etree.ElementTree as ET

        # Convert bytes to string if needed
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode('utf-8')

        # Parse XML
        root = ET.fromstring(xml_data)

        messages = []

        # Find all msg elements
        for msg_elem in root.findall('.//msg'):

            # Extract all attributes
            msg_dict = {attr_name: attr_value for attr_name, attr_value in msg_elem.attrib.items()}

            messages.append(msg_dict)

        logging.info(f"Parsed {len(messages)} messages from listing")
        return messages

    except Exception as e:
        logging.error(f"Error parsing message listing: {e}")
        return []


def get_msg_from_listing(xml_data: str | bytes, handle: str) -> dict[str, str] | None:
    """
    Get a specific message from message listing by handle

    Args:
        xml_data: XML message listing data
        handle: Message handle to find

    Returns:
        Message dictionary or None if not found
    """
    messages = parse_msg_listing(xml_data)

    for msg in messages:
        if msg.get('handle') == handle:
            return msg

    logging.warning(f"Message with handle {handle} not found in listing")
    return None


def filter_msg_from_listing(xml_data: str | bytes, **filters) -> list[dict[str, str]]:
    """
    Filter messages from listing based on criteria

    Args:
        xml_data: XML message listing data
        **filters: Filter criteria (e.g., read='yes', type='SMS_GSM', sender_name='John')

    Returns:
        List of filtered message dictionaries
    """
    messages = parse_msg_listing(xml_data)

    if not filters:
        return messages

    filtered = []
    for msg in messages:
        match = True
        for key, value in filters.items():
            if msg.get(key) != value:
                match = False
                break

        if match:
            filtered.append(msg)

    logging.info(f"Filtered {len(filtered)} messages from {len(messages)} total")
    return filtered


def parse_convo_listing(xml_data: str | bytes) -> list[dict[str, any]]:
    """
    Parse MAP conversation listing XML

    Args:
        xml_data: XML conversation listing data (string or bytes)

    Returns:
        List of conversation dictionaries with parsed attributes and participants
    """
    try:
        import xml.etree.ElementTree as ET

        # Convert bytes to string if needed
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode('utf-8')

        # Parse XML
        root = ET.fromstring(xml_data)

        conversations = []

        # Find all conversation elements
        for convo_elem in root.findall('.//conversation'):

            # Extract all conversation attributes
            convo_dict = {attr_name: attr_value for attr_name, attr_value in convo_elem.attrib.items()}

            # Parse participants
            participants = []
            for participant_elem in convo_elem.findall('participant'):

                # Extract all participant attributes
                participant_dict = {attr_name: attr_value for attr_name, attr_value in participant_elem.attrib.items()}

                participants.append(participant_dict)

            # Add participants list to conversation
            convo_dict['participants'] = participants

            conversations.append(convo_dict)

        logging.info(f"Parsed {len(conversations)} conversations from listing")
        return conversations

    except Exception as e:
        logging.error(f"Error parsing conversation listing: {e}")
        return []


def get_convo_from_listing(xml_data: str | bytes, convo_id: str) -> dict[str, any] | None:
    """
    Get a specific conversation from conversation listing by ID

    Args:
        xml_data: XML conversation listing data
        convo_id: Conversation ID to find

    Returns:
        Conversation dictionary with participants or None if not found
    """
    conversations = parse_convo_listing(xml_data)

    for convo in conversations:
        if convo.get('id') == convo_id:
            return convo

    logging.warning(f"Conversation with ID {convo_id} not found in listing")
    return None


def filter_convo_from_listing(xml_data: str | bytes, **filters) -> list[dict[str, any]]:
    """
    Filter conversations from listing based on criteria

    Args:
        xml_data: XML conversation listing data
        **filters: Filter criteria (e.g., read_status='yes', name='Test', last_activity='20240101T000000')

    Returns:
        List of filtered conversation dictionaries with participants
    """
    conversations = parse_convo_listing(xml_data)

    if not filters:
        return conversations

    filtered = []
    for convo in conversations:
        match = True
        for key, value in filters.items():
            # Skip participants key in filtering
            if key == 'participants':
                continue
            if convo.get(key) != value:
                match = False
                break

        if match:
            filtered.append(convo)

    logging.info(f"Filtered {len(filtered)} conversations from {len(conversations)} total")
    return filtered


def get_participants_from_convo(convo_dict: dict[str, any]) -> list[dict[str, str]]:
    """
    Get participants list from a conversation dictionary

    Args:
        convo_dict: Conversation dictionary

    Returns:
        List of participant dictionaries
    """
    return convo_dict.get('participants', [])


def filter_participants(convo_dict: dict[str, any], **filters) -> list[dict[str, str]]:
    """
    Filter participants from a conversation based on criteria

    Args:
        convo_dict: Conversation dictionary
        **filters: Filter criteria (e.g., uci='+1234567890', chat_state='1', presence_status='1')

    Returns:
        List of filtered participant dictionaries
    """
    participants = get_participants_from_convo(convo_dict)

    if not filters:
        return participants

    filtered = []
    for participant in participants:
        match = True
        for key, value in filters.items():
            if participant.get(key) != value:
                match = False
                break

        if match:
            filtered.append(participant)

    return filtered


def map_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{map_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def hdl_wid_1(_: WIDParams):
    """
    description: Send a Set Message Status request to set the status of a SMS_CDMA message from undeleted to deleted.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_CDMA")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.DELETED_STATUS,
            MAPAppParam.STATUS_VALUE: 1,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_2(_: WIDParams):
    """
    description: Send a Set Message Status request to set the status of an EMAIL message from undeleted to deleted.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="EMAIL")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.DELETED_STATUS,
            MAPAppParam.STATUS_VALUE: 1,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_3(_: WIDParams):
    """
    description: Send a Set Message Status request to set the status of a SMS_GSM message from undeleted to deleted.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_GSM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.DELETED_STATUS,
            MAPAppParam.STATUS_VALUE: 1,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_4(_: WIDParams):
    """
    description: Send a Set Message Status request to set the status of a MMS message from undeleted to deleted.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="MMS")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.DELETED_STATUS,
            MAPAppParam.STATUS_VALUE: 1,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_5(_: WIDParams):
    """
    description: Send an GetMASInstanceInformation request.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MAS_INST_INFO,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mce_mas(),
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_mas_inst_info(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MAS_INST_INFO, default_mce_mas())
    return True


def hdl_wid_6(_: WIDParams):
    """
    description: Send a Get Message request, with the Charset parameter as UTF-8, to retrieve an EMAIL message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="EMAIL")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.GET_MSG,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.ATTACHMENT: 0,  # OFF
            MAPAppParam.CHARSET: 1,  # UTF-8
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, default_mce_mas())
    return True


def hdl_wid_7(_: WIDParams):
    """
    description: Send a Get Folder Listing request. Please used telecom/msg/ for folder of choice.
    """
    btp.map_mce_mas_set_folder(default_mce_mas(), '/')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), 'telecom')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), 'msg')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_FOLDER_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_folder_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, default_mce_mas())
    return True


def hdl_wid_8(_: WIDParams):
    """
    description: Send a Get Message Listing request for the current folder.
    """
    set_folder('inbox')
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_9(params: WIDParams):
    """
    description: Send a Get Message Listing request filtering the message type for (%0X)
    """
    match = re.search(r'\((?P<msg_type>\w+)\)', params.description)
    msg_type = int(match.group('msg_type'), 16)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_MESSAGE_TYPE: msg_type,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_10(_: WIDParams):
    """
    description: Send a Get Message Listing request with FilterOriginator.
    Please enter pixit value for TSPX_filter_originator that match what is being send.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_ORIGINATOR: "PTS",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_11(_: WIDParams):
    """
    description: Send a Get Message Listing request with FilterPeriodBegin.
    Please enter pixit value for TSPX_filter_period_begin that match what is being send.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_PERIOD_BEGIN: "20100101T000000+0000",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_12(_: WIDParams):
    """
    description: Send a Get Message Listing request with FilterPeriodBegin and FilterPeriodEnd.
    Please enter pixit value for TSPX_filter_period_begin and TSPX_filter_period_end that match what is being send.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_PERIOD_BEGIN: "20100101T000000+0000",
            MAPAppParam.FILTER_PERIOD_END: "20111231T125959+0000",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_13(_: WIDParams):
    """
    description: Send a Get Message Listing request with FilterPeriodEnd.
    Please enter pixit value for TSPX_filter_period_end that match what is being send.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_PERIOD_END: "20111231T125959+0000",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_14(_: WIDParams):
    """
    description: Send a get Message Listing request with FilterPriority= high.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_PRIORITY: 1,  # High priority
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_15(_: WIDParams):
    """
    description: Send a get Message Listing request with FilterPriority= non high.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_PRIORITY: 2,  # Non-high priority
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_16(_: WIDParams):
    """
    description: Send a Get Message Listing request with Filter Read Status = read.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_READ_STATUS: 2,  # Read (0x02)
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_17(_: WIDParams):
    """
    description: Send a Get Message Listing request with Filter Read Status = unread.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_READ_STATUS: 1,  # Unread (0x01)
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_18(_: WIDParams):
    """
    description: Send a Get Message Listing request with FilterRecipient.
    Please enter pixit value for TSPX_filter_recipient that match what is being send.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_RECIPIENT: "IUT",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_19(_: WIDParams):
    """
    description: Send a Get Message request, with the Charset parameter as UTF-8, to retrieve an MMS message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="MMS")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.GET_MSG,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.ATTACHMENT: 0,
            MAPAppParam.CHARSET: 1,  # UTF-8
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, default_mce_mas())
    return True


def hdl_wid_21(_: WIDParams):
    """
    description: Send a Get Message request, with the Charset parameter as UTF-8, to retrieve an SMS CDMA message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_CDMA")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.GET_MSG,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.ATTACHMENT: 0,
            MAPAppParam.CHARSET: 1,  # UTF-8
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, default_mce_mas())
    return True


def hdl_wid_23(_: WIDParams):
    """
    description: Send a Get Message request, with the Charset parameter as UTF-8, to retrieve an SMS GSM message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_GSM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.GET_MSG,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.ATTACHMENT: 0,
            MAPAppParam.CHARSET: 1,  # UTF-8
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, default_mce_mas())
    return True


def hdl_wid_25(_: WIDParams):
    """
    description: Send a Set Notification Registration request with notification status turned Off to All MAS.
    """
    stack = get_stack()
    pts_addr = pts_addr_get()

    connections = stack.map.get_all_connections(pts_addr)
    connected_instances = [conn.instance_id for conn in connections
                           if conn.obex_type == defs.BTP_MAP_EV_MCE_MAS_CONNECT]

    for instance_id in connected_instances:
        mopl = btp.map_get_info(MAPInfo.MOPL, instance_id)
        conn_id = btp.map_get_info(MAPInfo.CONN_ID, instance_id)

        hdr = {
            OBEXHdr.CONN_ID: conn_id,
            OBEXHdr.TYPE: MAPType.SET_NTF_REG,
            OBEXHdr.APP_PARAM: {
                MAPAppParam.NOTIFICATION_STATUS: 0,  # Off
            },
            OBEXHdr.BODY: MAP_FILLER_BYTE,
        }
        encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
        btp.map_mce_mas_set_ntf_reg(instance_id, True, encoded_hdr)
        if btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG, instance_id) is None:
            return False
    return True


def mce_mas_transport_connect(conn_type=defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED):
    stack = get_stack()
    addr = pts_addr_get()

    sdp_list = stack.map.rx_sdp_get(addr, timeout=0)
    if sdp_list is None or len(sdp_list) == 0:
        btp.map_sdp_discover()

        sdp_list = stack.map.rx_sdp_get(addr)
        if sdp_list is None or len(sdp_list) == 0:
            return False

    sdp_list = [sdp for sdp in sdp_list if sdp.role == 'mas']

    history = stack.map.get_connection_history(addr)
    history_instances = [conn.instance_id for conn in history]

    # Find first SDP instance not in history
    selected_sdp = None
    for sdp in sdp_list:
        if sdp.instance_id not in history_instances:
            selected_sdp = sdp
            break

    # If all instances are in history, clear history and use first instance
    if selected_sdp is None:
        logging.info(f"All SDP instances in history, clearing history for {addr}")
        stack.map.clear_connection_history(addr)
        selected_sdp = sdp_list[0]

    if selected_sdp.psm != 0 and conn_type == defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED:
        btp.map_mce_mas_l2cap_connect(selected_sdp.instance_id, selected_sdp.psm)
        if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, selected_sdp.instance_id) is None:
            return False
    else:
        btp.map_mce_mas_rfcomm_connect(selected_sdp.instance_id, selected_sdp.channel)
        if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, selected_sdp.instance_id) is None:
            return False

    return True


def hdl_wid_26(params: WIDParams):
    """
    description: Send a Set Notification Registration request with notification status turned On to All MAS.
    Make sure to initiate an OBEX CONNECT REQ.
    """
    # Check if need to establish connection first
    need_connection = (
        params.test_case_name.startswith("MAP/MCE/MMN") or
        params.test_case_name.startswith("MAP/MCE/MNR") or
        params.test_case_name.startswith("MAP/MCE/MSM") or
        params.test_case_name.startswith("MAP/MCE/MMD")
    )

    if need_connection:
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()

    stack = get_stack()
    pts_addr = pts_addr_get()

    # Get SDP records
    sdp_list = stack.map.rx_sdp_get(pts_addr, timeout=0)
    if sdp_list is None or len(sdp_list) == 0:
        btp.map_sdp_discover()
        sdp_list = stack.map.rx_sdp_get(pts_addr)
        if sdp_list is None or len(sdp_list) == 0:
            return False

    sdp_list = [sdp for sdp in sdp_list if sdp.role == 'mas']

    if not sdp_list:
        logging.error("No MAS instances found in SDP")
        return False

    # Establish all transport and map connections
    if need_connection:
        for _ in range(len(sdp_list)):
            if not mce_mas_transport_connect():
                return False

            btp.map_mce_mas_connect(default_mce_mas())
            if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_CONNECT, default_mce_mas()) is None:
                return False

    # Send Set Notification Registration to all MAS instances
    connections = stack.map.get_all_connections(pts_addr)
    connected_instances = [conn.instance_id for conn in connections
                           if conn.obex_type == defs.BTP_MAP_EV_MCE_MAS_CONNECT]

    for instance_id in connected_instances:
        mopl = btp.map_get_info(MAPInfo.MOPL, instance_id)
        conn_id = btp.map_get_info(MAPInfo.CONN_ID, instance_id)

        hdr = {
            OBEXHdr.CONN_ID: conn_id,
            OBEXHdr.TYPE: MAPType.SET_NTF_REG,
            OBEXHdr.APP_PARAM: {
                MAPAppParam.NOTIFICATION_STATUS: 1,  # On
            },
            OBEXHdr.BODY: MAP_FILLER_BYTE,
        }

        encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
        btp.map_mce_mas_set_ntf_reg(instance_id, True, encoded_hdr)

        if btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_NTF_REG, instance_id) is None:
            return False

    return True


def hdl_wid_27(_: WIDParams):
    """
    description: Set path to either telecom/msg/draft or telecom/msg/outbox folder,
    and then send a Push Message request with CDMA-SMS message.
    """
    set_folder('outbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    # Create SMS_CDMA message body
    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.SMS_CDMA, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,  # UTF-8
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_28(params: WIDParams):
    """
    description: Set path to either telecom/msg/draft or telecom/msg/outbox folder,
    and then send a Push Message request with EMAIL message.
    """
    if params.test_case_name.startswith("MAP/MCE/MFMH"):
        dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
        if dct is None:
            rsp_code, dct = get_msg_listing('inbox')
            if rsp_code != OBEXRspCode.SUCCESS:
                return False

        btp.map_mce_mas_set_folder(default_mce_mas(), '../outbox')
        btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    else:
        set_folder('outbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    # Create EMAIL message body
    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.EMAIL, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,  # UTF-8
        },
        OBEXHdr.BODY: msg_body,
    }

    if params.test_case_name.startswith("MAP/MCE/MFMH"):
        filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="EMAIL")
        if not filtered:
            return False
        hdr[OBEXHdr.APP_PARAM][MAPAppParam.MESSAGE_HANDLE] = filtered[0]['handle']

        if params.test_case_name == "MAP/MCE/MFMH/BV-01-C":
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.ATTACHMENT] = 0  # OFF
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.MODIFY_TEXT] = 0  # REPLACE
        elif params.test_case_name == "MAP/MCE/MFMH/BV-02-C":
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.ATTACHMENT] = 1  # ON
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.MODIFY_TEXT] = 0  # REPLACE
        elif params.test_case_name == "MAP/MCE/MFMH/BV-03-C":
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.ATTACHMENT] = 0  # OFF
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.MODIFY_TEXT] = 1  # PREPEND
        elif params.test_case_name == "MAP/MCE/MFMH/BV-04-C":
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.ATTACHMENT] = 1  # ON
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.MODIFY_TEXT] = 0  # REPLACE
        elif params.test_case_name == "MAP/MCE/MFMH/BV-05-C":
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.ATTACHMENT] = 1  # ON
            hdr[OBEXHdr.APP_PARAM][MAPAppParam.MODIFY_TEXT] = 1  # PREPEND
        else:
            pass

    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_29(_: WIDParams):
    """
    description: Set path to either telecom/msg/draft or telecom/msg/outbox folder,
    and then send a Push Message request with GSM-SMS message.
    """
    set_folder('outbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    # Create SMS_GSM message body
    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,  # UTF-8
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_30(_: WIDParams):
    """
    description: Set path to either telecom/msg/draft or telecom/msg/outbox folder,
    and then send a Push Message request with MMS message.
    """
    set_folder('outbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    # Create MMS message body
    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.MMS, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,  # UTF-8
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_31(_: WIDParams):
    """
    description: Send Set Event Report with New CDMA Message.
    """
    msg = create_msg(MAPMsgType.SMS_CDMA, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no"
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_32(_: WIDParams):
    """
    description: Send Set Event Report with New EMAIL Message.
    """
    msg = create_msg(MAPMsgType.EMAIL, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no"
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_33(_: WIDParams):
    """
    description: Send Set Event Report with New GSM Message.
    """
    msg = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no",
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_35(_: WIDParams):
    """
    description: Please send Set Event Report with New IM Message.
    """
    msg = create_msg(MAPMsgType.IM, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no",
                conversation_id=conversation_id,
                conversation_name=conv.name,
                read_status=conv.read_status,
                participant_uci=conv.participants[0].uci,
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_44(_: WIDParams):
    """
    description: Make sure you set folder to /telecom/msg/inbox
    """
    set_folder('inbox')
    return True


def hdl_wid_45(_: WIDParams):
    """
    description: Send a Set Folder request to any valid folder.
    """
    btp.map_mce_mas_set_folder(default_mce_mas(), '/')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    btp.map_mce_mas_set_folder(default_mce_mas(), 'telecom')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())
    return True


def hdl_wid_46(_: WIDParams):
    """
    description: Send a Set Message Status request, setting the status from unread to read, on a SMS_CDMA message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_CDMA", read="no")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.READ_STATUS,
            MAPAppParam.STATUS_VALUE: 1,  # Read
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_47(_: WIDParams):
    """
    description: Send a Set Message Status request, setting the status from unread to read, on an EMAIL message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="EMAIL", read="no")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.READ_STATUS,
            MAPAppParam.STATUS_VALUE: 1,  # Read
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_48(_: WIDParams):
    """
    description: Send a Set Message Status request, setting the status from unread to read, on a SMS_GSM message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_GSM", read="no")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.READ_STATUS,
            MAPAppParam.STATUS_VALUE: 1,  # Read
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_49(params: WIDParams):
    """
    description: Using the Implementation Under Test(IUT), initiate ACL Create Connection Request to the PTS.
    """
    if params.test_case_name.startswith("MAP/MCE/SGSIT") or \
        params.test_case_name.startswith("IOPT/MAP/MCE/SDPR"):
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
        return True

    """
    description: Send a Set Message Status request, setting the status from unread to read, on a MMS message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="MMS", read="no")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.READ_STATUS,
            MAPAppParam.STATUS_VALUE: 1,  # Read
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_51(_: WIDParams):
    """
    description: Send an Update Inbox request.
    """
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: MAPType.UPDATE_INBOX,
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_update_inbox(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_UPDATE_INBOX, default_mce_mas())
    return True


def hdl_wid_53(_: WIDParams):
    """
    description: Verify that the status of one of the messages in IUT's inbox folder has changed from Unread to Read,
    then click OK. Otherwise click Cancel.
    """
    return True


def hdl_wid_54(_: WIDParams):
    """
    description: Verify that the message has been successfully delivered via the network,
    then click OK. Otherwise click Cancel.
    """
    return True


def hdl_wid_55(_: WIDParams):
    """
    description: Verify that new message is loaded from its corresponding remote mailbox,
    then click OK. Otherwise click Cancel.
    """
    msg = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    return True


def hdl_wid_56(_: WIDParams):
    """
    description: Verify that new message event is signal to the user, then click OK. Otherwise click Cancel.
    """
    return True


def hdl_wid_57(_: WIDParams):
    """
    description: Please add a message in the folder, then click OK. Otherwise click Cancel.
    """
    msg = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    return True


def hdl_wid_58(_: WIDParams):
    """
    description: Please add a participant in current a conversation.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv:
        logging.error(f"Conversation {conversation_id} not found in storage")
        return False

    # Add a new participant to the conversation
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    new_participant = MAPParticipant(
        uci="im:newuser@example.com",
        display_name="NewUser",
        chat_state=MAPChatState.ACTIVE,
        last_activity=datetime_str,
        name="NewUser",
        presence_availability=MAPPresenceAvailability.ONLINE,
        presence_text="Available",
        priority=0
    )

    # Create updated participant list with the new participant
    updated_participants = conv.participants.copy()
    updated_participants.append(new_participant)

    # Update conversation with new participant
    stack.map.storage.update_conversation(
        conversation_id,
        participants=updated_participants,
        last_activity=datetime_str
    )

    return True


def hdl_wid_59(_: WIDParams):
    """
    description: Please create a new conversation, then click OK. Otherwise click Cancel.
    """
    stack = get_stack()
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Create participants
    participants = [
        MAPParticipant(
            uci="im:pts@example.com",
            display_name="PTS",
            chat_state=MAPChatState.ACTIVE,
            last_activity=datetime_str,
            name="PTS",
            presence_availability=MAPPresenceAvailability.ONLINE,
            presence_text="Available",
            priority=0
        ),
        MAPParticipant(
            uci="im:iut@example.com",
            display_name="IUT",
            chat_state=MAPChatState.ACTIVE,
            last_activity=datetime_str,
            name="IUT",
            presence_availability=MAPPresenceAvailability.ONLINE,
            presence_text="Available",
            priority=0
        )
    ]

    # Create a new conversation
    new_conversation = MAPConversation(
        id="",  # Will be auto-generated
        name="New Conversation",
        last_activity=datetime_str,
        read_status="unread",
        summary="New conversation created",
        participants=participants
    )

    # Add conversation to storage
    stack.map.storage.add_conversation(new_conversation)
    return True


def hdl_wid_60(_: WIDParams):
    """
    description: Please change the presence, chat-state and LastActivity of a participant,
    then click OK. Otherwise click Cancel.
    """
    return True


def hdl_wid_61(_: WIDParams):
    """
    description: Send a Get Message request to retrieve an IM message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="IM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.GET_MSG,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.ATTACHMENT: 0,
            MAPAppParam.CHARSET: 1,  # UTF-8
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG, default_mce_mas())
    return True


def hdl_wid_62(_: WIDParams):
    """
    description: Send a Get Conversation Listing request.
    """
    rsp_code, _ = get_convo_listing()
    if rsp_code != OBEXRspCode.SUCCESS:
        return False
    return True


def hdl_wid_63(_: WIDParams):
    """
    description: Send a Set Message Status request, setting the status from unread to read, on an IM message.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="IM", read="no")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.READ_STATUS,
            MAPAppParam.STATUS_VALUE: 1,  # Read
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_64(_: WIDParams):
    """
    description: Set path to telecom/msg/inbox folder, and then send a Push Message request
    with IM message type and valid conversation ID.
    """
    set_folder('inbox')

    dct = btp.map_get_info(MAPInfo.CONVO_LISTING, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_convo_listing()
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    convo_list = parse_convo_listing(dct[OBEXHdr.BODY])
    if not convo_list or convo_list[0].get('id') is None:
        return False
    convo_id = convo_list[0].get('id')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    # Create IM message body
    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.IM, "telecom/msg/inbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,  # UTF-8
            MAPAppParam.CONVERSATION_ID: convo_id,  # Valid conversation ID
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_65(_: WIDParams):
    """
    description: Send an GetOwnerStatus request.
    """
    dct = btp.map_get_info(MAPInfo.CONVO_LISTING, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_convo_listing()
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    convo_list = parse_convo_listing(dct[OBEXHdr.BODY])
    if not convo_list or convo_list[0].get('id') is None:
        return False
    convo_id = convo_list[0].get('id')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_OWNER_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CONVERSATION_ID: convo_id,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_owner_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_OWNER_STATUS, default_mce_mas())
    return True


def hdl_wid_66(_: WIDParams):
    """
    description: Send an SetOwnerStatus request.
    """
    dct = btp.map_get_info(MAPInfo.CONVO_LISTING, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_convo_listing()
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    convo_list = parse_convo_listing(dct[OBEXHdr.BODY])
    if not convo_list or convo_list[0].get('id') is None:
        return False
    convo_id = convo_list[0].get('id')

    if btp.map_get_info(MAPInfo.UTC_OFFSET, default_mce_mas()):
        last_activity = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    else:
        last_activity = datetime.now().strftime("%Y%m%dT%H%M%S")

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: MAPType.SET_OWNER_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.PRESENCE_AVAILABILITY: MAPPresenceAvailability.UNKNOWN,
            MAPAppParam.PRESENCE_TEXT: "",
            MAPAppParam.LAST_ACTIVITY: last_activity,
            MAPAppParam.CHAT_STATE: MAPChatState.UNKNOWN,
            MAPAppParam.CONVERSATION_ID: convo_id,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_owner_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_OWNER_STATUS, default_mce_mas())
    return True


def hdl_wid_67(_: WIDParams):
    """
    description: Send Set Event Report that add a participant to a conversation Message.
    """
    stack = get_stack()
    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    # Add a new participant to the conversation
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    new_participant = MAPParticipant(
        uci="im:newuser@example.com",
        display_name="NewUser",
        chat_state=MAPChatState.ACTIVE,
        last_activity=datetime_str,
        name="NewUser",
        presence_availability=MAPPresenceAvailability.ONLINE,
        presence_text="Available",
        priority=0
    )

    # Create updated participant list with the new participant
    updated_participants = conv.participants.copy()
    updated_participants.append(new_participant)

    # Update conversation with new participant
    stack.map.storage.update_conversation(
        conversation_id,
        participants=updated_participants,
        last_activity=datetime_str
    )

    event = MAPEvent(
                event_type=MAPEventType.CONVERSATION_CHANGED,
                conversation_id=conversation_id,
                conversation_name=conv.name,
                participant_uci="im:newuser@example.com",
                presence_availability=MAPPresenceAvailability.ONLINE,
                presence_text="Available",
                chat_state=MAPChatState.ACTIVE,
                last_activity=datetime_str,
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_68(_: WIDParams):
    """
    description: Send a Get Message Listing request with for a specific conversation.
    """
    dct = btp.map_get_info(MAPInfo.CONVO_LISTING, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_convo_listing()
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    convo_list = parse_convo_listing(dct[OBEXHdr.BODY])
    if not convo_list or convo_list[0].get('id') is None:
        return False
    convo_id = convo_list[0].get('id')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CONVERSATION_ID: convo_id,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_69(_: WIDParams):
    """
    description: Send a Get Conversation Listing request with maxlistcount set to zero.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_CONVO_LISTING,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAX_LIST_COUNT: 0,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_convo_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, default_mce_mas())
    return True


def hdl_wid_70(_: WIDParams):
    """
    description: Send a Get Conversation Listing request with FilterRecipient.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_CONVO_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_RECIPIENT: "IUT",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_convo_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, default_mce_mas())
    return True


def hdl_wid_71(_: WIDParams):
    """
    description: Send a Get Conversation Listing request with Last Activity.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_CONVO_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_LAST_ACTIVITY_BEGIN: "20100101T000000+0000",
            MAPAppParam.FILTER_LAST_ACTIVITY_END: "20111231T125959+0000",
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_convo_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, default_mce_mas())
    return True


def hdl_wid_72(_: WIDParams):
    """
    description: Send a Get Conversation Listing request with read status.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_CONVO_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_READ_STATUS: 1,  # Unread
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_convo_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_CONVO_LISTING, default_mce_mas())
    return True


def hdl_wid_75(_: WIDParams):
    """
    description: Send 1.2 Event Report.
    """
    msg = create_msg(MAPMsgType.IM, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no",
                conversation_id=conversation_id,
                conversation_name=conv.name,
                read_status=conv.read_status,
                participant_uci=conv.participants[0].uci,
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_76(_: WIDParams):
    """
    description: Send Set Event Report for adding a conversation
    """
    stack = get_stack()
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Create participants
    participants = [
        MAPParticipant(
            uci="im:pts@example.com",
            display_name="PTS",
            chat_state=MAPChatState.ACTIVE,
            last_activity=datetime_str,
            name="PTS",
            presence_availability=MAPPresenceAvailability.ONLINE,
            presence_text="Available",
            priority=0
        ),
        MAPParticipant(
            uci="im:iut@example.com",
            display_name="IUT",
            chat_state=MAPChatState.ACTIVE,
            last_activity=datetime_str,
            name="IUT",
            presence_availability=MAPPresenceAvailability.ONLINE,
            presence_text="Available",
            priority=0
        )
    ]

    # Create a new conversation
    new_conversation = MAPConversation(
        id="",  # Will be auto-generated
        name="New Conversation",
        last_activity=datetime_str,
        read_status="unread",
        summary="New conversation created",
        participants=participants
    )

    # Add conversation to storage
    conversation_id = stack.map.storage.add_conversation(new_conversation)

    event = MAPEvent(
        event_type=MAPEventType.CONVERSATION_CHANGED,
        conversation_id=conversation_id,
        conversation_name=new_conversation.name,
        last_activity=datetime_str,
        presence_availability=MAPPresenceAvailability.ONLINE,
        presence_text="Available",
        chat_state=MAPChatState.ACTIVE,
        participant_uci=participants[0].uci,  # First participant
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_77(_: WIDParams):
    """
    description: Send a properly formatted SetNotificationFilter request from the Implementation Under Test (IUT).
    """
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: MAPType.SET_NTF_FILTER,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.NOTIFICATION_FILTER_MASK: 0x00007FFF,  # All events
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_ntf_filter(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_NTF_FILTER, default_mce_mas())
    return True


def hdl_wid_78(_: WIDParams):
    """
    description: Send a Set Message Status request to set the status of an IM message from undeleted to deleted.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="IM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.DELETED_STATUS,
            MAPAppParam.STATUS_VALUE: 1,
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_79(_: WIDParams):
    """
    description: Send Set Event Report that change the chat state of the owner Message.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv:
        logging.error("Conversation not found in storage")
        return False

    # Update owner's chat state
    new_chat_state = MAPChatState.COMPOSING
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    if not conv or not conv.participants:
        logging.error("Conversation has no participants")
        return False

    # Also update owner status in storage
    stack.map.storage.set_owner_status(
        conversation_id=conversation_id,
        chat_state=new_chat_state,
        last_activity=datetime_str
    )

    event = MAPEvent(
        event_type=MAPEventType.PARTICIPANT_CHAT_STATE_CHANGED,
        conversation_id=conversation_id,
        conversation_name=conv.name,
        chat_state=new_chat_state,
        last_activity=datetime_str,
    )

    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_80(_: WIDParams):
    """
    description: Send Set Event Report that remove a participant to a conversation Message.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv or not conv.participants:
        logging.error("Conversation has no participants")
        return False

    # Remove a participant from the conversation (remove the last participant)
    participant_removed = conv.participants[-1]
    updated_participants = conv.participants[:-1]
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Use update_conversation to update all fields at once
    stack.map.storage.update_conversation(
        conversation_id,
        participants=updated_participants,
        last_activity=datetime_str
    )

    event = MAPEvent(
        event_type=MAPEventType.CONVERSATION_CHANGED,
        conversation_id=conversation_id,
        conversation_name=conv.name,
        last_activity=datetime_str,
        participant_uci=participant_removed.uci,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas()
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_81(_: WIDParams):
    """
    description: Send Set Event Report with change the presence of the owner Message.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv:
        logging.error("Conversation not found in storage")
        return False

    # Update owner's presence
    new_presence_availability = MAPPresenceAvailability.DO_NOT_DISTURB
    new_presence_text = "Do not disturb"
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Also update owner status in storage
    stack.map.storage.set_owner_status(
        conversation_id=conversation_id,
        presence_availability=new_presence_availability,
        presence_text=new_presence_text,
        last_activity=datetime_str
    )

    event = MAPEvent(
        event_type=MAPEventType.PARTICIPANT_PRESENCE_CHANGED,
        conversation_id=conversation_id,
        conversation_name=conv.name,
        presence_availability=new_presence_availability,
        presence_text=new_presence_text,
        last_activity=datetime_str,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_82(_: WIDParams):
    """
    description: Send Set Event Report with MessageExtendedDataChanged Message.
    """
    stack = get_stack()

    # Find an IM message from storage
    im_messages = [msg for msg in stack.map.storage.messages.values()
                   if msg.msg_type == MAPMsgType.IM]
    if not im_messages:
        logging.error("No IM messages found in storage")
        return False
    msg = im_messages[0]

    if not msg.conversation_id:
        logging.error("IM Message has no conversation_id")
        return False

    conv = stack.map.storage.get_conversation(msg.conversation_id)
    if conv is None:
        logging.error(f"Conversation {msg.conversation_id} not found in storage")
        return False

    # Modify the extended data
    new_extended_data = "0:54;"  # 54 Facebook likes

    stack.map.storage.set_message_status(
        handle=msg.handle,
        status_indicator=MAPMsgStatusInd.SET_EXTENDED_DATA,
        extended_data=new_extended_data
    )

    # Create event
    event = MAPEvent(
        event_type=MAPEventType.MESSAGE_EXTENDED_DATA_CHANGED,
        handle=msg.handle,
        folder=msg.folder,
        msg_type=msg.msg_type,
        datetime=msg.datetime,
        sender_name=msg.sender_name,
        conversation_name=conv.name,
        conversation_id=conv.id,
        extended_data=msg.extended_data,
        participant_uci=conv.participants[0].uci,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_83(_: WIDParams):
    """
    description: Send Set Event Report with MessageRemoved Message.
    """
    stack = get_stack()

    # Find a message from storage to remove
    if not stack.map.storage.messages:
        logging.error("No messages found in storage")
        return False

    # Get the first message
    msg_handle = list(stack.map.storage.messages.keys())[0]
    msg = stack.map.storage.get_message(msg_handle)

    if not msg:
        logging.error(f"Message {msg_handle} not found in storage")
        return False

    event = MAPEvent(
        event_type=MAPEventType.MESSAGE_REMOVED,
        handle=msg.handle,
        folder=msg.folder,
        msg_type=msg.msg_type,
        conversation_id=msg.conversation_id,
        conversation_name=msg.conversation_name,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_84(_: WIDParams):
    """
    description: Send Set Event Report with ParticipantChatStateChanged Message.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv or not conv.participants:
        logging.error("Conversation has no participants")
        return False

    # Modify participant chat state (first participant)
    participant_idx = 0
    new_chat_state = MAPChatState.COMPOSING
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Create updated participant list with modified chat state
    updated_participants = conv.participants.copy()
    updated_participants[participant_idx].chat_state = new_chat_state
    updated_participants[participant_idx].last_activity = datetime_str

    stack.map.storage.update_conversation(
        conversation_id,
        participants=updated_participants,
        last_activity=datetime_str
    )

    event = MAPEvent(
        event_type=MAPEventType.PARTICIPANT_CHAT_STATE_CHANGED,
        conversation_id=conversation_id,
        conversation_name=conv.name,
        chat_state=new_chat_state,
        last_activity=datetime_str,
        sender_name=updated_participants[participant_idx].display_name,
        participant_uci=updated_participants[participant_idx].uci,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_85(_: WIDParams):
    """
    description: Send Set Event Report with change the presence of a participant Message.
    """
    stack = get_stack()

    # Find a conversation from storage
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv or not conv.participants:
        logging.error("Conversation has no participants")
        return False

    # Modify participant presence (first participant)
    participant_idx = 0
    new_presence_availability = MAPPresenceAvailability.BUSY
    new_presence_text = "Busy"
    datetime_str = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")

    # Create updated participant list with modified presence
    updated_participants = conv.participants.copy()
    updated_participants[participant_idx].presence_availability = new_presence_availability
    updated_participants[participant_idx].presence_text = new_presence_text
    updated_participants[participant_idx].last_activity = datetime_str

    stack.map.storage.update_conversation(
        conversation_id,
        participants=updated_participants,
        last_activity=datetime_str
    )

    event = MAPEvent(
        event_type=MAPEventType.PARTICIPANT_PRESENCE_CHANGED,
        conversation_id=conversation_id,
        conversation_name=conv.name,
        presence_availability=new_presence_availability,
        presence_text=new_presence_text,
        last_activity=datetime_str,
        sender_name=updated_participants[participant_idx].display_name,
        participant_uci=updated_participants[participant_idx].uci,
    )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_86(_: WIDParams):
    """
    description: Send a Get Message Listing request with maxlistcount set to zero.
    """
    set_folder('inbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAX_LIST_COUNT: 0,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_87(_: WIDParams):
    """
    description: Send a Set Message Status request, setting new values for the extended data.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_GSM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: msg_handle,
        OBEXHdr.TYPE: MAPType.SET_MSG_STATUS,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.STATUS_INDICATOR: MAPMsgStatusInd.SET_EXTENDED_DATA,
            MAPAppParam.EXTENDED_DATA: "0:54;",  # 54 Facebook likes
        },
        OBEXHdr.BODY: MAP_FILLER_BYTE,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_mce_mas_set_msg_status(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_MSG_STATUS, default_mce_mas())
    return True


def hdl_wid_88(_: WIDParams):
    """
    description: Send Set Event Report with New MMS Message.
    """
    msg = create_msg(MAPMsgType.MMS, "telecom/msg/inbox")
    stack = get_stack()
    stack.map.storage.add_message(msg)
    event = MAPEvent(
                event_type=MAPEventType.NEW_MESSAGE,
                handle=msg.handle,
                folder=msg.folder,
                msg_type=msg.msg_type,
                datetime=msg.datetime,
                subject=msg.subject,
                sender_name=msg.sender_name,
                priority="yes" if msg.priority else "no"
            )
    version = btp.map_get_info(MAPInfo.EVENT_VERSION)
    utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
    event_body = stack.map.storage.send_event(event, version, utc_offset)

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
    mopl = btp.map_get_info(MAPInfo.MOPL)
    conn_id = btp.map_get_info(MAPInfo.CONN_ID)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.SEND_EVENT,
        OBEXHdr.APP_PARAM: {
            MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
        },
        OBEXHdr.BODY: event_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
    btp.map_set_info(MAPInfo.TX_CNT, offset)
    btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)
    return True


def hdl_wid_89(_: WIDParams):
    """
    description: Is the IUT capable of establishing connection to an unpaired device?
    """
    return True


def hdl_wid_90(_: WIDParams):
    """
    description: Click OK when the IUT becomes connectable.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True


def hdl_wid_91(_: WIDParams):
    """
    description: Send a Get Message Listing request, filtered by message handle.
    """
    dct = btp.map_get_info(MAPInfo.INBOX, default_mce_mas())
    if dct is None:
        rsp_code, dct = get_msg_listing('inbox')
        if rsp_code != OBEXRspCode.SUCCESS:
            return False

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    filtered = filter_msg_from_listing(dct[OBEXHdr.BODY], type="SMS_GSM")
    if not filtered:
        return False
    msg_handle = filtered[0]['handle']

    # Now send filtered request
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.FILTER_MSG_HANDLE: msg_handle,
        }
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_92(_: WIDParams):
    """
    description: Verify that a new message has been added to the messages-listing,
    then click OK. Otherwise click Cancel.
    """
    return True


def hdl_wid_93(_: WIDParams):
    """
    description: Send Set Event Report for deleting a conversation
    """
    stack = get_stack()

    # Find a conversation from storage to delete
    if not stack.map.storage.conversations:
        logging.error("No conversations found in storage")
        return False

    conversation_id = list(stack.map.storage.conversations.keys())[0]
    conv = stack.map.storage.get_conversation(conversation_id)

    if not conv:
        logging.error(f"Conversation {conversation_id} not found in storage")
        return False

    # Find and delete all messages in this conversation
    messages_to_delete = []
    for handle, msg in stack.map.storage.messages.items():
        if msg.conversation_id == conversation_id:
            messages_to_delete.append((handle, msg))

    # Delete messages and generate MessageRemoved events
    for handle, msg in messages_to_delete:
        stack.map.storage.delete_message(handle, permanent=True)

        # Generate MessageRemoved event
        event = MAPEvent(
            event_type=MAPEventType.MESSAGE_REMOVED,
            handle=handle,
            folder=msg.folder,
            msg_type=msg.msg_type,
            conversation_id=conversation_id,
            conversation_name=conv.name,
        )
        version = btp.map_get_info(MAPInfo.EVENT_VERSION)
        utc_offset = btp.map_get_info(MAPInfo.UTC_OFFSET)
        event_body = stack.map.storage.send_event(event, version, utc_offset)

        is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED)
        mopl = btp.map_get_info(MAPInfo.MOPL)
        conn_id = btp.map_get_info(MAPInfo.CONN_ID)

        hdr = {
            OBEXHdr.CONN_ID: conn_id,
            OBEXHdr.SRM: 1 if is_l2cap else 0,
            OBEXHdr.TYPE: MAPType.SEND_EVENT,
            OBEXHdr.APP_PARAM: {
                MAPAppParam.MAS_INSTANCE_ID: default_mse_mas(),
            },
            OBEXHdr.BODY: event_body,
        }
        encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
        btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap)
        btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr)
        btp.map_set_info(MAPInfo.TX_CNT, offset)
        btp.map_mse_mns_send_event(len(remaining_hdr) == 0, encoded_hdr)
        btp.map_rx_data_get(defs.BTP_MAP_EV_MSE_MNS_SEND_EVENT)

    # Delete the conversation from storage
    stack.map.storage.delete_conversation(conversation_id)

    return True


def hdl_wid_4000(_: WIDParams):
    """
    description: Please accept the COPY ACTION command.
    """
    return True


def hdl_wid_4001(_: WIDParams):
    """
    description: Please accept the MOVE RENAME ACTION command.
    """
    return True


def hdl_wid_4002(_: WIDParams):
    """
    description: Please accept the SET PERMISSIONS ACTION command.
    """
    return True


def hdl_wid_4003(_: WIDParams):
    """
    description: Please accept the browse folders (GET) command.
    """
    return True


def hdl_wid_4004(params: WIDParams):
    """
    description: Please accept the OBEX CONNECT REQ.
    """
    return True


def hdl_wid_4007(_: WIDParams):
    """
    description: Please accept the OBEX DISCONNECT REQ command.
    """
    return True


def hdl_wid_4008(_: WIDParams):
    """
    description: Please accept the GET REQUEST.
    Note: This MMI will disappear after the GET operation completes.
    """
    return True


def hdl_wid_4010(_: WIDParams):
    """
    description: Please accept the GET REQUEST with an SRM ENABLED header.
    """
    return True


def hdl_wid_4012(_: WIDParams):
    """
    description: Please accept the PUT REQUEST.
    """
    return True


def hdl_wid_4014(_: WIDParams):
    """
    description: Please accept the PUT REQUEST with an SRM ENABLED header.
    """
    return True


def hdl_wid_4016(_: WIDParams):
    """
    description: Please accept the SET_PATH command.
    """
    return True


def hdl_wid_4017(_: WIDParams):
    """
    description: Please accept the l2cap channel connection for an OBEX connection.
    """
    return True


def hdl_wid_4018(_: WIDParams):
    """
    description: Please accept the rfcomm channel connection for an OBEX connection.
    """
    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED, default_mse_mas()) is None:
        return False
    return True


def hdl_wid_4019(_: WIDParams):
    """
    description: Please accept the disconnection of the transport channel.
    """
    return True


def hdl_wid_4020(_: WIDParams):
    """
    description: Take action to send a COPY ACTION command.
    """
    # COPY ACTION not typically used in MAP
    return True


def hdl_wid_4021(_: WIDParams):
    """
    description: Take action to send a MOVE RENAME ACTION command.
    """
    # MOVE RENAME ACTION not typically used in MAP
    return True


def hdl_wid_4022(_: WIDParams):
    """
    description: Take action to send a SET PERMISSIONS ACTION command.
    """
    # SET PERMISSIONS ACTION not typically used in MAP
    return True


def hdl_wid_4024(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ.
    """
    btp.map_mce_mas_connect(default_mce_mas())
    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_CONNECT, default_mce_mas()) is None:
        return False
    return True


def hdl_wid_4025(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP.
    """
    # FTP is not MAP - skip
    return True


def hdl_wid_4026(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP with authentication.
    """
    # FTP is not MAP - skip
    return True


def hdl_wid_4027(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP without authentication.
    """
    # FTP is not MAP - skip
    return True


def hdl_wid_4031(_: WIDParams):
    """
    description: Take action to initiate an OBEX DISCONNECT REQ.
    """
    stack = get_stack()
    pts_addr = pts_addr_get()

    connections = stack.map.get_all_connections(pts_addr)
    connected_instances = [conn.instance_id for conn in connections
                           if conn.obex_type == defs.BTP_MAP_EV_MCE_MAS_CONNECT]

    for instance_id in connected_instances:
        btp.map_mce_mas_disconnect(instance_id)
        if btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_DISCONNECT, instance_id) is None:
            return False

        if btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, instance_id):
            btp.map_mce_mas_l2cap_disconnect(instance_id)
            if btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_L2CAP_DISCONNECT, instance_id) is None:
                return False
        elif btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, instance_id):
            btp.map_mce_mas_rfcomm_disconnect(instance_id)
            if btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_DISCONNECT, instance_id) is None:
                return False

    return True


def hdl_wid_4032(_: WIDParams):
    """
    description: Take action to send a GET request. Then allow the operation to complete as normal.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_FOLDER_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_folder_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, default_mce_mas())
    return True


def hdl_wid_4034(_: WIDParams):
    """
    description: Take action to send a GET request without an SRM header.
    Then allow the operation to complete as normal.
    """
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: MAPType.GET_FOLDER_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, False, default_mce_mas())
    btp.map_mce_mas_get_folder_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, default_mce_mas())
    return True


def hdl_wid_4035(_: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header.
    Then allow the operation to complete as normal.
    """
    set_folder('inbox')

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1,  # Enable SRM
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: ''
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, True, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_4036(_: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header and an SRMP WAIT header.
    Then allow the operation to complete as normal.
    """
    set_folder('inbox')

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1,   # Enable SRM
        OBEXHdr.SRMP: 1,  # Wait
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: ''
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, True, default_mce_mas())
    btp.map_set_info(MAPInfo.LOCAL_SRMP, True, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_4037(_: WIDParams):
    """
    description: Take action to send a PUT request. Then allow the operation to complete as normal.
    """
    set_folder('outbox')

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas())
    return True


def hdl_wid_4038(_: WIDParams):
    """
    description: Take action to send a PUT request without an SRM header.
    Then allow the operation to complete as normal.
    Note: This object must be large enough to span multiple packets.
    """
    set_folder('outbox')

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, False, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    if btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas()) is None:
        return False
    return True


def hdl_wid_4039(_: WIDParams):
    """
    description: Take action to send a PUT request with an SRM ENABLED header.
    Then allow the operation to complete as normal.
    Note: This object should be large enough to span multiple packets.
    """
    set_folder('outbox')

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    supported_features = btp.map_get_info(MAPInfo.SUPPORTED_FEATURES, default_mce_mas())
    version = "1.1" if supported_features & MAPSupportedFeatures.MSG_FORMAT_VERSION_1_1 else "1.0"
    msg_body = create_msg(MAPMsgType.SMS_GSM, "telecom/msg/outbox").to_bmessage(version)

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1,  # Enable SRM
        OBEXHdr.TYPE: MAPType.PUSH_MSG,
        OBEXHdr.NAME: "",
        OBEXHdr.APP_PARAM: {
            MAPAppParam.CHARSET: 1,
        },
        OBEXHdr.BODY: msg_body,
    }
    encoded_hdr, remaining_hdr, offset = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, True, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_DATA, remaining_hdr, default_mce_mas())
    btp.map_set_info(MAPInfo.TX_CNT, offset, default_mce_mas())
    btp.map_mce_mas_push_msg(default_mce_mas(), len(remaining_hdr) == 0, encoded_hdr)
    if btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_PUSH_MSG, default_mce_mas()) is None:
        return False
    return True


def hdl_wid_4040(_: WIDParams):
    """
    description: Take action to send a vCard (PUT) to PTS.
    """
    # vCard is not part of MAP - skip
    return True


def hdl_wid_4042(_: WIDParams):
    """
    description: Take action to send a Set Path up one level.
    Note: Flags = Backup, Don't Create
    """
    # Flags: 0x03 = Backup (go up) + Don't Create
    btp.map_mce_mas_set_folder(default_mce_mas(), flags=0x03, buf_data=b'')
    return True


def hdl_wid_4046(_: WIDParams):
    """
    description: Take action to move to the root folder by sending a Set Path command
    with Flags = Don't Create and an empty Name header.
    """
    # Flags: 0x02 = Don't Create, empty name = go to root
    btp.map_mce_mas_set_folder(default_mce_mas(), flags=0x02, buf_data=b'')
    return True


def hdl_wid_4047(_: WIDParams):
    """
    description: Take action to create an l2cap channel for an OBEX connection.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    return mce_mas_transport_connect(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED)


def hdl_wid_4048(_: WIDParams):
    """
    description: Take action to create an rfcomm channel for an OBEX connection.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    return mce_mas_transport_connect(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED)


def hdl_wid_4049(_: WIDParams):
    """
    description: Take action to disconnect the transport channel.
    """
    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, default_mce_mas(), timeout=0):
        btp.map_mce_mas_rfcomm_disconnect(default_mce_mas())
        btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_DISCONNECT, default_mce_mas())
    elif btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas(), timeout=0):
        btp.map_mce_mas_l2cap_disconnect(default_mce_mas())
        btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_L2CAP_DISCONNECT, default_mce_mas())
    return True


def hdl_wid_4050(_: WIDParams):
    """
    description: Take action to reject the ACTION command sent by PTS.
    """
    return True


def hdl_wid_4054(_: WIDParams):
    """
    description: Was the currently displayed file or folder sent by the IUT?
    """
    return True


def hdl_wid_4056(_: WIDParams):
    """
    description: Was the currently displayed vcard sent by the IUT?
    """
    return True


def hdl_wid_4058(_: WIDParams):
    """
    description: Please respond to the PUT REQUEST with an SRM ENABLED header and an SRMP WAIT header.
    """
    return True


def hdl_wid_4059(params: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for MAP.
    """
    if params.test_case_name.startswith("MAP/MCE") or \
        params.test_case_name.startswith("IOPT/MAP/MCE"):
        btp.map_mce_mas_connect(default_mce_mas())
        if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_CONNECT, default_mce_mas()) is None:
            return False
    return True


def hdl_wid_4074(_: WIDParams):
    """
    description: Take action to respond to the folder listing request sent by the tester.
    """
    return True


def hdl_wid_4075(_: WIDParams):
    """
    description: Take action to accept the Push Folder operation from the tester.
    """
    return True


def hdl_wid_4077(_: WIDParams):
    """
    description: Take action to create a folder, using the Set Path command and flags = None.
    Note: The name must be for a new folder.
    """
    return True


def hdl_wid_4079(_: WIDParams):
    """
    description: Take action to delete the file or folder named '%s' in the current directory.
    """
    return True


def hdl_wid_4080(_: WIDParams):
    """
    description: Take action to browse the current folder listings.
    """
    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_FOLDER_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_folder_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, default_mce_mas())
    return True


def hdl_wid_4081(_: WIDParams):
    """
    description: Take action to browse the '%s' sub folder.
    Note: To browse a sub folder listing, change path to the specified sub folder
    and perform a browse folder listings operation.
    """
    # Navigate to subfolder (e.g., 'msg')
    btp.map_mce_mas_set_folder(default_mce_mas(), 'msg')
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_SET_FOLDER, default_mce_mas())

    is_l2cap = btp.map_is_connected(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas())
    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: MAPType.GET_FOLDER_LISTING,
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, is_l2cap, default_mce_mas())
    btp.map_mce_mas_get_folder_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_FOLDER_LISTING, default_mce_mas())
    return True


def hdl_wid_4082(_: WIDParams):
    """
    description: Take action to move to the '%s' folder the Set Path command and flags = Don't Create.
    """
    # Navigate to specified folder with Don't Create flag
    btp.map_mce_mas_set_folder(default_mce_mas(), 'telecom', flags=0x02)
    return True


def hdl_wid_4083(_: WIDParams):
    """
    description: Take action to perform a Pull Folder operation on the '%s' folder.
    The IUT must return back to the current folder after the Pull Folder operation is complete.
    """
    # Pull folder is not part of MAP
    return True


def hdl_wid_4084(_: WIDParams):
    """
    description: Take action to perform a Pull Folder operation on the '%s' folder.
    Once the Pull Folder operation begins quickly take action to send an ABORT operation.
    """
    # Pull folder with abort is not part of MAP
    return True


def hdl_wid_4085(_: WIDParams):
    """
    description: Take action to PUSH a folder to the Server.
    Make sure the folder being pushed does not already exist on the Server.
    Once all files have been pushed Set Path back to the original folder.
    """
    # Push folder is not part of MAP
    return True


def hdl_wid_4086(_: WIDParams):
    """
    description: Take action to ABORT a PUSH a folder operation.
    Make sure to push large files, then once the Push Folder operation begings take action to ABORT the operation.
    """
    # Push folder with abort is not part of MAP
    return True


def hdl_wid_4087(_: WIDParams):
    """
    description: Take action to Push a folder to the tester.
    Note: The create folder will be rejected by the tester, the IUT should not attempt to Push any files afterwards.
    """
    # Push folder is not part of MAP
    return True


def hdl_wid_4088(_: WIDParams):
    """
    description: Take action to ABORT the current operation.
    """
    btp.map_mce_mas_abort(default_mce_mas())
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_ABORT, default_mce_mas())
    return True


def hdl_wid_4090(_: WIDParams):
    """
    description: Take action to send a GET REQUEST with an SRM ENABLED header and an SRMP WAIT header.
    The next GET REQUEST must also contain an SRMP WAIT header.
    The third GET REQUEST must not contain an SRMP WAIT header.
    """
    set_folder('inbox')

    mopl = btp.map_get_info(MAPInfo.MOPL, default_mce_mas())
    conn_id = btp.map_get_info(MAPInfo.CONN_ID, default_mce_mas())

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1,   # Enable SRM
        OBEXHdr.SRMP: 1,  # Wait
        OBEXHdr.TYPE: MAPType.GET_MSG_LISTING,
        OBEXHdr.NAME: ''
    }
    encoded_hdr, _, _ = btp.map_enc_hdr(hdr, mopl - 3, 0)
    btp.map_set_info(MAPInfo.LOCAL_SRM, True, default_mce_mas())
    btp.map_set_info(MAPInfo.LOCAL_SRMP, 2, default_mce_mas())
    btp.map_mce_mas_get_msg_listing(default_mce_mas(), True, encoded_hdr)
    btp.map_rx_data_get(defs.BTP_MAP_EV_MCE_MAS_GET_MSG_LISTING, default_mce_mas())
    return True


def hdl_wid_4091(_: WIDParams):
    """
    description: Take action to reject the SESSION command sent by PTS.
    """
    return True


def hdl_wid_4100(params: WIDParams):
    """
    description: Take action to create an l2cap channel or rfcomm channel for an OBEX connection.
    """
    if params.test_case_name.startswith("MAP/MCE") or \
        params.test_case_name.startswith("IOPT/MAP/MCE"):
        btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
        btp.gap_wait_for_connection()
        return mce_mas_transport_connect()
    return True


def hdl_wid_4101(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for CTN.
    """
    # CTN (Calendar, Task, and Notes) is not MAP
    return True


def hdl_wid_4102(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for CTN with authentication.
    """
    # CTN is not MAP
    return True


def hdl_wid_4103(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for CTN without authentication.
    """
    # CTN is not MAP
    return True


def hdl_wid_4800(_: WIDParams):
    """
    description: Please remove pairing from the Implementation Under Test (IUT), then click Ok to continue.
    """
    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


def hdl_wid_20000(_: WIDParams):
    """
    description: Please prepare IUT into a connectable mode in BR/EDR.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True


def hdl_wid_20115(_: WIDParams):
    """
    description: Please initiate an ACL disconnection to the PTS.
    Verify that the Implementation Under Test (IUT) can initiate ACL disconnect request to PTS.
    """
    # Disconnect all active connections
    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_CONNECT, default_mce_mas(), timeout=0):
        btp.map_mce_mas_disconnect(default_mce_mas())
        btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_DISCONNECT, default_mce_mas())

    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED, default_mce_mas(), timeout=0):
        btp.map_mce_mas_rfcomm_disconnect(default_mce_mas())
        btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_RFCOMM_DISCONNECT, default_mce_mas())

    if btp.map_wait_for_connection(defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED, default_mce_mas(), timeout=0):
        btp.map_mce_mas_l2cap_disconnect(default_mce_mas())
        btp.map_wait_for_disconnection(defs.BTP_MAP_CMD_MCE_MAS_L2CAP_DISCONNECT, default_mce_mas())

    return True
