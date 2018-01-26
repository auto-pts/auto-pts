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
from ptsprojects.bluez.iutctl import get_iut

from pybtp import btp


class BTestCase(TestCase):
    """A Bluez test case class"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(BTestCase, self).__init__(*args, ptsproject_name="bluez",
                                        **kwargs)

        self.cmds.insert(0, TestFunc(btp.core_reg_svc_gap))
        self.cmds.insert(1, TestFunc(btp.gap_set_powered_on))

        self.cmds.append(TestFuncCleanUp(btp.gap_reset))
        self.cmds.append(TestFuncCleanUp(btp.gap_set_powered_off))
        self.cmds.append(TestFuncCleanUp(btp.core_unreg_svc_gap))
