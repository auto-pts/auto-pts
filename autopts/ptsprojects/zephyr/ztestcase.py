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

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestCaseLT3, TestFunc, TestFuncCleanUp
from autopts.ptsprojects.zephyr.iutctl import get_iut


class ZTestCase(TestCaseLT1):
    """A Zephyr test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="zephyr", **kwargs)

        self.stack = get_stack()
        self.zephyrctl = get_iut()

        self.cmds.insert(0, TestFunc(self.stack.core_init))

        # For HW, the IUT ready event is triggered at its reset and
        # can be only received after socket is successfully running.
        # This hw_reset will be active only at the first test case.
        self.cmds.insert(1, TestFunc(self.zephyrctl.hw_reset))

        # This will open BTP socket and start QEMU process.
        # For QEMU, the IUT ready event is sent at startup of the process.
        self.cmds.insert(2, TestFunc(self.zephyrctl.start, self))

        # Now socket should be open for IUT ready event from HW.
        # This hw_reset will be active only at the first test case.
        self.cmds.insert(3, TestFunc(self.zephyrctl.hw_reset))
        self.cmds.insert(4, TestFunc(self.zephyrctl.wait_iut_ready_event, False))

        self.cmds.append(TestFuncCleanUp(self.stack.cleanup))

        # Last command is to stop QEMU or HW.
        # For HW, this will trigger the HW reset and the IUT ready event.
        # The event will be used in the next test case, to skip double reset.
        self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))


class ZTestCaseSlave(TestCaseLT2):
    """A Zephyr helper test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="zephyr", **kwargs)


class ZTestCaseSlave2(TestCaseLT3):
    """A Zephyr helper test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="zephyr", **kwargs)
