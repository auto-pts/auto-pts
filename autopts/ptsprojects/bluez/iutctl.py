#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright 2025 NXP
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

import logging
import os
import shlex
import subprocess

from autopts.ptsprojects.stack import Stack
from autopts.pybtp import defs
from autopts.pybtp.iutctl_common import BTP_ADDRESS, BTPSocketSrv, BTPWorker
from autopts.pybtp.types import BTPError, BTPInitError

log = logging.debug
IUT = None

# IUT log file object
IUT_LOG_FO = None
IUT_AUDIO_LOG_FO = None
CLI_SUPPORT = ['btpclient_path']


def get_iut_cmd(btpclient_path):
    """Returns command to start IUT"""

    iut_cmd = f"{btpclient_path} -s {BTP_ADDRESS}"

    return iut_cmd


class IUTCtl:
    '''IUT Control Class'''

    def __init__(self, args):
        """Constructor."""
        log("%s.%s btpclient_path=%s external_audio=%s", self.__class__, self.__init__.__name__,
            args.btpclient_path, args.external_audio)

        self.btpclient_path = args.btpclient_path[0]
        self.external_audio = args.external_audio
        self.btp_socket = None
        self.btp_address = BTP_ADDRESS
        self.socket_srv = None
        self.iut_process = None
        self.audio_profile = None
        self.audio_process = None

        self.stack = Stack()
        self.stack.synch_init()

    def start(self, test_case):
        """Starts the IUT"""

        log("%s.%s", self.__class__, self.start.__name__)
        self.socket_srv = BTPSocketSrv(test_case.log_dir)
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
        except TimeoutError:
            log("IUT didn't connect!")
            self.stop()

#        self.wait_iut_ready_event()

    def wait_iut_ready_event(self):
        """Wait until IUT sends ready event after power up"""
        tuple_hdr, tuple_data = self.btp_socket.read()

        try:
            if (tuple_hdr.svc_id != defs.BTP_SERVICE_ID_CORE or
                    tuple_hdr.op != defs.BTP_CORE_EV_IUT_READY):
                raise BTPInitError("Failed to get ready event")
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

        self.stop_audio()

    def get_stack(self):
        return self.stack

    def get_external_audio_support(self):
        """Returns the type of external audio support, or None if not supported"""
        return self.external_audio

    def start_audio(self):
        if self.external_audio != "wireplumber":
            return

        logging.debug("Starting external audio with profile: %s", self.audio_profile)
        wp_env = os.environ.copy()
        wp_env["WIREPLUMBER_DEBUG"] = "I,spa.bluez*:D"
        if self.audio_profile is not None:
            base_cfg_dir = wp_env.get("WIREPLUMBER_CONFIG_DIR", "")
            profile_dir = os.path.join(os.path.dirname(__file__), "wireplumber/", self.audio_profile)
            if base_cfg_dir:
                wp_env["WIREPLUMBER_CONFIG_DIR"] = base_cfg_dir + ":" + profile_dir
            else:
                wp_env["WIREPLUMBER_CONFIG_DIR"] = profile_dir
        self.audio_process = subprocess.Popen(["wireplumber", "--profile", "bluetooth"],
                                                env=wp_env,
                                                stdout=IUT_AUDIO_LOG_FO,
                                                stderr=IUT_AUDIO_LOG_FO)
        logging.debug("Starting external audio process with PID: %s", self.audio_process.pid)

    def stop_audio(self):
        if self.audio_process and self.audio_process.poll() is None:
            logging.debug("Stopping external audio process with PID: %s", self.audio_process.pid)
            self.audio_process.terminate()
            try:
                self.audio_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logging.debug("External audio process with PID %s did not terminate in time, killing it",
                                self.audio_process.pid)
                self.audio_process.kill()
                self.audio_process.wait()
            self.audio_process = None
        self.audio_profile = None

    def set_audio_profile(self, profile):
        self.audio_profile = profile


def get_iut():
    return IUT


def init(args):
    """IUT init routine"""
    global IUT_LOG_FO
    global IUT_AUDIO_LOG_FO
    global IUT

    IUT_LOG_FO = open("iut-bluez.log", "w")
    IUT_AUDIO_LOG_FO = open("iut-bluez-audio.log", "w")

    IUT = IUTCtl(args)


def cleanup():
    """IUT cleanup routine"""
    global IUT_LOG_FO, IUT_AUDIO_LOG_FO, IUT
    if IUT_AUDIO_LOG_FO:
        IUT_AUDIO_LOG_FO.close()
        IUT_AUDIO_LOG_FO = None

    if IUT_LOG_FO:
        IUT_LOG_FO.close()
        IUT_LOG_FO = None

    if IUT:
        IUT.stop()
        IUT = None
