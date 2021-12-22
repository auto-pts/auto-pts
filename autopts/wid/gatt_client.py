#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

from binascii import hexlify
from random import randint
from time import sleep
import logging
import re
import socket
import struct
import sys

from pybtp import btp
from pybtp.types import Prop, Perm, IOCap, UUID, WIDParams
from ptsprojects.testcase import MMI
from ptsprojects.stack import get_stack, GattPrimary, GattService, GattSecondary, GattServiceIncluded, \
    GattCharacteristic, GattCharacteristicDescriptor, GattDB

log = logging.debug

indication_subbed_already = False


def gatt_cl_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log("%s, %r, %r, %s", gatt_cl_wid_hdl.__name__, wid, description,
            test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


# wid handlers section begin