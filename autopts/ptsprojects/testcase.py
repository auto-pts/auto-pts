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

"""PTS test case python implementation"""

import datetime
import errno
import logging
import os
import queue
import re
import shlex
import subprocess
import sys
import time

from autopts.utils import get_global_end

from . import ptstypes
from .stack import get_stack
from .utils import exec_iut_cmd

log = logging.debug


class ResponseWithPostWID:
    def __init__(self, response, next_steps):
        self.response = response
        self.next_steps = next_steps


class MmiParser:
    """Interface to parsing arguments from description of MMI

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
        """Parse PTS MMI description text for argument values.

        It is necessary to do it for now, but in future PTS will provide API to
        get the values

        An example of MMI that requires parsing is listed below. For that MMI
        00D3 should be converted to hexadecimal 0xD3 and size to int 45

        project_name: GATT
        wid: 69
        test_case_name: TC_GAC_CL_BV_01_C

        Please send prepare write request with handle = '00D3'O and size = '45'
        to the PTS.

        Description: Verify that the Implementation Under Test (IUT) can send
        data according to negotiate MTU size.

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
        """Replaces the MMI keywords arguments (e.g. MMI.arg_1) with the
        respective argument values from MMI description

        """
        log("%s: %s", self.process_args.__name__, args)
        log("MMI.args now %r", self.args)

        args_list = list(args)

        for arg_index, arg in enumerate(args):
            if not isinstance(arg, str):  # omit not strings
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

    def __init__(self, command, start_wid=None, stop_wid=None):
        """Constructor

        stop_wid -- some test cases require the child process (this test
                    command) to be termintated (Ctrl-C on terminal) in response
                    to dialog with this wid

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

        log(f"starting child process {self}")
        self.process = exec_iut_cmd(self.command)

    def stop(self):
        """Stops the command"""
        if not self.__started:
            return

        log(f"stopping child process {self}")
        self.process.kill()

    def __str__(self):
        """Returns string representation"""
        return f"{self.command} {self.start_wid} {self.stop_wid}"


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

        post_wid -- start TestFunc on the next MMI after MMI with this wid

        skip_call -- a tuple of integers of func call numbers to skip.
                     Starting from one so first call is 1.

        start_wid and stop_wid must be passed in as keyword arguments. This is
        because all other arguments will be passed to the func. For example:

        TestFunc(my_function, arg1, arg2, kwd1=5, start_wid=117)

        """
        self.skip_call = None
        self.start_wid = None
        self.stop_wid = None
        self.post_wid = None
        self.func = func
        self.__set_attrs(kwds)
        self.args = args
        self.kwds = kwds

        self.call_count = 0  # number of times func is run

        # true if parsing of MMI description text is needed by this test func
        self.desc_parsing_needed = False

        for arg in args:
            if isinstance(arg, str) and arg.startswith(MMI.arg_value_prefix):
                self.desc_parsing_needed = True
                break

    def __set_attrs(self, kwds):
        """Read attributes from arbitrary keyword argument dictionary.

        Attributes are not specified in the constructor as normal arguments
        cause they are not always used and when not used they would be
        consuming function (func) arguments (args).

        These attributes are used by this class and not passed to the func,
        hence they are removed from kwds.

        Note: with test functions stop_wid is only there to be compatible with
        TestCmd interface. But since functions cannot be stopped, stop_wid is
        useless.

        kwds -- arbitrary keyword argument dictionary

        """
        attr_names = ["start_wid", "stop_wid", "post_wid", "skip_call"]

        for attr_name in attr_names:
            if attr_name in kwds:
                attr_value = kwds.pop(attr_name)
            else:
                attr_value = None

            setattr(self, attr_name, attr_value)

    def start(self):
        """Starts the function"""
        self.call_count += 1
        log(f"Starting test function: {self}")

        if isinstance(self.skip_call, tuple):  # is None if not set
            if self.call_count in self.skip_call:
                log("Skipping starting test function")
                return

        if self.desc_parsing_needed:
            args = MMI.process_args(self.args)
        else:
            args = self.args

        log("Test function parameters: args=%r, kwds=%r", args, self.kwds)

        self.func(*args, **self.kwds)

    def stop(self):
        """Does nothing, since not easy job to stop a function"""

    def __str__(self):
        """Returns string representation"""
        return (
            f"class={self.__class__}, func={self.func} start_wid={self.start_wid} "
            f"stop_wid={self.stop_wid} post_wid={self.post_wid} skip_call={self.skip_call} "
            f"call_count={self.call_count} args={self.args} kwds={self.kwds}"
        )


class TestFuncCleanUp(TestFunc):
    """Clean-up function that is invoked after running test case in PTS."""


def is_cleanup_func(func):
    """Retruns True if func is an in an instance of TestFuncCleanUp"""
    return isinstance(func, TestFuncCleanUp)


class AbstractMethodException(Exception):
    """Exception raised if an abstract method is called."""


class PTSCallback:
    """Base class for PTS callback implementors"""

    def __init__(self):
        pass

    def log(self, log_type, logtype_string, log_time, log_message, test_case_name):
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
                         style):
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

    def copy(self):
        """Copy constructor"""
        return TestCase(self.project_name, self.name, self.cmds,
                        self.ptsproject_name, self.no_wid, self.edit1_wids,
                        self.verify_wids, self.ok_cancel_wids,
                        self.generic_wid_hdl, self.log_filename, self.log_dir)

    def __init__(self, project_name, test_case_name, cmds=None, ptsproject_name=None, no_wid=None, edit1_wids=None,
                 verify_wids=None, ok_cancel_wids=None, generic_wid_hdl=None, log_filename=None, log_dir=None):
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
                       description contains all of the strings in the tuple.
                       All the case-based characters are uppercased before
                       verification to avoid fake verification errors.
                       If the value is callable it will be passed PTS MMI
                       description as a parameter. It is expected to return
                       boolean True for the Yes and False for the No response
                       of MMI_Style_Yes_No1.

        ok_cancel_wids -- A dictionary of wids as keys and bool or callable as
                          values. The bool value or the bool returned from the
                          callable value is converted to OK, Cancel and send to
                          PTS in response to MMI_Style_Ok_Cancel1 and
                          MMI_Style_Ok_Cancel2 style prompts with matching wid.

        generic_wid_hdl -- A instance of general wid handler used for every wid
                           that came to test case.

        """
        super().__init__()
        if cmds is None:
            cmds = []
        self.project_name = project_name
        self.name = test_case_name
        # a.k.a. final verdict
        self.status = "init"
        # For instances synchronization
        self.state = None

        if isinstance(cmds, list):
            self.cmds = list(cmds)
        else:
            self.cmds = [cmds]

        # catch test case implementation syntax errors
        if no_wid:
            assert isinstance(no_wid, int), f"no_wid should be int, and not {no_wid!r}"
        if edit1_wids:
            assert isinstance(edit1_wids, dict), f"edit1_wids should be dict, and not {edit1_wids!r}"
        if verify_wids:
            assert isinstance(verify_wids, dict), f"verify_wids should be dict, and not {verify_wids!r}"
        if ok_cancel_wids:
            assert isinstance(ok_cancel_wids, dict), f"ok_cancel_wids should be dict, and not {ok_cancel_wids!r}"

        self.no_wid = no_wid
        self.edit1_wids = edit1_wids
        self.verify_wids = verify_wids
        self.ok_cancel_wids = ok_cancel_wids
        self.generic_wid_hdl = generic_wid_hdl
        self.steps_queue = None
        self.post_wid_queue = None
        self.ptsproject_name = ptsproject_name
        self.tc_subproc = None
        self.lf_subproc = None
        self.log_filename = log_filename
        self.log_dir = log_dir

        # pre_tc.py and post_tc.py are for starting/ending external tools like
        # btmon. For test cases with multiple LTs it is enough to start
        # the subprocess just for the first LT instance, the TestCaseLT1.
        self.run_pre_and_post_sp = True

    def reset(self):
        # Fields that have to be reinit before retrying a test case
        self.status = "init"
        self.state = None
        self.steps_queue = queue.Queue()
        self.post_wid_queue = []

    def __str__(self):
        """Returns string representation"""
        return f"{self.project_name} {self.name}"

    def initialize_logging(self, session_logging_dir):
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        normalized_name = self.name.replace('/', '_')
        timestamp_name = f"{normalized_name}_{now}"
        test_log_dir = os.path.join(session_logging_dir, timestamp_name)
        try:
            os.makedirs(test_log_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        log("Created logs directory %r", test_log_dir)

        self.log_dir = test_log_dir
        self.log_filename = os.path.join(test_log_dir, timestamp_name + ".log")

    def handle_mmi_style_yes_no1(self, wid, description):
        """Implements implicit send handling for MMI_Style_Yes_No1"""
        log("%s, %r %r", self.handle_mmi_style_yes_no1.__name__,
            wid, description)

        log("no_wid=%r verify_wids=%r", self.no_wid, self.verify_wids)

        yes_response = "Yes"
        no_response = "No"
        my_response = ""
        bool2rsp = {True: yes_response, False: no_response}

        # answer No
        if self.no_wid and wid == self.no_wid:
            my_response = no_response

        # answer No if description does not contain text from verify_wids
        elif self.verify_wids and wid in self.verify_wids:
            log("Starting verification of: %r", self.verify_wids)

            data = self.verify_wids[wid]
            if callable(data):
                bool_rsp = data(description)
                my_response = bool2rsp[bool_rsp]
            elif isinstance(data, tuple) and callable(data[0]):
                bool_rsp = data[0](description, *data[1:])
                my_response = bool2rsp[bool_rsp]
            else:
                for verify in self.verify_wids[wid]:
                    log("Verifying: %r", verify)
                    if isinstance(verify, list):
                        for x in verify:
                            if x.upper() not in description.upper():
                                my_response = no_response
                                log("%r not found, skipping...", x)
                                break  # for x in verify:
                            my_response = yes_response

                        # If all elements in the list have been successfully
                        # verified, break here
                        if my_response is yes_response:
                            break  # for verify in self.verify_wids[wid]:
                    else:
                        if verify.upper() not in description.upper():
                            my_response = no_response
                            break
                        my_response = yes_response

            if my_response is yes_response:
                log("All verifications passed")
            else:
                log("Verification failed: not in description")

        # answer Yes
        else:
            my_response = yes_response

        # log warning if confimation/verification is unhandled
        if not self.verify_wids or wid not in self.verify_wids:
            search_strings = ["confirm", "verify"]

            if any(string in description.lower() for string in search_strings):
                logging.warning("Verification missing for: %r", description)

        return my_response

    def handle_mmi_style_edit1(self, wid, description):
        """Implements implicit send handling for MMI_Style_Edit1"""
        log("%s, %r edit1_wids=%r", self.handle_mmi_style_edit1.__name__, wid,
            self.edit1_wids)

        my_response = ""

        if self.edit1_wids and wid in list(self.edit1_wids.keys()):
            response = self.edit1_wids[wid]
            if callable(response):
                my_response = response(description)
            elif isinstance(response, tuple) and callable(response[0]):
                # Handle command before responding
                my_response = response[0](description, *response[1:])
            else:
                my_response = response

        return my_response

    def handle_mmi_style_ok_cancel(self, wid, description):
        """Implements implicit send handling for MMI_Style_Ok_Cancel1 and
        MMI_Style_Ok_Cancel2"""
        log("%s, %r ok_cancel_wids=%r",
            self.handle_mmi_style_ok_cancel.__name__, wid, self.ok_cancel_wids)

        if self.ok_cancel_wids and wid in list(self.ok_cancel_wids.keys()):
            response = self.ok_cancel_wids[wid]
            if callable(response):
                my_response = response(description)
            elif isinstance(response, tuple) and callable(response[0]):
                # Handle command before responding
                my_response = response[0](description, *response[1:])
            else:
                my_response = response

        else:  # by default respond OK
            my_response = True

        response = {True: "OK", False: "Cancel"}[my_response]

        return response

    def start_stop_cmds_by_wid(self, wid, description):
        """Starts/stops commands

        The commands started/stopped are the ones that have the same start_wid
        or stop_wid as the argument

        """
        for cmd in self.cmds:
            if cmd.post_wid == wid:
                self.post_wid_queue.append(cmd)

            # start command
            if cmd.start_wid == wid:
                if cmd.desc_parsing_needed:
                    MMI.parse_description(description)

                cmd.start()

                if cmd.desc_parsing_needed:  # clear parsed description
                    MMI.reset()

            # stop command
            if cmd.stop_wid == wid:
                cmd.stop()

    def run_post_wid_cmds(self):
        """Run post wid commands"""
        log("%s %s", self, self.run_post_wid_cmds.__name__)

        for index, cmd in enumerate(self.post_wid_queue):
            log("%d) %s", index, cmd)

        # Define a helper function to safely start a command.
        def safe_start(cmd):
            try:
                cmd.start()
                return True
            except Exception as e:
                logging.exception(e)
                return False

        # Use the helper function in the loop.
        for cmd in self.post_wid_queue:
            if not safe_start(cmd):
                break

        del self.post_wid_queue[:]

        # No PTS response.
        return None

    def handle_mmi_generic(self, wid, description, style, test_case_name):
        response = self.generic_wid_hdl(wid, description, test_case_name)

        if isinstance(response, ResponseWithPostWID):
            next_steps = response.next_steps
            response = response.response

            # next_steps should be a list of tuples,
            # e.g. [(func1, arg1, arg2, ...), ...]
            for step in next_steps:
                self.add_next_step(*step)

        if response in ["WAIT", "END_TEST_CASE"]:
            return response

        if style in (ptstypes.MMI_Style_Edit1, ptstypes.MMI_Style_Edit2):
            return str(response)

        if style in (ptstypes.MMI_Style_Ok_Cancel1, ptstypes.MMI_Style_Ok_Cancel2):
            return "OK" if response else "Cancel"

        if style == ptstypes.MMI_Style_Yes_No1:
            return "Yes" if response else "No"

        if style == ptstypes.MMI_Style_Yes_No_Cancel1:
            if response is None:
                return "Cancel"
            if response:
                return "Yes"
            return "No"

        if style == ptstypes.MMI_Style_Ok:
            return "Ok"

        if style == ptstypes.MMI_Style_Abort_Retry1:
            return "Retry" if response else "Abort"

        return "Cancel"

    def on_implicit_send(self, project_name, wid, test_case_name, description,
                         style):
        """Callback called by PTS via xmlrpc proxy"""

        self.add_next_step(self.run_wid, project_name, wid,
                           test_case_name, description, style)

    def add_next_step(self, func, *args):
        """Queue WID or post-WID, that has to be run after sending
         a WID response to PTS, or other special step.

        :param func: function to queue in the steps queue"""
        self.steps_queue.put((func, *args))

    def run_next_step(self):
        try:
            item = self.steps_queue.get(block=False)
        except queue.Empty:
            return None

        step, *args = item
        response = step(*args)

        return response

    def run_wid(self, project_name, wid, test_case_name, description, style):
        """Handles MMI requested with
         PTSControl.IPTSImplicitSendCallbackEx.OnImplicitSend"""
        log("%s %s", self, self.on_implicit_send.__name__)

        synch_elem = None
        stack = get_stack()

        # Wait for other LT-threads if synch points configured for the test case
        if stack.synch:
            synch_elem = stack.synch.wait_for_start(wid, test_case_name)

        # start/stop command if triggered by wid
        self.start_stop_cmds_by_wid(wid, description)

        if self.generic_wid_hdl is not None:
            my_response = self.handle_mmi_generic(wid, description, style,
                                                  test_case_name)
        else:
            if style == ptstypes.MMI_Style_Yes_No1:
                my_response = self.handle_mmi_style_yes_no1(wid, description)

            elif style == ptstypes.MMI_Style_Edit1:
                my_response = self.handle_mmi_style_edit1(wid, description)

            # actually style == MMI_Style_Ok_Cancel2
            else:
                my_response = self.handle_mmi_style_ok_cancel(wid, description)

        # If there are post wid TestFunc waiting, run those after this one
        if self.post_wid_queue:
            self.add_next_step(self.run_post_wid_cmds)
            log("Running post_wid test functions")

        # Let other LT-threads know that this one completed the wid
        if synch_elem:
            def wait_for_end(): return stack.synch.wait_for_end(synch_elem)
            self.add_next_step(wait_for_end)

        log("Sending response %r to wid %d test case %s", my_response, wid, test_case_name)
        return my_response

    def pre_run(self):
        """Method called before test case is run in PTS"""
        log(f"{self.pre_run.__name__} {self.project_name} {self.name}")

        log(f"About to run test case {self.project_name} {self.name} with commands:")
        for index, cmd in enumerate(self.cmds):
            log(f"{index}) {cmd}")

        subproc_dir = (os.path.dirname(os.path.abspath(__file__)) + "/" +
                       self.ptsproject_name + "/")
        subproc_path = subproc_dir + "pre_tc.py"

        if self.run_pre_and_post_sp and os.path.exists(subproc_path):
            log(f"{self.pre_run.__name__}, run pre test case script")
            self.lf_subproc = open(subproc_dir + "sp_pre_stdout.log", "w")

            if sys.platform == "win32":
                subproc_cmd = " ".join(["python", repr(subproc_path),
                                        self.project_name, self.name])
            else:
                subproc_cmd = " ".join(
                    [subproc_path, self.project_name, self.name])

            self.tc_subproc = subprocess.Popen(shlex.split(subproc_cmd),
                                               shell=False,
                                               stdin=subprocess.PIPE,
                                               stdout=self.lf_subproc,
                                               stderr=self.lf_subproc)

        # start commands that don't have start trigger (lack start_wid or
        # post_wid) and are not cleanup functions
        for cmd in self.cmds:
            if cmd.start_wid is None and cmd.post_wid is None and \
               not is_cleanup_func(cmd):
                cmd.start()

    def post_run(self, error_code):
        """Method called after test case is run in PTS

        error_code -- String code of an error that occured during test run
        """
        log(f"{self.post_run.__name__} {self.project_name} {self.name} {error_code}")

        if error_code in list(ptstypes.PTSCONTROL_E_STRING.values()):
            self.status = error_code

        elif error_code:
            raise Exception(f"Unknown error code {error_code!r}!")

        # run the clean-up commands
        for cmd in self.cmds:
            if is_cleanup_func(cmd):
                cmd.start()

        # in accordance with PTSControlClient.cpp:
        # // Allow device to settle down
        # Sleep(3000);
        # otherwise 4th test case just blocks eternally
        if not get_global_end():
            time.sleep(3)

        for cmd in self.cmds:
            cmd.stop()

        if not self.run_pre_and_post_sp:
            return

        # Cleanup pre created subproc
        if self.tc_subproc is not None:
            log(f"{self.post_run.__name__}, cleanup running post test case script")
            self.tc_subproc.communicate(input=b'#close\n')
            self.lf_subproc.close()
        subproc_dir = (os.path.dirname(os.path.abspath(__file__)) + "/" +
                       self.ptsproject_name + "/")
        subproc_path = subproc_dir + "post_tc.py"

        if os.path.exists(subproc_path):
            log(f"{self.post_run.__name__}, run post test case script")
            self.lf_subproc = open(subproc_dir + "sp_post_stdout.log", "w")

            if sys.platform == "win32":
                subproc_cmd = " ".join(["python", repr(subproc_path),
                                        self.project_name, self.name])
            else:
                subproc_cmd = " ".join(
                    [subproc_path, self.project_name, self.name])

            self.tc_subproc = subprocess.Popen(shlex.split(subproc_cmd),
                                               shell=False,
                                               stdin=subprocess.PIPE,
                                               stdout=self.lf_subproc,
                                               stderr=self.lf_subproc)

            self.tc_subproc.communicate(input=b'#close\n')
            self.lf_subproc.close()


class TestCaseLT1(TestCase):
    def copy(self):
        """Copy constructor"""

        test_case = super().copy()
        test_case.name_lt2 = self.name_lt2
        test_case.name_lt3 = self.name_lt3

        return test_case

    def __init__(self, *args, **kwargs):
        name_lt2 = kwargs.pop('lt2', None)
        name_lt3 = kwargs.pop('lt3', None)
        super().__init__(*args, **kwargs)
        self.name_lt2 = name_lt2
        self.name_lt3 = name_lt3
        self.run_pre_and_post_sp = True


class TestCaseLT2(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_pre_and_post_sp = False


class TestCaseLT3(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_pre_and_post_sp = False


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

    return max_project_name, max_test_case_name
