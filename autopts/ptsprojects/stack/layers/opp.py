#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026 NXP
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

from autopts.ptsprojects.stack.common import wait_for_event


class OppDiscoveredResult:
    """Holds the result of an OPP discovery (BTP_OPP_EV_DISCOVERED)."""

    def __init__(self, rfcomm_channel: int, formats: list):
        """Initialize an OPP discovery result.

        Args:
            rfcomm_channel: RFCOMM channel from Protocol Descriptor List; 0 if not found.
            formats: List of bt_opp_format values from SupportedFormatsList attribute.
        """
        self.rfcomm_channel = rfcomm_channel
        self.formats = formats


class OPP:
    """Stack state for the OPP (Object Push Profile) service.

    Tracks transport and session state for both client and server roles,
    as well as SDP discovery results.
    """

    def __init__(self):
        # Discovery result (single slot; replaced on each discovery)
        self._discovered: OppDiscoveredResult | None = None

        # Client transport state (boolean flags)
        self._client_transport_connected: bool = False
        self._client_transport_disconnected: bool = False

        # Client OBEX session state
        self._client_connected: tuple | None = None   # (rsp_code, version, mopl)
        self._client_disconnected: int | None = None  # rsp_code

        # Client operation responses
        self._client_push_rsp: int | None = None
        self._client_pull_bcard_data: tuple | None = None  # (rsp_code, body)
        self._client_abort_rsp: int | None = None

        # Server transport state (boolean flags)
        self._server_transport_connected: bool = False
        self._server_transport_disconnected: bool = False

        # Server OBEX session state
        self._server_connected: tuple | None = None  # (version, mopl)
        self._server_disconnected: bool = False

        # Server operation queues
        self._server_push_requests: list = []
        self._server_pull_bcard_requests: int = 0  # event count
        self._server_abort_requests: int = 0        # event count

    def discovered(self, rfcomm_channel: int, formats: list) -> None:
        """Record an OPP discovery result.

        Args:
            rfcomm_channel: RFCOMM channel from Protocol Descriptor List.
            formats: List of supported object format codes.
        """
        self._discovered = OppDiscoveredResult(rfcomm_channel, formats)

    def client_transport_connected(self) -> None:
        """Record a client transport connected event."""
        self._client_transport_connected = True
        self._client_transport_disconnected = False

    def client_transport_disconnected(self) -> None:
        """Record a client transport disconnected event."""
        self._client_transport_connected = False
        self._client_connected = None
        self._client_transport_disconnected = True

    def client_connected(self, rsp_code: int, version: int, mopl: int) -> None:
        """Record a client OBEX session connected event.

        Args:
            rsp_code: OBEX response code from the server.
            version: OBEX version reported by the server.
            mopl: Maximum OBEX packet length of the server.
        """
        self._client_connected = (rsp_code, version, mopl)

    def client_disconnected(self, rsp_code: int) -> None:
        """Record a client OBEX session disconnected event.

        Args:
            rsp_code: OBEX response code.
        """
        self._client_connected = None
        self._client_disconnected = rsp_code

    def client_push(self, rsp_code: int) -> None:
        """Record a client push (PUT) response event.

        Args:
            rsp_code: OBEX response code from the server.
        """
        self._client_push_rsp = rsp_code

    def client_pull_bcard(self, rsp_code: int, body: bytes) -> None:
        """Record a client pull business card (GET) response event.

        Args:
            rsp_code: OBEX response code from the server.
            body: Received body data bytes.
        """
        self._client_pull_bcard_data = (rsp_code, body)

    def client_abort(self, rsp_code: int) -> None:
        """Record a client abort response event.

        Args:
            rsp_code: OBEX response code from the server.
        """
        self._client_abort_rsp = rsp_code

    def server_transport_connected(self) -> None:
        """Record a server transport connected event."""
        self._server_transport_connected = True
        self._server_transport_disconnected = False

    def server_transport_disconnected(self) -> None:
        """Record a server transport disconnected event."""
        self._server_transport_connected = False
        self._server_connected = None
        self._server_transport_disconnected = True

    def server_connected(self, version: int, mopl: int) -> None:
        """Record a server OBEX session connected event.

        Args:
            version: OBEX version requested by the client.
            mopl: Maximum OBEX packet length proposed by the client.
        """
        self._server_connected = (version, mopl)

    def server_disconnected(self) -> None:
        """Record a server OBEX session disconnected event."""
        self._server_connected = None
        self._server_disconnected = True

    def server_push(self, total_length: int, is_final: int,
                    name: bytes, mime_type: bytes, body: bytes) -> None:
        """Record a server push (PUT) request event.

        Args:
            total_length: Total object length reported in OBEX Length header.
            is_final: 1 if this is the End-of-Body packet, 0 otherwise.
            name: Object name bytes.
            mime_type: MIME type bytes.
            body: Body data bytes for this packet.
        """
        self._server_push_requests.append(
            (total_length, is_final, name, mime_type, body))

    def server_pull_bcard(self) -> None:
        """Record a server pull business card (GET) request event."""
        self._server_pull_bcard_requests += 1

    def server_abort(self) -> None:
        """Record a server abort request event."""
        self._server_abort_requests += 1

    def is_discovered(self) -> bool:
        """Return True if a discovery result has been received."""
        return self._discovered is not None

    def pop_discovered(self) -> OppDiscoveredResult | None:
        """Return and clear the discovery result.

        Returns:
            OppDiscoveredResult if available, None otherwise.
        """
        result = self._discovered
        self._discovered = None
        return result

    def is_client_transport_connected(self) -> bool:
        """Return True if the client transport is connected."""
        return self._client_transport_connected

    def is_client_transport_disconnected(self) -> bool:
        """Return True if the client transport has been disconnected."""
        return self._client_transport_disconnected

    def is_client_connected(self) -> bool:
        """Return True if the client OBEX session is connected."""
        return self._client_connected is not None

    def is_client_disconnected(self) -> bool:
        """Return True if the client OBEX session has been disconnected."""
        return self._client_disconnected is not None

    def has_client_push(self) -> bool:
        """Return True if a client push response has been received."""
        return self._client_push_rsp is not None

    def pop_client_push(self) -> int | None:
        """Return and clear the client push response code.

        Returns:
            OBEX response code int, or None if no entry exists.
        """
        result = self._client_push_rsp
        self._client_push_rsp = None
        return result

    def has_client_pull_bcard(self) -> bool:
        """Return True if a client pull business card response has been received."""
        return self._client_pull_bcard_data is not None

    def pop_client_pull_bcard(self) -> tuple | None:
        """Return and clear the client pull business card response.

        Returns:
            Tuple (rsp_code, body) or None if no entry exists.
        """
        result = self._client_pull_bcard_data
        self._client_pull_bcard_data = None
        return result

    def has_client_abort(self) -> bool:
        """Return True if a client abort response has been received."""
        return self._client_abort_rsp is not None

    def pop_client_abort(self) -> int | None:
        """Return and clear the client abort response code.

        Returns:
            OBEX response code int, or None if no entry exists.
        """
        result = self._client_abort_rsp
        self._client_abort_rsp = None
        return result

    def is_server_transport_connected(self) -> bool:
        """Return True if the server transport is connected."""
        return self._server_transport_connected

    def is_server_transport_disconnected(self) -> bool:
        """Return True if the server transport has been disconnected."""
        return self._server_transport_disconnected

    def is_server_connected(self) -> bool:
        """Return True if the server OBEX session is connected."""
        return self._server_connected is not None

    def has_server_disconnected(self) -> bool:
        """Return True if a server OBEX session disconnected event has been received."""
        return self._server_disconnected

    def pop_server_disconnected(self) -> bool:
        """Return and clear the server disconnected flag.

        Returns:
            True if a disconnected event had been received, False otherwise.
        """
        result = self._server_disconnected
        self._server_disconnected = False
        return result

    def has_server_push(self) -> bool:
        """Return True if at least one server push request has been received."""
        return bool(self._server_push_requests)

    def pop_server_push(self) -> tuple | None:
        """Return and remove the oldest pending server push request.

        Returns:
            Tuple (total_length, is_final, name, mime_type, body),
            or None if no request is pending.
        """
        if self._server_push_requests:
            return self._server_push_requests.pop(0)
        return None

    def has_server_pull_bcard(self) -> bool:
        """Return True if at least one server pull business card request has been received."""
        return self._server_pull_bcard_requests > 0

    def pop_server_pull_bcard(self) -> bool:
        """Consume one server pull business card request.

        Returns:
            True if an event was pending, False otherwise.
        """
        if self._server_pull_bcard_requests > 0:
            self._server_pull_bcard_requests -= 1
            return True
        return False

    def has_server_abort(self) -> bool:
        """Return True if at least one server abort request has been received."""
        return self._server_abort_requests > 0

    def pop_server_abort(self) -> bool:
        """Consume one server abort request.

        Returns:
            True if an event was pending, False otherwise.
        """
        if self._server_abort_requests > 0:
            self._server_abort_requests -= 1
            return True
        return False

    def wait_for_discovered(self, timeout: int = 30) -> OppDiscoveredResult | None:
        """Block until an OPP discovery result is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            OppDiscoveredResult, or None on timeout.
        """
        wait_for_event(timeout, self.is_discovered)
        return self.pop_discovered()

    def wait_for_client_transport_connected(self, timeout: int = 30) -> bool:
        """Block until the client transport connected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if connected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_client_transport_connected)
        return self.is_client_transport_connected()

    def wait_for_client_transport_disconnected(self, timeout: int = 30) -> bool:
        """Block until the client transport disconnected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if disconnected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_client_transport_disconnected)
        return self.is_client_transport_disconnected()

    def wait_for_client_connected(self, timeout: int = 30) -> bool:
        """Block until the client OBEX session connected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if connected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_client_connected)
        return self.is_client_connected()

    def wait_for_client_disconnected(self, timeout: int = 30) -> bool:
        """Block until the client OBEX session disconnected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if disconnected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_client_disconnected)
        return self.is_client_disconnected()

    def wait_for_client_push(self, timeout: int = 30) -> int | None:
        """Block until a client push response event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            OBEX response code int, or None on timeout.
        """
        wait_for_event(timeout, self.has_client_push)
        return self.pop_client_push()

    def wait_for_client_pull_bcard(self, timeout: int = 30) -> tuple | None:
        """Block until a client pull business card response event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            Tuple (rsp_code, body), or None on timeout.
        """
        wait_for_event(timeout, self.has_client_pull_bcard)
        return self.pop_client_pull_bcard()

    def wait_for_client_abort(self, timeout: int = 30) -> int | None:
        """Block until a client abort response event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            OBEX response code int, or None on timeout.
        """
        wait_for_event(timeout, self.has_client_abort)
        return self.pop_client_abort()

    def wait_for_server_transport_connected(self, timeout: int = 30) -> bool:
        """Block until the server transport connected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if connected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_server_transport_connected)
        return self.is_server_transport_connected()

    def wait_for_server_transport_disconnected(self, timeout: int = 30) -> bool:
        """Block until the server transport disconnected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if disconnected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_server_transport_disconnected)
        return self.is_server_transport_disconnected()

    def wait_for_server_connected(self, timeout: int = 30) -> bool:
        """Block until the server OBEX session connected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if connected within timeout, False otherwise.
        """
        wait_for_event(timeout, self.is_server_connected)
        return self.is_server_connected()

    def wait_for_server_disconnected(self, timeout: int = 30) -> bool:
        """Block until a server OBEX session disconnected event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if the event arrived, False on timeout.
        """
        wait_for_event(timeout, self.has_server_disconnected)
        return self.pop_server_disconnected()

    def wait_for_server_push(self, timeout: int = 30) -> tuple | None:
        """Block until a server push request event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            Tuple (total_length, is_final, name, mime_type, body),
            or None on timeout.
        """
        wait_for_event(timeout, self.has_server_push)
        return self.pop_server_push()

    def wait_for_server_pull_bcard(self, timeout: int = 30) -> bool:
        """Block until a server pull business card request event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if the event arrived, False on timeout.
        """
        wait_for_event(timeout, self.has_server_pull_bcard)
        return self.pop_server_pull_bcard()

    def wait_for_server_abort(self, timeout: int = 30) -> bool:
        """Block until a server abort request event is received.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            True if the event arrived, False on timeout.
        """
        wait_for_event(timeout, self.has_server_abort)
        return self.pop_server_abort()
