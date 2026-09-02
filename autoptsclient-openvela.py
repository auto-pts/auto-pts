#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""openvela auto PTS client

This client connects to openvela bttester running in QEMU via TCP socket.

Usage:
    1. Start QEMU with openvela:

    2. Start bttester in QEMU:
       adb shell "bttester &"

    3. Setup adb port forwarding:
       adb forward tcp:9876 tcp:9876

    4. Run this client:
       python autoptsclient-openvela.py <workspace> -i <pts_ip> --btp-tcp-port 9876
"""

import importlib

from autopts import client as autoptsclient
from autopts.ptsprojects.openvela.iutctl import get_iut
from cliparser import CliParser


class OpenVelaCliParser(CliParser):
    """CLI parser with openvela-specific options."""

    def __init__(self, iut_modes=None, board_names=None, add_help=True):
        # openvela only supports TCP mode
        if iut_modes is None:
            iut_modes = ['btp_tcp_client']
        super().__init__(iut_modes, board_names, add_help)
        self._add_openvela_options()

    def _add_openvela_options(self):
        """Add openvela-specific command line options."""
        self.add_argument('--adb-device',
                          type=str,
                          default=None,
                          help='ADB device serial number')

    def get_iut_mode(self, args):
        """openvela always uses TCP mode."""
        # Set default TCP port if not specified
        if args.btp_tcp_port is None:
            args.btp_tcp_port = 9876
        return 'btp_tcp_client'

    def check_args_btp_tcp_client(self, args):
        """Override port range check - openvela bttester uses port 9876."""
        if not 1024 <= args.btp_tcp_port <= 65535:
            return (
                f'btp_tcp_client mode: Invalid server port number={args.btp_tcp_port}, expected '
                'range <1024,65535>'
            )
        return ''


class OpenVelaClient(autoptsclient.Client):
    """openvela auto-pts client."""

    def __init__(self):
        # Import the openvela project package, which exposes the profile
        # modules (iutctl, a2dp) the framework looks up by name.
        project = importlib.import_module('autopts.ptsprojects.openvela')
        super().__init__(get_iut, project, 'openvela',
                         parser_class=OpenVelaCliParser)


def main():
    """Main entry point."""
    client = OpenVelaClient()
    client.start()


if __name__ == "__main__":
    main()
