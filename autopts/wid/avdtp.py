#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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
from autopts.wid import generic_wid_hdl

log = logging.debug


def avdtp_wid_hdl(wid, description, test_case_name):
    log(f'{avdtp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(params: WIDParams):
    # Example WID

    return True


def hdl_wid_14(_: WIDParams):
    """
    description: Take action to initiate an AVDTP media transport.
    """
    return True


def hdl_wid_18(_: WIDParams):
    """
    description: Take action to reject the invalid CLOSE command sent by the tester.
    """
    return True


def hdl_wid_19(_: WIDParams):
    """
    description: Please wait while the tester verifies that the IUT does not respond to the invalid DISCOVER
    command sent by the tester.
    """
    return True


def hdl_wid_20(_: WIDParams):
    """
    description: Take action to reject the invalid GET ALL CAPABILITIES command with the error code BAD_LENGTH.
    """
    return True


def hdl_wid_21(_: WIDParams):
    """
    description: Take action to reject the invalid GET CAPABILITIES command with the error code BAD_LENGTH.
    """
    return True


def hdl_wid_22(_: WIDParams):
    """
    description: Take action to reject the GET CONFIGURATION sent by the tester.  The IUT is expected to
    respond with BAD_ACP_SEID because the SEID requested was not previously configured.
    """
    return True


def hdl_wid_23(_: WIDParams):
    """
    description: Take action to reject the invalid command sent by the tester.
    """
    return True


def hdl_wid_24(_: WIDParams):
    """
    description: Take action to reject the invalid OPEN command sent by the tester.
    """
    return True


def hdl_wid_25(_: WIDParams):
    """
    description: Take action to reject the invalid or incompatible RECONFIGURE command sent by the tester.
    """
    return True


def hdl_wid_26(_: WIDParams):
    """
    description: Take action to reject the SET CONFIGURATION sent by the tester.  The IUT is expected to
    respond with SEP_IN_USE because the SEP requested was previously configured.
    """
    return True


def hdl_wid_27(_: WIDParams):
    """
    description: Take action to reject the invalid START command sent by the tester.
    """
    return True


def hdl_wid_28(_: WIDParams):
    """
    description: Take action to reject the invalid SUSPEND command sent by the tester.
    """
    return True


def hdl_wid_29(_: WIDParams):
    """
    description: Did the IUT receive media with the following information?
    """
    return True


def hdl_wid_30(_: WIDParams):
    """
    description: Were all the service capabilities reported to the upper tester valid?
    """
    return True


def hdl_wid_52(_: WIDParams):
    """
    description: Did the IUT successfully discard the invalid DISCOVER command sent by the tester?
    """
    return True


def hdl_wid_1000(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Abort operation initiated by the tester.
    """
    return True


def hdl_wid_1001(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Close operation initiated by the tester.
    """
    return True


def hdl_wid_1002(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Signaling Channel Connection initiated by the tester.
    """
    return True


def hdl_wid_1004(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Discover operation initiated by the tester.
    """
    return True


def hdl_wid_1005(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Get Capabilities operation initiated by the tester.
    """
    return True


def hdl_wid_1006(params: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Open operation initiated by the tester.
    """
    return True


def hdl_wid_1007(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Reconfigure operation initiated by the tester.
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


def hdl_wid_1014(_: WIDParams):
    """
    description: Send an abort command to PTS.
    """
    btp.a2dp_stream_abort()
    btp.a2dp_wait_for_aborted()
    return True


def hdl_wid_1015(_: WIDParams):
    """
    description: Close the streaming channel.
    """
    btp.a2dp_stream_release()
    btp.a2dp_wait_for_stream_released()
    return True


def hdl_wid_1018(_: WIDParams):
    """
    description: Send a discover command to PTS.
    """
    btp.a2dp_discover()
    btp.a2dp_wait_for_discovered()
    return True


def hdl_wid_1019(_: WIDParams):
    """
    description: Send a get capabilities command to PTS.
    """
    btp.a2dp_discover()
    btp.a2dp_wait_for_discovered()
    btp.a2dp_get_capabilities()
    btp.a2dp_wait_for_get_capabilities_finished()
    return True


def hdl_wid_1020(params: WIDParams):
    """
    description: Open a streaming media channel.
    """
    if params.test_case_name in ['AVDTP/SNK/INT/SIG/SMG/BV-33-C',
                                'AVDTP/SNK/INT/SIG/SMG/BV-13-C',
                                'AVDTP/SRC/INT/SIG/SMG/BV-13-C',
                                'AVDTP/SRC/INT/SIG/SMG/BV-33-C']:
        btp.a2dp_stream_establish()
        btp.a2dp_wait_for_stream_state(expected_state='established')
        if params.test_case_name in ['AVDTP/SNK/INT/SIG/SMG/BV-33-C',
                                    'AVDTP/SRC/INT/SIG/SMG/BV-33-C']:
            btp.a2dp_stream_start()
            btp.a2dp_wait_for_stream_state(expected_state='started')
        return True
    btp.a2dp_discover()
    btp.a2dp_wait_for_discovered()

    btp.a2dp_get_all_capabilities()
    btp.a2dp_wait_for_get_capabilities_finished()
    btp.a2dp_stream_config()
    btp.a2dp_wait_for_stream_state(expected_state='configured')
    btp.a2dp_stream_establish()
    btp.a2dp_wait_for_stream_state(expected_state='established')
    return True


def hdl_wid_1030(params: WIDParams):
    """
    description: Send a reconfigure command to PTS.
    """
    if params.test_case_name in ['AVDTP/SNK/INT/SIG/SMG/BV-33-C', 'AVDTP/SRC/INT/SIG/SMG/BV-33-C',
                                 ]:
        btp.a2dp_stream_suspend()
        btp.a2dp_wait_for_stream_state(expected_state='suspended', timeout=10)
    btp.a2dp_stream_reconfig()
    btp.a2dp_wait_for_stream_state(expected_state='configured')
    return True


def hdl_wid_1031(params: WIDParams):
    """
    description: Send a set configuration command to PTS.
    """
    if params.test_case_name in ['AVDTP/SNK/INT/SIG/SMG/BV-09-C', 'AVDTP/SRC/INT/SIG/SMG/BV-09-C',
                                 'AVDTP/SRC/INT/SIG/SMG/BV-23-C', 'AVDTP/SNK/INT/SIG/SMG/BV-23-C',
                                 ]:
        btp.a2dp_discover()
        btp.a2dp_wait_for_discovered()

        btp.a2dp_get_all_capabilities()
        btp.a2dp_wait_for_get_capabilities_finished()

    btp.a2dp_stream_config()
    btp.a2dp_wait_for_stream_state(expected_state='configured')
    return True


def hdl_wid_1032(params: WIDParams):
    """
    description: Send a start command to PTS.
    """
    if params.test_case_name in ['AVDTP/SNK/INT/SIG/SMG/BV-13-C',
                                 'AVDTP/SRC/INT/SIG/SMG/BV-13-C']:
        btp.a2dp_stream_start()
        btp.a2dp_wait_for_stream_state(expected_state='started')
        return True

    btp.a2dp_discover()
    btp.a2dp_wait_for_discovered()

    btp.a2dp_get_all_capabilities()
    btp.a2dp_wait_for_get_capabilities_finished()
    btp.a2dp_stream_config()
    btp.a2dp_wait_for_stream_state(expected_state='configured')
    btp.a2dp_stream_establish()
    btp.a2dp_wait_for_stream_state(expected_state='established')
    btp.a2dp_stream_start()
    btp.a2dp_wait_for_stream_state(expected_state='started')
    return True


def hdl_wid_1033(_: WIDParams):
    """
    description: Stream media to PTS.  If the IUT is a SNK, wait for PTS to start streaming media.
    """
    return True


def hdl_wid_1034(_: WIDParams):
    """
    description: Suspend the streaming channel.
    """
    btp.a2dp_stream_suspend()
    btp.a2dp_wait_for_stream_state(expected_state='suspended')
    return True


def hdl_wid_1035(_: WIDParams):
    """
    description: Send a GET ALL CAPABILITIES command to PTS.
    """
    btp.a2dp_discover()
    btp.a2dp_wait_for_discovered()
    btp.a2dp_get_all_capabilities()
    btp.a2dp_wait_for_get_capabilities_finished()
    return True


def hdl_wid_1036(_: WIDParams):
    """
    description: Take action if necessary to start streaming media to the tester.
    """
    return True


def hdl_wid_1037(_: WIDParams):
    """
    description: If necessary, take action to accept the AVDTP Get All Capabilities operation initiated by the tester.
    """
    return True


def hdl_wid_1038(_: WIDParams):
    """
    description: Please wait while the tester verifies the IUT does not send media during suspend ...
    """
    return True


def hdl_wid_1040(_: WIDParams):
    """
    description: Take action to accept the AVDTP Get Configuration command from the tester.
    """
    return True


def hdl_wid_1041(_: WIDParams):
    """
    description: Take action to initiate an AVDTP Get Configuration command.
    """
    btp.a2dp_stream_get_config()
    btp.a2dp_wait_for_stream_state(expected_state='get_configured')
    return True


def hdl_wid_1042(_: WIDParams):
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


def hdl_wid_1047(_: WIDParams):
    """
    description: Action: Place the IUT in connectable mode.
    """
    btp.gap_set_conn()
    btp.gap_set_gendiscov()
    return True
