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

from autopts.ptsprojects.stack.common import wait_for_event

log = logging.debug


class HIDHost:
    """
    HID Host (Human Interface Device Profile) layer implementation
    """
    def __init__(self):
        """Initialize HID Host layer"""
        log(f"{self.__init__.__name__}")
        self.connected = False
        self.connected_addr = None

        # Last received data from events (for WID verification).
        self.last_input_report = None
        self.last_get_report = None          # (result_code, report_type, report)
        self.last_set_report_result = None   # result_code
        self.last_get_protocol = None        # (result_code, protocol)
        self.last_set_protocol_result = None  # result_code

    def wait_for_connection(self, timeout=30):
        """
        Wait for HID Host connection to be established.

        Args:
            timeout (int): Maximum time to wait in seconds (default: 30)

        Returns:
            bool: True if connection established, False otherwise
        """
        logging.debug("%s timeout=%d", self.wait_for_connection.__name__, timeout)

        return wait_for_event(timeout, lambda: self.connected is True)

    def wait_for_disconnection(self, timeout=30):
        """
        Wait for HID Host connection to be closed.

        Args:
            timeout (int): Maximum time to wait in seconds (default: 30)

        Returns:
            bool: True if disconnection completed, False otherwise
        """
        logging.debug("%s timeout=%d", self.wait_for_disconnection.__name__, timeout)

        return wait_for_event(timeout, lambda: self.connected is False)

    def wait_for_input_report(self, timeout=30):
        """Wait until an input report has been received."""
        logging.debug("%s timeout=%d", self.wait_for_input_report.__name__, timeout)

        return wait_for_event(timeout, lambda: self.last_input_report is not None)

    def wait_for_get_report(self, timeout=30):
        """Wait until a GET_REPORT response has been received."""
        logging.debug("%s timeout=%d", self.wait_for_get_report.__name__, timeout)

        return wait_for_event(timeout, lambda: self.last_get_report is not None)

    def wait_for_set_report(self, timeout=30):
        """Wait until a SET_REPORT response has been received."""
        logging.debug("%s timeout=%d", self.wait_for_set_report.__name__, timeout)

        return wait_for_event(timeout, lambda: self.last_set_report_result is not None)

    def wait_for_get_protocol(self, timeout=30):
        """Wait until a GET_PROTOCOL response has been received."""
        logging.debug("%s timeout=%d", self.wait_for_get_protocol.__name__, timeout)

        return wait_for_event(timeout, lambda: self.last_get_protocol is not None)

    def wait_for_set_protocol(self, timeout=30):
        """Wait until a SET_PROTOCOL response has been received."""
        logging.debug("%s timeout=%d", self.wait_for_set_protocol.__name__, timeout)

        return wait_for_event(timeout, lambda: self.last_set_protocol_result is not None)

    def set_connected(self, addr):
        """
        Set the connection information when a HID Host connection is established.

        Args:
            addr (str): Bluetooth address of the connected device
        """
        self.connected = True
        self.connected_addr = addr

    def set_disconnected(self, addr):
        """
        Update state when a HID Host connection is closed.

        Args:
            addr (str): Bluetooth address of the disconnected device
        """
        self.connected = False
        self.connected_addr = addr

    def clear_input_report(self):
        """Drop the stored input report before waiting for a new one."""
        self.last_input_report = None

    def clear_get_report(self):
        """Drop the stored GET_REPORT response before a new request."""
        self.last_get_report = None

    def clear_set_report(self):
        """Drop the stored SET_REPORT result before a new request."""
        self.last_set_report_result = None

    def clear_get_protocol(self):
        """Drop the stored GET_PROTOCOL response before a new request."""
        self.last_get_protocol = None

    def clear_set_protocol(self):
        """Drop the stored SET_PROTOCOL result before a new request."""
        self.last_set_protocol_result = None

    def set_input_report(self, report):
        """Store the latest input report received from the HID Device."""
        self.last_input_report = report

    def set_get_report(self, result_code, report_type, report):
        """Store the latest GET_REPORT response."""

        self.last_get_report = (result_code, report_type, report)

    def set_set_report(self, result_code):
        """Store the latest SET_REPORT response result code."""
        self.last_set_report_result = result_code

    def set_get_protocol(self, result_code, protocol):
        """Store the latest GET_PROTOCOL response."""
        self.last_get_protocol = (result_code, protocol)

    def set_set_protocol(self, result_code):
        """Store the latest SET_PROTOCOL response result code."""
        self.last_set_protocol_result = result_code

    def cleanup(self):
        """Cleanup HID Host resources"""
        log(f"{self.cleanup.__name__}")
        self.connected = False
        self.connected_addr = None
        self.last_input_report = None
        self.last_get_report = None
        self.last_set_report_result = None
        self.last_get_protocol = None
        self.last_set_protocol_result = None
