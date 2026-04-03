#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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

import autopts.wid.bap
from autopts.ptsprojects.bluez.iutctl import get_iut
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def bap_wid_hdl(wid, description, test_case_name):
    log(f'{bap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.bap'])


def hdl_wid_302(params: WIDParams):
    """
    Please configure ASE state to CODEC configured with SINK/SOURCE ASE,
    Freq: X KHz, Frame Duration: X ms
    """

    if get_iut().external_audio is not None:
        logging.debug("External audio supported, skipping WID 302 handling")
        return True

    return autopts.wid.bap.hdl_wid_302(params)
