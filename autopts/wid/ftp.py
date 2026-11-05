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
import re
from datetime import datetime
from uuid import UUID as StdUUID

from autopts.ptsprojects.stack import (
    FtpInfo,
    get_stack,
)
from autopts.pybtp import btp, defs
from autopts.pybtp.btp.btp import pts_addr_get
from autopts.pybtp.types import OBEXHdr, OBEXRspCode, WIDParams

log = logging.debug

FTP_UUID = StdUUID("f9ec7bc4-953c-11d2-984e-525400dc9e09")


def set_folder(flags: int, folder_name: str = ''):
    """Send SET_PATH with required CONN_ID + NAME headers per Zephyr API.
    Always includes NAME header (empty string for root/backup navigation).
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    # Always include NAME header (empty for root/backup, folder name for navigate-down).
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: folder_name}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_set_folder(flags=flags, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_SET_FOLDER)


def get_folder_listing(folder_name=''):
    is_l2cap = btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.TYPE: 'x-obex/folder-listing',
        OBEXHdr.NAME: folder_name,
    }
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, is_l2cap)
    btp.ftp_client_pull_folder_listing(final=True, buf=encoded_hdr)
    result = btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PULL_FOLDER_LISTING)
    if result is None:
        return None

    rsp_code, dct = result
    if rsp_code != OBEXRspCode.SUCCESS:
        return None

    return dct.get(OBEXHdr.BODY)


def pull_file(file_name, timeout=120):
    is_l2cap = btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: file_name,
    }
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, is_l2cap)
    btp.ftp_client_pull_file(final=True, buf=encoded_hdr)
    result = btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PULL_FILE, pts_addr_get(), timeout=timeout)
    if result is None:
        return None

    rsp_code, dct = result
    if rsp_code != OBEXRspCode.SUCCESS:
        return None

    return dct.get(OBEXHdr.BODY)


def push_file(file_name, file_data, timeout=120):
    is_l2cap = btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1 if is_l2cap else 0,
        OBEXHdr.NAME: file_name,
        OBEXHdr.BODY: file_data
    }
    encoded_hdr, remaining, body_off = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, is_l2cap)
    btp.ftp_set_info(FtpInfo.TX_DATA, remaining)
    btp.ftp_set_info(FtpInfo.TX_CNT, body_off)
    is_final = len(remaining) == 0
    btp.ftp_client_push_file(final=is_final, buf=encoded_hdr)
    result = btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PUSH_FILE, pts_addr_get(), timeout=timeout)
    if result is None:
        return None

    rsp_code = result[0]
    if rsp_code == OBEXRspCode.SUCCESS:
        return btp.ftp_set_info(FtpInfo.LAST_PUSH_FILE_NAME, file_name)

    return rsp_code


def parse_folder_listing(xml_data: str | bytes) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    try:
        import xml.etree.ElementTree as ET

        # Convert bytes to string if needed
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode('utf-8')

        # Parse XML
        root = ET.fromstring(xml_data)

        folders = []
        files = []

        # Find all folder elements
        for folder_elem in root.findall('.//folder'):
            fodler_dict = {attr_name: attr_value for attr_name, attr_value in folder_elem.attrib.items()}
            folders.append(fodler_dict)

        # Find all file elements
        for file_elem in root.findall('.//file'):
            file_dict = {attr_name: attr_value for attr_name, attr_value in file_elem.attrib.items()}
            files.append(file_dict)

        logging.info(f"Parsed {len(folders)} folders from listing")
        logging.info(f"Parsed {len(files)} files from listing")

        return folders, files

    except Exception as e:
        logging.error(f"Error parsing folder listing: {e}")
        return [], []


def ftp_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{ftp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def hdl_wid_1(_: WIDParams):
    """
    description: Take action to accept the Put Delete operation.
    """
    # Server: DELETE request is handled automatically by the server event handler.
    return True


def hdl_wid_2(_: WIDParams):
    """
    description: Take action to pull a file (GET operation), then immediately ABORT the operation.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: 'get.txt'}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    # Initiate pull_file but ABORT immediately (before completion).
    btp.ftp_client_pull_file(final=True, buf=encoded_hdr)
    try:
        btp.ftp_client_abort()
        btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_ABORT)
    except Exception:
        pass  # Abort may fail if operation already completed
    return True


def hdl_wid_3(params: WIDParams):
    """
    description: Take action to pull the file named %s.xyz.
    Note: xyz varies depending on TSPX_supported_file_extensions.
    """
    ext = '.txt'
    match = re.search(r"(?P<fname>\w+)\.[a-zA-Z0-9]+", params.description)
    fname = f'{match.group("fname")}{ext}' if match else 'get.txt'
    pull_file(fname, timeout=900)
    return True


def hdl_wid_4(_: WIDParams):
    """
    description: Take action to initiate a PUT operation for a large file.
    Then take action to ABORT the operation before it completes.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    file_name = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    file_data = b'\x00' * (mopl * 10)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.NAME: file_name,
        OBEXHdr.BODY: file_data,
    }
    encoded_hdr, remaining, body_off = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.TX_DATA, remaining)
    btp.ftp_set_info(FtpInfo.TX_CNT, body_off)
    is_final = len(remaining) == 0
    btp.ftp_client_push_file(final=is_final, buf=encoded_hdr)
    try:
        btp.ftp_client_abort()
        btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_ABORT)
    except Exception:
        pass  # Abort may fail if operation already completed
    return True


def hdl_wid_5(_: WIDParams):
    """
    description: Take action to Pull a folder to the tester, this action will be rejected by the tester.
    """
    get_folder_listing()
    return True


def hdl_wid_6(_: WIDParams):
    """
    description: Take action to Pull the file just Pushed back to the IUT.
    """
    pull_file(btp.ftp_get_info(FtpInfo.LAST_PUSH_FILE_NAME))
    return True


def hdl_wid_7(params: WIDParams):
    """
    description: Take action to Push Files with the following extensions
    (as defined by TSPX_supported_file_extensions): %s
    """
    exts = re.findall(r'\.[a-zA-Z0-9]+', params.description)
    if not exts:
        exts = ['.txt']

    # Push a file for each extension in the description.
    file_data = b'\x00' * 64
    for ext in exts:
        fname = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}' + ext
        push_file(fname, file_data)
    return True


def hdl_wid_8(_: WIDParams):
    """
    description: Take action to push a file > 2 MB to the tester.
    """
    # Large file > 2MB; use multi-packet push with TX_DATA continuation.
    file_name = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    file_data = b'\x00' * (2 * 1024 * 1024 + 1024)
    push_file(file_name, file_data, timeout=900)
    return True


def hdl_wid_9(_: WIDParams):
    """
    description: Take action to move to a folder that does not exist by
    sending a Set Path command with Flags = Don't Create.
    """
    folder_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    set_folder(flags=0x02, folder_name=folder_name)
    return True


def hdl_wid_10(_: WIDParams):
    """
    description: Take action to reject the Pull Folder operation.
    """
    # Server: SET_PATH rejection is handled automatically by the server event handler.
    return True


def hdl_wid_12(_: WIDParams):
    """
    description: Take action to reject the testers Set Path to a non existant folder.
    """
    return True


def hdl_wid_14(_: WIDParams):
    """
    description: Does the IUT indicate that the current path is set to the root folder?
    Note: If there is no way to determine the current path press 'Yes'.
    """
    return True


def hdl_wid_15(_: WIDParams):
    """
    description: Does the IUT indicate that '%s' was removed?
    """
    return True


def hdl_wid_16(_: WIDParams):
    """
    description: Did the IUT receive the following folder contents for the 'pts' folder?
    """
    return True


def hdl_wid_17(_: WIDParams):
    """
    description: Was the IUT notified that the Pull File operation failed?
    """
    return True


def hdl_wid_18(_: WIDParams):
    """
    description: Was the IUT notified that the Pull Folder operation failed?
    """
    return True


def hdl_wid_20(_: WIDParams):
    """
    description: Does the file received by the IUT match '%s' in the recently opened folder?
    """
    return True


def hdl_wid_21(_: WIDParams):
    """
    description: Was the IUT notified that the Push Folder operation failed?
    """
    return True


def hdl_wid_23(_: WIDParams):
    """
    description: Does the file named '%s' in the recently opened window
    represent the file just pushed by the IUT?
    """
    return True


def hdl_wid_24(_: WIDParams):
    """
    description: Was the '%s' folder properly pushed to the tester?
    Note: A browse folder can be used to confirm.
    """
    return True


def hdl_wid_25(_: WIDParams):
    """
    description: Was the IUT notified that the Push File operation failed?
    """
    return True


def hdl_wid_26(_: WIDParams):
    """
    description: Did the IUT receive the following folder contents for the root folder?
    """
    return True


def hdl_wid_29(params: WIDParams):
    """
    description: Is a file named '%s' available on the IUT?
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    return stack.ftp.storage.is_existing_file_name(fname)


def hdl_wid_30(params: WIDParams):
    """
    description: If necessary take action to remove the file named '%s\\%s' on the IUT now.
    Once the file is gone press 'OK' to continue.
    """
    match = re.search(r"'\w+\\(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    if stack.ftp.storage.is_existing_file_name(fname):
        stack.ftp.storage.delete(fname)
    return True


def hdl_wid_31(params: WIDParams):
    """
    description: If necessary take action to create a file named '%s\\%s' on the IUT now.
    Once the file is in place press 'OK' to continue.
    """
    if params.test_case_name in ["FTP/SR/OTR/BV-14-C"]:
        return True

    match = re.search(r"'\w+\\(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    if not stack.ftp.storage.is_existing_file_name(fname):
        if params.test_case_name in ["FTP/SR/OTR/BV-13-C"]:
            file_data = b'\x00' * (2 * 1024 * 1024)  # 2MB file
        else:
            file_data = b'\x00' * 1024
        stack.ftp.storage.push_file(fname, file_data)

    return True


def hdl_wid_32(params: WIDParams):
    """
    description: Is a folder named '%s' available on the IUT?
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    return stack.ftp.storage.is_existing_folder_name(fname)


def hdl_wid_33(_: WIDParams):
    """
    description: Does the currently displayed file represent the folder contents of '%s'?
    """
    return True


def hdl_wid_34(params: WIDParams):
    """
    description: If necessary take action to create a folder named '%s\\%s' now.
    Once the folder is in place press 'OK' to continue.
    """
    match = re.search(r"'\w+\\(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    if not stack.ftp.storage.is_existing_folder_name(fname):
        stack.ftp.storage.create_folder(fname)
    return True


def hdl_wid_35(params: WIDParams):
    """
    description: If necessary take action to remove the folder named '%s\\%s' now.
    Once the folder is gone press 'OK' to continue.
    """
    match = re.search(r"'\w+\\(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    if stack.ftp.storage.is_existing_folder_name(fname):
        stack.ftp.storage.delete(fname)
    return True


def hdl_wid_36(_: WIDParams):
    """
    description: Does the IUT recognize that the Pull operation was aborted?
    """
    return True


def hdl_wid_38(_: WIDParams):
    """
    description: Does '%s' in the recently opened window match the file just returned by the IUT?
    """
    return True


def hdl_wid_39(_: WIDParams):
    """
    description: Does the server indicate that the Push File operation was aborted?
    """
    return True


def hdl_wid_40(_: WIDParams):
    """
    description: Did the IUT receive a well formatted file named '%s\\%s'?
    """
    return True


def hdl_wid_41(_: WIDParams):
    """
    description: Did the IUT successfully receive files and folders in the '%s' folder?
    """
    return True


def hdl_wid_42(_: WIDParams):
    """
    description: Does the currently displayed file represent the folder contents of the root folder?
    """
    return True


def hdl_wid_43(_: WIDParams):
    """
    description: Were permissions set correctly on '%s'?
    """
    return True


def hdl_wid_44(_: WIDParams):
    """
    description: Take action to navigate back to the parent folder.
    """
    set_folder(flags=0x03)
    return True


def hdl_wid_46(params: WIDParams):
    """
    description: The folder named '%s' should not be available on the IUT, press 'Yes' to confirm.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    return not stack.ftp.storage.is_existing_folder_name(fname)


def hdl_wid_47(params: WIDParams):
    """
    description: The file named '%s' should not be available on the IUT, press 'Yes' to confirm.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    stack = get_stack()
    return not stack.ftp.storage.is_existing_file_name(fname)


def hdl_wid_48(_: WIDParams):
    """
    description: The file or folder named '%s' should not have been removed, press 'Yes' to confirm.
    """
    return True


def hdl_wid_49(params: WIDParams):
    """
    description: Take action to navigate to the '%s' folder.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    set_folder(flags=0x02, folder_name=fname)
    return True


def hdl_wid_90(_: WIDParams):
    """
    description: Is the IUT capable of establishing connection to an unpaired device?
    """
    return True


def hdl_wid_20000(_: WIDParams):
    """
    description: Please prepare IUT into a connectable mode in BR/EDR.
    """
    # IUT is already in connectable/discoverable mode from pre_conditions.
    return True


def hdl_wid_20115(_: WIDParams):
    """
    description: Please initiate an ACL disconnection to the PTS.
    Verify that the Implementation Under Test (IUT) can initiate ACL disconnect request to PTS.
    """
    btp.gap_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    return True


# ===========================================================================
# OBEX MMI Operations (WID 4000+)
# ===========================================================================

def hdl_wid_4000(_: WIDParams):
    """
    description: Please accept the COPY ACTION command.
    """
    # Server: COPY ACTION is handled automatically by the server event handler.
    return True


def hdl_wid_4001(_: WIDParams):
    """
    description: Please accept the MOVE RENAME ACTION command.
    """
    # Server: MOVE/RENAME ACTION is handled automatically by the server event handler.
    return True


def hdl_wid_4002(_: WIDParams):
    """
    description: Please accept the SET PERMISSIONS ACTION command.
    """
    # Server: SET PERMISSIONS ACTION is handled automatically by the server event handler.
    return True


def hdl_wid_4003(_: WIDParams):
    """
    description: Please accept the browse folders (GET) command.
    """
    # Server: GET folder listing request handled automatically.
    return True


def hdl_wid_4004(_: WIDParams):
    """
    description: Please accept the OBEX CONNECT REQ.
    """
    # Server: OBEX CONNECT is accepted automatically by the server event handler.
    return True


def hdl_wid_4007(_: WIDParams):
    """
    description: Please accept the OBEX DISCONNECT REQ command.
    """
    # Server: DISCONNECT is accepted automatically.
    return True


def hdl_wid_4008(_: WIDParams):
    """
    description: Please accept the GET REQUEST.
    Note: This MMI will disappear after the GET operation completes.
    """
    # Server: GET file request handled automatically.
    return True


def hdl_wid_4010(_: WIDParams):
    """
    description: Please accept the GET REQUEST with an SRM ENABLED header.
    """
    # Server: GET with SRM is handled automatically by the server event handler.
    return True


def hdl_wid_4012(_: WIDParams):
    """
    description: Please accept the PUT REQUEST.
    """
    # Server: PUT file request handled automatically.
    return True


def hdl_wid_4058(_: WIDParams):
    """
    description: Please respond to the PUT REQUEST with an SRM ENABLED header and an SRMP WAIT header.
    """
    # Server: PUT with SRM+SRMP WAIT is handled automatically by the server event handler.
    return True


def hdl_wid_4016(_: WIDParams):
    """
    description: Please accept the SET_PATH command.
    """
    # Server: SET_PATH is accepted automatically.
    return True


def hdl_wid_4017(_: WIDParams):
    """
    description: Please accept the l2cap channel connection for an OBEX connection.
    """
    # Server: transport-layer accept is automatic.
    return True


def hdl_wid_4018(_: WIDParams):
    """
    description: Please accept the rfcomm channel connection for an OBEX connection.
    """
    return True


def hdl_wid_4019(_: WIDParams):
    """
    description: Please accept the disconnection of the transport channel.
    """
    return True


def hdl_wid_4020(_: WIDParams):
    """
    description: Take action to send a COPY ACTION command.
    """
    folder_listing = get_folder_listing()
    if folder_listing is None:
        return False

    files = parse_folder_listing(folder_listing)[1]
    file_names = [file.get('name') for file in files if file.get('name')]
    src_name = file_names[0] if file_names else 'get.txt'
    dst_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{src_name}'

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.ACTION_ID: 0x00,  # BT_OBEX_ACTION_COPY
        OBEXHdr.NAME: src_name,
        OBEXHdr.DEST_NAME: dst_name,
    }
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_copy(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_COPY)
    return True


def hdl_wid_4021(_: WIDParams):
    """
    description: Take action to send a MOVE RENAME ACTION command.
    """
    folder_listing = get_folder_listing()
    if folder_listing is None:
        return False

    files = parse_folder_listing(folder_listing)[1]
    file_names = [file.get('name') for file in files if file.get('name')]
    src_name = file_names[0] if file_names else 'get.txt'
    dst_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{src_name}'

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.ACTION_ID: 0x01,  # BT_OBEX_ACTION_MOVE_RENAME
        OBEXHdr.NAME: src_name,
        OBEXHdr.DEST_NAME: dst_name,
    }
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_rename(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_RENAME)
    return True


def hdl_wid_4022(_: WIDParams):
    """
    description: Take action to send a SET PERMISSIONS ACTION command.
    """
    folder_listing = get_folder_listing()
    if folder_listing is None:
        return False

    files = parse_folder_listing(folder_listing)[1]
    file_names = [file.get('name') for file in files if file.get('name')]
    file_name = file_names[0] if file_names else 'get.txt'

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.ACTION_ID: 0x02,  # BT_OBEX_ACTION_SET_PERM
        OBEXHdr.NAME: file_name,
        OBEXHdr.PERMISSION: 0x878787,
    }
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_set_permission(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_SET_PERMISSION)
    return True


def hdl_wid_4024(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ.
    """
    btp.ftp_client_connect()
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_CONNECT)
    return True


def hdl_wid_4025(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP.
    """
    if btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_CONNECT):
        return True

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    hdr = {OBEXHdr.TARGET: FTP_UUID}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_connect(encoded_hdr)
    if btp.ftp_wait_for_connection(defs.BTP_FTP_EV_CLIENT_CONNECT) is None:
        return False
    return True


def hdl_wid_4026(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP with authentication.
    """
    btp.ftp_client_connect()
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_CONNECT)
    return True


def hdl_wid_4027(_: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for FTP without authentication.
    """
    btp.ftp_client_connect()
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_CONNECT)
    return True


def hdl_wid_4031(_: WIDParams):
    """
    description: Take action to initiate an OBEX DISCONNECT REQ.
    """
    btp.ftp_client_disconnect()
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_DISCONNECT)
    return True


def hdl_wid_4032(_: WIDParams):
    """
    description: Take action to send a GET request.
    Then allow the operation to complete as normal.
    """
    pull_file('get.txt')
    return True


def hdl_wid_4037(_: WIDParams):
    """
    description: Take action to send a PUT request.
    Then allow the operation to complete as normal.
    """
    file_name = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    file_data = b'\x00' * 64
    push_file(file_name, file_data)
    return True


def hdl_wid_4035(_: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header.
    Then allow the operation to complete as normal.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: 'get.txt', OBEXHdr.SRM: 1}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, True)
    btp.ftp_client_pull_file(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PULL_FILE)
    return True


def hdl_wid_4036(_: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header and an SRMP WAIT header.
    Then allow the operation to complete as normal.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    # SRM=1 + SRMP=1 (WAIT): IUT requests SRM but delays first data packet.
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: 'get.txt', OBEXHdr.SRM: 1, OBEXHdr.SRMP: 1}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, True)
    btp.ftp_set_info(FtpInfo.LOCAL_SRMP, 1)
    btp.ftp_client_pull_file(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PULL_FILE)
    return True


def hdl_wid_4039(_: WIDParams):
    """
    description: Take action to send a PUT request with an SRM ENABLED header.
    Note: This object should be large enough to span multiple packets.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    # Large file spanning multiple MOPL packets. SRM=1 enables Single-Response Mode.
    file_name = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    file_data = b'\x00' * (mopl * 8)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.SRM: 1,
        OBEXHdr.NAME: file_name,
        OBEXHdr.BODY: file_data,
    }
    # Encode the first packet and save remaining data for event-handler continuation.
    encoded_hdr, remaining, body_off = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    # Store remaining body in TX_DATA so the event handler can send continuation packets.
    btp.ftp_set_info(FtpInfo.TX_DATA, remaining)
    btp.ftp_set_info(FtpInfo.TX_CNT, body_off)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, True)
    is_final = len(remaining) == 0
    btp.ftp_client_push_file(final=is_final, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PUSH_FILE)
    return True


def hdl_wid_4042(_: WIDParams):
    """
    description: Take action to send a Set Path up one level.
    Note: Flags = Backup, Don't Create.
    """
    set_folder(flags=0x03)
    return True


def hdl_wid_4046(_: WIDParams):
    """
    description: Take action to move to the root folder by sending a Set Path command
    with Flags = Don't Create and an empty Name header.
    """
    set_folder(flags=0x02)
    return True


def hdl_wid_4047(_: WIDParams):
    """
    description: Take action to create an l2cap channel for an OBEX connection.
    """
    # Establish BR/EDR ACL connection first, then trigger SDP + L2CAP transport.
    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    btp.ftp_client_l2cap_connect()
    if btp.ftp_wait_for_connection(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED) is None:
        return False
    # FTP/CL: send OBEX CONNECT with FTP Target UUID header.
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    hdr = {OBEXHdr.TARGET: FTP_UUID}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_connect(buf=encoded_hdr)
    if btp.ftp_wait_for_connection(defs.BTP_FTP_EV_CLIENT_CONNECT) is None:
        return False
    return True


def hdl_wid_4048(_: WIDParams):
    """
    description: Take action to create an rfcomm channel for an OBEX connection.
    """
    # Establish BR/EDR ACL connection first, then trigger SDP + RFCOMM transport.
    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    btp.ftp_client_rfcomm_connect(bd_addr=pts_addr_get())
    if btp.ftp_wait_for_connection(defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED) is None:
        return False
    # FTP/CL: send OBEX CONNECT with FTP Target UUID header.
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    hdr = {OBEXHdr.TARGET: FTP_UUID}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_connect(buf=encoded_hdr)
    if btp.ftp_wait_for_connection(defs.BTP_FTP_EV_CLIENT_CONNECT) is None:
        return False
    return True


def hdl_wid_4049(_: WIDParams):
    """
    description: Take action to disconnect the transport channel.
    """
    if btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED):
        btp.ftp_client_rfcomm_disconnect()
        btp.ftp_wait_for_disconnection(defs.BTP_FTP_EV_CLIENT_RFCOMM_CONNECTED)
    elif btp.ftp_is_connected(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED):
        btp.ftp_client_l2cap_disconnect()
        btp.ftp_wait_for_disconnection(defs.BTP_FTP_EV_CLIENT_L2CAP_CONNECTED)
    return True


def hdl_wid_4050(_: WIDParams):
    """
    description: Take action to reject the ACTION command sent by PTS.
    """
    return True


def hdl_wid_4074(_: WIDParams):
    """
    description: Take action to respond to the folder listing request sent by the tester.
    """
    # Server: folder listing response sent automatically.
    return True


def hdl_wid_4075(_: WIDParams):
    """
    description: Take action to accept the Push Folder operation from the tester.
    """
    # Server: Push Folder (PUT) accepted automatically.
    return True


def hdl_wid_4077(params: WIDParams):
    """
    description: Take action to create a folder, using the Set Path command and flags = None.
    Note: The name must be for a new folder.
    """
    folder = 'new_folder'
    set_folder(flags=0x00, folder_name=folder)
    return True


def hdl_wid_4079(params: WIDParams):
    """
    description: Take action to delete the file or folder named '%s' in the current directory.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: fname}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_delete(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_DELETE)
    return True


def hdl_wid_4080(_: WIDParams):
    """
    description: Take action to browse the current folder listings.
    """
    get_folder_listing()
    return True


def hdl_wid_4081(params: WIDParams):
    """
    description: Take action to browse the '%s' sub folder.
    Note: To browse a sub folder listing, change path to the specified sub folder
    and perform a browse folder listings operation.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    set_folder(flags=0x02, folder_name=fname)
    get_folder_listing()
    return True


def hdl_wid_4082(params: WIDParams):
    """
    description: Take action to move to the '%s' folder the Set Path command and flags = Don't Create.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    set_folder(flags=0x02, folder_name=fname)
    return True


def hdl_wid_4083(params: WIDParams):
    """
    description: Take action to perform a Pull Folder operation on the '%s' folder.
    The IUT must return back to the current folder after the Pull Folder operation is complete.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    set_folder(flags=0x02, folder_name=fname)

    folder_listing = get_folder_listing()
    if folder_listing is None:
        return False

    files = parse_folder_listing(folder_listing)[1]
    file_names = [file.get('name') for file in files if file.get('name')]

    for file_name in file_names:
        pull_file(file_name, timeout=900)

    # Navigate back to parent
    if fname:
        set_folder(flags=0x03)
    return True


def hdl_wid_4084(params: WIDParams):
    """
    description: Take action to perform a Pull Folder operation on the '%s' folder.
    Once the Pull Folder operation begins quickly take action to send an ABORT operation.
    """
    match = re.search(r"'(?P<fname>[^']+)'", params.description)
    if match is None:
        return False
    fname = match.group('fname')

    set_folder(flags=0x02, folder_name=fname)

    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.TYPE: 'x-obex/folder-listing'}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_client_pull_folder_listing(final=False, buf=encoded_hdr)
    try:
        btp.ftp_client_abort()
        btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_ABORT)
    except Exception:
        pass  # Abort may fail if operation already completed
    return True


def hdl_wid_4085(_: WIDParams):
    """
    description: Take action to PUSH a folder to the Server.
    Make sure the folder being pushed does not already exist on the Server.
    Once all files have been pushed Set Path back to the original folder.
    """
    # Create new folder on server via SET_PATH flags=0x00 (create).
    folder_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    set_folder(flags=0x00, folder_name=folder_name)
    # Push a file into the newly created folder.
    file_name = f'put_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    file_data = b'\x00' * 64
    push_file(file_name, file_data)
    # Navigate back to parent folder.
    set_folder(flags=0x03)
    return True


def hdl_wid_4086(_: WIDParams):
    """
    description: Take action to ABORT a PUSH a folder operation.
    Make sure to push large files, then once the Push Folder operation begins
    take action to ABORT the operation.
    """
    # Create new folder on server via SET_PATH flags=0x00 (create).
    folder_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    set_folder(flags=0x00, folder_name=folder_name)
    # Push a file into the newly created folder.
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    file_data = b'\x00' * (mopl * 10)
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: 'push_file.txt', OBEXHdr.BODY: file_data}
    encoded_hdr, remaining, body_off = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.TX_DATA, remaining)
    btp.ftp_set_info(FtpInfo.TX_CNT, body_off)
    is_final = len(remaining) == 0
    btp.ftp_client_push_file(final=is_final, buf=encoded_hdr)
    try:
        btp.ftp_client_abort()
        btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_ABORT)
    except Exception:
        pass  # Abort may fail if operation already completed
    return True


def hdl_wid_4087(_: WIDParams):
    """
    description: Take action to Push a folder to the tester.
    Note: The create folder will be rejected by the tester, the IUT should not
    attempt to Push any files afterwards.
    """
    folder_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    set_folder(flags=0x00, folder_name=folder_name)
    return True


def hdl_wid_4088(_: WIDParams):
    """
    description: Take action to ABORT the current operation.
    """
    # ABORT is sent immediately after PUT/GET operation
    return True


def hdl_wid_4090(_: WIDParams):
    """
    description: Take action to send a GET REQUEST with SRM ENABLED + SRMP WAIT (twice), then without SRMP WAIT.
    """
    mopl = btp.ftp_get_info(FtpInfo.MOPL)
    conn_id = btp.ftp_get_info(FtpInfo.CONN_ID)
    # SRM=1 + SRMP=1 WAIT for 2 continuations, then proceed.
    hdr = {OBEXHdr.CONN_ID: conn_id, OBEXHdr.NAME: 'get.txt', OBEXHdr.SRM: 1, OBEXHdr.SRMP: 1}
    encoded_hdr, _, _ = btp.ftp_enc_hdr(hdr, mopl - 3, 0)
    btp.ftp_set_info(FtpInfo.LOCAL_SRM, True)
    btp.ftp_set_info(FtpInfo.LOCAL_SRMP, 2)
    btp.ftp_client_pull_file(final=True, buf=encoded_hdr)
    btp.ftp_rx_data_get(defs.BTP_FTP_EV_CLIENT_PULL_FILE)
    return True


def hdl_wid_4091(_: WIDParams):
    """
    description: Take action to reject the SESSION command sent by PTS.
    """
    return True


def hdl_wid_4800(_: WIDParams):
    """
    description: Please remove pairing from the Implementation Under Test (IUT), then click Ok.
    """
    return True
