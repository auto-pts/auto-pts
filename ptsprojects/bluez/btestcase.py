#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

"""Test case that manages Zephyr IUT"""

from ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestFunc, \
    TestFuncCleanUp
from ptsprojects.stack import get_stack
from ptsprojects.bluez.iutctl import get_iut

class BTestCase(TestCaseLT1):
    """A Bluez test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(BTestCase, self).__init__(*args, ptsproject_name="bluez",
                                        **kwargs)

        self.stack = get_stack()
        self.bluezctrl = get_iut()

        # first command is to start bluez btpclient
        self.cmds.insert(0, TestFunc(self.bluezctrl.start))
        self.cmds.insert(1, TestFunc(self.bluezctrl.wait_iut_ready_event))

        self.cmds.append(TestFuncCleanUp(self.stack.cleanup))
        # last command is to stop bluez btpclient
        self.cmds.append(TestFuncCleanUp(self.bluezctrl.stop))


class BTestCaseSlave(TestCaseLT2):
    """ BlueZ helper test case as a 2nd uint """

    def __init__(self, *args, **kwargs):
        """ Refer to TestCase.__init__ for parameters and their documentation"""

        super(BTestCaseSlave, self).__init__(*args,
                                             ptsproject_name="bluez",
                                             **kwargs)
