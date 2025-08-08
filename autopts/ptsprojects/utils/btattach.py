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
import re
import select
import shlex
import subprocess
from time import sleep, time

from autopts.utils import get_global_end

log = logging.debug


class Btattach:
    def __init__(self):
        self._btattach_process = None
        self._log_file = None

    def _btattach(self, btattach_cmd, timeout):
        master_fd, slave_fd = pty.openpty()

        log(f"Starting btattach process: {btattach_cmd}")
        self._btattach_process = subprocess.Popen(
            shlex.split(btattach_cmd),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=self._log_file,
            close_fds=True,
        )

        os.close(slave_fd)

        start_time = time()
        attach_time = False
        buffer = b''
        hci = None
        error_detected = False
        post_attach_wait = 2

        while time() - start_time < timeout:
            rlist, _, _ = select.select([master_fd], [], [], 0.5)
            if master_fd in rlist:
                try:
                    chunk = os.read(master_fd, 1024)
                except OSError:
                    break
                if not chunk:
                    break

                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines[-1]
                for line in lines[:-1]:
                    text = line.decode(errors='ignore').strip()
                    log(f"[btattach] {text}")

                    match = re.search(r'Device index (\d+)', text)
                    if match and hci is None:
                        hci = int(match.group(1))
                        attach_time = time()

                    if 'Unable to create user channel socket' in text or 'Device or resource busy' in text:
                        log(text)
                        error_detected = True
                        break

            # We already have hci, wait a few seconds for a possible socket error
            if hci is not None and time() - attach_time > post_attach_wait:
                break

            if error_detected:
                hci = None
                break

        os.close(master_fd)

        return hci

    def _start(self, btattach_cmd):
        retry = 0
        while not get_global_end():
            hci = self._btattach(btattach_cmd, timeout=5)

            if hci is not None:
                return hci

            retry += 1
            if retry > 10 or get_global_end():
                log(f"btattach failed, no more retries... ({retry}/10)")
                return None

            log(f"btattach failed, retrying... ({retry}/10)")
            subprocess.run(['pkill', '-f', 'btattach'])
            sleep(5)

        return None

    def start(self, btattach_cmd, log_dir):
        try:
            self._log_file = open(os.path.join(log_dir, "btattach.log"), "a")

            hci = self._start(btattach_cmd)
            if hci is None:
                raise Exception("Btattach failed.")

            return hci
        except Exception:
            self.close()
            raise

    def close(self):
        if self._btattach_process and self._btattach_process.poll() is None:
            self._btattach_process.terminate()
            self._btattach_process.wait()
            self._btattach_process = None

        if self._log_file:
            self._log_file.close()
            self._log_file = None
