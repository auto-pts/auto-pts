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
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import xmlrpc.client
import xmlrpc.server
from os.path import dirname, abspath
from pathlib import Path
from time import sleep

import pythoncom
import win32com
import win32com.client
import wmi
from autopts import winutils, ptscontrol

from autopts.config import SERVER_PORT
from autopts.utils import usb_power

log = logging.debug
PROJECT_DIR = dirname(abspath(__file__))
PTS_START_LOCK = threading.RLock()


def server_start_lock_wrapper(func):
    def _server_start_lock_wrapper(*args):
        try:
            PTS_START_LOCK.acquire()
            ret = func(*args)
        finally:
            PTS_START_LOCK.release()
        return ret

    return _server_start_lock_wrapper


class PyPTSWithXmlRpcCallback(ptscontrol.PyPTS):
    """A child class that adds support of xmlrpc PTS callbacks to PyPTS"""

    def __init__(self):
        """Constructor"""
        super().__init__()

        log("%s", self.__init__.__name__)

        # address of the auto-pts client that started it's own xmlrpc server to
        # receive callback messages
        self.client_address = None
        self.client_port = None
        self.client_xmlrpc_proxy = None

    def register_xmlrpc_ptscallback(self, client_address, client_port):
        """Registers client callback. xmlrpc proxy/client calls this method
        to register its callback

        client_address -- IP address
        client_port -- TCP port
        """

        log("%s %s %d", self.register_xmlrpc_ptscallback.__name__,
            client_address, client_port)

        self.client_address = client_address
        self.client_port = client_port

        self.client_xmlrpc_proxy = xmlrpc.client.ServerProxy(
            "http://{}:{}/".format(self.client_address, self.client_port),
            allow_none=True)

        log("Created XMR RPC auto-pts client proxy, provides methods: %s" %
            self.client_xmlrpc_proxy.system.listMethods())

        self.register_ptscallback(self.client_xmlrpc_proxy)

    def unregister_xmlrpc_ptscallback(self):
        """Unregisters the client callback"""

        log("%s", self.unregister_xmlrpc_ptscallback.__name__)

        self.unregister_ptscallback()

        self.client_address = None
        self.client_port = None
        self.client_xmlrpc_proxy = None


class SvrArgumentParser(argparse.ArgumentParser):
    def __init__(self, description):
        argparse.ArgumentParser.__init__(self, description=description)

        self.add_argument("-S", "--srv_port", type=int,
                          nargs="+", default=[SERVER_PORT],
                          help="Specify the server port number")

        self.add_argument("--superguard", default=0, type=float, metavar='MINUTES',
                          help="Specify amount of time in minutes, after which"
                          " super guard will blindly trigger recovery steps.")

        self.add_argument("--ykush", nargs="+", default=[], metavar='YKUSH_PORT',
                          help="Specify ykush hub downstream port number, so "
                          "during recovery steps PTS dongle could be replugged.")

    @staticmethod
    def check_args(arg):
        """Sanity check command line arguments"""

        for srv_port in arg.srv_port:
            if not 49152 <= srv_port <= 65535:
                sys.exit("Invalid server port number=%s, expected range <49152,65535> " % (srv_port,))

        if len(arg.srv_port) == 1:
            arg.srv_port = arg.srv_port[0]

        arg.superguard = 60 * arg.superguard

    def parse_args(self, args=None, namespace=None):
        arg = super().parse_args()
        self.check_args(arg)
        return arg


def get_workspace(workspace):
    for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, 'autopts/workspaces'),
                                     topdown=True):
        for name in dirs:
            if name == workspace:
                return os.path.join(root, name)
    return None


def kill_all_processes(name):
    c = wmi.WMI()
    for ps in c.Win32_Process(name=name):
        try:
            ps.Terminate()
            log("%s process (PID %d) terminated successfully" % (name, ps.ProcessId))
        except BaseException as exc:
            logging.exception(exc)
            log("There is no %s process running with id: %d" % (name, ps.ProcessId))


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


def power_dongle(ykush_port, on=True):
    usb_power(ykush_port, on)


def dongle_exists(serial_address):
    wmi = win32com.client.GetObject("winmgmts:")

    if 'USB' in serial_address:  # USB:InUse:X&XXXXXXXX&X&X
        serial_address = serial_address.split(r':')[2]
        usbs = wmi.InstancesOf("Win32_USBHub")
    else:  # COMX
        usbs = wmi.InstancesOf("Win32_SerialPort")

    for usb in usbs:
        if serial_address in usb.DeviceID:
            return True

    return False


class SuperGuard(threading.Thread):
    def __init__(self, timeout):
        threading.Thread.__init__(self, daemon=True)
        self.servers = []
        self.timeout = timeout
        self.end = False
        self.was_timeout = False

    def run(self):
        while not self.end:
            idle_num = 0
            for srv in self.servers:
                if time.time() - srv.last_start() > self.timeout:
                    idle_num += 1

            if idle_num == len(self.servers) and idle_num != 0:
                log('Superguard timeout, recovering')
                for srv in self.servers:
                    srv.request_recovery()
                self.was_timeout = True
            sleep(5)

    def clear(self):
        self.servers.clear()
        self.was_timeout = False

    def add_server(self, srv):
        self.servers.append(srv)

    def terminate(self):
        self.end = True


class Server(threading.Thread):
    def __init__(self, _args=None):
        threading.Thread.__init__(self, daemon=True)
        self.server = None
        self._args = _args
        self.pts = None
        self._device = None
        self.end = False
        self.recovery_request = False
        self.name = 'S-' + str(self._args.srv_port)
        self.is_ready = False
        if self._args.ykush and type(self._args.ykush) is list:
            self._args.ykush = ' '.join(self._args.ykush)

    def last_start(self):
        try:
            return self.pts.last_start_time
        except:
            return time.time()

    def main(self, _args):
        """Main."""
        pythoncom.CoInitialize()

        c = wmi.WMI()
        for iface in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            print("Local IP address: %s DNS %r" % (iface.IPAddress, iface.DNSDomain))

        while not self.end:
            self.recovery_request = False
            try:
                self.server_init()
                self.is_ready = True
                while not self.end and not self.recovery_request:
                    self.server.handle_request()
            except Exception as e:
                logging.exception(e)
                kill_all_processes('PTS.exe')

            ptscontrol.set_stop_pts(False)
            self.is_ready = False

        return 0

    @server_start_lock_wrapper
    def server_init(self):
        if self.pts:
            self.pts.stop_pts()
            self.pts.delete_temp_workspace()
            del self.pts
            self.pts = None

        if self.server:
            self.server.server_close()
            del self.server
            self.server = None

        if self._args.ykush:
            log(f'Replugging device ({self._device}) under ykush:{self._args.ykush}')
            power_dongle(self._args.ykush, False)
            while self._device and dongle_exists(self._device):
                pass
            power_dongle(self._args.ykush, True)
            while self._device and not dongle_exists(self._device):
                pass

        print("Starting PTS ...")
        self.pts = PyPTSWithXmlRpcCallback()
        self._device = self.pts._device
        print("OK")

        print("Serving on port {} ...".format(self._args.srv_port))

        self.server = xmlrpc.server.SimpleXMLRPCServer(("", self._args.srv_port), allow_none=True)
        self.server.register_function(self.request_recovery, 'request_recovery')
        self.server.register_function(self.list_workspace_tree, 'list_workspace_tree')
        self.server.register_function(self.copy_file, 'copy_file')
        self.server.register_function(self.delete_file, 'delete_file')
        self.server.register_function(self.ready, 'ready')
        self.server.register_function(self.get_system_model, 'get_system_model')
        self.server.register_function(self.shutdown_pts_bpv, 'shutdown_pts_bpv')
        self.server.register_instance(self.pts)
        self.server.register_introspection_functions()
        self.server.timeout = 1.0

    def run(self):
        try:
            self.main(self._args)
        except Exception as exc:
            self.end = True
            logging.exception(exc)
            print('Server ', str(self._args.srv_port), ' finished')

    def request_recovery(self):
        self.is_ready = False
        self.recovery_request = True
        ptscontrol.set_stop_pts(True)

    def terminate(self):
        self.is_ready = False
        self.end = True

    def ready(self):
        return self.is_ready

    def get_system_model(self):
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
        return 'Unknown'

    def list_workspace_tree(self, workspace_dir):
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
        file_bin = None
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as handle:
                file_bin = xmlrpc.client.Binary(handle.read())
        return file_bin

    def delete_file(self, file_path):
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)

    def shutdown_pts_bpv(self):
        kill_all_processes('PTS.exe')
        kill_all_processes('Fts.exe')


def multi_main(_args, _superguard):
    """Multi server main."""

    servers = []
    for i in range(len(_args.srv_port)):
        args_copy = copy.deepcopy(_args)
        args_copy.srv_port = _args.srv_port[i]
        args_copy.ykush = _args.ykush[i] if _args.ykush else None
        srv = Server(_args=args_copy)
        servers.append(srv)
        srv.start()
        superguard.add_server(srv)

    all_alive = True
    while all_alive:
        for s in servers:
            if not s.is_alive():
                all_alive = False
        sleep(5)

    for s in servers:
        s.terminate()


if __name__ == "__main__":
    winutils.exit_if_admin()
    _args = SvrArgumentParser("PTS automation server").parse_args()

    script_name = os.path.basename(sys.argv[0])  # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = script_name_no_ext + '.log'
    format_template = '%(threadName)s %(asctime)s %(name)s %(levelname)s : %(message)s'

    logging.basicConfig(format=format_template,
                        filename=log_filename,
                        filemode='w',
                        level=logging.DEBUG)

    superguard = SuperGuard(float(_args.superguard))
    if _args.superguard:
        superguard.start()

    if _args.ykush:
        for port in _args.ykush:
            power_dongle(port, False)

    try:
        if isinstance(_args.srv_port, int):
            server = Server(_args)
            superguard.add_server(server)

            server.main(_args)  # Run server in main process
        else:
            multi_main(_args, superguard)  # Run many servers in threads

    except KeyboardInterrupt:  # Ctrl-C
        pass

    except Exception as e:
        logging.exception(e)
        traceback.print_exc()
        sys.exit(16)
