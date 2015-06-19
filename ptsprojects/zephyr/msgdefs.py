'''BTP header message definition'''

HDR_LEN = 4

#Service ID dictionary
SERVICE_ID = dict(SERVICE_ID_CORE = '\x00', SERVICE_ID_GAP = '\x01')

#Core Service
CORE_SERVICE_OP = dict(OP_STATUS = '\x00', OP_REGISTER_SERVICE = '\x01')

#GAP Service
GAP_SERVICE_OP = dict(OP_STATUS = '\x00')

#Status
STATUS = dict(STATUS_SUCCESS = '\x00', STATUS_FAILED = '\x01', STATUS_UNKNOWN_CMD = '\x02',
              STATUS_NOT_READY = '\x03')
