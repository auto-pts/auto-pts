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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum

from dateutil.relativedelta import relativedelta

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import defs

MAP_FILLER_BYTE = '0'
MAP_MANDATORY_SUPPORTED_FEATURES = 0x1F
MAP_MCE_SUPPORTED_FEATURES = 0x0077FFFF
MAP_MSE_SUPPORTED_FEATURES = 0x007FFFFF


class MAPType:
    SEND_EVENT = "x-bt/MAP-event-report"
    SET_NTF_REG = "x-bt/MAP-NotificationRegistration"
    GET_FOLDER_LISTING = "x-obex/folder-listing"
    GET_MSG_LISTING = "x-bt/MAP-msg-listing"
    GET_MSG = "x-bt/message"
    SET_MSG_STATUS = "x-bt/messageStatus"
    PUSH_MSG = "x-bt/message"
    UPDATE_INBOX = "x-bt/MAP-messageUpdate"
    GET_MAS_INST_INFO = "x-bt/MASInstanceInformation"
    SET_OWNER_STATUS = "x-bt/ownerStatus"
    GET_OWNER_STATUS = "x-bt/ownerStatus"
    GET_CONVO_LISTING = "x-bt/MAP-convo-listing"
    SET_NTF_FILTER = "x-bt/MAP-notification-filter"


class MAPMsgType(IntEnum):
    """MAP Message Types"""
    SMS_GSM = 0x01
    SMS_CDMA = 0x02
    EMAIL = 0x04
    MMS = 0x08
    IM = 0x10


class MAPMsgStatusInd(IntEnum):
    """MAP Message Status Indicator"""
    READ_STATUS = 0x0
    DELETED_STATUS = 0x01
    SET_EXTENDED_DATA = 0x02


class MAPMsgStatus(IntEnum):
    """MAP Message Status"""
    READ = 0x01
    DELETED = 0x02
    SENT = 0x04
    PROTECTED = 0x08


class MAPPresenceAvailability(IntEnum):
    """Presence Availability Status"""
    UNKNOWN = 0x00
    OFFLINE = 0x01
    ONLINE = 0x02
    AWAY = 0x03
    DO_NOT_DISTURB = 0x04
    BUSY = 0x05
    IN_A_MEETING = 0x06


class MAPChatState(IntEnum):
    """Chat State"""
    UNKNOWN = 0x00
    INACTIVE = 0x01
    ACTIVE = 0x02
    COMPOSING = 0x03
    PAUSED = 0x04
    GONE = 0x05


class MAPEventType(IntEnum):
    """MAP Event Types"""
    NEW_MESSAGE = 1 << 0
    MESSAGE_DELETED = 1 << 1
    MESSAGE_SHIFT = 1 << 2
    SENDING_SUCCESS = 1 << 3
    SENDING_FAILURE = 1 << 4
    DELIVERY_SUCCESS = 1 << 5
    DELIVERY_FAILURE = 1 << 6
    MEMORY_FULL = 1 << 7
    MEMORY_AVAILABLE = 1 << 8
    READ_STATUS_CHANGED = 1 << 9
    CONVERSATION_CHANGED = 1 << 10
    PARTICIPANT_PRESENCE_CHANGED = 1 << 11
    PARTICIPANT_CHAT_STATE_CHANGED = 1 << 12
    MESSAGE_EXTENDED_DATA_CHANGED = 1 << 13
    MESSAGE_REMOVED = 1 << 14


class MAPSupportedFeatures(IntEnum):
    """MAP supported features"""
    NTF_REG_FEATURE = 1 << 0
    NTF_FEATURE = 1 << 1
    BROWSING_FEATURE = 1 << 2
    UPLOADING_FEATURE = 1 << 3
    DELETE_FEATURE = 1 << 4
    INST_INFO_FEATURE = 1 << 5
    EXT_EVENT_REPORT_1_1 = 1 << 6
    EXT_EVENT_VERSION_1_2 = 1 << 7
    MSG_FORMAT_VERSION_1_1 = 1 << 8
    MSG_LISTING_FORMAT_VERSION_1_1 = 1 << 9
    PERSISTENT_MSG_HANDLE = 1 << 10
    DATABASE_ID = 1 << 11
    FOLDER_VERSION_CNTR = 1 << 12
    CONVO_VERSION_CNTR = 1 << 13
    PARTICIPANT_PRESENCE_CHANGE_NTF = 1 << 14
    PARTICIPANT_CHAT_STATE_CHANGE_NTF = 1 << 15
    PBAP_CONTACT_CROSS_REF = 1 << 16
    NTF_FILTERING = 1 << 17
    UTC_OFFSET_TIMESTAMP_FORMAT = 1 << 18
    SUPPORTED_FEATURES_CONNECT_REQ = 1 << 19
    CONVO_LISTING = 1 << 20
    OWNER_STATUS = 1 << 21
    MSG_FORWARDING = 1 << 22


"""MAP MSE Message Storage and Retrieval System"""


@dataclass
class MAPMsg:
    """Represents a MAP message"""
    handle: str  # 16-digit hex string
    subject: str
    datetime: str  # YYYYMMDDTHHMMSS±HHMM format
    sender_name: str = ""
    sender_addressing: str = ""
    recipient_name: str = ""
    recipient_addressing: str = ""
    msg_type: MAPMsgType = MAPMsgType.SMS_GSM
    size: int = 0
    text: str = ""
    reception_status: str = "complete"
    attachment_size: int = 0
    priority: bool = False
    read: bool = False
    sent: bool = False
    protected: bool = False
    deleted: bool = False
    replyto_addressing: str = ""
    conversation_id: str = ""
    conversation_name: str = ""
    direction: str = "incoming"  # "incoming", "outgoing", "outgoingdraft" or "outgoingpending"
    attachment_mime_types: list[str] = field(default_factory=list)
    folder: str = "telecom/msg/inbox"
    extended_data: str = ""  # Extended data string (e.g., "0:54;" for 54 Facebook likes)

    def get_status(self) -> int:
        """Get message status flags"""
        status = 0
        if self.read:
            status |= MAPMsgStatus.READ
        if self.deleted:
            status |= MAPMsgStatus.DELETED
        if self.sent:
            status |= MAPMsgStatus.SENT
        if self.protected:
            status |= MAPMsgStatus.PROTECTED
        return status

    def to_bmessage(self, version: str = "1.1") -> str:
        """
        Convert message to bMessage format

        Args:
            version: bMessage version ("1.0" or "1.1")

        Returns:
            bMessage formatted string
        """
        bmsg = "BEGIN:BMSG\r\n"
        bmsg += f"VERSION:{version}\r\n"
        bmsg += f"STATUS:{'READ' if self.read else 'UNREAD'}\r\n"
        bmsg += f"TYPE:{self._get_type_string()}\r\n"
        bmsg += f"FOLDER:{self.folder.upper()}\r\n"
        if version == "1.1" and self.msg_type == MAPMsgType.IM:
            bmsg += f"EXTENDEDDATA:{self.extended_data}\r\n"

        # Originator
        bmsg += "BEGIN:VCARD\r\n"
        bmsg += "VERSION:2.1\r\n"
        bmsg += f"N:{self.sender_name}\r\n"
        if self.msg_type == MAPMsgType.EMAIL:
            bmsg += f"EMAIL:{self.sender_addressing}\r\n"
        elif self.msg_type == MAPMsgType.IM:
            bmsg += f"X-BT-UCI:{self.sender_addressing}\r\n"
        else:
            bmsg += f"TEL:{self.sender_addressing}\r\n"
        bmsg += "END:VCARD\r\n"

        # Envelope
        bmsg += "BEGIN:BENV\r\n"

        # Recipient
        bmsg += "BEGIN:VCARD\r\n"
        bmsg += "VERSION:2.1\r\n"
        bmsg += f"N:{self.recipient_name}\r\n"
        if self.msg_type == MAPMsgType.EMAIL:
            bmsg += f"EMAIL:{self.recipient_addressing}\r\n"
        elif self.msg_type == MAPMsgType.IM:
            bmsg += f"X-BT-UCI:{self.recipient_addressing}\r\n"
        else:
            bmsg += f"TEL:{self.recipient_addressing}\r\n"
        bmsg += "END:VCARD\r\n"

        # Body
        bmsg += "BEGIN:BBODY\r\n"
        bmsg += "CHARSET:UTF-8\r\n"
        bmsg += "LANGUAGE:UNKNOWN\r\n"
        bmsg += f"LENGTH:{len(self.text.encode('utf-8')) + 22}\r\n"
        bmsg += "BEGIN:MSG\r\n"
        bmsg += self.text + "\r\n"
        bmsg += "END:MSG\r\n"
        bmsg += "END:BBODY\r\n"

        bmsg += "END:BENV\r\n"
        bmsg += "END:BMSG\r\n"

        return bmsg

    def _get_type_string(self) -> str:
        """Get message type string"""
        type_map = {
            MAPMsgType.EMAIL: "EMAIL",
            MAPMsgType.SMS_GSM: "SMS_GSM",
            MAPMsgType.SMS_CDMA: "SMS_CDMA",
            MAPMsgType.MMS: "MMS",
            MAPMsgType.IM: "IM"
        }
        return type_map.get(self.msg_type, "SMS_GSM")


@dataclass
class MAPParticipant:
    """Represents a participant in a MAP conversation"""
    uci: str  # Unique Contact Identifier
    display_name: str = ""
    chat_state: int = MAPChatState.INACTIVE
    last_activity: str = ""
    name: str = ""
    presence_availability: int = MAPPresenceAvailability.UNKNOWN
    presence_text: str = ""
    priority: int = 0


@dataclass
class MAPConversation:
    """Represents a MAP conversation"""
    id: str  # 16-digit hex string
    name: str
    last_activity: str  # YYYYMMDDTHHMMSS±HHMM format
    read_status: str = "unread"  # "read" or "unread"
    version_counter: str = "00000000000000000000000000000000"  # 32-digit hex (128-bit)
    summary: str = ""
    participants: list[MAPParticipant] = field(default_factory=list)


@dataclass
class MAPOwnerStatus:
    """Represents owner status for a conversation"""
    conversation_id: str = ""  # Empty string means applies to all conversations
    presence_availability: int = MAPPresenceAvailability.ONLINE
    presence_text: str = ""
    last_activity: str = ""
    chat_state: int = MAPChatState.INACTIVE


@dataclass
class MAPFolder:
    """Represents a MAP folder"""
    name: str
    parent: str | None = None
    subfolders: list[str] = field(default_factory=list)


@dataclass
class MAPEvent:
    """Represents a MAP event notification"""
    event_type: MAPEventType
    handle: str = ""
    folder: str = ""
    old_folder: str = ""
    msg_type: MAPMsgType = ""
    datetime: str = ""
    subject: str = ""
    sender_name: str = ""
    priority: str = ""
    conversation_id: str = ""
    conversation_name: str = ""
    presence_availability: int = None
    presence_text: str = ""
    last_activity: str = ""
    chat_state: int = None
    read_status: str = ""
    participant_uci: str = ""
    extended_data: str = ""
    contact_uid: str = ""

    def to_xml(self, version: str = "1.0", utc_offset: bool = True) -> str:
        """
        Convert event to XML format

        Args:
            version: MAP event report version ("1.0", "1.1", or "1.2")
            utc_offset: If True, include UTC offset in datetime format (±HHMM)

        Returns:
            XML event report string
        """
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\r\n'
        xml += f'<MAP-event-report version="{version}">\r\n'
        xml += f'  <event type="{self._get_event_type_string()}"'

        # Version 1.0 attributes (always included)
        if self.handle:
            xml += f' handle="{self.handle}"'
        if self.folder:
            xml += f' folder="{self._xml_escape(self.folder)}"'
        if self.old_folder:
            xml += f' old_folder="{self._xml_escape(self.old_folder)}"'
        if self.msg_type:
            xml += f' msg_type="{self._get_msg_type_string()}"'

        # Version 1.1 attributes (included in v1.1 and v1.2)
        if version in ["1.1", "1.2"]:
            if self.datetime:
                datetime_str = self.datetime if utc_offset else self.datetime[:-5]
                xml += f' datetime="{datetime_str}"'
            if self.subject:
                xml += f' subject="{self._xml_escape(self.subject)}"'
            if self.sender_name:
                xml += f' sender_name="{self._xml_escape(self.sender_name)}"'
            if self.priority:
                xml += f' priority="{self.priority}"'

        # Version 1.2 attributes (only included in v1.2)
        if version == "1.2":
            if self.conversation_name:
                xml += f' conversation_name="{self._xml_escape(self.conversation_name)}"'
            if self.conversation_id:
                xml += f' conversation_id="{self.conversation_id}"'
            if self.presence_availability:
                xml += f' presence_availability="{self.presence_availability}"'
            if self.presence_text:
                xml += f' presence_text="{self._xml_escape(self.presence_text)}"'
            if self.last_activity:
                last_activity_str = self.last_activity if utc_offset else self.last_activity[:-5]
                xml += f' last_activity="{last_activity_str}"'
            if self.chat_state:
                xml += f' chat_state="{self.chat_state}"'
            if self.read_status:
                xml += f' read_status="{self.read_status}"'
            if self.extended_data:
                xml += f' extended_data="{self._xml_escape(self.extended_data)}"'
            if self.participant_uci:
                xml += f' participant_uci="{self._xml_escape(self.participant_uci)}"'
            if self.contact_uid:
                xml += f' contact_uid="{self.contact_uid}"'

        xml += '/>\r\n'
        xml += '</MAP-event-report>'
        return xml

    def _get_event_type_string(self) -> str:
        """Get event type string"""
        event_map = {
            MAPEventType.NEW_MESSAGE: "NewMessage",
            MAPEventType.DELIVERY_SUCCESS: "DeliverySuccess",
            MAPEventType.SENDING_SUCCESS: "SendingSuccess",
            MAPEventType.DELIVERY_FAILURE: "DeliveryFailure",
            MAPEventType.SENDING_FAILURE: "SendingFailure",
            MAPEventType.MEMORY_FULL: "MemoryFull",
            MAPEventType.MEMORY_AVAILABLE: "MemoryAvailable",
            MAPEventType.MESSAGE_DELETED: "MessageDeleted",
            MAPEventType.MESSAGE_SHIFT: "MessageShift",
            MAPEventType.READ_STATUS_CHANGED: "ReadStatusChanged",
            MAPEventType.CONVERSATION_CHANGED: "ConversationChanged",
            MAPEventType.PARTICIPANT_PRESENCE_CHANGED: "ParticipantPresenceChanged",
            MAPEventType.PARTICIPANT_CHAT_STATE_CHANGED: "ParticipantChatStateChanged",
            MAPEventType.MESSAGE_EXTENDED_DATA_CHANGED: "MessageExtendedDataChanged",
            MAPEventType.MESSAGE_REMOVED: "MessageRemoved",
        }
        return event_map.get(self.event_type, "NewMessage")

    def _get_msg_type_string(self) -> str:
        """Get message type string"""
        type_map = {
            MAPMsgType.EMAIL: "EMAIL",
            MAPMsgType.SMS_GSM: "SMS_GSM",
            MAPMsgType.SMS_CDMA: "SMS_CDMA",
            MAPMsgType.MMS: "MMS",
            MAPMsgType.IM: "IM"
        }
        return type_map.get(self.msg_type, "SMS_GSM")

    def _xml_escape(self, text: str) -> str:
        """Escape XML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))


class MAPMsgStorage:
    """MAP MSE Message Storage System"""

    def __init__(self, storage_path: str = "./tmp/map_storage"):
        """
        Initialize MAP message storage

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = storage_path
        self.messages: dict[str, MAPMsg] = {}
        self.conversations: dict[str, MAPConversation] = {}
        self.owner_status: dict[str, MAPOwnerStatus] = {}
        self.folders: dict[str, MAPFolder] = {}
        self.current_folder = ""
        self._message_counter = 1
        self._conversation_counter = 1

        # Database Identifier - 128-bit UUID represented as 32 hex chars
        # Changes ONLY when version counters roll over (2^128-1 -> 0)
        self.database_identifier = self._generate_database_identifier()

        # Folder Version Counters - track changes to folder contents
        # Key: folder_path, Value: 32-digit hex counter (128-bit)
        self.folder_version_counters: dict[str, str] = {}

        # Conversation-Listing Version Counter - tracks changes to conversation list
        # 32-digit hex counter (128-bit)
        self.conversation_listing_version_counter = "00000000000000000000000000000000"

        # Initialize default folder structure
        self._init_default_folders()

        # Load existing data if available
        self._load_storage()

    def _generate_database_identifier(self) -> str:
        """
        Generate a new Database Identifier (128-bit UUID as 32 hex chars)

        Returns:
            32-character hex string representing 128-bit UUID
        """
        import uuid
        return uuid.uuid4().hex.upper()

    def _increment_folder_version_counter(self, folder: str):
        """
        Increment folder version counter (128-bit)
        Updates database identifier if counter rolls over (2^128-1 -> 0)

        Args:
            folder: Folder path
        """
        if folder not in self.folder_version_counters:
            self.folder_version_counters[folder] = "00000000000000000000000000000000"

        # Convert to integer, increment, and mask to 128 bits
        current = int(self.folder_version_counters[folder], 16)
        max_value = (1 << 128) - 1  # 2^128 - 1
        new_value = (current + 1) & max_value

        # Check for roll over (2^128-1 -> 0)
        if current == max_value and new_value == 0:
            old_db_id = self.database_identifier
            self.database_identifier = self._generate_database_identifier()
            logging.info(f"Folder version counter rolled over for {folder}, "
                        f"updated database identifier: {old_db_id} -> {self.database_identifier}")

        self.folder_version_counters[folder] = f"{new_value:032X}"
        logging.debug(f"Incremented folder version counter for {folder}: {self.folder_version_counters[folder]}")

    def _increment_conversation_listing_version_counter(self):
        """
        Increment conversation-listing version counter (128-bit)
        Updates database identifier if counter rolls over (2^128-1 -> 0)
        """
        # Convert to integer, increment, and mask to 128 bits
        current = int(self.conversation_listing_version_counter, 16)
        max_value = (1 << 128) - 1  # 2^128 - 1
        new_value = (current + 1) & max_value

        # Check for roll over (2^128-1 -> 0)
        if current == max_value and new_value == 0:
            old_db_id = self.database_identifier
            self.database_identifier = self._generate_database_identifier()
            logging.info(f"Conversation-listing version counter rolled over, "
                        f"updated database identifier: {old_db_id} -> {self.database_identifier}")

        self.conversation_listing_version_counter = f"{new_value:032X}"
        logging.debug(f"Incremented conversation-listing version counter: {self.conversation_listing_version_counter}")

    def _increment_conversation_version_counter(self, conversation_id: str):
        """
        Increment conversation version counter (128-bit)
        Updates database identifier if counter rolls over (2^128-1 -> 0)

        Args:
            conversation_id: Conversation ID
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            logging.error(f"Conversation not found: {conversation_id}")
            return

        # Convert to integer, increment, and mask to 128 bits
        current = int(conversation.version_counter, 16)
        max_value = (1 << 128) - 1  # 2^128 - 1
        new_value = (current + 1) & max_value

        # Check for roll over (2^128-1 -> 0)
        if current == max_value and new_value == 0:
            old_db_id = self.database_identifier
            self.database_identifier = self._generate_database_identifier()
            logging.info(f"Conversation version counter rolled over for {conversation_id}, "
                        f"updated database identifier: {old_db_id} -> {self.database_identifier}")

        conversation.version_counter = f"{new_value:032X}"
        logging.debug(f"Incremented conversation version counter for {conversation_id}: {conversation.version_counter}")

    def get_database_identifier(self) -> str:
        """
        Get current database identifier

        Returns:
            32-character hex string (128-bit)
        """
        return self.database_identifier

    def get_folder_version_counter(self, folder: str) -> str:
        """
        Get folder version counter

        Args:
            folder: Folder path

        Returns:
            32-character hex string (128-bit)
        """
        return self.folder_version_counters.get(folder, "00000000000000000000000000000000")

    def get_conversation_listing_version_counter(self) -> str:
        """
        Get conversation-listing version counter

        Returns:
            32-character hex string (128-bit)
        """
        return self.conversation_listing_version_counter

    def _init_default_folders(self):
        """Initialize default MAP folder structure according to MAP specification"""
        default_folders = [
            ("telecom", None),
            ("telecom/msg", "telecom"),
            ("telecom/msg/inbox", "telecom/msg"),
            ("telecom/msg/outbox", "telecom/msg"),
            ("telecom/msg/sent", "telecom/msg"),
            ("telecom/msg/deleted", "telecom/msg"),
            ("telecom/msg/draft", "telecom/msg"),
        ]

        for folder_name, parent in default_folders:
            self.folders[folder_name] = MAPFolder(name=folder_name, parent=parent)
            if parent and parent in self.folders:
                if folder_name not in self.folders[parent].subfolders:
                    self.folders[parent].subfolders.append(folder_name)

            # Initialize folder version counter (128-bit, 32 hex chars)
            self.folder_version_counters[folder_name] = "00000000000000000000000000000000"

    def is_valid_folder_name(self, folder_name: str) -> bool:
        """
        Check if a folder name is valid (no path, just name)

        Args:
            folder_name: Folder name to validate

        Returns:
            True if folder name is valid, False otherwise
        """
        if not folder_name:
            return False

        # Check for invalid characters
        invalid_chars = ['/', '\\', '\0', '<', '>', ':', '"', '|', '?', '*']
        if any(char in folder_name for char in invalid_chars):
            return False

        # Check if folder exists as subfolder of current folder
        if self.current_folder:
            full_path = f"{self.current_folder}/{folder_name}"
            return full_path in self.folders

        return folder_name in self.folders

    def _load_storage(self):
        """Load storage from disk"""

    def _save_storage(self):
        """Save storage to disk"""

    def push_message(self, bmessage: str | bytes, folder: str = "",
                    transparent: bool = False, retry: bool = False,
                    charset: int = 1, conversation_id: str = "",
                    message_handle: str = "", attachment: int = None,
                    modify_text: int = None) -> tuple[str, bool]:
        """
        Push a message to the MSE (handle PushMessage request)

        Args:
            bmessage: bMessage object content
            folder: Target folder (empty for current folder)
            transparent: Transparent mode flag
            retry: Retry flag
            charset: Character set (1=UTF-8)
            conversation_id: Conversation ID for IM messages (16-digit hex string)
            message_handle: Message handle for forward/modify operations (16-digit hex string)
            attachment: Attachment handling (0=OFF, 1=ON) - for email forwarding
            modify_text: Text modification (0=REPLACE, 1=PREPEND) - for email forwarding

        Returns:
            Tuple of (message_handle, success)
        """
        try:
            # Check if this is a forward/modify operation
            is_forward = bool(message_handle)

            if is_forward:
                # Forward/modify existing message
                original_msg = self.messages.get(message_handle)
                if not original_msg:
                    logging.error(f"Original message not found: {message_handle}")
                    return ("", False)

                # Parse new bMessage content
                new_msg = self._parse_bmessage(bmessage)
                if new_msg is None:
                    logging.error("Failed to parse bMessage")
                    return ("", False)

                # Create forwarded message based on original
                msg = MAPMsg(
                    handle="",  # Will be auto-generated
                    subject=new_msg.subject if new_msg.subject else original_msg.subject,
                    datetime="",  # Will be set below
                    sender_name=new_msg.sender_name,
                    sender_addressing=new_msg.sender_addressing,
                    recipient_name=new_msg.recipient_name,
                    recipient_addressing=new_msg.recipient_addressing,
                    msg_type=original_msg.msg_type,
                    text="",  # Will be set based on modify_text
                    priority=original_msg.priority,
                    folder="",  # Will be set below
                    conversation_id=original_msg.conversation_id,
                    conversation_name=original_msg.conversation_name,
                )

                # Handle text modification
                if modify_text == 0:  # REPLACE
                    msg.text = new_msg.text
                elif modify_text == 1:  # PREPEND
                    msg.text = new_msg.text + "\r\n" + original_msg.text
                else:
                    msg.text = new_msg.text

                # Handle attachment
                if attachment == 1:  # ON - include original attachments
                    msg.attachment_size = original_msg.attachment_size
                    msg.attachment_mime_types = original_msg.attachment_mime_types.copy()
                elif attachment == 0:  # OFF - no attachments
                    msg.attachment_size = 0
                    msg.attachment_mime_types = []
                else:
                    # Default: preserve original attachment info
                    msg.attachment_size = original_msg.attachment_size
                    msg.attachment_mime_types = original_msg.attachment_mime_types.copy()

            else:
                # Normal push message (not forward)
                msg = self._parse_bmessage(bmessage)
                if msg is None:
                    logging.error("Failed to parse bMessage")
                    return ("", False)

                # Set conversation ID if provided (for IM messages)
                if conversation_id:
                    # Get conversation name if conversation exists
                    conv = self.conversations.get(conversation_id)
                    if conv:
                        msg.conversation_id = conversation_id
                        msg.conversation_name = conv.name
                    else:
                        logging.warning(f"Conversation not found: {conversation_id}")

            # Determine target folder
            if folder:
                target_folder = folder if self.current_folder == "" else f"{self.current_folder}/{folder}"
            else:
                target_folder = self.current_folder

            if target_folder not in self.folders:
                logging.error(f"Invalid folder: {target_folder}")
                return ("", False)

            # Determine direction based on folder
            if "outbox" in target_folder or "sent" in target_folder:
                msg.direction = "outgoing"
                target_folder = "telecom/msg/sent"
                msg.sent = True
            else:
                msg.direction = "incoming"

            # Set message folder
            msg.folder = target_folder

            # Generate persistent message handle
            msg.handle = f"{self._message_counter:016X}"
            self._message_counter += 1

            # Set message properties
            msg.datetime = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
            msg.size = len(msg.text)

            # Store message if not transparent
            if not transparent:
                self.messages[msg.handle] = msg

                # Increment folder version counter (may trigger DB ID update on rollover)
                self._increment_folder_version_counter(target_folder)

                # If message is added to a conversation, increment conversation version counter
                if msg.conversation_id:
                    self._increment_conversation_version_counter(msg.conversation_id)
                    logging.debug(f"Message added to conversation {msg.conversation_id}, incremented version counter")

                self._save_storage()

            operation = "Forwarded" if is_forward else "Pushed"
            logging.info(f"{operation} message {msg.handle} to folder {target_folder}")
            if is_forward:
                logging.debug(f"  Original: {message_handle}, Attachment: {attachment}, ModifyText: {modify_text}")
            if conversation_id:
                logging.debug(f"  ConversationID: {conversation_id}")

            return (msg.handle, True)

        except Exception as e:
            logging.error(f"Error pushing message: {e}")
            return ("", False)

    def _parse_bmessage(self, bmessage: str | bytes) -> MAPMsg | None:
        """
        Parse bMessage format to Message object (supports v1.0 and v1.1)

        Args:
            bmessage: bMessage content

        Returns:
            Message object or None
        """
        try:
            msg = MAPMsg(
                handle="",
                subject="",
                datetime="",
                sender_name="",
                sender_addressing=""
            )

            if isinstance(bmessage, bytes):
                bmessage = bmessage.decode('utf-8')

            lines = bmessage.split('\r\n')
            in_vcard = False
            in_body = False
            vcard_count = 0
            body_text = []
            bmessage_version = "1.0"
            current_vcard_version = "2.1"

            for line in lines:
                line = line.strip()

                if line == "BEGIN:VCARD":
                    in_vcard = True
                    vcard_count += 1
                    continue
                elif line == "END:VCARD":
                    in_vcard = False
                    continue
                elif line == "BEGIN:MSG":
                    in_body = True
                    continue
                elif line == "END:MSG":
                    in_body = False
                    suffix_newline = 1 if body_text and body_text[-1] == '' else 0
                    msg.text = '\r\n'.join(body_text) + '\r\n' * suffix_newline
                    continue

                if in_body:
                    body_text.append(line)
                    continue

                if in_vcard:
                    if line.startswith("VERSION:"):
                        current_vcard_version = line[8:]
                    elif line.startswith("N:"):
                        name = line[2:]
                        if vcard_count == 1:
                            msg.sender_name = name
                        elif vcard_count == 2:
                            msg.recipient_name = name
                    elif line.startswith("TEL:"):
                        tel = line[4:]
                        if vcard_count == 1:
                            msg.sender_addressing = tel
                        elif vcard_count == 2:
                            msg.recipient_addressing = tel
                    elif line.startswith("EMAIL:"):
                        email = line[6:]
                        if vcard_count == 1:
                            msg.sender_addressing = email
                        elif vcard_count == 2:
                            msg.recipient_addressing = email
                    elif line.startswith("X-BT-UCI:") or line.startswith("X-BT-UID:"):
                        uci = line[9:]
                        if vcard_count == 1:
                            msg.sender_addressing = uci
                        elif vcard_count == 2:
                            msg.recipient_addressing = uci
                else:
                    if line.startswith("VERSION:"):
                        bmessage_version = line[8:]
                    elif line.startswith("STATUS:"):
                        status = line[7:]
                        msg.read = (status == "READ")
                    elif line.startswith("TYPE:"):
                        type_str = line[5:]
                        type_map = {
                            "EMAIL": MAPMsgType.EMAIL,
                            "SMS_GSM": MAPMsgType.SMS_GSM,
                            "SMS_CDMA": MAPMsgType.SMS_CDMA,
                            "MMS": MAPMsgType.MMS,
                            "IM": MAPMsgType.IM
                        }
                        msg.msg_type = type_map.get(type_str, MAPMsgType.SMS_GSM)
                    elif line.startswith("FOLDER:"):
                        msg.folder = line[7:].lower()

            # Set default subject if not provided
            if not msg.subject:
                msg.subject = msg.text[:50] if len(msg.text) > 50 else msg.text

            # Determine direction based on folder
            if "sent" in msg.folder or "outbox" in msg.folder:
                msg.direction = "outgoing"
                msg.sent = True
            elif "draft" in msg.folder:
                msg.direction = "outgoingdraft"
            else:
                msg.direction = "incoming"

            return msg

        except Exception as e:
            logging.error(f"Error parsing bMessage: {e}")
            return None

    def set_message_status(self, handle: str, status_indicator: int,
                          status_value: int = None, extended_data: str = None) -> bool:
        """
        Set message status (handle SetMessageStatus request)

        Args:
            handle: Message handle (persistent)
            status_indicator: Status indicator (0=read, 1=deleted, 2=extended_data)
            status_value: Status value (0=no, 1=yes) - used for read/deleted status
            extended_data: Extended data string - used for extended_data status

        Returns:
            True if successful
        """
        message = self.messages.get(handle)
        if not message:
            logging.error(f"Message not found: {handle}")
            return False

        old_read = message.read
        old_deleted = message.deleted
        old_folder = message.folder
        old_extended_data = message.extended_data

        if status_indicator == MAPMsgStatusInd.READ_STATUS:  # Read status
            if status_value is None:
                logging.error("status_value is required for READ_STATUS")
                return False

            message.read = (status_value == 1)

        elif status_indicator == MAPMsgStatusInd.DELETED_STATUS:  # Deleted status
            if status_value is None:
                logging.error("status_value is required for DELETED_STATUS")
                return False

            message.deleted = (status_value == 1)

            # Move to deleted folder if deleted
            if message.deleted and not old_deleted:
                new_folder = "telecom/msg/deleted"
                message.folder = new_folder

                # Increment folder version counters (may trigger DB ID update on rollover)
                self._increment_folder_version_counter(old_folder)
                self._increment_folder_version_counter(new_folder)

        elif status_indicator == MAPMsgStatusInd.SET_EXTENDED_DATA:  # Extended data
            if extended_data is None:
                logging.error("extended_data is required for SET_EXTENDED_DATA")
                return False

            message.extended_data = extended_data
        else:
            logging.error(f"Invalid status_indicator: {status_indicator}")
            return False

        self._save_storage()
        logging.info(f"Set message {handle} status: indicator={status_indicator}, "
                    f"value={status_value}, extended_data={extended_data}")
        return True

    def set_owner_status(self, conversation_id: str = "", presence_availability: int = None,
                        presence_text: str = None, last_activity: str = None,
                        chat_state: int = None) -> bool:
        """
        Set owner status for a conversation (handle SetOwnerStatus request)

        Args:
            conversation_id: Conversation ID (empty string means applies to all conversations)
            presence_availability: Presence availability status
            presence_text: Presence text
            last_activity: Last activity timestamp
            chat_state: Chat state

        Returns:
            True if successful
        """
        # Use empty string as key for global owner status
        key = conversation_id if conversation_id else ""

        # Get or create owner status
        if key not in self.owner_status:
            self.owner_status[key] = MAPOwnerStatus(conversation_id=key)

        status = self.owner_status[key]

        # Update fields
        if presence_availability is not None:
            status.presence_availability = presence_availability
        if presence_text is not None:
            status.presence_text = presence_text
        if last_activity is not None:
            status.last_activity = last_activity
        else:
            status.last_activity = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
        if chat_state is not None:
            status.chat_state = chat_state

        self._save_storage()

        if conversation_id:
            logging.info(f"Set owner status for conversation {conversation_id}")
        else:
            logging.info("Set global owner status (applies to all conversations)")

        return True

    def get_owner_status(self, conversation_id: str = "") -> MAPOwnerStatus | None:
        """
        Get owner status for a conversation

        Args:
            conversation_id: Conversation ID (empty string gets global owner status)

        Returns:
            OwnerStatus instance (returns default if not exists)
        """
        key = conversation_id if conversation_id else ""

        status = self.owner_status.get(key, None)

        if conversation_id:
            logging.debug(f"Retrieved owner status for conversation {conversation_id}: "
                         f"availability={status.presence_availability}, chat_state={status.chat_state}")
        else:
            logging.debug(f"Retrieved global owner status: "
                         f"availability={status.presence_availability}, chat_state={status.chat_state}")

        return status

    def build_folder_listing(self, max_list_count: int = 1024,
                           list_start_offset: int = 0) -> bytes:
        """
        Build folder listing XML

        Args:
            max_list_count: Maximum number of folders to return
            list_start_offset: Offset to start listing from

        Returns:
            XML folder listing as bytes
        """
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\r\n'
        xml += '<folder-listing version="1.0">\r\n'

        # Get subfolders of current folder
        current = self.folders.get(self.current_folder)
        if current:
            subfolders = current.subfolders[list_start_offset:list_start_offset + max_list_count]
            for subfolder_path in subfolders:
                folder = self.folders.get(subfolder_path)
                if folder:
                    folder_name = folder.name.split('/')[-1]
                    xml += f'  <folder name="{folder_name}"/>\r\n'

        xml += '</folder-listing>\r\n'

        logging.debug(f"Built folder listing: {len(xml)} bytes")
        return xml.encode('utf-8')

    def build_message_listing(self, folder: str = "",
                            max_list_count: int = 1024,
                            list_start_offset: int = 0,
                            subject_length: int = 255,
                            filter_message_type: int = 0,
                            filter_period_begin: str = "",
                            filter_period_end: str = "",
                            filter_read_status: int = 0,
                            filter_recipient: str = "",
                            filter_originator: str = "",
                            filter_priority: int = 0,
                            filter_message_handle: str = "",
                            conversation_id: str = "",
                            parameter_mask: int = 0xFFFFFFFF,
                            version: str = "1.1",
                            utc_offset: bool = True) -> tuple[int, bytes]:
        """
        Build message listing XML

        Args:
            folder: Folder path (empty for current folder)
            max_list_count: Maximum number of messages to return
            list_start_offset: Offset to start listing from
            subject_length: Maximum subject length
            filter_message_type: Message type filter
            filter_period_begin: Start date filter (YYYYMMDDTHHMMSS±HHMM)
            filter_period_end: End date filter (YYYYMMDDTHHMMSS±HHMM)
            filter_read_status: Read status filter (0=no filter, 1=unread, 2=read)
            filter_recipient: Recipient filter
            filter_originator: Originator filter
            filter_priority: Priority filter (0=no filter, 1=high, 2=non-high)
            filter_message_handle: Message handle filter (16-digit hex string)
            conversation_id: Conversation ID filter (16-digit hex string)
            parameter_mask: Parameter mask for included fields
            version: Message listing version ("1.0" or "1.1")
            utc_offset: If True, include UTC offset in datetime format (±HHMM)

        Returns:
            Tuple of (listing_size, XML message listing as bytes)
        """
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\r\n'
        xml += f'<MAP-msg-listing version="{version}">\r\n'

        # Determine target folder
        if folder:
            target_folder = folder if self.current_folder == "" else f"{self.current_folder}/{folder}"
        else:
            target_folder = self.current_folder

        # Filter messages
        filtered_messages = []
        for handle, msg in self.messages.items():
            # Filter by folder
            if msg.folder != target_folder:
                continue

            # Skip deleted messages unless in deleted folder
            if msg.deleted and "deleted" not in target_folder:
                continue

            # Apply filters
            if filter_message_type != 0:
                if not (int(msg.msg_type) & filter_message_type):
                    continue

            if filter_read_status == 1 and msg.read:
                continue
            if filter_read_status == 2 and not msg.read:
                continue

            if filter_period_begin and msg.datetime < filter_period_begin:
                continue
            if filter_period_end and msg.datetime > filter_period_end:
                continue

            if filter_recipient and filter_recipient.lower() not in msg.recipient_addressing.lower() \
                and filter_recipient.lower() not in msg.recipient_name.lower():
                continue
            if filter_originator and filter_originator.lower() not in msg.sender_addressing.lower() \
                and filter_originator.lower() not in msg.sender_name.lower():
                continue

            if filter_priority == 1 and not msg.priority:
                continue
            if filter_priority == 2 and msg.priority:
                continue

            if filter_message_handle and handle != filter_message_handle:
                continue

            if conversation_id and msg.conversation_id != conversation_id:
                continue

            filtered_messages.append((handle, msg))

        # Sort by datetime (newest first)
        filtered_messages.sort(key=lambda x: x[1].datetime, reverse=True)

        # Apply pagination
        paginated_messages = filtered_messages[list_start_offset:list_start_offset + max_list_count]

        # Build XML for each message
        for handle, msg in paginated_messages:
            xml += f'  <msg handle="{handle}"'

            # Version 1.0 parameters (bits 0-13)
            if parameter_mask & 0x00000001:  # Subject
                subject = msg.subject[:subject_length] if len(msg.subject) > subject_length else msg.subject
                xml += f' subject="{self._xml_escape(subject)}"'

            if parameter_mask & 0x00000002:  # Datetime
                datetime_str = msg.datetime if utc_offset else msg.datetime[:-5]
                xml += f' datetime="{datetime_str}"'

            if parameter_mask & 0x00000004:  # Sender name
                xml += f' sender_name="{self._xml_escape(msg.sender_name)}"'

            if parameter_mask & 0x00000008:  # Sender addressing
                xml += f' sender_addressing="{self._xml_escape(msg.sender_addressing)}"'

            if parameter_mask & 0x00000010:  # Recipient name
                if msg.recipient_name:
                    xml += f' recipient_name="{self._xml_escape(msg.recipient_name)}"'

            if parameter_mask & 0x00000020:  # Recipient addressing
                if msg.recipient_addressing:
                    xml += f' recipient_addressing="{self._xml_escape(msg.recipient_addressing)}"'

            if parameter_mask & 0x00000040:  # Type
                xml += f' type="{msg._get_type_string()}"'

            if parameter_mask & 0x00000080:  # Size
                xml += f' size="{msg.size if msg.size > 0 else len(msg.text)}"'

            if parameter_mask & 0x00000100:  # Reception status
                xml += f' reception_status="{msg.reception_status}"'

            if parameter_mask & 0x00000200:  # Attachment size
                xml += f' attachment_size="{msg.attachment_size}"'

            if parameter_mask & 0x00000400:  # Priority
                xml += f' priority="{"yes" if msg.priority else "no"}"'

            if parameter_mask & 0x00000800:  # Read
                xml += f' read="{"yes" if msg.read else "no"}"'

            if parameter_mask & 0x00001000:  # Sent
                xml += f' sent="{"yes" if msg.sent else "no"}"'

            if parameter_mask & 0x00002000:  # Protected
                xml += f' protected="{"yes" if msg.protected else "no"}"'

            if parameter_mask & 0x00004000:  # Replyto addressing
                if msg.replyto_addressing:
                    xml += f' replyto_addressing="{self._xml_escape(msg.replyto_addressing)}"'

            # Version 1.1 parameters (bits 14-18)
            if version == "1.1":
                if parameter_mask & 0x00008000:  # Delivery status
                    # For sent messages, show delivery status
                    if msg.sent:
                        xml += ' delivery_status="delivered"'

                if parameter_mask & 0x00010000:  # Conversation ID
                    if msg.conversation_id:
                        xml += f' conversation_id="{msg.conversation_id}"'

                if parameter_mask & 0x00020000:  # Conversation name
                    if msg.conversation_name:
                        xml += f' conversation_name="{self._xml_escape(msg.conversation_name)}"'

                if parameter_mask & 0x00040000:  # Direction
                    xml += f' direction="{msg.direction}"'

                if parameter_mask & 0x00080000:  # Attachment MIME types
                    if msg.attachment_mime_types:
                        mime_types = ";".join(msg.attachment_mime_types)
                        xml += f' attachment_mime_types="{self._xml_escape(mime_types)}"'

            xml += '/>\r\n'

        xml += '</MAP-msg-listing>'

        logging.debug(f"Built message listing v{version}: {len(paginated_messages)} messages, {len(xml)} bytes")
        return len(filtered_messages), xml.encode('utf-8')

    def build_conversation_listing(self, max_list_count: int = 1024,
                                  list_start_offset: int = 0,
                                  filter_read_status: int = 0,
                                  filter_recipient: str = "",
                                  filter_last_activity_begin: str = "",
                                  filter_last_activity_end: str = "",
                                  conversation_id: str = "",
                                  conv_parameter_mask: int = 0xFFFFFFFF,
                                  utc_offset: bool = True) -> tuple[int, bytes]:
        """
        Build conversation listing XML

        Args:
            max_list_count: Maximum number of conversations to return
            list_start_offset: Offset to start listing from
            filter_read_status: Read status filter (0=no filter, 1=unread, 2=read)
            filter_recipient: Recipient filter
            filter_last_activity_begin: Start date filter
            filter_last_activity_end: End date filter
            conversation_id: Conversation ID filter (16-digit hex string)
            conv_parameter_mask: Parameter mask for included fields
            utc_offset: If True, include UTC offset in datetime format (±HHMM)

        Returns:
            Tuple of (listing_size, XML conversation listing as bytes)
        """
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\r\n'
        xml += '<MAP-convo-listing version="1.0">\r\n'

        # Filter conversations
        filtered_convos = []
        for conv_id, conv in self.conversations.items():
            if conversation_id and conv_id != conversation_id:
                continue

            if filter_read_status == 1 and conv.read_status == "read":
                continue
            if filter_read_status == 2 and conv.read_status == "unread":
                continue

            if filter_last_activity_begin and conv.last_activity < filter_last_activity_begin:
                continue
            if filter_last_activity_end and conv.last_activity > filter_last_activity_end:
                continue

            if filter_recipient:
                found = False
                for participant in conv.participants:
                    if filter_recipient.lower() in participant.uci.lower():
                        found = True
                        break
                if not found:
                    continue

            filtered_convos.append((conv_id, conv))

        # Sort by last activity (newest first)
        filtered_convos.sort(key=lambda x: x[1].last_activity, reverse=True)

        # Apply pagination
        paginated_convos = filtered_convos[list_start_offset:list_start_offset + max_list_count]

        # Build XML for each conversation
        for conv_id, conv in paginated_convos:
            xml += f'  <conversation id="{conv_id}"'

            if conv_parameter_mask & 0x00000001:  # Name
                xml += f' name="{self._xml_escape(conv.name)}"'

            if conv_parameter_mask & 0x00000002:  # Last activity
                last_activity_str = conv.last_activity if utc_offset else conv.last_activity[:-5]
                xml += f' last_activity="{last_activity_str}"'

            if conv_parameter_mask & 0x00000004:  # Read status
                xml += f' read_status="{conv.read_status}"'

            if conv_parameter_mask & 0x00000008:  # Version counter
                xml += f' version_counter="{conv.version_counter}"'

            if conv_parameter_mask & 0x00000010:  # Summary
                if conv.summary:
                    xml += f' summary="{self._xml_escape(conv.summary)}"'

            xml += '>\r\n'

            # Add participants
            for participant in conv.participants:
                xml += '    <participant'
                xml += f' uci="{self._xml_escape(participant.uci)}"'

                if participant.display_name:
                    xml += f' display_name="{self._xml_escape(participant.display_name)}"'

                if participant.chat_state:
                    xml += f' chat_state="{participant.chat_state}"'

                if participant.last_activity:
                    last_activity_str = participant.last_activity if utc_offset else participant.last_activity[:-5]
                    xml += f' last_activity="{last_activity_str}"'

                if participant.name:
                    xml += f' name="{self._xml_escape(participant.name)}"'

                if participant.presence_availability:
                    xml += f' presence_availability="{participant.presence_availability}"'

                if participant.presence_text:
                    xml += f' presence_text="{self._xml_escape(participant.presence_text)}"'

                if participant.priority:
                    xml += f' priority="{participant.priority}"'

                xml += '/>\r\n'

            xml += '  </conversation>\r\n'

        xml += '</MAP-convo-listing>\r\n'

        logging.debug(f"Built conversation listing: {len(paginated_convos)} conversations, {len(xml)} bytes")
        return len(filtered_convos), xml.encode('utf-8')

    def send_event(self, event: MAPEvent, version: str = "1.0", utc_offset: bool = True) -> bytes:
        """
        Send event notification

        Args:
            event: MAPEvent to send
            version: Event report version
            utc_offset: If True, include UTC offset in datetime format (±HHMM)

        Returns:
            XML event report as bytes
        """
        xml = event.to_xml(version, utc_offset)
        logging.debug(f"Sending event: {event.event_type.name}, handle={event.handle}")
        return xml.encode('utf-8')

    def _xml_escape(self, text: str) -> str:
        """Escape XML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))

    def set_folder(self, folder: str, flags: int = 0) -> bool:
        """
        Set current folder

        Args:
            folder: Folder name or path
            flags: Navigation flags (0x02 = go to root, 0x03 = go up one level)

        Returns:
            True if successful
        """
        if flags == 0x02 and len(folder) == 0:  # Go to root
            self.current_folder = ""
            logging.debug("Set folder to root")
            return True
        elif flags == 0x03:  # Go up one level
            if '/' in self.current_folder:
                self.current_folder = '/'.join(self.current_folder.split('/')[:-1])
                logging.debug(f"Set folder up one level: {self.current_folder}")
            elif self.current_folder != "":
                # If at top level folder (like "telecom"), go to root
                self.current_folder = ""
                logging.debug("Set folder up to root")
            return True
        else:  # Navigate to folder
            if folder:
                new_path = folder if self.current_folder == "" else f"{self.current_folder}/{folder}"

                if new_path in self.folders:
                    self.current_folder = new_path
                    logging.debug(f"Set folder to: {self.current_folder}")
                    return True
                else:
                    logging.error(f"Folder not found: {new_path}")
                    return False
            return True  # Empty folder name with flags=0 is valid (stay in current folder)

    def get_current_folder(self) -> str:
        """Get current folder path"""
        return self.current_folder

    def add_message(self, message: MAPMsg) -> str:
        """
        Add a message to storage

        Args:
            message: Message to add

        Returns:
            Message handle (persistent)
        """
        if not message.handle:
            # Generate persistent message handle
            message.handle = f"{self._message_counter:016X}"
            self._message_counter += 1

        self.messages[message.handle] = message

        # Increment folder version counter (may trigger DB ID update on rollover)
        self._increment_folder_version_counter(message.folder)

        # If message is added to a conversation, increment conversation version counter
        if message.conversation_id:
            self._increment_conversation_version_counter(message.conversation_id)
            logging.debug(f"Message added to conversation {message.conversation_id}, incremented version counter")

        self._save_storage()

        logging.debug(f"Added message {message.handle} (persistent handle)")
        return message.handle

    def get_message(self, handle: str) -> MAPMsg | None:
        """
        Get message by handle

        Args:
            handle: Message handle (persistent)

        Returns:
            Message or None
        """
        return self.messages.get(handle)

    def get_message_bmessage(self, handle: str, version: str = "1.1") -> bytes | None:
        """
        Get message in bMessage format

        Args:
            handle: Message handle (persistent)
            version: bMessage version ("1.0" or "1.1")

        Returns:
            bMessage as bytes or None
        """
        message = self.messages.get(handle)
        if not message:
            return None

        bmsg = message.to_bmessage(version)
        return bmsg.encode('utf-8')

    def delete_message(self, handle: str, permanent: bool = False) -> bool:
        """
        Delete message

        Args:
            handle: Message handle (persistent)
            permanent: If True, permanently delete; if False, move to deleted folder

        Returns:
            True if successful
        """
        message = self.messages.get(handle)
        if not message:
            return False

        old_folder = message.folder
        old_conversation_id = message.conversation_id

        if permanent:
            # Permanently delete
            del self.messages[handle]

            # Increment folder version counter (may trigger DB ID update on rollover)
            self._increment_folder_version_counter(old_folder)

            # If message was in a conversation, increment conversation version counter
            if old_conversation_id:
                self._increment_conversation_version_counter(old_conversation_id)
                logging.debug(f"Message deleted from conversation {old_conversation_id}, incremented version counter")
        else:
            # Move to deleted folder
            new_folder = "telecom/msg/deleted"
            message.folder = new_folder
            message.deleted = True

            # Increment folder version counters (may trigger DB ID update on rollover)
            self._increment_folder_version_counter(old_folder)
            self._increment_folder_version_counter(new_folder)

            # If message was in a conversation, increment conversation version counter
            if old_conversation_id:
                self._increment_conversation_version_counter(old_conversation_id)
                logging.debug(f"Message deleted from conversation {old_conversation_id}, incremented version counter")

        self._save_storage()
        logging.info(f"Deleted message {handle} (permanent={permanent})")
        return True

    def add_conversation(self, conversation: MAPConversation) -> str:
        """
        Add a conversation

        Args:
            conversation: Conversation to add

        Returns:
            Conversation ID (persistent)
        """
        if not conversation.id:
            # Generate persistent conversation ID
            conversation.id = f"{self._conversation_counter:016X}"
            self._conversation_counter += 1

        self.conversations[conversation.id] = conversation

        # Increment conversation-listing version counter (may trigger DB ID update on rollover)
        self._increment_conversation_listing_version_counter()

        self._save_storage()

        logging.debug(f"Added conversation {conversation.id} (persistent ID)")
        return conversation.id

    def get_conversation(self, conversation_id: str) -> MAPConversation | None:
        """
        Get conversation by ID

        Args:
            conversation_id: Conversation ID (persistent)

        Returns:
            Conversation or None
        """
        return self.conversations.get(conversation_id)

    def update_conversation(self, conversation_id: str, **kwargs) -> bool:
        """
        Update conversation properties

        Args:
            conversation_id: Conversation ID (persistent)
            **kwargs: Properties to update

        Returns:
            True if successful
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return False

        # Track which fields changed to determine counter updates
        listing_fields_changed = False
        version_fields_changed = False

        # Fields that trigger Conversation-Listing Version Counter update
        # Fields that trigger Conversation Version Counter update
        listing_fields = {'id', 'name', 'last_activity', 'read_status', 'summary'}

        # Check what changed
        for key, value in kwargs.items():
            if hasattr(conversation, key):
                old_value = getattr(conversation, key)

                # Check if listing fields changed and version fields changed
                if key in listing_fields and old_value != value:
                    listing_fields_changed = True
                    version_fields_changed = True

                # Check if participants changed (add/remove operations)
                if key == 'participants' and old_value != value:
                    version_fields_changed = True

                # Update the value
                setattr(conversation, key, value)

        # Increment conversation version counter only if version fields changed
        # (id, name, last_activity, read_status, summary changed OR participants added/removed)
        if version_fields_changed:
            self._increment_conversation_version_counter(conversation_id)

        # Increment conversation-listing version counter only if listing fields changed
        # (id, name, last_activity, read_status, summary changed)
        if listing_fields_changed:
            self._increment_conversation_listing_version_counter()

        self._save_storage()

        logging.info(f"Updated conversation {conversation_id}, "
                    f"listing_changed={listing_fields_changed}, "
                    f"version_changed={version_fields_changed}, "
                    f"version_counter={conversation.version_counter}")
        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation

        Args:
            conversation_id: Conversation ID (persistent)

        Returns:
            True if successful
        """
        if conversation_id not in self.conversations:
            return False

        del self.conversations[conversation_id]

        # Increment conversation-listing version counter (may trigger DB ID update on rollover)
        self._increment_conversation_listing_version_counter()

        self._save_storage()

        logging.info(f"Deleted conversation {conversation_id}")
        return True

    def get_messages_in_folder(self, folder: str) -> list[MAPMsg]:
        """
        Get all messages in a specific folder

        Args:
            folder: Folder path

        Returns:
            List of messages
        """
        messages = [msg for msg in self.messages.values() if msg.folder == folder and not msg.deleted]
        return messages

    def get_message_count(self, folder: str = None) -> int:
        """
        Get message count

        Args:
            folder: Folder path (None for all folders)

        Returns:
            Message count
        """
        if folder is None:
            return len([msg for msg in self.messages.values() if not msg.deleted])
        else:
            return len([msg for msg in self.messages.values()
                       if msg.folder == folder and not msg.deleted])

    def clear_all_messages(self):
        """Clear all messages (for testing)"""
        self.messages.clear()
        self._message_counter = 1

        # Reset all folder version counters (128-bit, 32 hex chars)
        for folder in self.folder_version_counters:
            self.folder_version_counters[folder] = "00000000000000000000000000000000"

        self._save_storage()
        logging.info("Cleared all messages")

    def clear_all_conversations(self):
        """Clear all conversations (for testing)"""
        self.conversations.clear()
        self.owner_status.clear()
        self._conversation_counter = 1

        # Reset conversation-listing version counter (128-bit, 32 hex chars)
        self.conversation_listing_version_counter = "00000000000000000000000000000000"

        self._save_storage()
        logging.info("Cleared all conversations")


def create_sample_messages(storage: MAPMsgStorage, count: int = 10):
    """
    Create sample messages for testing
    Creates EMAIL, SMS_GSM, SMS_CDMA, MMS, and IM messages in inbox folder
    IM messages will have associated conversations
    """
    base_time = datetime(2010, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Message types to create
    msg_types = [
        MAPMsgType.EMAIL,
        MAPMsgType.SMS_GSM,
        MAPMsgType.SMS_CDMA,
        MAPMsgType.MMS,
        MAPMsgType.IM
    ]

    # Track conversations for IM messages
    im_conversations = {}

    for i in range(count):
        msg_type = msg_types[i % len(msg_types)]

        # Calculate timestamp (older messages have earlier timestamps)
        msg_time = base_time + relativedelta(months=i * 4)
        datetime_str = msg_time.strftime("%Y%m%dT%H%M%S%z")

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
        else:  # SMS_GSM, SMS_CDMA, MMS
            sender_name = 'PTS'
            sender_addressing = '+1234567890'
            recipient_name = 'IUT'
            recipient_addressing = '+9876543210'

        # Create conversation for IM messages
        conversation_id = ""
        conversation_name = f"Chat with {sender_name}"
        if msg_type == MAPMsgType.IM:
            # Create participants
            participants = [
                MAPParticipant(
                    uci=sender_addressing,
                    display_name=sender_name,
                    chat_state=MAPChatState.ACTIVE,
                    last_activity=datetime_str,
                    name=sender_name,
                    presence_availability=MAPPresenceAvailability.ONLINE,
                    presence_text="Available",
                    priority=0
                ),
                MAPParticipant(
                    uci=recipient_addressing,
                    display_name=recipient_name,
                    chat_state=MAPChatState.ACTIVE,
                    last_activity=datetime_str,
                    name=recipient_name,
                    presence_availability=MAPPresenceAvailability.ONLINE,
                    presence_text="Available",
                    priority=0
                )
            ]

            conv = MAPConversation(
                id="",  # Will be auto-generated
                name=conversation_name,
                last_activity=datetime_str,
                read_status="unread" if i % 2 == 0 else "read",
                summary=f"Test IM message {i + 1}",
                participants=participants
            )
            conversation_id = storage.add_conversation(conv)

            # Set owner status for this conversation
            storage.set_owner_status(
                conversation_id=conversation_id,
                presence_availability=MAPPresenceAvailability.ONLINE,
                presence_text="Available",
                last_activity=datetime_str,
                chat_state=MAPChatState.ACTIVE
            )

        # Create message
        msg = MAPMsg(
            handle="",  # Will be auto-generated
            subject=f"Test {msg_type.name} Message {i + 1}",
            datetime=datetime_str,
            sender_name=sender_name,
            sender_addressing=sender_addressing,
            recipient_name=recipient_name,
            recipient_addressing=recipient_addressing,
            msg_type=msg_type,
            text=f"This is test {msg_type.name} message number {i + 1}. Lorem ipsum dolor sit amet.",
            read=(i % 2 == 0),
            sent=False,
            priority=(i % 5 == 0),
            folder="telecom/msg/inbox",
            conversation_id=conversation_id,
            conversation_name=conversation_name
        )

        storage.add_message(msg)

    logging.info(f"Created {count} sample messages in inbox folder:")
    logging.info(f"  - EMAIL: {sum(1 for i in range(count) if msg_types[i % len(msg_types)] == MAPMsgType.EMAIL)}")
    logging.info(f"  - SMS_GSM: {sum(1 for i in range(count) if msg_types[i % len(msg_types)] == MAPMsgType.SMS_GSM)}")
    logging.info(f"  - SMS_CDMA: {sum(1 for i in range(count) if msg_types[i % len(msg_types)] == MAPMsgType.SMS_CDMA)}")
    logging.info(f"  - MMS: {sum(1 for i in range(count) if msg_types[i % len(msg_types)] == MAPMsgType.MMS)}")
    logging.info(f"  - IM: {sum(1 for i in range(count) if msg_types[i % len(msg_types)] == MAPMsgType.IM)}")
    logging.info(f"Created {len(im_conversations)} IM conversations")


class MAPSrmState:
    SRM_DISABLED = 0
    SRM_ENABLED_BUT_WAITING = 1
    SRM_ENABLED = 2


class MAPInfo:
    CONN_ID = "conn_id"
    PSM = "psm"
    CHANNEL = "channel"
    SUPPORTED_FEATURES = "supported_features"
    MOPL = "mopl"
    LOCAL_SRM = "local_srm"
    LOCAL_SRMP = "local_srmp"
    SRM_STATE = "srm_state"
    RX_DATA = "rx_data"
    TX_DATA = "tx_data"
    TX_CNT = "tx_cnt"
    UTC_OFFSET = "utc_offset"
    PREV_INBOX = "pre_inbox"
    INBOX = "inbox"
    OUTBOX = "outbox"
    SENT = "sent"
    DELETED = "deleted"
    DRAFT = "draft"
    CONVO_LISTING = "convo_listing"
    REG_NTF_CNT = "reg_ntf_cnt"
    EVENT_VERSION = "event_version"


class MapSdp:
    def __init__(self, addr, role, final, channel, psm, version, supported_features, msg_types, instance_id, svc_name):
        self.addr = addr
        self.role = role
        self.final = final
        self.channel = channel
        self.psm = psm
        self.map_version = version
        self.supported_features = supported_features
        self.msg_types = msg_types
        self.instance_id = instance_id
        self.svc_name = svc_name


class MapConnection:
    def __init__(self, addr, instance_id):
        """
        Represents a single MAP connection (can have both transport and OBEX layers)
        :param addr: Bluetooth address
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        self.addr = addr
        self.instance_id = instance_id
        self.transport_type = None  # RFCOMM or L2CAP connection type
        self.obex_type = None       # OBEX connection type
        self.conn_info = {}
        self.data_rx = {}  # {ev: [data_list]}

        # Initialize connection info
        self.conn_info[MAPInfo.CONN_ID] = 0
        self.conn_info[MAPInfo.PSM] = 0
        self.conn_info[MAPInfo.CHANNEL] = 0
        self.conn_info[MAPInfo.SUPPORTED_FEATURES] = MAP_MANDATORY_SUPPORTED_FEATURES
        self.conn_info[MAPInfo.MOPL] = 255
        self.conn_info[MAPInfo.RX_DATA] = {}
        self.conn_info[MAPInfo.TX_DATA] = {}
        self.conn_info[MAPInfo.TX_CNT] = 0
        self.conn_info[MAPInfo.SRM_STATE] = MAPSrmState.SRM_DISABLED
        self.conn_info[MAPInfo.LOCAL_SRM] = False
        self.conn_info[MAPInfo.LOCAL_SRMP] = 0
        self.conn_info[MAPInfo.UTC_OFFSET] = False

    def set_transport(self, conn_type):
        """Set transport layer connection type"""
        self.transport_type = conn_type

    def clear_transport(self):
        """Clear transport layer connection"""
        self.transport_type = None

    def set_obex(self, conn_type):
        """Set OBEX layer connection type"""
        self.obex_type = conn_type

    def clear_obex(self):
        """Clear OBEX layer connection"""
        self.obex_type = None

    def has_transport(self, conn_type):
        """Check if has specific transport connection"""
        return self.transport_type == conn_type

    def has_obex(self, conn_type):
        """Check if has specific OBEX connection"""
        return self.obex_type == conn_type

    def is_transport_connected(self):
        """Check if transport layer is connected"""
        return self.transport_type is not None

    def is_obex_connected(self):
        """Check if OBEX layer is connected"""
        return self.obex_type is not None

    def set_info(self, key, value):
        self.conn_info[key] = value

    def get_info(self, key=None):
        if key is None:
            return self.conn_info
        return self.conn_info.get(key, None)

    def clear_rx_tx_state(self):
        self.conn_info[MAPInfo.TX_DATA] = {}
        self.conn_info[MAPInfo.RX_DATA] = {}
        self.conn_info[MAPInfo.TX_CNT] = 0
        self.conn_info[MAPInfo.SRM_STATE] = MAPSrmState.SRM_DISABLED
        self.conn_info[MAPInfo.LOCAL_SRM] = False
        self.conn_info[MAPInfo.LOCAL_SRMP] = 0

    def rx(self, ev, data):
        self.data_rx.setdefault(ev, []).append(data)

    def rx_data_get(self, ev, timeout, clear):
        if ev in self.data_rx and len(self.data_rx[ev]) != 0:
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        if wait_for_event(timeout, lambda: ev in self.data_rx and len(self.data_rx[ev]) != 0):
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        return None

    def rx_data_clear(self, ev, data):
        if ev in self.data_rx:
            if data in self.data_rx[ev]:
                self.data_rx[ev].remove(data)


class MAP:
    # Transport layer connection types
    TRANSPORT_TYPES = {
        defs.BTP_MAP_EV_MCE_MAS_RFCOMM_CONNECTED,
        defs.BTP_MAP_EV_MCE_MAS_L2CAP_CONNECTED,
        defs.BTP_MAP_EV_MCE_MNS_RFCOMM_CONNECTED,
        defs.BTP_MAP_EV_MCE_MNS_L2CAP_CONNECTED,
        defs.BTP_MAP_EV_MSE_MAS_RFCOMM_CONNECTED,
        defs.BTP_MAP_EV_MSE_MAS_L2CAP_CONNECTED,
        defs.BTP_MAP_EV_MSE_MNS_RFCOMM_CONNECTED,
        defs.BTP_MAP_EV_MSE_MNS_L2CAP_CONNECTED,
    }

    # OBEX layer connection types
    OBEX_TYPES = {
        defs.BTP_MAP_EV_MCE_MAS_CONNECT,
        defs.BTP_MAP_EV_MCE_MNS_CONNECT,
        defs.BTP_MAP_EV_MSE_MAS_CONNECT,
        defs.BTP_MAP_EV_MSE_MNS_CONNECT,
    }

    def __init__(self):
        self.connections = {}  # {addr: [MapConnection1, MapConnection2, ...]}
        self.sdp = {}  # {addr: [MapSdp1, MapSdp2, ...]}
        self.connections_history = {}  # {addr: [MapConnection1, MapConnection2, ...]}
        self.default_mce_mas = {}  # {addr: instance_id}
        self.default_mse_mas = {}  # {addr: instance_id}
        self.ntf_filter_mask = {}  # {addr: ntf_filter_mask}
        self.storage = None
        from autopts.pybtp.btp.map import MAPEventHandler
        self.event_handler = MAPEventHandler(self)
        self.event_handler.start()
        self.pre_conditions = {}

    def set_pre_conditions(self, key, value):
        self.pre_conditions[key] = value

    def get_pre_conditions(self, key=None):
        if key is None:
            return self.pre_conditions
        return self.pre_conditions.get(key, None)

    def clear_pre_conditions(self):
        self.pre_conditions = {}

    def cleanup(self):
        if hasattr(self, 'event_handler') and self.event_handler:
            self.event_handler.stop()

    def conn_lookup(self, addr, instance_id=None):
        """
        Find a MAP connection by address and instance_id
        :param addr: Bluetooth address
        :param instance_id: Instance ID (0x00-0xFF for MAS, None for MNS)
        :return: MapConnection or None
        """
        if addr not in self.connections:
            return None

        for conn in self.connections[addr]:
            if conn.instance_id == instance_id:
                return conn

        return None

    def _is_transport_type(self, conn_type):
        """Check if connection type is transport layer"""
        return conn_type in self.TRANSPORT_TYPES

    def _is_obex_type(self, conn_type):
        """Check if connection type is OBEX layer"""
        return conn_type in self.OBEX_TYPES

    def add_connection(self, addr, conn_type, instance_id=None):
        """
        Add or update a MAP connection
        :param addr: Bluetooth address
        :param conn_type: Connection type (transport or OBEX)
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        conn = self.conn_lookup(addr, instance_id)

        if conn is None:
            # Create new connection
            conn = MapConnection(addr, instance_id)

            # Add to connections dict
            if addr not in self.connections:
                self.connections[addr] = []
            self.connections[addr].append(conn)

            # Add to history
            if addr not in self.connections_history:
                self.connections_history[addr] = []
            self.connections_history[addr].append(conn)

            logging.debug(f"Created new connection: addr={addr}, instance={instance_id}")

        # Set appropriate layer
        if self._is_transport_type(conn_type):
            conn.set_transport(conn_type)
            logging.debug(f"Set transport: addr={addr}, instance={instance_id}, type={conn_type}")
        elif self._is_obex_type(conn_type):
            conn.set_obex(conn_type)
            logging.debug(f"Set OBEX: addr={addr}, instance={instance_id}, type={conn_type}")
        else:
            logging.warning(f"Unknown connection type: {conn_type}")

        for key in self.pre_conditions:
            if key == MAPInfo.LOCAL_SRMP:
                conn.set_info(key, self.pre_conditions[key])

    def remove_connection(self, addr, conn_type, instance_id=None):
        """
        Remove a MAP connection layer
        :param addr: Bluetooth address
        :param conn_type: Connection type (transport or OBEX)
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return

        # Clear appropriate layer
        if self._is_transport_type(conn_type):
            conn.clear_transport()
            logging.debug(f"Cleared transport: addr={addr}, instance={instance_id}, type={conn_type}")
        elif self._is_obex_type(conn_type):
            conn.clear_obex()
            logging.debug(f"Cleared OBEX: addr={addr}, instance={instance_id}, type={conn_type}")

        # Remove connection if both layers are disconnected
        if not conn.is_transport_connected() and not conn.is_obex_connected():
            self.connections[addr].remove(conn)
            logging.debug(f"Removed connection: addr={addr}, instance={instance_id}")

            # Remove addr entry if no more connections
            if not self.connections[addr]:
                del self.connections[addr]
                logging.debug(f"Removed address entry: addr={addr}")

    def get_connection_history(self, addr=None):
        """
        Get connection history
        :param addr: Bluetooth address (None for all addresses)
        :return: List of MapConnection instances or dict of all histories
        """
        if addr is None:
            return self.connections_history
        return self.connections_history.get(addr, [])

    def clear_connection_history(self, addr=None):
        """
        Clear connection history
        :param addr: Bluetooth address (None to clear all)
        """
        if addr is None:
            self.connections_history.clear()
            logging.debug("Cleared all connection history")
        elif addr in self.connections_history:
            del self.connections_history[addr]
            logging.debug(f"Cleared connection history for addr={addr}")

    def is_connected(self, addr, conn_type, instance_id=None):
        """
        Check if a specific connection layer exists
        :param addr: Bluetooth address
        :param conn_type: Connection type
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        :return: True if connected
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            return False

        if self._is_transport_type(conn_type):
            return conn.has_transport(conn_type)
        elif self._is_obex_type(conn_type):
            return conn.has_obex(conn_type)

        return False

    def wait_for_connection(self, addr, conn_type, timeout, instance_id=None):
        """
        Wait for a connection layer to be established
        :param addr: Bluetooth address
        :param conn_type: Connection type
        :param timeout: Timeout in seconds
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        :return: True if connected within timeout
        """
        if self.is_connected(addr=addr, instance_id=instance_id, conn_type=conn_type):
            return True
        return wait_for_event(timeout, self.is_connected, addr=addr, instance_id=instance_id, conn_type=conn_type)

    def wait_for_disconnection(self, addr, conn_type, timeout, instance_id=None):
        """
        Wait for a connection layer to be disconnected
        :param addr: Bluetooth address
        :param conn_type: Connection type
        :param timeout: Timeout in seconds
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        :return: True if disconnected within timeout
        """
        if not self.is_connected(addr=addr, instance_id=instance_id, conn_type=conn_type):
            return True
        return wait_for_event(timeout, lambda: not self.is_connected(addr=addr, instance_id=instance_id, conn_type=conn_type))

    def set_info(self, addr, key, value, instance_id=None):
        """
        Set connection info
        :param addr: Bluetooth address
        :param key: Info key
        :param value: Info value
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return

        conn.set_info(key, value)

    def get_info(self, addr, key, instance_id=None):
        """
        Get connection info
        :param addr: Bluetooth address
        :param key: Info key
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        :return: Info value or None if not found
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return None

        return conn.get_info(key)

    def clear_rx_tx_state(self, addr, instance_id=None):
        """Clear RX and TX state for a connection"""
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return

        conn.clear_rx_tx_state()

    def rx(self, addr, ev, data, instance_id=None):
        """
        Store received data
        :param addr: Bluetooth address
        :param ev: Event type
        :param data: Event data
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return

        conn.rx(ev, data)

    def rx_data_get(self, addr, ev, timeout=10, instance_id=None, clear=True):
        """
        Get received data
        :param addr: Bluetooth address
        :param ev: Event type
        :param timeout: Timeout in seconds
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        :param clear: Whether to remove the data after getting it
        :return: Data or None
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return None

        return conn.rx_data_get(ev, timeout, clear)

    def rx_data_clear(self, addr, ev, data, instance_id=None):
        """
        Clear specific received data
        :param addr: Bluetooth address
        :param ev: Event type
        :param data: Data to clear
        :param instance_id: 0x00-0xFF for MAS, None for MNS
        """
        conn = self.conn_lookup(addr, instance_id)
        if conn is None:
            logging.error(f"Connection not found: addr={addr}, instance={instance_id}")
            return

        conn.rx_data_clear(ev, data)

    def get_all_connections(self, addr):
        """
        Get all connections for a specific address
        :param addr: Bluetooth address
        :return: List of MapConnection instances
        """
        return self.connections.get(addr, [])

    def rx_sdp(self, addr, role, final, channel, psm, version,
               supported_features, msg_types=None, instance_id=None, svc_name=None):
        if addr in self.sdp:
            self.sdp[addr].append(MapSdp(addr, role, final, channel, psm, version,
                                         supported_features, msg_types, instance_id, svc_name))
        else:
            self.sdp[addr] = []
            self.sdp[addr].append(MapSdp(addr, role, final, channel, psm, version,
                                         supported_features, msg_types, instance_id, svc_name))

    def rx_sdp_get(self, addr, timeout=10, clear=False):
        if addr in self.sdp and len(self.sdp[addr]) != 0:
            sdp_list = self.sdp[addr]
            if clear:
                del self.sdp[addr]
            return sdp_list

        if wait_for_event(timeout, lambda: addr in self.sdp and len(self.sdp[addr]) != 0 and self.sdp[addr][-1].final):
            sdp_list = self.sdp[addr]
            if clear:
                del self.sdp[addr]
            return sdp_list

        return None

    def storage_init(self):
        if self.storage is None:
            self.storage = MAPMsgStorage()
            create_sample_messages(self.storage)
