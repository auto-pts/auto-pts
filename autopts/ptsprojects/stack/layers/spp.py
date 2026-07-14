#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026, NXP.
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

class SPP:
    """
    SPP (Serial Port Profile) layer implementation
    """
    def __init__(self):
        """Initialize SPP layer"""
        log(f"{self.__init__.__name__}")
        self.discovered_addr = None
        self.discovered_addr_type = None
        self.discovered_channel = None

    def wait_for_discovered(self, timeout=30):
        """
        Wait for SPP service discovery to complete.

        Args:
            timeout (int): Maximum time to wait in seconds (default: 30)

        Returns:
            bool: True if discovery completed successfully, False otherwise
        """
        logging.debug("%s timeout=%d", self.wait_for_discovered.__name__, timeout)

        return wait_for_event(timeout, lambda: self.discovered_channel is not None)

    def set_discovered(self, addr, addr_type, channel):
        """
        Set the discovered service information when SPP service is found.

        Args:
            addr (str): Bluetooth address of the discovered device
            addr_type (int): Address type
            channel (int): RFCOMM channel number
        """
        self.discovered_addr = addr
        self.discovered_addr_type = addr_type
        self.discovered_channel = channel

    def cleanup(self):
        """Cleanup SPP resources"""
        log(f"{self.cleanup.__name__}")
        self.discovered_addr = None
        self.discovered_addr_type = None
        self.discovered_channel = None
