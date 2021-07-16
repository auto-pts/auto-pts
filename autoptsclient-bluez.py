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

"""Bluez auto PTS client"""

import os
import sys

import autoptsclient_common as autoptsclient
import ptsprojects.bluez as autoprojects
from ptsprojects.bluez.iutctl import get_iut


class BluezClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'bluez')

    def parse_args(self):
        arg_parser = autoptsclient.CliParser("PTS automation client")
        args = arg_parser.parse_args()

        self.check_args(args)

        return args

    def init_iutctl(self, args):
        autoprojects.iutctl.AUTO_PTS_LOCAL = autoptsclient.AUTO_PTS_LOCAL
        autoprojects.iutctl.init(args.btpclient_path)

    def setup_test_cases(self, ptses):
        self.test_cases = autoprojects.gap.test_cases(ptses[0])
        self.test_cases += autoprojects.sm.test_cases(ptses[0])

    def cleanup(self):
        autoprojects.iutctl.cleanup()


def main():
    """Main."""

    client = BluezClient()
    client.start()


if __name__ == "__main__":
    main()
