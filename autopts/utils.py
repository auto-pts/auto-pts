#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
# Copyright (c) 2021, Codecoup.
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

"""Utilities"""
import ctypes
import multiprocessing
import os
import subprocess
import sys
import threading
from ctypes import wintypes

PTS_WORKSPACE_FILE_EXT = ".pqw6"


class InterruptableThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, *, daemon=None, queue=None, final_fun=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, args=args,
                                  kwargs=kwargs, daemon=daemon)
        self.queue = queue
        self.final_fun = final_fun

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except BaseException as exc:
            if self.queue:
                self.queue.put(exc)
        finally:
            if self.final_fun:
                self.final_fun()
            del self._target, self._args, self._kwargs

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for _id, thread in threading._active.items():
            if thread is self:
                return _id
        return None

    def interrupt(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')


def usb_power(ykush_port, on=True):
    ykushcmd = 'ykushcmd'

    if sys.platform == "win32":
        ykushcmd += '.exe'

    p = subprocess.Popen([ykushcmd, '-u' if on else '-d', str(ykush_port)], stdout=subprocess.PIPE)
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        # The subprocess could hang in case autopts client and server
        # try to use ykush at the same time.
        p.kill()


def get_own_workspaces():
    """Get auto-pts own workspaces"""
    script_path = os.path.split(os.path.realpath(__file__))[0]
    workspaces = {}

    for root, dirs, files in os.walk(os.path.join(script_path, "workspaces")):
        for file in files:
            if file.endswith(PTS_WORKSPACE_FILE_EXT):
                name = os.path.splitext(file)[0]
                path = os.path.join(script_path, root, file)
                workspaces[name] = path

    return workspaces


# ****************************************************************************
# .ets swapper
# ****************************************************************************
def swap_etses(ptses, test_cases, revert):
    """
    Swap original .ets files with the ones from local ets/ folder,
    i.e. GAP.ets, GATT.ets. The ets/GAP_CONN_ACEP_BV_01_C.ets will
    be swapped with original GAP.ets

    Set revert=True to undo the swap.

    For the swap to work, the autoptsserver.py has to be run with the
    admin rights.
    """
    result = False

    if type(test_cases) == str:
        # Test case level swap
        result = ptses[0].swap_ets(test_cases, revert)
    else:
        # Project level swap
        stack_parts = {}
        for tc in test_cases:
            key, *_ = tc.split('/')
            stack_parts[key] = 1

        stack_parts = stack_parts.keys()

        # For GAP, GATT, etc. ...
        for p in stack_parts:
            result = result or ptses[0].swap_ets(p, revert)

    return result


def win32_is_file_in_use(filepath):
    ntdll = ctypes.WinDLL('ntdll')
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    NTSTATUS = wintypes.LONG
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
    FILE_READ_ATTRIBUTES = 0x80
    FILE_SHARE_READ = 1
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_INFORMATION_CLASS = wintypes.ULONG
    FileProcessIdsUsingFileInformation = 47
    LPSECURITY_ATTRIBUTES = wintypes.LPVOID
    ULONG_PTR = wintypes.WPARAM

    # -----------------------------------------------------------------------------
    # create handle on concerned file with dwDesiredAccess == FILE_READ_ATTRIBUTES
    # -----------------------------------------------------------------------------

    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,  # In     lpFileName
        wintypes.DWORD,  # In     dwDesiredAccess
        wintypes.DWORD,  # In     dwShareMode
        LPSECURITY_ATTRIBUTES,  # In_opt lpSecurityAttributes
        wintypes.DWORD,  # In     dwCreationDisposition
        wintypes.DWORD,  # In     dwFlagsAndAttributes
        wintypes.HANDLE)  # In_opt hTemplateFile
    hFile = kernel32.CreateFileW(
        filepath, FILE_READ_ATTRIBUTES, FILE_SHARE_READ, None, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS, None)
    if hFile == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    # -----------------------------------------------------------------------------
    # prepare data types for system call
    # -----------------------------------------------------------------------------

    class IO_STATUS_BLOCK(ctypes.Structure):
        class _STATUS(ctypes.Union):
            _fields_ = (('Status', NTSTATUS),
                        ('Pointer', wintypes.LPVOID))

        _anonymous_ = '_Status',
        _fields_ = (('_Status', _STATUS),
                    ('Information', ULONG_PTR))

    iosb = IO_STATUS_BLOCK()

    class FILE_PROCESS_IDS_USING_FILE_INFORMATION(ctypes.Structure):
        _fields_ = (('NumberOfProcessIdsInList', wintypes.LARGE_INTEGER),
                    ('ProcessIdList', wintypes.LARGE_INTEGER * 64))

    info = FILE_PROCESS_IDS_USING_FILE_INFORMATION()

    PIO_STATUS_BLOCK = ctypes.POINTER(IO_STATUS_BLOCK)
    ntdll.NtQueryInformationFile.restype = NTSTATUS
    ntdll.NtQueryInformationFile.argtypes = (
        wintypes.HANDLE,  # In  FileHandle
        PIO_STATUS_BLOCK,  # Out IoStatusBlock
        wintypes.LPVOID,  # Out FileInformation
        wintypes.ULONG,  # In  Length
        FILE_INFORMATION_CLASS)  # In  FileInformationClass

    # -----------------------------------------------------------------------------
    # system call to retrieve list of PIDs currently using the file
    # -----------------------------------------------------------------------------
    status = ntdll.NtQueryInformationFile(hFile, ctypes.byref(iosb),
                                          ctypes.byref(info),
                                          ctypes.sizeof(info),
                                          FileProcessIdsUsingFileInformation)
    pidList = info.ProcessIdList[0:info.NumberOfProcessIdsInList]
    process_pid = multiprocessing.current_process().pid
    if process_pid in pidList:
        pidList.remove(process_pid)

    return len(pidList) > 0


# 10x faster than win32_is_file_in_use, but less secure when interrupted
def is_file_in_use(filepath):
    try:
        os.rename(filepath, filepath + "_")
        os.rename(filepath + "_", filepath)
    except:
        return True

    return False
