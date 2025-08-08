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

import glob
import logging
import os
import pty
import select
import shlex
import subprocess
from pathlib import Path
from time import sleep, time

from autopts.utils import get_global_end

log = logging.debug


def find_hci_device(vid, pid, serial=None):
    hci_devices = glob.glob("/sys/class/bluetooth/hci*")
    for hci in hci_devices:
        dev_path = os.path.realpath(os.path.join(hci, "device"))
        usb_dir = Path(dev_path)

        while usb_dir.exists():
            id_vendor = usb_dir / "idVendor"
            id_product = usb_dir / "idProduct"
            serial_file = usb_dir / "serial"

            if id_vendor.exists() and id_product.exists():
                with open(id_vendor) as vf, open(id_product) as pf:
                    dev_vid = vf.read().strip().lower()
                    dev_pid = pf.read().strip().lower()

                if dev_vid == vid.lower() and dev_pid == pid.lower():
                    if serial:
                        if serial_file.exists():
                            with open(serial_file) as sf:
                                dev_serial = sf.read().strip()
                            if dev_serial == serial:
                                return os.path.basename(hci)[len('hci'):]
                    else:
                        return os.path.basename(hci)[len('hci'):]

            if usb_dir == usb_dir.parent:
                break
            usb_dir = usb_dir.parent
    return None


def btmgmt_power_off_hci(btmgmt_bin, hci):
    cmd = subprocess.run([btmgmt_bin, '-i', str(hci), 'power', 'off'],
                         stdout=subprocess.PIPE)
    result = cmd.stdout.decode()
    if 'Invalid Index' in result:
        raise Exception(f'Invalid HCI index {hci}')


class Btproxy:
    def __init__(self):
        self._btproxy_process = None
        self._log_file = None

    def _btproxy(self, btproxy_cmd, timeout):
        master_fd, slave_fd = pty.openpty()

        log(f"Starting btproxy process: {btproxy_cmd}")
        self._btproxy_process = subprocess.Popen(
            shlex.split(btproxy_cmd),
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=self._log_file,
            close_fds=True,
        )

        os.close(slave_fd)

        start_time = time()
        buffer = b''
        ready = False
        post_attach_wait = 5
        ready_time = False

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
                    log(f"[btproxy] {text}")

                    if 'Listening on /tmp/bt-server-bredr' in text:
                        ready = True
                        ready_time = time()

                    if 'No controller available: Device or resource busy' in text:
                        ready = False
                        break

            # We already have hci, wait a few seconds for a possible socket error
            if ready and time() - ready_time > post_attach_wait:
                break

        os.close(master_fd)

        return ready

    def start(self, btproxy_cmd, hci, log_dir, btmgmt_bin=None):
        retry = 0

        try:
            while not get_global_end():
                self._log_file = open(os.path.join(log_dir, "btproxy.log"), "a")

                if btmgmt_bin:
                    btmgmt_power_off_hci(btmgmt_bin, hci)

                if self._btproxy(btproxy_cmd, timeout=5):
                    return

                self.close()

                retry += 1
                if retry > 10 or get_global_end():
                    log(f"btproxy failed, no more retries... ({retry}/10)")
                    return None

                log(f"btproxy failed, retrying... ({retry}/10)")
                subprocess.run(['pkill', '-f', 'btproxy'])
                sleep(3)
        except Exception:
            self.close()
            raise

        return None

    def close(self):
        if self._btproxy_process and self._btproxy_process.poll() is None:
            self._btproxy_process.terminate()
            self._btproxy_process.wait()
            self._btproxy_process = None

        if self._log_file:
            self._log_file.close()
            self._log_file = None
