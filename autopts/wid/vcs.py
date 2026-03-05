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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


# wid handlers section begin
def hdl_wid_20001(params: WIDParams):
    stack = get_stack()
    btp.gap_set_conn()
    btp.gap_adv_ind_on(ad=stack.gap.ad)

    delayed_vcs_reg_tc = [
        'VCS/SR/CP/BV-01-C',
        'VCS/SR/CP/BV-02-C',
        'VCS/SR/CP/BV-03-C',
        'VCS/SR/CP/BV-04-C',
    ]

    if params.test_case_name not in delayed_vcs_reg_tc:
        btp.vcs_register(1, False, 100)

    return True


def hdl_wid_1(params: WIDParams):

    if params.test_case_name == 'VCS/SR/CP/BV-01-C':
        btp.vcs_register(1, False, 2)
    else:
        btp.vcs_set_vol(2)
    return True


def hdl_wid_2(params: WIDParams):
    if params.test_case_name == 'VCS/SR/CP/BV-03-C':
        btp.vcs_register(1, True, 2)
    else:
        btp.vcs_set_vol(2)
        btp.vcs_mute()
    return True


def hdl_wid_3(params: WIDParams):
    if params.test_case_name == 'VCS/SR/CP/BV-02-C':
        btp.vcs_register(1, False, 255 - 2)
    else:
        btp.vcs_set_vol(255 - 2)
    return True


def hdl_wid_4(params: WIDParams):
    if params.test_case_name == 'VCS/SR/CP/BV-04-C':
        btp.vcs_register(1, True, 255 - 2)
    else:
        btp.vcs_set_vol(255 - 2)
        btp.vcs_mute()
    return True
