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
import xmlrpc.client
import ctypes
import threading
from pathlib import Path

import win32com.client
import win32com.server.connect
import win32com.server.util
import pythoncom
import wmi

from autopts.ptsprojects import ptstypes
from autopts.utils import PTS_WORKSPACE_FILE_EXT, get_own_workspaces

log = logging.debug

logtype_whitelist = [ptstypes.PTS_LOGTYPE_START_TEST,
                     ptstypes.PTS_LOGTYPE_END_TEST,
                     ptstypes.PTS_LOGTYPE_ERROR,
                     ptstypes.PTS_LOGTYPE_FINAL_VERDICT]

PTS_START_LOCK = threading.RLock()


def pts_lock_wrapper(lock):
    def _pts_lock_wrapper(func):
        def __pts_lock_wrapper(*args):
            try:
                lock.acquire()
                ret = func(*args)
            finally:
                lock.release()
            return ret

        return __pts_lock_wrapper

    return _pts_lock_wrapper


STOP_PTS = False


class StopPTS(Exception):
    pass


def set_stop_pts(stop=True):
    global STOP_PTS
    STOP_PTS = stop


def force_pts_stop_wrapper(func):
    def _force_pts_stop_wrapper(*args):
        if STOP_PTS:
            raise StopPTS
        return func(*args)
    return _force_pts_stop_wrapper


class PTSLogger(win32com.server.connect.ConnectableServer):
    """PTS control client logger callback implementation"""
    _reg_desc_ = "AutoPTS Logger"
    _reg_clsid_ = "{50B17199-917A-427F-8567-4842CAD241A1}"
    _reg_progid_ = "autopts.PTSLogger"
    _public_methods_ = ['Log'] + win32com.server.connect.ConnectableServer._public_methods_

    def __init__(self):
        """"Constructor"""
        super().__init__()

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

        void Log(
                        [in] unsigned int logType,
                        [in] BSTR szLogType,
                        [in] BSTR szTime,
                        [in] BSTR pszMessage);
        };
        """

        logger = logging.getLogger(self.__class__.__name__)

        logger.info("%d %s %s %s", log_type, logtype_string, log_time, log_message)

        try:
            if self._callback is not None:
                if self._maximum_logging or log_type in logtype_whitelist:
                    self._callback.log(log_type, logtype_string, log_time,
                                       log_message, self._test_case_name)
        except Exception as e:
            logging.exception(repr(e))
            sys.exit("Exception in Log")


class PTSSender(win32com.server.connect.ConnectableServer):
    """PTS control client implicit send callback implementation"""
    _reg_desc_ = "AutoPTS Sender"
    _reg_clsid_ = "{9F4517C9-559D-4655-9032-076A1E9B7654}"
    _reg_progid_ = "autopts.PTSSender"
    _public_methods_ = ['OnImplicitSend'] + win32com.server.connect.ConnectableServer._public_methods_

    def __init__(self):
        """"Constructor"""
        super().__init__()

        self._callback = None

    def set_callback(self, callback):
        """Sets the callback"""
        self._callback = callback

    def unset_callback(self):
        """Unsets the callback"""
        self._callback = None

    @force_pts_stop_wrapper
    def OnImplicitSend(self, project_name, wid, test_case, description, style):
        """Implements:

        VARIANT OnImplicitSend(
                        [in] BSTR pszProjectName,
                        [in] unsigned short wID,
                        [in] BSTR szTestCase,
                        [in] BSTR szDescription,
                        [in] unsigned long style);
        };
        """
        logger = logging.getLogger(self.__class__.__name__)
        timer = 0

        # Remove whitespaces from project and test case name
        project_name = project_name.replace(" ", "")
        test_case = test_case.replace(" ", "")

        logger.info("*" * 20)
        logger.info("BEGIN OnImplicitSend:")
        logger.info("project_name: %s %s", project_name, type(project_name))
        logger.info("wid: %d %s", wid, type(wid))
        logger.info("test_case_name: %s %s", test_case, type(test_case))
        logger.info("description: %s %s", description, type(description))
        logger.info("style: %s 0x%x", ptstypes.MMI_STYLE_STRING[style], style)

        rsp = ""

        try:
            if self._callback is not None:
                logger.info("Calling callback.on_implicit_send")
                rsp = self._callback.on_implicit_send(project_name, wid,
                                                      test_case, description,
                                                      style)

                # Don't block xml-rpc
                if rsp == "WAIT":
                    rsp = self._callback.get_pending_response(
                        test_case)
                    while not rsp:
                        # XXX: Ask for response every second
                        timer = timer + 1
                        # XXX: Timeout 90 seconds
                        if timer > 90:
                            rsp = "Cancel"
                            break

                        logger.info("Rechecking response...")
                        time.sleep(1)
                        rsp = self._callback.get_pending_response(test_case)

                logger.info("callback returned on_implicit_send, respose: %r", rsp)

        except xmlrpc.client.Fault as err:
            logger.info("A fault occurred, code = %d, string = %s",
                        err.faultCode, err.faultString)

        except Exception as e:
            logger.info("Caught exception")
            logger.info(e)
            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in OnImplicitSend")

        if rsp:
            is_present = 1
        else:
            is_present = 0

        # Stringify response
        rsp = str(rsp)
        rsp_len = str(len(rsp))
        is_present = str(is_present)

        log("END OnImplicitSend:")
        log("*" * 20)

        return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR,
                                       [rsp, rsp_len, is_present])


def parse_ptscontrol_error(err):
    try:
        _, source, description, _, _, hresult = err.excepinfo

        ptscontrol_e = ctypes.c_uint32(hresult).value
        ptscontrol_e_string = ptstypes.PTSCONTROL_E_STRING[ptscontrol_e]

        logging.exception(ptscontrol_e_string)

        return ptscontrol_e_string

    except Exception:
        raise Exception() from err


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
        self._temp_changes = []
        self._recov_in_progress = False

        self._temp_workspace_path = None
        self.last_start_time = time.time()

        self._pts = None
        self._pts_proc = None
        self._pts_logger = None
        self._pts_sender = None
        self.__bd_addr = None
        self._com_logger = None
        self._com_sender = None
        self._device = None

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
        self._pts_proc = None

        self._pts_logger = None
        self._pts_sender = None
        self._com_logger = None
        self._com_sender = None

        # Cached frequently used PTS attributes: for optimisation reasons it is
        # avoided to contact PTS. These attributes should not change anyway.
        self.__bd_addr = None

        self._pts_projects = {}

    def add_recov(self, func, *args, **kwds):
        """Add function to recovery list"""
        if self._recov_in_progress:
            return

        log("%s %r %r %r", self.add_recov.__name__, func, args, kwds)

        # Re-set recovery element to avoid duplications
        if func == self.set_pixit:  # pylint: disable=W0143
            profile = args[0]
            pixit = args[1]
            # Look for possible re-setable PIXIT
            try:
                # Search for matching recover function, PIXIT and recover if value was changed.
                item = next(x for x in self._recov if ((x[0] ==
                                                        self.set_pixit) and (x[1][0] == profile) and
                                                       (x[1][1] == pixit)))

                self._recov.remove(item)
                log("%s, re-set pixit: %s", self.add_recov.__name__, pixit)

            except StopIteration:
                pass

        self._recov.append((func, args, kwds))

    def _add_temp_change(self, func, *args, **kwds):
        """Add function to set temporary value"""
        if not self._recov_in_progress:
            log("%s %r %r %r", self._add_temp_change.__name__, func, args, kwds)
            self._temp_changes.append((func, args, kwds))

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

    def _recover_item(self, item):
        """Recovery item wraper"""

        func = item[0]
        args = item[1]
        kwds = item[2]
        log("%s, Recovering: %s, %r %r", self._recover_item.__name__,
            func, args, kwds)

        func(*args, **kwds)

    @pts_lock_wrapper(PTS_START_LOCK)
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
            self._recover_item(item)

        self._recov_in_progress = False

    @pts_lock_wrapper(PTS_START_LOCK)
    def restart_pts(self):
        """Restarts PTS

        This function will block for couple of seconds while PTS starts

        """

        log("%s", self.restart_pts.__name__)

        # Startup of ptscontrol doesn't have PTS pid yet set - no pts running
        if self._pts_proc:
            self.stop_pts()
        time.sleep(1)  # otherwise there are COM errors occasionally
        self.start_pts()

    @pts_lock_wrapper(PTS_START_LOCK)
    def start_pts(self):
        """Starts PTS

        This function will block for couple of seconds while PTS starts"""

        log("%s", self.start_pts.__name__)

        # Get PTS process list before running new PTS daemon
        c = wmi.WMI()
        pts_ps_list_pre = []
        pts_ps_list_post = []

        for ps in c.Win32_Process(name="PTS.exe"):
            pts_ps_list_pre.append(ps)

        self._pts = win32com.client.Dispatch('ProfileTuningSuite_6.PTSControlServer')

        # Get PTS process list after running new PTS daemon to get PID of
        # new instance
        for ps in c.Win32_Process(name="PTS.exe"):
            pts_ps_list_post.append(ps)

        pts_ps_list = list(set(pts_ps_list_post) - set(pts_ps_list_pre))
        if not pts_ps_list:
            log("Error during pts startup!")
            return

        self._pts_proc = pts_ps_list[0]

        log("Started new PTS daemon with pid: %d" % self._pts_proc.ProcessId)

        self._pts_logger = PTSLogger()
        self._pts_sender = PTSSender()

        # cached frequently used PTS attributes: due to optimisation reasons it
        # is avoided to contact PTS. These attributes should not change anyway.
        self.__bd_addr = None

        self._com_logger = win32com.client.dynamic.Dispatch(
            win32com.server.util.wrap(self._pts_logger))
        self._com_sender = win32com.client.dynamic.Dispatch(
            win32com.server.util.wrap(self._pts_sender))

        self._pts.SetControlClientLoggerCallback(self._com_logger)
        self._pts.RegisterImplicitSendCallbackEx(self._com_sender)

        log("PTS Version: %s", self.get_version())
        log("PTS Bluetooth Address: %s", self.get_bluetooth_address())
        log("PTS BD_ADDR: %s" % self.bd_addr())

    def stop_pts(self):
        """Stops PTS"""

        try:
            log("About to stop PTS with pid: %d", self._pts_proc.ProcessId)
            self._pts_proc.Terminate()
            self._pts_proc = None

        except Exception as error:
            logging.exception(repr(error))

        self._init_attributes()

    def create_workspace(self, bd_addr, pts_file_path, workspace_name,
                         workspace_path):
        """Creates a new workspace"""

        log("%s %s %s %s %s", self.create_workspace.__name__, bd_addr,
            pts_file_path, workspace_name, workspace_path)

        self._pts.CreateWorkspace(bd_addr, pts_file_path, workspace_name,
                                  workspace_path)

    def delete_temp_workspace(self):
        if self._temp_workspace_path and os.path.exists(self._temp_workspace_path):
            os.remove(self._temp_workspace_path)

    @pts_lock_wrapper(PTS_START_LOCK)
    def open_workspace(self, workspace_path):
        """Opens existing workspace"""

        log("%s %s", self.open_workspace.__name__, workspace_path)

        # auto-pts own workspaces
        autopts_workspaces = get_own_workspaces()

        if workspace_path in list(autopts_workspaces.keys()):
            workspace_name = workspace_path
            workspace_path = autopts_workspaces[workspace_path]
            log("Using %s workspace: %s", workspace_name, workspace_path)

        if not os.path.isfile(workspace_path):
            raise Exception("Workspace file '%s' does not exist" %
                            (workspace_path,))

        specified_ext = os.path.splitext(workspace_path)[1]
        if PTS_WORKSPACE_FILE_EXT != specified_ext:
            raise Exception(
                "Workspace file '%s' extension is wrong, should be %s" %
                (workspace_path, PTS_WORKSPACE_FILE_EXT))

        # Workaround CASE0044114 PTS issue
        # Do not open original workspace file that can become broken by
        # TestCase. Instead use a copy of this file
        if self._temp_workspace_path and \
                os.path.exists(self._temp_workspace_path):
            os.unlink(self._temp_workspace_path)

        workspace_dir = os.path.dirname(workspace_path)
        workspace_name = os.path.basename(workspace_path)

        temp_workspace_dir = os.path.join(workspace_dir, "_" + self.get_bluetooth_address())
        Path(temp_workspace_dir).mkdir(parents=False, exist_ok=True)

        self._temp_workspace_path = \
            os.path.join(temp_workspace_dir, "temp_" + workspace_name)
        shutil.copy2(workspace_path, self._temp_workspace_path)
        log("Using temporary workspace: %s", self._temp_workspace_path)

        self._pts.OpenWorkspace(self._temp_workspace_path)
        self.add_recov(self.open_workspace, workspace_path)
        self._cache_test_cases()

    def _cache_test_cases(self):
        """Cache test cases"""
        self._pts_projects.clear()

        for i in range(0, self._pts.GetProjectCount()):
            project_name = self._pts.GetProjectName(i)
            self._pts_projects[project_name] = {}

            for j in range(0, self._pts.GetTestCaseCount(project_name)):
                test_case_name = self._pts.GetTestCaseName(project_name,
                                                           j)
                self._pts_projects[project_name][test_case_name] = j

    def get_project_list(self):
        """Returns list of projects available in the current workspace"""

        return tuple(self._pts_projects.keys())

    def get_project_version(self, project_name):
        """Returns project version"""

        return self._pts.GetProjectVersion(project_name)

    def get_test_case_list(self, project_name):
        """Returns list of active test cases of the specified project"""

        test_case_list = []

        for test_case_name in list(self._pts_projects[project_name].keys()):
            if self._pts.IsActiveTestCase(project_name, test_case_name):
                test_case_list.append(test_case_name)

        return tuple(test_case_list)

    def get_test_case_description(self, project_name, test_case_name):
        """Returns description of the specified test case"""

        test_case_index = self._pts_projects[project_name][test_case_name]

        return self._pts.GetTestCaseDescription(project_name, test_case_index)

    def _revert_temp_changes(self):
        """Recovery default state for test case"""

        if not self._temp_changes:
            return

        log("%s", self._revert_temp_changes.__name__)

        self._recov_in_progress = True

        for tch in self._temp_changes:
            func = tch[0]

            if func == self.update_pixit_param:
                # Look for possible recoverable parameter
                try:
                    '''Search for matching recover function, PIXIT and recover
                    if value was changed. '''
                    item = next(x for x in self._recov if ((x[0] ==
                                                            self.set_pixit) and (x[1][0] ==
                                                                                 tch[1][0]) and (x[1][1] == tch[1][1])))

                    self._recover_item(item)

                except StopIteration:
                    continue

        self._recov_in_progress = False
        self._temp_changes = []

    def run_test_case(self, project_name, test_case_name):
        """Executes the specified Test Case.

        If an error occurs when running test case returns code of an error as a
        string, otherwise returns an empty string
        """

        log("Starting %s %s %s", self.run_test_case.__name__, project_name,
            test_case_name)

        self.last_start_time = time.time()

        self._pts_logger.set_test_case_name(test_case_name)

        error_code = ""

        try:
            self._pts.RunTestCase(project_name, test_case_name)

            self._revert_temp_changes()

        except pythoncom.com_error as e:
            error_code = parse_ptscontrol_error(e)
            self.stop_test_case(project_name, test_case_name)
            self.recover_pts()

        log("Done %s %s %s out: %s", self.run_test_case.__name__,
            project_name, test_case_name, error_code)

        return error_code

    def stop_test_case(self, project_name, test_case_name):
        """NOTE: According to documentation 'StopTestCase() is not currently
        implemented'"""

        log("%s %s %s", self.stop_test_case.__name__, project_name,
            test_case_name)

        self._pts.StopTestCase()

    def get_test_case_count_from_tss_file(self, project_name):
        """Returns the number of test cases that are available in the specified
        project according to TSS file."""

        return self._pts.GetTestCaseCountFromTSSFile(project_name)

    def get_test_cases_from_tss_file(self, project_name):
        """Returns array of test case names according to TSS file."""

        return self._pts.GetTestCasesFromTSSFile(project_name)

    def set_pics(self, project_name, entry_name, bool_value):
        """Set PICS

        Method used to setup workspace default PICS

        This wrapper handles exceptions that PTS throws if PICS entry is
        already set to the same value.

        PTS throws exception if the value passed to UpdatePics is the same as
        the value when PTS was started.

        In C++ HRESULT error with this value is returned:
        PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED (0x849C0032)

        """
        log("%s %s %s %s", self.set_pics.__name__, project_name,
            entry_name, bool_value)

        try:
            self._pts.UpdatePics(project_name, entry_name, bool_value)
            self.add_recov(self.set_pics, project_name, entry_name,
                           bool_value)

        except pythoncom.com_error as e:
            parse_ptscontrol_error(e)

    def set_pixit(self, project_name, param_name, param_value):
        """Set PIXIT

        Method used to setup workspace default PIXIT

        This wrapper handles exceptions that PTS throws if PIXIT param is
        already set to the same value.

        PTS throws exception if the value passed to UpdatePixitParam is the
        same as the value when PTS was started.

        In C++ HRESULT error with this value is returned:
        PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED (0x849C0021)

        """
        log("%s %s %s %s", self.set_pixit.__name__, project_name,
            param_name, param_value)

        try:
            self._pts.UpdatePixitParam(project_name, param_name, param_value)
            self.add_recov(self.set_pixit, project_name, param_name,
                           param_value)

        except pythoncom.com_error as e:
            parse_ptscontrol_error(e)

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
            self._add_temp_change(self.update_pixit_param, project_name,
                                  param_name)

        except pythoncom.com_error as e:
            parse_ptscontrol_error(e)

    def enable_maximum_logging(self, enable):
        """Enables/disables the maximum logging."""

        log("%s %s", self.enable_maximum_logging.__name__, enable)
        self._pts.EnableMaximumLogging(enable)
        self._pts_logger.enable_maximum_logging(enable)

    def set_call_timeout(self, timeout):
        """Sets a timeout period in milliseconds for the RunTestCase() calls
        to PTS."""

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
        """Returns PTS bluetooth address string"""
        device = self._pts.GetSelectedDevice()
        log(f"Remembered device {self._device}, selected device {device}")
        device_to_connect = None
        if self._device is not None and device != self._device:
            log(f"Will select another device {device}")
            device_to_connect = self._device.replace(r'InUse', r'Free')
        else:
            device_to_connect = device.replace(r'InUse', r'Free')

        try:
            if device_to_connect is not None:
                log(f"Will try to connect {device_to_connect}")
                self._pts.SelectDevice(device_to_connect)
            address = self._pts.GetPTSBluetoothAddress()
        except Exception as e:
            logging.exception(e)
            self.disconnect_dongle()
            address = ""

        for i in range(3):
            if address == "":
                self.connect_to_dongle()
                try:
                    address = self._pts.GetPTSBluetoothAddress()
                except Exception as e:
                    log(f"Connecting to dongle failed {e}")
                    self.disconnect_dongle()
            else:
                break
        else:
            raise Exception("Failed to connect dongle after 3 iterations")

        self._device = self._pts.GetSelectedDevice()
        return address

    def connect_to_dongle(self):
        device_to_connect = None
        devices = self._pts.GetDeviceList()
        for device in devices:
            if 'USB:Free' in device:
                log("Connecting to dual-mode dongle")
                device_to_connect = device
                break
            elif 'COM' in device:
                log("Connecting to LE-only dongle")
                device_to_connect = device
                break

        if device_to_connect is not None:
            self._pts.SelectDevice(device_to_connect)

    def disconnect_dongle(self):
        self._pts.SelectDevice('')
        if self._pts.GetSelectedDevice():
            log("Failed to disconnect current dongle")

    def bd_addr(self):
        """Returns PTS Bluetooth address as a colon separated string"""
        # use cached address if available
        if not self.__bd_addr:
            a = self.get_bluetooth_address().upper()
            self.__bd_addr = ":".join(a[i:i + 2] for i in range(0, len(a), 2))

        return self.__bd_addr

    def get_version(self):
        """Returns PTS version"""

        return self._pts.GetPTSVersion()

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

    arg_parser = argparse.ArgumentParser(
        description="PTS Control")

    arg_parser.add_argument(
        "workspace",
        help="Path to PTS workspace to use for testing. It should have %s "
        "extension" % (PTS_WORKSPACE_FILE_EXT,))

    args = arg_parser.parse_args()

    return args
