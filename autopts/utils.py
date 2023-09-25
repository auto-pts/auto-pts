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
import logging
import os
import subprocess
import sys
import threading
import psutil

PTS_WORKSPACE_FILE_EXT = ".pqw6"

# A mechanism for safely terminating threads
# after interrupt triggered with Ctrl+C
GLOBAL_END = False


class RunEnd(KeyboardInterrupt):
    pass


def set_global_end():
    global GLOBAL_END
    GLOBAL_END = True


def raise_on_global_end():
    if GLOBAL_END:
        raise RunEnd


def get_global_end():
    return GLOBAL_END


def log_running_threads():
    active_threads = threading.enumerate()
    logging.debug("Active threads:")
    for thread in active_threads:
        logging.debug(f"Thread Name: {thread.name}")


class ResultWithFlag:
    """"""
    def __init__(self, init_value=None):
        self.result = init_value
        self.event = threading.Event()
        self.lock = threading.Lock()

    def is_set(self):
        return self.event.is_set()

    def set_flag(self):
        self.event.set()

    def set(self, value):
        with self.lock:
            self.result = value
            self.event.set()

    def get(self, timeout=None, predicate=None):
        """
        Args:
            timeout: timeout in seconds
            predicate: a function that will check other additional
             waiting conditions
        """
        self.wait(timeout=timeout, predicate=predicate)
        with self.lock:
            return self.result

    def wait(self, timeout=None, predicate=lambda: True):
        """
        Args:
            timeout: timeout in seconds
            predicate: a function that will check other additional
             waiting conditions

        If timeout, will throw an exception: TimeoutError
        """
        # Ctrl+C friendly under Windows
        if predicate is None:
            predicate = lambda: True

        raise_timeout = False

        def on_timeout():
            nonlocal raise_timeout
            raise_timeout = True
            self.event.set()

        timer = None
        if timeout:
            timer = threading.Timer(timeout, on_timeout)
            timer.name = f'Timer{timer.name}'
            timer.start()

        try:
            while predicate() and not self.event.is_set():
                raise_on_global_end()
                self.event.wait(1)
        finally:
            if timer:
                timer.cancel()
                if raise_timeout:
                    raise TimeoutError

    def get_nowait(self):
        with self.lock:
            return self.result

    def cancel_wait(self):
        self.set(None)

    def clear(self):
        with self.lock:
            self.result = None
        self.event.clear()


class CounterWithFlag(ResultWithFlag):
    def __init__(self, init_count):
        super().__init__()
        self.result = init_count

    def add(self, value):
        with self.lock:
            self.result += value
        with self.event._cond:
            self.event._cond.notify_all()

    def wait_for(self, value, timeout=None):
        def predicate():
            with self.lock:
                return self.result != value

        self.wait(timeout=timeout, predicate=predicate)


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
        # Inject raise KeyboardInterrupt into a thread. Under Windows will not
        # work if a thread stacked on wait() or get() from the 'threading' module.
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(KeyboardInterrupt))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            logging.debug(f'Failed to inject an KeyboardInterrupt into a thread {self.name}')


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
    script_path = os.path.split(os.path.abspath(__file__))[0]
    workspaces = {}

    for root, dirs, files in os.walk(os.path.join(script_path, "workspaces")):
        for file in files:
            if file.endswith(PTS_WORKSPACE_FILE_EXT):
                name = os.path.splitext(file)[0]
                path = os.path.join(script_path, root, file)
                workspaces[name] = path

    return workspaces


def count_script_instances(script_name):
    count = 0
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'].startswith('python') and script_name in ' '.join(proc.info['cmdline']):
            count += 1
    return count


class AdminStateUnknownError(Exception):
    pass


if sys.platform == 'win32':
    import win32com
    import win32com.client

    def device_exists(serial_address):
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


    def have_admin_rights():
        """"Check if the process has Administrator rights"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except AttributeError:
            raise AdminStateUnknownError

else:
    _pyudev = False

    def device_exists(serial_address, subsystem='tty'):
        global _pyudev
        if not _pyudev:
            import pyudev
            _pyudev = pyudev

        context = _pyudev.Context()
        for device in context.list_devices(subsystem=subsystem):
            try:
                if serial_address in device.get('DEVNAME'):
                    return True
            except BaseException as e:
                pass
        return False

    def have_admin_rights():
        """"Check if the process has Administrator rights"""
        try:
            return os.getuid() == 0
        except AttributeError:
            raise AdminStateUnknownError


def exit_if_admin():
    """Exit program if running as Administrator"""
    if have_admin_rights():
        sys.exit("Administrator rights are not required to run this script!")


def main():
    """Main."""

    is_admin = have_admin_rights()

    if is_admin:
        print("Running as administrator")
    else:
        print("Not running as administrator")

    exit_if_admin()


if __name__ == "__main__":
    main()
