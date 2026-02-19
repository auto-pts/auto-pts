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

import logging

from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


def hdl_wid_104(_: WIDParams):
    return True


def hdl_wid_114(_: WIDParams):
    return True


def hdl_wid_118(params: WIDParams):
    """
    Please press ok to disconnect the link.
    """

    # Directed connection test cases with privacy needs to
    # make sure that Central Address Resolution attribute is
    # received.
    if params.test_case_name in ['GAP/CONN/DCON/BV-04-C',
                                 'GAP/CONN/DCON/BV-05-C']:
        return btp.gap_wait_for_car_receive()

    return True


def hdl_wid_162(_: WIDParams):
    return True


def hdl_wid_224(_: WIDParams):
    return True
