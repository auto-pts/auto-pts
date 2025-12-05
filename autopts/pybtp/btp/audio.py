#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2025, Nordic Semiconductor ASA.
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

"""Common LE Audio related functions that are not specific to any profiles"""

import struct

from autopts.pybtp import defs


def is_uint8(val: int) -> bool:
    """
    Returns True if val is a unsigned 8-bit integer

    Args:
        val (int): The int to check

    Returns:
        bool: True if val is an unsigned 8-bit integer (0x00-0xFF), False otherwise
    """
    return isinstance(val, int) and 0x00 <= val <= 0xFF


def is_uint16(val: int) -> bool:
    """
    Returns True if val is a unsigned 16-bit integer

    Args:
        val (int): The int to check

    Returns:
        bool: True if val is an unsigned 16-bit integer (0x0000-0xFFFF), False otherwise
    """
    return isinstance(val, int) and 0x0000 <= val <= 0xFFFF


def is_utf8_string(val: str, max_len: int = 254) -> bool:
    """
    Returns True if val is a valid UTF-8 string

    By default it checks if the string fits in LTV data (max size in octets is 255 - 1 for the type)

    Args:
        val (str): The string to check
        max_len (int): The maximum size in octets of the string (default 254)

    Returns:
        bool: True if val is a string with size <= max_len, False otherwise
    """
    return isinstance(val, str) and len(val.encode("utf-8")) <= max_len


def pack_metadata(stream_context: int = None, ccid_list: list[int] = None, program_info: str = None) -> bytes:
    """
    Pack LE Audio metadata into LTV (Length-Type-Value) format.

    Args:
        stream_context (int, optional): Audio stream context value (0x0000 to 0xFFFF).
            If provided, must be an unsigned 16-bit integer.
        ccid_list (list[int], optional): List of unique Content Control IDs (0x00 to 0xFF each).
            If provided, must be a list of unique unsigned 8-bit integers, max length 254.
        program_info (str, optional): UTF-8 program info string (max 254 bytes).

    Returns:
        bytes: Packed metadata in LTV format.

    Raises:
        ValueError: If any parameter is invalid (wrong type, out of range, or not unique).

    Example:
        >>> pack_metadata(stream_context=0x1234, ccid_list=[1,2,3], program_info="Test")
        b'\\x03\\x02\\x34\\x12\\x04\\x05\\x01\\x02\\x03\\x05\\x03Test'
    """

    metadata = b""

    if stream_context is not None:
        if is_uint16(stream_context):
            metadata += struct.pack("<BBH", 3, defs.AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, stream_context)
        else:
            raise ValueError(f"Invalid stream_context value: {stream_context}")

    if ccid_list is not None:
        if (
            isinstance(ccid_list, list)
            and len(ccid_list) <= 254  # max number of CCIDs
            and all(is_uint8(ccid) for ccid in ccid_list)
            and len(ccid_list) == len(set(ccid_list))  # check uniqueness
        ):
            metadata += struct.pack(
                f"<BB{len(ccid_list)}B",
                1 + len(ccid_list),
                defs.AUDIO_METADATA_CCID_LIST,
                *ccid_list,
            )
        else:
            raise ValueError(f"Invalid ccid_list value: {ccid_list}")

    if program_info is not None:
        if is_utf8_string(program_info):
            metadata += struct.pack(
                "<BB", 1 + len(program_info.encode("utf-8")), defs.AUDIO_METADATA_PROGRAM_INFO
            ) + program_info.encode("utf-8")
        else:
            raise ValueError(f"Invalid program_info value: {program_info}")

    return metadata
