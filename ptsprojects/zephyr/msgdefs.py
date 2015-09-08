'''BTP header message definition'''

HDR_LEN = 5

CONTROLLER_INDEX = '\x00'
BTP_INDEX_NONE = '\xff'

#Service ID dictionary
SERVICE_ID = dict(
                  SERVICE_ID_CORE = '\x00',
                  SERVICE_ID_GAP = '\x01',
                  )

#Core Service
# COMMANDS
CORE_SERVICE_OP = dict(
                       CORE_READ_SUPPORTED_COMMANDS = '\x01',
                       CORE_READ_SUPPORTED_SERVICES = '\x02',
                       CORE_REGISTER_SERVICE = '\x03',
                       )

#GAP Service
# COMMANDS
GAP_SERVICE_OP = dict(
                      GAP_READ_SUPPORTED_COMMANDS = '\x01',
                      GAP_READ_CONTROLLER_INDEX_LIST = '\x02',
                      GAP_READ_CONTROLLER_INFO = '\x03',
                      GAP_RESET = '\x04',
                      GAP_SET_POWERED = '\x05',
                      GAP_SET_CONNECTABLE = '\x06',
                      GAP_SET_FAST_CONNECTABLE = '\x07',
                      GAP_SET_DISCOVERABLE = '\x08',
                      GAP_SET_BONDABLE = '\x09',
                      GAP_START_ADVERTISING = '\x0a',
                      GAP_STOP_ADVERTISING = '\x0b',
                      )

ADV_TYPE = dict(
                ADV_IND = '\x00',
                ADV_DIRECT_IND_HD = '\x01',
                ADV_SCAN_IND = '\x02',
                ADV_NONCONN_IND = '\x03',
                ADV_DIRECT_IND_LD = '\x04',
                )

# EVENTS
GAP_SERVICE_EV = dict(
                      GAP_EV_NEW_SETTINGS = '\x80',
                      GAP_EV_DEVICE_FOUND = '\x81',
                      GAP_EV_DEVICE_CONNECTED = '\x82',
                      GAP_EV_DEVICE_DISCONNECTED = '\x83',
                      )

#Status
BTP_STATUS = '\x00'

STATUS = dict(
              STATUS_SUCCESS = '\x00',
              STATUS_FAILED = '\x01',
              STATUS_UNKNOWN_CMD = '\x02',
              STATUS_NOT_READY = '\x03',
              )
