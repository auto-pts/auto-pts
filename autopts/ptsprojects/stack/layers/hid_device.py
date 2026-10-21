#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#

import logging
import threading

from autopts.ptsprojects.stack.common import wait_for_event

log = logging.debug


class HIDDevice:
    """
    HID Device (Human Interface Device Profile) layer implementation
    """
    def __init__(self):
        """Initialize HID Device layer"""
        log(f"{self.__init__.__name__}")
        self.connected = False
        self.connected_addr = None

        # Background worker started by a WID handler (device-initiated connect,
        # input-report sender). At most one worker runs at a time because they
        # all drive the same BTP socket, whose command/response framing has no
        # per-caller demultiplexing.
        self.worker_stop = None
        self.worker_thread = None

    def wait_for_connection(self, timeout=30):
        """
        Wait for HID Device connection to be established.

        Args:
            timeout (int): Maximum time to wait in seconds (default: 30)

        Returns:
            bool: True if connection established, False otherwise
        """
        logging.debug("%s timeout=%d", self.wait_for_connection.__name__, timeout)

        return wait_for_event(timeout, lambda: self.connected is True)

    def wait_for_disconnection(self, timeout=30):
        """
        Wait for HID Device connection to be closed.

        Args:
            timeout (int): Maximum time to wait in seconds (default: 30)

        Returns:
            bool: True if disconnection completed, False otherwise
        """
        logging.debug("%s timeout=%d", self.wait_for_disconnection.__name__, timeout)

        return wait_for_event(timeout, lambda: self.connected is False)

    def set_connected(self, addr):
        """
        Set the connection information when a HID Device connection is established.

        Args:
            addr (str): Bluetooth address of the connected device
        """
        self.connected = True
        self.connected_addr = addr

    def set_disconnected(self, addr):
        """
        Update state when a HID Device connection is closed.

        Args:
            addr (str): Bluetooth address of the disconnected device
        """
        self.connected = False
        self.connected_addr = addr

    def start_worker(self, target, name, **kwargs):
        """Start the background worker that drives the IUT over BTP.

        A worker left over from an earlier WID is stopped and joined first so
        two threads never write to the BTP socket at the same time.

        Args:
            target (callable): worker function, called as
                               target(stop_event, **kwargs)
            name (str): thread name
            kwargs: additional keyword arguments passed to target

        Returns:
            threading.Event: stop event of the new worker
        """
        self.stop_worker()

        self.worker_stop = threading.Event()
        self.worker_thread = threading.Thread(
            target=target,
            args=(self.worker_stop,),
            kwargs=kwargs,
            name=name,
            daemon=True,
        )
        self.worker_thread.start()

        return self.worker_stop

    def stop_worker(self, timeout=6):
        """Stop the background worker and wait until it released the BTP socket.

        Args:
            timeout (int): seconds to wait for the worker to exit

        Returns:
            bool: True when no worker is left running
        """
        if self.worker_stop is not None:
            self.worker_stop.set()

        thread = self.worker_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout)
            if thread.is_alive():
                logging.debug("%s: worker %s still alive after %ds",
                              self.stop_worker.__name__, thread.name, timeout)
                return False

        self.worker_stop = None
        self.worker_thread = None

        return True

    def cleanup(self):
        """Cleanup HID Device resources"""
        log(f"{self.cleanup.__name__}")
        self.stop_worker()
        self.connected = False
        self.connected_addr = None
