#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Nordic Semiconductor ASA.
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


class NLCP:
    def __init__(self):
        self.event_queues = {}

        # Identity report
        self.ident_is_valid = False
        self.ident_iut_uuid = None  # 16 bytes max

    def set_identity_report(self, uuid):
        self.ident_iut_uuid = bytes(uuid).hex()
        self.ident_is_valid = True

    def get_identity_uuid(self):
        return self.ident_iut_uuid
