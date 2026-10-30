#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Codecoup.
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
import socket
import sys
from abc import ABC, abstractmethod


class BTPTransport(ABC):
    """Byte stream between AutoPTS and the IUT."""

    @abstractmethod
    def open(self) -> None:
        pass

    @abstractmethod
    def accept(self, timeout: float | None = 10.0) -> None:
        """Wait until the IUT is connected."""

    @abstractmethod
    def recv(self, size: int, timeout: float | None) -> bytes:
        """Return up to size bytes.

        Raises TimeoutError if nothing arrived and ConnectionError
        if the connection is closed.
        """

    @abstractmethod
    def send(self, data: bytes) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class _SocketTransport(BTPTransport):
    def __init__(self) -> None:
        self.conn: socket.socket | None = None

    def recv(self, size: int, timeout: float | None) -> bytes:
        if self.conn.gettimeout() != timeout:
            self.conn.settimeout(timeout)
        data = self.conn.recv(size)
        if not data:
            raise ConnectionError("BTP connection closed")
        return data

    def send(self, data: bytes) -> None:
        self.conn.sendall(data)

    def close(self) -> None:
        if self.conn is None:
            return
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError as e:
            logging.exception(e)
        self.conn.close()
        self.conn = None


class SocketServerTransport(_SocketTransport):
    """Socket the IUT connects to.

    UNIX socket at address, on Windows TCP socket at port (0 - any free).
    """

    def __init__(self, address: str, port: int = 0) -> None:
        super().__init__()
        self.address = address
        self.port = port
        self.sock: socket.socket | None = None

    def open(self) -> None:
        if sys.platform == "win32":
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((socket.gethostname(), self.port))
        else:
            if os.path.exists(self.address):
                os.remove(self.address)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.bind(self.address)

        self.sock.listen(1)

    def accept(self, timeout: float | None = 10.0) -> None:
        self.sock.settimeout(timeout)
        self.conn, _ = self.sock.accept()

    def close(self) -> None:
        super().close()
        if self.sock is not None:
            self.sock.close()
            self.sock = None


class SocketClientTransport(_SocketTransport):
    """TCP connection to the IUT listening at host:port."""

    def __init__(self, host: str, port: int) -> None:
        super().__init__()
        self.host = host
        self.port = port

    def open(self) -> None:
        pass

    def accept(self, timeout: float | None = 10.0) -> None:
        self.conn = socket.create_connection((self.host, self.port), timeout)
