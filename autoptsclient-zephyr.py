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
import importlib

from autopts import client as autoptsclient
from autopts.ptsprojects.zephyr.iutctl import get_iut


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        project = importlib.import_module('autopts.ptsprojects.zephyr')
        super().__init__(get_iut, project, 'zephyr')


def main():
    """Main."""

    client = ZephyrClient()
    client.start()


if __name__ == "__main__":
    main()
