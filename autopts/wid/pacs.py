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
import sys

from autopts.pybtp import btp
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams

log = logging.debug
pacs_update_fun = None


def pacs_wid_hdl(wid, description, test_case_name, logs=True):
    if logs:
        log(f'{pacs_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    module = sys.modules[__name__]

    try:
        handler = getattr(module, f'hdl_wid_{wid}')
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError as e:
        logging.exception(e)


# wid handlers section begin
def hdl_wid_1(_: WIDParams):
    btp.pacs_update_sink_pac()
    return True


def hdl_wid_2(_: WIDParams):
    btp.pacs_update_source_pac()
    return True


def hdl_wid_3(_: WIDParams):
    btp.pacs_update_sink_audio_locations()
    return True


def hdl_wid_4(_: WIDParams):
    btp.pacs_update_source_audio_locations()
    return True


def hdl_wid_5(_: WIDParams):
    btp.pacs_update_available_audio_contexts()
    return True


def hdl_wid_6(_: WIDParams):
    btp.pacs_update_supported_audio_contexts()
    return True


def hdl_wid_7(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_sink_pac
    return True


def hdl_wid_8(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_source_pac
    return True


def hdl_wid_9(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_sink_audio_locations
    return True


def hdl_wid_10(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_source_audio_locations
    return True


def hdl_wid_11(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_available_audio_contexts
    return True


def hdl_wid_12(_: WIDParams):
    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_supported_audio_contexts
    return True


def hdl_wid_13(_: WIDParams):
    return True


def hdl_wid_14(_: WIDParams):
    return True


def hdl_wid_20001(_: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)
    return True


def hdl_wid_20108(_: WIDParams):
    pacs_update_fun()
    return True
