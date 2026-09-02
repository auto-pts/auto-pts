#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Xiaomi Corporation.
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

"""openvela IUT Control Module

This module provides IUT (Implementation Under Test) control for openvela
running on QEMU. It connects to the bttester application via TCP socket
through adb port forwarding.

Architecture:
    auto-pts (Host) <--TCP:9876--> adb forward <--TCP:9876--> bttester (QEMU)
"""

import logging
import socket
import subprocess
import time

from autopts.ptsprojects.stack import Stack, get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.iutctl_common import BTPSocketCli, BTPWorker
from autopts.pybtp.types import BTPInitError

log = logging.debug

openvela = None


def _first(value, default):
    """Unwrap a possibly list-valued CLI argument, falling back to default."""
    if value is None:
        return default
    if isinstance(value, (list, tuple)):
        return value[0] if value else default
    return value


# Default BTP TCP port used by bttester
BTP_TCP_PORT = 9876


class OpenVelaCtl:
    """openvela IUT Control Class

    This class manages the connection to openvela bttester running in QEMU.
    It uses TCP socket connection through adb port forwarding.
    """

    def __init__(self, args):
        """Constructor.

        Args:
            args: Command line arguments containing:
                - btp_tcp_port: TCP port for BTP connection (default: 9876)
                - btp_tcp_ip: TCP host for BTP connection (default: 127.0.0.1)
                - adb_device: ADB device serial (optional)
        """
        log(f"{self.__class__}.{self.__init__.__name__}")

        # Use standard auto-pts parameter names
        # --btp-tcp-port/--btp-tcp-ip are declared with nargs='+', so passing
        # them explicitly yields a list. Unwrap it, otherwise the value ends up
        # formatted as "tcp:[9876]" and adb rejects it.
        self.btp_tcp_port = _first(getattr(args, 'btp_tcp_port', None), BTP_TCP_PORT)
        self.btp_tcp_host = _first(getattr(args, 'btp_tcp_ip', None), '127.0.0.1')
        self.adb_device = getattr(args, 'adb_device', None)

        self.is_running = False
        self.socket_srv = None
        self.btp_socket = None
        self.test_case = None
        self._adb_forward_setup = False

        self.iut_mode = "btp_tcp_client"

        # btp._get_stack() resolves the stack through get_iut().get_stack(),
        # so every IUT control class has to own its Stack instance the way
        # ptsprojects.iutctl.IutCtl does.
        self.stack = Stack()
        self.stack.synch_init()

    def _setup_adb_forward(self):
        """Setup adb port forwarding for BTP TCP connection."""
        # Always re-setup to ensure the forward is active
        log(f"Setting up adb forward tcp:{self.btp_tcp_port} tcp:{self.btp_tcp_port}")

        cmd = ['adb']
        if self.adb_device:
            cmd.extend(['-s', self.adb_device])
        cmd.extend(['forward', f'tcp:{self.btp_tcp_port}', f'tcp:{self.btp_tcp_port}'])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            self._adb_forward_setup = True
            log("adb forward setup successful")
        except subprocess.CalledProcessError as e:
            log(f"adb forward failed: {e.stderr.decode()}")
            raise Exception(f"Failed to setup adb forward: {e}") from e

    def _remove_adb_forward(self):
        """Remove adb port forwarding."""
        if not self._adb_forward_setup:
            return

        log(f"Removing adb forward tcp:{self.btp_tcp_port}")

        cmd = ['adb']
        if self.adb_device:
            cmd.extend(['-s', self.adb_device])
        cmd.extend(['forward', '--remove', f'tcp:{self.btp_tcp_port}'])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Ignore errors when removing forward

        self._adb_forward_setup = False

    def start(self, test_case):
        """Start the IUT for a test case.

        Args:
            test_case: The test case object
        """
        log(">>> OpenVelaCtl.start called")

        self.test_case = test_case

        # Setup adb port forwarding (idempotent)
        self._setup_adb_forward()

        # Create TCP socket connection to bttester
        log(">>> OpenVelaCtl.start: creating BTPSocketCliTcp")
        self.socket_srv = BTPSocketCliTcp(test_case.log_dir)
        self.socket_srv.open((self.btp_tcp_host, self.btp_tcp_port))
        self.btp_socket = BTPWorker(self.socket_srv)

        # Connect to bttester
        log(f">>> OpenVelaCtl.start: connecting to {self.btp_tcp_host}:{self.btp_tcp_port}")
        self.btp_socket.accept(timeout=30.0)
        log(">>> OpenVelaCtl.start: connected OK")

        self.is_running = True

    def stop(self):
        """Stop the IUT (disconnect TCP, keep bttester running)."""
        log(f"{self.__class__}.{self.stop.__name__}")

        if not self.is_running:
            return

        # Close BTP socket (bttester stays running, waits for new connection)
        if self.btp_socket:
            self.btp_socket.close()
            self.btp_socket = None

        if self.socket_srv:
            self.socket_srv.close()
            self.socket_srv = None

        self.is_running = False

    def wait_iut_ready_event(self, reset=True):
        """Wait for IUT ready event.

        Args:
            reset: Whether to reset the IUT (restart bttester)
        """
        log(f">>> OpenVelaCtl.wait_iut_ready_event reset={reset}")

        stack = get_stack()

        if reset:
            log(">>> OpenVelaCtl.wait_iut_ready_event: stop+start")
            self.stop()
            self.start(self.test_case)

        # Wait for IUT ready event
        log(">>> OpenVelaCtl.wait_iut_ready_event: waiting for IUT ready ev...")
        ev = stack.core.wait_iut_ready_ev(30)
        stack.core.event_queues[defs.BTP_CORE_EV_IUT_READY].clear()

        if not ev:
            log(">>> OpenVelaCtl.wait_iut_ready_event: TIMEOUT - no IUT ready event!")
            self.stop()
            raise BTPInitError('IUT ready event NOT received!')

        log(">>> OpenVelaCtl.wait_iut_ready_event: IUT ready event received OK")

    def get_supported_svcs(self):
        """Get supported BTP services."""
        btp.read_supp_svcs()

    def get_stack(self):
        """Return the Stack owned by this IUT."""
        return self.stack

    def cleanup_stack(self):
        """Reset the Stack between test cases."""
        self.stack.cleanup()


class BTPSocketCliTcp(BTPSocketCli):
    """BTP Socket Client using TCP connection.

    This extends BTPSocketCli to use TCP instead of Unix domain socket.
    """

    def __init__(self, log_dir=None):
        super().__init__(log_dir)
        self._connected = False

    def open(self, addr):
        """Open connection to the specified address.

        Args:
            addr: Tuple of (host, port)
        """
        self.addr = addr
        log(f"BTPSocketCliTcp.open addr={addr}")

    def accept(self, timeout=10.0):
        """Connect to the BTP server (bttester).

        Args:
            timeout: Connection timeout in seconds
        """
        log(f"BTPSocketCliTcp.accept timeout={timeout}")

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(timeout)

        # Retry connection with backoff
        max_retries = 10
        retry_delay = 0.5

        for i in range(max_retries):
            error = self._try_connect()
            if error is None:
                return

            log(f"Connection attempt {i + 1}/{max_retries} failed: {error}")
            if i < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff

        raise Exception(f"Failed to connect to {self.addr} after {max_retries} attempts")

    def _try_connect(self):
        """Try a single TCP connection attempt.

        Returns:
            The exception raised on failure, or None on success.
        """
        try:
            self.conn.connect(self.addr)
        except (ConnectionRefusedError, TimeoutError) as e:
            return e

        self._connected = True
        log(f"Connected to {self.addr}")
        self.conn.settimeout(None)
        return None

    def close(self):
        """Close the TCP connection."""
        log("BTPSocketCliTcp.close")

        if self.conn and self._connected:
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.conn.close()
            except OSError:
                pass

        self.conn = None
        self._connected = False

        if self.log_file:
            self.log_file.close()
            self.log_file = None


def get_iut():
    """Get the openvela IUT instance."""
    return openvela


def init(args):
    """Initialize the openvela IUT.

    Args:
        args: Command line arguments
    """
    global openvela

    log("openvela IUT init")
    openvela = OpenVelaCtl(args)


def cleanup():
    """Cleanup the openvela IUT."""
    global openvela

    if openvela:
        openvela.stop()
        openvela._remove_adb_forward()
        openvela = None
