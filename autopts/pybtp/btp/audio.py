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
from dataclasses import dataclass, field

from autopts.pybtp import defs
from autopts.pybtp.types import LC3_LTV_Config_Type


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


@dataclass(frozen=True)
class LTV:
    """A Length-Type-Value structure, used e.g. in codec configuration and metadata.

    Attributes:
        type: LTV type (0x00-0xFF), e.g. defs.AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS.
        value: LTV value, without the length and type octets.
    """

    type: int
    value: bytes

    def to_bytes(self) -> bytes:
        """Return the LTV as it is encoded on air: length (1), type (1), value."""
        return struct.pack("<BB", 1 + len(self.value), self.type) + self.value


def parse_ltvs(data: bytes) -> list[LTV]:
    """Parse a sequence of LTV structures.

    Args:
        data: Concatenated LTVs, without any leading total length octet.

    Returns:
        The parsed LTVs, in the order they appear in data.

    Raises:
        ValueError: If an LTV is empty (length 0) or does not fit in data.
    """
    ltvs = []
    pos = 0

    while pos < len(data):
        ltv_len = data[pos]
        if ltv_len == 0 or pos + 1 + ltv_len > len(data):
            raise ValueError(f"Malformed LTV at offset {pos}")

        ltvs.append(LTV(data[pos + 1], bytes(data[pos + 2:pos + 1 + ltv_len])))
        pos += 1 + ltv_len

    return ltvs


def find_ltv(ltvs: list[LTV], ltv_type: int) -> LTV | None:
    """Return the first LTV of the given type, or None if there is no such LTV.

    Args:
        ltvs: LTVs to search, e.g. returned by parse_ltvs().
        ltv_type: LTV type to look for (0x00-0xFF).
    """
    return next((ltv for ltv in ltvs if ltv.type == ltv_type), None)


@dataclass(frozen=True)
class BaseBis:
    """A BIS of a subgroup of a Basic Audio Announcement (BASE).

    Attributes:
        index: BIS_index, starting at 1.
        codec_config: BIS specific Codec_Specific_Configuration LTVs, they override the ones of the subgroup.
    """

    index: int
    codec_config: list[LTV] = field(default_factory=list)


@dataclass(frozen=True)
class BaseSubgroup:
    """A subgroup of a Basic Audio Announcement (BASE).

    Attributes:
        codec_id: Codec_ID: coding format (1), company ID (2), vendor specific codec ID (2).
        codec_config: Codec_Specific_Configuration LTVs common for all BISes of the subgroup.
        metadata: Metadata LTVs of the subgroup.
        bis_indexes: BIS_index of every BIS in the subgroup.
        bises: The BISes of the subgroup, with their BIS specific Codec_Specific_Configuration.
    """

    codec_id: bytes
    codec_config: list[LTV] = field(default_factory=list)
    metadata: list[LTV] = field(default_factory=list)
    bis_indexes: list[int] = field(default_factory=list)
    bises: list[BaseBis] = field(default_factory=list)


@dataclass(frozen=True)
class Base:
    """A Basic Audio Announcement (BASE), see BAP 3.7.2.2.

    Attributes:
        presentation_delay: Presentation delay in microseconds (24 bit).
        subgroups: Subgroups of the announcement.
    """

    presentation_delay: int
    subgroups: list[BaseSubgroup]


def parse_base(data: bytes) -> Base:
    """Parse a BASE from periodic advertising data.

    Args:
        data: Periodic advertising data, a sequence of AD structures (length, type, data). One of them
            has to be the Service Data AD (type 0x16) of the Basic Audio Announcement Service (UUID 0x1851),
            it does not have to be the first one.

    Returns:
        The parsed BASE.

    Raises:
        ValueError: If there is no BASE in data, or it is not well-formed.
    """
    # Locate the Service Data AD: AD length (1), AD type (1), UUID (2), followed by the BASE
    start = None
    ad_pos = 0
    while ad_pos < len(data) and data[ad_pos] != 0:
        ad_end = ad_pos + 1 + data[ad_pos]
        if ad_end > len(data):
            raise ValueError("Truncated AD structure")
        if data[ad_pos + 1] == 0x16 and data[ad_pos + 2:ad_pos + 4] == b"\x51\x18":
            start = ad_pos + 4
            break
        ad_pos = ad_end

    if start is None:
        raise ValueError("Not a Basic Audio Announcement")

    # Parsing never reads past the Service Data AD
    end = ad_end
    pos = start

    def take(length: int) -> bytes:
        nonlocal pos
        if pos + length > end:
            raise ValueError("Truncated Basic Audio Announcement")
        chunk = data[pos:pos + length]
        pos += length
        return bytes(chunk)

    presentation_delay = int.from_bytes(take(3), "little")
    num_subgroups = take(1)[0]
    subgroups = []

    for _ in range(num_subgroups):
        num_bis = take(1)[0]
        codec_id = take(5)
        codec_config = parse_ltvs(take(take(1)[0]))
        metadata = parse_ltvs(take(take(1)[0]))

        bises = []
        for _ in range(num_bis):
            bis_index = take(1)[0]
            bises.append(BaseBis(bis_index, parse_ltvs(take(take(1)[0]))))

        subgroups.append(BaseSubgroup(codec_id, codec_config, metadata, [bis.index for bis in bises], bises))

    return Base(presentation_delay, subgroups)


LC3_CODING_FORMAT = 0x06


def get_bis_codec_config(subgroup: BaseSubgroup, bis: BaseBis) -> list[LTV]:
    """Get the Codec_Specific_Configuration of a BIS: the one of its subgroup, overridden by the BIS specific one.

    Args:
        subgroup: Subgroup of the BASE that the BIS belongs to.
        bis: BIS of the subgroup.

    Returns:
        The LTVs of the subgroup that the BIS does not override, followed by the BIS specific LTVs.
    """
    overridden = {ltv.type for ltv in bis.codec_config}
    return [ltv for ltv in subgroup.codec_config if ltv.type not in overridden] + bis.codec_config


def is_codec_config_supported(
    codec_id: bytes,
    config: list[LTV],
    coding_format: int,
    frequencies: int,
    frame_durations: int,
    octets_per_frame: int,
    channel_counts: int,
) -> bool:
    """Check if a Codec_Specific_Configuration is supported by a PAC record.

    Only the LC3 parameters that are present in the configuration are checked, a parameter that is not
    present does not make the configuration unsupported. The codec specific parameters of other codecs are not
    interpreted, only the coding format is compared.

    Args:
        codec_id: Codec_ID of the configuration: coding format (1), company ID (2), vendor specific codec ID (2).
        config: Codec_Specific_Configuration LTVs, e.g. of a BASE subgroup.
        coding_format: Coding format of the PAC record.
        frequencies: Supported_Sampling_Frequencies bitfield of the PAC record, bit 0 is 8 kHz.
        frame_durations: Supported_Frame_Durations bitfield of the PAC record, bit 0 is 7.5 ms and bit 1 is 10 ms.
        octets_per_frame: Supported_Octets_Per_Codec_Frame of the PAC record: the minimum in the low 16 bits and the
            maximum in the high 16 bits.
        channel_counts: Supported_Audio_Channel_Counts bitfield of the PAC record, bit 0 is 1 channel.

    Returns:
        True if the PAC record supports the configuration, False otherwise.
    """
    if codec_id[0] != coding_format:
        return False

    if coding_format != LC3_CODING_FORMAT:
        return True

    sampling_freq = find_ltv(config, LC3_LTV_Config_Type.SAMPLING_FREQ)
    if sampling_freq is not None:
        # Sampling_Frequency 0x01 is 8 kHz, the same as bit 0 of the Supported_Sampling_Frequencies
        code = sampling_freq.value[0]
        if code == 0 or not frequencies & (1 << (code - 1)):
            return False

    frame_duration = find_ltv(config, LC3_LTV_Config_Type.FRAME_DURATION)
    if frame_duration is not None:
        # Frame_Duration 0x00 is 7.5 ms, the same as bit 0 of the Supported_Frame_Durations
        if not frame_durations & (1 << frame_duration.value[0]):
            return False

    frame_len = find_ltv(config, LC3_LTV_Config_Type.FRAME_LEN)
    if frame_len is not None:
        octets = int.from_bytes(frame_len.value[:2], "little")
        if not octets_per_frame & 0xFFFF <= octets <= octets_per_frame >> 16:
            return False

    # Audio_Channel_Allocation is a bitfield of the audio locations, without it or with none set the audio is mono
    channel_allocation = find_ltv(config, LC3_LTV_Config_Type.CHANNEL_ALLOCATION)
    channels = 1
    if channel_allocation is not None:
        channels = max(1, int.from_bytes(channel_allocation.value[:4], "little").bit_count())
    if not channel_counts & (1 << (channels - 1)):
        return False

    return True
