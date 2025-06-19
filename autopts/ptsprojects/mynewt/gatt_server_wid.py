#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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
from autopts.wid import generic_wid_hdl

log = logging.debug


def gatt_sr_wid_hdl(wid, description, test_case_name):
    log(f'{gatt_sr_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    stack = get_stack()
    if stack.is_svc_supported('GATTS') and 'GATT/SR' in test_case_name:
        return generic_wid_hdl(wid,
                               description,
                               test_case_name,
                               [__name__, 'autopts.wid.gatt_server',
                                'autopts.wid.gatt'])
    return generic_wid_hdl(wid,
                           description,
                           test_case_name,
                           ['autopts.ptsprojects.mynewt.gatt_wid',
                            'autopts.wid.gatt'])
