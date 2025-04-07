#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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
import struct
import sys

from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams
from autopts.wid.micp import micp_wid_hdl as gen_wid_hdl


log = logging.debug


def micp_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", micp_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)
