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

from autopts.ptsprojects.testcase import TestCaseLT1, TestCaseLT2, TestCaseLT3, TestFunc, TestFuncCleanUp
from autopts.pybtp.btp import get_iut


class ZTestCase(TestCaseLT1):
    """A Zephyr test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super().__init__(*args, ptsproject_name="zephyr", **kwargs)

        i = 0

        for _id in range(self.iut_count):
            iut = get_iut(iutctl_id=_id)
            if iut is None:
                break

            # Init stack.core to be able to receive IUT ready event
            self.cmds.insert(i, TestFunc(iut.get_stack().core_init))
            # Open BTP socket and start IUT
            self.cmds.insert(i + 1, TestFunc(iut.start, self))
            # Await IUT ready event
            self.cmds.insert(i + 2, TestFunc(iut.wait_iut_ready_event, False))
            off = 3

            if iut.iut_mode == "native":
                self.cmds.insert(i, TestFunc(iut.remove_flash_bin))
                off += 1

            i += off

            self.cmds.append(TestFuncCleanUp(iut.stack.cleanup))

            # Last command is to stop QEMU or HW.
            # For HW, this will trigger the HW reset and the IUT ready event.
            # The event will be used in the next test case, to skip double reset.
            self.cmds.append(TestFuncCleanUp(iut.stop))

            _id += 1


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
