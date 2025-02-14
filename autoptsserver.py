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

import argparse
import copy
import logging as root_logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback
import xmlrpc.client
import xmlrpc.server

from functools import partial
from os.path import dirname, abspath
from pathlib import Path
from queue import Queue, Empty
from time import sleep

import pythoncom
import wmi

import serial.tools.list_ports

from autopts import ptscontrol
from autopts.config import SERVER_PORT
from autopts.utils import CounterWithFlag, get_global_end, exit_if_admin, ykush_replug_usb, ykush_set_usb_power, \
    print_thread_stack_trace, active_hub_server_replug_usb, active_hub_server_set_usb_power
from autopts.winutils import kill_all_processes

logging = root_logging.getLogger('server')
log = root_logging.debug
log_inited = False
PROJECT_DIR = dirname(abspath(__file__))

def _com_port_exists(port_name):
    """Check if the COM port exists."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device == port_name:
            return True
    return False

def init_logging(_args):
    """Initialize server logging"""
    global logging, log, log_inited
    if log_inited:
        return

    log_inited = True
    logger = root_logging.getLogger('server')
    format_template = '%(asctime)s %(threadName)s %(name)s %(levelname)s : %(message)s'
    formatter = root_logging.Formatter(format_template)
    file_handler = root_logging.FileHandler(_args.log_filename, mode='w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(root_logging.DEBUG)
    logging.propagate = False
    log = logging.debug

    # Init root logger if server is run as a separate process
    root_logger = root_logging.getLogger('root')
    if __name__ == "__main__":
        root_logger.setLevel(root_logging.DEBUG)
        root_logger.addHandler(file_handler)


class PtsClientProxy(xmlrpc.client.ServerProxy):
    """TCP/IP socket for sending callbacks to the auto-pts client.
    Args:
        client_address: IP address of the auto-pts client that started
         its own xmlrpc server to receive callback messages

        client_port: TCP port
    """
    def __init__(self, client_address, client_port):
        super().__init__(uri=f"http://{client_address}:{client_port}/",
                         allow_none=True, transport=None,
                         encoding=None, verbose=False,
                         use_datetime=False, use_builtin_types=False,
                         headers=(), context=None)

        log(f"{self.__init__.__name__}, uri={self.uri}")

        self.client_address = client_address
        self.client_port = client_port


class PyPTSWithCallback(ptscontrol.PyPTS, threading.Thread):
    """A child class that adds support of xmlrpc PTS callbacks to PyPTS"""

    def __init__(self, args, name):
        log(f"{self.__init__.__name__}")
        ptscontrol.PyPTS.__init__(self, args.dongle)
        threading.Thread.__init__(self, target=self._pts_thread_work,
                                  name=name)
        self.args = args
        self.client_callback = None
        self.pts_thread = None
        self.pts_thread_id = None
        self.ptscontrol_request_queue = Queue()
        self.ptscontrol_response_queue = Queue()

    def _update_request_time(self):
        # Overwritten in a derived class
        pass

    def register_client_callback(self, kwargs):
        """Registers client callback. xmlrpc proxy/client calls this method
        to register its callback
        """

        log(f"{self.register_client_callback.__name__}")

        if 'xmlrpc_address' in kwargs:
            # auto-pts client and server as a separate processes
            self.client_callback = PtsClientProxy(kwargs['xmlrpc_address'], kwargs['xmlrpc_port'])
        else:
            # One process mode
            self.client_callback = kwargs['client_callback']

        self.register_ptscallback(self.client_callback)

    def unregister_client_callback(self):
        """Unregisters the client callback"""

        log(f"{self.unregister_client_callback.__name__},"
            f"{self.client_callback}")

        self.unregister_ptscallback()
        self.client_callback = None

    def _replug_dongle(self):
        log(f"{self._replug_dongle.__name__}")

        if self.args.ykush:
            ykush_port = self.args.ykush
            device = self._device
            log(f'Replugging device ({device}) under ykush:{ykush_port} ...')
            if device:
                ykush_replug_usb(self.args.ykush, device_id=device, delay=0, end_flag=self._end)
            else:
                # Cases where ykush was down or the dongle was
                # not enumerated for any other reason.
                ykush_replug_usb(self.args.ykush, device_id=None, delay=3, end_flag=self._end)
            log(f'Done replugging device ({device}) under ykush:{ykush_port}')

        elif self.args.active_hub_server:
            active_hub_server_replug_usb(self.args.active_hub_server)

    def _dispatch(self, method_name, param_tuple):
        """Dispatcher that is used by xmlrpc server"""
        try:
            self._update_request_time()

            if method_name in ['start_pts', 'restart_pts',
                               'recover_pts', 'run_test_case']:
                # Methods that have to be called in the same context
                # as the PTS instance was created, but the pts client
                # callback has been already initialized, so it is better
                # to await them outside the XMLRPC context.
                result = self._dispatch_nonblocking(method_name, *param_tuple)

            elif method_name in ['unregister_client_callback', 'ready',
                                 'stop_test_case', 'set_wid_response']:
                # Short nonblocking calls
                method = getattr(self, method_name)
                result = method(*param_tuple)

            else:
                # Methods that have to be called in the same context
                # as the PTS instance was created, but are short enough
                # to run them in a blocking manner.
                result = self._dispatch_blocking(method_name, *param_tuple)
        except BaseException as e:
            logging.exception(e)
            return "FATAL ERROR"

        if isinstance(result, BaseException):
            logging.exception(result)
            raise result

        return result

    def _dispatch_nonblocking(self, method_name, *args):
        self.ptscontrol_request_queue.put((method_name, False, args))
        return "WAIT"

    def _dispatch_blocking(self, method_name, *args):
        self.ptscontrol_request_queue.put((method_name, True, args))
        result = None
        while not self._end.is_set():
            try:
                result = self.ptscontrol_response_queue.get(block=True, timeout=1)
                self.ptscontrol_response_queue.task_done()
                return result
            except Empty:
                pass

        return result

    def _pts_thread_work(self):
        """Main"""
        # Some ptscontrol methods have to be executed in the same
        # thread context as PTS was inited. Otherwise, PTSSender
        # and PTSLogger are not reachable by PTS, hence the
        # OnImplicitSend will not arrive.
        #
        # Since the RunTestCase() is blocking, other functions like e.g.
        # StopTestCase(), those have to be called outside of this thread.
        try:
            pythoncom.CoInitialize()
            log(f'pythoncom._GetInterfaceCount(): {pythoncom._GetInterfaceCount()}')

            self.pts_thread_id = threading.get_ident()

            print(f"({id(self)}) Starting PTS {self.args.srv_port} ...")
            self.restart_pts()
            print(f"({id(self)}) OK")

            while not self._end.is_set() and not get_global_end():
                self._handle_ptscontrol_request(timeout=1)

            self.stop_pts()
            self.delete_temp_workspace()
            self.unregister_ptscallback()
        except Exception as e:
            logging.exception(e)
        finally:
            pythoncom.CoUninitialize()
            log(f'pythoncom._GetInterfaceCount(): {pythoncom._GetInterfaceCount()}')

        log("_pts_thread_work finished")

    def _handle_ptscontrol_request(self, timeout=None):
        # Wait for request to call a ptscontrol method
        try:
            item = self.ptscontrol_request_queue.get(block=True, timeout=timeout)
            self.ptscontrol_request_queue.task_done()
            method_name, blocking, args = item
        except BaseException:
            return

        timer = None

        # Call ptscontrol method
        try:
            if self.args.superguard:
                timeout = self.args.superguard
                timer = threading.Timer(timeout, self.stop_pts)
                timer.name = f'SuperguardTimer{timer.name}'
                timer.start()

            method = getattr(self, method_name)
            result = method(*args)
        except BaseException as e:
            logging.exception(e)
            result = e

        if timer:
            timer.cancel()

        # Send response with method result to client
        try:
            if blocking:
                log(f'Setting result {result} for blocking method {method_name}')
                self.ptscontrol_response_queue.put(result)
            elif self._callback:
                log(f'Setting result {result} for non-blocking method {method_name}')
                self._callback.set_result(method_name, result)
            else:
                log(f'Dropping PTS result {result}')
        except BaseException as e:
            logging.exception(e)


class SvrArgumentParser(argparse.ArgumentParser):
    def __init__(self, description):
        argparse.ArgumentParser.__init__(self, description=description)

        self.add_argument("-S", "--srv_port", type=int,
                          nargs="+", default=[SERVER_PORT],
                          help="Specify the server port number."
                            " If running with three dongles, this may be on the form:"
                            " \"-S 65000 65002 65004\"")

        self.add_argument("--superguard", default=0, type=float, metavar='MINUTES',
                          help="Specify amount of time in minutes, after which"
                          " super guard will blindly trigger recovery steps.")

        self.add_argument("--ykush", nargs="+", default=[], metavar='YKUSH_PORT',
                          help="Specify ykush hub downstream port number, so "
                          "during recovery steps PTS dongle could be replugged.")

        self.add_argument("--active-hub-server", nargs="+", default=[],
                          help="Specify active hub server e.g. IP:TCP_PORT:USB_PORT, so "
                          "during recovery steps PTS dongle could be replugged.")

        self.add_argument("--dongle", nargs="+", default=None,
                          help='Select the dongle port.'
                               'COMx in case of LE only dongle. '
                               r'For dual-mode dongle the port will have format'
                               r' like "USB:Free:5&A70BC4C&0&8 where"'
                               r'the last part 5&A70BC4C&0&8 can be found in'
                               r'"Device instance path" in device settings, e.g. '
                               r'"USB\VID_0A12&PID_0001\5&A70BC4C&0&8"')

        self.add_argument("--dongle_init_delay", default=0.1, type=float, metavar='SECONDS',
                          help="Specify amount of time in seconds to wait before RunTestCase()"
                               "after dongle reinitialization has been triggered with"
                               "GetPTSBluetoothAddress().")

    @staticmethod
    def check_args(arg):
        """Sanity check command line arguments"""

        tag = '_'.join(str(x) for x in list(arg.srv_port))
        arg.log_filename = f'autoptsserver_{tag}.log'

        for srv_port in arg.srv_port:
            if not 49152 <= srv_port <= 65535:
                sys.exit("Invalid server port number=%s, expected range <49152,65535> " % (srv_port,))

        arg.superguard = 60 * arg.superguard

        if arg.ykush:
            ykush_confs = []
            for ykush_conf in arg.ykush:
                config = {}
                if ':' in ykush_conf:
                    ykush_srn, port = ykush_conf.split(':')
                else:
                    port = ykush_conf
                    ykush_srn = None

                config['ports'] = port
                config['ykush_srn'] = ykush_srn
                ykush_confs.append(config)

            arg.ykush = ykush_confs
            arg.active_hub = True

        elif arg.active_hub_server:
            active_hub_server_configs = []
            for active_hub_server_conf in arg.active_hub_server:
                config = {}
                ip, tcp_port, usb_port = active_hub_server_conf.split(':')

                config['ip'] = ip
                config['tcp_port'] = tcp_port
                config['usb_port'] = usb_port
                config['replug_delay'] = 5
                active_hub_server_configs.append(config)

            arg.active_hub_server = active_hub_server_configs
            arg.active_hub = True

        os.environ['GLOBAL_DONGLE_INIT_DELAY'] = str(arg.dongle_init_delay)

    def parse_args(self, args=None, namespace=None):
        namespace = argparse.Namespace(active_hub=None)
        arg = super().parse_args(args, namespace)
        self.check_args(arg)
        return arg


def get_workspace(workspace):
    for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, 'autopts/workspaces'),
                                     topdown=True):
        for name in dirs:
            if name == workspace:
                return os.path.join(root, name)
    return None


def delete_workspaces():
    def recursive(directory, depth):
        depth -= 1
        with os.scandir(directory) as iterator:
            for f in iterator:
                if f.is_dir() and depth > 0:
                    recursive(f.path, depth)
                elif f.name.startswith('temp_') and f.name.endswith('.pqw6'):
                    os.remove(f)

    init_depth = 4
    recursive(os.path.join(PROJECT_DIR, 'autopts/workspaces'), init_depth)


class Server(threading.Thread):
    def __init__(self, finish_count, _args=None):
        init_logging(_args)
        threading.Thread.__init__(self, daemon=True)
        self.server = None
        self._args = _args
        self.builtin_server = getattr(_args, 'builtin_server', False)
        self.name = 'S-' + str(self._args.srv_port)
        self.pts = PyPTSWithCallback(self._args,
                                     name=f'{self.name}-PTS')
        self.last_request_time = time.time()
        self.pts._update_request_time = self._update_request_time

        # Flag for ending sub-threads
        self.end = finish_count

        if self._args.ykush and type(self._args.ykush) is list:
            self._args.ykush = ' '.join(self._args.ykush)

        if self.builtin_server:
            # Register ptscontrol methods
            for method_name in dir(PyPTSWithCallback):
                method = getattr(self.pts, method_name)
                if not hasattr(self, method_name) and \
                        callable(method) and not method_name.startswith('_'):
                    self.__setattr__(method_name, partial(
                        self._dispatch_to_pts, method_name))

    def _dispatch_to_pts(self, method_name, *args, **kwargs):
        return self.pts._dispatch(method_name, (*args, *kwargs))

    def main(self, _args):
        """Main."""
        try:
            if self.builtin_server:
                self.pts.run()
            else:
                self.pts.start()
                self._xmlrpc_thread_work()
        finally:
            self.pts.terminate()
            self.terminate()

        return 0

    def _xmlrpc_thread_work(self):
        """
        This thread accepts and queues the client calls to
        the PyPTSWithCallback, does not process them.

        The PyPTSWithCallback methods should be processed in the
        same context as its instance was initialized.
        """

        if threading.current_thread().name != 'MainThread':
            # Should be called only in threads other than the main one.
            pythoncom.CoInitialize()
            log(f'pythoncom._GetInterfaceCount(): {pythoncom._GetInterfaceCount()}')

        c = wmi.WMI()
        for iface in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            print("Local IP address: %s DNS %r" % (iface.IPAddress, iface.DNSDomain))

        self.server_init()

        while not self.end.is_set() and not self.pts._end.is_set() \
                and not get_global_end():
            try:
                # Init
                if self._args.superguard and \
                        self._args.superguard < time.time() - self.last_request_time:
                    log('Superguard timeout, reinitializing XMLRPC')
                    print_thread_stack_trace()
                    self.server_init()

                # Main work
                self.server.handle_request()

            except KeyboardInterrupt:
                # Ctrl-C termination for single instance mode
                print("Keyboard Interrupt. Single-instance termination")
                break

            except BaseException as e:
                logging.exception(e)

        if threading.current_thread().name != 'MainThread':
            pythoncom.CoUninitialize()
            log(f'pythoncom._GetInterfaceCount(): {pythoncom._GetInterfaceCount()}')

    def server_init(self):
        if self.server:
            self.server.server_close()
            del self.server
            self.server = None

        print("Serving on port {} ...".format(self._args.srv_port))

        self.server = xmlrpc.server.SimpleXMLRPCServer(("", self._args.srv_port), allow_none=True)
        # These methods will be run in the XMLRPC context
        self.server.register_function(self.list_workspace_tree, 'list_workspace_tree')
        self.server.register_function(self.copy_file, 'copy_file')
        self.server.register_function(self.delete_file, 'delete_file')
        self.server.register_function(self.get_system_model, 'get_system_model')
        self.server.register_function(self.get_system_version, 'get_system_version')
        self.server.register_function(self.shutdown_pts_bpv, 'shutdown_pts_bpv')
        self.server.register_function(self.get_path, 'get_path')
        self.server.register_instance(self.pts)
        self.server.register_introspection_functions()
        self.server.timeout = 1.0

        # Some of PyPTS methods have to be run in the same context as
        # PTS init was performed, instead of the XMLRPC context.
        # To handle this, the special _dispatch method was implemented.
        self.server.register_instance(self.pts)
        self._update_request_time()

    def run(self):
        try:
            self.main(self._args)
        except Exception as exc:
            logging.exception(exc)
        finally:
            self.terminate()
            self.end.add(1)
            log(f'Server {str(self._args.srv_port)} finished')

    def terminate(self):
        self.end.set_flag()

    def _update_request_time(self):
        self.last_request_time = time.time()

    def get_system_model(self):
        self._update_request_time()
        proc = subprocess.Popen(['systeminfo'],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if stdout:
            info = stdout.splitlines()
            for line in info:
                line = line.decode('utf-8')
                if 'System Model' in line:
                    for platform in ['VirtualBox', 'VMware']:
                        if platform in line:
                            return platform
                    return 'Real HW'
        return 'PotatOS'

    def get_system_version(self):
        os_name = platform.system()
        version = platform.release()
        return f'{os_name} {version}'

    def get_path(self):
        self._update_request_time()
        return os.path.dirname(os.path.abspath(__file__))

    def list_workspace_tree(self, workspace_dir):
        self._update_request_time()
        if Path(workspace_dir).is_absolute():
            logs_root = workspace_dir
        else:
            logs_root = get_workspace(workspace_dir)

        file_list = []
        for root, dirs, files in os.walk(logs_root,
                                         topdown=False):
            for name in files:
                file_list.append(os.path.join(root, name))

            file_list.append(root)

        return file_list

    def copy_file(self, file_path):
        self._update_request_time()
        file_bin = None
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as handle:
                file_bin = xmlrpc.client.Binary(handle.read())
        return file_bin

    def delete_file(self, file_path):
        self._update_request_time()
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)

    def shutdown_pts_bpv(self):
        self._update_request_time()
        kill_all_processes('PTS.exe')
        kill_all_processes('Fts.exe')


if __name__ == "__main__":
    exit_if_admin()
    _args = SvrArgumentParser("PTS automation server").parse_args()

    init_logging(_args)

    if _args.active_hub:
        if _args.ykush:
            for ykush_config in _args.ykush:
                ykush_set_usb_power(ykush_config['ports'], False, ykush_config['ykush_srn'])

        elif _args.active_hub_server:
            for active_hub_server_config in _args.active_hub_server:
                active_hub_server_set_usb_power(active_hub_server_config, False)

    autoptsservers = []
    server_count = len(_args.srv_port)
    finish_count = CounterWithFlag(init_count=0)

    if _args.dongle is not None:
        for dongle in _args.dongle:
            # If dongle does not start with "COM" then it is considered valid port
            # for legacy dual-mode dongle compatibility.
            if dongle.startswith("COM"):
                if not _com_port_exists(dongle):
                    sys.exit(f"Port {dongle} not found")
            else:
                continue

    try:
        for i in range(server_count):
            args_copy = copy.deepcopy(_args)
            args_copy.srv_port = _args.srv_port[i]
            args_copy.ykush = _args.ykush[i] if _args.ykush else None
            args_copy.active_hub_server = _args.active_hub_server[i] if _args.active_hub_server else None
            args_copy.dongle = _args.dongle[i] if _args.dongle else None
            srv = Server(finish_count, args_copy)
            autoptsservers.append(srv)

            if server_count > 1:
                srv.start()
            else:
                srv.run()

        finish_count.wait_for(value=server_count)

    except KeyboardInterrupt:  # Ctrl-C
        # Termination for multi instance mode
        # because the threads does not receive a signal from Ctrl-C
        print("Keyboard Interrupt. Multi-instance termination")
        for s in autoptsservers:
            s.terminate()

        # Wait till PTS.exe shutdown.
        finish_count.wait_for(value=server_count)

    except Exception as e:
        logging.exception(e)
        traceback.print_exc()
        sys.exit(16)
