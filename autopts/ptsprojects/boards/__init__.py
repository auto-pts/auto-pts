#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
# Copyright (c) 2021, Nordic Semiconductor ASA.
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

import importlib
import json
import logging
import os
import pkgutil
import shlex
import subprocess
import sys

import pylink
import serial.tools.list_ports

# For each new board just create a <new-board-name>.py file that contains reset_cmd() function and list
# of supported boards.

log = logging.debug
devices_in_use = []


class Board:
    """HW DUT board"""

    def __init__(self, board_name, iutctl):
        """Constructor of board"""

        self.name = board_name
        self.iutctl = iutctl
        self.reset_cmd = self.get_reset_cmd()

    def reset(self):
        """Reset HW DUT board with
        """
        log(f"About to reset DUT: {self.reset_cmd}")

        if isinstance(self.reset_cmd, str):
            reset_process = subprocess.Popen(shlex.split(self.reset_cmd),
                                             shell=False,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)

            if reset_process.wait(20):
                logging.error("reset failed")

        else:
            self.reset_cmd()

    def get_reset_cmd(self):
        """Get and Return Board reset command,
        which will be executed in Board.reset() with subprocess.

        Returns:
            return board_name.py.reset_cmd(self.iutctl) when board module exists.
            else return Jlink(self.iutctl.debugger_snr, self.iutctl.device_core).reset_command as default.
        """

        module_name = __package__ + '.' + self.name
        if getattr(self.iutctl, 'pylink_reset', False):
            return lambda: pylink_reset(self.iutctl.debugger_snr, self.iutctl.device_core)
        elif importlib.util.find_spec(module_name):
            board_mod = importlib.import_module(__package__ + '.' + self.name)

            if board_mod is None:
                raise Exception(f"Board name {self.name} is not supported!")
            return board_mod.reset_cmd(self.iutctl)
        else:
            try:
                return Jlink(self.iutctl.debugger_snr, self.iutctl.device_core).reset_command
            except Exception as e:
                raise Exception(f"Board name {self.name} is not supported! and failed to reset with Jlink.") from e


def pylink_reset(debugger_snr, device_core):
    log(f'debugger_snr={debugger_snr}, device_core={device_core}')

    jlink = pylink.JLink()
    try:
        jlink.disable_dialog_boxes()
        if not jlink.opened():
            jlink.open(serial_no=debugger_snr)

        jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        jlink.connect(device_core)
        jlink.reset(ms=0, halt=False)
    finally:
        jlink.close()


def get_build_and_flash(board_name):
    board_mod = importlib.import_module(__package__ + '.' + board_name)

    if board_mod is None:
        raise Exception(f"Board name {board_name} is not supported!")

    try:
        return board_mod.build_and_flash
    except AttributeError:
        return None


def get_board_type(board_name):
    board_mod = importlib.import_module(__package__ + '.' + board_name)

    if board_mod is None:
        raise Exception(f"Board name {board_name} is not supported!")

    try:
        return board_mod.board_type
    except AttributeError:
        return None


def get_available_boards(project):
    names = []

    for m in pkgutil.iter_modules(__path__):
        board_mod = importlib.import_module(__package__ + '.' + m.name)

        if project in board_mod.supported_projects:
            names.append(m.name)

    return names


def get_openocd_reset_cmd(openocd_bin, openocd_scripts, openocd_cfg):
    """Compute openocd reset command"""
    if not os.path.isfile(openocd_bin):
        raise Exception(f"openocd {openocd_bin} not found!")

    if not os.path.isdir(openocd_scripts):
        raise Exception(f"openocd scripts {openocd_scripts} not found!")

    if not os.path.isfile(openocd_cfg):
        raise Exception(f"openocd config {openocd_cfg} not found!")

    reset_cmd = (
        f'{openocd_bin} -s {openocd_scripts} -f {openocd_cfg} -c "init" -c "targets 1" '
        f'-c "reset halt" -c "reset run" -c "shutdown"'
    )

    return reset_cmd


def get_device_list():
    """Returns dictionary of <tty>: <jlink_srn> (eg. {'/dev/ttyUSB0': 'xxxxxx'}) of found devices"""

    device_list = {}

    for dev in serial.tools.list_ports.comports():
        if dev.serial_number is not None:
            device_list[dev.device] = dev.serial_number.lstrip("0")

    return device_list


def get_free_device(board=None):
    """Returns tty path and jlink serial number of a free device."""
    devices = get_device_list()

    ret_snr = None
    ret_tty = None

    for tty, snr in devices.items():
        if tty not in devices_in_use and len(snr) >= 9 and snr.isnumeric():
            ret_snr = snr
            ret_tty = tty
            # Opposite enumeration-order for TTY to coproccessor cores on nRF5340 Audio devkit.
            if board != 'nrf53_audio':
                break

    if ret_tty is not None:
        devices_in_use.append(ret_tty)

    log(f"Got free rtt for device {ret_snr}: {ret_tty}")
    return ret_tty, ret_snr


def get_debugger_snr(tty):
    """Return jlink serial number of the device with the given tty.
    """
    jlink = None
    devices = get_device_list()
    if sys.platform == 'win32':
        tty = tty_to_com(tty)

    for dev in devices.keys():
        if dev == tty:
            jlink = devices[dev]
            break

    return jlink


def get_tty(debugger_snr, board=None):
    """Return tty or COM of the device with given serial number.
    """
    tty = None
    devices = get_device_list()

    for dev in devices.keys():
        if devices[dev] == debugger_snr:
            tty = dev
            # Opposite enumeration-order for TTY to coproccessor cores on nRF5340 Audio devkit.
            if board != 'nrf53_audio':
                break

    log(f"Got tty for device {debugger_snr}: {tty}")
    return tty


def release_device(tty):
    if tty and tty in devices_in_use:
        devices_in_use.remove(tty)


def tty_exists(tty):
    if tty is None:
        return False

    if sys.platform == 'win32' and tty.startswith('/dev/ttyS'):
        tty = tty_to_com(tty)

    exists = tty in [port.device for port in serial.tools.list_ports.comports()]

    if not exists:
        exists = os.path.exists(tty)

    return exists


def com_to_tty(com):
    if com.startswith('COM'):
        return '/dev/ttyS' + str(int(com['COM'.__len__():]) - 1)
    elif com.startswith('/dev/ttyS'):
        return com
    return None


def tty_to_com(tty):
    if tty.startswith('/dev/ttyS'):
        return 'COM' + str(int(tty['/dev/ttyS'.__len__():]) + 1)
    elif tty.startswith('COM'):
        return tty
    return None


class Jlink:
    """
    A wrapper for SEGGER-JLink.
    """

    def __init__(self, sn, device):
        """
        Create an instance of the JLink debugger class.

        Arguments:
            sn {str} -- serial number of Jlink device.
            device {str} -- device core name to be connected with jlink
        """
        super().__init__()
        self.sn = sn
        self.device = device
        self._reset_seqs = (
            "si 1\n"
            "speed 4000\n"
            "h\n"
            "RSetType 2\n"
            "r\n"
            "g\n"
            "q\n"
        )

    @property
    def reset_command(self):
        """Return Jlink reset command, executed on the console.

        Example:
            'JLink -CommandFile reset.jlink -usb 1062902236 -device kw45b41z83'
        """
        jlink = 'JLink' if sys.platform == "win32" else 'JLinkExe'
        jlink_cmd = [jlink, '-CommandFile', self._generate_reset_file()]
        device_option = ['-device', self.device]
        debugger_option = ['-usb', self.sn] if self.sn else []
        jlink_cmd += debugger_option + device_option
        return ' '.join(jlink_cmd)

    def update_reset_seqs(self, reset_seqs):
        self._reset_seqs = reset_seqs

    def _generate_reset_file(self):
        file_path = "reset.jlink"
        if not os.path.exists(file_path):
            with open(file_path, 'x') as f:
                f.write(self._reset_seqs)
                f.close()
        return file_path


class NrfUtil:
    """
    Provides utility wrapper functions for nRF Util command line tool.
    """
    _FAMILY_TO_JSON = {
        "nrf52": "NRF52_FAMILY",
        "nrf53": "NRF53_FAMILY",
        "nrf54h": "NRF54H_FAMILY",
        "nrf54l": "NRF54L_FAMILY",
    }

    _JSON_TO_FAMILY = {v: k for k, v in _FAMILY_TO_JSON.items()}

    # nRF Util commands required by this wrapper
    _NRFUTIL_CMDS = (
        "device",
    )

    def __init__(self, board_name, debugger_snr):
        self._check_nrfutil()
        self._check_nrfjprog()

        if debugger_snr is None:
            debugger_snr = self.find_debugger(board_name)

        self.debugger_snr = debugger_snr
        self.family = self._get_family(self.debugger_snr)

    @staticmethod
    def _check_nrfutil():
        from autopts.bot.common import check_call

        try:
            check_call(["nrfutil", "--version"], stdout=False, stderr=False)
        except subprocess.CalledProcessError:
            raise Exception("nrfutil not found!") from None

        def check_nrfutil_cmd(c):
            try:
                check_call(["nrfutil", c], stdout=False, stderr=False)
            except subprocess.CalledProcessError:
                raise Exception(f"nrfutil {c} not found!") from None

        for cmd in NrfUtil._NRFUTIL_CMDS:
            check_nrfutil_cmd(cmd)

    @staticmethod
    def _check_nrfjprog():
        from autopts.bot.common import check_call

        try:
            check_call(["nrfjprog", "--version"], stdout=False, stderr=False)
        except subprocess.CalledProcessError:
            raise Exception("nrfjprog not found!") from None

    @staticmethod
    def _family2json(family):
        try:
            return NrfUtil._FAMILY_TO_JSON[family.lower()]
        except (AttributeError, KeyError):
            raise ValueError(f"Unsupported family: {family}") from None

    @staticmethod
    def _json2family(family):
        try:
            return NrfUtil._JSON_TO_FAMILY[family]
        except KeyError:
            raise ValueError(f"Unsupported family: {family}") from None

    @staticmethod
    def _board_name2version(board_name):
        module_name = importlib.import_module(__package__ + '.' + board_name)

        version = getattr(module_name, 'version', None)
        if not version:
            raise ValueError(f"Unspecified {board_name} version. Please add \"version = 'VERSION'\"") from None

        return version

    @staticmethod
    def _is_multi_core(family):
        return family in ["nrf53"]

    @staticmethod
    def _get_family(sn):
        from autopts.bot.common import check_output

        output = check_output(["nrfutil", "device", "list", "--json", "--skip-overhead"])
        stdout = output.decode("utf-8")
        devices = json.loads(stdout)["devices"]

        for device in devices:
            if device["serialNumber"] == sn and "devkit" in device:
                family = device["devkit"]["deviceFamily"]
                return NrfUtil._json2family(family)

        return None

    @staticmethod
    def find_debugger(board_name):
        """Return the first found non-protected nRF5x DUT serial number

        :param board_name: board name
        :return: debugger serial number
        """
        from autopts.bot.common import check_output

        output = check_output(["nrfutil", "device", "list", "--json", "--skip-overhead"])
        stdout = output.decode("utf-8")
        devices = json.loads(stdout)["devices"]
        version = NrfUtil._board_name2version(board_name)

        for device in devices:
            if "devkit" not in device:
                continue

            if version and device["devkit"]["boardVersion"] != version:
                continue

            return device["serialNumber"]

        raise Exception("Could not find debugger")

    def get_debugger_snr(self):
        return self.debugger_snr

    def device_protection_get(self):
        """Return device protection state

        :return: True if device protection is enabled, False otherwise
        """
        from autopts.bot.common import check_output

        cmd = ["nrfutil", "device", "protection-get", "--json", "--skip-overhead", "--serial-number", self.debugger_snr]
        output = check_output(cmd)
        stdout = output.decode("utf-8")
        devices = json.loads(stdout)["devices"]

        for device in devices:
            device_protection = device["protectionStatus"]
            return "None" not in device_protection

        raise Exception("Could not check device protection state")

    def device_protection_disable(self):
        """Disable device protection

        Erases user code and UICR flash areas.
        :return: None
        """
        from autopts.bot.common import check_call

        # For multicore devices like nRF53 Series, make sure to recover the network core before the application core:
        if self._is_multi_core(self.family):
            check_call(f'nrfjprog --recover --coprocessor CP_NETWORK -s {self.debugger_snr}')

        check_call(f'nrfjprog --recover -s {self.debugger_snr}')
