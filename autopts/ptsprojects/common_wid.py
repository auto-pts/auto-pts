#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Codecoup.
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
from enum import IntEnum
from importlib.util import find_spec

from autopts.ptsprojects.stack import get_stack

LOG = logging.debug

PTSPROJECTS_NS_FMT = "autopts.ptsprojects.{backend}.{service}_wid"
WID_NS_FMT = "autopts.wid.{service}"

GATT_CL_SVC = "GATT_CL"
GATT_CL_TC_SUBSTR = "GATT/CL"
GATT_CLIENT_SERVICE = "gatt_client"


class Backend(IntEnum):
    """Supported Bluetooth stack execution backends."""

    ZEPHYR = 1
    MYNEWT = 2
    BLUEZ = 3


class Service(IntEnum):
    """Supported Bluetooth services and specifications."""

    AICS = 1
    ASCS = 2
    BAP = 3
    BASS = 4
    CAP = 5
    CAS = 6
    CCP = 7
    CSIP = 8
    CSIS = 9
    DIS = 10
    GAP = 11
    GATT = 12
    GATTC = 13
    GMCS = 14
    HAP = 15
    HAS = 16
    IAS = 17
    L2CAP = 18
    MCP = 19
    MCS = 20
    MESH = 21
    MICP = 22
    MICS = 23
    MMDL = 24
    OTS = 25
    PACS = 26
    PBP = 27
    RFCOMM = 28
    SDP = 29
    SM = 30
    TBS = 31
    TMAP = 32
    VCP = 33
    VCS = 34
    VOCS = 35
    # GENERATOR append service_enum


def get_wid_handler(backend: Backend, service: Service):
    """Generates a WID (Widget ID) handler function for a specific backend and service.

    Args:
        backend: The execution backend as a Backend enum.
        service: The Bluetooth service as a Service enum.

    Returns:
        Callable[[str, str, str], Any]: A handler function that processes a WID,
            description, and test case name to execute the corresponding test logic.
    """
    backend_str = backend.name.lower()
    service_str = service.name.lower()

    def handler(wid, description, test_case_name):
        """Dispatches a WID event to its backend-specific or generic service namespace handler.

        Args:
            wid: The Widget Identifier string.
            description: Human-readable prompt or description of the WID step.
            test_case_name: Name of the currently executing test case.

        Returns:
            Any: Result of the target generic or project-specific WID handler execution.
        """
        from autopts.wid import generic_wid_hdl

        LOG("%r.%r handler, wid=%r, tc=%r", backend_str, service_str, wid, test_case_name)

        if service in (Service.GATT, Service.GATTC):
            stack = get_stack()
            if stack.is_svc_supported(GATT_CL_SVC) and GATT_CL_TC_SUBSTR in test_case_name:
                sub_service = GATT_CLIENT_SERVICE
            else:
                sub_service = Service.GATT.name.lower()
        else:
            sub_service = service_str

        project_ns = PTSPROJECTS_NS_FMT.format(backend=backend_str, service=sub_service)
        generic_ns = WID_NS_FMT.format(service=sub_service)

        ns = [generic_ns]
        if find_spec(project_ns) is not None:
            ns.insert(0, project_ns)

        return generic_wid_hdl(wid, description, test_case_name, ns)

    return handler


def get_backend() -> Backend:
    """Retrieves the active Bluetooth stack Backend enum at runtime from the active IUT controller."""
    from autopts.pybtp import btp

    iut = btp.get_iut_method()
    if iut is None:
        raise RuntimeError("No active IUT instance initialized.")

    # IUT controller classes live in autopts.ptsprojects.<backend>.iutctl,
    # so match the backend package name exactly.
    module_parts = type(iut).__module__.split(".")
    if len(module_parts) > 2 and module_parts[:2] == ["autopts", "ptsprojects"]:
        backend_name = module_parts[2].upper()
        if backend_name in Backend.__members__:
            return Backend[backend_name]

    raise ValueError(f"Could not determine Backend for active IUT controller: {type(iut)}")
