import logging
import sys
from ..ptsprojects.stack import get_stack
from ..pybtp.types import WIDParams

log = logging.debug


def _generic_wid_hdl(wid, description, test_case_name, module_names):
    wid_hdl = None
    wid_str = f'hdl_wid_{wid}'

    for module_name in module_names:
        module = sys.modules[module_name]
        if hasattr(module, wid_str):
            wid_hdl = getattr(module, wid_str)
            break

    if wid_hdl is None:
        log(f'No {wid_str} found!')
        return False

    return wid_hdl(WIDParams(wid, description, test_case_name))


def generic_wid_hdl(wid, description, test_case_name, module_names):
    stack = get_stack()

    if not stack.synch or not stack.synch.is_required_synch(test_case_name, wid):
        return _generic_wid_hdl(wid, description, test_case_name, module_names)

    actions = stack.synch.perform_synch(wid, test_case_name, description)
    if not actions:
        return "WAIT"

    for action in actions:
        result = _generic_wid_hdl(action.wid, description, action.test_case, module_names)
        stack.synch.prepare_pending_response(action.test_case,
                                             result, action.delay)

    stack.synch.set_pending_responses_if_any()

    return "WAIT"
