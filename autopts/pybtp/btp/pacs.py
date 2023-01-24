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

"""Wrapper around btp messages. The functions are added as needed."""

import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

PACS = {
    'update_char': (defs.BTP_SERVICE_ID_PACS, defs.PACS_UPDATE_CHARACTERISTIC,
                    CONTROLLER_INDEX),
}


def pacs_update_characteristic(characteristic):
    logging.debug(f"{pacs_update_characteristic.__name__} {characteristic}")

    iutctl = get_iut()

    data = bytearray(struct.pack("<B", characteristic))

    iutctl.btp_socket.send(*PACS['update_char'], data=data)


def pacs_update_sink_pac():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_SINK_PAC)


def pacs_update_source_pac():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_SOURCE_PAC)


def pacs_update_sink_audio_locations():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_SINK_AUDIO_LOCATIONS)


def pacs_update_source_audio_locations():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_SOURCE_AUDIO_LOCATIONS)


def pacs_update_available_audio_contexts():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_AVAILABLE_AUDIO_CONTEXTS)


def pacs_update_supported_audio_contexts():
    pacs_update_characteristic(defs.PACS_CHARACTERISTIC_SUPPORTED_AUDIO_CONTEXTS)


PACS_EV = {
}
