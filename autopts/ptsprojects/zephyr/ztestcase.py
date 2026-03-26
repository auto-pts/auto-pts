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

        self.cmds.insert(0, TestFunc(self._test_case_start))
        self.cmds.append(TestFuncCleanUp(self._test_case_cleanup))

    def _test_case_start(self):
        iut = get_iut()

        for iut_id in range(self.iut_count):
            if hasattr(iut, 'select_iut'):
                iut.select_iut(iut_id)

            # Init stack.core to be able to receive IUT ready event
            iut.get_stack().core_init()
            # Open BTP socket and start IUT
            iut.start(self)
            # Await IUT ready event
            iut.wait_iut_ready_event(False)

            if iut.iut_mode == "native":
                iut.remove_flash_bin()

        if hasattr(iut, 'select_iut'):
            iut.select_iut(0)

    def _test_case_cleanup(self):
        iut = get_iut()

        for iut_id in range(self.iut_count):
            if hasattr(iut, 'select_iut'):
                iut.select_iut(iut_id)

            iut.stack.cleanup()

            # Last command is to stop QEMU or HW.
            # For HW, this will trigger the HW reset and the IUT ready event.
            # The event will be used in the next test case, to skip double reset.
            iut.stop()

        if hasattr(iut, 'select_iut'):
            iut.select_iut(0)


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
