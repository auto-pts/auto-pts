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
import sys
import threading
import traceback
import xmlrpc.client
from time import sleep

import hid
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

    def get(self, timeout=None, predicate=None, clear=False):
        """
        Args:
            timeout: timeout in seconds
            predicate: a function that will check other additional
             waiting conditions
            clear: clear result and flag so the result will not be reused
        """
        self.wait(timeout=timeout, predicate=predicate)
        with self.lock:
            result = self.result
            if clear:
                self.result = None
                self.event.clear()
            return result

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
        self.interrupt_lock = threading.RLock()

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
        with self.interrupt_lock:
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                thread_id, ctypes.py_object(KeyboardInterrupt))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            logging.debug(f'Failed to inject an KeyboardInterrupt into a thread {self.name}')


pykush_installed = False
try:
    import pykush.pykush as pykush
    pykush_installed = True
except:
    pass


def ykush_set_usb_power(ykush_port, on=True, ykush_srn=None):
    if not pykush_installed:
        print('pykush not installed')
        return

    yk = None
    try:
        ykush_port = int(ykush_port)
        yk = pykush.YKUSH(serial=ykush_srn)
        state = pykush.YKUSH_PORT_STATE_UP if on else pykush.YKUSH_PORT_STATE_DOWN
        yk.set_port_state(ykush_port, state)
        if yk.get_port_state(ykush_port) != state:
            ykush_name = ykush_srn if ykush_srn else ''
            raise Exception(f'YKUSH {ykush_name} failed to change state {state} of port {ykush_port}')
    finally:
        if yk:
            del yk


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


def terminate_process(pid=None, name=None, cmdline=None):
    if pid is None and name is None and cmdline is None:
        logging.debug('No arguments provided')
        return

    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if pid and pid != process.info["pid"]:
            continue

        if name and (process.info["name"] or name not in process.info["name"]):
            continue

        if cmdline and (not process.info["cmdline"] or
           cmdline not in ' '.join(process.info["cmdline"])):
            continue

        process.terminate()
        process.wait()

        logging.debug(f"The process with pid={process.info['pid']} name={process.info['name']} "
                      f"cmdline={process.info['cmdline']} has been terminated.")


class AdminStateUnknownError(Exception):
    pass


if sys.platform == 'win32':
    import win32com
    import win32com.client

    def device_exists(serial_address):
        if not serial_address:
            return False

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

        if os.path.islink(serial_address):
            serial_address = os.path.realpath(serial_address)

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


def ykush_replug_usb(ykush_config, device_id=None, delay=0, end_flag=None):
    if isinstance(ykush_config, str):
        ykush_port = ykush_config
        ykush_srn = None
    elif isinstance(ykush_config, dict):
        ykush_port = ykush_config['ports']
        ykush_srn = ykush_config['ykush_srn']
    else:
        logging.debug('Invalid format of ykush config')
        return

    if device_id is None:
        ykush_set_usb_power(ykush_port, False, ykush_srn)
        sleep(delay)
        ykush_set_usb_power(ykush_port, True, ykush_srn)
        sleep(delay)
        return

    i = 0
    while device_exists(device_id):
        raise_on_global_end()
        if end_flag and end_flag.is_set():
            return

        if i == 0:
            logging.debug(f'Power down device ({device_id}) under ykush_port:{ykush_port}')
            ykush_set_usb_power(ykush_port, False, ykush_srn)
            i = 20
        else:
            i -= 1
        sleep(0.1)

    sleep(delay)
    logging.debug(f'Power up device ({device_id}) under ykush_port:{ykush_port}')
    ykush_set_usb_power(ykush_port, True, ykush_srn)

    i = 0
    while not device_exists(device_id):
        raise_on_global_end()
        if end_flag and end_flag.is_set():
            return

        if i == 20:
            # Sometimes JLink falls into a bad state and cannot
            # be enumerated correctly at first time
            ykush_set_usb_power(ykush_port, False, ykush_srn)
            sleep(delay)
            ykush_set_usb_power(ykush_port, True, ykush_srn)
            i = 0
        else:
            i += 1

        sleep(0.1)


def hid_gpio_hub_set_usb_power(vid, pid, port, on):
    path = None
    cmd = b"\x05xxxxxxxx"
    index = int(port)

    if 1 <= index <= len(cmd) - 1:
        cmd_list = list(cmd)
        cmd_list[index] = ord('0' if on else '1')
        cmd = bytes(cmd_list)

    for device in hid.enumerate(vid, pid):
        print(device)
        path = device['path']

    device = hid.device()
    device.open_path(path)
    device.send_feature_report(cmd)
    device.close()

    # Read the flashed versions of hid_gpio and apache-mynewt-core
    # print(device.get_indexed_string(32))
    # print(device.get_indexed_string(33))
    # Read the states of hub ports
    # print(device.get_feature_report(5, 9))


def active_hub_server_replug_usb(config):
    with xmlrpc.client.ServerProxy(uri=f"http://{config['ip']}:{config['tcp_port']}/",
                                   allow_none=True, transport=None,
                                   encoding=None, verbose=False,
                                   use_datetime=False, use_builtin_types=False,
                                   headers=(), context=None) as proxy:
        logging.debug(f'Power down USB port: {config["usb_port"]}')
        proxy.set_usb_power(config['usb_port'], False)
        sleep(config['replug_delay'])
        logging.debug(f'Power up USB port: {config["usb_port"]}')
        proxy.set_usb_power(config['usb_port'], True)


def active_hub_server_set_usb_power(config, on):
    with xmlrpc.client.ServerProxy(uri=f"http://{config['ip']}:{config['tcp_port']}/",
                                   allow_none=True, transport=None,
                                   encoding=None, verbose=False,
                                   use_datetime=False, use_builtin_types=False,
                                   headers=(), context=None) as proxy:

        proxy.set_usb_power(config['usb_port'], on)


def print_thread_stack_trace():
    logging.debug("Printing stack trace for each thread:")
    for thread_id, thread_obj in threading._active.items():
        stack = sys._current_frames().get(thread_id)
        if stack is not None:
            logging.debug(f"Thread ID: {thread_id}, Thread Name: {thread_obj.name}")
            logging.debug(traceback.extract_stack(stack))


def exit_if_admin():
    """Exit program if running as Administrator"""
    if have_admin_rights():
        sys.exit("Administrator rights are not required to run this script!")


def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    mem_usage = mem_info.rss / (1024 ** 2)
    logging.debug(f"Memory usage: {mem_usage:.2f} MB")


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
