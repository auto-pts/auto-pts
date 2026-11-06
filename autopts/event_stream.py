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

"""Events from autoptsserver to the client.

The client opens 'GET /events' on the XML-RPC port of the server and keeps
the connection open. The server pushes the PTS callbacks (WIDs, logs,
results of asynchronous methods) over it as JSON lines:

    {"method": "set_result", "args": ["run_test_case", "PASS"]}

so the client does not need its own XML-RPC server.
"""

import json
import logging
import socket
import threading
import time
from collections.abc import Callable
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

EVENTS_PATH = '/events'

log = logging.debug


class EventStream:
    """Server side of the event stream, used as the PTS callback.

    Args:
        send_timeout: seconds after which a client that does not read
            the events is disconnected
    """

    def __init__(self, send_timeout: float = 10.0) -> None:
        self._send_timeout: float = send_timeout
        self._conn: socket.socket | None = None
        self._lock = threading.Lock()

    def attach(self, conn: socket.socket) -> None:
        """Pushes the next events over conn, replacing the previous client."""
        conn.settimeout(self._send_timeout)
        with self._lock:
            self._close()
            self._conn = conn
        log(f'Event stream connected: {conn.getpeername()}')

    def owns(self, conn: socket.socket) -> bool:
        return conn is self._conn

    def close(self) -> None:
        with self._lock:
            self._close()

    def _close(self) -> None:
        if self._conn is None:
            return
        try:
            self._conn.close()
        except OSError as e:
            logging.exception(e)
        self._conn = None

    def _push(self, method: str, *args) -> bool:
        data = (json.dumps({'method': method, 'args': args}, default=str) + '\n').encode()
        with self._lock:
            if self._conn is None:
                log(f'No event stream, dropping {method} {args}')
                return False
            try:
                self._conn.sendall(data)
                return True
            except OSError as e:
                log(f'Event stream lost: {e!r}, dropping {method} {args}')
                self._close()
                return False

    def log(self, log_type, logtype_string, log_time, log_message, test_case_name) -> None:
        self._push('log', log_type, logtype_string, log_time, log_message, test_case_name)

    def on_implicit_send(self, project_name, wid, test_case_name, description, style) -> str:
        if not self._push('on_implicit_send', project_name, wid, test_case_name, description, style):
            return 'Cancel'
        # The client responds with set_wid_response()
        return 'WAIT'

    def set_result(self, method_name: str, result) -> None:
        self._push('set_result', method_name, result)


class _RequestHandler(SimpleXMLRPCRequestHandler):
    def do_GET(self) -> None:
        if self.path != EVENTS_PATH:
            self.report_404()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson')
        self.end_headers()
        self.wfile.flush()
        self.server.event_stream.attach(self.connection)
        self.close_connection = True


class EventStreamXMLRPCServer(SimpleXMLRPCServer):
    """XML-RPC server that also serves the event stream.

    Args:
        addr: (host, port) to listen at
        event_stream: where 'GET /events' connections are attached
    """

    def __init__(self, addr: tuple[str, int], event_stream: EventStream, **kwargs) -> None:
        self.event_stream: EventStream = event_stream
        super().__init__(addr, requestHandler=_RequestHandler, **kwargs)

    def shutdown_request(self, request) -> None:
        # Keep the event stream connection open
        if not self.event_stream.owns(request):
            super().shutdown_request(request)


class EventStreamReader(threading.Thread):
    """Client side of the event stream. Calls the methods of callback for
    the received events and reconnects if the stream is lost.

    Args:
        host: autoptsserver address
        port: autoptsserver XML-RPC port
        callback: object with the PTS callback methods (log,
            on_implicit_send, set_result)
        on_wid_response: called with the response of
            callback.on_implicit_send() other than 'WAIT'
        name: thread name
    """

    RECONNECT_INTERVAL = 1.0

    def __init__(self, host: str, port: int, callback, on_wid_response: Callable[[str], None],
                 name: str) -> None:
        super().__init__(name=name, daemon=True)
        self.host: str = host
        self.port: int = port
        self.callback = callback
        self.on_wid_response: Callable[[str], None] = on_wid_response
        self.connected = threading.Event()
        self.end = False

    def stop(self) -> None:
        self.end = True

    def run(self) -> None:
        while not self.end:
            try:
                self._read_events(self._connect())
            except (OSError, ValueError) as e:
                log(f'Event stream from {self.host}:{self.port} lost: {e!r}')
            self.connected.clear()
            if not self.end:
                time.sleep(self.RECONNECT_INTERVAL)

    def _connect(self) -> socket.socket:
        sock = socket.create_connection((self.host, self.port), timeout=10)
        sock.sendall(f'GET {EVENTS_PATH} HTTP/1.0\r\nHost: {self.host}\r\n\r\n'.encode())

        buf = b''
        while b'\r\n\r\n' not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError('Event stream closed')
            buf += chunk
        head, self._buf = buf.split(b'\r\n\r\n', 1)
        if b' 200 ' not in head.split(b'\r\n')[0]:
            raise ConnectionError(f'Event stream refused: {head!r}')

        # Short timeout to notice stop()
        sock.settimeout(1.0)
        self.connected.set()
        log(f'Event stream from {self.host}:{self.port} connected')
        return sock

    def _read_events(self, sock: socket.socket) -> None:
        with sock:
            while not self.end:
                while b'\n' in self._buf:
                    line, self._buf = self._buf.split(b'\n', 1)
                    self._handle(json.loads(line))
                try:
                    chunk = sock.recv(65536)
                except TimeoutError:
                    continue
                if not chunk:
                    raise ConnectionError('Event stream closed')
                self._buf += chunk

    def _handle(self, event: dict) -> None:
        method = event['method']
        if method not in ('log', 'on_implicit_send', 'set_result'):
            logging.error(f'Unknown event {event}')
            return

        try:
            result = getattr(self.callback, method)(*event['args'])
            if method == 'on_implicit_send' and result != 'WAIT':
                self.on_wid_response(result)
        except Exception as e:
            logging.exception(e)
