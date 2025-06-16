import logging

from autopts.ptsprojects.stack import get_stack
from autopts.wid import generic_wid_hdl

log = logging.debug


def get_wid_handler(backend: str, profile: str):
    """
    Returns a handler that:
    - always logs the call
    - for profile == "gatt" manages two namespaces
    - for profile == "gattc" manages three namespaces
    - in other cases uses only [__name__, autopts.wid.<profile>]
    """
    def handler(wid, description, test_case_name):
        log(f"{backend}.{profile} handler, wid={wid}, tc={test_case_name}")
        if profile == "gatt":
            stack = get_stack()
            ns = [__name__]
            if stack.is_svc_supported("GATT_CL") and "GATT/CL" in test_case_name:
                ns.append("autopts.wid.gatt_client")
            else:
                ns.append("autopts.wid.gatt")

            return generic_wid_hdl(wid, description, test_case_name, ns)

        if profile == "gattc":
            stack = get_stack()
            # always include this module
            ns = [__name__]
            # decide between client vs server WID modules
            if stack.is_svc_supported("GATT_CL") and "GATT/CL" in test_case_name:
                ns.extend([
                    f"autopts.ptsprojects.{backend}.gatt_client_wid",
                    "autopts.wid.gatt_client"
                ])
            else:
                ns.extend([
                    f"autopts.ptsprojects.{backend}.gatt_wid",
                    "autopts.wid.gatt"
                ])
            return generic_wid_hdl(wid, description, test_case_name, ns)

        return generic_wid_hdl(
            wid,
            description,
            test_case_name,
            [__name__, f"autopts.wid.{profile}"]
        )
    return handler
