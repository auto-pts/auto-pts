import logging
import socket

from autopts.pybtp import btp
from autopts.pybtp.types import (
    BTPError,
)


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
    except (BTPError, socket.timeout):
        pass
