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

import ctypes
import logging as root_logging
import os
import shutil
import threading
import time
import xmlrpc.client
from datetime import datetime
from pathlib import Path

import psutil
import pythoncom
import win32com.client
import win32com.server.connect
import win32com.server.util

from autopts.ptsprojects import ptstypes
from autopts.ptsprojects.ptstypes import E_FATAL_ERROR
from autopts.utils import PTS_WORKSPACE_FILE_EXT, ResultWithFlag, count_script_instances, get_own_workspaces
from autopts.winutils import get_pid_by_window_title, kill_all_processes

logging = root_logging.getLogger('server')
log = logging.debug


logtype_whitelist = [ptstypes.PTS_LOGTYPE_START_TEST,
                     ptstypes.PTS_LOGTYPE_END_TEST,
                     ptstypes.PTS_LOGTYPE_ERROR,
                     ptstypes.PTS_LOGTYPE_FINAL_VERDICT]

PTS_START_LOCK = threading.RLock()


def pts_lock_wrapper(lock):
    def _pts_lock_wrapper(func):
        def __pts_lock_wrapper(*args, **kwargs):
            try:
                lock.acquire()
                ret = func(*args, **kwargs)
            finally:
                lock.release()
            return ret

        return __pts_lock_wrapper

    return _pts_lock_wrapper


class AlreadyClosedException(Exception):
    pass


class BadPixitException(Exception):
    pass


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
        self._end = False
        self._tc_status = ResultWithFlag()
        self.in_call = False

    def close(self):
        self._end = True

    def reopen(self):
        self._end = False
        self._test_case_name = None
        self._tc_status.clear()

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

        if self._end:
            raise AlreadyClosedException

        self.in_call = True

        logger = logging.getChild(self.__class__.__name__)

        logger.info("%d %s %s %s", log_type, logtype_string, log_time, log_message)

        try:
            if self._callback is not None:
                if self._maximum_logging or log_type in logtype_whitelist:
                    self._callback.log(log_type, logtype_string, log_time,
                                       log_message, self._test_case_name)

                    # PTS uses PTSLogger.Log only after the RunTestCase
                    # has been finished, so consider only the final verdict
                    # of the test case.
                    # Check for "final verdict" to avoid "Encrypted Verdict".
                    # It could be 'Final verdict' or 'Final Verdict'.
                    if log_type == ptstypes.PTS_LOGTYPE_FINAL_VERDICT and \
                            logtype_string.lower() == "final verdict":

                        if "PASS" in log_message:
                            new_status = "PASS"
                        elif "INDCSV" in log_message:
                            new_status = "INDCSV"
                        elif "INCONC" in log_message:
                            new_status = "INCONC"
                        elif "FAIL" in log_message:
                            new_status = "FAIL"
                        else:
                            new_status = f"UNKNOWN VERDICT: {log_message.strip()}"

                        self._tc_status.set(new_status)
                        log(f"Final verdict found: {self._test_case_name} {new_status}")
        except Exception as e:
            if not self._tc_status.is_set():
                self._tc_status.set(None)
            logging.exception(e)
        finally:
            self.in_call = False

    def get_test_case_status(self, timeout):
        return self._tc_status.get(timeout=timeout, predicate=lambda: not self._end)


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
        self._end = False
        self._response = ResultWithFlag()
        self.in_call = False

    def close(self):
        self._end = True
        self._response.set(None)

    def reopen(self):
        self._end = False
        self._response.clear()

    def set_callback(self, callback):
        """Sets the callback"""
        self._callback = callback

    def unset_callback(self):
        """Unsets the callback"""
        self._callback = None

    def set_wid_response(self, response):
        """Sets response for pending OnImplicitSend"""
        self._response.set(response)

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
        if self._end:
            raise AlreadyClosedException

        self.in_call = True

        logger = logging.getChild(self.__class__.__name__)

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

        rsp = "Cancel"

        try:
            if self._callback and not self._end:
                logger.info(f"Calling callback.on_implicit_send, wid {wid}")
                result = self._callback.on_implicit_send(project_name, wid,
                                                         test_case, description,
                                                         style)

                # Don't block xml-rpc
                if result == "WAIT":
                    def wait_until():
                        logger.debug(f"Waiting for response from callback.on_implicit_send, wid {wid}")
                        return not self._end

                    result = self._response.get(timeout=90, predicate=wait_until)

                if result is not None:
                    rsp = result

                if rsp == "END_TEST_CASE":
                    # Client failed, skip next MMIs
                    self.close()
                    rsp = "Cancel"

                logger.info(f"Response for on_implicit_send (wid {wid}): {rsp}")
        except xmlrpc.client.Fault as err:
            logger.info("A fault occurred, code = %d, string = %s",
                        err.faultCode, err.faultString)
            self.close()

        except Exception as e:
            logger.exception(e)
            self.close()

        finally:
            self._response.clear()

        if rsp in ['No', 'Cancel', 'Abort', None]:
            # NULL pointer is acceptable for any negative response which includes No and Cancel.
            rsp = ""
            rsp_len = 0
            is_present = False
        else:  # if rsp in ['OK', 'Yes', 'Retry' or Edit value]:
            # Stringify response
            rsp = str(rsp)
            rsp_len = str(len(rsp))
            is_present = str(1)

        logger.info("END OnImplicitSend")
        logger.info("*" * 20)

        self.in_call = False

        return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_BSTR,
                                       [rsp, rsp_len, is_present])


def parse_ptscontrol_error(err):
    try:
        # Decode HRESULT code from PTS exception
        _, source, description, _, _, hresult = err.excepinfo

        ptscontrol_e = ctypes.c_uint32(hresult).value
        ptscontrol_e_string = ptstypes.PTSCONTROL_E_STRING[ptscontrol_e]

        logging.exception(ptscontrol_e_string)

        return ptscontrol_e_string

    except Exception as e:
        logging.exception(e)
        # No HRESULT in excepinfo means that the call to COM Object
        # method failed, perhaps the PTS COM Object has been closed.
        return None


class PyPTS:
    """PTS control interface.

    Provides wrappers around Interop.PTSControl.PTSControlClass methods and
    some additional features.

    For detailed documentation see 'Extended Automatiing - Using PTSControl'
    document provided with PTS in file Extended_Automating.pdf

    """

    def __init__(self, device=None, lite_start=False):
        """Constructor"""
        log("%s", self.__init__.__name__)

        self._init_attributes()
        self._end = threading.Event()

        # list of tuples of methods and arguments to recover after PTS restart
        self._recov = []
        self._temp_changes = []
        self._recov_in_progress = False
        self._ready = False

        self._temp_workspace_path = None

        self._pts = None
        self._pts_dispatch_id = None
        self._pts_proc = None
        self._pts_logger = None
        self._pts_sender = None
        self._callback = None
        self.__bd_addr = None
        self._com_logger = None
        self._com_sender = None
        self._preferred_device = device
        self._device = None
        self.lite_start = lite_start
        self._last_recovery_time = datetime.now()

    def _init_attributes(self):
        """Initializes class attributes"""
        log("%s", self._init_attributes.__name__)

        self._pts = None
        self._pts_dispatch_id = None
        self._pts_proc = None

        self._pts_logger = None
        self._pts_sender = None
        self._com_logger = None
        self._com_sender = None

        # Cached frequently used PTS attributes: for optimisation reasons it is
        # avoided to contact PTS. These attributes should not change anyway.
        self.__bd_addr = None

        self._pts_projects = {}

    def cleanup_caches(self):
        self._recov.clear()
        self._recov_in_progress = False

    def ready(self):
        return self._ready

    def terminate(self):
        self._end.set()
        if self._pts_sender:
            self._pts_sender.close()

        if self._pts_logger:
            self._pts_logger.close()

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

    def _replug_dongle(self):
        log(f"{self._replug_dongle.__name__} not implemented")
        pass

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

        log("recover_pts")
        log("recov=%s", self._recov)

        self._recov_in_progress = True

        self.restart_pts()

        for item in self._recov:
            self._recover_item(item)

        self._recov_in_progress = False
        self._last_recovery_time = datetime.now()

        return True

    @pts_lock_wrapper(PTS_START_LOCK)
    def restart_pts(self, args=None):
        """Restarts PTS

        This function will block for a couple of seconds while PTS starts
        """

        log("restart_pts")
        exception = 0
        dongle_init_retry = getattr(args, "dongle_init_retry", 5)

        while not self._end.is_set():
            try:
                self.stop_pts()

                # Only if ykush available
                self._replug_dongle()

                self.start_pts()

                break
            except Exception as e:
                logging.exception(e)
                self.stop_pts()
                # Kill all stale PTS.exe processes only if this is
                # the only running instance of autoptsserver.py
                if count_script_instances('autoptsserver.py') <= 1:
                    kill_all_processes('PTS.exe')
                if dongle_init_retry == 0:
                    continue
                exception += 1
                if exception >= dongle_init_retry:
                    # This stops PTS from restarting indefinitely when PTS
                    # dongle is unplugged
                    print("Please check your dongle connection! Aborting")
                    kill_all_processes('PTS.exe')
                    self.terminate()
                    break

        return True

    @pts_lock_wrapper(PTS_START_LOCK)
    def start_pts(self):
        """Starts PTS

        This function will block for a couple of seconds while PTS starts"""

        log("start_pts")

        self._pts = win32com.client.Dispatch('ProfileTuningSuite_6.PTSControlServer')

        if self.lite_start:
            return True

        # The dispatched COM object cannot be passed between threads directly
        self._pts_dispatch_id = pythoncom.CoMarshalInterThreadInterfaceInStream(
            pythoncom.IID_IDispatch, self._pts)

        log('Started new PTS daemon')

        self._pts_logger = PTSLogger()
        self._pts_sender = PTSSender()

        if self._callback:
            self._pts_logger.set_callback(self._callback)
            self._pts_sender.set_callback(self._callback)

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
        log(f'PTS Bluetooth Address: {self.get_bluetooth_address()}')
        log(f"PTS BD_ADDR: {self.bd_addr()}")
        log(f'PTS daemon PID: {self._get_process_pid()}')

        self._ready = True

        return True

    def stop_pts(self):
        """Stops PTS"""
        log(f"{self.stop_pts.__name__}")
        self._ready = False

        if self._pts_logger:
            log("Closing PTSLogger")
            log("Closing PTSSender")
            # No new calls to the PTS callbacks after closing
            self._pts_logger.close()
            self._pts_sender.close()

            # Wait until the PTS callbacks are out of fn call to decrease
            # a chance of breaking the log file handler lock
            for _i in range(10):
                if not self._pts_logger.in_call and not self._pts_sender.in_call:
                    break
                time.sleep(1)

            self._pts_logger = None
            self._pts_sender = None

        if self._pts:
            pid = self._get_process_pid()
            log(f"About to stop PTS with pid: {pid}")

            if pid and psutil.pid_exists(pid):
                # If we have the pid, lets just terminate the process.
                # This is faster that ExitPTS. Moreover, the ExitPTS
                # can fail to close the PTS due to a broken COM server.
                try:
                    del self._com_logger
                    del self._com_sender
                    del self._pts_logger
                    del self._pts_sender
                    del self._pts_dispatch_id
                    del self._pts
                    self._com_logger = None
                    self._com_sender = None
                    self._pts_logger = None
                    self._pts_sender = None
                    self._pts_dispatch_id = None
                    self._pts = None
                    self._pts_proc.terminate()
                except Exception as error:
                    logging.exception(repr(error))
                finally:
                    self._pts_proc = None
            else:
                try:
                    log("Terminating with ExitPTS command")
                    self._pts.ExitPTS()
                except Exception:
                    # The COM timeout exception is a valid behavior here,
                    # since the PTS closes itself within ExitPTS(). It takes
                    # exactly 5 seconds to receive the exception, because
                    # Windows do not delete the COM server right away, instead
                    # it waits a little in case someone wants to reconnect to it.
                    pass

        self._init_attributes()

    def set_wid_response(self, response):
        if self._pts_sender:
            self._pts_sender.set_wid_response(response)

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
    def open_workspace(self, workspace_path, copy):
        """Opens existing workspace"""

        log(f"open_workspace {workspace_path}")

        # auto-pts own workspaces
        autopts_workspaces = get_own_workspaces()

        if workspace_path in list(autopts_workspaces.keys()):
            workspace_name = workspace_path
            workspace_path = autopts_workspaces[workspace_path]
            log("Using %s workspace: %s", workspace_name, workspace_path)

        if not os.path.isfile(workspace_path):
            raise Exception(f"Workspace file '{workspace_path}' does not exist")

        specified_ext = os.path.splitext(workspace_path)[1]
        if PTS_WORKSPACE_FILE_EXT != specified_ext:
            raise Exception(
                f"Workspace file '{workspace_path}' extension is wrong, should be {PTS_WORKSPACE_FILE_EXT}"
            )

        # Workaround CASE0044114 PTS issue
        # Do not open original workspace file that can become broken by
        # TestCase. Instead use a copy of this file
        if copy:
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
        else:
            self._pts.OpenWorkspace(workspace_path)

        self.add_recov(self.open_workspace, workspace_path, copy)
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

        err = None

        try:
            self._pts_logger.reopen()
            self._pts_logger.set_test_case_name(test_case_name)
            self._pts_sender.reopen()

            # Workaround for PTS issue 145370.
            # PTS server can detect that the PTS dongle had been corrupted
            # by calling GetPTSBluetoothAddress() before test case started.
            address = None
            for _i in range(10):
                try:
                    address = self._pts.GetPTSBluetoothAddress()
                    log(f"GetPTSBluetoothAddress(): {address}")
                    if address:
                        break
                except Exception as e:
                    log(e)
                finally:
                    # The dongle verification should take less than 100ms,
                    # but it might take longer on a slow VM.
                    time.sleep(float(os.environ.get('GLOBAL_DONGLE_INIT_DELAY')))

            if not address:
                raise Exception("Bluetooth address not available")

            self._pts.RunTestCase(project_name, test_case_name)

            err = self._pts_logger.get_test_case_status(timeout=30)

            self._revert_temp_changes()
        except Exception as e:
            # PTS exception or COM Object exception
            if isinstance(e, pythoncom.com_error):
                err = parse_ptscontrol_error(e)
                # If successfully parsed, it was PTS exception

            self.stop_test_case(project_name, test_case_name)
            self.recover_pts()

        if not err:
            # Nonblocking methods will not throw exceptions
            err = E_FATAL_ERROR

        log("Done %s %s %s out: %s", self.run_test_case.__name__,
            project_name, test_case_name, err)

        return err

    def stop_test_case(self, project_name, test_case_name):
        log("%s %s %s", self.stop_test_case.__name__, project_name,
            test_case_name)

        # After close, the sender will send 'Cancel' as WID response
        if self._pts_sender:
            self._pts_sender.close()

        # NOTE: According to documentation 'StopTestCase() is not
        # currently implemented'. If by any chance this changes in
        # the future, try the code below to use unmarshalling, because
        # a dispatched COM Object cannot be shared directly between threads:
        # pythoncom.CoInitialize()
        # # Get dispatched PTS interface from the id
        # pts = win32com.client.Dispatch(
        #     pythoncom.CoGetInterfaceAndReleaseStream(self._pts_dispatch_id, pythoncom.IID_IDispatch))
        # pts.StopTestCase()
        # pythoncom.CoUninitialize()

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

        except BaseException as e:
            if not parse_ptscontrol_error(e):
                raise Exception(e) from e

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

        except Exception as e:
            if isinstance(e, (pythoncom.com_error, TypeError)):
                err = parse_ptscontrol_error(e)
                if not err:
                    err = str(e)

                raise BadPixitException(f'{project_name} {param_name} {param_value}:\n{err}') from e

            raise Exception(e) from e

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
        except Exception as e:
            if isinstance(e, (pythoncom.com_error, TypeError)):
                err = parse_ptscontrol_error(e)
                if not err:
                    err = str(e)

                raise BadPixitException(f'{project_name} {param_name} value={new_param_value} :\n{err}') from e

            raise Exception(e) from e

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

    def _get_process_pid(self, retry=10):
        if self.__bd_addr is None:
            return None

        address = self.__bd_addr.replace(':', '')

        if self._pts_proc:
            return self._pts_proc.pid

        pts_window_title = f'PTS - {address.upper()}'
        pid = None

        for _i in range(retry):
            pid = get_pid_by_window_title(pts_window_title)

            if pid is None:
                log(f'Failed to find PTS window with title: {pts_window_title}.')
                return None

        self._pts_proc = psutil.Process(pid)

        return pid

    def _get_connectable_dongle(self, port):
        devices = self._pts.GetDeviceList()
        log(f'GetDeviceList: {devices}')
        if port:
            # Selected device has to be visible by PTS
            if port not in devices:
                log(f'The port {port} is not available')
                return None
        else:
            # Select random device
            for device in devices:
                if not device.startswith('USB:InUse'):
                    port = device
                    break

        return port

    def get_bluetooth_address(self):
        """Returns PTS bluetooth address string"""
        log(self.get_bluetooth_address.__name__)

        if self.lite_start:
            return 'xxxxxxxxxxxx'

        address = None
        if self._device:
            # The dongle already connected. Try to read the address.
            for _i in range(10):
                try:
                    # As described in the PTS CONTROL API documentation, the
                    # GetPTSBluetoothAddress() may not be immediately available
                    # after PTS is started.
                    address = self._pts.GetPTSBluetoothAddress()
                    break
                except Exception as e:
                    log(e)

        if not address:
            # First connect at init or reconnect after fail to read the address
            address = self._connect_to_dongle()

        return address

    def _connect_to_dongle(self):
        log(self._connect_to_dongle.__name__)

        port = None
        address = None
        device_to_connect = ''
        selected_device = self._pts.GetSelectedDevice()

        log(f"Remembered device: {self._device}, selected device: {selected_device}, "
            f"preferred device: {self._preferred_device}")

        # Possible use cases:
        # 1. Connect always to the preferred device(--dongle option).
        # 2. Reconnect to the device connected at init.
        # 3. PTS already connected to random dongle at its startup
        # (happens only for BR/EDR/LE dongles).
        # 4. First connection, no preferred device specified, BR/EDR/LE
        # dongle not found by PTS at its startup, hence connecting randomly
        # to LE only dongle or other available device.
        if self._preferred_device:
            log(f'Using device selected with --dongle option: {self._preferred_device}')
            device_to_connect = self._preferred_device
        elif self._device is not None:
            log(f'Using the device selected at first init: {self._device}')
            device_to_connect = self._device.strip().replace(r'InUse', r'Free')
        elif selected_device:
            log(f'Random dongle selected by PTS at startup: {selected_device}')
            device_to_connect = selected_device.replace(r'InUse', r'Free')
        else:
            # The selected_device should be empty string here.
            log('First random dongle selection')

        if device_to_connect and device_to_connect == selected_device.replace(r'InUse', r'Free'):
            log(f'PTS already connected to the right dongle: {device_to_connect}')
            address = self._pts.GetPTSBluetoothAddress()
            self._device = device_to_connect
            return address

        for _i in range(4):
            try:
                port = self._get_connectable_dongle(device_to_connect)
                if not port:
                    self._disconnect_dongle()
                    continue

                log(f"Will try to connect {port}")
                self._pts.SelectDevice(port)
                address = self._pts.GetPTSBluetoothAddress()
                self._device = self._pts.GetSelectedDevice()
                log(f'Successfully connected to the dongle with address: {address}')
                break
            except Exception as e:
                address = None
                log(f"Connecting to dongle {port} failed")
                logging.exception(e)
                self._disconnect_dongle()

        if not address:
            raise Exception('Failed to connect dongle after 4 iterations')

        return address

    def _disconnect_dongle(self):
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

        self._callback = callback

        if not self._ready:
            return

        self._pts_logger.set_callback(callback)
        self._pts_sender.set_callback(callback)

    def unregister_ptscallback(self):
        """Unregisters the testcase.PTSCallback callback"""

        log("%s", self.unregister_ptscallback.__name__)

        self._callback = None

        if not self._ready:
            return

        self._pts_logger.unset_callback()
        self._pts_sender.unset_callback()

    def get_last_recovery_time(self):
        return self._last_recovery_time
