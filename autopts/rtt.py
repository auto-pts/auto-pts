#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

import logging
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time

import pylink

from autopts.config import BTMON_PORT
from autopts.utils import get_global_end

log = logging.debug


class RTT:
    # Due to Pylink module limitations we have to
    # share one instance of JLink object
    jlink = None
    lib = None

    def __init__(self):
        self.read_thread = None
        self.stop_thread = threading.Event()
        pylink.logger.setLevel(logging.WARNING)

    def _get_buffer_index(self, buffer_name):
        timeout = time.time() + 10
        num_up = 0
        while True:
            try:
                num_up = RTT.jlink.rtt_get_num_up_buffers()
                break
            except pylink.errors.JLinkRTTException:
                if time.time() > timeout:
                    break
                time.sleep(0.1)

        for buf_index in range(num_up):
            buf = RTT.jlink.rtt_get_buf_descriptor(buf_index, True)
            if buf.name == buffer_name:
                return buf_index

    @staticmethod
    def _read_from_buffer(jlink, buffer_index, stop_thread, user_callback, user_data):
        try:
            while not stop_thread.is_set() and jlink.connected() and not get_global_end():
                byte_list = jlink.rtt_read(buffer_index, 1024)
                if len(byte_list) > 0:
                    user_callback(bytes(byte_list), user_data)
        except BaseException:
            pass  # JLink closed

    def init_jlink(self, device_core, debugger_snr):
        if RTT.jlink:
            return

        if not RTT.lib and (dllpath := os.environ.get("AUTOPTS_RTT_OVERRIDE_JLINK_DLLPATH")):
            # Allow for the J-Link DLL to be specified
            RTT.lib = pylink.library.Library(dllpath=dllpath)

        RTT.jlink = pylink.JLink(lib=RTT.lib)
        # Pylink loads a new cache of J-Link DLL at its __init__,
        # but the __del__ does not unload it. Luckily we can reuse
        # the cached lib to prevent memory leak (around 20MB per test case!).
        RTT.lib = RTT.jlink._library

        RTT.jlink.disable_dialog_boxes()
        if not RTT.jlink.opened():
            RTT.jlink.open(serial_no=debugger_snr)

        RTT.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        RTT.jlink.connect(device_core)

        status = RTT.jlink.rtt_get_status()
        if status.IsRunning == 0:
            RTT.jlink.rtt_start()

    def start(self, buffer_name, device_core, debugger_snr, user_callback, user_data):
        log("%s.%s", self.__class__, self.start.__name__)

        self.init_jlink(device_core, debugger_snr)
        buffer_index = self._get_buffer_index(buffer_name)
        self.stop_thread.clear()
        self.read_thread = threading.Thread(target=self._read_from_buffer,
                                            args=(RTT.jlink,
                                                  buffer_index,
                                                  self.stop_thread,
                                                  user_callback,
                                                  user_data))
        self.read_thread.start()

    def stop(self):
        log("%s.%s", self.__class__, self.stop.__name__)
        self.stop_thread.set()

        if self.read_thread:
            self.read_thread.join()
            self.read_thread = None
            if RTT.jlink:
                try:
                    RTT.jlink.rtt_stop()
                except (pylink.errors.JLinkRTTException, pylink.errors.JLinkException) as err:
                    log(f'Failed to stop RTT, err: {err}')
                try:
                    RTT.jlink.close()
                except pylink.errors.JLinkException as err:
                    log(f'Failed to close J-Link connection, err: {err}')
                del RTT.jlink
                RTT.jlink = None


class BTMON:
    def __init__(self):
        self.rtt_reader = RTT()
        self.btmon_process = None
        self.socat_process = None
        self.log_filename = None
        self.plain_log_filename = None
        self.log_filecwd = None

    def _on_line_read_callback(self, data, user_data):
        sock, = user_data
        try:
            sock.sendall(data)
        except UnicodeDecodeError:
            pass

    def _wsl_call(self, cmd):
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl
        subprocess.call(cmd, shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

    def _wsl_popen(self, cmd, cwd):
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl
        return subprocess.Popen(cmd, shell=False, cwd=cwd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def is_running(self):
        return not self.rtt_reader.stop_thread.is_set()

    def start(self, buffer_name, log_file, device_core, debugger_snr, hci):
        log("%s.%s", self.__class__, self.start.__name__)

        self.log_filecwd = os.path.dirname(os.path.abspath(log_file))
        # btsnoop file
        self.log_filename = os.path.basename(log_file)
        # readable log file from btmon output
        self.plain_log_filename, *extension = os.path.splitext(self.log_filename)
        self.plain_log_filename += '_text' + ''.join(extension)

        if sys.platform == 'win32':
            # Remember to install btmon and socat in your Ubuntu WSL2 instance,
            # as they are not available after fresh install.
            self._wsl_call('killall btmon')
            self._wsl_call('killall socat')

            cmd = f'socat -dd pty,raw,echo=0 TCP-LISTEN:{BTMON_PORT},reuseaddr'
            self.socat_process = self._wsl_popen(cmd, self.log_filecwd)
            if not self.socat_process or self.socat_process.poll():
                log('Socat failed to start')
                self.stop()
                return

            pty = None
            err = ""
            for line in self.socat_process.stderr:
                match = re.findall(r'/dev/pts/\d+', line.decode())
                if match:
                    pty = match[0]
                    break
                else:
                    err += line.decode()

            if not pty:
                log(f'Socat failed to start, err: {err}')
                self.stop()
                return

            cmd = ['btmon', '-C', str(130), '-d', pty, '-w', self.log_filename]
            self.btmon_process = self._wsl_popen(subprocess.list2cmdline(cmd), self.log_filecwd)
            if not self.btmon_process or self.btmon_process.poll():
                log('BTMON failed to start')
                self.stop()
                return

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = ('localhost', BTMON_PORT)
            sock.connect(server_address)

            self.rtt_reader.start(buffer_name, device_core, debugger_snr, self._on_line_read_callback, (sock,))
        else:
            if hci is not None:
                cmd = f"btmon -C 130 -i {hci} -w {self.log_filename}"
            else:
                cmd = f"btmon -C 130 -J {device_core},{debugger_snr} -w {self.log_filename}"
            self.btmon_process = subprocess.Popen(cmd, cwd=self.log_filecwd,
                                                  shell=True,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  preexec_fn=os.setsid)

    def stop(self):
        log("%s.%s", self.__class__, self.stop.__name__)
        self.rtt_reader.stop()

        if self.btmon_process and self.btmon_process.poll() is None:
            if sys.platform != 'win32':
                os.killpg(os.getpgid(self.btmon_process.pid), signal.SIGTERM)

            self.btmon_process.terminate()
            self.btmon_process.wait()
            self.btmon_process = None

        if self.socat_process and self.socat_process.poll() is None:
            self.socat_process.terminate()
            self.socat_process.wait()
            self.socat_process = None

        # copy btmon output to readable log file
        cmd = f"btmon -r {self.log_filename} -P > {self.plain_log_filename}"
        if sys.platform == 'win32':
            proc = self._wsl_popen(cmd, self.log_filecwd)
        else:
            proc = subprocess.Popen(cmd, cwd=self.log_filecwd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    preexec_fn=os.setsid)
        proc.wait()


class RTTLogger:
    def __init__(self, syncto=0):
        self.rtt_reader = RTT()
        self.log_file = None
        self.syncto = syncto

    def _on_line_read_callback(self, data, user_data):
        file, = user_data
        try:
            file.write(data)
            file.flush()
        except UnicodeDecodeError:
            pass

    def is_running(self):
        return not self.rtt_reader.stop_thread.is_set()

    def start(self, buffer_name, log_filename, device_core, debugger_snr):
        log("%s.%s", self.__class__, self.start.__name__)
        self.log_file = open(log_filename, 'ab')
        self.rtt_reader.start(buffer_name, device_core, debugger_snr, self._on_line_read_callback, (self.log_file,))

    def stop(self):
        log("%s.%s", self.__class__, self.stop.__name__)
        if self.syncto > 0:
            time.sleep(self.syncto)
        self.rtt_reader.stop()

        if self.log_file:
            self.log_file.close()
            self.log_file = None


if __name__ == "__main__":
    btmon_buffer = 'btmonitor'
    rttlog_buffer = 'Logger'
    device_core = 'NRF52840_XXAA'
    debugger_snr = '123456789'
    btmon_logfile = 'btmon_snoop.log'
    rtt_logfile = 'rtt_logs.log'

    btmon = None
    rtt_logger = None
    try:
        btmon = BTMON()
        btmon.start(btmon_buffer, btmon_logfile, device_core, debugger_snr)

        rtt_logger = RTTLogger()
        rtt_logger.start(rttlog_buffer, rtt_logfile, device_core, debugger_snr)

        while btmon.is_running() and rtt_logger.is_running():
            pass
    except BaseException:
        if btmon:
            btmon.stop()

        if rtt_logger:
            rtt_logger.stop()
