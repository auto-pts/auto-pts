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

from autopts.pybtp import defs
from autopts.pybtp.types import BTPError
from autopts.pybtp.iutctl_common import BTPSocketSrv, BTPWorker, BTP_ADDRESS

log = logging.debug
IUT = None

# IUT log file object
IUT_LOG_FO = None
CLI_SUPPORT = ['btp_py', 'btpclient_path']


def get_iut_cmd(btpclient_path):
    """Returns command to start IUT"""

    iut_cmd = ("%s -s %s" % (btpclient_path, BTP_ADDRESS))

    return iut_cmd


class IUTCtl:
    '''IUT Control Class'''

    def __init__(self, args):
        """Constructor."""
        log("%s.%s btpclient_path=%s", self.__class__, self.__init__.__name__,
            args.btpclient_path)

        self.btpclient_path = args.btpclient_path
        self.btp_socket = None
        self.btp_address = BTP_ADDRESS
        self.socket_srv = None
        self.iut_process = None

    def start(self):
        """Starts the IUT"""

        log("%s.%s", self.__class__, self.start.__name__)
        self.socket_srv = BTPSocketSrv()
        self.socket_srv.open(self.btp_address)
        self.btp_socket = BTPWorker(self.socket_srv)

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

        try:
            if (tuple_hdr.svc_id != defs.BTP_SERVICE_ID_CORE or
                    tuple_hdr.op != defs.CORE_EV_IUT_READY):
                raise BTPError("Failed to get ready event")
        except BTPError as err:
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


def init(args):
    """IUT init routine"""
    global IUT_LOG_FO
    global IUT

    IUT_LOG_FO = open("iut-bluez.log", "w")

    IUT = IUTCtl(args)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, IUT
    if IUT_LOG_FO:
        IUT_LOG_FO.close()
        IUT_LOG_FO = None

    if IUT:
        IUT.stop()
        IUT = None
