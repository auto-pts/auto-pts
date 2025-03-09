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

# Generated by h2py.py (CPython 2.7.10) from
# zephyr/tests/bluetooth/tester/src/bttester.h


def BIT(bit):
    return 1 << bit

BTP_BR_ADDRESS_TYPE = 0xe0

BTP_MTU = 1024
BTP_INDEX_NONE = 0xff
BTP_SERVICE_ID_CORE = 0x00
BTP_SERVICE_ID_GAP = 0x01
BTP_SERVICE_ID_GATT = 0x02
BTP_SERVICE_ID_L2CAP = 0x03
BTP_SERVICE_ID_MESH = 0x04
BTP_SERVICE_ID_MMDL = 0x05
BTP_SERVICE_ID_GATTC = 0x06
BTP_SERVICE_ID_VCS = 0x08
BTP_SERVICE_ID_IAS = 0x09
BTP_SERVICE_ID_AICS = 0x0a
BTP_SERVICE_ID_VOCS = 0x0b
BTP_SERVICE_ID_PACS = 0x0c
BTP_SERVICE_ID_ASCS = 0x0d
BTP_SERVICE_ID_BAP = 0x0e
BTP_SERVICE_ID_HAS = 0x0f
BTP_SERVICE_ID_MICP = 0x10
BTP_SERVICE_ID_CSIS = 0x11
BTP_SERVICE_ID_MICS = 0x12
BTP_SERVICE_ID_CCP = 0x13
BTP_SERVICE_ID_VCP = 0x14
BTP_SERVICE_ID_CAS = 0x15
BTP_SERVICE_ID_MCP = 0x16
BTP_SERVICE_ID_GMCS = 0x17
BTP_SERVICE_ID_HAP = 0x18
BTP_SERVICE_ID_CSIP = 0x19
BTP_SERVICE_ID_CAP = 0x1a
BTP_SERVICE_ID_TBS = 0x1b
BTP_SERVICE_ID_TMAP = 0x1c
BTP_SERVICE_ID_OTS = 0x1d
BTP_SERVICE_ID_PBP = 0x1e
# GENERATOR append 1

BTP_ERROR = 0x00
BTP_STATUS_SUCCESS = 0x00
BTP_STATUS_FAILED = 0x01
BTP_STATUS_UNKNOWN_CMD = 0x02
BTP_STATUS_NOT_READY = 0x03
BTP_STATUS = 0x00
BTP_CORE_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CORE_CMD_READ_SUPPORTED_SERVICES = 0x02
BTP_CORE_CMD_REGISTER_SERVICE = 0x03
BTP_CORE_CMD_UNREGISTER_SERVICE = 0x04
BTP_CORE_CMD_LOG_MESSAGE = 0x05
BTP_CORE_EV_IUT_READY = 0x80
BTP_GAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_GAP_CMD_READ_CONTROLLER_INDEX_LIST = 0x02
GAP_SETTINGS_POWERED = 0
GAP_SETTINGS_CONNECTABLE = 1
GAP_SETTINGS_FAST_CONNECTABLE = 2
GAP_SETTINGS_DISCOVERABLE = 3
GAP_SETTINGS_BONDABLE = 4
GAP_SETTINGS_LINK_SEC_3 = 5
GAP_SETTINGS_SSP = 6
GAP_SETTINGS_BREDR = 7
GAP_SETTINGS_HS = 8
GAP_SETTINGS_LE = 9
GAP_SETTINGS_ADVERTISING = 10
GAP_SETTINGS_SC = 11
GAP_SETTINGS_DEBUG_KEYS = 12
GAP_SETTINGS_PRIVACY = 13
GAP_SETTINGS_CONTROLLER_CONFIG = 14
GAP_SETTINGS_STATIC_ADDRESS = 15
GAP_SETTINGS_SC_ONLY = 16
GAP_SETTINGS_EXTENDED_ADVERTISING = 17
BTP_GAP_CMD_READ_CONTROLLER_INFO = 0x03
BTP_GAP_CMD_RESET = 0x04
BTP_GAP_CMD_SET_POWERED = 0x05
BTP_GAP_CMD_SET_CONNECTABLE = 0x06
BTP_GAP_CMD_SET_FAST_CONNECTABLE = 0x07
GAP_NON_DISCOVERABLE = 0x00
GAP_GENERAL_DISCOVERABLE = 0x01
GAP_LIMITED_DISCOVERABLE = 0x02
BTP_GAP_CMD_SET_DISCOVERABLE = 0x08
BTP_GAP_CMD_SET_BONDABLE = 0x09
BTP_GAP_CMD_START_ADVERTISING = 0x0a
BTP_GAP_CMD_STOP_ADVERTISING = 0x0b
GAP_DISCOVERY_FLAG_LE = 0x01
GAP_DISCOVERY_FLAG_BREDR = 0x02
GAP_DISCOVERY_FLAG_LIMITED = 0x04
GAP_DISCOVERY_FLAG_LE_ACTIVE_SCAN = 0x08
GAP_DISCOVERY_FLAG_LE_OBSERVE = 0x10
BTP_GAP_CMD_START_DISCOVERY = 0x0c
BTP_GAP_CMD_STOP_DISCOVERY = 0x0d
BTP_GAP_CMD_CONNECT = 0x0e
BTP_GAP_CMD_DISCONNECT = 0x0f
GAP_IO_CAP_DISPLAY_ONLY = 0
GAP_IO_CAP_DISPLAY_YESNO = 1
GAP_IO_CAP_KEYBOARD_ONLY = 2
GAP_IO_CAP_NO_INPUT_OUTPUT = 3
GAP_IO_CAP_KEYBOARD_DISPLAY = 4
BTP_GAP_CMD_SET_IO_CAP = 0x10
BTP_GAP_CMD_PAIR = 0x11
BTP_GAP_CMD_UNPAIR = 0x12
BTP_GAP_CMD_PASSKEY_ENTRY = 0x13
BTP_GAP_CMD_PASSKEY_CONFIRM = 0x14
GAP_START_DIRECT_ADV_HD = 0x0001
GAP_START_DIRECT_ADV_OWN_ID = 0x0002
GAP_START_DIRECT_ADV_PEER_RPA = 0x0004
BTP_GAP_CMD_START_DIRECT_ADV = 0x15
BTP_GAP_CMD_CONN_PARAM_UPDATE = 0x16
BTP_GAP_CMD_PAIRING_CONSENT_RSP = 0x17
BTP_GAP_CMD_OOB_LEGACY_SET_DATA = 0x18
BTP_GAP_CMD_OOB_SC_GET_LOCAL_DATA = 0x19
BTP_GAP_CMD_OOB_SC_SET_REMOTE_DATA = 0x1a
BTP_GAP_CMD_SET_MITM = 0x1b
BTP_GAP_CMD_SET_FILTER_ACCEPT_LIST = 0x1c
BTP_GAP_CMD_SET_PRIVACY = 0x1d
BTP_GAP_CMD_SET_SC_ONLY = 0x1e
BTP_GAP_CMD_SET_SC = 0x1f
BTP_GAP_CMD_SET_MIN_ENC_KEY_SIZE = 0x20
BTP_GAP_CMD_SET_EXTENDED_ADVERTISING = 0x21
BTP_GAP_CMD_PADV_CONFIGURE = 0x22
BTP_GAP_CMD_PADV_START = 0x23
BTP_GAP_CMD_PADV_STOP = 0x24
BTP_GAP_CMD_PADV_SET_DATA = 0x25
BTP_GAP_CMD_PADV_CREATE_SYNC = 0x26
BTP_GAP_CMD_PADV_SYNC_TRANSFER_SET_INFO = 0x27
BTP_GAP_CMD_PADV_SYNC_TRANSFER_START = 0x28
BTP_GAP_CMD_PADV_SYNC_TRANSFER_RECV = 0x29
BTP_GAP_CMD_PAIR_V2_MODE_1 = 0x01
BTP_GAP_CMD_PAIR_V2_MODE_2 = 0x02
BTP_GAP_CMD_PAIR_V2_MODE_3 = 0x03
BTP_GAP_CMD_PAIR_V2_MODE_4 = 0x04
BTP_GAP_CMD_PAIR_V2_MODE_ANY = 0xFF
BTP_GAP_CMD_PAIR_V2_LEVEL_0 = 0x00
BTP_GAP_CMD_PAIR_V2_LEVEL_1 = 0x01
BTP_GAP_CMD_PAIR_V2_LEVEL_2 = 0x02
BTP_GAP_CMD_PAIR_V2_LEVEL_3 = 0x03
BTP_GAP_CMD_PAIR_V2_LEVEL_4 = 0x04
BTP_GAP_CMD_PAIR_V2_LEVEL_ANY = 0xFF
BTP_GAP_CMD_PAIR_V2_FLAG_NONE = 0x00
BTP_GAP_CMD_PAIR_V2_FLAG_FORCE_PAIR = 0x01
BTP_GAP_CMD_PAIR_V2 = 0x2a
BTP_GAP_EV_NEW_SETTINGS = 0x80
GAP_DEVICE_FOUND_FLAG_RSSI = 0x01
GAP_DEVICE_FOUND_FLAG_AD = 0x02
GAP_DEVICE_FOUND_FLAG_SD = 0x04
BTP_GAP_EV_DEVICE_FOUND = 0x81
BTP_GAP_EV_DEVICE_CONNECTED = 0x82
BTP_GAP_EV_DEVICE_DISCONNECTED = 0x83
BTP_GAP_EV_PASSKEY_DISPLAY = 0x84
BTP_GAP_EV_PASSKEY_ENTRY_REQ = 0x85
BTP_GAP_EV_PASSKEY_CONFIRM_REQ = 0x86
BTP_GAP_EV_IDENTITY_RESOLVED = 0x87
BTP_GAP_EV_CONN_PARAM_UPDATE = 0x88
BTP_GAP_EV_SEC_LEVEL_CHANGED = 0x89
BTP_GAP_EV_PAIRING_CONSENT_REQ = 0x8a
BTP_GAP_EV_BOND_LOST = 0x8b
BTP_GAP_EV_PAIRING_FAILED = 0x8c
BTP_GAP_EV_PERIODIC_SYNC_ESTABLISHED = 0x8d
BTP_GAP_EV_PERIODIC_SYNC_LOST = 0x8e
BTP_GAP_EV_PERIODIC_REPORT = 0x8f
BTP_GAP_EV_PERIODIC_TRANSFER_RECEIVED = 0x90
BTP_GAP_EV_ENCRYPTION_CHANGE=0x91
BTP_GATT_CMD_READ_SUPPORTED_COMMANDS = 0x01
GATT_SERVICE_PRIMARY = 0x00
GATT_SERVICE_SECONDARY = 0x01
BTP_GATT_CMD_ADD_SERVICE = 0x02
BTP_GATT_CMD_ADD_CHARACTERISTIC = 0x03
BTP_GATT_CMD_ADD_DESCRIPTOR = 0x04
BTP_GATT_CMD_ADD_INCLUDED_SERVICE = 0x05
BTP_GATT_CMD_SET_VALUE = 0x06
BTP_GATT_CMD_START_SERVER = 0x07
BTP_GATT_CMD_SET_ENC_KEY_SIZE = 0x09
BTP_GATT_CMD_EXCHANGE_MTU = 0x0a
BTP_GATT_CMD_DISC_ALL_PRIM = 0x0b
BTP_GATT_CMD_DISC_PRIM_UUID = 0x0c
BTP_GATT_CMD_FIND_INCLUDED = 0x0d
BTP_GATT_CMD_DISC_ALL_CHRC = 0x0e
BTP_GATT_CMD_DISC_CHRC_UUID = 0x0f
BTP_GATT_CMD_DISC_ALL_DESC = 0x10
BTP_GATT_CMD_READ = 0x11
BTP_GATT_CMD_READ_UUID = 0x12
BTP_GATT_CMD_READ_LONG = 0x13
BTP_GATT_CMD_READ_MULTIPLE = 0x14
BTP_GATT_CMD_WRITE_WITHOUT_RSP = 0x15
BTP_GATT_CMD_SIGNED_WRITE_WITHOUT_RSP = 0x16
BTP_GATT_CMD_WRITE = 0x17
BTP_GATT_CMD_WRITE_LONG = 0x18
BTP_GATT_CMD_WRITE_RELIABLE = 0x19
BTP_GATT_CMD_CFG_NOTIFY = 0x1a
BTP_GATT_CMD_CFG_INDICATE = 0x1b
BTP_GATT_CMD_GET_ATTRIBUTES = 0x1c
BTP_GATT_CMD_GET_ATTRIBUTE_VALUE = 0x1d
BTP_GATT_CMD_CHANGE_DATABASE = 0x1e
BTP_GATT_CMD_EATT_CONNECT = 0x1f
BTP_GATT_CMD_READ_MULTIPLE_VAR = 0x20
BTP_GATT_CMD_NOTIFY_MULTIPLE = 0x21
BTP_GATT_EV_NOTIFICATION = 0x80
BTP_GATT_EV_ATTR_VALUE_CHANGED = 0x81
BTP_GATTC_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_GATTC_CMD_EXCHANGE_MTU = 0x02
BTP_GATTC_CMD_DISC_ALL_PRIM = 0x03
BTP_GATTC_CMD_DISC_PRIM_UUID = 0x04
BTP_GATTC_CMD_FIND_INCLUDED = 0x05
BTP_GATTC_CMD_DISC_ALL_CHRC = 0x06
BTP_GATTC_CMD_DISC_CHRC_UUID = 0x07
BTP_GATTC_CMD_DISC_ALL_DESC = 0x08
BTP_GATTC_CMD_READ = 0x09
BTP_GATTC_CMD_READ_UUID = 0x0a
BTP_GATTC_CMD_READ_LONG = 0x0b
BTP_GATTC_CMD_READ_MULTIPLE = 0x0c
BTP_GATTC_CMD_WRITE_WITHOUT_RSP = 0x0d
BTP_GATTC_CMD_SIGNED_WRITE_WITHOUT_RSP = 0x0e
BTP_GATTC_CMD_WRITE = 0x0f
BTP_GATTC_CMD_WRITE_LONG = 0x10
BTP_GATTC_CMD_WRITE_RELIABLE = 0x11
BTP_GATTC_CMD_CFG_NOTIFY = 0x12
BTP_GATTC_CMD_CFG_INDICATE = 0x13
BTP_GATTC_CMD_READ_MULTIPLE_VAR = 0x14
BTP_GATTC_EV_MTU_EXCHANGED = 0x80
BTP_GATTC_EV_DISC_ALL_PRIM_RP = 0x81
BTP_GATTC_EV_DISC_PRIM_UUID_RP = 0x82
BTP_GATTC_EV_FIND_INCLUDED_RP = 0x83
BTP_GATTC_EV_DISC_ALL_CHRC_RP = 0x84
BTP_GATTC_EV_DISC_CHRC_UUID_RP = 0x85
BTP_GATTC_EV_DISC_ALL_DESC_RP = 0x86
BTP_GATTC_EV_READ_RP = 0x87
BTP_GATTC_EV_READ_UUID_RP = 0x88
BTP_GATTC_EV_READ_LONG_RP = 0x89
BTP_GATTC_EV_READ_MULTIPLE_RP = 0x8a
BTP_GATTC_EV_WRITE_RP = 0x8b
BTP_GATTC_EV_WRITE_LONG_RP = 0x8c
BTP_GATTC_EV_RELIABLE_WRITE_RP = 0x8d
BTP_GATTC_EV_CFG_NOTIFY_RP = 0x8e
BTP_GATTC_EV_CFG_INDICATE_RP = 0x8f
BTP_GATTC_EV_EV_NOTIFICATION_RXED = 0x90
BTP_GATTC_EV_READ_MULTIPLE_VAR_RP = 0x91
BTP_L2CAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_L2CAP_CMD_CONNECT = 0x02
L2CAP_CONNECT_OPT_ECFC = 0x01
L2CAP_CONNECT_OPT_HOLD_CREDIT = 0x02
BTP_L2CAP_CMD_DISCONNECT = 0x03
BTP_L2CAP_CMD_SEND_DATA = 0x04
L2CAP_TRANSPORT_BREDR = 0x00
L2CAP_TRANSPORT_LE = 0x01
BTP_L2CAP_CMD_LISTEN = 0x05
BTP_L2CAP_CMD_ACCEPT_CONNECTION = 0x06
BTP_L2CAP_CMD_RECONFIGURE = 0x07
BTP_L2CAP_CMD_CREDITS = 0x08
BTP_L2CAP_CMD_DISCONNECT_EATT_CHANS = 0x09
BTP_L2CAP_EV_CONNECTION_REQ = 0x80
BTP_L2CAP_EV_CONNECTED = 0x81
BTP_L2CAP_EV_DISCONNECTED = 0x82
BTP_L2CAP_EV_DATA_RECEIVED = 0x83
BTP_L2CAP_EV_RECONFIGURED = 0x84
BTP_MESH_CMD_READ_SUPPORTED_COMMANDS = 0x01
MESH_STATIC_OOB = 0x01
MESH_OUTPUT_OOB = 0x02
MESH_INPUT_OOB = 0x03
MESH_OUT_BLINK = 0x01
MESH_OUT_BEEP = 0x02
MESH_OUT_VIBRATE = 0x04
MESH_OUT_DISPLAY_NUMBER = 0x08
MESH_OUT_DISPLAY_STRING = 0x10
MESH_IN_PUSH = 0x01
MESH_IN_TWIST = 0x02
MESH_IN_ENTER_NUMBER = 0x04
MESH_IN_ENTER_STRING = 0x08
BTP_MESH_CMD_CONFIG_PROVISIONING = 0x02
BTP_MESH_CMD_PROVISION_NODE = 0x03
BTP_MESH_CMD_INIT = 0x04
BTP_MESH_CMD_START = 0x78
BTP_MESH_CMD_RESET = 0x05
BTP_MESH_CMD_INPUT_NUMBER = 0x06
BTP_MESH_CMD_INPUT_STRING = 0x07
BTP_MESH_CMD_IV_UPDATE_TEST_MODE = 0x08
BTP_MESH_CMD_IV_UPDATE_TOGGLE = 0x09
BTP_MESH_CMD_NET_SEND = 0x0a
BTP_MESH_CMD_HEALTH_ADD_FAULTS = 0x0b
BTP_MESH_CMD_HEALTH_CLEAR_FAULTS = 0x0c
BTP_MESH_CMD_LPN_SET = 0x0d
BTP_MESH_CMD_LPN_POLL = 0x0e
BTP_MESH_CMD_MODEL_SEND = 0x0f
BTP_MESH_CMD_LPN_SUBSCRIBE = 0x10
BTP_MESH_CMD_LPN_UNSUBSCRIBE = 0x11
BTP_MESH_CMD_RPL_CLEAR = 0x12
BTP_MESH_CMD_PROXY_IDENTITY = 0x13
BTP_MESH_CMD_COMP_DATA_GET = 0x14
BTP_MESH_CMD_CFG_BEACON_GET = 0x15
BTP_MESH_CMD_CFG_BEACON_SET = 0x16
MESH_CFG_DATA_SET = 0x17
BTP_MESH_CMD_CFG_DEFAULT_TTL_GET = 0x18
BTP_MESH_CMD_CFG_DEFAULT_TTL_SET = 0x19
BTP_MESH_CMD_CFG_GATT_PROXY_GET = 0x1a
BTP_MESH_CMD_CFG_GATT_PROXY_SET = 0x1b
BTP_MESH_CMD_CFG_FRIEND_GET = 0x1c
BTP_MESH_CMD_CFG_FRIEND_SET = 0x1d
BTP_MESH_CMD_CFG_RELAY_GET = 0x1e
BTP_MESH_CMD_CFG_RELAY_SET = 0x1f
BTP_MESH_CMD_CFG_MODEL_PUB_GET = 0x20
BTP_MESH_CMD_CFG_MODEL_PUB_SET = 0x21
BTP_MESH_CMD_CFG_MODEL_SUB_ADD = 0x22
BTP_MESH_CMD_CFG_MODEL_SUB_DEL = 0x23
BTP_MESH_CMD_CFG_NETKEY_ADD = 0x24
BTP_MESH_CMD_CFG_NETKEY_GET = 0x25
BTP_MESH_CMD_CFG_NETKEY_DEL = 0x26
BTP_MESH_CMD_CFG_APPKEY_ADD = 0x27
BTP_MESH_CMD_CFG_APPKEY_DEL = 0x28
BTP_MESH_CMD_CFG_APPKEY_GET = 0x29
BTP_MESH_CMD_CFG_MODEL_APP_BIND = 0x2A
BTP_MESH_CMD_CFG_MODEL_APP_UNBIND = 0x2B
BTP_MESH_CMD_CFG_MODEL_APP_GET = 0x2C
BTP_MESH_CMD_CFG_MODEL_APP_VND_GET = 0x2D
BTP_MESH_CMD_CFG_HEARTBEAT_PUB_SET = 0x2E
BTP_MESH_CMD_CFG_HEARTBEAT_PUB_GET = 0x2F
BTP_MESH_CMD_CFG_HEARTBEAT_SUB_SET = 0x30
BTP_MESH_CMD_CFG_HEARTBEAT_SUB_GET = 0x31
BTP_MESH_CMD_CFG_NET_TRANSMIT_GET = 0x32
BTP_MESH_CMD_CFG_NET_TRANSMIT_SET = 0x33
BTP_MESH_CMD_CFG_MODEL_SUB_OVW = 0x34
BTP_MESH_CMD_CFG_MODEL_SUB_DEL_ALL = 0x35
BTP_MESH_CMD_CFG_MODEL_SUB_GET = 0x36
BTP_MESH_CMD_CFG_MODEL_SUB_VND_GET = 0x37
BTP_MESH_CMD_CFG_MODEL_SUB_VA_ADD = 0x38
BTP_MESH_CMD_CFG_MODEL_SUB_VA_DEL = 0x39
BTP_MESH_CMD_CFG_MODEL_SUB_VA_OVW = 0x3A
BTP_MESH_CMD_CFG_NETKEY_UPDATE = 0x3B
BTP_MESH_CMD_CFG_APPKEY_UPDATE = 0x3C
BTP_MESH_CMD_CFG_NODE_IDT_SET = 0x3D
BTP_MESH_CMD_CFG_NODE_IDT_GET = 0x3E
BTP_MESH_CMD_CFG_NODE_RESET = 0x3F
BTP_MESH_CMD_CFG_LPN_POLLTIMEOUT_GET = 0x40
BTP_MESH_CMD_CFG_MODEL_PUB_VA_SET = 0x41
BTP_MESH_CMD_CFG_MODEL_APP_BIND_VND = 0x42
BTP_MESH_CMD_HEALTH_FAULT_GET = 0x43
BTP_MESH_CMD_HEALTH_FAULT_CLEAR = 0x44
BTP_MESH_CMD_HEALTH_FAULT_TEST = 0x45
BTP_MESH_CMD_HEALTH_PERIOD_GET = 0x46
BTP_MESH_CMD_HEALTH_PERIOD_SET = 0x47
BTP_MESH_CMD_HEALTH_ATTENTION_GET = 0x48
BTP_MESH_CMD_HEALTH_ATTENTION_SET = 0x49
BTP_MESH_CMD_PROVISION_ADV = 0x4A
BTP_MESH_CMD_CFG_KRP_GET = 0x4B
BTP_MESH_CMD_CFG_KRP_SET = 0x4C
BTP_MESH_CMD_VA_ADD = 0x4D
BTP_MESH_CMD_VA_DEL = 0x4E
BTP_MESH_CMD_SAR_TRANSMITTER_GET = 0x4F
BTP_MESH_CMD_SAR_TRANSMITTER_SET = 0x50
BTP_MESH_CMD_SAR_RECEIVER_GET = 0x51
BTP_MESH_CMD_SAR_RECEIVER_SET = 0x52
BTP_MESH_CMD_LARGE_COMP_DATA_GET = 0x53
BTP_MESH_CMD_MODELS_METADATA_GET = 0x54
BTP_MESH_CMD_OPCODES_AGGREGATOR_INIT = 0x55
BTP_MESH_CMD_OPCODES_AGGREGATOR_SEND = 0x56
BTP_MESH_CMD_COMP_CHANGE_PREPARE = 0x57
BTP_MESH_CMD_RPR_SCAN_START = 0x59
BTP_MESH_CMD_RPR_EXT_SCAN_START = 0x5a
BTP_MESH_CMD_RPR_SCAN_CAPS_GET = 0x5b
BTP_MESH_CMD_RPR_SCAN_GET = 0x5c
BTP_MESH_CMD_RPR_SCAN_STOP = 0x5d
BTP_MESH_CMD_RPR_LINK_GET = 0x5e
BTP_MESH_CMD_RPR_LINK_CLOSE = 0x5f
BTP_MESH_CMD_RPR_PROV_REMOTE = 0x60
BTP_MESH_CMD_RPR_REPROV_REMOTE = 0x61
BTP_MESH_CMD_SUBNET_BRIDGE_GET = 0x62
BTP_MESH_CMD_SUBNET_BRIDGE_SET = 0x63
BTP_MESH_CMD_BRIDGING_TABLE_ADD = 0x64
BTP_MESH_CMD_BRIDGING_TABLE_REMOVE = 0x65
BTP_MESH_CMD_BRIDGED_SUBNETS_GET = 0x66
BTP_MESH_CMD_BRIDGING_TABLE_GET = 0x67
BTP_MESH_CMD_BRIDGE_CAPABILITY_GET = 0x68

BTP_MESH_CMD_PRIV_BEACON_GET = 0x6c
BTP_MESH_CMD_PRIV_BEACON_SET = 0x6d
BTP_MESH_CMD_PRIV_GATT_PROXY_GET = 0x6e
BTP_MESH_CMD_PRIV_GATT_PROXY_SET = 0x6f
BTP_MESH_CMD_PRIV_NODE_ID_GET = 0x70
BTP_MESH_CMD_PRIV_NODE_ID_SET = 0x71
BTP_MESH_CMD_PROXY_PRIVATE_IDENTITY = 0x72
BTP_MESH_CMD_OD_PRIV_PROXY_GET = 0x73
BTP_MESH_CMD_OD_PRIV_PROXY_SET = 0x74
BTP_MESH_CMD_SRPL_CLEAR = 0x75
BTP_MESH_CMD_PROXY_SOLICIT = 0x76
BTP_MESH_CMD_PROXY_CONNECT = 0x77
BTP_MESH_EV_OUT_NUMBER_ACTION = 0x80
BTP_MESH_EV_OUT_STRING_ACTION = 0x81
BTP_MESH_EV_IN_ACTION = 0x82
BTP_MESH_EV_PROVISIONED = 0x83
MESH_PROV_BEARER_PB_ADV = 0x00
MESH_PROV_BEARER_PB_GATT = 0x01
BTP_MESH_EV_PROV_LINK_OPEN = 0x84
BTP_MESH_EV_PROV_LINK_CLOSED = 0x85
BTP_MESH_EV_NET_RECV = 0x86
BTP_MESH_EV_INVALID_BEARER = 0x87
BTP_MESH_EV_INCOMP_TIMER_EXP = 0x88
BTP_MESH_EV_FRND_ESTABLISHED = 0x89
BTP_MESH_EV_FRND_TERMINATED = 0x8a
BTP_MESH_EV_LPN_ESTABLISHED = 0x8b
BTP_MESH_EV_LPN_TERMINATED = 0x8c
BTP_MESH_EV_LPN_POLLED = 0x8d
BTP_MESH_EV_PROV_NODE_ADDED = 0x8e
BTP_MESH_EV_MODEL_RECV = 0x8f
BTP_MESH_EV_BLOB_LOST_TARGET = 0x90
BTP_MMDL_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_MMDL_CMD_GEN_ONOFF_GET = 0x02
BTP_MMDL_CMD_GEN_ONOFF_SET = 0x03
BTP_MMDL_CMD_GEN_LVL_GET = 0x04
BTP_MMDL_CMD_GEN_LVL_SET = 0x05
BTP_MMDL_CMD_GEN_LVL_DELTA_SET = 0x06
BTP_MMDL_CMD_GEN_LVL_MOVE_SET = 0x07
BTP_MMDL_CMD_GEN_DTT_GET = 0x08
BTP_MMDL_CMD_GEN_DTT_SET = 0x09
BTP_MMDL_CMD_GEN_PONOFF_GET = 0x0a
BTP_MMDL_CMD_GEN_PONOFF_SET = 0x0b
BTP_MMDL_CMD_GEN_PLVL_GET = 0x0c
BTP_MMDL_CMD_GEN_PLVL_SET = 0x0d
BTP_MMDL_CMD_GEN_PLVL_LAST_GET = 0x0e
BTP_MMDL_CMD_GEN_PLVL_DFLT_GET = 0x0f
BTP_MMDL_CMD_GEN_PLVL_DFLT_SET = 0x10
BTP_MMDL_CMD_GEN_PLVL_RANGE_GET = 0x11
BTP_MMDL_CMD_GEN_PLVL_RANGE_SET = 0x12
BTP_MMDL_CMD_GEN_BATTERY_GET = 0x13
BTP_MMDL_CMD_GEN_LOC_GLOBAL_GET = 0x14
BTP_MMDL_CMD_GEN_LOC_LOCAL_GET = 0x15
BTP_MMDL_CMD_GEN_LOC_GLOBAL_SET = 0x16
BTP_MMDL_CMD_GEN_LOC_LOCAL_SET = 0x17
BTP_MMDL_CMD_GEN_PROPS_GET = 0x18
BTP_MMDL_CMD_GEN_PROP_GET = 0x19
BTP_MMDL_CMD_GEN_PROP_SET = 0x1a
BTP_MMDL_CMD_SENSOR_DESC_GET = 0x1b
BTP_MMDL_CMD_SENSOR_GET = 0x1c
BTP_MMDL_CMD_SENSOR_COLUMN_GET = 0x1d
BTP_MMDL_CMD_SENSOR_SERIES_GET = 0x1e
BTP_MMDL_CMD_SENSOR_CADENCE_GET = 0x1f
BTP_MMDL_CMD_SENSOR_CADENCE_SET = 0x20
BTP_MMDL_CMD_SENSOR_SETTINGS_GET = 0x21
BTP_MMDL_CMD_SENSOR_SETTING_GET = 0x22
BTP_MMDL_CMD_SENSOR_SETTING_SET = 0x23
BTP_MMDL_CMD_TIME_GET = 0x24
BTP_MMDL_CMD_TIME_SET = 0x25
BTP_MMDL_CMD_TIME_ROLE_GET = 0x26
BTP_MMDL_CMD_TIME_ROLE_SET = 0x27
BTP_MMDL_CMD_TIME_ZONE_GET = 0x28
BTP_MMDL_CMD_TIME_ZONE_SET = 0x29
BTP_MMDL_CMD_TIME_TAI_UTC_DELTA_GET = 0x2a
BTP_MMDL_CMD_TIME_TAI_UTC_DELTA_SET = 0x2b
BTP_MMDL_CMD_LIGHT_LIGHTNESS_GET = 0x2c
BTP_MMDL_CMD_LIGHT_LIGHTNESS_SET = 0x2d
BTP_MMDL_CMD_LIGHT_LIGHTNESS_LINEAR_GET = 0x2e
BTP_MMDL_CMD_LIGHT_LIGHTNESS_LINEAR_SET = 0x2f
BTP_MMDL_CMD_LIGHT_LIGHTNESS_LAST_GET = 0x30
BTP_MMDL_CMD_LIGHT_LIGHTNESS_DEFAULT_GET = 0x31
BTP_MMDL_CMD_LIGHT_LIGHTNESS_DEFAULT_SET = 0x32
BTP_MMDL_CMD_LIGHT_LIGHTNESS_RANGE_GET = 0x33
BTP_MMDL_CMD_LIGHT_LIGHTNESS_RANGE_SET = 0x34
BTP_MMDL_CMD_LIGHT_LC_MODE_GET = 0x35
BTP_MMDL_CMD_LIGHT_LC_MODE_SET = 0x36
BTP_MMDL_CMD_LIGHT_LC_OCCUPANCY_MODE_GET = 0x37
BTP_MMDL_CMD_LIGHT_LC_OCCUPANCY_MODE_SET = 0x38
BTP_MMDL_CMD_LIGHT_LC_LIGHT_ONOFF_MODE_GET = 0x39
BTP_MMDL_CMD_LIGHT_LC_LIGHT_ONOFF_MODE_SET = 0x3a
BTP_MMDL_CMD_LIGHT_LC_PROPERTY_GET = 0x3b
BTP_MMDL_CMD_LIGHT_LC_PROPERTY_SET = 0x3c
BTP_MMDL_CMD_SENSOR_DATA_SET = 0x3d
BTP_MMDL_CMD_LIGHT_CTL_STATES_GET = 0x3e
BTP_MMDL_CMD_LIGHT_CTL_STATES_SET = 0x3f
BTP_MMDL_CMD_LIGHT_CTL_TEMPERATURE_GET = 0x40
BTP_MMDL_CMD_LIGHT_CTL_TEMPERATURE_SET = 0x41
BTP_MMDL_CMD_LIGHT_CTL_DEFAULT_GET = 0x42
BTP_MMDL_CMD_LIGHT_CTL_DEFAULT_SET = 0x43
BTP_MMDL_CMD_LIGHT_CTL_TEMPERATURE_RANGE_GET = 0x44
BTP_MMDL_CMD_LIGHT_CTL_TEMPERATURE_RANGE_SET = 0x45
BTP_MMDL_CMD_SCENE_STATE_GET = 0x46
BTP_MMDL_CMD_SCENE_REGISTER_GET = 0x47
BTP_MMDL_CMD_SCENE_STORE_PROCEDURE = 0x48
BTP_MMDL_CMD_SCENE_RECALL = 0x49
BTP_MMDL_CMD_LIGHT_XYL_GET = 0x4a
BTP_MMDL_CMD_LIGHT_XYL_SET = 0x4b
BTP_MMDL_CMD_LIGHT_XYL_TARGET_GET = 0x4c
BTP_MMDL_CMD_LIGHT_XYL_DEFAULT_GET = 0x4d
BTP_MMDL_CMD_LIGHT_XYL_DEFAULT_SET = 0x4e
BTP_MMDL_CMD_LIGHT_XYL_RANGE_GET = 0x4f
BTP_MMDL_CMD_LIGHT_XYL_RANGE_SET = 0x50
BTP_MMDL_CMD_LIGHT_HSL_GET = 0x51
BTP_MMDL_CMD_LIGHT_HSL_SET = 0x52
BTP_MMDL_CMD_LIGHT_HSL_TARGET_GET = 0x53
BTP_MMDL_CMD_LIGHT_HSL_DEFAULT_GET = 0x54
BTP_MMDL_CMD_LIGHT_HSL_DEFAULT_SET = 0x55
BTP_MMDL_CMD_LIGHT_HSL_RANGE_GET = 0x56
BTP_MMDL_CMD_LIGHT_HSL_RANGE_SET = 0x57
BTP_MMDL_CMD_LIGHT_HSL_HUE_GET = 0x58
BTP_MMDL_CMD_LIGHT_HSL_HUE_SET = 0x59
BTP_MMDL_CMD_LIGHT_HSL_SATURATION_GET = 0x5a
BTP_MMDL_CMD_LIGHT_HSL_SATURATION_SET = 0x5b
BTP_MMDL_CMD_SCHEDULER_GET = 0x5c
BTP_MMDL_CMD_SCHEDULER_ACTION_GET = 0x5d
BTP_MMDL_CMD_SCHEDULER_ACTION_SET = 0x5e
BTP_MMDL_CMD_DFU_INF_GET = 0x5f
BTP_MMDL_CMD_BLOB_INFO_GET = 0x60
BTP_MMDL_CMD_DFU_UPDATE_FIRMWARE_CHECK = 0x61
BTP_MMDL_CMD_DFU_UPDATE_FIRMWARE_GET = 0x62
BTP_MMDL_CMD_DFU_UPDATE_FIRMWARE_CANCEL = 0x63
BTP_MMDL_CMD_DFU_UPDATE_FIRMWARE_START = 0x64
BTP_MMDL_CMD_BLOB_SRV_RECV = 0x65
BTP_MMDL_CMD_BLOB_TRANSFER_START = 0x66
BTP_MMDL_CMD_BLOB_TRANSFER_CANCEL = 0x67
BTP_MMDL_CMD_BLOB_TRANSFER_GET = 0x68
BTP_MMDL_CMD_BLOB_SRV_CANCEL = 0x69
BTP_MMDL_CMD_DFU_UPDATE_FIRMWARE_APPLY = 0x6A
BTP_MMDL_CMD_DFU_SRV_APPLY = 0x6B

BTP_VCS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_VCS_CMD_SET_VOL = 0x02
BTP_VCS_CMD_VOL_UP = 0x03
BTP_VCS_CMD_VOL_DOWN = 0x04
BTP_VCS_CMD_MUTE = 0x05
BTP_VCS_CMD_UNMUTE = 0x06

BTP_IAS_EV_OUT_ALERT_ACTION = 0x80

BTP_AICS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_AICS_CMD_SET_GAIN = 0x02
BTP_AICS_CMD_MUTE = 0x03
BTP_AICS_CMD_UNMUTE = 0x04
BTP_AICS_CMD_MAN_GAIN_SET = 0x05
BTP_AICS_CMD_AUTO_GAIN_SET = 0x06
BTP_AICS_CMD_SET_MAN_GAIN_ONLY = 0x07
BTP_AICS_CMD_SET_AUTO_GAIN_ONLY = 0x08
BTP_AICS_CMD_AUDIO_DESC_SET = 0x09
BTP_AICS_CMD_MUTE_DISABLE = 0x0a
BTP_AICS_CMD_GAIN_SETTING_PROP_GET = 0x0b
BTP_AICS_CMD_TYPE_GET = 0x0c
BTP_AICS_CMD_STATUS_GET = 0x0d
BTP_AICS_CMD_STATE_GET = 0x0e
BTP_AICS_CMD_DESCRIPTION_GET = 0x0f
BTP_AICS_EV_STATE = 0x80
BTP_AICS_EV_GAIN_SETTING_PROP = 0x81
BTP_AICS_EV_INPUT_TYPE = 0x82
BTP_AICS_EV_STATUS = 0x83
BTP_AICS_EV_DESCRIPTION = 0x84
BTP_AICS_EV_PROCEDURE = 0x85

BTP_VOCS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_VOCS_CMD_UPDATE_AUDIO_LOC = 0x02
BTP_VOCS_CMD_UPDATE_OUT_DESC = 0x03
BTP_VOCS_CMD_OFFSET_STATE_GET = 0x04
BTP_VOCS_CMD_AUDIO_LOC_GET = 0x05
BTP_VOCS_CMD_OFFSET_STATE_SET = 0x06
BTP_VOCS_EV_OFFSET = 0x80
BTP_VOCS_EV_AUDIO_LOC = 0x81
BTP_VOCS_EV_PROCEDURE = 0x82

BTP_PACS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_PACS_CMD_UPDATE_CHARACTERISTIC = 0x02
BTP_PACS_CMD_SET_LOCATION = 0x03
BTP_PACS_CMD_SET_AVAILABLE_CONTEXTS = 0x04
BTP_PACS_CMD_SET_SUPPORTED_CONTEXTS = 0x05

PACS_CHARACTERISTIC_SINK_PAC = 0x01
PACS_CHARACTERISTIC_SOURCE_PAC = 0x02
PACS_CHARACTERISTIC_SINK_AUDIO_LOCATIONS = 0x03
PACS_CHARACTERISTIC_SOURCE_AUDIO_LOCATIONS = 0x04
PACS_CHARACTERISTIC_AVAILABLE_AUDIO_CONTEXTS = 0x05
PACS_CHARACTERISTIC_SUPPORTED_AUDIO_CONTEXTS = 0x06
BTP_PACS_EV_CHARACTERISTIC_SUBSCRIBED = 0x80

PACS_AUDIO_DIR_SINK = 0x01
PACS_AUDIO_DIR_SOURCE = 0x02

PACS_AUDIO_LOCATION_PROHIBITED = 0x00000000
PACS_AUDIO_LOCATION_FRONT_LEFT = 0x00000001
PACS_AUDIO_LOCATION_FRONT_RIGHT = 0x00000002
PACS_AUDIO_LOCATION_FRONT_CENTER = 0x00000004
PACS_AUDIO_LOCATION_LOW_FREQ_EFFECTS_1 = 0x00000008
PACS_AUDIO_LOCATION_BACK_LEFT = 0x00000010
PACS_AUDIO_LOCATION_BACK_RIGHT = 0x00000020
PACS_AUDIO_LOCATION_FRONT_LEFT_OF_CENTER = 0x00000040
PACS_AUDIO_LOCATION_FRONT_RIGHT_OF_CENTER = 0x00000080
PACS_AUDIO_LOCATION_BACK_CENTER = 0x00000100
PACS_AUDIO_LOCATION_LOW_FREQ_EFFECTS_2 = 0x00000200
PACS_AUDIO_LOCATION_SIDE_LEFT = 0x00000400
PACS_AUDIO_LOCATION_SIDE_RIGHT = 0x00000800
PACS_AUDIO_LOCATION_TOP_FRONT_LEFT = 0x00001000
PACS_AUDIO_LOCATION_TOP_FRONT_RIGHT = 0x00002000
PACS_AUDIO_LOCATION_TOP_FRONT_CENTER = 0x00004000
PACS_AUDIO_LOCATION_TOP_CENTER = 0x00008000
PACS_AUDIO_LOCATION_TOP_BACK_LEFT = 0x00010000
PACS_AUDIO_LOCATION_TOP_BACK_RIGHT = 0x00020000
PACS_AUDIO_LOCATION_TOP_SIDE_LEFT = 0x00040000
PACS_AUDIO_LOCATION_TOP_SIDE_RIGHT = 0x00080000
PACS_AUDIO_LOCATION_TOP_BACK_CENTER = 0x00100000
PACS_AUDIO_LOCATION_BOTTOM_FRONT_CENTER = 0x00200000
PACS_AUDIO_LOCATION_BOTTOM_FRONT_LEFT = 0x00400000
PACS_AUDIO_LOCATION_BOTTOM_FRONT_RIGHT = 0x00800000
PACS_AUDIO_LOCATION_FRONT_LEFT_WIDE = 0x01000000
PACS_AUDIO_LOCATION_FRONT_RIGHT_WIDE = 0x02000000
PACS_AUDIO_LOCATION_LEFT_SURROUND = 0x04000000
PACS_AUDIO_LOCATION_RIGHT_SURROUND = 0x08000000

PACS_AUDIO_CONTEXT_TYPE_PROHIBITED = 0
PACS_AUDIO_CONTEXT_TYPE_UNSPECIFIED = BIT(0)
PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL = BIT(1)
PACS_AUDIO_CONTEXT_TYPE_MEDIA = BIT(2)
PACS_AUDIO_CONTEXT_TYPE_GAME = BIT(3)
PACS_AUDIO_CONTEXT_TYPE_INSTRUCTIONAL = BIT(4)
PACS_AUDIO_CONTEXT_TYPE_VOICE_ASSISTANTS = BIT(5)
PACS_AUDIO_CONTEXT_TYPE_LIVE = BIT(6)
PACS_AUDIO_CONTEXT_TYPE_SOUND_EFFECTS = BIT(7)
PACS_AUDIO_CONTEXT_TYPE_NOTIFICATIONS = BIT(8)
PACS_AUDIO_CONTEXT_TYPE_RINGTONE = BIT(9)
PACS_AUDIO_CONTEXT_TYPE_ALERTS = BIT(10)
PACS_AUDIO_CONTEXT_TYPE_EMERGENCY_ALARM = BIT(11)

AUDIO_METADATA_TYPE_PREFERRED_AUDIO_CONTEXTS = 0x01
AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS = 0x02
AUDIO_METADATA_PROGRAM_INFO = 0x03
AUDIO_METADATA_LANGUAGE = 0x04
AUDIO_METADATA_CCID_LIST = 0x05
AUDIO_METADATA_PARENTAL_RATING = 0x06
AUDIO_METADATA_PROGRAM_INFO_URI = 0x07
AUDIO_METADATA_AUDIO_ACTIVE_STATE = 0x08
AUDIO_METADATA_BRCST_IMM_REND_FLAG = 0x09
AUDIO_METADATA_EXTENDED_METADATA = 0xFE
AUDIO_METADATA_VENDOR_SPECIFIC = 0xFF

BTP_ASCS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_ASCS_CMD_CONFIGURE_CODEC = 0x02
BTP_ASCS_CMD_CONFIGURE_QOS = 0x03
BTP_ASCS_CMD_ENABLE = 0x04
BTP_ASCS_CMD_RECEIVER_START_READY = 0x05
BTP_ASCS_CMD_RECEIVER_STOP_READY = 0x06
BTP_ASCS_CMD_DISABLE = 0x07
BTP_ASCS_CMD_RELEASE = 0x08
BTP_ASCS_CMD_UPDATE_METADATA = 0x09
BTP_ASCS_CMD_ADD_ASE_TO_CIS = 0x0a
BTP_ASCS_CMD_PRECONFIG_QOS = 0x0b
BTP_ASCS_EV_OPERATION_COMPLETED = 0x80
BTP_ASCS_EV_CHARACTERISTIC_SUBSCRIBED = 0x81
BTP_ASCS_EV_ASE_STATE_CHANGED = 0x82

BTP_BAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_BAP_CMD_DISCOVER = 0x02
BTP_BAP_CMD_SEND = 0x03
BTP_BAP_CMD_BROADCAST_SOURCE_SETUP = 0x04
BTP_BAP_CMD_BROADCAST_SOURCE_RELEASE = 0x05
BTP_BAP_CMD_BROADCAST_ADV_START = 0x06
BTP_BAP_CMD_BROADCAST_ADV_STOP = 0x07
BTP_BAP_CMD_BROADCAST_SOURCE_START = 0x08
BTP_BAP_CMD_BROADCAST_SOURCE_STOP = 0x09
BTP_BAP_CMD_BROADCAST_SINK_SETUP = 0x0a
BTP_BAP_CMD_BROADCAST_SINK_RELEASE = 0x0b
BTP_BAP_CMD_BROADCAST_SCAN_START = 0x0c
BTP_BAP_CMD_BROADCAST_SCAN_STOP = 0x0d
BTP_BAP_CMD_BROADCAST_SINK_SYNC = 0x0e
BTP_BAP_CMD_BROADCAST_SINK_STOP = 0x0f
BTP_BAP_CMD_BROADCAST_SINK_BIS_SYNC = 0x10
BTP_BAP_CMD_DISCOVER_SCAN_DELEGATOR = 0x11
BTP_BAP_CMD_BROADCAST_ASSISTANT_SCAN_START = 0x12
BTP_BAP_CMD_BROADCAST_ASSISTANT_SCAN_STOP = 0x13
BTP_BAP_CMD_ADD_BROADCAST_SRC = 0x14
BTP_BAP_CMD_REMOVE_BROADCAST_SRC = 0x15
BTP_BAP_CMD_MODIFY_BROADCAST_SRC = 0x16
BTP_BAP_CMD_SET_BROADCAST_CODE = 0x17
BTP_BAP_CMD_SEND_PAST = 0x18
BTP_BAP_CMD_BROADCAST_SOURCE_SETUP_V2 = 0x19
BTP_BAP_EV_DISCOVERY_COMPLETED = 0x80
BTP_BAP_EV_CODEC_CAP_FOUND = 0x81
BTP_BAP_EV_ASE_FOUND = 0x82
BTP_BAP_EV_STREAM_RECEIVED = 0x83
BTP_BAP_EV_BAA_FOUND = 0x84
BTP_BAP_EV_BIS_FOUND = 0x85
BTP_BAP_EV_BIS_SYNCED = 0x86
BTP_BAP_EV_BIS_STREAM_RECEIVED = 0x87
BTP_BAP_EV_SCAN_DELEGATOR_FOUND = 0x88
BTP_BAP_EV_BROADCAST_RECEIVE_STATE = 0x89
BTP_BAP_EV_PA_SYNC_REQ = 0x8a

BTP_HAS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_HAS_CMD_SET_ACTIVE_INDEX = 0x02
BTP_HAS_CMD_SET_PRESET_NAME = 0x03
BTP_HAS_CMD_REMOVE_PRESET = 0x04
BTP_HAS_CMD_ADD_PRESET = 0x05
BTP_HAS_CMD_SET_PROPERTIES = 0x06
HAS_TSPX_available_presets_indices = [1,2,4]
HAS_TSPX_unavailable_presets_indices = [3]
HAS_TSPX_writable_preset_indices = [1,2]
HAS_TSPX_unwritable_preset_indices = [4]

BTP_CSIS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CSIS_CMD_SET_MEMBER_LOCK = 0x02
BTP_CSIS_CMD_GET_MEMBER_RSI = 0x03
BTP_CSIS_CMD_SET_SIRK_TYPE = 0x04

BTP_MICP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_MICP_CMD_DISCOVERY = 0x02
BTP_MICP_CMD_MUTE_STATE = 0x03
BTP_MICP_CMD_MUTE = 0x04
BTP_MICP_EV_DISCOVERED = 0x80
BTP_MICP_EV_MUTE_STATE = 0x81

BTP_MICS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_MICS_CMD_MUTE_DISABLE = 0x02
BTP_MICS_CMD_MUTE_READ = 0x03
BTP_MICS_CMD_MUTE = 0x04
BTP_MICS_CMD_UNMUTE = 0x05
BTP_MICS_EV_MUTE_STATE = 0x80

BTP_CCP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CCP_CMD_DISCOVER_TBS = 0x02
BTP_CCP_CMD_ACCEPT_CALL = 0x03
BTP_CCP_CMD_TERMINATE_CALL = 0x04
BTP_CCP_CMD_ORIGINATE_CALL = 0x05
BTP_CCP_CMD_READ_CALL_STATE = 0x06
BTP_CCP_CMD_READ_BEARER_NAME = 0x07
BTP_CCP_CMD_READ_BEARER_UCI = 0x08
BTP_CCP_CMD_READ_BEARER_TECH = 0x09
BTP_CCP_CMD_READ_URI_LIST = 0x0a
BTP_CCP_CMD_READ_SIGNAL_STRENGTH = 0x0b
BTP_CCP_CMD_READ_SIGNAL_INTERVAL = 0x0c
BTP_CCP_CMD_READ_CURRENT_CALLS = 0x0d
BTP_CCP_CMD_READ_CCID = 0x0e
BTP_CCP_CMD_READ_CALL_URI = 0x0f
BTP_CCP_CMD_READ_STATUS_FLAGS = 0x10
BTP_CCP_CMD_READ_OPTIONAL_OPCODES = 0x11
BTP_CCP_CMD_READ_FRIENDLY_NAME = 0x12
BTP_CCP_CMD_READ_REMOTE_URI = 0x13
BTP_CCP_CMD_SET_SIGNAL_INTERVAL = 0x14
BTP_CCP_CMD_HOLD_CALL = 0x15
BTP_CCP_CMD_RETRIEVE_CALL = 0x16
BTP_CCP_CMD_JOIN_CALLS = 0x17
BTP_CCP_EV_DISCOVERED = 0x80
BTP_CCP_EV_CALL_STATES = 0x81
BTP_CCP_EV_CHRC_HANDLES = 0x82
BTP_CCP_EV_CHRC_VAL = 0x83
BTP_CCP_EV_CHRC_STR = 0x84
BTP_CCP_EV_CP = 0x85
BTP_CCP_EV_CURRENT_CALLS = 0x86

BTP_VCP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_VCP_CMD_DISCOVERY = 0x02
BTP_VCP_CMD_STATE_READ = 0x03
BTP_VCP_CMD_FLAGS_READ = 0x04
BTP_VCP_CMD_VOL_DOWN = 0x05
BTP_VCP_CMD_VOL_UP = 0x06
BTP_VCP_CMD_UNMUTE_VOL_DOWN = 0x07
BTP_VCP_CMD_UNMUTE_VOL_UP = 0x08
BTP_VCP_CMD_SET_VOL = 0x09
BTP_VCP_CMD_UNMUTE = 0x0a
BTP_VCP_CMD_MUTE = 0x0b
BTP_VCP_EV_DISCOVERED = 0x80
BTP_VCP_EV_STATE = 0x81
BTP_VCP_EV_FLAGS = 0x82
BTP_VCP_EV_PROCEDURE = 0x83

BTP_CAS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CAS_CMD_SET_MEMBER_LOCK = 0x02
BTP_CAS_CMD_GET_MEMBER_RSI = 0x03

BTP_MCP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_MCP_CMD_DISCOVERY = 0x02
BTP_MCP_CMD_TRACK_DURATION_READ = 0x03
BTP_MCP_CMD_TRACK_POSITION_READ = 0x04
BTP_MCP_CMD_TRACK_POSITION_SET = 0x05
BTP_MCP_CMD_PLAYBACK_SPEED_READ = 0x06
BTP_MCP_CMD_PLAYBACK_SPEED_SET = 0x07
BTP_MCP_CMD_SEEKING_SPEED_READ = 0x08
BTP_MCP_CMD_ICON_OBJ_ID_READ = 0x09
BTP_MCP_CMD_NEXT_TRACK_OBJ_ID_READ = 0x0a
BTP_MCP_CMD_NEXT_TRACK_OBJ_ID_SET = 0x0b
BTP_MCP_CMD_PARENT_GROUP_OBJ_ID_READ = 0x0c
BTP_MCP_CMD_CURRENT_GROUP_OBJ_ID_READ = 0x0d
BTP_MCP_CMD_CURRENT_GROUP_OBJ_ID_SET = 0x0e
BTP_MCP_CMD_PLAYING_ORDER_READ = 0x0f
BTP_MCP_CMD_PLAYING_ORDER_SET = 0x10
BTP_MCP_CMD_PLAYING_ORDERS_SUPPORTED_READ = 0x11
BTP_MCP_CMD_MEDIA_STATE_READ = 0x12
BTP_MCP_CMD_OPCODES_SUPPORTED_READ = 0x13
BTP_MCP_CMD_CONTENT_CONTROL_ID_READ = 0x14
BTP_MCP_CMD_SEGMENTS_OBJ_ID_READ = 0x15
BTP_MCP_CMD_CURRENT_TRACK_OBJ_ID_READ = 0x16
BTP_MCP_CMD_CURRENT_TRACK_OBJ_ID_SET = 0x17
BTP_MCP_CMD_CMD_SEND = 0x18
BTP_MCP_CMD_SCP_SEND = 0x19
BTP_MCP_EV_DISCOVERED = 0x80
BTP_MCP_EV_TRACK_DURATION = 0x81
BTP_MCP_EV_TRACK_POSITION = 0x82
BTP_MCP_EV_PLAYBACK_SPEED = 0x83
BTP_MCP_EV_SEEKING_SPEED = 0x84
BTP_MCP_EV_ICON_OBJ_ID = 0x85
BTP_MCP_EV_NEXT_TRACK_OBJ_ID = 0x86
BTP_MCP_EV_PARENT_GROUP_OBJ_ID = 0x87
BTP_MCP_EV_CURRENT_GROUP_OBJ_ID = 0x88
BTP_MCP_EV_PLAYING_ORDER = 0x89
BTP_MCP_EV_PLAYING_ORDERS_SUPPORTED = 0x8a
BTP_MCP_EV_MEDIA_STATE = 0x8b
BTP_MCP_EV_OPCODES_SUPPORTED = 0x8c
BTP_MCP_EV_CONTENT_CONTROL_ID = 0x8d
BTP_MCP_EV_SEGMENTS_OBJ_ID = 0x8e
BTP_MCP_EV_CURRENT_TRACK_OBJ_ID = 0x8f
BTP_MCP_EV_COMMAND = 0x90
BTP_MCP_EV_SEARCH = 0x91
BTP_MCP_EV_CMD_NTF = 0x92
BTP_MCP_EV_SEARCH_NTF = 0x93

BTP_BASS_CMD_READ_SUPPORTED_COMMANDS = 0x01

BTP_GMCS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_GMCS_CMD_COMMAND_SEND = 0x02
BTP_GMCS_CMD_CURRENT_TRACK_OBJ_ID_GET = 0x03
BTP_GMCS_CMD_NEXT_TRACK_OBJ_ID_GET = 0x04
BTP_GMCS_CMD_INACTIVE_STATE_SET = 0x05
BTP_GMCS_CMD_PARENT_GROUP_SET = 0x06

HAP_HA_TYPE_BINAURAL = 0x00
HAP_HA_TYPE_MONAURAL = 0x01
HAP_HA_TYPE_BANDED = 0x02

HAP_HA_OPT_PRESETS_SYNC = 0x01
HAP_HA_OPT_PRESETS_INDEPENDENT = 0x02
HAP_HA_OPT_PRESETS_DYNAMIC = 0x04
HAP_HA_OPT_PRESETS_WRITABLE = 0x08

HAP_IAC_ALERT_LEVEL_NONE = 0x00
HAP_IAC_ALERT_LEVEL_MILD = 0x01
HAP_IAC_ALERT_LEVEL_HIGH = 0x02

BTP_HAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_HAP_CMD_HA_INIT = 0x02
BTP_HAP_CMD_HARC_INIT = 0x03
BTP_HAP_CMD_HAUC_INIT = 0x04
BTP_HAP_CMD_IAC_INIT = 0x05
BTP_HAP_CMD_IAC_DISCOVER = 0x06
BTP_HAP_CMD_IAC_SET_ALERT = 0x07
BTP_HAP_CMD_HAUC_DISCOVER = 0x08
BTP_HAP_CMD_READ_PRESETS = 0x09
BTP_HAP_CMD_WRITE_PRESET_NAME = 0x0A
BTP_HAP_CMD_SET_ACTIVE_PRESET = 0x0B
BTP_HAP_CMD_SET_NEXT_PRESET = 0x0C
BTP_HAP_CMD_SET_PREVIOUS_PRESET = 0x0D
BTP_HAP_EV_IAC_DISCOVERY_COMPLETE = 0x80
BTP_HAP_EV_HAUC_DISCOVERY_COMPLETE = 0x81
BTP_HAP_EV_PRESET_READ = 0x82
BTP_HAP_EV_PRESET_CHANGED = 0x83

BTP_CAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CAP_CMD_DISCOVER = 0x02
BTP_CAP_CMD_UNICAST_SETUP_ASE = 0x03
BTP_CAP_CMD_UNICAST_AUDIO_START = 0x04
BTP_CAP_CMD_UNICAST_AUDIO_UPDATE = 0x05
BTP_CAP_CMD_UNICAST_AUDIO_STOP = 0x06
BTP_CAP_CMD_BROADCAST_SOURCE_SETUP_STREAM = 0x07
BTP_CAP_CMD_BROADCAST_SOURCE_SETUP_SUBGROUP = 0x08
BTP_CAP_CMD_BROADCAST_SOURCE_SETUP = 0x09
BTP_CAP_CMD_BROADCAST_SOURCE_RELEASE = 0x0a
BTP_CAP_CMD_BROADCAST_ADV_START = 0x0b
BTP_CAP_CMD_BROADCAST_ADV_STOP = 0x0c
BTP_CAP_CMD_BROADCAST_SOURCE_START = 0x0d
BTP_CAP_CMD_BROADCAST_SOURCE_STOP = 0x0e
BTP_CAP_CMD_BROADCAST_SOURCE_UPDATE = 0x0f

BTP_CAP_EV_DISCOVERY_COMPLETED = 0x80
BTP_CAP_EV_UNICAST_START_COMPLETED = 0x81
BTP_CAP_EV_UNICAST_STOP_COMPLETED = 0x82

CAP_UNICAST_AUDIO_START_SET_TYPE_AD_HOC = 0x00
CAP_UNICAST_AUDIO_START_SET_TYPE_CSIP = 0x01

BTP_CSIP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_CSIP_CMD_DISCOVER = 0x02
BTP_CSIP_CMD_START_ORDERED_ACCESS = 0x03
BTP_CSIP_CMD_SET_COORDINATOR_LOCK = 0x04
BTP_CSIP_CMD_SET_COORDINATOR_RELEASE = 0x05
BTP_CSIP_EV_DISCOVERED = 0x80
BTP_CSIP_EV_SIRK = 0x81
BTP_CSIP_EV_LOCK = 0x82

BTP_TBS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_TBS_CMD_REMOTE_INCOMING = 0x02
BTP_TBS_CMD_HOLD_CALL = 0x03
BTP_TBS_CMD_SET_BEARER_NAME = 0x04
BTP_TBS_CMD_SET_BEARER_TECHNOLOGY = 0x05
BTP_TBS_CMD_SET_URI_SCHEME_LIST = 0x06
BTP_TBS_CMD_SET_STATUS_FLAGS = 0x07
BTP_TBS_CMD_REMOTE_HOLD_CALL = 0x08
BTP_TBS_CMD_ORIGINATE_CALL = 0x09
BTP_TBS_CMD_SIGNAL_STRENGTH = 0x0a
BTP_TBS_CMD_TERMINATE_CALL = 0x0b

BTP_TMAP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_TMAP_CMD_DISCOVER = 0x02
BTP_TMAP_EV_DISCOVERY_COMPLETED = 0x80

BTP_OTS_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_OTS_CMD_REGISTER_OBJECT = 0x02

BTP_PBP_CMD_READ_SUPPORTED_COMMANDS = 0x01
BTP_PBP_CMD_SET_PUBLIC_BROADCAST_ANNOUNCEMENT = 0x02
BTP_PBP_CMD_SET_BROADCAST_NAME = 0x03
BTP_PBP_CMD_BROADCAST_SCAN_START = 0x04
BTP_PBP_CMD_BROADCAST_SCAN_STOP = 0x05
BTP_PBP_EV_PUBLIC_BROADCAST_ANNOUNCEMENT_FOUND = 0x80

# GENERATOR append 2
