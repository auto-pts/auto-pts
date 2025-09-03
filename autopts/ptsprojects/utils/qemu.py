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
import pty
import shlex
import subprocess
from time import sleep, time

log = logging.debug


class QEMU:
    def __init__(self):
        self._qemu_process = None
        self._master_fd = None
        self._log_file = None
        self._log_file_name = "qemu-iut.log"

    def _start(self, qemu_cmd, boot_log, log_dir, timeout):
        self._master_fd, slave_fd = pty.openpty()

        if isinstance(qemu_cmd, str):
            cmd = shlex.split(qemu_cmd)
        else:
            cmd = qemu_cmd

        log_file_path = os.path.join(log_dir, self._log_file_name)
        self._log_file = open(log_file_path, "a")

        self._qemu_process = subprocess.Popen(
            cmd,
            shell=False,
            stdin=slave_fd,
            stdout=self._log_file,
            stderr=self._log_file,
            close_fds=True
        )
        os.close(slave_fd)

        boot_detected = False
        start_time = time()

        with open(log_file_path) as f:
            while time() - start_time < timeout and not boot_detected:
                line = f.readline()
                if not line:
                    sleep(0.1)
                    continue
                log(f"[qemu] {line.strip()}")
                if boot_log in line:
                    boot_detected = True
                    break

        if not boot_detected:
            raise Exception(f"QEMU failed to boot: did not find '{boot_log}' in '{log_file_path}' "
                            f"within {timeout} seconds.")

    def start(self, qemu_cmd, boot_log, log_dir, timeout=10):
        try:
            self._start(qemu_cmd, boot_log, log_dir, timeout)
        except Exception:
            self.close()
            raise

    def close(self):
        if self._master_fd is None:
            return

        try:
            log("Sending Ctrl+A x to exit qemu")
            os.write(self._master_fd, b'\x01x')
        except Exception as e:
            log(f"Failed to send Ctrl+A x to QEMU: {e}")

        try:
            self._qemu_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            log("QEMU didn't exit, terminating...")

            if self._qemu_process.poll() is None:
                self._qemu_process.terminate()
                self._qemu_process.wait()
        finally:
            self._qemu_process = None
            os.close(self._master_fd)
            self._master_fd = None

            if self._log_file:
                self._log_file.close()
                self._log_file = None
