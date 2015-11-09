"""Test case that manages Zephyr QEMU"""

from ptsprojects.testcase import TestCase, TestFunc, \
    TestFuncCleanUp
from ptsprojects.zephyr.iutctl import get_zephyr

class QTestCase(TestCase):
    """A test case that uses QEMU as DUT"""

    def __init__(self, project_name, test_case_name, cmds = [], no_wid = None,
                 edit1_wids = None, verify_wids = None):
        """
        cmds -- a list of TestCmd and TestFunc or single instance of them

        no_wid -- a wid (tag) to respond No to

        edit1_wids -- A dictionary of wids as keys and string input as values.
                      The value is send to PTS in response to MMI_Style_Edit1
                      style prompts with matching wid.

        verify_wids -- A dictionary of wids as keys and a tuple of strings as
                       values. The strings are used with MMI_Style_Yes_No1 to
                       confirm/verify that the MMI description contains all of
                       the strings in the tuple.
        """

        super(QTestCase, self).__init__(project_name,
                                        test_case_name,
                                        cmds,
                                        no_wid,
                                        edit1_wids,
                                        verify_wids)

        self.zephyrctl = get_zephyr()

        # first command is to start QEMU
        self.cmds.insert(0, TestFunc(self.zephyrctl.start))

        # last command is to stop QEMU
        self.cmds.append(TestFuncCleanUp(self.zephyrctl.stop))
