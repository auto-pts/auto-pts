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

"""Test case that manages Mynewt IUT"""

from autopts.ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestFunc, \
    TestFuncCleanUp
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.mynewt.iutctl import get_iut


class ZTestCase(TestCaseLT1):
    """A Mynewt test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="mynewt", **kwargs)

        self.stack = get_stack()
        self.mynewtctl = get_iut()

        # first command is to start QEMU or HW
        self.cmds.insert(0, TestFunc(self.mynewtctl.start, self))
        self.cmds.insert(1, TestFunc(self.mynewtctl.wait_iut_ready_event))
        self.cmds.insert(2, TestFunc(self.mynewtctl.get_supported_svcs))

        self.cmds.append(TestFuncCleanUp(self.stack.cleanup))
        # last command is to stop QEMU or HW
        self.cmds.append(TestFuncCleanUp(self.mynewtctl.stop))


class ZTestCaseSlave(TestCaseLT2):
    """A Mynewt helper test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="mynewt", **kwargs)
