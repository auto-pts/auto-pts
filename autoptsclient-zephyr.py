#!/usr/bin/env python

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

"""Zephyr auto PTS client"""

import os
import sys

import autoptsclient_common as autoptsclient
import ptsprojects.zephyr as autoprojects
from ptsprojects.zephyr.iutctl import get_iut


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'zephyr')

    def parse_args(self):
        arg_parser = autoptsclient.CliParser("PTS automation client",
                                             autoprojects.iutctl.Board.names)

        args = arg_parser.parse_args()

        if args.hci is None:
            args.qemu_bin = autoprojects.iutctl.QEMU_BIN

        self.check_args(args)

        return args

    def init_iutctl(self, args):
        autoprojects.iutctl.init(args)

    def cleanup(self):
        autoprojects.iutctl.cleanup()


def main():
    """Main."""

    client = ZephyrClient()
    client.start()


if __name__ == "__main__":
    main()
