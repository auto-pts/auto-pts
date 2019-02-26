#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

"""Python bindings for PTSControl introp objects

Cause of tight coupling with PTS, this module is Windows specific
"""

import os
import sys
import time
import logging
import argparse
import shutil
import xmlrpclib

import clr
import System

import ctypes
libc = ctypes.cdll.msvcrt  # for wcscpy_s

# workaround to a bug in IronPython: cwd in missing from sys.path under pdb
# https://github.com/IronLanguages/main/issues/1225
if "pdb" in sys.modules:
    sys.path.insert(0, os.getcwd())

import ptsprojects.ptstypes as ptstypes

# load the PTS interop assembly
clr.AddReferenceToFile("Interop.PTSControl.dll")

import Interop.PTSControl as PTSControl

log = logging.debug

logtype_whitelist = [ptstypes.PTS_LOGTYPE_START_TEST,
                     ptstypes.PTS_LOGTYPE_END_TEST,
                     ptstypes.PTS_LOGTYPE_ERROR,
                     ptstypes.PTS_LOGTYPE_FINAL_VERDICT]


class PTSLogger(PTSControl.IPTSControlClientLogger):
    """PTS control client logger implementation"""

    def __init__(self):
        """"Constructor"""

        # an object that implements testcase.PTSCallback, it can either be
        # TestCase or xmlrpc SimpleXMLRPCServer running in auto pts client.
        self._callback = None
        self._maximum_logging = False
        self._test_case_name = None

    def set_callback(self, callback):
        """Set the callback"""
        self._callback = callback

    def unset_callback(self):
        """Unset the callback"""
        self._callback = None

    def enable_maximum_logging(self, enable):
        """Enable/disable maximum logging"""
        self._maximum_logging = enable

    def set_test_case_name(self, test_case_name):
        """Required to identify multiple instances on client side"""
        self._test_case_name = test_case_name

    def Log(self, log_type, logtype_string, log_time, log_message):
        """Implements:

        interface IPTSControlClientLogger : IUnknown {
            HRESULT _stdcall Log(
                            [in] _PTS_LOGTYPE logType,
                            [in] LPWSTR szLogType,
                            [in] LPWSTR szTime,
                            [in] LPWSTR pszMessage);
        };
        """

        logger = logging.getLogger(self.__class__.__name__)
        log = logger.info

        log("%s %s %s %s" % (log_type, logtype_string, log_time, log_message))

        try:
            # xmrpc proxy object in boolean test calls the method __nonzero__
            # of the xmlrpc server, so "is" test is a better choice here
            if self._callback is not None:
                log("Calling callback.log")
                # log_type of type PTSControl._PTS_LOGTYPE is marshalled as
                # int since xmlrpc has not marshalling rules for _PTS_LOGTYPE
                if self._maximum_logging or int(log_type) in logtype_whitelist:
                    self._callback.log(int(log_type), logtype_string, log_time,
                                       log_message, self._test_case_name)
        except Exception as e:
            log("Caught exception")
            log(e)
            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in Log")


class PTSSender(PTSControl.IPTSImplicitSendCallbackEx):
    """Implicit send callback implementation"""

    def __init__(self):
        """"Constructor"""

        # an object that implements testcase.PTSCallback, it can either be
        # TestCase or xmlrpc SimpleXMLRPCServer running in auto pts client.
        self._callback = None

    def set_callback(self, callback):
        """Sets the callback"""
        self._callback = callback

    def unset_callback(self):
        """Unsets the callback"""
        self._callback = None

    def OnImplicitSend(self, project_name, wid, test_case_name, description,
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
        """
        logger = logging.getLogger(self.__class__.__name__)
        log = logger.info
        timer = 0

        log("*" * 20)
        log("BEGIN OnImplicitSend:")
        log("project_name: %s %s" % (project_name, type(project_name)))
        log("wid: %d %s" % (wid, type(wid)))
        log("test_case_name: %s %s" % (test_case_name, type(test_case_name)))
        log("description: %s %s" % (description, type(description)))
        log("style: %s 0x%x", ptstypes.MMI_STYLE_STRING[style], style)
        log("response:  %s %s %s" %
            (repr(response), type(response), id(response)))
        log("response_size: %d %s" % (response_size, type(response_size)))
        log("response_is_present:  %s %s" %
            (response_is_present, type(response_is_present)))

        try:
            # xmrpc proxy object in boolean test calls the method __nonzero__
            # of the xmlrpc server, so "is" test is a better choice here
            if self._callback is not None:
                log("Calling callback.on_implicit_send")
                callback_response = self._callback.on_implicit_send(
                    project_name,
                    int(wid),  # UInt16 cannot be marshalled
                    test_case_name,
                    description,
                    int(style),
                    response,
                    int(response_size),
                    int(response_is_present))

                # Don't block xml-rpc
                if callback_response == "WAIT":
                    callback_response = self._callback.get_pending_response(
                        test_case_name)
                    while not callback_response:
                        # XXX: Ask for response every second
                        timer = timer + 1
                        # XXX: Timeout 90 seconds
                        if timer > 90:
                            callback_response = "Cancel"
                            break

                        log("Rechecking response...")
                        time.sleep(1)
                        callback_response \
                            = self._callback.get_pending_response(
                                test_case_name)
                        pass

                log("callback returned on_implicit_send, respose: %s",
                    callback_response)

                if callback_response:
                    libc.wcscpy_s(response, response_size,
                                  unicode(callback_response))
                    response_is_present.Value = 1

        except xmlrpclib.Fault as err:
            log("A fault occurred, code = %d, string = %s" %
                (err.faultCode, err.faultString))

        except Exception as e:
            log("Caught exception")
            log(e)
            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in OnImplicitSend")

        # not easy to to redirect libc stdout to the log file, can print it by:
        # libc._putws(response)
        # libc.fflush(None);
        log("final response: %s %s %s" % (response, type(response),
                                          id(response)))
        log("final response_is_present: %s %s" %
            (response_is_present, type(response_is_present)))

        log("END OnImplicitSend:")
        log("*" * 20)


class PyPTS:
    """PTS control interface.

    Provides wrappers around Interop.PTSControl.PTSControlClass methods and
    some additional features.

    For detailed documentation see 'Extended Automatiing - Using PTSControl'
    document provided with PTS in file Extended_Automating.pdf

    """

    def __init__(self):
        """Constructor"""
        log("%s", self.__init__.__name__)

        self._init_attributes()

        # list of tuples of methods and arguments to recover after PTS restart
        self._recov = []
        self._recov_in_progress = False

        self._temp_workspace_path = None

        # This is done to have valid _pts in case client does not restart_pts
        # and uses other methods. Normally though, the client should
        # restart_pts, see its docstring for the details
        #
        # Another reason: PTS starting from version 6.2 returns
        # PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_ALREADY_REGISTERED 0x849C004 in
        # RegisterImplicitSendCallbackEx if PTS from previous autoptsserver is
        # used
        self.restart_pts()

    def _init_attributes(self):
        """Initializes class attributes"""
        log("%s", self._init_attributes.__name__)

        self._pts = None
        self._pts_pid = None

        self._pts_logger = None
        self._pts_sender = None

        # Cached frequently used PTS attributes: for optimisation reasons it is
        # avoided to contact PTS. These attributes should not change anyway.
        self.__bd_addr = None

    def add_recov(self, func, *args, **kwds):
        """Add function to recovery list"""
        if not self._recov_in_progress:
            log("%s %r %r %r", self.add_recov.__name__, func, args, kwds)
            self._recov.append((func, args, kwds))

    def del_recov(self, func, *args, **kwds):
        """Remove function from recovery list"""
        log("%s %r %r %r", self.del_recov.__name__, func, args, kwds)

        recov_funcs = [item[0] for item in self._recov]

        if func not in recov_funcs:
            return

        # no arguments specified: remove all method calls
        if not args and not kwds:
            self._recov = [item for item in self._recov if item[0] != func]

        # remove single method call with matching arguments
        else:
            item = (func, args, kwds)
            if item in self._recov:
                self._recov.remove(item)

    def recover_pts(self):
        """Recovers PTS from errors occured during RunTestCase call.

        The errors include timeout set by SetPTSCallTimeout. The only way to
        correctly recover is to restart PTS and restore its settings.

        Timeouts break some PTS functionality, hence it is good idea to start a
        new instance of PTS every time. For details see:

        https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13794

        PTS timeouts also break run_test_case in a way that the status of
        completed test cases is incorrect.

        """

        log("%s", self.recover_pts.__name__)
        log("recov=%s", self._recov)

        self._recov_in_progress = True

        self.restart_pts()

        for item in self._recov:
            func = item[0]
            args = item[1]
            kwds = item[2]
            log("Recovering: %s, %r %r", func, args, kwds)
            func(*args, **kwds)

        self._recov_in_progress = False

    def restart_pts(self):
        """Restarts PTS

        Timeouts break some PTS functionality, hence it is good idea to start a
        new instance of PTS every time. For details see:

        https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13794

        This function will block for couple of seconds while PTS starts

        """

        log("%s", self.restart_pts.__name__)

        # Startup of ptscontrol doesn't have PTS pid yet set - no pts running
        if self._pts_pid:
            self.stop_pts()
        time.sleep(3)  # otherwise there are COM errors occasionally
        self.start_pts()

    def start_pts(self):
        """Starts PTS

        This function will block for couple of seconds while PTS starts"""

        log("%s", self.start_pts.__name__)

        # Get PTS process list before running new PTS daemon
        pts_ps_list = System.Diagnostics.Process.GetProcessesByName("PTS")
        pts_pid_list_pre = [ps.Id for ps in pts_ps_list]
        self._pts = PTSControl.PTSControlClass()
        # Get PTS process list after running new PTS daemon to get PID of
        # new instance
        pts_ps_list = System.Diagnostics.Process.GetProcessesByName("PTS")
        pts_pid_list_post = [ps.Id for ps in pts_ps_list]

        pid = list(set(pts_pid_list_post) - set(pts_pid_list_pre))
        if len(pid) != 1:
            log("Error during pts startup!")
            return

        self._pts_pid = pid[0]
        log("Started new PTS daemon with pid: %d" % self._pts_pid)

        self._pts_logger = PTSLogger()
        self._pts_sender = PTSSender()

        # cached frequently used PTS attributes: due to optimisation reasons it
        # is avoided to contact PTS. These attributes should not change anyway.
        self.__bd_addr = None

        # mandatory to set at least to None if logger is not used
        self.set_control_client_logger_callback(self._pts_logger)

        self.register_implicit_send_callback_ex(self._pts_sender)

        log("PTS Version: %x", self.get_version())
        log("PTS Bluetooth Address: %x", self.get_bluetooth_address())
        log("PTS BD_ADDR: %s" % self.bd_addr())

    def stop_pts(self):
        """Stops PTS"""

        try:
            pts_process = \
                System.Diagnostics.Process.GetProcessById(self._pts_pid)
            log("About to stop PTS with pid: %d, process: %s", self._pts_pid,
                pts_process)

            pts_process.CloseMainWindow()
            # Give PTS process time to close otherwise do it brutally to not
            # block testing. This happens occasionally when tester tries to
            # close PTS while after test logs are processing.
            res = pts_process.WaitForExit(5000)
            if not res:
                pts_process.Kill()
                log("Process didn't close within limited time - killed")
            pts_process.Close()
        except Exception as error:
            logging.exception(error.message)

        self._init_attributes()

    def create_workspace(self, bd_addr, pts_file_path, workspace_name,
                         workspace_path):
        """Creates a new workspace"""

        log("%s %s %s %s %s", self.create_workspace.__name__, bd_addr,
            pts_file_path, workspace_name, workspace_path)

        self._pts.CreateWorkspace(bd_addr, pts_file_path, workspace_name,
                                  workspace_path)

    @staticmethod
    def _get_own_workspaces():
        """Get auto-pts own workspaces"""
        script_path = os.path.split(os.path.realpath(__file__))[0]
        required_ext = ".pqw6"  # valid PTS workspace file extension
        workspaces = {}

        for root, dirs, files in os.walk("workspaces"):
            for file in files:
                if file.endswith(required_ext):
                    name = os.path.splitext(file)[0]
                    path = os.path.join(script_path, root, file)
                    workspaces[name] = path

        return workspaces

    def open_workspace(self, workspace_path):
        """Opens existing workspace"""

        log("%s %s", self.open_workspace.__name__, workspace_path)

        required_ext = ".pqw6"  # valid PTS workspace file extension

        # auto-pts own workspaces
        autopts_workspaces = self._get_own_workspaces()

        if workspace_path in autopts_workspaces.keys():
            workspace_name = workspace_path
            workspace_path = autopts_workspaces[workspace_path]
            log("Using %s workspace: %s", workspace_name, workspace_path)

        if not os.path.isfile(workspace_path):
            raise Exception("Workspace file '%s' does not exist" %
                            (workspace_path,))

        specified_ext = os.path.splitext(workspace_path)[1]
        if required_ext != specified_ext:
            raise Exception(
                "Workspace file '%s' extension is wrong, should be %s" %
                (workspace_path, required_ext))

        # Workaround CASE0044114 PTS issue
        # Do not open original workspace file that can become broken by
        # TestCase. Instead use a copy of this file
        if self._temp_workspace_path and \
                os.path.exists(self._temp_workspace_path):
            os.unlink(self._temp_workspace_path)

        workspace_dir = os.path.dirname(workspace_path)
        workspace_name = os.path.basename(workspace_path)

        self._temp_workspace_path = \
            os.path.join(workspace_dir, "temp_" + workspace_name)
        shutil.copy2(workspace_path, self._temp_workspace_path)
        log("Using temporary workspace: %s", self._temp_workspace_path)

        self._pts.OpenWorkspace(self._temp_workspace_path)
        self.add_recov(self.open_workspace, workspace_path)

    def get_project_count(self):
        """Returns number of projects available in the current workspace"""

        project_count = clr.StrongBox[System.UInt32]()
        self._pts.GetProjectCount(project_count)
        project_count_int = int(project_count)

        log("%s out: %s", self.get_project_count.__name__, project_count_int)

        return project_count_int

    def get_project_name(self, project_index):
        """Returns project name"""

        project_name = ""
        project_name = self._pts.GetProjectName(project_index, project_name)

        log("%s %s out: %s", self.get_project_name.__name__, project_index,
            project_name)

        return project_name

    def get_project_version(self, project_name):
        """Returns project version"""

        project_version = clr.StrongBox[System.UInt32]()
        self._pts.GetProjectVersion(project_name)
        project_version_int = int(project_version)

        log("%s %s out: %s", self.get_project_version.__name__, project_name,
            project_version_int)

        return project_version_int

    def get_test_case_count(self, project_name):
        """Returns the number of test cases that are available in the specified
        project."""

        test_case_count = clr.StrongBox[System.UInt32]()
        self._pts.GetTestCaseCount(project_name, test_case_count)
        test_case_count_int = int(test_case_count)

        log("%s %s out: %s", self.get_test_case_count.__name__, project_name,
            test_case_count_int)

        return test_case_count_int

    def get_test_case_name(self, project_name, test_case_index):
        """Returns name of the specified test case"""

        test_case_name = ""
        test_case_name = self._pts.GetTestCaseName(project_name,
                                                   test_case_index,
                                                   test_case_name)

        log("%s %s %s out: %s", self.get_test_case_name.__name__, project_name,
            test_case_index, test_case_name)

        return test_case_name

    def get_test_case_description(self, project_name, test_case_index):
        """Returns description of the specified test case"""

        test_case_description = ""
        test_case_description = self._pts.GetTestCaseDescription(
            project_name, test_case_index, test_case_description)

        log("%s %s %s out: %s", self.get_test_case_description.__name__,
            project_name, test_case_index,
            test_case_description.encode("ascii", "ignore"))

        return test_case_description

    def is_active_test_case(self, project_name, test_case_name):
        """Returns True if the specified test case is active (enabled) in the
        specified project. Returns False is if the test case is not active
        (disabled).
        """

        is_active = clr.StrongBox[System.Int32]()
        self._pts.IsActiveTestCase(project_name, test_case_name, is_active)
        is_active_bool = bool(int(is_active))

        log("%s %s %s out: %s", self.is_active_test_case.__name__,
            project_name, test_case_name, is_active_bool)

        return is_active_bool

    def run_test_case(self, project_name, test_case_name):
        """Executes the specified Test Case.

        If an error occurs when running test case returns code of an error as a
        string, otherwise returns an empty string

        [1] 32 bit IronPython converts error codes to long integer, which is
            not supported by xmlrpc:

            Fault: <Fault 1: "<type 'exceptions.OverflowError'>:long int
            exceeds XML-RPC limits">

            Hence, error codes are passed over xmlrpc as strings

        """

        log("Starting %s %s %s", self.run_test_case.__name__, project_name,
            test_case_name)

        self._pts_logger.set_test_case_name(test_case_name)

        error_code = ""

        try:
            self._pts.RunTestCase(project_name, test_case_name)

        except System.Runtime.InteropServices.COMException as exc:
            log("Exception in %s", self.run_test_case.__name__)
            log(exc)

            hresult = int(System.UInt32(exc.HResult))
            error_code = ptstypes.PTSCONTROL_E_STRING[hresult]  # see [1]

            self.recover_pts()

        log("Done %s %s %s out: %s", self.run_test_case.__name__,
            project_name, test_case_name, error_code)

        return error_code

    def stop_test_case(self, project_name, test_case_name):
        """NOTE: According to documentation 'StopTestCase() is not currently
        implemented'"""

        log("%s %s %s", self.is_active_test_case.__name__, project_name,
            test_case_name)

        self._pts.StopTestCase(project_name, test_case_name)

    def get_test_case_count_from_tss_file(self, project_name):
        """Returns the number of test cases that are available in the specified
        project according to TSS file."""

        test_case_count = clr.StrongBox[System.UInt32]()
        self._pts.GetTestCaseCountFromTSSFile(project_name, test_case_count)
        test_case_count_int = int(test_case_count)

        log("%s %s out: %s", self.get_test_case_count_from_tss_file.__name__,
            project_name, test_case_count_int)

        return test_case_count_int

    def get_test_cases_from_tss_file(self, project_name):
        """Returns array of test case names according to TSS file."""

        test_cases_unused = []
        test_cases = self._pts.GetTestCasesFromTSSFile(project_name,
                                                       test_cases_unused)

        log("%s %s out: %s", self.get_test_cases_from_tss_file.__name__,
            project_name, repr(test_cases))

        return test_cases

    def update_pics(self, project_name, entry_name, bool_value):
        """Updates PICS

        This wrapper handles exceptions that PTS throws if PICS entry is
        already set to the same value.

        PTS throws exception if the value passed to UpdatePics is the same as
        the value when PTS was started.

        In C++ HRESULT error with this value is returned:
        PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED (0x849C0032)

        """
        log("%s %s %s %s", self.update_pics.__name__, project_name,
            entry_name, bool_value)

        try:
            self._pts.UpdatePics(project_name, entry_name, bool_value)
            self.add_recov(self.update_pics, project_name, entry_name,
                           bool_value)

        except System.Runtime.InteropServices.COMException as e:
            log('Exception in UpdatePics "%s", is pics value already set?' %
                (e.Message,))

    def update_pixit_param(self, project_name, param_name, new_param_value):
        """Updates PIXIT

        This wrapper handles exceptions that PTS throws if PIXIT param is
        already set to the same value.

        PTS throws exception if the value passed to UpdatePixitParam is the
        same as the value when PTS was started.

        In C++ HRESULT error with this value is returned:
        PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED (0x849C0021)

        """
        log("%s %s %s %s", self.update_pixit_param.__name__, project_name,
            param_name, new_param_value)

        try:
            self._pts.UpdatePixitParam(
                project_name, param_name, new_param_value)
            self.add_recov(self.update_pixit_param, project_name, param_name,
                           new_param_value)

        except System.Runtime.InteropServices.COMException as e:
            log(('Exception in UpdatePixitParam "%s", is pixit param already '
                 'set?') % (e.Message,))

    def enable_maximum_logging(self, enable):
        """Enables/disables the maximum logging."""

        log("%s %s", self.enable_maximum_logging.__name__, enable)
        self._pts.EnableMaximumLogging(enable)
        self._pts_logger.enable_maximum_logging(enable)

    def set_call_timeout(self, timeout):
        """Sets a timeout period in milliseconds for the RunTestCase() calls
        to PTS."""

        log("%s %s", self.set_call_timeout.__name__, timeout)
        self._pts.SetPTSCallTimeout(timeout)

        if timeout:
            self.add_recov(self.set_call_timeout, timeout)
        else:  # timeout 0 = no timeout
            self.del_recov(self.set_call_timeout)

    def save_test_history_log(self, save):
        """This function enables automation clients to specify whether test
        logs have to be saved in the corresponding workspace folder.

        save -- Boolean

        """

        log("%s %s", self.save_test_history_log.__name__, save)
        self._pts.SaveTestHistoryLog(save)

    def get_bluetooth_address(self):
        """Returns PTS bluetooth address as a 64 bit integer"""

        pts_bt_address = clr.StrongBox[System.UInt64]()
        self._pts.GetPTSBluetoothAddress(pts_bt_address)
        pts_bt_address_int = int(pts_bt_address)

        log("%s out: %x", self.get_bluetooth_address.__name__,
            pts_bt_address_int)

        return pts_bt_address_int

    def bd_addr(self):
        '''Returns PTS BD_ADDR as a string'''
        # use cached address if available
        if self.__bd_addr:
            log("%s out cached: %s", self.bd_addr.__name__, self.__bd_addr)
            return self.__bd_addr

        bt_address_int = self.get_bluetooth_address()
        bt_address_upper = ("%x" % bt_address_int).upper()

        bd_addr = "00"
        for i in range(0, len(bt_address_upper), 2):
            bd_addr += ":" + bt_address_upper[i:i + 2]

        self.__bd_addr = bd_addr

        log("%s out: %s", self.bd_addr.__name__, self.__bd_addr)

        return bd_addr

    def get_version(self):
        """Returns PTS version"""

        pts_version = clr.StrongBox[System.UInt32]()
        self._pts.GetPTSVersion(pts_version)
        pts_version_int = int(pts_version)

        log("%s out: %x", self.get_version.__name__, pts_version_int)

        return pts_version_int

    def set_control_client_logger_callback(self, logger):
        """Sets PTSControl logger

        Note: if this function is not called upon initialization of PTSControl
        COM object, the COM object won't work. Calling with logger set to
        None also get the COM object working.

        logger -- a COM object derived from IPTSControlClientLogger, set it to
                  None to disable logging

        """

        log("%s %s", self.set_control_client_logger_callback.__name__, logger)

        self._pts.SetControlClientLoggerCallback(logger)

    def register_implicit_send_callback_ex(self, callback):
        """Connects the implicit send handler to the PTS.

        callback -- a COM object derived from IPTSImplicitSendCallbackEx

        """

        log("%s %s", self.register_implicit_send_callback_ex.__name__,
            callback)

        self._pts.RegisterImplicitSendCallbackEx(callback)

    def unregister_implicit_send_callback_ex(self, callback):
        """Disconnects the implicit send handler from the PTS."""

        log("%s %s", self.unregister_implicit_send_callback_ex.__name__,
            callback)

        self._pts.UnregisterImplicitSendCallbackEx(callback)

    def register_ptscallback(self, callback):
        """Registers testcase.PTSCallback instance to be used as PTS log and
        implicit send callback"""

        log("%s %s", self.register_ptscallback.__name__, callback)

        self._pts_logger.set_callback(callback)
        self._pts_sender.set_callback(callback)

        self.add_recov(self.register_ptscallback, callback)

    def unregister_ptscallback(self):
        """Unregisters the testcase.PTSCallback callback"""

        log("%s", self.unregister_ptscallback.__name__)

        self._pts_logger.unset_callback()
        self._pts_sender.unset_callback()

        self.del_recov(self.register_ptscallback)


def parse_args():
    """Parses command line arguments and options"""
    required_ext = ".pqw6"  # valid PTS workspace file extension

    arg_parser = argparse.ArgumentParser(
        description="PTS Control")

    arg_parser.add_argument(
        "workspace",
        help="Path to PTS workspace to use for testing. It should have %s "
        "extension" % (required_ext,))

    args = arg_parser.parse_args()

    return args


def main():
    """Rudimentary testing."""

    args = parse_args()

    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    logging.basicConfig(format='%(name)s [%(asctime)s] %(message)s',
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)

    pts = PyPTS()

    pts.open_workspace(args.workspace)

    # pts.run_test_case("RFCOMM", "TC_RFC_BV_19_C")

    project_count = pts.get_project_count()
    print "Project count:", project_count

    # print all projects and their test cases
    for project_index in range(project_count):
        project_name = pts.get_project_name(project_index)
        print "\nProject name:", project_name
        print "Project version:", pts.get_project_version(project_name)
        test_case_count = pts.get_test_case_count(project_name)
        print "Test case count:", test_case_count

        for test_case_index in range(test_case_count):
            test_case_name = pts.get_test_case_name(
                project_name, test_case_index)
            print "\nTest case project:", project_name
            print "Test case name:", test_case_name
            print "Test case description:", pts.get_test_case_description(
                project_name, test_case_index)
            print "Is active test case:", pts.is_active_test_case(
                project_name, test_case_name)

    print "\n\n\n\nTSS file info:"

    # print all projects and their test cases
    for project_index in range(project_count):
        project_name = pts.get_project_name(project_index)
        print "\nProject name:", project_name
        print "Project version:", pts.get_project_version(project_name)
        test_case_count = pts.get_test_case_count_from_tss_file(project_name)
        print "Test case count:", test_case_count

        test_cases = pts.get_test_cases_from_tss_file(project_name)
        print test_cases

        for test_case in test_cases:
            print test_case

    pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "FALSE")
    pts.update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "TRUE")

    pts.update_pics("L2CAP", "TSPC_L2CAP_3_13", True)
    pts.update_pics("L2CAP", "TSPC_L2CAP_3_13", False)

    pts.enable_maximum_logging(True)
    pts.enable_maximum_logging(False)

    pts.set_call_timeout(600000)
    pts.set_call_timeout(0)

    pts.save_test_history_log(True)
    pts.save_test_history_log(False)

    print
    print "PTS Bluetooth Address: %x" % pts.get_bluetooth_address()
    print "PTS BD_ADDR:", pts.bd_addr()
    print "PTS BD_ADDR:", pts.bd_addr()
    print "PTS Version: %x" % pts.get_version()


if __name__ == "__main__":
    main()
