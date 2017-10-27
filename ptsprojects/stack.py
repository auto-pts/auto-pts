#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Codecoup.
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

import uuid

STACK = None

class Mesh():
    def __init__(self, dev_uuid):
        self.dev_uuid = uuid.UUID(dev_uuid)

class Stack():
    def __init__(self):
        self.mesh = None

    def mesh_init(self, dev_uuid):
        self.mesh = Mesh(dev_uuid)

def init_stack():
    global STACK

    STACK = Stack()

def cleanup_stack():
    global STACK

    STACK = None

def get_stack():
    return STACK
