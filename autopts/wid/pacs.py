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

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.defs import PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL, PACS_AUDIO_CONTEXT_TYPE_MEDIA
from autopts.pybtp.types import WIDParams

log = logging.debug
pacs_update_fun = None


def pacs_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{pacs_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(_: WIDParams):
    """
    Please update Sink PAC characteristic value (Handle 0x0026), and send notification.
    """

    btp.pacs_update_sink_pac()
    return True


def hdl_wid_2(_: WIDParams):
    """
    Please update Source PAC characteristic value (Handle 0x002C), and send notification.
    """

    btp.pacs_update_source_pac()
    return True


def hdl_wid_3(_: WIDParams):
    """
    Please update Sink Audio Locations characteristic value (Handle 0x0029), and send notification.
    """

    btp.pacs_update_sink_audio_locations()
    return True


def hdl_wid_4(_: WIDParams):
    """
    Please update Source Audio Locations characteristic value (Handle 0x002F), and send notification.
    """

    btp.pacs_update_source_audio_locations()
    return True


def hdl_wid_5(_: WIDParams):
    """
    Please update Available Audio Contexts characteristic value (Handle 0x0032), and send notification.
    """

    btp.pacs_update_available_audio_contexts()
    return True


def hdl_wid_6(_: WIDParams):
    """
    Please update Supported Audio Contexts characteristic value (Handle 0x0035), and send notification.
    """

    btp.pacs_set_supported_contexts(PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                                    PACS_AUDIO_CONTEXT_TYPE_MEDIA)
    return True


def hdl_wid_7(_: WIDParams):
    """
    Please update Sink PAC characteristic value (Handle 0x0026),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_sink_pac
    return True


def hdl_wid_8(_: WIDParams):
    """
    Please update Source PAC characteristic value (Handle 0x002C),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_source_pac
    return True


def hdl_wid_9(_: WIDParams):
    """
    Please update Sink Audio Locations characteristic value (Handle 0x0029),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_sink_audio_locations
    return True


def hdl_wid_10(_: WIDParams):
    """
    Please update Source Audio Locations characteristic value (Handle 0x002F),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_source_audio_locations
    return True


def hdl_wid_11(_: WIDParams):
    """
    Please update Available Audio Contexts characteristic value (Handle 0x0032),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun

    def pacs_update_fun():
        btp.pacs_set_available_contexts(
            PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
            PACS_AUDIO_CONTEXT_TYPE_MEDIA
        )

    return True


def hdl_wid_12(_: WIDParams):
    """
    Please update Supported Audio Contexts characteristic value (Handle 0x0035),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun

    def pacs_update_fun():
        btp.pacs_set_supported_contexts(
            PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
            PACS_AUDIO_CONTEXT_TYPE_MEDIA
        )

    return True


def hdl_wid_13(_: WIDParams):
    """
    Wait for Sink Audio Locations characteristic notification value (Handle 0x0029).
    """

    return True


def hdl_wid_14(_: WIDParams):
    """
    Wait for Source Audio Locations characteristic notification value (Handle 0x002F).
    """

    return True


def hdl_wid_35(_: WIDParams):
    """
    Please update Sink PAC V2 characteristic value (Handle 0x0026),
    and expect to receive a notification after reconnection.
    """

    global pacs_update_fun
    pacs_update_fun = btp.pacs_update_sink_pac
    return True


def hdl_wid_20001(_: WIDParams):
    """
    Please prepare IUT into a connectable mode.
    """

    stack = get_stack()
    btp.gap_set_connectable()
    btp.gap_start_advertising(ad=stack.gap.ad)
    return True


def hdl_wid_20108(_: WIDParams):
    """
    Please send notifications for Characteristic 'Sink PAC Records' to the PTS.
    """

    pacs_update_fun()
    return True
