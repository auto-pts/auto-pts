import logging

from autopts.pybtp import btp
from autopts.pybtp.types import (
    BTPError,
)

LT2_CASE_TOKEN = "LT2"


def is_lt2_case(test_case_name: str) -> bool:
    """Return whether a test case name targets the LT2 PTS instance.

    Args:
        test_case_name: Full PTS test case name.

    Returns:
        True if the test case is for LT2, otherwise False.
    """
    return LT2_CASE_TOKEN in test_case_name


def peer_addr_and_type(test_case_name: str) -> tuple[str, int]:
    """Return peer address and address type for the active PTS link.

    Args:
        test_case_name: Full PTS test case name used to select LT1 or LT2.

    Returns:
        A tuple containing the peer Bluetooth address and LE address type.
    """
    if is_lt2_case(test_case_name):
        return btp.lt2_addr_get(), btp.lt2_addr_type_get()

    return btp.pts_addr_get(), btp.pts_addr_type_get()


def _safe_bap_send(ase_id: int, data: bytearray):
    """Safely send BAP/ISO data, ignoring buffer full errors."""
    try:
        btp.bap_send(ase_id, data)
    except BTPError:
        # Buffer full — ignore silently or optionally log
        pass


def _safe_l2cap_disconnect(channel_id):
    try:
        btp.l2cap_disconn(channel_id)
    except BTPError:
        logging.debug("Ignoring expected error on L2CAP disconnect")


def _l2cap_send_forever(channel_id):
    try:
        while True:
            btp.l2cap_send_data(channel_id, '00')
    except (BTPError, TimeoutError):
        pass
