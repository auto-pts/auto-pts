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
import csv
import ctypes
import logging
import os
import re
import sys
import threading
import traceback
import xmlrpc.client
from collections import defaultdict
from pathlib import Path
from time import sleep

import hid
import psutil

from autopts.config import FILE_PATHS

PTS_WORKSPACE_FILE_EXT = ".pqw6"

# Global paths for wid report
BASE_DIR = Path(__file__).parent.parent.resolve()
LOG_DIR = BASE_DIR / "logs"

# Regex patterns for log field parsing in wid report
WID_REGEX = re.compile(r"^wid:\s*(\S+)")
TC_NAME_REGEX = re.compile(r"^test_case_name:\s*(.+)")

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

        def _default_predicate():
            return True

        # Ctrl+C friendly under Windows
        if predicate is None:
            predicate = _default_predicate

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
except ImportError:
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

    for root, _dirs, files in os.walk(os.path.join(script_path, "workspaces")):
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
        except AttributeError as e:
            raise AdminStateUnknownError from e


else:
    _pyudev = False

    def device_exists(serial_address, subsystem='tty'):
        global _pyudev
        if not _pyudev:
            import pyudev
            _pyudev = pyudev

        if os.path.islink(serial_address):
            serial_address = os.path.realpath(serial_address)

        def _device_has_serial(device, serial_address):
            try:
                return serial_address in device.get('DEVNAME')
            except BaseException:
                return False

        context = _pyudev.Context()
        for device in context.list_devices(subsystem=subsystem):
            if _device_has_serial(device, serial_address):
                return True

        return False

    def have_admin_rights():
        """"Check if the process has Administrator rights"""
        try:
            return os.getuid() == 0
        except AttributeError as e:
            raise AdminStateUnknownError from e


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
        cmd_list[index] = ord('1' if on else '0')
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
    if isinstance(config["usb_port"], list):
        ports = config["usb_port"]
    else:
        ports = [config["usb_port"]]

    with xmlrpc.client.ServerProxy(uri=f"http://{config['ip']}:{config['tcp_port']}/",
                                   allow_none=True, transport=None,
                                   encoding=None, verbose=False,
                                   use_datetime=False, use_builtin_types=False,
                                   headers=(), context=None) as proxy:
        for port in ports:
            logging.debug(f'Power down USB port: {port}')
            proxy.set_usb_power(port, False)

        sleep(config['replug_delay'])

        for port in ports:
            logging.debug(f'Power up USB port: {port}')
            proxy.set_usb_power(port, True)


def active_hub_server_set_usb_power(config, on):
    if isinstance(config["usb_port"], list):
        ports = config["usb_port"]
    else:
        ports = [config["usb_port"]]

    with xmlrpc.client.ServerProxy(uri=f"http://{config['ip']}:{config['tcp_port']}/",
                                   allow_none=True, transport=None,
                                   encoding=None, verbose=False,
                                   use_datetime=False, use_builtin_types=False,
                                   headers=(), context=None) as proxy:

        for port in ports:
            proxy.set_usb_power(port, on)


def print_thread_stack_trace():
    try:
        logging.debug("Printing stack trace for each thread:")
        for thread_id, thread_obj in threading._active.items():
            stack = sys._current_frames().get(thread_id)
            if stack is not None:
                logging.debug(f"Thread ID: {thread_id}, Thread Name: {thread_obj.name}")
                logging.debug(traceback.extract_stack(stack))
    except RuntimeError as e:
        # threading._active dictionary can change size during iteration
        logging.debug(e)


def exit_if_admin():
    """Exit program if running as Administrator"""
    if have_admin_rights():
        sys.exit("Administrator rights are not required to run this script!")


def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    mem_usage = mem_info.rss / (1024 ** 2)
    logging.debug(f"Memory usage: {mem_usage:.2f} MB")


def extract_wid_testcases_to_csv(log_dir: Path = None):

    # Example log block format:
    # BEGIN OnImplicitSend:
    # wid: 35
    # test_case_name: GAP/ADV/BV-01-C
    # ...
    # END OnImplicitSend

    target_log_dir = log_dir if log_dir else LOG_DIR

    profile_wid_map = defaultdict(lambda: defaultdict(set))

    for log_file in target_log_dir.rglob("*.log"):
        logging.debug(f"Processing log file: {log_file}")
        try:
            with log_file.open(encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            logging.warning(f"Failed to read {log_file}: {e}")
            continue

        # Track wheter inside an OnImplicitSend block
        in_implicit_send_block = False
        wid = None
        test_case_name = None

        for line in lines:
            stripped = line.strip()

            # Detect start of a new block
            if not in_implicit_send_block and stripped.startswith("BEGIN OnImplicitSend:"):
                in_implicit_send_block = True
                wid = None
                test_case_name = None

            elif in_implicit_send_block:
                # Match and extractWID and TC fields
                wid_match = WID_REGEX.match(stripped)
                tc_name_match = TC_NAME_REGEX.match(stripped)

                if wid_match:
                    wid = wid_match.group(1)
                elif tc_name_match:
                    test_case_name = tc_name_match.group(1)
                elif stripped == "END OnImplicitSend":
                    # End of block - store data if complete
                    if wid and test_case_name:
                        if '/' in test_case_name:
                            profile = test_case_name.split('/')[0]
                        else:
                            profile = "UNKNOWN"
                            logging.warning(f"Missing profile prefix in test_case_name: '{test_case_name}'")

                        profile_wid_map[profile][wid].add(test_case_name)
                    else:
                        logging.error(
                            "INCOMPLETE BLOCK:\n"
                            f"  File           : {log_file.name}\n"
                            f"  WID            : {wid!r}\n"
                            f"  TestCase Name  : {test_case_name!r}"
                        )
                    in_implicit_send_block = False
                    wid = None
                    test_case_name = None

    # Output results to CSV grouped by profile and wid
    OUTPUT_CSV_PATH = Path(FILE_PATHS['WID_USE_CSV_FILE'])
    with OUTPUT_CSV_PATH.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for profile in sorted(profile_wid_map.keys()):
            writer.writerow([f'{profile}'])
            for wid in sorted(profile_wid_map[profile], key=lambda x: int(x)):
                testcases = sorted(profile_wid_map[profile][wid])
                testcases_combined = " ".join(testcases)
                writer.writerow([wid, testcases_combined])

    print(f"WID usage report saved to: {OUTPUT_CSV_PATH.resolve()}")


Sep = re.compile(r'[,\s;|]+')


def load_wid_report() -> dict[tuple[str, str], list[str]]:
    """
    Parse a 'sectioned' CSV where:
      - A row with a single non-empty field denotes a SERVICE header (e.g., 'GAP').
      - Subsequent rows belong to that service and look like: wid_number, testcases...
        (testcases may be separated by spaces/commas/semicolons/pipes)
      - A new SERVICE header starts a new section.

    Returns:
      mapping[(SERVICE_UPPER, WID_STR)] -> [testcase, ...]
    """
    mapping: dict[tuple[str, str], list[str]] = defaultdict(list)
    current_service: str = "<UNSET>"
    OUTPUT_CSV_PATH = Path(FILE_PATHS['WID_USE_CSV_FILE'])

    if not OUTPUT_CSV_PATH.exists():
        raise FileNotFoundError(f"WID report not found: {OUTPUT_CSV_PATH}")

    with open(OUTPUT_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for raw in reader:
            row = [col.strip() for col in raw if col is not None]
            if not row or all(col == "" for col in row):
                continue

            if len([c for c in row if c]) == 1 and not row[0].isdigit():
                current_service = row[0].upper()
                continue

            if current_service == "<UNSET>":
                raise RuntimeError(f"Data row found before any service header: {row}")

            wid = row[0].strip()
            tcs_field = row[1].strip() if len(row) > 1 else ""
            testcases = [t for t in Sep.split(tcs_field) if t]
            if testcases:
                mapping[(current_service, wid)].extend(testcases)

    return mapping


def get_tc_from_wid(service: str, wid: int, mapping: dict[tuple[str, str], list[str]]) -> list[str]:
    """
    Return testcases for (service, wid). Service match is case-insensitive.
    """
    return mapping.get((service.upper(), str(wid)), [])


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
