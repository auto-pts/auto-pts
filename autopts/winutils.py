#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation
# Copyright (c) 2023, Codecoup
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

"""Windows utilities"""
import logging

import win32gui
import win32process
import wmi


def get_pid_by_window_title(title):
    def callback(hwnd, hwnd_list):
        window_title = win32gui.GetWindowText(hwnd)
        if window_title.startswith(title):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                hwnd_list.append(pid)
            except Exception as e:
                logging.warning(f"Failed to get PID for hwnd {hwnd}: {e}")

    hwnd_list = []
    win32gui.EnumWindows(callback, hwnd_list)
    if hwnd_list:
        return hwnd_list[0]
    else:
        return None


def _terminate_process_safely(process, name):
    try:
        process.Terminate()
        logging.debug(f"{name} process (PID {process.ProcessId}) terminated successfully")
    except BaseException as exc:
        logging.exception(exc)
        logging.debug(f"There is no {name} process running with id: {process.ProcessId}")


def kill_all_processes(name):
    c = wmi.WMI()
    for ps in c.Win32_Process(name=name):
        _terminate_process_safely(ps, name)
