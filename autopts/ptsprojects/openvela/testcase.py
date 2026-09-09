#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""Test case that manages the openvela IUT.

Drives the IUT lifecycle (start, wait ready, read supported services, run the
test case commands, clean up) for a bttester DUT in QEMU over TCP.
"""

from autopts.ptsprojects.testcase import TestCaseLT1, TestFunc, TestFuncCleanUp
from autopts.pybtp.btp import get_iut


class OpenVelaTestCase(TestCaseLT1):
    """An openvela test case whose DUT is bttester running in QEMU over TCP."""

    def __init__(self, *args, **kwargs) -> None:
        """Refer to ``TestCase.__init__`` for parameters and their documentation."""

        super().__init__(*args, ptsproject_name="openvela", **kwargs)

        self.cmds.insert(0, TestFunc(self._test_case_start))
        self.cmds.append(TestFuncCleanUp(self._test_case_cleanup))

    def _test_case_start(self) -> None:
        """Bring the IUT up before the test case commands run."""

        iut = get_iut()

        for iut_id in range(self.iut_count):
            if hasattr(iut, 'select_iut'):
                iut.select_iut(iut_id)

            # Init stack.core to be able to receive the IUT ready event.
            iut.get_stack().core_init()
            # Open the BTP socket and connect to bttester.
            iut.start(self)
            # Await the IUT ready event.
            iut.wait_iut_ready_event(False)
            # Read the BTP services the IUT supports.
            iut.get_supported_svcs()

        if hasattr(iut, 'select_iut'):
            iut.select_iut(0)

    def _test_case_cleanup(self) -> None:
        """Reset the IUT after the test case commands have run."""

        iut = get_iut()

        for iut_id in range(self.iut_count):
            if hasattr(iut, 'select_iut'):
                iut.select_iut(iut_id)

            iut.stack.cleanup()

            # For openvela this closes the BTP socket but keeps bttester
            # running, waiting for the next connection.
            iut.stop()

        if hasattr(iut, 'select_iut'):
            iut.select_iut(0)
