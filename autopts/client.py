#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2024, Codecoup.
# Copyright (c) 2025, Atmosic.
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
import copy
import datetime
import errno
import json
import logging
import os
import queue
import random
import shutil
import signal
import socket
import sys
import threading
import time
import traceback
import xml.etree.ElementTree as ElementTree
import xmlrpc.client
from os.path import dirname
from xmlrpc.server import SimpleXMLRPCServer

from termcolor import colored

from autopts.config import FILE_PATHS
from autopts.ptsprojects import ptstypes, stack
from autopts.ptsprojects.boards import get_available_boards, tty_to_com
from autopts.ptsprojects.ptstypes import E_FATAL_ERROR
from autopts.ptsprojects.testcase import PTSCallback, TestCaseLT1, TestCaseLT2, TestCaseLT3
from autopts.ptsprojects.testcase_db import TestCaseTable
from autopts.pybtp import btp
from autopts.pybtp.types import BTPError, BTPInitError, MissingWIDError, SynchError
from autopts.utils import (
    CounterWithFlag,
    InterruptableThread,
    ResultWithFlag,
    RunEnd,
    active_hub_server_replug_usb,
    extract_wid_testcases_to_csv,
    get_global_end,
    have_admin_rights,
    raise_on_global_end,
    set_global_end,
    ykush_replug_usb,
)
from cliparser import CliParser

log = logging.debug
log_lock = threading.RLock()

RUNNING_TEST_CASE = {}
autoprojects = None
TEST_CASE_TIMEOUT_MS = 300000  # milliseconds

# To test autopts client locally:
# Envrinment variable AUTO_PTS_LOCAL must be set for FakeProxy to
# be used. When FakeProxy is used autoptsserver on Windows will
# not be contacted.
AUTO_PTS_LOCAL = "AUTO_PTS_LOCAL" in os.environ


def logger_log(self, *args, **kwargs):
    with log_lock:
        self.original_log(*args, **kwargs)


class PtsServerProxy(xmlrpc.client.ServerProxy):
    """Client to remote autoptsserver"""
    def __init__(self, server_address, server_port):
        super().__init__(uri=f"http://{server_address}:{server_port}/",
                         allow_none=True, transport=None,
                         encoding=None, verbose=False,
                         use_datetime=False, use_builtin_types=False,
                         headers=(), context=None)
        self.info = f"{server_address}:{server_port}"
        self.callback_thread = None
        self.callback = None

    @staticmethod
    def factory_get_instance(_id, server_address, server_port,
                             client_address, client_port, timeout):
        proxy = proxy = PtsServerProxy(server_address, server_port)
        result = ResultWithFlag(False)
        print(f"{id(proxy)} Starting PTS: {proxy.info} ...")

        def wait_for():
            try:
                proxy.ready()
                result.set(True)
            except BaseException:
                log('autoptsserver not responding, retrying...')
            # Continue waiting
            return True

        result.wait(timeout=timeout, predicate=wait_for)

        log("Server methods: %s", proxy.system.listMethods())
        proxy.callback_thread = ClientCallbackServer(client_port, f'LT{_id}-callback')
        proxy.callback = proxy.callback_thread.callback
        proxy.callback_thread.start()
        proxy.register_client_callback({'xmlrpc_address': client_address, 'xmlrpc_port': client_port})
        log("Client IP Address: %s", client_address)
        print(f"({id(proxy)}) OK")

        return proxy


class FakeProxy:
    """Fake PTS XML-RPC proxy client.

    Usefull when testing code locally and auto-pts server is not needed"""

    def __init__(self):
        self.info = "mock"

    def __getattr__(self, item):
        return '_generic'

    def _generic(self, *args, **kwargs):
        return True

    def get_version(self):
        return 0x65

    def bd_addr(self):
        return "00:01:02:03:04:05"


if sys.platform == "win32":
    from autoptsserver import Server
else:
    # Client is running under Linux and will not
    # be able to import some Windows-only modules
    Server = FakeProxy


class PtsServer(Server):
    """Builtin instance of autoptsserver for one process mode"""

    # Counter of closed autoptsservers
    finish_count = CounterWithFlag(init_count=0)

    def __init__(self, _args=None):
        super().__init__(PtsServer.finish_count, _args=_args)
        self.info = f'builtin {_args.srv_port}'

    @staticmethod
    def factory_get_instance(args, timeout):
        proxy = PtsServer(args)
        proxy.start()

        result = ResultWithFlag(False)

        def wait_for():
            if proxy.ready():
                result.set(True)
                return False
            # Continue waiting
            return True

        try:
            result.wait(timeout=timeout, predicate=wait_for)
            if not result.get_nowait():
                raise Exception('Failed to start autoptsserver')
        except BaseException:
            proxy.terminate()
            raise

        proxy.callback = ClientCallback()
        proxy.register_client_callback({'client_callback': proxy.callback})

        return proxy


class ClientCallback(PTSCallback):
    def __init__(self):
        super().__init__()
        self.exception = queue.Queue()
        self._results = {}
        self._callbacks = {}
        # Long methods run asynchronously
        for method in ['start_pts', 'restart_pts', 'recover_pts', 'run_test_case']:
            self._results[method] = ResultWithFlag()
            self._callbacks[method] = None

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

        logger = logging.getLogger(f"{self.__class__.__name__}.{self.log.__name__}")
        logger.info("%s %s %s %s %s", ptstypes.PTS_LOGTYPE_STRING[log_type],
                    logtype_string, log_time, test_case_name,
                    log_message)

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

        logger = logging.getLogger(f"{self.__class__.__name__}.{self.on_implicit_send.__name__}")

        logger.info(f"""
    {"*" * 20}
    BEGIN OnImplicitSend:
    project_name: {project_name}
    wid: {wid}
    test_case_name: {test_case_name}
    description: {description}
    style: {ptstypes.MMI_STYLE_STRING[style]} 0x{style:x}""")

        try:
            # XXX: 361 WID MESH sends tc name with leading white spaces
            test_case_name = test_case_name.lstrip()

            logger.info("Calling test cases on_implicit_send")

            RUNNING_TEST_CASE[test_case_name].on_implicit_send(project_name, wid, test_case_name,
                                                               description, style)

            # Make the PTS wait for response without blocking xmlrpc server
            testcase_response = "WAIT"

        except Exception as e:
            testcase_response = "Cancel"
            logging.exception("OnImplicitSend caught exception %s", e)
            self.exception.put(sys.exc_info()[1])

        logger.info(f"""
    on_implicit_send returned response: {testcase_response}
    END OnImplicitSend
    {'*' * 20}""")

        return testcase_response

    def set_result(self, method_name, result):
        """
        Result of a ptscontrol method that was called asynchronously
        and has to be awaited.
        """
        log(f"{self.__class__.__name__}, {self.set_result.__name__},"
            f" {method_name}, {result}")

        method_result = self._results[method_name]
        callback = self._callbacks[method_name]

        method_result.set(result)
        if callable(callback):
            callback(result)

    def get_result(self, method_name, timeout=None, predicate=None):
        """
        Result of a ptscontrol method that was called asynchronously
        and has to be awaited.
        """
        log(f"{self.__class__.__name__}.{self.get_result.__name__} {method_name}")

        method_result = self._results[method_name]
        result = method_result.get(timeout=timeout, predicate=predicate)
        method_result.clear()

        return result

    def cleanup(self):
        while not self.exception.empty():
            self.exception.get_nowait()
            self.exception.task_done()

        # Reinit everything in case a KeyboardInterrupt exception triggered
        # by a superguard timeout breaks the lock states.
        self.exception = queue.Queue()

        for key in self._results:
            self._results[key] = ResultWithFlag()


class ClientCallbackServer(threading.Thread):
    """Thread for XML-RPC callback server

    To prevent SimpleXMLRPCServer blocking whole app it is started in a thread

    """

    def __init__(self, port, name):
        log("%s.%s port=%r", self.__class__.__name__, self.__init__.__name__, port)
        super().__init__()
        self.name = name
        self.server = None
        self.callback = ClientCallback()
        self.port = port
        self.current_test_case = None
        self.end = False

    def safe_handle_request(self):
        """Calls handle_request and logs exceptions."""
        try:
            self.server.handle_request()
        except Exception as e:
            logging.exception(e)

    def run(self):
        """Starts the xmlrpc callback server"""
        log("%s.%s", self.__class__.__name__, self.run.__name__)
        log("Client callback serving on port %s ...", self.port)

        self.server = SimpleXMLRPCServer(("", self.port),
                                         allow_none=True, logRequests=False)
        self.server.register_instance(self.callback)
        self.server.register_introspection_functions()
        self.server.timeout = 1.0

        try:
            while not self.end and not get_global_end():
                self.safe_handle_request()
        except BaseException as e2:
            logging.exception(e2)
        finally:
            log("Client callback finishing...")
            self.server.server_close()

    def stop(self):
        log("%s.%s", self.__class__.__name__, self.stop.__name__)
        self.end = True


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


def get_test_data_path(pts):
    autopts_dir = pts.get_path()
    return autopts_dir + "\\autopts\\test_data\\"


get_my_ip_address.cached_address = None


def init_logging(tag="", log_filename=None):
    """Initialize logging"""
    root_logger = logging.getLogger('root')

    # Monkey-patch this to make use of logger lock
    if not hasattr(logging.Logger, 'original_log'):
        logging.Logger.original_log = logging.Logger._log
        logging.Logger._log = logger_log

    if root_logger.handlers:
        # Already inited
        return

    if log_filename:
        os.makedirs(dirname(log_filename), exist_ok=True)
    else:
        script_name = os.path.basename(sys.argv[0])  # in case it is full path
        script_name_no_ext = os.path.splitext(script_name)[0]
        log_filename = f"{script_name_no_ext}{tag}.log"

    format_template = ("%(asctime)s %(threadName)s %(name)s %(levelname)s %(filename)-25s "
                       "%(lineno)-5s %(funcName)-25s : %(message)s")

    logging.basicConfig(format=format_template,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG,
                        force=True)


def init_pts_thread_entry_wrapper(func):
    def wrapper(*args):
        exceptions = args[2]
        counter = args[3]
        try:
            func(*args)
        except Exception as exc:
            logging.exception(exc)
            exceptions.put(exc)
        finally:
            counter.add(1)

    return wrapper


@init_pts_thread_entry_wrapper
def init_pts_thread_entry(proxy, args, exceptions, finish_count):
    """PTS instance initialization thread function entry"""

    sys.stdout.flush()
    proxy.cleanup_caches()
    err = proxy.restart_pts()
    if err != "WAIT":
        raise Exception("Failed to restart PTS!")

    err = proxy.callback.get_result('restart_pts', timeout=args.max_server_restart_time)
    if not err:
        raise Exception(f"Failed to restart PTS, err {err}")

    proxy.set_call_timeout(TEST_CASE_TIMEOUT_MS)  # milliseconds

    log("PTS Version: %s", proxy.get_version())

    # cache locally for quick access (avoid contacting server)
    proxy.q_bd_addr = proxy.bd_addr()
    log("PTS BD_ADDR: %s", proxy.q_bd_addr)

    log("Opening workspace: %s", args.workspace)
    log("Copy workspace: %s", args.copy)
    proxy.open_workspace(args.workspace, args.copy)

    if args.bd_addr:
        projects = proxy.get_project_list()
        for project_name in projects:
            log("Set bd_addr PIXIT: %s for project: %s", args.bd_addr, project_name)
            proxy.update_pixit_param(project_name, "TSPX_bd_addr_iut", args.bd_addr)

    proxy.enable_maximum_logging(args.enable_max_logs)


def init_pts(args, ptses):
    """Initialization procedure for PTS instances"""

    proxy_list = ptses
    thread_list = []
    exceptions = queue.Queue()
    thread_count = len(args.cli_port)
    finish_count = CounterWithFlag(init_count=0)

    server_count = getattr(args, 'server_count', len(args.cli_port))

    # PtsServer.finish_count.clear()
    for i in range(0, server_count):
        if i < len(proxy_list):
            proxy = proxy_list[i]
        else:
            if AUTO_PTS_LOCAL:
                proxy = FakeProxy()
            elif getattr(args, 'server_args', False):
                proxy = PtsServer.factory_get_instance(args.server_args[i], args.max_server_restart_time)
            else:
                proxy = PtsServerProxy.factory_get_instance(
                    i + 1, args.ip_addr[i], args.srv_port[i],
                    args.local_addr[i], args.cli_port[i],
                    args.max_server_restart_time)
            proxy_list.append(proxy)

        thread = InterruptableThread(target=init_pts_thread_entry,
                                     name=f'LT{i + 1}-server-init',
                                     args=(proxy, args, exceptions, finish_count))
        thread_list.append(thread)
        thread.start()

    # Wait until each PTS instance is initialized.
    try:
        finish_count.wait_for(thread_count, timeout=max(
            180.0, server_count * args.max_server_restart_time))
    except Exception as e:
        logging.exception(e)
        raise
    finally:
        for _i, thread in enumerate(thread_list):
            if thread.is_alive():
                thread.interrupt()
                log(f"({id(proxy_list[i])}) init failed")

    exeption_msg = ''
    for _ in range(exceptions.qsize()):
        exeption_msg += str(exceptions.get_nowait()) + '\n'

    if exeption_msg:
        raise Exception(exeption_msg)

    return proxy_list


def get_result_color(status):
    if status == "PASS":
        return "green"
    if status == "FAIL":
        return "red"
    if status in ("INCONC", "INDCSV"):
        return "yellow"
    return "white"


class TestCaseRunStats:
    def __init__(self, projects, test_cases, retry_count, db=None,
                 xml_results_file=None):
        self.pts_ver = ''
        self.platform = ''
        self.system_version = ''
        self.run_count_max = retry_count + 1  # Run test at least once
        self.run_count = 0  # Run count of current test case
        self.num_test_cases = len(test_cases)
        self.num_test_cases_width = len(str(self.num_test_cases))
        self.max_project_name = len(max(projects, key=len)) if projects else 0
        self.max_test_case_name = len(max(test_cases, key=len)) if test_cases else 0
        self.margin = 3
        self.index = 0
        self.xml_results = xml_results_file
        self.db = db
        self.est_duration = 0
        self.pending_config = None
        self.pending_test_case = None
        self.test_run_completed = False
        self.session_log_dir = None
        self.fail_info_cb = None

        if self.xml_results and not os.path.exists(self.xml_results):
            os.makedirs(dirname(self.xml_results), exist_ok=True)
            root = ElementTree.Element("results")
            tree = ElementTree.ElementTree(root)
            tree.write(self.xml_results)

        if self.db:
            self.est_duration = db.estimate_session_duration(test_cases,
                                                             self.run_count_max)

    def save_to_backup(self, filename):
        data_to_save = {key: value
                        for key, value in self.__dict__.items()
                        if isinstance(value, (int, str, bool))}

        with open(filename, 'w') as json_file:
            json.dump(data_to_save, json_file, indent=4)

    @staticmethod
    def load_from_backup(backup_file):
        with open(backup_file) as f:
            data = json.load(f)
            stats = TestCaseRunStats([], [], 0, None)
            stats.__dict__.update(data)
            return stats

    def merge(self, stats2):
        self.num_test_cases = self.num_test_cases + stats2.num_test_cases
        self.num_test_cases_width = max(self.num_test_cases_width, stats2.num_test_cases_width)
        self.max_project_name = max(self.max_project_name, stats2.max_project_name)
        self.max_test_case_name = max(self.max_test_case_name, stats2.max_test_case_name)
        self.est_duration = self.est_duration + stats2.est_duration
        self.pending_config = stats2.pending_config
        self.pending_test_case = stats2.pending_test_case
        self.session_log_dir = stats2.session_log_dir

        stats2_tree = ElementTree.parse(stats2.xml_results)
        root2 = stats2_tree.getroot()

        self_tree = ElementTree.parse(self.xml_results)
        root1 = self_tree.getroot()
        root1.extend(root2)
        self_tree.write(self.xml_results)

    def update(self, test_case_name, duration, status, description='', test_start_time=None, test_end_time=None):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        elem = root.find(f"./test_case[@name='{test_case_name}']")
        if elem is None:
            elem = ElementTree.SubElement(root, 'test_case')
            elem.attrib["new"] = '0'

            status_previous = None
            if self.db:
                status_previous = self.db.get_result(test_case_name)
                if status_previous is None:
                    elem.attrib["new"] = '1'

            elem.attrib["project"] = test_case_name.split('/')[0]
            elem.attrib["name"] = test_case_name
            elem.attrib["duration"] = str(duration)
            elem.attrib["status"] = ""
            elem.attrib["status_previous"] = str(status_previous)
            elem.attrib["description"] = description
            elem.attrib["test_start_time"] = ""
            elem.attrib["test_end_time"] = ""

            run_count = 0
        else:
            run_count = int(elem.attrib["run_count"])

        elem.attrib["status"] = status

        if test_start_time is not None:
            elem.attrib["test_start_time"] = test_start_time.strftime('%Y-%m-%d %H:%M:%S')
        if test_end_time is not None:
            elem.attrib["test_end_time"] = test_end_time.strftime('%Y-%m-%d %H:%M:%S')

        regression = bool(elem.attrib["status"] != "PASS" and elem.attrib["status_previous"] == "PASS")
        progress = bool(elem.attrib["status"] == "PASS" and elem.attrib["status_previous"] != "PASS"
                        and elem.attrib["status_previous"] != "None")

        elem.attrib["regression"] = str(regression)
        elem.attrib["progress"] = str(progress)
        elem.attrib["run_count"] = str(run_count + 1)

        tree.write(self.xml_results)

        return regression, progress

    def update_descriptions(self, descriptions):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        for tc in descriptions.keys():
            elem = root.find(f"./test_case[@name='{tc}']")
            if elem is None:
                continue

            elem.attrib["description"] = descriptions[tc]

        tree.write(self.xml_results)

    def get_descriptions(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        descriptions = {}

        for tc_xml in root.findall("./test_case"):
            descriptions[tc_xml.attrib["name"]] = tc_xml.attrib["description"]

        return descriptions

    def get_wid_usage(self):
        extract_wid_testcases_to_csv()

    def get_results(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()

        results = {}
        for tc_xml in root.findall("./test_case"):
            status = tc_xml.attrib["status"]
            run_count = tc_xml.attrib["run_count"]
            start_time = tc_xml.attrib.get("test_start_time")
            end_time = tc_xml.attrib.get("test_end_time")
            duration = tc_xml.attrib.get("duration")

            patterns = ["UNKNOWN VERDICT"]
            if (self.fail_info_cb):
                patterns.extend(["BTP TIMEOUT", "FAIL", "INDCSV", "INCONC"])
            parsed_result = status
            additional_info = ""

            for pattern in patterns:
                if pattern in status:
                    additional_info = status.replace(pattern, "").strip()
                    parsed_result = pattern
                    break

            if (self.fail_info_cb):
                if parsed_result in patterns:
                    assertion_line = self.fail_info_cb(tc_xml.attrib["name"])
                    if assertion_line:
                        if additional_info:
                            additional_info += " | " + assertion_line
                        else:
                            additional_info = assertion_line

            results[tc_xml.attrib["name"]] = {
                "status": status,
                "run_count": run_count,
                "test_start_time": start_time,
                "test_end_time": end_time,
                "duration": duration,
                "parsed_result": parsed_result,
                "additional_info": additional_info
            }

        return results

    def get_regressions(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()
        tcs_xml = root.findall("./test_case[@regression='True']")

        return [tc_xml.attrib["name"] for tc_xml in tcs_xml]

    def get_progresses(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()
        tcs_xml = root.findall("./test_case[@progress='True']")

        return [tc_xml.attrib["name"] for tc_xml in tcs_xml]

    def get_new_cases(self):
        tree = ElementTree.parse(self.xml_results)
        root = tree.getroot()
        tcs_xml = root.findall("./test_case[@new='1']")

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

    def print_summary(self, detailed=False):
        """Prints test case list status summary"""
        print("\nSummary:\n")
        print(get_formatted_summary(self.get_status_count(),
                                    self.num_test_cases,
                                    len(self.get_regressions()),
                                    len(self.get_progresses())))
        if not detailed:
            return

        print('\nRegressions:')
        print('\n'.join(self.get_regressions()))
        print('\nProgresses:')
        print('\n'.join(self.get_progresses()))
        print('\nNew cases:')
        print('\n'.join(self.get_new_cases()))


def get_formatted_summary(status_count, num_test_cases, regressions_count, progresses_count):
    content = [['Status', 'Count'], '=']
    for status, count in list(status_count.items()):
        content.append([status, str(count)])

    content.append(['='])
    content.append(['Total', str(num_test_cases)])

    if regressions_count != 0:
        content.append(['='])
        content.append(['Regressions', str(regressions_count)])

    if progresses_count != 0:
        if (content[len(content) - 1]) != 1:
            content.append(['='])
        content.append(['Progresses', str(progresses_count)])

    max_len = 0
    for line in content:
        if len(line) == 2:
            max_len = max(max_len, len(' '.join(line)))

    summary = []
    for line in content:
        if len(line) == 1:
            summary.append(f'{line[0] * max_len}')
        elif len(line) == 2:
            spaces = ' ' * (max_len - len(line[0]) - len(line[1]))
            summary.append(f'{line[0]}{spaces}{line[1]}')

    return '\n'.join(summary)


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

        start_dt_test = datetime.datetime.now()
        start_time = time.time()
        status = func(*args)
        duration = time.time() - start_time
        end_dt_test = datetime.datetime.now()

        regression, progress = stats.update(
            test_case_name,
            duration,
            status,
            test_start_time=start_dt_test,
            test_end_time=end_dt_test,
        )

        retries_max = run_count_max - 1
        if run_count:
            retries_msg = f"#{run_count}"
        else:
            retries_msg = ""

        if regression and run_count == retries_max:
            regression_msg = "REGRESSION"
        elif progress:
            regression_msg = "PROGRESS"
        else:
            regression_msg = ""

        end_time_str = str(round(datetime.timedelta(
            seconds=duration).total_seconds(), 3))

        result = (f"{status} ".ljust(15) +
                  end_time_str.rjust(len(end_time_str)) +
                  retries_msg.rjust(len(f"#{retries_max}") + margin) +
                  regression_msg.rjust(len("REGRESSION") + margin))

        if sys.stdout.isatty():
            output_color = get_result_color(status)
            print(colored(result, output_color))
        else:
            print(result)

        sys.stdout.flush()

        return status, duration

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

    elif isinstance(exc, MissingWIDError):
        error_code = ptstypes.E_MISSING_WID_ERROR

    elif isinstance(exc, BTPInitError):
        error_code = ptstypes.E_IUT_INIT_ERROR

    elif error_code is None:
        error_code = ptstypes.E_FATAL_ERROR

    log("%s returning error code %r for exception %r",
        get_error_code.__name__, error_code, exc)

    return error_code


def synchronize_instances(state, break_state=None, end_flag=None):
    """Synchronize instances to be in one state before executing further"""
    match = ResultWithFlag()

    def wait_for():
        if get_global_end():
            return False

        for tc in RUNNING_TEST_CASE.values():
            if tc.state != state:
                if break_state and tc.state in break_state:
                    log(f'SynchError: {tc.name} in an invalid state {tc.state} ')
                    return False

                if end_flag and end_flag.is_set():
                    log(f'SynchError: timeout: {tc.name} in an invalid state {tc.state} ')
                    return False

                return True

        # Instances are in sync
        match.set(True)
        return False

    return match.get(predicate=wait_for)


class LTThread(InterruptableThread):
    def __init__(self, name=None, args=()):
        super().__init__(name=name)
        self._args = args
        self.locked = False

    def run(self):
        exceptions = self._args[2]
        finish_count = self._args[3]
        try:
            self.locked = self.interrupt_lock.acquire()
            self._run_test_case(*self._args)
        except Exception as exc:
            logging.exception(exc)
            exceptions.put(exc)
        finally:
            finish_count.add(1)
            if self.locked:
                self.interrupt_lock.release()

    def cancel_sync_points(self):
        stack_inst = stack.get_stack()
        stack_inst.synch.cancel_synch()

    def interrupt(self):
        self.cancel_sync_points()

        # Acquire the lock to prevent breaking pre- or post-test-case steps,
        # which crucial and do not fail in general.
        while not self.interrupt_lock.acquire(True, timeout=1) and not get_global_end():
            # Ctrl + C friendly loop
            pass

        # Acquire the logger lock to prevent breaking the lock or other
        # logger handles at interrupt.
        while not log_lock.acquire(True, timeout=1) and not get_global_end():
            # Ctrl + C friendly loop
            pass

        try:
            super().interrupt()
        except BaseException as e:
            logging.exception(e)
            traceback.print_exc()
        finally:
            log_lock.release()
            self.interrupt_lock.release()

    def _run_test_case(self, pts, test_case, exceptions, finish_count):
        """Runs the test case specified by a TestCase instance."""
        log("Starting TestCase %s %s", self._run_test_case.__name__,
            test_case)

        if AUTO_PTS_LOCAL:  # set fake status and return
            statuses = ["PASS", "INCONC", "FAIL", "UNKNOWN VERDICT: NONE",
                        "BTP ERROR", "XML-RPC ERROR", "BTP TIMEOUT", "INDCSV"]
            test_case.status = random.choice(statuses)
            return

        error_code = None
        pts.callback.cleanup()

        try:
            pts.callback._callbacks['run_test_case'] = self.set_test_case_result
            RUNNING_TEST_CASE[test_case.name] = test_case
            test_case.state = "PRE_RUN"
            test_case.pre_run()
            test_case.status = "RUNNING"
            test_case.state = "RUNNING"
            self.interrupt_lock.release()
            self.locked = False

            if not synchronize_instances(test_case.state, ["FINISHED"], end_flag=finish_count):
                raise SynchError

            result = pts.run_test_case(test_case.project_name, test_case.name)
            if result != "WAIT":
                raise Exception(f"Failed to start the test case {test_case.name}")

            def wait_if_no_step():
                return test_case.steps_queue.empty()

            try:
                while not finish_count.is_set():
                    # Wait for the test case result
                    if test_case.state == "RUNNING":
                        status = pts.callback.get_result(
                            'run_test_case', predicate=wait_if_no_step)

                        if status:
                            test_case.status = status
                            test_case.state = "FINISHING"
                    elif test_case.steps_queue.empty():
                        error_code = 0
                        break

                    # or perform next step (WID or other)
                    response = test_case.run_next_step()
                    if response is None:
                        continue

                    pts.set_wid_response(response)

            except BaseException as test_case_error:
                try:
                    self.locked = self.interrupt_lock.acquire(blocking=False)
                except KeyboardInterrupt:
                    # In case KeyboardInterrupt was injected, we deliberately ignore it here
                    pass
                except Exception as e:
                    log(f"Unexpected error while acquiring interrupt lock: {e}")

                if isinstance(test_case_error, threading.BrokenBarrierError):
                    log(f'SYNCH: Cancelled waiting at a barrier, tc {test_case.name}')
                else:
                    logging.exception(test_case_error)

                error_code = get_error_code(test_case_error)
                exceptions.put(test_case_error)
                pts.set_wid_response("Cancel")
                pts.stop_test_case(test_case.project_name, test_case.name)

            finally:
                if not self.locked:
                    self.locked = self.interrupt_lock.acquire(blocking=False)

            if finish_count.is_set():
                test_case.state = E_FATAL_ERROR
                log('Test case stopped externally')

            log("After run_test_case error_code=%r status=%r",
                error_code, test_case.status)

            # raise exception discovered by thread
            thread_error = pts.callback.error_code()
            pts.callback.cleanup()

            if thread_error:
                error_code = thread_error

        except Exception as error:
            logging.exception(error)
            error_code = get_error_code(error)

        except BaseException as ex:
            logging.exception(ex)
            error_code = get_error_code(None)

        finally:
            test_case.state = "FINISHED"

            if test_case.status != "PASS":
                finish_count.set_flag()
                self.cancel_sync_points()
            else:
                synchronize_instances(test_case.state, end_flag=finish_count)

            test_case.post_run(error_code)  # stop qemu and other commands
            del RUNNING_TEST_CASE[test_case.name]

            log("Done TestCase %s %s", self._run_test_case.__name__, test_case)

    def set_test_case_result(self, status):
        if status != 'PASS':
            # No point in waiting longer at the thread barrier
            self.cancel_sync_points()


@run_test_case_wrapper
def run_test_case(ptses, test_case_instances, test_case_name, stats,
                  session_log_dir, exceptions, timeout):
    def test_case_lookup_name(name, test_case_class):
        """Return 'test_case_class' instance if found or None otherwise"""
        if test_case_instances is None:
            return None

        for tc in test_case_instances:
            if tc.name == name and isinstance(tc, test_case_class):
                return tc

        return None

    logger = logging.getLogger()

    format_template = ("%(asctime)s %(threadName)s %(name)s %(levelname)s %(filename)-25s "
                       "%(lineno)-5s %(funcName)-25s : %(message)s")
    formatter = logging.Formatter(format_template)

    # Lookup TestCase class instances
    test_case_lts = []
    tc_name = test_case_name

    for i, tc_class in enumerate([TestCaseLT1, TestCaseLT2, TestCaseLT3], 2):
        test_case_lt = test_case_lookup_name(tc_name, tc_class)
        if test_case_lt is None:
            log(f'The {tc_name} test case enabled in workspace, but the profile not implemented!')
            return 'NOT_IMPLEMENTED'

        test_case_lt.reset()
        test_case_lts.append(test_case_lt)

        tc_name = getattr(test_case_lts[0], f'name_lt{i}', None)
        if tc_name is None:
            break

        if len(ptses) < i:
            log(f'Not enough PTS instances configured. At least {i}'
                f'instances are required for this test case!')
            return f'LT{i}_NOT_AVAILABLE'

    test_case_lts[0].initialize_logging(session_log_dir)
    file_handler = logging.FileHandler(test_case_lts[0].log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Multi-instance related stuff
    finish_count = CounterWithFlag(init_count=0)
    thread_count = 0
    thread_list = []

    for thread_count, (test_case_lt, pts) in enumerate(zip(test_case_lts, ptses), 1):
        thread = LTThread(
            name=f'LT{thread_count}-thread',
            args=(pts, test_case_lt, exceptions, finish_count))
        thread_list.append(thread)
        thread.start()

    superguard_timeout = False
    try:
        # Wait until each PTS instance has finished executing its test case
        finish_count.wait_for(thread_count, timeout=timeout)
    except TimeoutError:
        superguard_timeout = True
        log('Superguard timeout')
    except RunEnd:
        log('Test case interrupted with SIGINT')
        raise
    finally:
        finish_count.set_flag()
        for i, thread in enumerate(thread_list):
            if thread.is_alive():
                log(f"Interrupting {test_case_lts[i]} test case of thread {thread.name}")
                thread.interrupt()

        while True:
            alive_threads = []
            for _i, thread in enumerate(thread_list):
                if thread.is_alive():
                    alive_threads.append(thread)

            if len(alive_threads) == 0:
                break

            log(f"Waiting for {alive_threads} to finish ...")
            thread_list = alive_threads
            time.sleep(1)

        if superguard_timeout:
            test_case_lts[0].status = 'SUPERGUARD TIMEOUT'

    logger.removeHandler(file_handler)

    for test_case_lt in test_case_lts:
        if test_case_lt.status != "PASS":
            return test_case_lt.status

    return test_case_lts[0].status


test_case_blacklist = [
    "_HELPER",
    "LT2",
    "LT3",
    "TWO_NODES_PROVISIONER",
]


def run_or_not(test_case_name, test_cases, excluded):
    for entry in test_case_blacklist:
        if entry in test_case_name:
            return False

    if excluded:
        for n in excluded:
            if test_case_name.startswith(n):
                return False

    if test_cases:
        for n in test_cases:
            if test_case_name.startswith(n):
                return True

        return False

    # Empty test_cases means "run them all"
    return True


def get_test_cases(pts, test_cases, excluded):
    """
    param: pts: proxy to initiated pts instance
    param: test_cases: test cases specified with -c option or in iut_config.
                       If empty, all test cases from workspace will be run
                       (Except those specified in "excluded").
    param: excluded: test cases specified with -e option
    """

    projects = pts.get_project_list()

    _test_cases = []

    for project in projects:
        _test_case_list = pts.get_test_case_list(project)
        _test_cases += [tc for tc in _test_case_list if run_or_not(tc, test_cases, excluded)]

    return _test_cases


def run_test_cases(ptses, test_case_instances, args, stats, **kwargs):
    """Runs a list of test cases"""
    session_log_dir = stats.session_log_dir

    if not session_log_dir:
        ports_str = '_'.join(str(x) for x in args.cli_port)
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        logs_folder = kwargs["file_paths"]["IUT_LOGS_DIR"]
        session_log_dir = f'{logs_folder}/cli_port_{ports_str}/{now}'
        stats.session_log_dir = session_log_dir
        try:
            os.makedirs(session_log_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    test_cases = args.test_cases
    retry_config = getattr(args, 'retry_config', None)
    repeat_until_failed = getattr(args, 'repeat_until_fail', False)
    pre_test_case_fn = kwargs.get('pre_test_case_fn', None)
    exceptions = queue.Queue()

    approx = ''
    if stats.est_duration:
        approx = " in approximately: " + str(datetime.timedelta(seconds=stats.est_duration))
    print(f"Number of test cases to run: {stats.num_test_cases}{approx}")

    for test_case in test_cases:
        stats.run_count = 0
        test_retry_count = None

        if retry_config is not None:
            if test_case in retry_config:
                test_retry_count = retry_config[test_case]

        while True:
            if pre_test_case_fn:
                pre_test_case_fn(test_case=test_case, stats=stats, **kwargs)

            status, duration = run_test_case(ptses, test_case_instances,
                                             test_case, stats, session_log_dir,
                                             exceptions, args.superguard)

            raise_on_global_end()

            num_exceptions = exceptions.qsize()
            if num_exceptions:
                exception_messages = [str(exceptions.get_nowait()) for _ in range(num_exceptions)]
                exeption_msg = "\n".join(exception_messages) + "\n"
            else:
                exeption_msg = ""
            log(f'exception_msg: {exeption_msg}')

            if args.recovery and (exeption_msg != '' or status not in args.not_recover):
                run_recovery(args, ptses)

            if test_retry_count is not None:
                retry_limit = test_retry_count
            else:
                retry_limit = args.retry

            if repeat_until_failed and status == 'PASS':
                continue

            if (status in ('PASS', 'MISSING WID ERROR') and not args.stress_test) or \
                    stats.run_count == retry_limit:
                if stats.db:
                    stats.db.update_statistics(test_case, duration, status)

                break

            stats.run_count += 1

        stats.index += 1

    stats.print_summary()

    return stats


class Client:
    """AutoPTS Client abstract class.

       Contains common client steps.

    """

    def __init__(self, get_iut, project, name, parser_class=CliParser):
        """
        param get_iut: function from autoptsprojects.<project>.iutctl
        param project: name of project
        param name: name of stack
        param parser_class: argument parser
        """
        self.test_cases = None
        self.file_paths = FILE_PATHS
        self.get_iut = get_iut
        self.autopts_project_name = name
        self.store_tag = name + '_'
        setup_project_name(project)
        self.boards = get_available_boards(name)
        self.ptses = []
        # Namespace with parsed command line arguments (and bot config)
        self.args = None
        # Command line arguments parser
        self.arg_parser = parser_class(board_names=self.boards)
        self.prev_sigint_handler = None
        self.test_case_database = None

    def parse_config_and_args(self, args_namespace=None):
        if args_namespace is None:
            args_namespace = self.args

        self.args, errmsg = self.arg_parser.parse(args_namespace)

        return errmsg

    def load_test_case_database(self):
        if not self.args.store or self.test_case_database:
            return

        tc_db_table_name = self.store_tag + str(self.args.board_name)

        if os.path.exists(self.args.database_file) and \
                not os.path.exists(self.file_paths['TEST_CASE_DB_FILE']):
            shutil.copy(self.args.database_file, self.file_paths['TEST_CASE_DB_FILE'])

        self.test_case_database = TestCaseTable(tc_db_table_name,
                                                self.file_paths['TEST_CASE_DB_FILE'])

    def start(self, args=None):
        """Start main with exception handling."""

        def sigint_handler(sig, frame):
            """Thread safe SIGINT interrupting"""
            set_global_end()

            if sys.platform != "win32":
                signal.signal(signal.SIGINT, self.prev_sigint_handler)
                threading.Thread(target=signal.raise_signal(signal.SIGINT)).start()

        try:
            self.prev_sigint_handler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, sigint_handler)

            return self.main(args)
        except KeyboardInterrupt:
            # Handling Ctrl-C
            raise
        except SystemExit as e:
            if e.code != 0:
                logging.exception(e)
            # Handling --help
            raise
        except (TimeoutError, BaseException) as e:
            logging.exception(e)
            # We have to propagate an exception from the simple client layer
            # up to the bot layer, so it could handle its own cleanup.
            raise
        finally:
            set_global_end()
            self.cleanup()

    def main(self, _args=None):
        """Main.
        Args:
            _args: namespace of predefined or parsed earlier args
        """
        errmsg = self.parse_config_and_args(_args)
        if errmsg != '':
            sys.exit(errmsg)

        if not self.args.sudo and have_admin_rights():
            sys.exit("root privileges detected. Use --sudo to skip this check.")

        os.makedirs(self.file_paths["TMP_DIR"], exist_ok=True)

        self.load_test_case_database()

        if self.args.test_cases_file:
            tests = [_line for line in self.args.test_cases_file.readlines()
                if (_line := line.strip()) and not _line.startswith("#")]
            self.args.test_cases.extend(tests)

        init_pts(self.args, self.ptses)

        btp.init(self.get_iut)
        self.init_iutctl(self.args)

        stack.init_stack()

        self.setup_project_pixits(self.ptses)
        self.setup_test_cases(self.ptses)

        stats = self.run_test_cases()

        self.cleanup()

        if self.args.store:
            shutil.move(self.file_paths['TEST_CASE_DB_FILE'], self.args.database_file)

        print("\nBye!")
        sys.stdout.flush()

        return stats

    def init_iutctl(self, args):
        autoprojects.iutctl.init(args)

    def setup_project_pixits(self, ptses):
        setup_project_pixits(ptses)

    def setup_test_cases(self, ptses):
        self.test_cases = setup_test_cases(ptses)

    def run_test_cases(self):
        """Runs a list of test cases in simple client mode.

        In bot client mode this method is overwritten to inject multiple
        build-flash-run routines, so multiple reinitialization could
        be skipped. See BotClient class in bot/common.py.
        """
        self.args.test_cases = get_test_cases(self.ptses[0],
                                              self.args.test_cases,
                                              self.args.excluded)

        projects = self.ptses[0].get_project_list()

        if os.path.exists(self.file_paths['TC_STATS_RESULTS_XML_FILE']):
            os.remove(self.file_paths['TC_STATS_RESULTS_XML_FILE'])

        stats = TestCaseRunStats(projects, self.args.test_cases,
                                 self.args.retry, self.test_case_database,
                                 xml_results_file=self.file_paths['TC_STATS_RESULTS_XML_FILE'])

        return run_test_cases(self.ptses, self.test_cases, self.args, stats,
                              file_paths=copy.deepcopy(self.file_paths))

    def cleanup(self):
        log(f'{self.__class__.__name__}.{self.cleanup.__name__}')
        autoprojects.iutctl.cleanup()
        self.shutdown_pts()

    def shutdown_pts(self):
        log(f'{self.__class__.__name__}.{self.shutdown_pts.__name__}')
        for pts in self.ptses:
            try:
                pts.stop_pts()
                pts.cleanup_caches()
                pts.unregister_client_callback()
            except Exception as e:
                logging.exception(e)

            if getattr(pts, 'callback_thread', None):
                pts.callback_thread.stop()

            if isinstance(pts, PtsServer):
                pts.terminate()

        self.ptses.clear()


def recover_at_exception(func):
    """The ultimate recovery of recovery, in case of server
     jammed/crashed, but there is still a chance it will be recovered."""

    def _attempt_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e

    def _recover_at_exception(*args, **kwargs):
        restart_time = args[0].max_server_restart_time

        while not get_global_end():
            result = _attempt_func(*args, **kwargs)
            if not isinstance(result, Exception):
                return result

            logging.exception(result)
            traceback.print_exc()

            if isinstance(result, RunEnd):
                # Stopped with SIGINT
                break

            time.sleep(restart_time)

            if args[0].superguard:
                # Wait longer next time. Hopefully the server
                # superguard will work and trigger the restart.
                restart_time = args[0].superguard

        return None

    return _recover_at_exception


@recover_at_exception
def run_recovery(args, ptses):
    log('Running recovery')

    iut = autoprojects.iutctl.get_iut()
    iut.stop()

    if args.usb_replug_available:
        iut.btattach_stop()
        replug_usb(args)
        iut.btattach_start()

    for pts in ptses:
        req_sent = False
        last_restart_time = None

        while not get_global_end():
            try:
                if not last_restart_time:
                    last_restart_time = pts.get_last_recovery_time()
                    log(f'Last restart time of PTS {pts}: {last_restart_time}')

                if not req_sent:
                    log(f'Recovering PTS {pts} ...')
                    pts.recover_pts()
                    req_sent = True
                    err = pts.callback.get_result('recover_pts', timeout=args.max_server_restart_time)
                    if err:
                        log('PTS recovered')
                        break

                if last_restart_time < pts.get_last_recovery_time():
                    log('PTS recovered')
                    break

            except BaseException as e:
                log(e)

            log('Server is still resetting. Wait a little more.')
            time.sleep(1)

    stack_inst = stack.get_stack()
    stack_inst.cleanup()

    log('Recovery finished')


def replug_usb(args):
    log(f'{replug_usb.__name__}')
    if args.ykush:
        if sys.platform == 'win32':
            device_id = tty_to_com(args.tty_file)
        elif args.tty_alias:
            device_id = args.tty_alias
        else:
            device_id = args.tty_file

        ykush_replug_usb(args.ykush, device_id=device_id, delay=args.ykush_replug_delay)

    elif args.active_hub_server:
        active_hub_server_replug_usb(args.active_hub_server)

    if args.tty_alias:
        while not os.path.islink(args.tty_alias) and not os.path.exists(os.path.realpath(args.tty_alias)):
            raise_on_global_end()
            log(f'Waiting for TTY {args.tty_alias} to appear...\n')
            time.sleep(1)

        args.tty_file = os.path.realpath(args.tty_alias)
        iut = autoprojects.iutctl.get_iut()
        if iut:
            iut.tty_file = args.tty_file
        log(f'TTY {args.tty_alias} mounted as {args.tty_file}\n')


def setup_project_name(project):
    global autoprojects
    autoprojects = project  # importlib.import_module('ptsprojects.' + project)


def _get_profiles(ptses):
    pts_projects = ptses[0].get_project_list()
    profiles = set(map(str.lower, pts_projects))
    return profiles


def setup_project_pixits(ptses):
    for profile in _get_profiles(ptses):
        mod = getattr(autoprojects, profile, None)
        if mod is not None:
            mod.set_pixits(ptses)


def setup_test_cases(ptses):
    test_cases = []

    for profile in _get_profiles(ptses):
        mod = getattr(autoprojects, profile, None)
        if mod is not None:
            test_cases += mod.test_cases(ptses)

    return test_cases
