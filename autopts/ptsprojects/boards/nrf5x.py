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

from autopts.bot.common import check_call, check_output

supported_projects = ['zephyr']


FAMILY_TO_JSON = {
    "nrf52": "NRF52_FAMILY",
    "nrf53": "NRF53_FAMILY",
    "nrf54h": "NRF54H_FAMILY",
    "nrf54l": "NRF54L_FAMILY",
}

JSON_TO_FAMILY = {v: k for k, v in FAMILY_TO_JSON.items()}


def _family2json(family):
    try:
        return FAMILY_TO_JSON[family.lower()]
    except (AttributeError, KeyError):
        raise ValueError(f"Unsupported family: {family}") from None


def _json2family(family):
    try:
        return JSON_TO_FAMILY[family]
    except KeyError:
        raise ValueError(f"Unsupported family: {family}") from None


def _board_name2version(board_name):
    module_name = importlib.import_module(__package__ + '.' + board_name)

    version = getattr(module_name, 'version', None)
    if not version:
        raise ValueError(f"Unsupported board: {board_name}") from None

    return version


def _is_multi_core(family):
    return family in ["nrf53"]


def _get_family(debugger_snr):
    output = check_output(["nrfutil", "device", "list", "--json", "--skip-overhead"])
    stdout = output.decode("utf-8")
    devices = json.loads(stdout)["devices"]

    for device in devices:
        if device["serialNumber"] == debugger_snr and "devkit" in device:
            family = device["devkit"]["deviceFamily"]
            return _json2family(family)

    return None


def check_device_protection(debugger_snr):
    """Return device protection state on nRF5x DUT

    Dependency: nRF5x command line tools
    :param debugger_snr: debugger serial number
    :return: True if device protection is enabled, False otherwise
    """
    cmd = ["nrfutil", "device", "protection-get", "--json", "--skip-overhead", "--serial-number", debugger_snr]
    output = check_output(cmd)
    stdout = output.decode("utf-8")
    devices = json.loads(stdout)["devices"]

    for device in devices:
        device_protection = device["protectionStatus"]
        return "None" not in device_protection

    raise Exception("Could not check device protection state")


def disable_device_protection(debugger_snr):
    """Disable device protection on nRF5x DUT

    Erases user code and UICR flash areas.

    Dependency: nRF5x command line tools
    :param debugger_snr: debugger serial number
    :return: None
    """
    family = _get_family(debugger_snr)

    # For multi-core devices like nRF53 Series, make sure to recover the network core before the application core:
    if _is_multi_core(family):
        check_call(f'nrfjprog --recover --coprocessor CP_NETWORK -s {debugger_snr}')

    check_call(f'nrfjprog --recover -s {debugger_snr}')


def find_debugger(board_name):
    """Return the first found non-protected nRF5x DUT serial number

    Dependency: nRF5x command line tools
    :param board_name: board name
    :return: debugger serial number
    """
    output = check_output(["nrfutil", "device", "list", "--json", "--skip-overhead"])
    stdout = output.decode("utf-8")
    devices = json.loads(stdout)["devices"]
    version = _board_name2version(board_name)

    for device in devices:
        if "devkit" not in device:
            continue

        if version and device["devkit"]["boardVersion"] != version:
            continue

        return device["serialNumber"]

    return None


def reset_cmd(iutctl):
    """Return reset command for nRF5x DUT

    Dependency: nRF5x command line tools
    """

    return f'nrfjprog -r -s {iutctl.debugger_snr}'


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, project_repos=None,
                    env_cmd=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    :param project_repos: a list of repo paths
    :param env_cmd: a command to for environment activation, e.g. source /path/to/venv/activate
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file)

    if env_cmd:
        env_cmd = env_cmd.split() + ['&&']
    else:
        env_cmd = []

    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    if conf_file and conf_file not in ["default", "prj.conf"]:
        cmd.extend(('--', f'-DEXTRA_CONF_FILE=\'{conf_file}\''))

    check_call(env_cmd + cmd, cwd=tester_dir)
    check_call(env_cmd + ['west', 'flash', '--skip-rebuild', '--recover',
                          '-i', debugger_snr], cwd=tester_dir)
