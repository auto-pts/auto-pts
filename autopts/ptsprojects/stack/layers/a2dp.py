#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, NXP.
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
from dataclasses import dataclass

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp.types import AVDTPServiceCategory


@dataclass
class A2DP_ENDPOINT:
    ep_id: int
    media_type: int = 0
    tsep: int = 0
    in_use: int = 0
    capabilities: list = None  # New field for service category capabilities


@dataclass
class A2DP_STREAM:
    stream_id: int
    state: str
    delay_report: int
    codec_ie: bytes
    received_data: list
    stream_sent_flag: bool


class A2DP_CONNECTION:
    def __init__(self, addr):
        self.addr = addr
        self.endpoints = []
        self.streams = {}
        self.config_request = None
        self.reconfig_request = None
        self.delay_report_value = None
        self.discover_state = False

    def add_endpoint(self, ep_id, media_type, tsep, in_use, cap=None):
        """Add discovered endpoint"""
        endpoint = A2DP_ENDPOINT(
            ep_id=ep_id,
            media_type=media_type,
            tsep=tsep,
            in_use=in_use,
            capabilities=cap
        )
        if not any(ep.ep_id == ep_id for ep in self.endpoints):
            self.endpoints.append(endpoint)

    def get_endpoint(self, ep_id):
        """Get endpoint by ID"""
        return next((ep for ep in self.endpoints if ep.ep_id == ep_id), None)

    def get_endpoints(self):
        """Get all endpoints"""
        return self.endpoints

    def clear_endpoints(self):
        """Clear all endpoints"""
        self.endpoints = []

    def set_discover_state(self, state):
        """Set discover state"""
        self.discover_state = state

    def get_discover_state(self):
        """Get discover state"""
        return self.discover_state

    def set_capability(self, ep_id, capability: list):
        """set capability to endpoint"""
        endpoint = self.get_endpoint(ep_id)
        if endpoint:
            endpoint.capabilities = capability

    def get_capability(self, ep_id, service_cap):
        """Get media type of endpoint"""
        endpoint = self.get_endpoint(ep_id)
        if endpoint:
            result = None
            for cap in endpoint.capabilities:
                if cap.get('service_category') == service_cap:
                    result = cap
                    break
            return result
        return None

    def add_stream(self, stream_id, state='idle', delay_report=0, codec_ie=b'', recv_data=None, sent_flag=False):
        """Add or update stream"""
        self.streams[stream_id] = A2DP_STREAM(
            stream_id=stream_id,
            state=state,
            delay_report=delay_report,
            codec_ie=codec_ie,
            received_data=recv_data,
            stream_sent_flag=sent_flag
        )

    def get_stream(self, stream_id):
        """Get stream by ID"""
        return self.streams.get(stream_id)

    def remove_stream(self, stream_id):
        """Remove stream"""
        self.streams.pop(stream_id, None)

    def get_stream_state(self, stream_id):
        """Get stream state"""
        stream = self.get_stream(stream_id)
        return stream.state if stream else None

    def set_stream_state(self, stream_id, state):
        """Set stream state"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.state = state

    def wait_for_stream_state(self, stream_id, expected_state, timeout=10):
        """Wait for stream to reach expected state"""
        wait_for_event(
            timeout,
            lambda: (self.get_stream(stream_id) is not None) and
                    self.get_stream_state(stream_id) == expected_state
        )
        return (self.get_stream(stream_id) is not None) and self.get_stream_state(stream_id) == expected_state

    def get_config_request(self):
        """Get config request"""
        return self.config_request

    def set_reconfig_request(self, stream_id, delay_report, codec_ie):
        """Store reconfig request"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.delay_report = delay_report
            stream.codec_ie = codec_ie

    def get_reconfig_request(self):
        """Get reconfig request"""
        return self.reconfig_request

    def set_delay_report(self, stream_id, delay):
        """Set delay report value"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.delay_report = delay

    def get_delay_report(self, stream_id):
        """Get delay report value"""
        stream = self.get_stream(stream_id)
        return stream.delay_report if stream else None

    def add_received_data(self, stream_id, seq_num, timestamp, data):
        """Add received stream data"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.received_data.append({
                'seq_num': seq_num,
                'timestamp': timestamp,
                'data': data
            })

    def get_received_data(self, stream_id):
        """Get all received data"""
        stream = self.get_stream(stream_id)
        if stream:
            return stream.received_data
        return []

    def clear_received_data(self, stream_id):
        """Clear received data"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.received_data = []

    def set_stream_sent(self, stream_id):
        """Mark stream as sent"""
        stream = self.get_stream(stream_id)
        if stream:
            stream.stream_sent_flag = True

    def is_stream_sent(self, is_stream_sent):
        """Check if stream was sent"""
        stream = self.get_stream(is_stream_sent)
        if stream:
            return self.stream_sent_flag
        return False

    def wait_for_stream_sent(self, stream_id, timeout=10):
        """Wait for stream sent event"""
        wait_for_event(
            timeout,
            lambda: self.get_stream_state(stream_id).stream_sent_flag
        )
        return self.get_stream_state(stream_id).stream_sent_flag


class A2DP:
    def __init__(self):
        self.connections = {}
        self.mmi_round = {}

    def increase_mmi_round(self, key):
        if key not in self.mmi_round:
            self.mmi_round[key] = 1
        else:
            self.mmi_round[key] += 1

    def get_mmi_round(self, key):
        if key in self.mmi_round:
            return self.mmi_round[key]
        return 0

    def add_connection(self, addr):
        """Add A2DP connection"""
        if addr not in self.connections:
            self.connections[addr] = A2DP_CONNECTION(addr=addr)

    def remove_connection(self, addr):
        """Remove A2DP connection"""
        self.connections.pop(addr, None)

    def get_connection(self, addr):
        """Get connection by address"""
        return self.connections.get(addr)

    def is_connected(self, addr):
        """Check if connected"""
        return self.get_connection(addr) is not None

    def wait_for_connection(self, addr, timeout=10):
        """Wait for connection"""
        conn = self.get_connection(addr)
        if conn:
            return True

        wait_for_event(timeout, lambda: self.get_connection(addr))
        return self.get_connection(addr) is not None

    def wait_for_disconnection(self, addr, timeout=10):
        """Wait for disconnection"""
        conn = self.get_connection(addr)
        if not conn:
            return True

        wait_for_event(timeout, lambda: not self.get_connection(addr))
        return self.get_connection(addr) is None

    def add_endpoint(self, addr, ep_id, media_type, tsep, in_use, capabilities=None):
        """Add endpoint to connection"""
        conn = self.get_connection(addr)
        if conn:
            conn.add_endpoint(ep_id, media_type, tsep, in_use, cap=capabilities)

    def set_discover_state(self, addr, state):
        """Set discover state"""
        conn = self.get_connection(addr)
        if conn:
            conn.set_discover_state(state)

    def get_discover_state(self, addr):
        """Get discover state"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_discover_state()
        return None

    def set_cap_to_endpoint(self, addr, ep_id, capability):
        """Set capability to endpoint"""
        conn = self.get_connection(addr)
        if conn:
            conn.set_capability(ep_id, capability)

    def get_service_cap(self, addr, ep_id, service_cap=AVDTPServiceCategory.MEDIA_CODEC):
        """Get service capability from endpoint"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_capability(ep_id, service_cap)
        return None

    def get_endpoint(self, addr, ep_id):
        """Get endpoint"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_endpoint(ep_id)
        return None

    def get_endpoints(self, addr):
        """Get all endpoints"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_endpoints()
        return []

    def wait_for_endpoint_count(self, addr, expected_count, timeout=10):
        """Wait for expected number of endpoints"""
        wait_for_event(timeout, lambda: len(self.get_endpoints(addr)) == expected_count)
        return len(self.get_endpoints(addr)) == expected_count

    def add_stream(self, addr, stream_id, state='idle', delay_report=0, codec_ie=b''):
        """Add stream to connection"""
        conn = self.get_connection(addr)
        if conn:
            conn.add_stream(stream_id, state, delay_report, codec_ie)

    def get_stream(self, addr, stream_id):
        """Get stream"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_stream(stream_id)
        return None

    def remove_stream(self, addr, stream_id):
        """Remove stream"""
        conn = self.get_connection(addr)
        if conn:
            conn.remove_stream(stream_id)

    def get_stream_state(self, addr, stream_id):
        """Get stream state"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_stream_state(stream_id)
        return None

    def set_stream_state(self, addr, stream_id, state):
        """Set stream state"""
        conn = self.get_connection(addr)
        if conn:
            conn.set_stream_state(stream_id, state)

    def wait_for_stream_state(self, addr, stream_id, expected_state, timeout=10):
        """Wait for stream state"""
        conn = self.get_connection(addr)
        if conn:
            return conn.wait_for_stream_state(stream_id, expected_state, timeout)
        return False

    def set_config_request(self, addr, result, stream_id, delay_report, codec_ie):
        """Set config request"""
        if result == 0:
            self.add_stream(addr, stream_id, 'configured', delay_report, codec_ie)

    def get_config_request(self, addr):
        """Get config request"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_config_request()
        return None

    def set_config_response(self, addr, stream_id, rsp_err_code):
        """Handle config response"""
        if rsp_err_code == 0:
            if self.get_stream(addr, stream_id):
                self.set_stream_state(addr, stream_id, 'configured')
            else:
                self.add_stream(addr, stream_id, state='configured')

    def set_reconfig_request(self, addr, result, stream_id, delay_report, codec_ie):
        """Set reconfig request"""
        conn = self.get_connection(addr)
        if conn and result == 0:
            conn.set_reconfig_request(stream_id, delay_report, codec_ie)

    def get_reconfig_request(self, addr):
        """Get reconfig request"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_reconfig_request()
        return None

    def set_establish_request(self, addr, result, stream_id):
        """Handle establish request"""
        if result == 0:
            self.set_stream_state(addr, stream_id, 'established')

    def set_establish_response(self, addr, stream_id, rsp_err_code):
        """Handle establish response"""
        if rsp_err_code == 0:
            self.set_stream_state(addr, stream_id, 'established')

    def set_release_request(self, result, addr, stream_id):
        """Handle release request"""
        if result == 0:
            self.remove_stream(addr, stream_id)

    def set_release_response(self, addr, stream_id, rsp_err_code):
        """Handle release response"""
        if rsp_err_code == 0:
            self.remove_stream(addr, stream_id)

    def set_start_request(self, addr, result, stream_id):
        """Handle start request"""
        if result == 0:
            self.set_stream_state(addr, stream_id, 'started')

    def set_start_response(self, addr, stream_id, rsp_err_code):
        """Handle start response"""
        if rsp_err_code == 0:
            self.set_stream_state(addr, stream_id, 'started')

    def set_suspend_request(self, addr, result, stream_id):
        """Handle suspend request"""
        if result == 0:
            self.set_stream_state(addr, stream_id, 'suspended')

    def set_suspend_response(self, addr, stream_id, rsp_err_code):
        """Handle suspend response"""
        if rsp_err_code == 0:
            self.set_stream_state(addr, stream_id, 'suspended')

    def set_abort_request(self, addr, result, stream_id):
        """Handle abort request"""
        if result == 0:
            self.connections.pop(addr)

    def set_abort_response(self, addr, stream_id, rsp_err_code):
        """Handle abort response"""
        if rsp_err_code == 0:
            self.connections.pop(addr)

    def set_get_config_request(self, addr, result, stream_id):
        """Handle get config request"""
        if result == 0:
            self.set_stream_state(addr, stream_id, 'get_configured')

    def set_get_config_response(self, addr, stream_id, rsp_err_code,
                                delay_report, codec_ie):
        """Handle get config response"""
        if rsp_err_code == 0:
            self.set_stream_state(addr, stream_id, 'get_configured')

    def set_delay_report(self, addr, stream_id, delay):
        """Set delay report"""
        conn = self.get_connection(addr)
        if conn:
            conn.set_delay_report(stream_id, delay)

    def get_delay_report(self, addr, stream_id):
        """Get delay report"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_delay_report(stream_id)
        return None

    def set_delay_report_request(self, addr, result, stream_id, delay):
        """Handle delay report request"""
        if result == 0:
            self.set_delay_report(addr, stream_id, delay)
            self.set_stream_state(addr, stream_id, 'delay_reported')

    def set_delay_report_response(self, addr, stream_id, rsp_err_code):
        """Handle delay report response"""
        if rsp_err_code == 0:
            self.set_stream_state(addr, stream_id, 'delay_reported')

    def add_received_data(self, addr, stream_id, seq_num, timestamp, data):
        """Add received data"""
        conn = self.get_connection(addr)
        if conn:
            conn.add_received_data(stream_id, seq_num, timestamp, data)

    def get_received_data(self, addr, stream_id):
        """Get received data"""
        conn = self.get_connection(addr)
        if conn:
            return conn.get_received_data(stream_id)
        return []

    def set_stream_sent(self, addr, stream_id):
        """Set stream sent flag"""
        conn = self.get_connection(addr)
        if conn:
            conn.set_stream_sent(stream_id)

    def is_stream_sent(self, addr, stream_id):
        """Check if stream was sent"""
        conn = self.get_connection(addr)
        if conn:
            return conn.is_stream_sent(stream_id)
        return False

    def wait_for_stream_sent(self, addr, stream_id, timeout=10):
        """Wait for stream sent"""
        conn = self.get_connection(addr)
        if conn:
            return conn.wait_for_stream_sent(stream_id, timeout)
        return False

    def wait_for_stream_released(self, addr, stream_id, timeout=10):
        """Wait for stream to be released"""

        wait_for_event(timeout, lambda: self.get_connection(addr) is None or
                       self.get_connection(addr).get_stream(stream_id) is None)
        return self.get_connection(addr) is None or self.get_connection(addr).get_stream(stream_id) is None

    def wait_for_aborted(self, addr, stream_id, timeout=10):
        """Wait for stream to be aborted"""

        wait_for_event(timeout, lambda: self.get_connection(addr) is None)
        return self.get_connection(addr) is None or self.get_connection(addr).get_stream(stream_id) is None

    def wait_for_discovered(self, addr, timeout=10):
        """Wait for device to be discovered"""
        wait_for_event(timeout, lambda: self.get_discover_state(addr))
        return self.get_discover_state(addr)

    def wait_for_get_capabilities_finished(self, addr, ep_id, timeout=5):
        """Wait for device to be discovered"""
        logging.info(f'addr {addr}, ep_id {ep_id}')
        wait_for_event(timeout, lambda: self.get_service_cap(addr, ep_id) is not None)
        return self.get_service_cap(addr, ep_id) is not None
