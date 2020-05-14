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

import subprocess
import logging
import shlex
import socket

from pybtp import defs
from pybtp.types import BTPError
from pybtp.iutctl_common import BTPWorker, BTP_ADDRESS

log = logging.debug
IUT = None

# IUT log file object
IUT_LOG_FO = None


def get_iut_cmd(btpclient_path):
    """Returns command to start IUT"""

    iut_cmd = ("%s -s %s" % (btpclient_path, BTP_ADDRESS))

    return iut_cmd


class IUTCtl:
    '''IUT Control Class'''

    def __init__(self, btpclient_path):
        """Constructor."""
        log("%s.%s btpclient_path=%s", self.__class__, self.__init__.__name__,
            btpclient_path)

        self.btpclient_path = btpclient_path

        self.btp_socket = None
        self.iut_process = None


    def start(self):
        """Starts the IUT"""

        log("%s.%s", self.__class__, self.start.__name__)
        self.btp_socket = BTPWorker()
        self.btp_socket.open()

        iut_cmd = get_iut_cmd(self.btpclient_path)

        log("Starting IUT process: %s", iut_cmd)

        self.iut_process = subprocess.Popen(shlex.split(iut_cmd),
                                            shell=False,
                                            stdout=IUT_LOG_FO,
                                            stderr=IUT_LOG_FO)

        try:
            self.btp_socket.accept()
        except socket.timeout:
            log("IUT didn't connect!")
            self.stop()

#        self.wait_iut_ready_event()

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        tuple_hdr, tuple_data = self.btp_socket.read()

        if (tuple_hdr.svc_id != defs.BTP_SERVICE_ID_CORE or
                tuple_hdr.op != defs.CORE_EV_IUT_READY):
            log("Unexpected event received (%s), expected IUT ready!", err)
            self.stop()
        else:
            log("IUT ready event received OK")

    def reset(self):
        """Reset IUT like removing all paired devices"""


    def stop(self):
        """Powers off the IUT"""
        log("%s.%s", self.__class__, self.stop.__name__)

        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.iut_process and self.iut_process.poll() is None:
            self.iut_process.terminate()
            self.iut_process.wait()  # do not let zombies take over
            self.iut_process = None


def get_iut():
    return IUT


def init(btpclient_path):
    """IUT init routine"""
    global IUT_LOG_FO
    global IUT

    IUT_LOG_FO = open("iut-bluez.log", "w")

    IUT = IUTCtl(btpclient_path)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, IUT
    IUT_LOG_FO.close()
    IUT_LOG_FO = None

    if IUT:
        IUT.stop()
        IUT = None
