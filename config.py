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

"""Configuration variables"""

SERVER_PORT = 65000
CLIENT_PORT = 65001

IUT_CFG = None

class IUT_NAMES:
    ZEPHYR = "zephyr"

class IUT:
    def __init__(self, iut_name):
        self.iut_name = iut_name

def init_iut_cfg(iut_name):
    global IUT_CFG

    IUT_CFG = IUT(iut_name)
