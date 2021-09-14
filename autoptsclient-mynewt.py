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

"""Mynewt auto PTS client"""

import autoptsclient_common as autoptsclient
from ptsprojects.mynewt.iutctl import get_iut


class MynewtClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'mynewt')


def main():
    """Main."""

    client = MynewtClient()
    client.start()


if __name__ == "__main__":
    main()
