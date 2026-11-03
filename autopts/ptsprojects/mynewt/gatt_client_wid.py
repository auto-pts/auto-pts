#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
from autopts.ptsprojects.testcase import MMI
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

log = logging.debug


def hdl_wid_24(params: WIDParams):
    """
    Please confirm IUT received include services:
        Attribute Handle = '0002'O
        Included Service Attribute handle = '0080'O,
        End Group Handle = '0085'O,
        Service UUID = 'A00B'O
        Attribute Handle = '0021'O
        Included Service Attribute handle = '0001'O,
        End Group Handle = '0006'O,
        Service UUID = 'A00D'O
        Attribute Handle = '0091'O
        Included Service Attribute handle = '0001'O
        End Group Handle = '0006'O,
        Service UUID = 'A00D'O

    Click Yes if IUT received it, otherwise click No.

    Description: Verify that the Implementation Under Test (IUT) can send
    Discover all include services in database.
    """
    MMI.reset()
    MMI.parse_description(params.description)

    if not MMI.args:
        return False

    # split MMI args into tuples (att_hdl, incl_svc_hdl, end_gp_hdl, svc_uuid)
    mmi_args_tupled = [
        tuple(MMI.args[i:i + 4]) for i in range(0, len(MMI.args), 4)
    ]

    stack = get_stack()
    # TODO: there is no way to access included service handle wit current API.
    #  For now, we skip this value when comparing find included services results
    #  with description
    incl_svcs = [tup[1:] for tup in stack.gatt_cl.incl_svcs]
    mmi_args = [tup[1:] for tup in mmi_args_tupled]

    return set(incl_svcs).issubset(set(mmi_args))


def hdl_wid_142(_: WIDParams):
    """
    Please send an ATT_Write_Request to Client Support Features handle = '0015'O with 0x02 to enable Enhanced ATT.

    Discover all characteristics if needed.
    """

    btp.gap_pair()

    return True


def hdl_wid_400(_: WIDParams):

    return True


def hdl_wid_402(_: WIDParams):
    """Please initiate an L2CAP Credit Based Connection using LE signaling channel to the PTS."""

    return True
