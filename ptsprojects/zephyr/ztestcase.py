"""Test case that manages Zephyr IUT"""

from ptsprojects.testcase import TestCase, TestFunc, \
    TestFuncCleanUp
from ptsprojects.zephyr.iutctl import get_zephyr


class ZTestCase(TestCase):
    """A Zephyr test case that uses QEMU or HW as DUT"""

    def __init__(self, *args, **kwargs):
        """Refer to TestCase.__init__ for parameters and their documentation"""

        super(ZTestCase, self).__init__(*args, **kwargs)

        self.zephyrctl = get_zephyr()

        # first command is to start QEMU or HW
        self.cmds.insert(0, TestFunc(self.zephyrctl.start))

        # last command is to stop QEMU or HW
        self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))
