#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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
import sys
from typing import Protocol

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self):
            return self.value


class AutoPTSMode(StrEnum):
    # The mode only for unit tests, autopts server is mocked, no PTS instance is opened.
    FAKE_PROXY = 'fake_proxy'
    # In this mode the PTS is opened in GUI mode and the autopts client provides
    # the window for entering MMI/WID. The autopts server should not be running.
    GUI_CLIENT_ONLY = 'gui_client_only'
    # In this mode the PTS is opened in the automation mode by the autopts server.
    # The autopts client communicates with the autopts server via TCP/IP.
    AUTO_TCP_IP = 'auto_tcp_ip'
    # In this mode the autopts server functionality is handled by the autopts client and
    # the PTS is opened in the automation mode by the autopts client. Works only for Windows.
    AUTO_CLIENT_ONLY = 'auto_client_only'


class PTSProxy(Protocol):
    """Interface implemented by all PTS proxy instances."""
