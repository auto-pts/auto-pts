"""PTS test case python implementation"""

import time
import logging

from utils import exec_iut_cmd
import ptstypes

log = logging.debug

class TestCmd:
    """A command ran in IUT during test case execution"""

    def __init__(self, command, start_wid = None, stop_wid = None):
        """stop_wid - some test cases require the child process (this test command) to
                      be termintated (Ctrl-C on terminal) in response to dialog
                      with this wid
        """
        self.command = command
        self.start_wid = start_wid
        self.stop_wid = stop_wid
        self.process = None
        self.__started = False

    def start(self):
        """Starts the command"""
        if self.__started:
            return

        self.__started = True

        log("starting child process %s" % self)
        self.process = exec_iut_cmd(self.command)

    def stop(self):
        """Stops the command"""
        if not self.__started:
            return

        log("stopping child process %s" % self)
        self.process.kill()

    def __str__(self):
        """Returns string representation"""
        return "%s %s %s" % (self.command, self.start_wid, self.stop_wid)

class TestFunc:
    """Some test commands, like setting PIXIT, PICS are functions. This is a
    wrapper around functions"""

    def __init__(self, func, *args, **kwds):
        """Constructor"""
        self.__func = func
        self.__args = args
        self.__kwds = kwds
        self.start_wid = None
        self.stop_wid = None

    def start(self):
        """Starts the function"""
        log("Starting test function: %s" % str(self))
        self.__func(*self.__args, **self.__kwds)

    def stop(self):
        """Does nothing, since not easy job to stop a function"""
        pass

    def __str__(self):
        """Returns string representation"""
        return "%s %s %s" % (self.__func, self.__args, self.__kwds)

class TestFuncCleanUp(TestFunc):
    """Clean-up function that is invoked after running test case in PTS."""
    pass

def is_cleanup_func(func):
    """'Retruns True if func is an in an instance of TestFuncCleanUp"""
    return isinstance(func, TestFuncCleanUp)

class AbstractMethodException(Exception):
    """Exception raised if an abstract method is called."""
    pass

class PTSCallback:
    """Base class for PTS callback implementors"""

    def __init__(self):
        pass

    def log(self, log_type, logtype_string, log_time, log_message):
        """Implements:

        interface IPTSControlClientLogger : IUnknown {
            HRESULT _stdcall Log(
                            [in] _PTS_LOGTYPE logType,
                            [in] LPWSTR szLogType,
                            [in] LPWSTR szTime,
                            [in] LPWSTR pszMessage);
        };
        """
        raise AbstractMethodException()

    def on_implicit_send(self, project_name, wid, test_case_name, description,
                         style, response, response_size, response_is_present):
        """Implements:

        interface IPTSImplicitSendCallbackEx : IUnknown {
        HRESULT _stdcall OnImplicitSend(
                    [in] LPWSTR pszProjectName,
                    [in] unsigned short wID,
                    [in] LPWSTR pszTestCase,
                    [in] LPWSTR pszDescription,
                    [in] unsigned long style,
                    [in, out] LPWSTR pszResponse,
                    [in] unsigned long responseSize,
                    [in, out] long* pbResponseIsPresent);
        };

        return -- response as a python string
        """
        raise AbstractMethodException()

class TestCase(PTSCallback):
    """A PTS test case"""

    def __init__(self, project_name, test_case_name, cmds = [], no_wid = None):
        """cmds - a list of TestCmd and TestFunc or single instance of them
        no_wid - a wid (tag) to respond No to"""
        self.project_name = project_name
        self.name = test_case_name
        # a.k.a. final verdict
        self.status = "init"

        if isinstance(cmds, list):
            self.cmds = cmds
        else:
            self.cmds = [cmds]

        if no_wid is not None and not isinstance(no_wid, int):
            raise Exception("no_wid should be int, and not %s" % (repr(no_wid),))

        self.no_wid = no_wid

    def __str__(self):
        """Returns string representation"""
        return "%s %s" % (self.project_name, self.name)

    def log(self, log_type, logtype_string, log_time, log_message):
        """Overrides PTSCallback method. Handles
        PTSControl.IPTSControlClientLogger.Log"""

        new_status = None

        # mark test case as started
        if log_type == ptstypes.PTS_LOGTYPE_START_TEST
            new_status = "Started"

        # mark the final verdict of the test case
        elif log_type == ptstypes.PTS_LOGTYPE_FINAL_VERDICT and \
             logtype_string == "Final verdict": # avoid "Encrypted Verdict"

            if "PASS" in log_message:
                new_status = "PASS"
            elif "INCONC" in log_message:
                new_status = "INCONC"
            elif "FAIL" in log_message:
                new_status = "FAIL"
            else:
                new_status = "UNKNOWN VERDICT: %s" % log_message

        if new_status:
            self.status = new_status
            log("New status %s - %s", str(self), new_status)

    def on_implicit_send(self, project_name, wid, test_case_name, description, style,
                         response, response_size, response_is_present):
        """Overrides PTSCallback method. Handles
        PTSControl.IPTSImplicitSendCallbackEx.OnImplicitSend"""
        log("%s %s", self, self.on_implicit_send.__name__)

        # this should never happen, pts does not run tests in parallel
        assert project_name == self.project_name and \
            test_case_name == self.name

        my_response = ""

        # MMI_Style_Yes_No1
        if style == 0x11044:
            # answer No
            if self.no_wid and wid == self.no_wid:
                my_response = "No"

            # answer Yes
            else:
                my_response = "Yes"

        # actually style == 0x11141, MMI_Style_Ok_Cancel2
        else:
            my_response = "OK"

        # start/stop command if triggered by wid
        for cmd in self.cmds:
            # start command
            if cmd.start_wid == wid:
                cmd.start()

            # stop command
            if cmd.stop_wid == wid:
                cmd.stop()

        return my_response

    def pre_run(self):
        """Method called before test case is run in PTS"""
        log("%s %s %s" % (self.pre_run.__name__, self.project_name, self.name))

        log("About to run test case %s %s with commands:" %
            (self.project_name, self.name))
        for cmd in self.cmds:
            log(cmd)

        # start commands that don't have start trigger (lack start_wid) and are
        # not cleanup functions
        for cmd in self.cmds:
            if cmd.start_wid is None and not is_cleanup_func(cmd):
                cmd.start()

    def post_run(self):
        """Method called after test case is run in PTS"""
        log("%s %s %s" % (self.post_run.__name__, self.project_name, self.name))

        # run the clean-up commands
        for cmd in self.cmds:
            if is_cleanup_func(cmd):
                cmd.start()

        # in accordance with PTSControlClient.cpp:
        # // Allow device to settle down
        # Sleep(3000);
        # otherwise 4th test case just blocks eternally
        time.sleep(3)

        for cmd in self.cmds:
            cmd.stop()

def get_max_test_case_desc(test_cases):
    """Takes a list of test cases and return a tuple of longest project name
    and test case name."""

    max_project_name = 0
    max_test_case_name = 0

    for test_case in test_cases:
        project_name_len = len(test_case.project_name)
        test_case_name_len = len(test_case.name)

        if project_name_len > max_project_name:
            max_project_name = project_name_len

        if test_case_name_len > max_test_case_name:
            max_test_case_name = test_case_name_len

    return (max_project_name, max_test_case_name)
