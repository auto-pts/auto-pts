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
import logging
import os
import re
import shutil

from autopts.bot.common import check_call

supported_projects = ["zephyr"]


def reset_cmd(iutctl):
    """Return reset command for nRF5x DUT
    Dependency: nRF5x command line tools
    """

    return f"nrfjprog -r -s {iutctl.debugger_snr}"


def _sanitize_ninja(path):
    """
    Sanitize a Ninja build file by stripping ANSI escape sequences and
    merging split command lines without removing report targets.

    This helper is especially needed when building Zephyr on Windows
    to prevent lexing errors in build.ninja caused by leftover ANSI
    color codes and broken continuation lines.

    Reads the specified build.ninja file, removes all ANSI
    escape codes (e.g., color sequences like "\\x1b[...m"), and merges
    any broken continuation lines (such as fragmented COMMAND arguments
    like "-d 99 ram"). It preserves the structure and content of
    custom report blocks (e.g., ram_report and rom_report) intact,
    aside from ANSI code removal.

    :param path: Path to the build.ninja file to sanitize
    :type path: str
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    clean = re.sub(r"\x1b\[[0-9;]*[mK]", "", text)

    lines = clean.splitlines(keepends=True)
    out = []
    for line in lines:
        if out and re.match(r"^[ \t]+-\w+", line):
            out[-1] = out[-1].rstrip("\r\n") + " " + line.strip() + "\n"
        else:
            out.append(line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, *args):
    """
    Build the Zephyr test application and flash the resulting binary to an nRF5x board.

    Steps performed:
      1. Remove any existing "build" directory under the tester path.
      2. Run CMake configuration only via `west build --cmake-only`, applying an optional overlay.
      3. Sanitize the generated build.ninja file (strip ANSI codes and merge broken lines).
      4. Invoke Ninja to perform a full build, including report targets.
      5. Flash the built firmware with `west flash`, skipping rebuild and using recovery mode.

    :param zephyr_wd: Path to the root of the Zephyr project.
    :type zephyr_wd: str
    :param board: Board name for the build (e.g., 'nrf52840dk/nrf52840').
    :type board: str
    :param debugger_snr: Serial number of the nRF5x debugger to use for flashing.
    :type debugger_snr: str
    :param conf_file: Optional Kconfig overlay filename (e.g., 'overlay.conf').
    :type conf_file: str or None
    """
    logging.debug(
        "%s called with zephyr_wd=%s, board=%s, overlay=%s",
        build_and_flash.__name__,
        zephyr_wd,
        board,
        conf_file,
    )

    # Determine tester and build directories
    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")
    build_dir = os.path.join(tester_dir, "build")

    # 1. Remove existing build directory if present
    if os.path.isdir(build_dir):
        logging.debug("Removing existing build directory at %s", build_dir)
        shutil.rmtree(build_dir)

    # 2. Configure with CMake only, adding EXTRA_CONF_FILE if an overlay is provided
    cmd_configure = [
        "west",
        "build",
        "--cmake-only",
        "-p",
        "auto",
        "-b",
        board,
    ]
    if conf_file and conf_file not in ("default", "prj.conf"):
        # For audio-related overlays, append the controller overlay as well
        if "audio" in conf_file:
            conf_file += ";overlay-le-audio-ctlr.conf"
        cmd_configure.extend(["--", f"-DEXTRA_CONF_FILE={conf_file}"])
    check_call(cmd_configure, cwd=tester_dir)

    # 3. Sanitize build.ninja (remove ANSI escape sequences and fix line breaks)
    ninja_file = os.path.join(build_dir, "build.ninja")
    if os.path.isfile(ninja_file):
        logging.debug("Sanitizing Ninja build file at %s", ninja_file)
        _sanitize_ninja(ninja_file)

    # 4. Run full Ninja build (including report generation)
    check_call(["ninja", "-C", build_dir], cwd=tester_dir)

    # 5. Flash the firmware, skipping rebuild and enabling recovery
    check_call(
        ["west", "flash", "--skip-rebuild", "--recover", "-i", debugger_snr],
        cwd=tester_dir,
    )
