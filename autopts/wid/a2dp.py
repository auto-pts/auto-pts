#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, nxp.
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

from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def a2dp_wid_hdl(wid, description, test_case_name):
    log(f'{a2dp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(params: WIDParams):
    # Example WID

    return True


def hdl_wid_6(params: WIDParams):
    """
    description: Is the delay value 1, within a device acceptable range?
    """
    return True


def hdl_wid_9(_: WIDParams):
    """
    Take action if necessary to initiate a Delay Reporting command.
    """
    return True


def hdl_wid_12(_: WIDParams):
    """
    description: Delete the link key with PTS on the Implementation Under Test (IUT), and then click OK to continue.
    """
    btp.gap_unpair()
    return True


def hdl_wid_13(_: WIDParams):
    """
    description: Is the IUT capable of establishing connection to an unpaired device?
    """
    return True


def hdl_wid_15(params: WIDParams):
    """
    description: Please prepare the IUT to reject an AVDTP SET CONFIGURATION command
    with error code NOT_SUPPORTED_CODEC_TYPE, then press 'OK' to continue.
    """
    return True


def hdl_wid_33(params: WIDParams):
    """
    description: Please make IUT general discoverable.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True


def hdl_wid_102(_: WIDParams):
    """
    description: Please send an HCI connect request to establish a basic rate connection
    after the IUT discovers the Lower Tester over BR and LE.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    return True


def hdl_wid_1001(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Close operation initiated by the tester.
    """
    return True


def hdl_wid_1002(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Signaling Channel Connection initiated by the tester.
    """
    return True


def hdl_wid_1004(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Discover operation initiated by the tester.
    """
    return True


def hdl_wid_1006(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Open operation initiated by the tester.
    """
    return True


def hdl_wid_1009(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Set Configuration operation initiated by the tester.
    """
    return True


def hdl_wid_1010(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Start operation initiated by the tester.
    """
    return True


def hdl_wid_1012(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Suspend operation initiated by the tester.
    """
    return True


def hdl_wid_1013(_: WIDParams):
    """
    description: Is the IUT (Implementation Under Test) receiving streaming media from PTS?
    """
    return True


def hdl_wid_1015(_: WIDParams):
    """
    description: Close the streaming channel.
    """
    btp.a2dp_release()
    return True


def hdl_wid_1016(params: WIDParams):
    """
    description: Create an AVDTP signaling channel.
    """
    btp.a2dp_connect()
    return True


def hdl_wid_1020(params: WIDParams):
    """
    description: Open a streaming media channel.
    """
    if btp.a2dp_get_mmi_round(1020) == 0:
        btp.a2dp_discover()
        btp.a2dp_configure()
        btp.a2dp_establish()
        btp.a2dp_increase_mmi_round(1020)

    return True


def hdl_wid_1029(params: WIDParams):
    """
    description: Move the IUT out of range to create a link loss scenario.
    """
    btp.a2dp_release()
    btp.gap_disconn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    return True


def hdl_wid_1032(params: WIDParams):
    """
    description: Send a start command to PTS.
    """
    if params.test_case_name in ['A2DP/SNK/SYN/BV-01-C']:
        btp.a2dp_send_delay_report(1)
        return True
    if params.test_case_name in ['A2DP/SNK/SET/BV-04-C', 'A2DP/SRC/SET/BV-03-C',
                                 'A2DP/SRC/SET/BV-05-C', 'A2DP/SNK/SET/BV-06-C',
                                 'A2DP/SRC/SET/BV-04-C', 'A2DP/SNK/SET/BV-02-C',
                                ]:
        btp.a2dp_discover()
        btp.a2dp_configure()
        btp.a2dp_establish()
    btp.a2dp_start()
    return True


def hdl_wid_1034(params: WIDParams):
    """
    description: Suspend the streaming channel.
    """
    btp.a2dp_suspend()

    return True


def hdl_wid_1037(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Get All Capabilities operation initiated by the tester.
    """
    return True


def hdl_wid_1042(params: WIDParams):
    """
    description: Take action to accept transport channels for the recently configured media stream.
    """
    return True


def hdl_wid_1043(_: WIDParams):
    """
    description: Is the test system properly playing back the media being sent by the IUT?
    """
    return True


def hdl_wid_1046(_: WIDParams):
    """
    description: Begin streaming media ...
    """
    return True


def hdl_wid_20000(params: WIDParams):
    """
    description: Please prepare IUT into a connectable mode in BR/EDR.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True
