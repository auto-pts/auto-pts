"""Test case that manages Viper QEMU"""

from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
    TestFuncCleanUp
from ptsprojects.viper.iutctrl import ViperCtl

class QTestCase(TestCase):
        """A test case that uses QEMU as DUT"""

        def __init__(self, project_name, test_case_name, cmds = [], no_wid = None):
            """cmds - a list of TestCmd and TestFunc or single instance of them
            no_wid - a wid (tag) to respond No to"""

            super(QTestCase, self).__init__(project_name,
                                            test_case_name,
                                            cmds,
                                            no_wid)

            self.viperctl = ViperCtl()

            # first command is to start QEMU
            self.cmds.insert(0, TestFunc(self.viperctl.start))

            # last command is to stop QEMU
            self.cmds.append(TestFuncCleanUp(self.viperctl.stop))
