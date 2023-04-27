#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2022, Codecoup Corporation.
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
import sys

from autopts.pybtp import btp
from autopts.pybtp.types import UUID
from autopts.wid.vocs import vocs_wid_hdl as gen_wid_hdl

log = logging.debug


def vocs_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", vocs_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]
    wid_str = f'hdl_wid_{wid}'

    if hasattr(module, wid_str):
        handler = getattr(module, wid_str)
        return handler(description)
    else:
        return gen_wid_hdl(wid, description, test_case_name, False)
