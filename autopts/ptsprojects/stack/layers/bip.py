#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, NXP.
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

import datetime
import io
import re
import struct
from dataclasses import dataclass, field
from datetime import timezone
from threading import Condition

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import defs, types
from autopts.pybtp.types import BIPAppParamTag, BIPRemoteDisplay, OBEXHdr, OBEXRspCode, obex_build_tlv

# BIP user-defined OBEX header IDs (Section 5.2.2)
BIP_HDR_IMG_HANDLE = 0x30
BIP_HDR_IMG_DESC = 0x71


# ---------------------------------------------------------------------------
# Data Models (from bip_server.py)
# ---------------------------------------------------------------------------
@dataclass
class ImageVariant:
    encoding: str
    pixel: str
    maxsize: int = None
    transformation: str = None


@dataclass
class ImageAttachment:
    name: str
    content_type: str
    data: bytes = b""
    charset: str = None
    size: int = None
    created: str = None
    modified: str = None

    def __post_init__(self):
        if self.size is None:
            self.size = len(self.data)


@dataclass
class ImageRecord:
    handle: str
    friendly_name: str
    created: str
    native_encoding: str
    native_pixel: str
    native_size: int
    image_data: bytes
    thumbnail_data: bytes
    modified: str = None
    is_captured: bool = False
    variants: list = field(default_factory=list)
    attachments: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# BIPDataStore (in-memory image repository)
# ---------------------------------------------------------------------------
class BIPDataStore:
    def __init__(self):
        self.images: dict[str, ImageRecord] = {}
        self.preferred_format = {
            "encoding": "JPEG", "pixel": "1280*1024",
            "transformation": "stretch crop fill"}
        self.image_formats = [
            {"encoding": "JPEG", "pixel": "160*120", "maxsize": 5000},
            {"encoding": "JPEG", "pixel": "320*240"},
            {"encoding": "JPEG", "pixel": "640*480"},
            {"encoding": "JPEG", "pixel": "1280*1024"},
            {"encoding": "PNG", "pixel": "160*120-1280*960"},
            {"encoding": "GIF", "pixel": "160*120-640*480"},
            {"encoding": "BMP", "pixel": "160*120"},
        ]
        self.attachment_formats = [
            {"content_type": "text/plain"},
            {"content_type": "audio/basic"},
        ]
        self.filtering_parameters = {
            "created": "1", "modified": "1",
            "encoding": "1", "pixel": "1"}
        self.dpof_options = {
            "standard-print": "1", "index-print": "1",
            "number-sets": "1", "trimming": "1"}
        self.display_index = 0
        self.monitoring_image_data = _make_dummy_jpeg(160, 120)

    def add_image(self, img: ImageRecord):
        self.images[img.handle] = img

    def remove_image(self, handle: str) -> bool:
        return self.images.pop(handle, None) is not None

    def ordered_handles(self) -> list:
        return sorted(self.images.keys())

    def captured_handles_desc(self) -> list:
        return sorted(
            [h for h, img in self.images.items() if img.is_captured],
            key=lambda h: self.images[h].created,
            reverse=True)

    def next_handle(self) -> str:
        if not self.images:
            return "1000001"
        return str(max(int(h) for h in self.images) + 1).zfill(7)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_dummy_jpeg(w: int, h: int) -> bytes:
    try:
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (w, h), (128, 128, 128)).save(buf, "JPEG")
        return buf.getvalue()
    except ImportError:
        return (b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00"
                b"\x00\x01\x00\x01\x00\x00\xFF\xD9")


def _parse_xml_attr(xml_str, attr):
    if not xml_str:
        return None
    m = re.search(rf'{attr}\s*=\s*"([^"]*)"', xml_str)
    return m.group(1) if m else None


def _parse_date_range(xml_str, attr):
    val = _parse_xml_attr(xml_str, attr)
    if not val:
        return None
    parts = val.split("-", 1)
    if len(parts) == 2:
        return (parts[0] if parts[0] != "*" else None,
                parts[1] if parts[1] != "*" else None)
    return (val, val)


def _parse_app_param_value(app_params, tag, fmt):
    raw = app_params.get(tag)
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        size = struct.calcsize(fmt)
        if len(raw) >= size:
            return struct.unpack(fmt, raw[:size])[0]
    return None


def _get_img_desc_xml(headers):
    raw = headers.get(BIP_HDR_IMG_DESC)
    if not raw:
        return None
    if isinstance(raw, (bytes, bytearray)):
        try:
            return raw.decode('utf-8').rstrip('\x00')
        except UnicodeDecodeError:
            return None
    return str(raw) if raw else None


def _handle_to_utf16(handle_str):
    return handle_str.encode('utf-16-be') + b'\x00\x00'


IMAGE_HANDLE = _handle_to_utf16("1000001")


def _obex_hdr_byte_seq(hdr_id, data):
    buf = bytearray()
    buf.append(hdr_id)
    buf.extend(struct.pack('>H', 3 + len(data)))
    buf.extend(data)
    return buf


# ---------------------------------------------------------------------------
# Sample Data (from bip_server.py create_sample_data)
# ---------------------------------------------------------------------------
def create_sample_data() -> BIPDataStore:
    ds = BIPDataStore()
    thm = _make_dummy_jpeg(160, 120)

    ds.add_image(ImageRecord(
        handle="1000001", friendly_name="ABCD0001.JPG",
        created="20000801T060000Z", native_encoding="JPEG",
        native_pixel="1280*1024", native_size=1048576,
        image_data=_make_dummy_jpeg(1280, 1024), thumbnail_data=thm,
        is_captured=True,
        variants=[
            ImageVariant("JPEG", "640*480"),
            ImageVariant("JPEG", "160*120"),
            ImageVariant("GIF", "80*60-640*480"),
        ],
        attachments=[
            ImageAttachment("ABCD0001.txt", "text/plain",
                            b"Sample text for image 1000001",
                            created="20000801T060000Z"),
            ImageAttachment("ABCD0001.wav", "audio/basic",
                            b"\x00" * 1024,
                            created="20000801T060000Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1000002", friendly_name="ABCD0002.JPG",
        created="20000801T060030Z", native_encoding="JPEG",
        native_pixel="640*480", native_size=307200,
        image_data=_make_dummy_jpeg(640, 480), thumbnail_data=thm,
        is_captured=True,
        variants=[
            ImageVariant("JPEG", "320*240"),
            ImageVariant("JPEG", "160*120"),
        ],
        attachments=[
            ImageAttachment("ABCD0002.txt", "text/plain",
                            b"Sample text for image 1000002",
                            created="20000801T060030Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1000003", friendly_name="ABCD0003.JPG",
        created="20000801T060115Z", modified="20000808T071500Z",
        native_encoding="JPEG", native_pixel="1280*1024",
        native_size=1048576,
        image_data=_make_dummy_jpeg(1280, 1024), thumbnail_data=thm,
        is_captured=True,
        variants=[
            ImageVariant("JPEG", "640*480"),
            ImageVariant("PNG", "640*480", maxsize=500000),
        ],
        attachments=[
            ImageAttachment("ABCD0003.txt", "text/plain",
                            b"Sample text for image 1000003",
                            created="20000801T060115Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1000004", friendly_name="IMG_0004.PNG",
        created="20000801T060137Z", native_encoding="PNG",
        native_pixel="800*600", native_size=460800,
        image_data=_make_dummy_jpeg(800, 600), thumbnail_data=thm,
        variants=[
            ImageVariant("JPEG", "800*600"),
            ImageVariant("JPEG", "160*120"),
        ],
        attachments=[
            ImageAttachment("IMG_0004.txt", "text/plain",
                            b"Sample text for image 1000004",
                            created="20000801T060137Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1000005", friendly_name="ANIM0001.GIF",
        created="20010315T143000Z", native_encoding="GIF",
        native_pixel="320*240", native_size=76800,
        image_data=_make_dummy_jpeg(320, 240), thumbnail_data=thm,
        attachments=[
            ImageAttachment("ANIM0001.txt", "text/plain",
                            b"Sample text for image 1000005",
                            created="20010315T143000Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1000006", friendly_name="PHOTO001.BMP",
        created="20010520T091500Z", modified="20010521T100000Z",
        native_encoding="BMP", native_pixel="640*480",
        native_size=921600,
        image_data=_make_dummy_jpeg(640, 480), thumbnail_data=thm,
        is_captured=True,
        variants=[
            ImageVariant("JPEG", "640*480"),
            ImageVariant("JPEG", "160*120"),
        ],
        attachments=[
            ImageAttachment("notes.txt", "text/plain",
                            b"Photo taken at the park.",
                            charset="iso-8859-1",
                            created="20010520T091500Z"),
        ]))

    ds.add_image(ImageRecord(
        handle="1020001", friendly_name="BLUE0001.JPG",
        created="20020101T120000Z", native_encoding="JPEG",
        native_pixel="1920*1080", native_size=2073600,
        image_data=_make_dummy_jpeg(1920, 1080), thumbnail_data=thm,
        is_captured=True,
        variants=[
            ImageVariant("JPEG", "1280*960"),
            ImageVariant("JPEG", "640*480"),
            ImageVariant("JPEG", "160*120"),
            ImageVariant("PNG", "1920*1080", maxsize=5000000),
        ],
        attachments=[
            ImageAttachment("BLUE0001.txt", "text/plain",
                            b"Sample text for image 1020001",
                            created="20020101T120000Z"),
        ]))

    return ds


# ---------------------------------------------------------------------------
# BIPImageDatabase — backed by BIPDataStore + BIPServer logic
# ---------------------------------------------------------------------------
class BIPImageDatabase:

    def __init__(self):
        self.ds = create_sample_data()
        self._current_put_handle = None
        # Reassembly state for linked-thumbnail / linked-attachment PUTs so the
        # received bytes are stored back onto the correct image record and stay
        # consistent with what a later Get* returns.
        self._current_thm_handle = None
        self._thm_in_progress = False
        self._current_att_handle = None
        self._current_att_meta = None
        self._att_in_progress = False
        # When True, respond to the final PutImage with Partial Content (0xa6)

        # instead of the default Success (0xa0). Only enabled for the specific
        # test cases that require this special behaviour (e.g. BIP/RDR/FFC/BV-11-C).
        self.put_image_final_partial_content = False
        # Most recently pushed image (was the module-global _last_put_image).
        self.last_put_image = None
        # Handles returned by the last GetImagesList (was the module-global
        # `handles`). Consumed by RemoteDisplay SELECT_IMAGE test cases.
        self.last_image_list = None

    # === GetCapabilities (4.5.1) ===
    def get_caps_rsp(self, headers):
        parts = ['<imaging-capabilities version="1.0">']
        pf = self.ds.preferred_format
        parts.append(
            f'<preferred-format encoding="{pf["encoding"]}"'
            f' pixel="{pf["pixel"]}"'
            f' transformation="{pf["transformation"]}" />')
        for fmt in self.ds.image_formats:
            a = f'encoding="{fmt["encoding"]}"'
            if "pixel" in fmt:
                a += f' pixel="{fmt["pixel"]}"'
            if "maxsize" in fmt:
                a += f' maxsize="{fmt["maxsize"]}"'
            parts.append(f'<image-formats {a} />')
        for af in self.ds.attachment_formats:
            parts.append(
                f'<attachment-formats content-type="{af["content_type"]}" />')
        fp = self.ds.filtering_parameters
        fp_a = " ".join(f'{k}="{v}"' for k, v in fp.items() if v == "1")
        if fp_a:
            parts.append(f'<filtering-parameters {fp_a} />')
        dp = self.ds.dpof_options
        dp_a = " ".join(f'{k}="{v}"' for k, v in dp.items() if v == "1")
        if dp_a:
            parts.append(f'<DPOF-options {dp_a} />')
        parts.append('</imaging-capabilities>')
        return "\n".join(parts).encode("utf-8")

    # === Capability lookup helpers (aligned with GetCapabilities) ===
    def supported_encodings(self):
        """Return the set of encodings actually advertised by get_caps_rsp.

        This is the union of the preferred-format encoding and every
        image-formats encoding, i.e. exactly what GetCapabilities reports.
        """
        encs = set()
        pf_enc = self.ds.preferred_format.get("encoding")
        if pf_enc:
            encs.add(pf_enc.upper())
        for fmt in self.ds.image_formats:
            enc = fmt.get("encoding")
            if enc:
                encs.add(enc.upper())
        return encs

    @staticmethod
    def _pixel_in_range(pixel, spec):
        """Return True if pixel string matches a capabilities pixel spec.

        The spec may be an exact size ("160*120") or a range
        ("160*120-1280*960") as used in the image-formats entries. A range
        matches when the requested width/height fall within the lower and
        upper bounds (inclusive).
        """
        def _wh(s):
            m = re.match(r'^\s*(\d+)\s*\*\s*(\d+)\s*$', s)
            if not m:
                return None
            return int(m.group(1)), int(m.group(2))

        req = _wh(pixel)
        if req is None:
            return False
        if "-" in spec:
            lo_s, hi_s = spec.split("-", 1)
            lo = _wh(lo_s)
            hi = _wh(hi_s)
            if lo is None or hi is None:
                return False
            return (lo[0] <= req[0] <= hi[0]) and (lo[1] <= req[1] <= hi[1])
        exact = _wh(spec)
        return exact is not None and exact == req

    def is_format_supported(self, encoding, pixel):
        """Check a requested (encoding, pixel) against advertised capabilities.

        Mirrors what get_caps_rsp exposes: the encoding must be one of the
        advertised encodings, and (when a pixel is requested) it must match one
        of the pixel specs advertised for that encoding, or the preferred
        format. Either argument may be None (meaning "not specified"), in which
        case that dimension is not constrained.
        """
        if encoding is not None:
            if encoding.upper() not in self.supported_encodings():
                return False

        if pixel is not None:
            candidates = []
            pf = self.ds.preferred_format
            if pf.get("pixel") and (
                    encoding is None or
                    (pf.get("encoding") or "").upper() == encoding.upper()):
                candidates.append(pf["pixel"])
            for fmt in self.ds.image_formats:
                if encoding is not None and \
                        (fmt.get("encoding") or "").upper() != encoding.upper():
                    continue
                if fmt.get("pixel"):
                    candidates.append(fmt["pixel"])
            if not any(self._pixel_in_range(pixel, c) for c in candidates):
                return False

        return True

    # === GetImagesList (4.5.6) ===

    def get_image_list_rsp(self, headers, app_params):
        nb_max = _parse_app_param_value(
            app_params, BIPAppParamTag.NB_RETURNED_HANDLES, '>H')
        if nb_max is None:
            nb_max = 65535
        offset = _parse_app_param_value(
            app_params, BIPAppParamTag.LIST_START_OFFSET, '>H') or 0
        latest = _parse_app_param_value(
            app_params, BIPAppParamTag.LATEST_CAPTURED_IMAGES, '>B') or 0

        img_desc_xml = _get_img_desc_xml(headers)
        f_created = _parse_date_range(img_desc_xml, "created")
        f_modified = _parse_date_range(img_desc_xml, "modified")
        f_encoding = _parse_xml_attr(img_desc_xml, "encoding")

        handles = (self.ds.captured_handles_desc() if latest == 1
                   else self.ds.ordered_handles())

        filtered = []
        for h in handles:
            img = self.ds.images[h]
            if f_created:
                s, e = f_created
                if s and img.created and img.created < s:
                    continue
                if e and img.created and img.created > e:
                    continue
            if f_modified:
                s, e = f_modified
                if s and (not img.modified or img.modified < s):
                    continue
                if e and (not img.modified or img.modified > e):
                    continue
            if f_encoding and \
                    img.native_encoding.upper() != f_encoding.upper():
                continue
            filtered.append(h)

        page = filtered[offset:offset + nb_max] if nb_max > 0 else []

        parts = ['<images-listing version="1.0">']
        for h in page:
            img = self.ds.images[h]
            a = f'handle="{h}" created="{img.created}"'
            if img.modified:
                a += f' modified="{img.modified}"'
            parts.append(f'<image {a} />')
        parts.append('</images-listing>')
        body = "\n".join(parts).encode("utf-8")

        # Per BIP spec 4.5.6, the response NbReturnedHandles reports the number
        # of handles actually returned in THIS images-listing object. When the
        # request asked for 0 handles (client only wants the count), the list
        # is empty and NbReturnedHandles carries the total available count.
        if nb_max == 0:
            nb_returned = len(filtered)
        else:
            nb_returned = len(page)

        rsp_app_params = obex_build_tlv(
            {BIPAppParamTag.NB_RETURNED_HANDLES: nb_returned},
            BIPAppParamTag.TAG_SIZES)

        img_desc_rsp = b''
        if img_desc_xml and img_desc_xml.strip():
            img_desc_rsp = img_desc_xml.encode('utf-8')
        elif BIP_HDR_IMG_DESC in headers:
            # PTS sent an empty Image-Descriptor as a wildcard filter.
            # BIP spec still requires the response to include an Image-Descriptor
            # header describing the format of the returned images.
            # Use the preferred_format from BIPDataStore, which is aligned with
            # TSPX_supported_encodings / TSPX_supported_pixels PIXIT values.
            enc = self.ds.preferred_format.get("encoding", "JPEG")
            pix = self.ds.preferred_format.get("pixel", "1280*1024")
            img_desc_rsp = (
                f'<image-descriptor version="1.0">'
                f'<image encoding="{enc}" pixel="{pix}"/>'
                f'</image-descriptor>'
            ).encode()

        return body, bytes(rsp_app_params), img_desc_rsp

    # === GetImageProperties (4.5.7) ===
    def get_image_properties_rsp(self, headers):
        img_handle = self._extract_handle(headers)
        img = self.ds.images.get(img_handle)
        if not img:
            img = next(iter(self.ds.images.values()))

        h = f'<image-properties version="1.0" handle="{img.handle}"'
        if img.friendly_name:
            h += f' friendly-name="{img.friendly_name}"'
        h += '>'
        parts = [h]
        na = f'encoding="{img.native_encoding}" pixel="{img.native_pixel}"'
        if img.native_size:
            na += f' size="{img.native_size}"'
        parts.append(f'<native {na}/>')
        for v in img.variants:
            va = f'encoding="{v.encoding}" pixel="{v.pixel}"'
            if v.maxsize:
                va += f' maxsize="{v.maxsize}"'
            if v.transformation:
                va += f' transformation="{v.transformation}"'
            parts.append(f'<variant {va} />')
        for att in img.attachments:
            aa = f'content-type="{att.content_type}" name="{att.name}"'
            if att.size is not None:
                aa += f' size="{att.size}"'
            if att.charset:
                aa += f' charset="{att.charset}"'
            if att.created:
                aa += f' created="{att.created}"'
            parts.append(f'<attachment {aa}/>')
        parts.append('</image-properties>')
        return "\n".join(parts).encode("utf-8")

    # === GetImage (4.5.8) ===
    def get_image_rsp(self, headers):
        img_handle = self._extract_handle(headers)
        img = self.ds.images.get(img_handle)
        if img and img.image_data:
            return img.image_data
        return next(iter(self.ds.images.values())).image_data

    # === GetLinkedThumbnail (4.5.9) ===
    def get_linked_thumbnail_rsp(self, headers):
        img_handle = self._extract_handle(headers)
        img = self.ds.images.get(img_handle)
        if img and img.thumbnail_data:
            return img.thumbnail_data
        return _make_dummy_jpeg(160, 120)

    # === GetLinkedAttachment (4.5.10) ===
    @staticmethod
    def _extract_name(headers):
        """Decode the OBEX Name header (attachment file name) to a string."""
        raw = headers.get(OBEXHdr.NAME)
        if not raw:
            return ""
        if isinstance(raw, (bytes, bytearray)):
            try:
                return raw.decode('utf-16-be').rstrip('\x00')
            except UnicodeDecodeError:
                return raw.decode('utf-8', errors='replace').rstrip('\x00')
        return str(raw)

    def find_attachment_data(self, handle, name):
        """Return the attachment bytes referenced by (handle, name).

        Spec 4.5.10: an attachment is referenced by the linked image handle
        plus the attachment file name (OBEX Name header). Returns None when
        the image or the named attachment does not exist.
        """
        img = self.ds.images.get(handle)
        if not img or not img.attachments:
            return None
        if not name:
            return None
        for att in img.attachments:
            if att.name == name:
                return att.data
        return None

    def get_linked_attachment_rsp(self, headers):
        handle = self._extract_handle(headers)
        name = self._extract_name(headers)
        data = self.find_attachment_data(handle, name)
        if data is not None:
            return data
        return b"attachment data"

    # === GetPartialImage (4.5.13) ===
    def get_partial_image_rsp(self, headers, app_params):
        name_raw = headers.get(OBEXHdr.NAME)
        name = ""
        if isinstance(name_raw, (bytes, bytearray)):
            try:
                name = name_raw.decode('utf-16-be').rstrip('\x00')
            except UnicodeDecodeError:
                name = name_raw.decode('utf-8', errors='replace')
        img = next((i for i in self.ds.images.values()
                    if i.friendly_name == name), None)
        if not img:
            img = next(iter(self.ds.images.values()))

        data = img.image_data or b""
        total_size = len(data)
        start = _parse_app_param_value(
            app_params, BIPAppParamTag.PARTIAL_FILE_START_OFFSET, '>I') or 0
        length = _parse_app_param_value(
            app_params, BIPAppParamTag.PARTIAL_FILE_LENGTH, '>I') or 0xFFFFFFFF

        end_pos = min(start + length, total_size)
        chunk = data[start:end_pos] if start < total_size else b""
        end_flag = 1 if end_pos >= total_size else 0

        rsp_app_params = obex_build_tlv(
            {BIPAppParamTag.TOTAL_FILE_SIZE: total_size,
             BIPAppParamTag.END_FLAG: end_flag},
            BIPAppParamTag.TAG_SIZES)

        return chunk, bytes(rsp_app_params)

    # === GetMonitoringImage (4.5.16) ===
    def get_monitoring_image_rsp(self, headers):
        # Spec Table 4.50: the response always carries an Img-Handle header
        # (empty when there is no handle to return) plus the monitoring image
        # object in Body/EndOfBody. When StoreFlag (tag 0x0A) is 0x01 the
        # server must store the full-size captured image and return its
        # handle; 0x00 means do not store (Img-Handle present but empty).
        app_params = headers.get(OBEXHdr.APP_PARAM, {})
        store_flag = _parse_app_param_value(
            app_params, BIPAppParamTag.STORE_FLAG, '>B') or 0

        img_handle = None
        if store_flag == 0x01:
            # Store a full-size captured image and return its handle.
            handle = self.ds.next_handle()
            now = datetime.datetime.now(
                timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            full_image = _make_dummy_jpeg(640, 480)
            self.ds.add_image(ImageRecord(
                handle=handle,
                friendly_name=f"captured_{handle}.jpg",
                created=now,
                native_encoding="JPEG",
                native_pixel="640*480",
                native_size=len(full_image),
                image_data=full_image,
                thumbnail_data=_make_dummy_jpeg(160, 120),
                is_captured=True,
                variants=[
                    ImageVariant("JPEG", "160*120"),
                ]))
            img_handle = _handle_to_utf16(handle)

        return self.ds.monitoring_image_data, img_handle

    # === GetStatus (4.5.15) ===
    def get_status_rsp(self, secondary_active):
        # Spec Table 4.48: the GetStatus response carries only a Response
        # Code and no OBEX headers (not even Body/EndOfBody). The code
        # reports the state of the secondary connection:
        #   Success  = secondary connection has terminated
        #   Continue = secondary connection is still active
        # The secondary_active flag is derived from the live OBEX session
        # state (see BIP.build_get_status_rsp) rather than a side-band flag.
        if secondary_active:
            return OBEXRspCode.CONTINUE, b''
        return OBEXRspCode.SUCCESS, b''

    # === PutImage (4.5.2) ===
    # === PutImage (4.5.2) ===
    def put_image_rsp(self, final, headers):
        name = None
        name_raw = headers.get(OBEXHdr.NAME)
        if isinstance(name_raw, (bytes, bytearray)):
            try:
                name = name_raw.decode('utf-16-be').rstrip('\x00')
            except UnicodeDecodeError:
                name = name_raw.decode('utf-8', errors='replace')
        elif name_raw is not None:
            name = str(name_raw)

        img_desc_xml = _get_img_desc_xml(headers)

        # 2. If not final and no ongoing PUT, create a new image record
        if not final and not getattr(self, '_current_put_handle', None):
            handle = self.ds.next_handle()
            now = datetime.datetime.now(
                timezone.utc).strftime("%Y%m%dT%H%M%SZ")

            encoding = "JPEG"
            pixel = "640*480"
            if img_desc_xml:
                enc = _parse_xml_attr(img_desc_xml, "encoding")
                if enc:
                    encoding = enc
                pix = _parse_xml_attr(img_desc_xml, "pixel")
                if pix:
                    pixel = pix

            friendly_name = name if name else f"received_{handle}.jpg"

            self.ds.add_image(ImageRecord(
                handle=handle,
                friendly_name=friendly_name,
                created=now,
                native_encoding=encoding,
                native_pixel=pixel,
                native_size=0,
                image_data=b"",
                thumbnail_data=_make_dummy_jpeg(160, 120)))
            self._current_put_handle = handle

        # 3. Append body data to the image if present, regardless of final
        body = headers.get(OBEXHdr.BODY) or headers.get(OBEXHdr.END_BODY)
        if body and getattr(self, '_current_put_handle', None):
            img = self.ds.images.get(self._current_put_handle)
            if img:
                img.image_data += body
                img.native_size = len(img.image_data)

        # 4. Always return the same Img-Handle for this image
        handle = getattr(self, '_current_put_handle', None)
        if not handle:
            handle = self.ds.next_handle()
        img_handle = _handle_to_utf16(handle)

        if final:
            self._current_put_handle = None
            if self.put_image_final_partial_content:
                return OBEXRspCode.PARTIAL_CONTENT, img_handle
            return OBEXRspCode.SUCCESS, img_handle

        return OBEXRspCode.CONTINUE, img_handle

    # === PutLinkedThumbnail (4.5.3) ===
    def put_linked_thumbnail_rsp(self, final, headers):
        # Resolve the linked image handle carried in this request. The handle
        # was allocated by the preceding PutImage and must reference an
        # existing image record; store the received thumbnail bytes back onto
        # that record so a subsequent GetLinkedThumbnail returns the same data.
        handle = self._extract_handle(headers)
        if handle and handle in self.ds.images:
            self._current_thm_handle = handle
        target = getattr(self, '_current_thm_handle', None)

        body = headers.get(OBEXHdr.BODY) or headers.get(OBEXHdr.END_BODY)
        if body and target and target in self.ds.images:
            img = self.ds.images[target]
            # Accumulate across multi-packet PUTs. The first fragment of a new
            # thumbnail transfer replaces any pre-seeded dummy thumbnail.
            if not getattr(self, '_thm_in_progress', False):
                img.thumbnail_data = b""
                self._thm_in_progress = True
            img.thumbnail_data += body

        if final:
            self._current_thm_handle = None
            self._thm_in_progress = False
            return OBEXRspCode.SUCCESS, b''
        return OBEXRspCode.CONTINUE, b''

    # === PutLinkedAttachment (4.5.4) ===
    def put_linked_attachment_rsp(self, final, headers):
        # Resolve the linked image handle and the attachment descriptor so the
        # received attachment is stored against the correct image record. A
        # subsequent GetLinkedAttachment / GetImageProperties then reflects the
        # data that was actually pushed.
        handle = self._extract_handle(headers)
        if handle and handle in self.ds.images:
            self._current_att_handle = handle
        target = getattr(self, '_current_att_handle', None)

        # Parse the attachment-descriptor (carried in the Img-Description
        # header) once, on the first fragment, to learn the attachment name
        # and content-type.
        if not getattr(self, '_att_in_progress', False):
            desc_xml = _get_img_desc_xml(headers) or ""
            att_name = _parse_xml_attr(desc_xml, "name") or "attachment.txt"
            att_ctype = _parse_xml_attr(desc_xml, "content-type") \
                or "text/plain"
            att_charset = _parse_xml_attr(desc_xml, "charset")
            self._current_att_meta = {
                "name": att_name,
                "content_type": att_ctype,
                "charset": att_charset,
            }

        body = headers.get(OBEXHdr.BODY) or headers.get(OBEXHdr.END_BODY)
        if target and target in self.ds.images:
            img = self.ds.images[target]
            meta = getattr(self, '_current_att_meta', {}) or {}
            att = None
            for existing in img.attachments:
                if existing.name == meta.get("name"):
                    att = existing
                    break
            if att is None:
                att = ImageAttachment(
                    name=meta.get("name", "attachment.txt"),
                    content_type=meta.get("content_type", "text/plain"),
                    charset=meta.get("charset"),
                    data=b"")
                img.attachments.append(att)
            if not getattr(self, '_att_in_progress', False):
                att.data = b""
                self._att_in_progress = True
            if body:
                att.data += body
            att.size = len(att.data)

        if final:
            self._current_att_handle = None
            self._current_att_meta = None
            self._att_in_progress = False
            return OBEXRspCode.SUCCESS, b''
        return OBEXRspCode.CONTINUE, b''

    # === RemoteDisplay (4.5.5) ===
    def remote_display_rsp(self, final, headers):
        handles = self.ds.ordered_handles()
        if not handles:
            return OBEXRspCode.SUCCESS, _handle_to_utf16("0000000")
        app_params = headers.get(OBEXHdr.APP_PARAM, {})
        cmd = _parse_app_param_value(
            app_params, BIPAppParamTag.REMOTE_DISPLAY, '>B')
        if cmd is None:
            cmd = BIPRemoteDisplay.CURRENT_IMAGE
        idx = self.ds.display_index
        if cmd == BIPRemoteDisplay.NEXT_IMAGE:
            idx = min(idx + 1, len(handles) - 1)
        elif cmd == BIPRemoteDisplay.PREVIOUS_IMAGE:
            idx = max(idx - 1, 0)
        elif cmd == BIPRemoteDisplay.SELECT_IMAGE:
            img_handle = self._extract_handle(headers)
            if img_handle in handles:
                idx = handles.index(img_handle)
        self.ds.display_index = idx
        return OBEXRspCode.SUCCESS, _handle_to_utf16(handles[idx])

    # === DeleteImage (4.5.11) ===
    def delete_image_rsp(self, final, headers):
        img_handle = self._extract_handle(headers)
        if img_handle:
            self.ds.remove_image(img_handle)
        return OBEXRspCode.SUCCESS, b''

    # === StartPrint (4.5.12) ===
    def start_print_rsp(self, final, headers):
        # The printer-control object (a DPOF 1.1 text description) arrives in
        # the Body/End-Body of the StartPrint PUT and can span several packets.
        # Accumulate it and, once complete, extract the IMG SRC file names so a
        # later GetPartialImage can reference them.
        body = headers.get(OBEXHdr.BODY) or headers.get(OBEXHdr.END_BODY)
        if body:
            if not getattr(self, '_print_body_in_progress', False):
                self._print_body = b''
                self._print_body_in_progress = True
            self._print_body += body

        if final:
            self._print_body_in_progress = False
            self._extract_print_img_src()

        if final:
            return OBEXRspCode.SUCCESS, b''
        return OBEXRspCode.CONTINUE, b''

    def _extract_print_img_src(self):
        body = getattr(self, '_print_body', b'')
        if not body:
            return
        text = body.decode('utf-8', errors='replace')
        self.print_img_srcs = re.findall(
            r'<IMG\s+SRC\s*=\s*"([^"]+)"', text, re.IGNORECASE)

    def get_print_img_src(self):
        srcs = getattr(self, 'print_img_srcs', None)
        return srcs[0] if srcs else None

    def set_last_image_list(self, handles):
        self.last_image_list = handles

    def get_last_image_list(self):
        return self.last_image_list

    # === StartArchive (4.5.14) ===
    def start_archive_rsp(self, final, headers):
        return OBEXRspCode.SUCCESS, b''

    # --- public helpers ---
    def extract_handle(self, headers):
        """Public wrapper: decode the Img-Handle header to a string."""
        return self._extract_handle(headers)

    def has_image(self, handle):
        """Return True if *handle* refers to an existing image record."""
        return handle in self.ds.images

    # --- internal ---
    @staticmethod
    def _extract_handle(headers):

        raw = headers.get(BIP_HDR_IMG_HANDLE)
        if not raw:
            return ""
        if isinstance(raw, (bytes, bytearray)):
            try:
                return raw.decode('utf-16-be').rstrip('\x00')
            except UnicodeDecodeError:
                return raw.decode('utf-8', errors='replace').rstrip('\x00')
        return str(raw)


class BIPSrmState:
    DISABLED = 0
    ENABLING = 1
    ENABLED = 2
    ENABLED_SRMP = 3


class BIPSrmFlag:
    SRM_LOCAL = 0x01
    SRM_REMOTE = 0x02
    SRMP_LOCAL = 0x04
    SRMP_REMOTE = 0x08


class BIPObexRole:
    """Role of an OBEX logical connection carried over one transport.

    A single BIP transport connection (RFCOMM or L2CAP) can carry more than
    one OBEX connection. The primary connection targets the Imaging Service;
    the secondary connections target the Referenced Objects and Archived
    Objects services used by Advanced Image Printing and Automatic Archive.
    """
    PRIMARY = 0
#     SEC_REFERENCED = 1
#     SEC_ARCHIVED = 2
    # Generic secondary role used when the concrete sub-type is not tracked.
    SECONDARY = 1

    @staticmethod
    def from_conn_type(conn_type):
        """Map a BIPConnType value to an OBEX session role.

        Any non-primary connection type is treated as a secondary session.
        The default (SEC_REFERENCED) is used when the concrete sub-type is
        not distinguished by the caller.
        """
        sec_archived = getattr(types.BIPConnType, 'SEC_ARCHIVED_OBJECTS', None)
        if sec_archived is not None and conn_type == sec_archived:
            return BIPObexRole.SEC_ARCHIVED
        return BIPObexRole.SEC_REFERENCED


class OBEXSession:
    """State of a single OBEX logical connection.

    Each session owns its own connection id, OBEX-connected flag, target,
    SRM negotiation state, receive/transmit queues and reassembly buffers so
    that a primary and a secondary session sharing one transport do not clash
    (for example the secondary CONNECT no longer overwrites the primary
    connection id).
    """

    def __init__(self, role=BIPObexRole.PRIMARY, connection=None):
        self.role = role
        # Back-reference to the owning transport-level BIPConnection (used only
        # for lifecycle bookkeeping). The transport type is owned per-session:
        # a primary (Image Push) and a secondary (Referenced/Archived Objects)
        # OBEX session share one BIPConnection but may ride different transports
        # (L2CAP vs RFCOMM), so is_srm_allowed() reads the session's own
        # transport_type rather than a single shared value.
        self.connection = connection
        self.obex_connected = False
        self.transport_type = None

        self.conn_id = None
        self.conn_info = {}
        self.data_rx = {}
        self.data_tx = {}
        self.srm_flags = 0
        self.srmp_wait_count = 0
        self._pending_body = {}
        # Per-operation transfer state (was module-level globals). Kept on the
        # session so an aborted or disconnected transfer cannot leak its
        # continuation/offset state into another connection or test case.
        self.pending_put = None
        self.chunk_offsets = {}
        # Guards data_rx and wakes any thread waiting in rx_data_get /
        # wait_for_operation_complete as soon as a new entry is enqueued.
        # This removes the pure busy-poll race where an entry was enqueued
        # but the waiter did not observe it in time.
        self._rx_cond = Condition()

    def is_srm_enabled(self):
        return (self.srm_flags & 0x03) == 0x03

    def is_srm_full_speed(self):
        return self.is_srm_enabled() and not (self.srm_flags & 0x0C)

    def is_srm_allowed(self):
        # SRM is a GOEP 2.0 / L2CAP-only feature. Whether it may be used at all
        # depends on the transport this session rides, which is owned per-session
        # (primary and secondary may use different transports).
        return self.transport_type == types.BIPTransportType.L2CAP_CONN

    def reset_srm(self):
        self.srm_flags = 0
        self.srmp_wait_count = 0

    def set_obex(self):
        self.obex_connected = True

    def clear_obex(self):
        self.obex_connected = False

    def is_obex_connected(self):
        return self.obex_connected

    def rx(self, ev, data):
        # Enqueue under the condition lock and wake any waiter so that a newly
        # arrived entry is guaranteed to be observed (no busy-poll race where
        # the entry is enqueued but the waiter never sees it in time).
        with self._rx_cond:
            self.data_rx.setdefault(ev, []).append(data)
            self._rx_cond.notify_all()

    def rx_data_get(self, ev, timeout, clear):
        with self._rx_cond:
            def _ready():
                return ev in self.data_rx and len(self.data_rx[ev]) != 0

            if not _ready():
                # wait_for() releases the lock while blocking and re-acquires
                # it before returning; it returns False on timeout.
                self._rx_cond.wait_for(_ready, timeout=timeout)

            if _ready():
                if clear:
                    return self.data_rx[ev].pop(0)
                return self.data_rx[ev][0]

            return None

    def wait_for_operation_complete(self, ev, rsp_code=None, timeout=30):
        """Wait for a client response event matching *rsp_code* on this session.

        Returns (rsp_code, body) on success, or None on timeout.
        """
        def _has_matching():
            entries = self.data_rx.get(ev, [])
            if rsp_code is None:
                return len(entries) > 0
            return any(e[0] == rsp_code for e in entries)

        with self._rx_cond:
            if not self._rx_cond.wait_for(_has_matching, timeout=timeout):
                return None

            entries = self.data_rx.get(ev, [])
            if rsp_code is None:
                return self.data_rx[ev].pop(0)
            for i, entry in enumerate(entries):
                if entry[0] == rsp_code:
                    return self.data_rx[ev].pop(i)
            return None


class BIPConnection:
    """Transport-level BIP connection owning one or more OBEX sessions.

    A primary OBEX session is created eagerly. Call sites operate on a
    specific session explicitly via get_session()/get_or_add_session(role);
    secondary sessions are added on demand and kept fully isolated.
    """

    def __init__(self, address):
        self.address = address
        self.sessions = {}
        # Eagerly create the primary session. All per-session state is
        # accessed explicitly through get_session()/get_or_add_session(role).
        self.add_session(BIPObexRole.PRIMARY)

    # ---- session lifecycle ----
    def add_session(self, role):
        session = OBEXSession(role, connection=self)
        self.sessions[role] = session
        return session

    def get_session(self, role=BIPObexRole.PRIMARY):
        return self.sessions.get(role)

    def get_or_add_session(self, role):
        return self.sessions.get(role) or self.add_session(role)

    def remove_session(self, role):
        self.sessions.pop(role, None)

    def is_secondary_active(self):
        return any(role != BIPObexRole.PRIMARY and s.is_obex_connected()
                   for role, s in self.sessions.items())

    def find_session_by_conn_id(self, conn_id):
        for session in self.sessions.values():
            if session.conn_id == conn_id:
                return session
        return None


class BIPSdpConnection:
    def __init__(self, address, rfcomm_channel, l2cap_psm,
                 caps, features, functions):
        self.address = address
        self.rfcomm_channel = rfcomm_channel
        self.l2cap_psm = l2cap_psm
        self.caps = caps
        self.features = features
        self.functions = functions


class BIP:
    def __init__(self):
        from autopts.pybtp.btp.bip import BIPEventHandler
        self.event_handler = BIPEventHandler(self)
        self.event_handler.start()
        self.bip_connections = {}
        self.sdp_connections = {}
        self.image_db = BIPImageDatabase()
        self.auto_response_enabled = False
        self.default_srmp_wait_count = 0

    def enable_auto_response(self):
        self.auto_response_enabled = True

    def disable_auto_response(self):
        self.auto_response_enabled = False

    # ---- SDP connection management ----

    def add_sdp_connection(self, address, rfcomm_channel, l2cap_psm,
                           caps, features, functions):
        self.sdp_connections[address] = BIPSdpConnection(
            address, rfcomm_channel, l2cap_psm,
            caps, features, functions)

    def get_sdp_connection(self, address):
        return self.sdp_connections.get(address)

    def remove_sdp_connection(self, address):
        if address in self.sdp_connections:
            del self.sdp_connections[address]

    def wait_for_sdp_finished(self, address, timeout=30):
        wait_for_event(
            timeout,
            lambda: self.get_sdp_connection(address) is not None)
        return self.get_sdp_connection(address) is not None

    # ---- Transport connection management ----

    def add_bip_connection(self, address,
                           transport_type: types.BIPTransportType,
                           role=BIPObexRole.PRIMARY):
        # A single BR/EDR link can raise more than one transport-connected
        # event for the same address: e.g. the primary L2CAP/RFCOMM transport
        # first, then a second transport for the secondary (Referenced/Archived
        # Objects) server used by Advanced Image Printing / Automatic Archive.
        # If a connection already exists for this address, preserve it (and all
        # its per-session state, most importantly the primary OBEX conn_id that
        # was assigned on CONNECT). Rebuilding the BIPConnection here would wipe
        # that conn_id and cause later requests such as GetCapabilities to omit
        # the required Connection-ID header. The transport type is recorded on
        # the role's own session so a primary L2CAP and a secondary RFCOMM
        # (or vice versa) no longer overwrite each other.
        conn = self.bip_connections.get(address)
        if conn is None:
            conn = BIPConnection(address)
            self.bip_connections[address] = conn
        session = conn.get_or_add_session(role)
        session.transport_type = transport_type
        session.srmp_wait_count = self.default_srmp_wait_count

    def get_bip_connection(self, address):
        return self.bip_connections.get(address)

    def remove_bip_connection(self, address,
                              transport_type: types.BIPTransportType,
                              role=BIPObexRole.PRIMARY):
        conn = self.get_bip_connection(address)
        if conn is None:
            return
        session = conn.get_session(role)
        if session and session.transport_type == transport_type:
            session.transport_type = None
        # Only drop the whole connection once no session still has an active
        # transport. This lets a secondary disconnect clean up its own transport
        # without tearing down a still-active primary (and vice versa).
        if not any(s.transport_type is not None
                   for s in conn.sessions.values()):
            del self.bip_connections[address]

    def wait_for_bip_connection(self, address, timeout=30):
        wait_for_event(
            timeout,
            lambda: self.get_bip_connection(address) is not None)
        return self.get_bip_connection(address) is not None

    def wait_for_bip_disconnection(self, address, timeout=30):
        wait_for_event(
            timeout,
            lambda: self.get_bip_connection(address) is None)
        return self.get_bip_connection(address) is None

    # ---- OBEX connection management ----

    def add_bip_obex_connection(self, address, role=BIPObexRole.PRIMARY):
        conn = self.get_bip_connection(address)
        if conn:
            session = conn.get_or_add_session(role)
            session.set_obex()

    def is_bip_obex_connected(self, address, role=BIPObexRole.PRIMARY,
                              timeout=5):
        # The transport-level connection and the per-role OBEX session objects
        # are created lazily when the corresponding BTP events are processed by
        # the rx thread (e.g. BTP_BIP_EV_SECOND_CLIENT_CONNECTED for a
        # SECONDARY role). Calling this helper immediately after issuing the
        # connect command can race that event, so evaluate the full connected
        # condition inside the wait rather than bailing out early when the
        # conn/session are not present yet.
        def _is_connected():
            conn = self.get_bip_connection(address)
            if conn is None:
                return False
            session = conn.get_session(role)
            if session is None:
                return False
            return session.is_obex_connected()

        if timeout > 0:
            wait_for_event(timeout, _is_connected)
        return _is_connected()

    def remove_bip_obex_connection(self, address, role=BIPObexRole.PRIMARY):
        conn = self.get_bip_connection(address)
        if conn:
            session = conn.get_session(role)
            if session:
                session.clear_obex()

    def is_bip_secondary_active(self, address):
        conn = self.get_bip_connection(address)
        return bool(conn and conn.is_secondary_active())

    def has_pending_second_connect(self, address):
        """Return True if a secondary (Referenced/Archived Objects) server
        OBEX CONNECT is awaiting a response.

        The secondary server CONNECT request event is enqueued on the primary
        session's rx queue (see _bip_ev_second_server_connect_req), so a
        pending entry there means WID 4004 must be answered on the secondary
        server via second_connect_rsp rather than the primary connect_rsp.
        """
        conn = self.get_bip_connection(address)
        if conn is None:
            return False
        session = conn.get_session(BIPObexRole.PRIMARY)
        if session is None:
            return False
        entries = session.data_rx.get(
            defs.BTP_BIP_EV_SECOND_SERVER_CONNECT_REQ, [])
        return len(entries) > 0

    def build_get_status_rsp(self, address):
        """Build the GetStatus (4.5.15) response from live connection state.

        The response code reports the state of the secondary connection:
          Success  = secondary connection has terminated
          Continue = secondary connection is still active
        The active flag is derived from the connection's secondary OBEX
        session rather than a side-band data-store flag.
        """
        active = self.is_bip_secondary_active(address)
        return self.image_db.get_status_rsp(active)

    # ---- Connection data rx/tx proxy ----

    def rx(self, address, ev, data, role=BIPObexRole.PRIMARY):
        conn = self.get_bip_connection(address)
        if conn is None:
            return
        session = conn.get_session(role)
        if session is None:
            return
        session.rx(ev, data)

    def rx_data_get(self, address, ev, timeout=10, clear=True,
                    role=BIPObexRole.PRIMARY):
        conn = self.get_bip_connection(address)
        if conn is None:
            return None
        session = conn.get_session(role)
        if session is None:
            return None
        return session.rx_data_get(ev, timeout, clear)

    def wait_for_operation_complete(self, address, ev, rsp_code=None,
                                    timeout=30, role=BIPObexRole.PRIMARY):
        """Wait for a client response event matching *rsp_code*.

        Polls the rx queue of the given OBEX session until an entry whose
        first element equals *rsp_code* is found, or until *timeout* seconds
        elapse. If *rsp_code* is None, returns the first entry that arrives.

        Returns (rsp_code, body) on success, or None on timeout.
        """
        conn = self.get_bip_connection(address)
        if conn is None:
            return None
        session = conn.get_session(role)
        if session is None:
            return None
        return session.wait_for_operation_complete(ev, rsp_code, timeout)
