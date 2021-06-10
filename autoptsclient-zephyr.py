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
    def parse_args(self):
        arg_parser = autoptsclient.CliParser("PTS automation client",
                                             autoprojects.iutctl.Board.names)

        # IUT specific arguments below
        arg_parser.add_argument("kernel_image",
                                help="Zephyr OS kernel image to be used for "
                                "testing. Normally a zephyr.elf file.")

        args = arg_parser.parse_args()
        args.qemu_bin = autoprojects.iutctl.QEMU_BIN

        self.check_args(args)

        return args

    def check_args(self, args):
        autoptsclient.Client.check_args(self, args)

        if not os.path.isfile(args.kernel_image):
            sys.exit("kernel_image %s is not a file!" % repr(args.kernel_image))

    def init_iutctl(self, args):
        autoprojects.iutctl.init(args.kernel_image, args.tty_file, args.board, args.rtt2pty)

    def setup_project_pixits(self, ptses):
        autoprojects.gap.set_pixits(ptses[0])
        autoprojects.dis.set_pixits(ptses[0])
        autoprojects.sm.set_pixits(ptses[0])
        autoprojects.l2cap.set_pixits(ptses[0])
        autoprojects.gatt.set_pixits(ptses)
        autoprojects.mesh.set_pixits(ptses)

    def setup_test_cases(self, ptses):
        self.test_cases = autoprojects.gap.test_cases(ptses[0])
        self.test_cases += autoprojects.dis.test_cases(ptses)
        self.test_cases += autoprojects.gatt.test_cases(ptses)
        self.test_cases += autoprojects.sm.test_cases(ptses[0])
        self.test_cases += autoprojects.l2cap.test_cases(ptses[0])
        self.test_cases += autoprojects.mesh.test_cases(ptses)

    def cleanup(self):
        autoprojects.iutctl.cleanup()


def main():
    """Main."""

    client = ZephyrClient(get_iut, "zephyr_")
    client.start()


if __name__ == "__main__":
    main()
