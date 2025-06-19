import importlib
import logging
from typing import Callable

from autopts.wid import generic_wid_hdl
from autopts.wid.gap import hdl_wid_139_mode1_lvl2

log = logging.debug

# ==========================================
# exceptions: (backend,profile)->{wid:handler…}
# ==========================================
PROFILE_OVERRIDES: dict[tuple[str, str], dict[int, Callable[[str], any]]] = {
    ("mynewt", "gap"): {
        139: hdl_wid_139_mode1_lvl2,
    },
}


def get_wid_handler(backend: str, profile: str) -> Callable[[int, str, str], any]:
    """
    Returns a single handler function:
    - first looks in PROFILE_OVERRIDES[(backend,profile)]
    - if finds wid -> calls override(description)
    - otherwise -> imports module and fires generic_wid_hdl
    """
    overrides = PROFILE_OVERRIDES.get((backend, profile), {})

    def handler(wid: int, description: str, test_case_name: str):
        if wid in overrides:
            log(f"override handler for {backend}.{profile} wid={wid}")
            return overrides[wid](description)

        # fallback: dynamic import and generic_wid_hdl
        log(f"profile_wid_hdl: {backend}.{profile}  wid={wid}  tc={test_case_name}")
        namespaces = []
        module_name = f"autopts.ptsprojects.{backend}.{profile}_wid"
        try:
            m = importlib.import_module(module_name)
            namespaces.append(m.__name__)
        except ImportError:
            log(f"No module {module_name}")

        namespaces.append(f"autopts.wid.{profile}")
        return generic_wid_hdl(wid, description, test_case_name, namespaces)

    return handler
