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

from ptsprojects.testcase import TestCase, TestFunc, \
    TestFuncCleanUp
from ptsprojects.stack import get_stack
from ptsprojects.zephyr.iutctl import get_iut


class ZTestCase(TestCase):
    """A Zephyr test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(ZTestCase, self).__init__(*args, ptsproject_name="zephyr",
                                        **kwargs)

        self.stack = get_stack()
        self.zephyrctl = get_iut()

        # first command is to start QEMU or HW
        self.cmds.insert(0, TestFunc(self.zephyrctl.start))
        self.cmds.insert(1, TestFunc(self.zephyrctl.wait_iut_ready_event))

        self.cmds.append(TestFuncCleanUp(self.stack.cleanup))
        # last command is to stop QEMU or HW
        self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))


class ZTestCaseSlave(TestCase):
    """A Zephyr helper test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(ZTestCaseSlave, self).__init__(*args, ptsproject_name="zephyr",
                                             **kwargs)
