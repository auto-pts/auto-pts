"""PTS test case python implementation"""

import re
import time
import logging

from utils import exec_iut_cmd
import ptstypes

log = logging.debug

class MmiParser(object):
    """"Interface to parsing arguments from description of MMI

    It is assumed that all arguments in description are enclosed in single
    quotes.

    """

    min_arg = 1
    # hopefully this is the max number of arguments in MMI description
    max_arg = 10

    arg_name_prefix = "arg_"
    arg_value_prefix = "MMI_arg_value_"

    def __init__(self):
        """Constructor of the parser"""

        # pattern used to search for args in MMI description
        self.pattern = re.compile(r"(?:'|=\s+)([0-9-xA-Fa-f]+)")

        # list of the parsed argument values from MMI description
        self.args = []

        # create attributes to reference the args
        for i in range(self.min_arg, self.max_arg):
            index = str(i)
            mmi_arg_name = self.arg_name_prefix + index
            mmi_arg_value = self.arg_value_prefix + index
            setattr(self, mmi_arg_name, mmi_arg_value)

    def parse_description(self, description):
        """Parses PTS MMI description text for argument values. It is necessary to do
        it for now, but in future PTS will provide API to get the values

        An example of MMI that requires parsing is listed below. For that MMI
        00D3 should be converted to hexadecimal 0xD3 and size to int 45

        project_name: GATT
        wid: 69
        test_case_name: TC_GAC_CL_BV_01_C

        Please send prepare write request with handle = '00D3'O and size = '45' to the PTS.

        Description: Verify that the Implementation Under Test (IUT) can send data according to negotiate MTU size."

        """
        log("%s %r", self.parse_description.__name__, description)

        self.args = self.pattern.findall(description)

        log("Parse result: %r", self.args)

    def reset(self):
        """Resets the args

        To be used when parsed values are not needed anymore

        """
        self.args = []

    def process_args(self, args):
        """Replaces the MMI keywords arguments (e.g. MMI.arg_1) with the respective
        argument values from MMI description

        """
        log("%s: %s", self.process_args.__name__, args)
        log("MMI.args now %r", self.args)

        args_list = list(args)

        for arg_index, arg in enumerate(args):
            if not isinstance(arg, basestring): # omit not strings
                continue

            if arg.startswith(MMI.arg_value_prefix):
                mmi_index = int(arg[arg.rfind("_") + 1:])

                args_list[arg_index] = self.args[mmi_index - 1]

        out_args = tuple(args_list)
        log("returning %r", out_args)
        return out_args

MMI = MmiParser()

class TestCmd:
    """A command ran in IUT during test case execution"""

    def __init__(self, command, start_wid = None, stop_wid = None):
        """stop_wid -- some test cases require the child process (this test command) to
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
    """A wrapper around test functions"""

    def __init__(self, func, *args, **kwds):
        """Constructor of TestFunc

        MMI.arg_X -- Passing these keywords in args would enable parsing the
                     description of PTS MMI for values. Each of the keywords
                     has the value of the description. For example: for
                     description "Please send prepare write request with handle
                     = '00D3'O and size = '45' to the PTS" MMI.arg_1 will have
                     the value 0xD3 and MMI.arg_2 will have the value 45

        start_wid -- wid to start TestFunc

        stop_wid -- not used by TestFunc, because function stopping is not easy
                    to implement. Provided only for compatibility with TestCmd.

        start_wid and stop_wid must be passed in as keyword arguments. This is
        because all other arguments will be passed to the func. For example:

        TestFunc(my_function, arg1, arg2, kwd1 = 5, start_wid = 117)

        """
        self.func = func
        self.__read_start_stop_wids(kwds)
        self.args = args
        self.kwds = kwds

        # true if parsing of MMI description text is needed by this test func
        self.desc_parsing_needed = False

        for arg in args:
            if isinstance(arg, str) and arg.startswith(MMI.arg_value_prefix):
                self.desc_parsing_needed = True
                break

    def __read_start_stop_wids(self, kwds):
        """Reads start_wid and stop_wid from arbitrary keyword argument
        dictionary.

        start_wid and stop_wid are not specified in the constructor as normal
        aruments cause they are not always used and when not used they would be
        consuming function (func) arguments (args).

        start_wid and stop_wid are used by this class and not passed to the
        func, hence they are removed from kwds.

        Note: with test functions stop_wid is only there to be compatible with
        TestCmd interface. But since functions cannot be stopped, stop_wid is
        useless.

        kwds -- arbitrary keyword argument dictionary

        """
        arg_names = ["start_wid", "stop_wid"]

        for arg_name in arg_names:
            if arg_name in kwds:
                arg_value = kwds.pop(arg_name)
            else:
                arg_value = None

            setattr(self, arg_name, arg_value)

    def start(self):
        """Starts the function"""
        log("Starting test function: %s" % str(self))


        if self.desc_parsing_needed:
            args = MMI.process_args(self.args)
        else:
            args = self.args

        log("Test function parameters: args=%r, kwds=%r", args, self.kwds)

        self.func(*args, **self.kwds)

    def stop(self):
        """Does nothing, since not easy job to stop a function"""
        pass

    def __str__(self):
        """Returns string representation"""
        return "%s %s %s %s %s %s" % \
            (self.__class__, self.func, self.start_wid, self.stop_wid,
             self.args, self.kwds)

class TestFuncCleanUp(TestFunc):
    """Clean-up function that is invoked after running test case in PTS."""
    pass

def is_cleanup_func(func):
    """'Retruns True if func is an in an instance of TestFuncCleanUp"""
    return isinstance(func, TestFuncCleanUp)

class AbstractMethodException(Exception):
    """Exception raised if an abstract method is called."""
    pass

class PTSCallback(object):
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

    def __init__(self, project_name, test_case_name, cmds = [], no_wid = None,
                 edit1_wids = None, verify_wids = None):
        """TestCase constructor

        cmds -- a list of TestCmd and TestFunc or single instance of them

        no_wid -- a wid (tag) to respond No to

        edit1_wids -- A dictionary of wids as keys and string or callable as
                      values. The string value or the string returned from the
                      callable value is send to PTS in response to
                      MMI_Style_Edit1 style prompts with matching wid.

        verify_wids -- A dictionary of wids as keys and a tuple of strings as
                       values or a callable as value. The strings are used with
                       MMI_Style_Yes_No1 to confirm/verify that the MMI
                       description contains all of the strings in the tuple. If
                       the value is callable it will be passed PTS MMI
                       description as a parameter. It is expected to return
                       boolean True for the Yes and False for the No response
                       of MMI_Style_Yes_No1.

        """
        log("%r %r %r %r %r %r", project_name, test_case_name, cmds, no_wid,
            edit1_wids, verify_wids)

        self.project_name = project_name
        self.name = test_case_name
        # a.k.a. final verdict
        self.status = "init"

        if isinstance(cmds, list):
            self.cmds = list(cmds)
        else:
            self.cmds = [cmds]

        # catch test case implementation syntax errors
        if no_wid:
            assert isinstance(no_wid, int), \
                "no_wid should be int, and not %r" % no_wid
        if edit1_wids:
            assert isinstance(edit1_wids, dict), \
                "edit1_wids should be dict, and not %r" % edit1_wids
        if verify_wids:
            assert isinstance(verify_wids, dict), \
                "verify_wids should be dict, and not %r" % verify_wids

        self.no_wid = no_wid
        self.edit1_wids = edit1_wids
        self.verify_wids = verify_wids

    def __str__(self):
        """Returns string representation"""
        return "%s %s" % (self.project_name, self.name)

    def log(self, log_type, logtype_string, log_time, log_message):
        """Overrides PTSCallback method. Handles
        PTSControl.IPTSControlClientLogger.Log"""

        new_status = None

        # mark test case as started
        if log_type == ptstypes.PTS_LOGTYPE_START_TEST:
            new_status = "Started"

        # mark the final verdict of the test case
        # check for "final verdict" to avoid "Encrypted Verdict"
        # it could be 'Final verdict' or 'Final Verdict'
        elif log_type == ptstypes.PTS_LOGTYPE_FINAL_VERDICT and \
             logtype_string.lower() == "final verdict":

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


    def handle_mmi_style_yes_no1(self, wid, description):
        """Implements implicit send handling for MMI_Style_Yes_No1"""
        log("%s, %r %r", self.handle_mmi_style_yes_no1.__name__,
            wid, description)

        log("no_wid=%r verify_wids=%r", self.no_wid, self.verify_wids)

        yes_response = "Yes"
        no_response = "No"
        my_response = ""

        # answer No
        if self.no_wid and wid == self.no_wid:
            my_response = no_response

        # answer No if description does not contain text from verify_wids
        elif self.verify_wids and wid in self.verify_wids:
            log("Starting verification of: %r", self.verify_wids)

            if callable(self.verify_wids[wid]):
                resp = self.verify_wids[wid](description)
                my_response = {True: yes_response, False: no_response}[resp]

            else:
                for verify in self.verify_wids[wid]:
                    log("Verifying: %r", verify)
                    if verify not in description:
                        log("Verification failed: not in description")
                        my_response = no_response
                        break
                else:
                    log("All verifications passed")
                    my_response = yes_response

        # answer Yes
        else:
            my_response = yes_response

        # log warning if confimation/verification is unhandled
        if not self.verify_wids or wid not in self.verify_wids:
            search_strings = ["confirm", "verify"]

            if any(str in description.lower() for str in search_strings):
                logging.warning("Verification missing for: %r", description)

        return my_response

    def handle_mmi_style_edit1(self, wid):
        """Implements implicit send handling for MMI_Style_Edit1"""
        log("%s, %r edit1_wids=%r", self.handle_mmi_style_edit1.__name__, wid,
            self.edit1_wids)

        my_response = ""

        if self.edit1_wids and wid in self.edit1_wids.keys():
            response = self.edit1_wids[wid]
            if callable(response):
                my_response = response()
            else:
                my_response = response

        return my_response

    def start_stop_cmds_by_wid(self, wid, description):
        """Starts/stops commands

        The commands started/stopped are the ones that have the same start_wid
        or stop_wid as the argument

        """
        for cmd in self.cmds:
            # start command
            if cmd.start_wid == wid:
                if cmd.desc_parsing_needed:
                    MMI.parse_description(description)

                cmd.start()

                if cmd.desc_parsing_needed: # clear parsed description
                    MMI.reset()

            # stop command
            if cmd.stop_wid == wid:
                cmd.stop()

    def on_implicit_send(self, project_name, wid, test_case_name, description, style,
                         response, response_size, response_is_present):
        """Overrides PTSCallback method. Handles
        PTSControl.IPTSImplicitSendCallbackEx.OnImplicitSend"""
        log("%s %s", self, self.on_implicit_send.__name__)

        # this should never happen, pts does not run tests in parallel
        # TODO - This is a temporary solution for PTS bug #14270
        # assert project_name == self.project_name, \
        #   "Unexpected project name %r should be %r" % \
        #    (project_name, self.project_name)

        assert test_case_name == self.name, \
            "Unexpected test case name %r should be %r" % \
            (test_case_name, self.name)

        my_response = ""

        if style == ptstypes.MMI_Style_Yes_No1:
            my_response = self.handle_mmi_style_yes_no1(wid, description)

        elif style == ptstypes.MMI_Style_Edit1:
            my_response = self.handle_mmi_style_edit1(wid)

        # actually style == MMI_Style_Ok_Cancel2
        else:
            my_response = "OK"

        # start/stop command if triggered by wid
        self.start_stop_cmds_by_wid(wid, description)

        log("Sending response %r", my_response)
        return my_response

    def pre_run(self):
        """Method called before test case is run in PTS"""
        log("%s %s %s" % (self.pre_run.__name__, self.project_name, self.name))

        log("About to run test case %s %s with commands:" %
            (self.project_name, self.name))
        for index, cmd in enumerate(self.cmds):
            log("%d) %s", index, cmd)

        # start commands that don't have start trigger (lack start_wid) and are
        # not cleanup functions
        for cmd in self.cmds:
            if cmd.start_wid is None and not is_cleanup_func(cmd):
                cmd.start()

    def post_run(self, error_code):
        """Method called after test case is run in PTS

        error_code -- String code of an error that occured during test run
        """
        log("%s %s %s %s" % (self.post_run.__name__, self.project_name,
                             self.name, error_code))

        if error_code in ptstypes.PTSCONTROL_E_STRING.values():

            # shortened status for timeout
            if error_code == ptstypes.PTSCONTROL_E_STRING[
                    ptstypes.PTSCONTROL_E_TESTCASE_TIMEOUT]:
                self.status = "TIMEOUT"
            else:
                self.status = error_code

        elif error_code:
            raise Exception("Unknown error code %r!" % error_code)

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
