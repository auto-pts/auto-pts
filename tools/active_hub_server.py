#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
import argparse
import sys
import traceback
import xmlrpc.client  # noqa: F401  #TODO check if needed
import xmlrpc.server
from os.path import abspath, dirname

AUTOPTS_REPO = dirname(dirname(abspath(__file__)))
sys.path.insert(0, AUTOPTS_REPO)

from autopts.utils import (  # noqa: E402 # the order of import is very important here
    hid_gpio_hub_set_usb_power,
    ykush_set_usb_power,
)

SRN = None
VID = None
PID = None


class StartArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)

        self.add_argument("--ip", default='', type=str,
                          help="IP address")

        self.add_argument("--port", default=65100, type=int,
                          help="TCP port")

        self.add_argument("--ykush-srn", type=str,
                          help="Select serial number of the YKUSH to be used "
                               "as an active hub.")

        self.add_argument("--hid-gpio-hub", type=str,
                          help="Select VID:PID of the hid_gpio device to be used"
                               " as an active hub.")

    @staticmethod
    def check_args(arg):
        """Sanity check command line arguments"""
        if not 49152 <= arg.port <= 65535:
            sys.exit(f"Invalid server port number={arg.port}, expected range <49152,65535>")

    def parse_args(self, args=None, namespace=None):
        arg = super().parse_args(args, namespace)
        self.check_args(arg)
        return arg


def set_usb_power(port, on):
    try:
        if SRN:
            ykush_set_usb_power(port, on=on, ykush_srn=SRN)
        elif VID:
            hid_gpio_hub_set_usb_power(VID, PID, port, on)
    except BaseException as e:
        traceback.print_exception(e)
        return traceback.format_exception(e)


def _handle_usb_request(server):
    try:
        server.handle_request()
    except KeyboardInterrupt:
        return False
    except BaseException as e:
        traceback.print_exception(e)
    return True


def start_server():
    global SRN, VID, PID
    args = StartArgumentParser().parse_args()

    if args.ykush_srn:
        SRN = args.ykush_srn
    elif args.hid_gpio_hub:
        VID, PID = args.hid_gpio_hub.split(':')
        VID = int(VID, 16)
        PID = int(PID, 16)

    print(f"Active USB hub serving on port {args.port} ...")
    server = xmlrpc.server.SimpleXMLRPCServer((args.ip, args.port), allow_none=True)
    server.register_function(set_usb_power, 'set_usb_power')
    server.register_introspection_functions()
    server.timeout = 1.0

    while _handle_usb_request(server):
        pass


if __name__ == "__main__":
    start_server()
