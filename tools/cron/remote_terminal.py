#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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
import argparse
import os
import shlex
import socket
import subprocess
import sys
import traceback
import xmlrpc.client
import xmlrpc.server
from os.path import abspath, dirname

AUTOPTS_REPO = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, AUTOPTS_REPO)

from autopts.utils import terminate_process as utils_terminate_process  # noqa: E402, I001 # the order of import is very important here


class StartArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)

        self.add_argument("--ip", default='', type=str,
                          help="IP address")

        self.add_argument("--port", default=65100, type=int,
                          help="TCP port")

    @staticmethod
    def check_args(arg):
        """Sanity check command line arguments"""
        if not 49152 <= arg.port <= 65535:
            sys.exit(f"Invalid server port number={arg.port}, expected range <49152,65535>")

    def parse_args(self, args=None, namespace=None):
        arg = super().parse_args(args, namespace)
        self.check_args(arg)
        return arg


def run_command(command, cwd):
    """Run a command as a subprocess and return the output."""
    try:
        print(f'Running command: {command}')
        output = subprocess.check_output(command, shell=True,
                                         cwd=cwd, stderr=subprocess.STDOUT)
        return output.decode()

    except BaseException as e:
        return traceback.format_exception(e)


def open_process(command, cwd):
    """Run a command as a subprocess and skip the output."""
    try:
        print(f'Running command: {command}')
        subprocess.Popen(shlex.split(command),
                         shell=True,
                         cwd=cwd)
        return 'OK'

    except BaseException as e:
        traceback.print_exception(e)
        return traceback.format_exception(e)


def terminate_process(pid=None, name=None, cmdline=None):
    if pid is None and name is None and cmdline is None:
        return 'No arguments'

    try:
        utils_terminate_process(pid, name, cmdline)
    except BaseException as e:
        traceback.print_exception(e)
        return traceback.format_exception(e)

    return ''


def copy_file(file_path):
    file_bin = None
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as handle:
            file_bin = xmlrpc.client.Binary(handle.read())
    return file_bin


def start_server():
    args = StartArgumentParser().parse_args()

    print(f"Serving on port {args.port} ...")
    server = xmlrpc.server.SimpleXMLRPCServer((args.ip, args.port), allow_none=True)
    server.register_function(run_command, 'run_command')
    server.register_function(open_process, 'open_process')
    server.register_function(terminate_process, 'terminate_process')
    server.register_function(copy_file, 'copy_file')
    server.register_introspection_functions()
    server.timeout = 1.0

    try:
        while True:
            server.handle_request()
    except KeyboardInterrupt:
        return
    except BaseException as e:
        traceback.print_exception(e)


class TimeoutTransport (xmlrpc.client.Transport):
    def __init__(self, timeout, context=None, use_datetime=0):
        xmlrpc.client.Transport.__init__(self, use_datetime)
        self._timeout = timeout
        self.context = context

    def make_connection(self, host):
        conn = xmlrpc.client.Transport.make_connection(self, host)
        conn.timeout = self._timeout
        return conn


class RemoteTerminalClientProxy(xmlrpc.client.ServerProxy):
    def __init__(self, client_address, client_port, timeout=None):
        if not timeout:
            timeout = socket._GLOBAL_DEFAULT_TIMEOUT

        super().__init__(uri=f"http://{client_address}:{client_port}/",
                         allow_none=True, transport=TimeoutTransport(timeout=timeout),
                         encoding=None, verbose=False,
                         use_datetime=False, use_builtin_types=False,
                         headers=(), context=None)

        print(f"{self.__init__.__name__}, uri={self.uri}")

        self.client_address = client_address
        self.client_port = client_port


if __name__ == "__main__":
    start_server()
