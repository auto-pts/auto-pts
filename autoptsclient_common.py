#!/usr/bin/env python

"""Common code for the auto PTS clients"""

import os
import sys
import socket
import logging
import xmlrpclib
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer
from ptsprojects.testcase import get_max_test_case_desc
from ptsprojects.testcase import TestCase, TestCmd, PTSCallback
import ptsprojects.ptstypes as ptstypes

log = logging.debug

SERVER_PORT = 65000

RUNNING_TEST_CASE = None

class ClientCallback(PTSCallback):
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
            log("Caught exception")
            log(e)
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
        log("style: Ox%x" % style)
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

                log("test case returned on_implicit_send, respose: %s",
                    testcase_response)

        except Exception as e:
            log("Caught exception")
            log(e)
            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in OnImplicitSend")

        log("END OnImplicitSend:")
        log("*" * 20)

        return testcase_response

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

def start_callback():
    """Starts the xmlrpc callback server"""

    callback = ClientCallback()

    print "Serving on port {} ...\n".format(SERVER_PORT)

    server = SimpleXMLRPCServer(("", SERVER_PORT),
                                allow_none = True, logRequests = False)
    server.register_instance(callback)
    server.register_introspection_functions()
    server.serve_forever()

def init_core(server_address, workspace_path, bd_addr):
    "Initialization procedure"

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    format = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
              "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format = format,
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    log("my IP address is: %s", get_my_ip_address())

    proxy = xmlrpclib.ServerProxy(
        "http://{}:{}/".format(server_address, SERVER_PORT),
        allow_none = True,)

    print "Starting PTS ...",
    sys.stdout.flush()
    proxy.restart_pts()
    print "OK"

    # to prevent SimpleXMLRPCServer blocking whole app start it in a thread
    thread = threading.Thread(target = start_callback)
    thread.start()

    proxy.set_call_timeout(120000) # milliseconds

    log("Server methods: %s", proxy.system.listMethods())
    log("PTS Version: %x", proxy.get_version())
    log("PTS BD_ADDR: %s", proxy.bd_addr())

    proxy.register_xmlrpc_ptscallback(get_my_ip_address(), SERVER_PORT)

    log("Opening workspace: %s", workspace_path)
    proxy.open_workspace(workspace_path)

    if bd_addr:
        project_count = proxy.get_project_count()
        for index in range(project_count):
            project_name = proxy.get_project_name(index)
            log("Set bd_addr PIXIT: %s for project: %s", bd_addr, project_name)
            proxy.update_pixit_param(project_name, "TSPX_bd_addr_iut", bd_addr)

    return proxy

def run_test_case(pts, test_case):
    """Runs the test case specified by a TestCase instance."""
    log("Starting TestCase %s %s", run_test_case.__name__, test_case)

    global RUNNING_TEST_CASE
    RUNNING_TEST_CASE = test_case

    test_case.pre_run()
    error_code = pts.run_test_case(test_case.project_name, test_case.name)
    test_case.post_run(error_code)
    RUNNING_TEST_CASE = None

    log("Done TestCase %s %s", run_test_case.__name__, test_case)

def run_test_cases(pts, test_cases):
    """Runs a list of test cases"""

    num_test_cases = len(test_cases)
    num_test_cases_width = len(str(num_test_cases))
    max_project_name, max_test_case_name = get_max_test_case_desc(test_cases)
    margin = 3

    for index, test_case in enumerate(test_cases):
        print (str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case.project_name.ljust(max_project_name + margin) +
               test_case.name.ljust(max_test_case_name + margin - 1)),
        sys.stdout.flush()
        run_test_case(pts, test_case)
        print test_case.status
