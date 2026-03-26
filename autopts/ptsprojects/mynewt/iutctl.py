#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2025, Atmosic.
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

from autopts.ptsprojects.iutctl import IutCtl, IutCtlWrapper

log = logging.debug
MYNEWT = None


def create_mynewt_ctl_class(use_wrapper: bool):
    base = IutCtlWrapper if use_wrapper else IutCtl

    class MynewtCtl(base):
        """Mynewt OS Control Class"""

        def __init__(self, args):
            super().__init__(args)
            self._rtt_logger_name = 'Terminal'

    return MynewtCtl


def get_iut():
    return MYNEWT


def init(args):
    """IUT init routine

    tty_file -- Path to TTY file. BTP communication with HW DUT will be done
    over this TTY.
    board -- HW DUT board to use for testing.
    """
    global MYNEWT

    if len(args.iut_targets_args) == 1:
        use_wrapper = False
        args = next(iter(args.iut_targets_args.values()))
    else:
        use_wrapper = True

    mynewt_ctl_class = create_mynewt_ctl_class(use_wrapper)

    MYNEWT = mynewt_ctl_class(args)


def cleanup():
    """IUT cleanup routine"""
    global MYNEWT

    if MYNEWT:
        MYNEWT.stop()
        MYNEWT = None
