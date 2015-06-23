"""Test case that manages Zephyr QEMU"""

from ptsprojects.testcase import TestCase, TestFunc, \
    TestFuncCleanUp
from ptsprojects.zephyr.iutctl import ZephyrCtl

class QTestCase(TestCase):
        """A test case that uses QEMU as DUT"""

        def __init__(self, project_name, test_case_name, cmds = [], no_wid = None):
            """cmds - a list of TestCmd and TestFunc or single instance of them
            no_wid - a wid (tag) to respond No to"""

            super(QTestCase, self).__init__(project_name,
                                            test_case_name,
                                            cmds,
                                            no_wid)

            self.zephyrctl = ZephyrCtl()

            # first command is to start QEMU
            self.cmds.insert(0, TestFunc(self.zephyrctl.start))

            # last command is to stop QEMU
            self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))
