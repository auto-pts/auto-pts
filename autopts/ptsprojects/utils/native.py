#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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

log = logging.debug


class NativeIUT:
    def __init__(self):
        self._native_process = None
        self._log_file = None
        self._ansi_log_proc = None

    def start(self, native_cmd, log_dir):
        try:
            self._log_file = open(os.path.join(log_dir, "native-iut.log"), "a")

            log(f"Starting native process: {native_cmd}")
            self._native_process = subprocess.Popen(shlex.split(native_cmd),
                                                    shell=False,
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT)
            self._ansi_log_proc = subprocess.Popen(
                ["ansi2txt"],
                stdin=self._native_process.stdout,
                stdout=self._log_file
            )

        except Exception:
            self.close()
            raise

    def close(self):
        if self._native_process and self._native_process.poll() is None:
            self._native_process.terminate()
            self._native_process.wait()
            self._native_process = None
            self._ansi_log_proc.terminate()
            self._ansi_log_proc.wait()
            self._ansi_log_proc = None

        if self._log_file:
            self._log_file.close()
            self._log_file = None
