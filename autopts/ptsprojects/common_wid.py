import importlib
import logging
from autopts.wid import generic_wid_hdl

log = logging.debug

# List of supported backends; please add more in the future
BACKENDS = ["zephyr", "mynewt", "bluez"]

def profile_wid_hdl(backend: str,
                    profile: str,
                    wid: int,
                    description: str,
                    test_case_name: str):
    """
    Generic WID handler for any backend.

    backend -- directory name (zephyr, mynewt, bluez...)
    profile -- profile name (ascs, bap, gap...)
    wid -- WID identifier
    """
    log(f"profile_wid_hdl: {backend}.{profile}  wid={wid}  tc={test_case_name}")

    namespaces = []
    # 1) profil-specific module: autopts.ptsprojects.<backend>.<profile>_wid
    module_name = f"autopts.ptsprojects.{backend}.{profile}_wid"
    try:
        m = importlib.import_module(module_name)
        namespaces.append(m.__name__)
    except ImportError:
        log(f"No module {module_name}")

    # 2) common directory autopts.wid.<profile>
    namespaces.append(f"autopts.wid.{profile}")

    return generic_wid_hdl(wid, description, test_case_name, namespaces)