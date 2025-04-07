import importlib
import logging

from ..pybtp.types import MissingWIDError, WIDParams


log = logging.debug


def _generic_wid_hdl(wid, description, test_case_name, module_names):
    wid_hdl = None
    wid_str = f'hdl_wid_{wid}'

    for module_name in module_names:
        module = importlib.import_module(module_name)
        if hasattr(module, wid_str):
            wid_hdl = getattr(module, wid_str)
            break

    if wid_hdl is None:
        raise MissingWIDError(f'No {wid_str} found!')

    return wid_hdl(WIDParams(wid, description, test_case_name))


def generic_wid_hdl(wid, description, test_case_name, module_names):
    response = _generic_wid_hdl(wid, description, test_case_name, module_names)

    return response
