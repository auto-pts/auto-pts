#!/usr/bin/env python

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

"""Common code for the auto PTS clients"""

import os
import sys
import random
import socket
import logging
import datetime
import xmlrpclib
import Queue
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer

import ptsprojects.stack as stack
from ptsprojects.testcase import get_max_test_case_desc
from ptsprojects.testcase import PTSCallback
from pybtp.types import BTPError
import ptsprojects.ptstypes as ptstypes
from config import SERVER_PORT, CLIENT_PORT

log = logging.debug

RUNNING_TEST_CASE = None

LOG_DIR_NAME = None

# To test autopts client locally:
# Envrinment variable AUTO_PTS_LOCAL must be set for FakeProxy to
# be used. When FakeProxy is used autoptsserver on Windows will
# not be contacted.
AUTO_PTS_LOCAL = os.environ.has_key("AUTO_PTS_LOCAL")

# xmlrpclib._Method patched to get __repr__ and __str__
#
# This is used to log and print xmlrpclib.ServerProxy methods. Without this
# patch TestCase with xmlrpc TestFunc, e.g. pts.update_pixit_param, will cause
# traceback:
#
# Fault: <Fault 1: '<type \'exceptions.Exception\'>:method "update_pixit_param.__str__" is not supported'>
#
# To be used till this fix is backported to python 2.7
# https://bugs.python.org/issue1690840
class _Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args):
        return self.__send(self.__name, args)
    def __repr__(self):
        return "<%s.%s %s %s>" % (self.__class__.__module__,
                                  self.__class__.__name__,
                                  self.__name, self.__send)
    __str__ = __repr__
xmlrpclib._Method = _Method

class ClientCallback(PTSCallback):
    def __init__(self):
        self.exception = Queue.Queue()

    def error_code(self):
        """Return error code or None if there are no errors

        Used by the main thread to get the errors happened in the callback
        thread

        """

        error_code = None

        try:
            exc = self.exception.get_nowait()
        except Queue.Empty:
            pass
        else:
            error_code = get_error_code(exc)
            log("Error %r from the callback thread", error_code)
            self.exception.task_done()

        return error_code

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

        logger = logging.getLogger("{}.{}".format(self.__class__.__name__,
                                                  self.log.__name__))
        log = logger.info

        log("%s %s %s %s" % (ptstypes.PTS_LOGTYPE_STRING[log_type],
                             logtype_string, log_time, log_message))

        try:
            if RUNNING_TEST_CASE is not None:
                RUNNING_TEST_CASE.log(log_type, logtype_string, log_time,
                                      log_message)
        except Exception as e:
            logging.exception("Log caught exception")
            self.exception.put(sys.exc_info()[1])

            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in Log")

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
        """

        logger = logging.getLogger("{}.{}".format(
            self.__class__.__name__, self.on_implicit_send.__name__))

        log = logger.info

        log("*" * 20)
        log("BEGIN OnImplicitSend:")
        log("project_name: %s" % project_name)
        log("wid: %s" % wid)
        log("test_case_name: %s" % test_case_name)
        log("description: %s" % description)
        log("style: %s 0x%x", ptstypes.MMI_STYLE_STRING[style], style)
        log("response: %s %s %s" % (repr(response), type(response),
                                    id(response)))
        log("response_size: %s" % response_size)
        log("response_is_present: %s %s" % (response_is_present,
                                            type(response_is_present)))

        try:
            if RUNNING_TEST_CASE:
                log("Calling test cases on_implicit_send")
                testcase_response = RUNNING_TEST_CASE.on_implicit_send(
                    project_name,
                    wid,
                    test_case_name,
                    description,
                    style,
                    response,
                    response_size,
                    response_is_present)

                log("test case returned on_implicit_send, response: %s",
                    testcase_response)

        except Exception as e:
            logging.exception("OnImplicitSend caught exception")
            self.exception.put(sys.exc_info()[1])

            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in OnImplicitSend")

        log("END OnImplicitSend:")
        log("*" * 20)

        return testcase_response

    def cleanup(self):
        while not self.exception.empty():
            self.exception.get_nowait()
            self.exception.task_done()


class CallbackThread(threading.Thread):
    """Thread for XML-RPC callback server

    To prevent SimpleXMLRPCServer blocking whole app it is started in a thread

    """
    def __init__(self):
        log("%s.%s", self.__class__.__name__, self.__init__.__name__)
        threading.Thread.__init__(self)
        self.callback = ClientCallback()

    def run(self):
        """Starts the xmlrpc callback server"""
        log("%s.%s", self.__class__.__name__, self.run.__name__)

        print "Serving on port {} ...\n".format(CLIENT_PORT)

        server = SimpleXMLRPCServer(("", CLIENT_PORT),
                                    allow_none = True, logRequests = False)
        server.register_instance(self.callback)
        server.register_introspection_functions()
        server.serve_forever()

    def error_code(self):
        log("%s.%s", self.__class__.__name__, self.error_code.__name__)
        return self.callback.error_code()

    def cleanup(self):
        log("%s.%s", self.__class__.__name__, self.cleanup.__name__)
        return self.callback.cleanup()


def get_my_ip_address():
    """Returns the IP address of the host"""
    if get_my_ip_address.cached_address:
        return get_my_ip_address.cached_address

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.connect(('8.8.8.8', 0)) # udp connection to google public dns
    my_ip_address = my_socket.getsockname()[0]

    get_my_ip_address.cached_address = my_ip_address
    return my_ip_address

get_my_ip_address.cached_address = None

def init_logging():
    """Initialize logging"""
    global LOG_DIR_NAME
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
    LOG_DIR_NAME = os.path.join("logs", now)

    while os.path.exists(LOG_DIR_NAME): # make sure it does not exit
        LOG_DIR_NAME += "_"

    os.makedirs(LOG_DIR_NAME)

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
              "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format = format,
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    log("Created logs directory %r", LOG_DIR_NAME)

class FakeProxy(object):
    """Fake PTS XML-RPC proxy client.

    Usefull when testing code locally and auto-pts server is not needed"""

    class System(object):
        def listMethods(self):
            pass

    def __init__(self):
        self.system = FakeProxy.System()

    def restart_pts(self):
        pass

    def set_call_timeout(self, timeout):
        pass

    def get_version(self):
        return 0x65

    def bd_addr(self):
        return "00:01:02:03:04:05"

    def register_xmlrpc_ptscallback(self, client_address, client_port):
        pass

    def unregister_xmlrpc_ptscallback(self):
        pass

    def open_workspace(self, workspace_path):
        pass

    def enable_maximum_logging(self, enable):
        pass

    def update_pixit_param(self, project_name, param_name, new_param_value):
        pass

    def run_test_case(self, project_name, test_case_name):
        pass

    def get_project_count(self):
        """Returns number of projects available in the current workspace"""
        return 1

    def get_project_name(self, project_index):
        """Returns project name"""
        return "Project%d" % project_index

def init_core(server_address, workspace_path, bd_addr, enable_max_logs):
    "Initialization procedure"
    init_logging()

    log("my IP address is: %s", get_my_ip_address())

    if AUTO_PTS_LOCAL:
        proxy = FakeProxy()
    else:
        proxy = xmlrpclib.ServerProxy(
            "http://{}:{}/".format(server_address, SERVER_PORT),
            allow_none = True,)

    print "Starting PTS ...",
    sys.stdout.flush()
    proxy.restart_pts()
    print "OK"

    callback_thread = CallbackThread()
    callback_thread.start()
    proxy.callback_thread = callback_thread

    proxy.set_call_timeout(120000) # milliseconds

    log("Server methods: %s", proxy.system.listMethods())
    log("PTS Version: %x", proxy.get_version())

    # cache locally for quick access (avoid contacting server)
    proxy.q_bd_addr = proxy.bd_addr()
    log("PTS BD_ADDR: %s", proxy.q_bd_addr)

    proxy.register_xmlrpc_ptscallback(get_my_ip_address(), CLIENT_PORT)

    log("Opening workspace: %s", workspace_path)
    proxy.open_workspace(workspace_path)

    if bd_addr:
        project_count = proxy.get_project_count()
        for index in range(project_count):
            project_name = proxy.get_project_name(index)
            log("Set bd_addr PIXIT: %s for project: %s", bd_addr, project_name)
            proxy.update_pixit_param(project_name, "TSPX_bd_addr_iut", bd_addr)

    proxy.enable_maximum_logging(enable_max_logs)

    return proxy

def print_test_case_status(func):
    def wrapper(*args):
        test_case = args[1]
        (index, num_test_cases, num_test_cases_width, max_project_name,
         max_test_case_name, margin, retries_counter) = args[2]

        print (str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case.project_name.ljust(max_project_name + margin) +
               test_case.name.ljust(max_test_case_name + margin - 1)),
        sys.stdout.flush()

        func(*args)

        print("{}".format(test_case.status).ljust(25) +
              ("#{}".format(retries_counter) if retries_counter else ""))

    return wrapper

def log2file(function):
    """Decorator to log function call into separate log file.

    Currently only used with run_test_case

    """
    def wrapper(*args):
        test_case = args[1]
        normalized_name = test_case.name.replace('/', '_')

        # TODO remove project_name prefix from log_filename when GAP project
        # Test Cases will follow the same convention like other projects
        log_filename = os.path.join(
            LOG_DIR_NAME,
            "%s_%s.log" % (test_case.project_name, normalized_name))

        # if log file exists, append date to its name to make it unique
        if os.path.exists(log_filename):
            (root, ext) = os.path.splitext(log_filename)
            now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
            log_filename = "%s_%s%s" % (root, now, ext)

        logger = logging.getLogger()
        file_handler = logging.FileHandler(log_filename)

        format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
                  "%(lineno)-5s %(funcName)-25s : %(message)s")
        formatter = logging.Formatter(format)

        file_handler.setFormatter(formatter)
        # file_handler.setLevel(logging.ERROR)
        logger.addHandler(file_handler)

        function(*args)

        logger.removeHandler(file_handler)

    return wrapper

def get_error_code(exc):
    """Return string error code for argument exception"""
    error_code = None

    if isinstance(exc, BTPError):
        error_code = ptstypes.E_BTP_ERROR

    elif isinstance(exc, socket.timeout):
        error_code = ptstypes.E_BTP_TIMEOUT

    elif isinstance(exc, xmlrpclib.Fault):
        error_code = ptstypes.E_XML_RPC_ERROR

    elif error_code is None:
        error_code = ptstypes.E_FATAL_ERROR

    log("%s returning error code %r for exception %r",
        get_error_code.__name__, error_code, exc)

    return error_code

@print_test_case_status
@log2file
def run_test_case(pts, test_case, *unused):
    """Runs the test case specified by a TestCase instance.

    [1] xmlrpclib.Fault normally happens due to unhandled exception in the
        autoptsserver on Windows

    """
    log("Starting TestCase %s %s", run_test_case.__name__, test_case)

    if AUTO_PTS_LOCAL: # set fake status and return
        statuses = ["PASS", "INCONC", "FAIL", "UNKNOWN VERDICT: NONE",
                    "BTP ERROR", "XML-RPC ERROR", "BTP TIMEOUT"]
        test_case.status = random.choice(statuses)
        return

    global RUNNING_TEST_CASE

    error_code = None

    try:
        RUNNING_TEST_CASE = test_case
        test_case.pre_run()
        error_code = pts.run_test_case(test_case.project_name, test_case.name)

        log("After run_test_case error_code=%r status=%r",
            error_code, test_case.status)

        # raise exception discovered by thread
        thread_error = pts.callback_thread.error_code()
        pts.callback_thread.cleanup()

        if thread_error:
            error_code = thread_error

    except Exception as error:
        error_code = get_error_code(error)

    except:
        error_code = get_error_code(None)

    finally:
        test_case.post_run(error_code) # stop qemu and other commands
        RUNNING_TEST_CASE = None

    log("Done TestCase %s %s", run_test_case.__name__, test_case)

def print_summary(status_count, num_test_cases_str, margin):
    """Prints test case list status summary"""
    print "\nSummary:\n"

    status_str = "Status"
    max_status = len(status_str)
    num_test_cases_width = len(num_test_cases_str)

    for status in status_count:
        if status > max_status:
            max_status = len(status)

    status_just = max_status + margin
    count_just = num_test_cases_width + margin

    title_str = status_str.ljust(status_just) + "Count".rjust(count_just)
    border = "=" * len(title_str)

    print title_str
    print border

    # print each status and count
    for status in sorted(status_count.keys()):
        count = status_count[status]
        print status.ljust(status_just) + str(count).rjust(count_just)

    # print total
    print border
    print "Total".ljust(status_just) + num_test_cases_str.rjust(count_just)

def run_test_cases(pts, test_cases, retries_max=0):
    """Runs a list of test cases"""

    run_count_max = retries_max + 1  # Run test at least once
    run_count = run_count_max

    num_test_cases = len(test_cases)
    num_test_cases_width = len(str(num_test_cases))
    max_project_name, max_test_case_name = get_max_test_case_desc(test_cases)
    margin = 3

    # Summary related stuff
    status_count = {}

    for index, test_case in enumerate(test_cases):
        while True:
            run_test_case(pts, test_case,
                          (index, num_test_cases, num_test_cases_width,
                           max_project_name, max_test_case_name, margin,
                           run_count_max - run_count))
            run_count -= 1
            if test_case.status != 'PASS' and run_count > 0:
                test_case = test_case.copy()
            else:
                break

        if test_case.status in status_count:
            status_count[test_case.status] += 1
        else:
            status_count[test_case.status] = 1

        run_count = run_count_max

    print_summary(status_count, str(num_test_cases), margin)

def get_test_cases_subset(test_cases, test_case_names, excluded_names=None):
    """Return subset of test cases

    test_cases -- list of all test cases, instances on TestCase

    test_case_names -- list of names and matching patterns of test cases.
                       Names in this list specify the subset from test_cases
                       to return.
                       Name may be:
                       - Profile (all test cases from profile)
                       - Matching name pattern (test cases which contains
                            given string pattern)

    excluded_names -- list of names and matching patterns of test cases.
                       Names in this list specify the subset from test_cases
                       to be excluded from run return.
                       Name may be:
                       - Profile (all test cases from profile)
                       - Matching name pattern (test cases which contains
                            given string pattern)

    """
    # protocols and profiles
    profiles = ["GATT", "GAP", "L2CAP", "RFCOMM", "SM", "MESH"]

    # subsets of profiles
    profiles_subset = {
        "GATTC" : [tc for tc in test_cases
                   if tc.project_name == "GATT" and "/CL/" in tc.name],

        "GATTS" : [tc for tc in test_cases
                   if tc.project_name == "GATT" and "/SR/" in tc.name]
    }

    test_cases_dict = {tc.name : tc for tc in test_cases}
    test_cases_subset = []

    if excluded_names:
        profiles = [name for name in profiles if name not in excluded_names]

        for subset_name, tcs in profiles_subset.items():
            profiles_subset[subset_name] = \
                [tc for tc in tcs if tc.name not in excluded_names
                 and tc.project_name not in excluded_names]
            if subset_name in excluded_names:
                for tc in tcs:
                    test_cases.remove(tc)
                del profiles_subset[subset_name]

        test_cases_dict = \
            {tc_name: tc for tc_name, tc in test_cases_dict.items()
             if tc_name not in excluded_names
             and tc.project_name not in excluded_names}
        test_cases = \
            [tc for tc in test_cases if tc.name not in excluded_names
             and tc.project_name not in excluded_names]

    if test_case_names:
        for name in test_case_names:
            # whole profile/protocol
            if name in profiles:
                test_cases_subset += [tc for tc in test_cases
                                      if tc.project_name == name]

            # subset of profile/protocol
            elif name in profiles_subset.keys():
                test_cases_subset += profiles_subset[name]

            # name pattern contain matching
            else:
                for tc in test_cases_dict:
                    if name == tc:
                        test_cases_subset.append(test_cases_dict[tc].copy())
                    elif name in tc:
                        test_cases_subset.append(test_cases_dict[tc])
    else:
        test_cases_subset = test_cases

    return test_cases_subset


def print_test_cases(func):
    class Dummy(object):
        def __call__(self, *args, **kwargs):
            pass

    class DummyPts(object):
        def __getattr__(self, item):
            return Dummy()

    stack.init_stack()

    pts = DummyPts()
    test_cases = func(pts)

    num_test_cases = len(test_cases)
    num_test_cases_width = len(str(num_test_cases))
    max_project_name, max_test_case_name = get_max_test_case_desc(test_cases)
    margin = 3

    for index, test_case in enumerate(test_cases):
        print(str(index + 1).rjust(num_test_cases_width) +
              "/" +
              str(num_test_cases).ljust(num_test_cases_width + margin) +
              test_case.project_name.ljust(max_project_name + margin) +
              test_case.name.ljust(max_test_case_name + margin - 1))
