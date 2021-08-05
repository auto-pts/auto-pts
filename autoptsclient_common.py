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
import argparse
import datetime
import errno
import importlib
import logging
import os
import queue
import random
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import xml.etree.ElementTree as ElementTree
import xmlrpc.client
from distutils.spawn import find_executable
from xmlrpc.server import SimpleXMLRPCServer

import _locale
from termcolor import colored

import ptsprojects.ptstypes as ptstypes
from config import SERVER_PORT, CLIENT_PORT
from ptsprojects import stack
from ptsprojects.testcase import PTSCallback, TestCaseLT1, TestCaseLT2
from ptsprojects.testcase_db import TestCaseTable
from pybtp import btp
from pybtp.types import BTPError, SynchError
from utils import InterruptableThread
from winutils import have_admin_rights

log = logging.debug

RUNNING_TEST_CASE = {}
TEST_CASE_DB = None

autoprojects = None

profiles = {'dis', 'gap', 'gatt', 'sm', 'l2cap', 'mesh', 'mmdl'}

# To test autopts client locally:
# Envrinment variable AUTO_PTS_LOCAL must be set for FakeProxy to
# be used. When FakeProxy is used autoptsserver on Windows will
# not be contacted.
AUTO_PTS_LOCAL = "AUTO_PTS_LOCAL" in os.environ


# xmlrpclib._Method patched to get __repr__ and __str__
#
# This is used to log and print xmlrpclib.ServerProxy methods. Without this
# patch TestCase with xmlrpc TestFunc, e.g. pts.update_pixit_param, will cause
# traceback:
#
# Fault: <Fault 1: '<type \'exceptions.Exception\'>:method
# "update_pixit_param.__str__" is not supported'>
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


xmlrpc.client._Method = _Method


class ClientCallback(PTSCallback):
    def __init__(self):
        super().__init__()
        self.exception = queue.Queue()
        self._pending_responses = {}

    def error_code(self):
        """Return error code or None if there are no errors

        Used by the main thread to get the errors happened in the callback
        thread

        """

        error_code = None

        try:
            exc = self.exception.get_nowait()
        except queue.Empty:
            pass
        else:
            error_code = get_error_code(exc)
            log("Error %r from the callback thread", error_code)
            self.exception.task_done()

        return error_code

    def log(self, log_type, logtype_string, log_time, log_message,
            test_case_name):
        """Implements:

        interface IPTSControlClientLogger : IUnknown {
            HRESULT _stdcall Log(
                            [in] _PTS_LOGTYPE logType,
                            [in] LPWSTR szLogType,
                            [in] LPWSTR szTime,
                            [in] LPWSTR pszMessage);
        };

        test_case_name - To be identified by client in case of multiple pts
                         usage.
        """

        logger = logging.getLogger("{}.{}".format(self.__class__.__name__,
                                                  self.log.__name__))
        logger.info("%s %s %s %s %s", ptstypes.PTS_LOGTYPE_STRING[log_type],
                    logtype_string, log_time, test_case_name,
                    log_message)

        try:
            if test_case_name in RUNNING_TEST_CASE:
                RUNNING_TEST_CASE[test_case_name].log(log_type, logtype_string,
                                                      log_time, log_message, test_case_name)

        except Exception as e:
            logging.exception(e)
            self.exception.put(sys.exc_info()[1])

            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in Log")

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
        """

        logger = logging.getLogger("{}.{}".format(
            self.__class__.__name__, self.on_implicit_send.__name__))

        logger.info("*" * 20)
        logger.info("BEGIN OnImplicitSend:")
        logger.info("project_name: %s", project_name)
        logger.info("wid: %s", wid)
        logger.info("test_case_name: %s", test_case_name)
        logger.info("description: %s", description)
        logger.info("style: %s 0x%x", ptstypes.MMI_STYLE_STRING[style], style)

        try:
            # XXX: 361 WID MESH sends tc name with leading white spaces
            test_case_name = test_case_name.lstrip()

            logger.info("Calling test cases on_implicit_send")

            testcase_response = RUNNING_TEST_CASE[test_case_name].on_implicit_send(project_name, wid, test_case_name,
                                                                                   description, style)

            logger.info("test case returned on_implicit_send, response: %s",
                        testcase_response)

        except Exception as e:
            logging.exception("OnImplicitSend caught exception %s", e)
            self.exception.put(sys.exc_info()[1])

            # exit does not work, cause app is blocked in PTS.RunTestCase?
            sys.exit("Exception in OnImplicitSend")

        logger.info("END OnImplicitSend:")
        logger.info("*" * 20)

        return testcase_response

    def get_pending_response(self, test_case_name):
        log("%s.%s, %s", self.__class__.__name__,
            self.get_pending_response.__name__, test_case_name)
        if not self._pending_responses:
            return None

        rsp = self._pending_responses.pop(test_case_name, None)
        if not rsp:
            return rsp

        if rsp["delay"]:
            time.sleep(rsp["delay"])
        return rsp["value"]

    def set_pending_response(self, pending_response):
        tc_name = pending_response[0]
        response = pending_response[1]
        delay = pending_response[2]

        self._pending_responses[tc_name] = {"value": response, "delay": delay}

    def clear_pending_responses(self):
        self._pending_responses = {}

    def cleanup(self):
        self.clear_pending_responses()

        while not self.exception.empty():
            self.exception.get_nowait()
            self.exception.task_done()


class CallbackThread(threading.Thread):
    """Thread for XML-RPC callback server

    To prevent SimpleXMLRPCServer blocking whole app it is started in a thread

    """

    def __init__(self, port):
        log("%s.%s port=%r", self.__class__.__name__, self.__init__.__name__, port)
        threading.Thread.__init__(self)
        self.callback = ClientCallback()
        self.port = port
        self.current_test_case = None

    def run(self):
        """Starts the xmlrpc callback server"""
        log("%s.%s", self.__class__.__name__, self.run.__name__)

        log("Serving on port %s ...", self.port)

        server = SimpleXMLRPCServer(("", self.port),
                                    allow_none=True, logRequests=False)
        server.register_instance(self.callback)
        server.register_introspection_functions()
        server.serve_forever()

    def set_current_test_case(self, name):
        log("%s.%s %s", self.__class__.__name__, self.set_current_test_case.__name__, name)
        self.current_test_case = name

    def get_current_test_case(self):
        log("%s.%s %s", self.__class__.__name__, self.get_current_test_case.__name__, self.current_test_case)
        return self.current_test_case

    def error_code(self):
        log("%s.%s", self.__class__.__name__, self.error_code.__name__)
        return self.callback.error_code()

    def set_pending_response(self, pending_response):
        log("%s.%s, %r", self.__class__.__name__,
            self.set_pending_response.__name__, pending_response)
        return self.callback.set_pending_response(pending_response)

    def clear_pending_responses(self):
        log("%s.%s", self.__class__.__name__,
            self.clear_pending_responses.__name__)
        return self.callback.clear_pending_responses()

    def cleanup(self):
        log("%s.%s", self.__class__.__name__, self.cleanup.__name__)
        return self.callback.cleanup()


def get_my_ip_address():
    """Returns the IP address of the host"""
    if get_my_ip_address.cached_address:
        return get_my_ip_address.cached_address

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.connect(('8.8.8.8', 0))  # udp connection to google public dns
    my_ip_address = my_socket.getsockname()[0]

    get_my_ip_address.cached_address = my_ip_address
    return my_ip_address


def get_unique_name(pts):
    name = 'Tester'

    # get address of PTS dongle IUT is connecting to
    pts_addr = pts.q_bd_addr.replace(":", "")
    # use last 6 characters of PTS dongle adress
    name += "_" + pts_addr[6:12]

    return name.encode('utf-8')


get_my_ip_address.cached_address = None


def init_logging(tag=""):
    """Initialize logging"""
    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s%s.log" % (script_name_no_ext, tag)
    format_template = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
                       "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format=format_template,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)


class FakeProxy:
    """Fake PTS XML-RPC proxy client.

    Usefull when testing code locally and auto-pts server is not needed"""

    class System:
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


def init_pts_thread_entry_wrapper(func):
    def wrapper(*args):
        exeptions = args[6]
        try:
            func(*args)
        except Exception as exc:
            logging.exception(exc)
            exeptions.put(exc)

    return wrapper


@init_pts_thread_entry_wrapper
def init_pts_thread_entry(proxy, local_address, local_port, workspace_path,
                          bd_addr, enable_max_logs, exceptions):
    """PTS instance initialization thread function entry"""

    sys.stdout.flush()
    proxy.restart_pts()
    print("(%r) OK" % (id(proxy),))

    proxy.callback_thread = CallbackThread(local_port)
    proxy.callback_thread.start()

    proxy.set_call_timeout(300000)  # milliseconds

    log("Server methods: %s", proxy.system.listMethods())
    log("PTS Version: %s", proxy.get_version())

    # cache locally for quick access (avoid contacting server)
    proxy.q_bd_addr = proxy.bd_addr()
    log("PTS BD_ADDR: %s", proxy.q_bd_addr)

    client_ip_address = local_address
    if client_ip_address is None:
        client_ip_address = get_my_ip_address()

    log("Client IP Address: %s", client_ip_address)

    proxy.register_xmlrpc_ptscallback(client_ip_address, local_port)

    log("Opening workspace: %s", workspace_path)
    proxy.open_workspace(workspace_path)

    if bd_addr:
        projects = proxy.get_project_list()
        for project_name in projects:
            log("Set bd_addr PIXIT: %s for project: %s", bd_addr, project_name)
            proxy.update_pixit_param(project_name, "TSPX_bd_addr_iut", bd_addr)

    proxy.enable_maximum_logging(enable_max_logs)


def init_pts(args, tc_db_table_name=None):
    """Initialization procedure for PTS instances"""

    proxy_list = []
    thread_list = []
    exceptions = queue.Queue()

    init_logging('_' + '_'.join(str(x) for x in args.cli_port))

    for server_addr, local_addr, server_port, local_port \
            in zip(args.ip_addr, args.local_addr, args.srv_port, args.cli_port):
        if AUTO_PTS_LOCAL:
            proxy = FakeProxy()
        else:
            proxy = xmlrpc.client.ServerProxy(
                "http://{}:{}/".format(server_addr, server_port),
                allow_none=True, )

        print("(%r) Starting PTS %s:%s ..." % (id(proxy), server_addr, server_port))

        thread = threading.Thread(target=init_pts_thread_entry,
                                  args=(proxy, local_addr, local_port, args.workspace,
                                        args.bd_addr, args.enable_max_logs, exceptions))
        thread.start()

        proxy_list.append(proxy)
        thread_list.append(thread)

    if tc_db_table_name:
        global TEST_CASE_DB
        TEST_CASE_DB = TestCaseTable(tc_db_table_name)

    for index, thread in enumerate(thread_list):
        thread.join(timeout=180.0)

        # check init completed
        if thread.is_alive():
            raise Exception("(%r) init failed" % (id(proxy_list[index]),))

    exeption_msg = ''
    while not exceptions.empty():
        try:
            exeption_msg += str(exceptions.get_nowait()) + '\n'
        except BaseException as e:
            logging.exception(e)
            traceback.print_exc()
        finally:
            print(exeption_msg)

    if exeption_msg != '':
        raise Exception(exeption_msg, proxy_list)

    return proxy_list


def reinit_pts(ptses, args, tc_db_table_name=None):
    """Reinitialization procedure for PTS instances"""

    try:
        for pts in ptses:
            pts.unregister_xmlrpc_ptscallback()
    except BaseException as e:
        logging.exception(e)
        traceback.print_exc()

    return init_pts(args, tc_db_table_name)


def get_result_color(status):
    if status == "PASS":
        return "green"
    if status == "FAIL":
        return "red"
    if status == "INCONC":
        return "yellow"
    return "white"


class TestCaseRunStats:
    def __init__(self, projects, test_cases, retry_count, db=None):

        self.run_count_max = retry_count + 1  # Run test at least once
        self.run_count = 0  # Run count of current test case
        self.num_test_cases = len(test_cases)
        self.num_test_cases_width = len(str(self.num_test_cases))
        self.max_project_name = len(max(projects, key=len)) if projects else 0
        self.max_test_case_name = len(max(test_cases, key=len)) if test_cases else 0
        self.margin = 3
        self.index = 0

        self.xml_results = tempfile.NamedTemporaryFile(delete=False).name
        root = ElementTree.Element("results")
        tree = ElementTree.ElementTree(root)
        tree.write(self.xml_results)

        self.db = db

        if self.db:
            self.est_duration = db.estimate_session_duration(test_cases,
                                                             self.run_count_max)
            if self.est_duration:
                approx = str(datetime.timedelta(seconds=self.est_duration))

                print("Number of test cases to run: ", self.num_test_cases, " in approximately: ", approx)
        else:
            self.est_duration = 0

    def update(self, test_case_name, duration, status):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        elem = root.find("./test_case[@name='%s']" % test_case_name)
        if elem is None:
            elem = ElementTree.SubElement(root, 'test_case')

            status_previous = None
            if self.db:
                status_previous = self.db.get_result(test_case_name)

            elem.attrib["project"] = test_case_name.split('/')[0]
            elem.attrib["name"] = test_case_name
            elem.attrib["duration"] = str(duration)
            elem.attrib["status"] = ""
            elem.attrib["status_previous"] = str(status_previous)

            run_count = 0
        else:
            run_count = int(elem.attrib["run_count"])

        elem.attrib["status"] = status

        regression = bool(elem.attrib["status"] != "PASS" and elem.attrib["status_previous"] == "PASS")

        elem.attrib["regression"] = str(regression)
        elem.attrib["run_count"] = str(run_count + 1)

        tree.write(self.xml_results)

        return regression

    def get_results(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        results = {}

        for tc_xml in root.findall("./test_case"):
            results[tc_xml.attrib["name"]] = \
                tc_xml.attrib["status"]

        return results

    def get_regressions(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()
        tcs_xml = root.findall("./test_case[@regression='True']")

        return [tc_xml.attrib["name"] for tc_xml in tcs_xml]

    def get_status_count(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        status_dict = {}

        for test_case_xml in root.findall("./test_case"):
            if test_case_xml.attrib["status"] not in status_dict:
                status_dict[test_case_xml.attrib["status"]] = 0

            status_dict[test_case_xml.attrib["status"]] += 1

        return status_dict

    def print_summary(self):
        """Prints test case list status summary"""
        print("\nSummary:\n")

        status_str = "Status"
        status_str_len = len(status_str)
        count_str_len = len("Count")
        total_str_len = len("Total")
        regressions_str = "Regressions"
        regressions_str_len = len(regressions_str)
        regressions_count = len(self.get_regressions())
        regressions_count_str_len = len(str(regressions_count))
        num_test_cases_str = str(self.num_test_cases)
        num_test_cases_str_len = len(num_test_cases_str)
        status_count = self.get_status_count()

        status_just = max(status_str_len, total_str_len)
        count_just = max(count_str_len, num_test_cases_str_len)

        title_str = ''
        border = ''

        if regressions_count != 0:
            status_just = max(status_just, regressions_str_len)
            count_just = max(count_just, regressions_count_str_len)

        for status, count in list(status_count.items()):
            status_just = max(status_just, len(status))
            count_just = max(count_just, len(str(count)))

            status_just += self.margin
            title_str = status_str.ljust(status_just) + "Count".rjust(count_just)
            border = "=" * (status_just + count_just)

        print(title_str)
        print(border)

        # print each status and count
        for status in sorted(status_count.keys()):
            count = status_count[status]
            print(status.ljust(status_just) + str(count).rjust(count_just))

        # print total
        print(border)
        print("Total".ljust(status_just) + num_test_cases_str.rjust(count_just))

        if regressions_count != 0:
            print(border)

        print(regressions_str.ljust(status_just) +
              str(regressions_count).rjust(count_just))


def run_test_case_wrapper(func):
    def wrapper(*args):
        test_case_name = args[2]
        stats = args[3]

        run_count_max = stats.run_count_max
        run_count = stats.run_count
        num_test_cases = stats.num_test_cases
        num_test_cases_width = stats.num_test_cases_width
        max_project_name = stats.max_project_name
        max_test_case_name = stats.max_test_case_name
        margin = stats.margin
        index = stats.index

        print((str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case_name.split('/')[0].ljust(max_project_name + margin) +
               test_case_name.ljust(max_test_case_name + margin - 1)), end=' ')
        sys.stdout.flush()

        start_time = time.time()
        status = func(*args)
        end_time = time.time() - start_time

        regression = stats.update(test_case_name, end_time, status)

        retries_max = run_count_max - 1
        if run_count:
            retries_msg = "#{}".format(run_count)
        else:
            retries_msg = ""

        if regression and run_count == retries_max:
            regression_msg = "REGRESSION"
        else:
            regression_msg = ""

        end_time_str = str(round(datetime.timedelta(
            seconds=end_time).total_seconds(), 3))

        result = ("{}".format(status).ljust(16) +
                  end_time_str.rjust(len(end_time_str)) +
                  retries_msg.rjust(len("#{}".format(retries_max)) + margin) +
                  regression_msg.rjust(len("REGRESSION") + margin))

        if sys.stdout.isatty():
            output_color = get_result_color(status)
            print(colored(result, output_color))
        else:
            print(result)

        return status, end_time

    return wrapper


def get_error_code(exc):
    """Return string error code for argument exception"""
    error_code = None

    if isinstance(exc, BTPError):
        error_code = ptstypes.E_BTP_ERROR

    elif isinstance(exc, socket.timeout):
        error_code = ptstypes.E_BTP_TIMEOUT

    elif isinstance(exc, xmlrpc.client.Fault):
        error_code = ptstypes.E_XML_RPC_ERROR

    elif error_code is None:
        error_code = ptstypes.E_FATAL_ERROR

    log("%s returning error code %r for exception %r",
        get_error_code.__name__, error_code, exc)

    return error_code


def synchronize_instances(state, break_state=None):
    """Synchronize instances to be in one state before executing further"""
    while True:
        time.sleep(1)
        match = True

        for tc in RUNNING_TEST_CASE.values():
            if tc.state != state:
                if break_state and tc.state in break_state:
                    raise SynchError

                match = False
                continue

        if match:
            return


def run_test_case_thread_entry_wrapper(func):
    def wrapper(*args):
        exeptions = args[2]
        try:
            func(*args)
        except Exception as exc:
            logging.exception(exc)
            exeptions.put(exc)

    return wrapper


@run_test_case_thread_entry_wrapper
def run_test_case_thread_entry(pts, test_case, exceptions):
    """Runs the test case specified by a TestCase instance.

    [1] xmlrpclib.Fault normally happens due to unhandled exception in the
        autoptsserver on Windows

    """
    log("Starting TestCase %s %s", run_test_case_thread_entry.__name__,
        test_case)

    if AUTO_PTS_LOCAL:  # set fake status and return
        statuses = ["PASS", "INCONC", "FAIL", "UNKNOWN VERDICT: NONE",
                    "BTP ERROR", "XML-RPC ERROR", "BTP TIMEOUT"]
        test_case.status = random.choice(statuses)
        return

    error_code = None

    try:
        RUNNING_TEST_CASE[test_case.name] = test_case
        test_case.state = "PRE_RUN"
        test_case.pre_run()
        test_case.status = "RUNNING"
        test_case.state = "RUNNING"
        pts.callback_thread.set_current_test_case(test_case.name)
        synchronize_instances(test_case.state)
        error_code = pts.run_test_case(test_case.project_name, test_case.name)

        log("After run_test_case error_code=%r status=%r",
            error_code, test_case.status)

        # raise exception discovered by thread
        thread_error = pts.callback_thread.error_code()
        pts.callback_thread.cleanup()

        if thread_error:
            error_code = thread_error

    except Exception as error:
        logging.exception(error)
        error_code = get_error_code(error)

    except BaseException as ex:
        logging.exception(ex)
        error_code = get_error_code(None)

    finally:
        try:
            if error_code == ptstypes.E_XML_RPC_ERROR:
                pts.recover_pts()
        except Exception as error:
            logging.exception(error)
            exceptions.put(error)
        test_case.state = "FINISHING"
        synchronize_instances(test_case.state)
        test_case.post_run(error_code)  # stop qemu and other commands
        del RUNNING_TEST_CASE[test_case.name]

    log("Done TestCase %s %s", run_test_case_thread_entry.__name__,
        test_case)


def run_test_case_thread_fun(results, ptses, test_case_instances, test_case_name, stats,
                             session_log_dir, exceptions):
    status, duration = run_test_case(ptses, test_case_instances, test_case_name, stats,
                                     session_log_dir, exceptions)
    results.append(status)
    results.append(duration)


@run_test_case_wrapper
def run_test_case(ptses, test_case_instances, test_case_name, stats,
                  session_log_dir, exceptions):
    def test_case_lookup_name(name, test_case_class):
        """Return 'test_case_class' instance if found or None otherwise"""
        if test_case_instances is None:
            return None

        for tc in test_case_instances:
            if tc.name == name and isinstance(tc, test_case_class):
                return tc

        return None

    logger = logging.getLogger()

    format_template = ("%(asctime)s %(name)s %(levelname)s %(filename)-25s "
                       "%(lineno)-5s %(funcName)-25s : %(message)s")
    formatter = logging.Formatter(format_template)

    # Lookup TestCase class instance
    test_case_lt1 = test_case_lookup_name(test_case_name, TestCaseLT1)
    if test_case_lt1 is None:
        # FIXME
        return 'NOT_IMPLEMENTED'

    test_case_lt1.reset()
    test_case_lt1.initialize_logging(session_log_dir)
    file_handler = logging.FileHandler(test_case_lt1.log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if test_case_lt1.name_lt2:
        if len(ptses) < 2:
            return 'LT2_NOT_AVAILABLE'

        test_case_lt2 = test_case_lookup_name(test_case_lt1.name_lt2,
                                              TestCaseLT2)
        if test_case_lt2 is None:
            # FIXME
            return 'NOT_IMPLEMENTED'
    else:
        test_case_lt2 = None

    while True:
        # Multiple PTS instances test cases may fill status already
        if test_case_lt1.status != 'init':
            continue

        # Multi-instance related stuff
        pts_threads = []

        pts_thread = threading.Thread(
            target=run_test_case_thread_entry,
            args=(ptses[0], test_case_lt1, exceptions))
        pts_threads.append(pts_thread)
        pts_thread.start()

        if test_case_lt2:
            pts_thread = threading.Thread(
                target=run_test_case_thread_entry,
                args=(ptses[1], test_case_lt2, exceptions))
            pts_threads.append(pts_thread)
            pts_thread.start()

        # Wait till every PTS instance finish executing test case
        for pts_thread in pts_threads:
            pts_thread.join()

        logger.removeHandler(file_handler)

        if test_case_lt2 and test_case_lt2.status != "PASS" \
                and test_case_lt1.status == "PASS":
            return test_case_lt2.status

        return test_case_lt1.status


test_case_blacklist = [
    "_HELPER",
    "-LT2",
    "TWO_NODES_PROVISIONER",
]


def run_test_cases(ptses, test_case_instances, args):
    """Runs a list of test cases"""

    def run_or_not(test_case_name):
        for entry in test_case_blacklist:
            if entry in test_case_name:
                return False

        if args.excluded:
            for n in args.excluded:
                if test_case_name.startswith(n):
                    return False

        if args.test_cases:
            for n in args.test_cases:
                if test_case_name.startswith(n):
                    return True

            return False

        return True

    ports_str = '_'.join(str(x) for x in args.cli_port)
    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    session_log_dir = 'logs/cli_port_' + ports_str + '/' + now
    try:
        os.makedirs(session_log_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    test_cases = []

    projects = ptses[0].get_project_list()

    for project in projects:
        _test_case_list = ptses[0].get_test_case_list(project)
        test_cases += [tc for tc in _test_case_list if run_or_not(tc)]

    # Statistics
    stats = TestCaseRunStats(projects, test_cases, args.retry, TEST_CASE_DB)

    exceptions = queue.Queue()

    for test_case in test_cases:
        stats.run_count = 0

        while True:
            timeout = False

            if args.superguard:
                results = []
                guarded_thread = InterruptableThread(target=run_test_case_thread_fun,
                                                     args=(results, ptses,
                                                           test_case_instances,
                                                           test_case, stats,
                                                           session_log_dir,
                                                           exceptions), daemon=True)

                guarded_thread.start()
                guarded_thread.join(timeout=args.superguard)

                if guarded_thread.is_alive():
                    exceptions.put(Exception('Superguard timeout'))
                    guarded_thread.interrupt()
                    status = 'SUPERGUARD TIMEOUT'
                    duration = args.superguard
                    timeout = True
                else:
                    status = results[0]
                    duration = results[1]
            else:
                status, duration = run_test_case(ptses, test_case_instances,
                                                 test_case, stats,
                                                 session_log_dir, exceptions)

            exeption_msg = ''
            while not exceptions.empty():
                try:
                    exeption_msg += str(exceptions.get_nowait()) + '\n'
                except BaseException as e:
                    logging.exception(e)
                    traceback.print_exc()
                finally:
                    print(exeption_msg)

            if timeout or args.recovery and \
                    (exeption_msg != '' or status not in {'PASS', 'INCONC', 'FAIL'}):
                run_recovery(args, ptses)

            if (status == 'PASS' and not args.stress_test) or stats.run_count == args.retry:
                if TEST_CASE_DB:
                    TEST_CASE_DB.update_statistics(test_case, duration, status)

                break

            stats.run_count += 1

        stats.index += 1

    stats.print_summary()

    return stats.get_status_count(), stats.get_results(), stats.get_regressions()


class CliParser(argparse.ArgumentParser):
    def __init__(self, description, board_names=None):
        argparse.ArgumentParser.__init__(self, description=description)

        self.add_argument("-i", "--ip_addr", nargs="+",
                          help="IP address of the PTS automation servers")

        self.add_argument("-l", "--local_addr", nargs="+", default=None,
                          help="Local IP address of PTS automation client")

        self.add_argument("workspace",
                          help="Path to PTS workspace file to use for "
                               "testing. It should have pqw6 extension. "
                               "The file should be located on the "
                               "machine, where automation server is running.")

        self.add_argument("kernel_image", nargs='?', default=None,
                          help="OS kernel image to be used for testing,"
                               "e.g. elf file for qemu, exe for native.")

        self.add_argument("-a", "--bd-addr",
                          help="Bluetooth device address of the IUT")

        self.add_argument("-d", "--debug-logs", dest="enable_max_logs",
                          action='store_true', default=False,
                          help="Enable the PTS maximum logging. Equivalent "
                               "to running test case in PTS GUI using "
                               "'Run (Debug Logs)'")

        self.add_argument("-c", "--test-cases", nargs='+', default=[],
                          help="Names of test cases to run. Groups of "
                               "test cases can be specified by profile names")

        self.add_argument("-e", "--excluded", nargs='+', default=[],
                          help="Names of test cases to exclude. Groups of "
                               "test cases can be specified by profile names")

        self.add_argument("-r", "--retry", type=int, default=0,
                          help="Repeat test if failed. Parameter specifies "
                               "maximum repeat count per test")

        self.add_argument("--stress_test", action='store_true', default=False,
                          help="Repeat every test even if previous result was PASS")

        self.add_argument("-S", "--srv_port", type=int, nargs="+", default=[SERVER_PORT],
                          help="Specify the server port number")

        self.add_argument("-C", "--cli_port", type=int, nargs="+", default=[CLIENT_PORT],
                          help="Specify the client port number")

        self.add_argument("--recovery", action='store_true', default=False,
                          help="Specify if autoptsserver should try to recover"
                               " itself after exception.")

        self.add_argument("--superguard", default=0, metavar='MINUTES', type=float,
                          help="Specify amount of time in minutes, after which"
                               " super guard will blindly trigger recovery steps.")

        self.add_argument("--ykush", metavar='YKUSH_PORT', help="Specify "
                                                                "ykush downstream port number, so on BTP TIMEOUT "
                                                                "the iut device could be powered off and on.")

        # Hidden option to select qemu bin file
        self.add_argument("--qemu_bin", help=argparse.SUPPRESS, default=None)

        # Hidden option to save test cases data in TestCase.db
        self.add_argument("-s", "--store", action="store_true",
                          default=False, help=argparse.SUPPRESS)

        self.add_argument("--hci", type=int, default=None, help="Specify the number of the"
                                                                " HCI controller(currently only used "
                                                                "under native posix)")

        if board_names:
            self.add_argument("-t", "--tty-file",
                              help="If TTY is specified, BTP communication "
                                   "with OS running on hardware will be done over "
                                   "this TTY. Hence, QEMU will not be used.")

            self.add_argument("-b", "--board",
                              help="Used DUT board. This option is used to "
                                   "select DUT reset command that is run before "
                                   "each test case. If board is not specified DUT "
                                   "will not be reset. Supported boards: %s. " %
                                   (", ".join(board_names, ),), choices=board_names)

            self.add_argument("--rtt2pty",
                              help="Use RTT2PTY to capture logs from device."
                                   "Requires rtt2pty tool and rtt support on IUT.",
                              action='store_true', default=False)
        else:
            self.add_argument("btpclient_path",
                              help="Path to tool btpclient.")


class Client:
    """AutoPTS Client abstract class.

       Contains common client steps.

    """

    def __init__(self, get_iut, project):
        self.test_cases = None
        self.get_iut = get_iut
        self.store_tag = project + '_'
        setup_project_name(project)

    def start(self):
        """Start main with exception handling."""
        while True:
            try:
                self.main()
                break

            # os._exit: not the cleanest but the easiest way to exit the server thread
            except KeyboardInterrupt:  # Ctrl-C
                sys.exit(14)

            # SystemExit is thrown in arg_parser.parse_args and in sys.exit
            except SystemExit:
                raise  # let the default handlers do the work

            except Exception as exc:
                traceback.print_exc()
                try:
                    # FIXME: why would a generic Exception have ptses as args?
                    ptses = exc.args[1]
                    for pts in ptses:
                        recover_autoptsserver(pts)
                    time.sleep(20)
                except BaseException as e:
                    logging.exception(e)
                    traceback.print_exc()

            except BaseException as e:
                logging.exception(e)
                sys.exit(16)

    def main(self):
        """Main."""

        # Workaround for logging error: "UnicodeEncodeError: 'charmap' codec can't
        # encode character '\xe6' in position 138: character maps to <undefined>",
        # which occurs under Windows with default encoding other than cp1252
        # each time log() is called.
        _locale._getdefaultlocale = (lambda *arg: ['en_US', 'utf8'])

        args = self.parse_args()

        # root privileges only needed for native mode.
        if args.hci is not None:
            if not have_admin_rights():
                sys.exit("Please run this program as root.")
        elif have_admin_rights():
            sys.exit("Please do not run this program as root.")

        if args.store:
            tc_db_table_name = self.store_tag + str(args.board)
        else:
            tc_db_table_name = None

        ptses = init_pts(args, tc_db_table_name)

        btp.init(self.get_iut)
        self.init_iutctl(args)

        stack.init_stack()
        stack_inst = stack.get_stack()
        stack_inst.synch_init([pts.callback_thread for pts in ptses])

        self.setup_project_pixits(ptses)
        self.setup_test_cases(ptses)

        run_test_cases(ptses, self.test_cases, args)

        self.cleanup()

        print("\nBye!")
        sys.stdout.flush()

        for pts in ptses:
            pts.unregister_xmlrpc_ptscallback()

        # not the cleanest but the easiest way to exit the server thread
        sys.exit(0)

    def parse_args(self):
        """Parses command line arguments and options"""

        arg_parser = CliParser("PTS automation client")
        args = arg_parser.parse_args()

        self.check_args(args)

        return args

    def check_args(self, args):
        """Sanity check command line arguments"""

        qemu_bin = args.qemu_bin

        if not args.ip_addr:
            args.ip_addr = ['127.0.0.1'] * len(args.srv_port)

        if not args.local_addr:
            args.local_addr = ['127.0.0.1'] * len(args.cli_port)

        if args.ykush:
            board_power(args.ykush, True)
            time.sleep(1)

        if 'tty_file' in args and args.tty_file:
            tty_file = args.tty_file

            if tty_file.startswith("COM"):
                if not os.path.exists(tty_file):
                    sys.exit("%s COM file does not exist!" % repr(tty_file))
                args.tty_file = "/dev/ttyS" + str(int(tty_file["COM".__len__():]) - 1)
            elif (not tty_file.startswith("/dev/tty") and
                  not tty_file.startswith("/dev/pts")):
                sys.exit("%s is not a TTY nor COM file!" % repr(tty_file))
            elif not os.path.exists(tty_file):
                sys.exit("%s TTY file does not exist!" % repr(tty_file))
        elif 'btpclient_path' in args:
            if not os.path.exists(args.btpclient_path):
                sys.exit("Path %s of btpclient.py file does not exist!" % repr(args.btpclient_path))
        elif qemu_bin:
            if not find_executable(qemu_bin):
                sys.exit("%s is needed but not found!" % (qemu_bin,))

            if args.kernel_image is None or not os.path.isfile(args.kernel_image):
                sys.exit("kernel_image %s is not a file!" % repr(args.kernel_image))
        else:
            if args.hci is None:
                sys.exit("No TTY, HCI, COM, QEMU_BIN or btpclient.py path has been specified!")

            if args.kernel_image is None or not os.path.isfile(args.kernel_image):
                sys.exit("kernel_image %s is not a file!" % repr(args.kernel_image))

        args.superguard = 60 * args.superguard

    # Overwrite those
    def init_iutctl(self, args):
        sys.exit("Client.init_iutctl not implemented")

    def setup_project_pixits(self, ptses):
        setup_project_pixits(ptses)

    def setup_test_cases(self, ptses):
        self.test_cases = setup_test_cases(ptses)

    def cleanup(self):
        sys.exit("Client.cleanup not implemented")


def run_recovery(args, ptses):
    # It is hard to say, when we should restart PTS or board.
    # Some wrong result statuses are not accompanied by exceptions,
    # e.g. when test finished with RUNNING status.
    ykush = args.ykush
    if ykush:
        board_power(ykush, False)

    time.sleep(20)  # Server could already restart by itself,
    try:
        for pts in ptses:
            recover_autoptsserver(pts)  # but restart it anyway
    except BaseException as e:
        logging.exception(e)
        traceback.print_exc()

    if ykush:
        board_power(ykush, True)
    time.sleep(20)  # Give server some time to restart

    try:
        reinit_pts(ptses, args)
    except BaseException as e:
        logging.exception(e)
        traceback.print_exc()

    setup_project_pixits(ptses)


def setup_project_name(project):
    global autoprojects
    autoprojects = importlib.import_module('ptsprojects.' + project)


def setup_project_pixits(ptses):
    for profile in profiles:
        mod = getattr(autoprojects, profile, None)
        if mod is not None:
            mod.set_pixits(ptses)


def setup_test_cases(ptses):
    test_cases = []

    for profile in profiles:
        mod = getattr(autoprojects, profile, None)
        if mod is not None:
            test_cases += mod.test_cases(ptses)

    return test_cases


def recover_autoptsserver(server):
    if server:
        print('Attempting to recover autoptsserver')
        log('Attempting to recover autoptsserver')
        server.request_recovery()
        return 0
    return 1


def board_power(ykush_port, on=True):
    ykushcmd = 'ykushcmd'
    if sys.platform == "win32":
        ykushcmd += '.exe'

    if on:
        subprocess.Popen([ykushcmd, '-u', str(ykush_port)])
    else:
        subprocess.Popen([ykushcmd, '-d', str(ykush_port)])
