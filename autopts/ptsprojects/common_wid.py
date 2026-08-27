import logging
from enum import IntEnum
from importlib.util import find_spec

from autopts.ptsprojects.stack import get_stack

LOG = logging.debug

PTSPROJECTS_NS_FMT = "autopts.ptsprojects.{backend}.{profile}_wid"
WID_NS_FMT = "autopts.wid.{profile}"

GATT_CL_SVC = "GATT_CL"
GATT_CL_TC_SUBSTR = "GATT/CL"
GATT_CLIENT_PROFILE = "gatt_client"


class Backend(IntEnum):
    """Supported Bluetooth stack execution backends."""

    ZEPHYR = 1
    MYNEWT = 2
    BLUEZ = 3


class Service(IntEnum):
    """Supported Bluetooth profile services and specifications."""

    AICS = 1
    ASCS = 2
    BAP = 3
    BASS = 4
    CAP = 5
    CAS = 6
    CCP = 7
    CSIP = 8
    CSIS = 9
    DFUM = 10
    DIS = 11
    GAP = 12
    GATT = 13
    GATTC = 14
    GMCS = 15
    HAP = 16
    HAS = 17
    IAS = 18
    L2CAP = 19
    MBTM = 20
    MCP = 21
    MCS = 22
    MESH = 23
    MICP = 24
    MICS = 25
    MMDL = 26
    OTS = 27
    PACS = 28
    PBP = 29
    RFCOMM = 30
    SDP = 31
    SM = 32
    TBS = 33
    TMAP = 34
    VCP = 35
    VCS = 36
    VOCS = 37
    # GENERATOR append profile_enum


def get_wid_handler(backend: Backend | str, service: Service | str):
    """Generates a WID (Widget ID) handler function for a specific backend and service.

    Args:
        backend: The execution backend as a Backend enum or string name (e.g., 'ZEPHYR').
        service: The Bluetooth profile service as a Service enum or string name (e.g., 'GATT').

    Returns:
        Callable[[str, str, str], Any]: A handler function that processes a WID,
            description, and test case name to execute the corresponding test logic.

    Raises:
        KeyError: If the provided backend or service string does not match standard Enums.
    """

    backend_enum = backend if isinstance(backend, Backend) else Backend[str(backend).upper()]
    profile_enum = service if isinstance(service, Service) else Service[str(service).upper()]

    backend_str = backend_enum.name.lower()
    profile_str = profile_enum.name.lower()

    def handler(wid, description, test_case_name):
        """Dispatches a WID event to its backend-specific or generic profile namespace handler.

        Args:
            wid: The Widget Identifier string.
            description: Human-readable prompt or description of the WID step.
            test_case_name: Name of the currently executing test case.

        Returns:
            Any: Result of the target generic or project-specific WID handler execution.
        """
        from autopts.wid import generic_wid_hdl

        LOG("%r.%r handler, wid=%r, tc=%r", backend_str, profile_str, wid, test_case_name)

        if profile_enum in (Service.GATT, Service.GATTC):
            stack = get_stack()
            if stack.is_svc_supported(GATT_CL_SVC) and GATT_CL_TC_SUBSTR in test_case_name:
                sub_profile = GATT_CLIENT_PROFILE
            else:
                sub_profile = Service.GATT.name.lower()
        else:
            sub_profile = profile_str

        project_ns = PTSPROJECTS_NS_FMT.format(backend=backend_str, profile=sub_profile)
        generic_ns = WID_NS_FMT.format(profile=sub_profile)

        ns = [generic_ns]
        if find_spec(project_ns) is not None:
            ns.insert(0, project_ns)

        return generic_wid_hdl(wid, description, test_case_name, ns)

    return handler
