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

import logging
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import defs
from autopts.pybtp.types import OBEXRspCode

# The working folder name must match the value of TSPX_working_folder_path
FTP_WORKING_FOLDER_PATH = 'pts'


# ---------------------------------------------------------------------------
# FTP Virtual Filesystem (in-memory, zero external dependencies)
# ---------------------------------------------------------------------------

# Permission mask format (3 octets): [User][Group][Other]
# Per-octet permission bits:
#   bit0 = Read
#   bit1 = Write
#   bit2 = Delete
#   bit7 = Modify Permissions
#
# Example:
#   0x870505 -> User: Read/Write/Delete/Modify Permissions
#               Group: Read/Delete
#               Other: Read/Delete
def _make_file(data: bytes, perms: int = 0x878787) -> dict:
    return {'_type': 'file', 'data': data, 'perms': perms}


def _make_dir(children: dict = None, perms: int = 0x878787) -> dict:
    return {'_type': 'dir', 'children': dict(children) if children else {}, 'perms': perms}


# Small (~10 KB), medium (~50 KB), and large (~2 MB) pre-seeded file content
_SMALL = b'\x00' * 10240
_MEDIUM = b'\x00' * 51200
_LARGE = b'\x00' * (2 * 1024 * 1024)


def _default_tree() -> dict:
    """Build the default FTP server virtual filesystem per FTP ATS section 6.2."""
    return _make_dir({
        FTP_WORKING_FOLDER_PATH: _make_dir({
            # Folders required by ATS 6.2
            'OTR_BV_08_I': _make_dir({
                'sub': _make_dir({
                    'sub_file.txt': _make_file(_SMALL),
                }),
                'file.txt': _make_file(_SMALL),
            }),
            'OTR_BV_09_I': _make_dir({
                'sub': _make_dir({
                    'sub_file.txt': _make_file(_SMALL),
                }),
                'file.txt': _make_file(_SMALL),
            }),
            'OTR_BV_10_I': _make_dir({
                'sub': _make_dir({
                    'sub_file.txt': _make_file(_SMALL),
                }),
                'file.txt': _make_file(_SMALL),
            }),
            'OMA_BV_06_I': _make_dir({}),
            'OMA_BV_07_I': _make_dir({
                'sub': _make_dir({
                    'sub_file.txt': _make_file(_SMALL),
                }),
                'file.txt': _make_file(_SMALL),
            }),
            'OMA_BV_08_I': _make_dir({
                'sub': _make_dir({
                    'sub_file.txt': _make_file(_SMALL),
                }),
                'file.txt': _make_file(_SMALL),
            }),
            # Files required by ATS 6.2
            'OTR_BV_11.txt':     _make_file(_SMALL),
            'OTR_BV_12_I.txt':   _make_file(_SMALL),
            'OMA_BV_04_I.txt':   _make_file(_SMALL),
            'OMA_BV_05_I.txt':   _make_file(_SMALL),
            'ACT_BV_04_C.txt':   _make_file(_SMALL),
            'ACT_BV_06_C.txt':   _make_file(_SMALL),
            'SRMP_BI_02_C.txt':  _make_file(_MEDIUM),
            # Get Files required by ATS 6.2
            'get.txt':           _make_file(_SMALL),
        }),
    })


class FtpStorage:
    """In-memory virtual FTP filesystem for the FTP server role.

    Directory structure is stored as nested dicts. Paths are handled via
    PurePosixPath (stdlib, no I/O). Python process exit automatically
    reclaims all memory.

    Supported operations (matching btp_ftp.h server commands):
        set_folder(name, flags)              -- SET_PATH / navigate
        build_folder_listing()               -- GET folder listing -> XML bytes
        push_file(name, data)                -- PUT (receive file from client)
        pull_file(name)                      -- GET (send file to client)
        delete(name)                         -- DELETE file or folder
        copy(src_name, dst_name)             -- COPY ACTION
        rename(src_name, dst_name)           -- MOVE/RENAME ACTION
        set_permissions(name, perms)         -- SET PERMISSIONS ACTION
        create_folder(name, perms)           -- SET_PATH with create flag
        is_existing_folder_name(name)        -- Check if folder name exists
        is_existing_file_name(name)          -- Check if file name exists
    """

    # Set path operation flags
    SET_PATH_FLAG_NAVIGATE = 0x02   # navigate to child / root
    SET_PATH_FLAG_BACKUP = 0x03   # go up one level

    # Permission bit indices
    PERM_READ = 0
    PERM_WRITE = 1
    PERM_DELETE = 2
    PERM_MODPERM = 7

    def __init__(self):
        self._root = _default_tree()
        self._cwd = PurePosixPath('/')  # absolute path inside virtual FS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, path: PurePosixPath) -> dict | None:
        """Walk the tree and return the node at *path*, or None."""
        node = self._root
        # path.parts[0] == '/' (root sentinel)
        for part in path.parts[1:]:
            if node['_type'] != 'dir':
                return None
            node = node['children'].get(part)
            if node is None:
                return None
        return node

    def _resolve_cwd(self) -> dict | None:
        return self._resolve(self._cwd)

    def _cwd_str(self) -> str:
        return str(self._cwd)

    def _to_abs(self, path_str: str) -> PurePosixPath:
        """Convert a path string to an absolute PurePosixPath.
        Strings starting with '/' are treated as absolute (from virtual root).
        All other strings are resolved relative to the current working directory.
        """
        if path_str.startswith('/'):
            return PurePosixPath(path_str)
        return self._cwd / path_str

    def _resolve_parent(self, abs_path: PurePosixPath):
        """Return (parent_node, entry_name) for *abs_path*, or (None, None) on error."""
        parent_node = self._resolve(abs_path.parent)
        if parent_node is None or parent_node['_type'] != 'dir':
            return None, None
        return parent_node, abs_path.name

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_perm(node: dict, bit: int) -> bool:
        """Return True if the User permission *bit* is set in *node*."""
        user_byte = (node['perms'] >> 16) & 0xFF
        return bool(user_byte & (1 << bit))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def set_folder(self, name: str, flags: int) -> int:
        """Navigate the virtual filesystem.

        flags == SET_PATH_FLAG_BACKUP  -> go up one level (name ignored)
        flags == SET_PATH_FLAG_NAVIGATE:
            name == '' -> go to root
            otherwise -> navigate into child named *name*

        Returns OBEXRspCode on success or error.
        """
        if flags == self.SET_PATH_FLAG_BACKUP:
            if self._cwd == PurePosixPath('/'):
                return OBEXRspCode.FORBIDDEN  # already at root
            self._cwd = self._cwd.parent
            logging.debug('FtpStorage: cwd -> %s', self._cwd)
            return OBEXRspCode.SUCCESS

        if flags == self.SET_PATH_FLAG_NAVIGATE:
            if not name:
                self._cwd = PurePosixPath('/')
                logging.debug('FtpStorage: cwd -> / (root)')
                return OBEXRspCode.SUCCESS

            target = self._cwd / name
            node = self._resolve(target)
            if node is None or node['_type'] != 'dir':
                logging.warning('FtpStorage: set_folder %r not found', name)
                return OBEXRspCode.NOT_FOUND

            if not self._check_perm(node, self.PERM_READ):
                logging.warning('FtpStorage: set_folder %r permission denied', name)
                return OBEXRspCode.UNAUTH

            self._cwd = target
            logging.debug('FtpStorage: cwd -> %s', self._cwd)
            return OBEXRspCode.SUCCESS

        logging.warning('FtpStorage: set_folder flag %d not supported', flags)
        return OBEXRspCode.NOT_FOUND

    def create_folder(self, name: str, perms: int = 0x878787) -> int:
        """Create a new subdirectory in the current working directory.

        Returns OBEXRspCode on success or error.
        """
        if not name or '/' in name:
            return OBEXRspCode.BAD_REQ
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND
        if not self._check_perm(cwd_node, self.PERM_WRITE):
            logging.warning('FtpStorage: create_folder %r permission denied in %s', name, self._cwd)
            return OBEXRspCode.UNAUTH
        if name in cwd_node['children']:
            return OBEXRspCode.FORBIDDEN  # already exists
        cwd_node['children'][name] = _make_dir(None, perms)
        logging.debug('FtpStorage: created folder %r in %s', name, self._cwd)
        return OBEXRspCode.SUCCESS

    def is_existing_folder_name(self, name: str) -> bool:
        """Return True if *name* is a existing child folder name in the CWD."""
        if not name:
            return False
        invalid = set('/\\\0<>:"|?*')
        if any(c in invalid for c in name):
            return False
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return False
        child = cwd_node['children'].get(name)
        return child is not None and child['_type'] == 'dir'

    def is_existing_file_name(self, name: str) -> bool:
        """Return True if *name* is already exists in the CWD.

        Returns False if *name* is empty, contains invalid characters,
        the CWD cannot be resolved, or a file with that name does NOT
        already exist in the CWD.
        """
        if not name:
            return False
        invalid = set('/\\\0<>:"|?*')
        if any(c in invalid for c in name):
            return False
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return False
        child = cwd_node['children'].get(name)
        return child is not None and child['_type'] != 'dir'

    def check_write_permission(self) -> int:
        """Check if the CWD allows writing (push_file / create_folder).

        Returns OBEXRspCode.SUCCESS if allowed, or an error code.
        Can be called before push_file to reject early on the first packet.
        """
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND
        if not self._check_perm(cwd_node, self.PERM_WRITE):
            return OBEXRspCode.UNAUTH
        return OBEXRspCode.SUCCESS

    # ------------------------------------------------------------------
    # Folder listing
    # ------------------------------------------------------------------

    def build_folder_listing(self) -> tuple[int, bytes]:
        """Return (OBEXRspCode, folder-listing XML bytes) for CWD.

        Returns FORBIDDEN if the CWD does not have Read permission.
        Returns NOT_FOUND if the CWD cannot be resolved.
        Returns SUCCESS with the XML bytes on success.
        """
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND, b''

        if not self._check_perm(cwd_node, self.PERM_READ):
            logging.warning('FtpStorage: build_folder_listing permission denied in %s', self._cwd)
            return OBEXRspCode.UNAUTH, b''

        root_el = ET.Element('folder-listing', version='1.0')
        # Parent folder entry (except when at root)
        if self._cwd != PurePosixPath('/'):
            ET.SubElement(root_el, 'parent-folder')

        for name, node in sorted(cwd_node['children'].items()):
            if node['_type'] == 'dir':
                ET.SubElement(root_el, 'folder', name=name)
            else:
                size = str(len(node['data']))
                ET.SubElement(root_el, 'file', name=name, size=size)

        ET.indent(root_el, space='  ', level=0)

        xml_str = ('<?xml version="1.0"?>\n'
                  '<!DOCTYPE folder-listing SYSTEM "obex-folder-listing.dtd">\n') + \
                  ET.tostring(root_el, encoding='unicode')
        return OBEXRspCode.SUCCESS, xml_str.encode('utf-8')

    # ------------------------------------------------------------------
    # File transfer
    # ------------------------------------------------------------------

    def push_file(self, name: str, data: bytes) -> int:
        """Receive a file PUT from the client into CWD.

        Returns OBEXRspCode on success or error.
        """
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND
        if not self._check_perm(cwd_node, self.PERM_WRITE):
            logging.warning('FtpStorage: push_file %r permission denied in %s', name, self._cwd)
            return OBEXRspCode.UNAUTH
        cwd_node['children'][name] = _make_file(data)
        logging.debug('FtpStorage: pushed file %r (%d bytes) into %s', name, len(data), self._cwd)
        return OBEXRspCode.SUCCESS

    def pull_file(self, name: str) -> tuple[int, bytes | None]:
        """Send a file GET to the client from CWD.

        Returns (OBEXRspCode, data) tuple.
        """
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND, None
        node = cwd_node['children'].get(name)
        if node is None or node['_type'] != 'file':
            logging.warning('FtpStorage: pull_file %r not found in %s', name, self._cwd)
            return OBEXRspCode.NOT_FOUND, None
        if not self._check_perm(node, self.PERM_READ):
            logging.warning('FtpStorage: pull_file %r permission denied in %s', name, self._cwd)
            return OBEXRspCode.UNAUTH, None
        logging.debug('FtpStorage: pulling file %r (%d bytes) from %s', name, len(node['data']), self._cwd)
        return OBEXRspCode.SUCCESS, node['data']

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, name: str) -> int:
        """Delete a file or folder (recursive) from CWD.

        Returns OBEXRspCode on success or error.
        """
        cwd_node = self._resolve_cwd()
        if cwd_node is None or cwd_node['_type'] != 'dir':
            return OBEXRspCode.NOT_FOUND
        if name not in cwd_node['children']:
            logging.warning('FtpStorage: delete %r not found in %s', name, self._cwd)
            return OBEXRspCode.NOT_FOUND
        target = cwd_node['children'][name]
        if not self._check_perm(target, self.PERM_DELETE):
            logging.warning('FtpStorage: delete %r permission denied in %s', name, self._cwd)
            return OBEXRspCode.UNAUTH
        del cwd_node['children'][name]
        logging.debug('FtpStorage: deleted %r from %s', name, self._cwd)
        return OBEXRspCode.SUCCESS

    # ------------------------------------------------------------------
    # COPY / RENAME (ACTION commands) -- support cross-directory paths
    # ------------------------------------------------------------------

    def copy(self, src_name: str, dst_path: str) -> int:
        """Copy a file or folder from the CWD to dst_path.

        src_name: bare name (no path separators) of an entry in the CWD.
        dst_path: destination path, relative to CWD or absolute (starts with '/').
                  Supports cross-directory destinations.

        Returns OBEXRspCode on success or error.
        """
        import copy as _copy

        if '/' in src_name:
            logging.warning('FtpStorage: copy src %r must be a bare name in CWD', src_name)
            return OBEXRspCode.BAD_REQ

        cwd_node = self._resolve_cwd()
        if cwd_node is None or src_name not in cwd_node['children']:
            logging.warning('FtpStorage: copy src %r not found in CWD %s', src_name, self._cwd)
            return OBEXRspCode.NOT_FOUND
        src_node = cwd_node['children'][src_name]

        if not self._check_perm(src_node, self.PERM_READ):
            logging.warning('FtpStorage: copy src %r permission denied', src_name)
            return OBEXRspCode.UNAUTH

        dst_abs = self._to_abs(dst_path)
        if self._resolve(dst_abs) is not None:
            logging.warning('FtpStorage: copy dst %r already exists', dst_path)
            return OBEXRspCode.FORBIDDEN

        dst_parent, dst_name = self._resolve_parent(dst_abs)
        if dst_parent is None:
            logging.warning('FtpStorage: copy dst parent not found for %r', dst_path)
            return OBEXRspCode.NOT_FOUND

        if not self._check_perm(dst_parent, self.PERM_WRITE):
            logging.warning('FtpStorage: copy dst parent permission denied for %r', dst_path)
            return OBEXRspCode.UNAUTH

        dst_parent['children'][dst_name] = _copy.deepcopy(src_node)
        logging.debug('FtpStorage: copied %r -> %s', src_name, dst_abs)
        return OBEXRspCode.SUCCESS

    def rename(self, src_name: str, dst_path: str) -> int:
        """Move/rename a file or folder from the CWD to dst_path.

        src_name: bare name (no path separators) of an entry in the CWD.
        dst_path: destination path, relative to CWD or absolute (starts with '/').
                  Supports cross-directory destinations.

        Returns OBEXRspCode on success or error.
        """
        if '/' in src_name:
            logging.warning('FtpStorage: rename src %r must be a bare name in CWD', src_name)
            return OBEXRspCode.BAD_REQ

        cwd_node = self._resolve_cwd()
        if cwd_node is None or src_name not in cwd_node['children']:
            logging.warning('FtpStorage: rename src %r not found in CWD %s', src_name, self._cwd)
            return OBEXRspCode.NOT_FOUND
        src_node = cwd_node['children'][src_name]

        if not self._check_perm(src_node, self.PERM_DELETE):
            logging.warning('FtpStorage: rename src %r permission denied', src_name)
            return OBEXRspCode.UNAUTH

        dst_abs = self._to_abs(dst_path)
        if self._resolve(dst_abs) is not None:
            logging.warning('FtpStorage: rename dst %r already exists', dst_path)
            return OBEXRspCode.FORBIDDEN

        dst_parent, dst_name = self._resolve_parent(dst_abs)
        if dst_parent is None:
            logging.warning('FtpStorage: rename dst parent not found for %r', dst_path)
            return OBEXRspCode.NOT_FOUND

        if not self._check_perm(dst_parent, self.PERM_WRITE):
            logging.warning('FtpStorage: rename dst parent permission denied for %r', dst_path)
            return OBEXRspCode.UNAUTH

        dst_parent['children'][dst_name] = src_node
        del cwd_node['children'][src_name]
        logging.debug('FtpStorage: moved %r -> %s', src_name, dst_abs)
        return OBEXRspCode.SUCCESS

    # ------------------------------------------------------------------
    # SET PERMISSIONS
    # ------------------------------------------------------------------

    def set_permissions_recursive(self, path: str, perms: int) -> int:
        """Recursively set permissions on the node at *path* and all its descendants."""
        abs_path = self._to_abs(path)
        node = self._resolve(abs_path)
        if node is None:
            return OBEXRspCode.NOT_FOUND
        node['perms'] = perms
        if node['_type'] == 'dir':
            for child_name in list(node['children']):
                self.set_permissions_recursive(str(abs_path / child_name), perms)
        return OBEXRspCode.SUCCESS

    def set_permissions(self, name: str, perms: int) -> int:
        """Set permission bits on a file or folder.

        *name* may be a bare name (in CWD), a relative path, or an absolute
        path starting with '/'.

        Returns OBEXRspCode on success or error.
        """
        abs_path = self._to_abs(name)
        parent, entry_name = self._resolve_parent(abs_path)
        if parent is None or entry_name not in parent['children']:
            logging.warning('FtpStorage: set_permissions %r not found', name)
            return OBEXRspCode.NOT_FOUND
        target = parent['children'][entry_name]
        if not self._check_perm(target, self.PERM_MODPERM):
            logging.warning('FtpStorage: set_permissions %r permission denied', name)
            return OBEXRspCode.UNAUTH
        target['perms'] = perms
        logging.debug('FtpStorage: set perms 0x%04x on %r', perms, name)
        return OBEXRspCode.SUCCESS


class FtpSrmState:
    SRM_DISABLED = 0
    SRM_ENABLED_BUT_WAITING = 1
    SRM_ENABLED = 2


class FtpAuthStatus:
    LOCAL_AUTH_ENABLED = 0x01   # This side sent a challenge nonce
    PEER_AUTH_ENABLED = 0x02   # Peer sent a challenge nonce


class FtpInfo:
    CONN_ID = "conn_id"
    MOPL = "mopl"
    LOCAL_SRM = "local_srm"
    LOCAL_SRMP = "local_srmp"
    SRM_STATE = "srm_state"
    RX_DATA = "rx_data"
    TX_DATA = "tx_data"
    TX_CNT = "tx_cnt"
    LAST_PUSH_FILE_NAME = "last_push_file_name"
    PWD = "pwd"                 # Password string for OBEX authentication
    LOCAL_NONCE = "local_nonce"  # 16-byte nonce generated by this side
    PEER_NONCE = "peer_nonce"   # 16-byte nonce received from peer
    AUTH_STATE = "auth_state"   # Bitmask: bit0=LOCAL_AUTH_ENABLED, bit1=PEER_AUTH_ENABLED


class FtpConnection:
    """Represents a single FTP connection (transport + OBEX layers) to one peer."""

    def __init__(self, addr):
        """
        :param addr: Bluetooth address string (hex, lowercase, no colons)
        """
        self.addr = addr
        self.transport_type = None  # e.g. BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED
        self.obex_type = None       # e.g. BTP_FTP_EV_CLIENT_CONNECT
        self.conn_info = {}
        self.data_rx = {}           # {ev: [data_list]}

        # Default connection info
        self.conn_info[FtpInfo.CONN_ID] = 0
        self.conn_info[FtpInfo.MOPL] = 255
        self.conn_info[FtpInfo.RX_DATA] = {}
        self.conn_info[FtpInfo.TX_DATA] = {}
        self.conn_info[FtpInfo.TX_CNT] = 0
        self.conn_info[FtpInfo.SRM_STATE] = FtpSrmState.SRM_DISABLED
        self.conn_info[FtpInfo.LOCAL_SRM] = False
        self.conn_info[FtpInfo.LOCAL_SRMP] = 0
        self.conn_info[FtpInfo.PWD] = "ftp"  # Must match the value of TSPX_auth_password
        self.conn_info[FtpInfo.LOCAL_NONCE] = None
        self.conn_info[FtpInfo.PEER_NONCE] = None
        self.conn_info[FtpInfo.AUTH_STATE] = 0

    # --- Transport layer ---

    def set_transport(self, conn_type):
        self.transport_type = conn_type

    def clear_transport(self):
        self.transport_type = None

    def set_obex(self, conn_type):
        self.obex_type = conn_type

    def clear_obex(self):
        self.obex_type = None

    def has_transport(self, conn_type):
        return self.transport_type == conn_type

    def has_obex(self, conn_type):
        return self.obex_type == conn_type

    def is_transport_connected(self):
        return self.transport_type is not None

    def is_obex_connected(self):
        return self.obex_type is not None

    # --- Connection info ---

    def set_info(self, key, value):
        self.conn_info[key] = value

    def get_info(self, key=None):
        if key is None:
            return self.conn_info
        return self.conn_info.get(key, None)

    def clear_rx_tx_state(self):
        self.conn_info[FtpInfo.TX_DATA] = {}
        self.conn_info[FtpInfo.RX_DATA] = {}
        self.conn_info[FtpInfo.TX_CNT] = 0
        self.conn_info[FtpInfo.SRM_STATE] = FtpSrmState.SRM_DISABLED
        self.conn_info[FtpInfo.LOCAL_SRM] = False
        self.conn_info[FtpInfo.LOCAL_SRMP] = 0

    # --- Event data queues ---

    def rx(self, ev, data):
        self.data_rx.setdefault(ev, []).append(data)

    def rx_data_get(self, ev, timeout, clear):
        if ev in self.data_rx and len(self.data_rx[ev]) != 0:
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        if wait_for_event(timeout, lambda: ev in self.data_rx and len(self.data_rx[ev]) != 0):
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        return None

    def rx_data_clear(self, ev, data):
        if ev in self.data_rx:
            if data in self.data_rx[ev]:
                self.data_rx[ev].remove(data)


class FTP:
    """FTP stack layer. Manages FtpConnection objects keyed by peer address."""

    # Transport layer connection event types
    TRANSPORT_TYPES = {
        defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED,
        defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED,
        defs.BTP_FTP_EV_SERVER_RFCOMM_CONNECTED,
        defs.BTP_FTP_EV_SERVER_L2CAP_CONNECTED,
    }

    # OBEX layer connection event types
    OBEX_TYPES = {
        defs.BTP_FTP_EV_CLIENT_CONNECT,
        defs.BTP_FTP_EV_SERVER_CONNECT,
    }

    def __init__(self):
        self.connections = {}           # {addr: FtpConnection}
        self.connections_history = {}   # {addr: [FtpConnection, ...]}
        self.pre_conditions = {}        # {key: value} applied to each new connection
        self.storage = FtpStorage()
        logging.debug('FTP: storage initialized')

        from autopts.pybtp.btp.ftp import FtpEventHandler
        self.event_handler = FtpEventHandler(self)
        self.event_handler.start()

    def set_pre_conditions(self, key, value):
        """Set a pre-condition key/value to be applied to every new connection."""
        self.pre_conditions[key] = value

    def get_pre_conditions(self, key=None):
        if key is None:
            return self.pre_conditions
        return self.pre_conditions.get(key, None)

    def clear_pre_conditions(self):
        self.pre_conditions = {}

    def cleanup(self):
        if hasattr(self, 'event_handler') and self.event_handler:
            self.event_handler.stop()
        self.storage = None

    # --- Internal helpers ---

    def _is_transport_type(self, conn_type):
        return conn_type in self.TRANSPORT_TYPES

    def _is_obex_type(self, conn_type):
        return conn_type in self.OBEX_TYPES

    def conn_lookup(self, addr):
        """Find FtpConnection by address, or None."""
        return self.connections.get(addr)

    # --- Connection lifecycle ---

    def add_connection(self, addr, conn_type):
        """Add or update a FTP connection."""
        conn = self.conn_lookup(addr)

        if conn is None:
            conn = FtpConnection(addr)
            self.connections[addr] = conn
            self.connections_history.setdefault(addr, []).append(conn)
            logging.debug('FTP: created new connection addr=%s', addr)

        if self._is_transport_type(conn_type):
            conn.set_transport(conn_type)
        elif self._is_obex_type(conn_type):
            conn.set_obex(conn_type)

        # Apply pre-conditions to the new connection (e.g. LOCAL_SRMP for SRMP test cases).
        for key, value in self.pre_conditions.items():
            conn.set_info(key, value)

        logging.debug('FTP: add_connection addr=%s type=0x%02x', addr, conn_type)

    def remove_connection(self, addr, conn_type):
        """Clear transport or OBEX layer from a connection."""
        conn = self.conn_lookup(addr)
        if conn is None:
            return

        if self._is_transport_type(conn_type):
            conn.clear_transport()
        elif self._is_obex_type(conn_type):
            conn.clear_obex()

        if not conn.is_transport_connected() and not conn.is_obex_connected():
            del self.connections[addr]
            logging.debug('FTP: removed connection addr=%s', addr)

    def is_connected(self, addr, conn_type=None):
        """Check if a connection of given type is active."""
        conn = self.conn_lookup(addr)
        if conn is None:
            return False
        if conn_type is None:
            return conn.is_transport_connected() or conn.is_obex_connected()
        if self._is_transport_type(conn_type):
            return conn.has_transport(conn_type)
        if self._is_obex_type(conn_type):
            return conn.has_obex(conn_type)
        return False

    # --- Connection info ---

    def set_info(self, addr, key, value):
        conn = self.conn_lookup(addr)
        if conn:
            conn.set_info(key, value)

    def get_info(self, addr, key=None):
        conn = self.conn_lookup(addr)
        if conn:
            return conn.get_info(key)
        return None

    def clear_rx_tx_state(self, addr):
        conn = self.conn_lookup(addr)
        if conn:
            conn.clear_rx_tx_state()

    def wait_for_connection(self, addr, conn_type, timeout=5) -> bool:
        """Block until a connection of *conn_type* is active for *addr*."""
        return wait_for_event(timeout, self.is_connected, addr=addr, conn_type=conn_type)

    def wait_for_disconnection(self, addr, conn_type, timeout=5) -> bool:
        """Block until the connection of *conn_type* for *addr* is gone."""
        return wait_for_event(timeout, lambda: not self.is_connected(addr, conn_type))

    # --- Event data ---

    def rx(self, addr, ev, data):
        """Store received event data for the connection identified by addr."""
        conn = self.conn_lookup(addr)
        if conn is None:
            return None
        conn.rx(ev, data)

    def rx_data_get(self, addr, ev, timeout=30, clear=True):
        """Get received event data for addr, blocking up to timeout seconds."""
        conn = self.conn_lookup(addr)
        if conn is None:
            return None
        return conn.rx_data_get(ev, timeout, clear)

    def rx_data_clear(self, addr, ev, data):
        conn = self.conn_lookup(addr)
        if conn:
            conn.rx_data_clear(ev, data)
