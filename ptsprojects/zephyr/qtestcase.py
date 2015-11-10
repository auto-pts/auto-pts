"""Test case that manages Zephyr QEMU"""

from ptsprojects.testcase import TestCase, TestFunc, \
    TestFuncCleanUp
from ptsprojects.zephyr.iutctl import get_zephyr

class QTestCase(TestCase):
    """A test case that uses QEMU as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(QTestCase, self).__init__(*args, **kwargs)

        self.zephyrctl = get_zephyr()

        # first command is to start QEMU
        self.cmds.insert(0, TestFunc(self.zephyrctl.start))

        # last command is to stop QEMU
        self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))
