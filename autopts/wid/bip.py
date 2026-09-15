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

from autopts.pybtp import btp, defs

from autopts.pybtp.types import BIPAppParamTag, BIPConnType, OBEXHdr, OBEXRspCode, WIDParams, \
    BIPRemoteDisplay, BIPImagingSvclass

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.stack.layers.bip import BIPObexRole
from autopts.wid import sdp


log = logging.debug


def bip_wid_hdl(wid, description, test_case_name):
    log(f'{bip_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    from autopts.wid import generic_wid_hdl
    return generic_wid_hdl(wid, description, test_case_name, [__name__])

def hdl_wid_3(params: WIDParams):
    """
    Did the Implementation Under Test (IUT) receive the imaging-capabilities object correctly without any errors?
    """
    return True


def hdl_wid_15(params: WIDParams):
    """
    Please disconnect the OBEX connection between the PTS and Implementation Under Test (IUT).
    """
    if params.test_case_name == "BIP/AAR/FFC/BV-01-C":
        btp.bip_second_obex_disconnect()
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_DISCONNECTED,
            rsp_code=OBEXRspCode.SUCCESS)

    btp.bip_obex_disconnect()
    if not btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_CLIENT_DISCONNECTED,
            rsp_code=OBEXRspCode.SUCCESS):
        return False

    if params.test_case_name == "BIP/IPSI/MFS/BV-01-C":
        btp.bip_disconnect_l2cap()
        if not btp.bip_wait_for_transport_disconnected():
            return False

    return True


def hdl_wid_18(params: WIDParams):
    """
    Click OK when the IUT becomes connectable.
    """
    stack = get_stack()
    stack.bip.enable_auto_response()
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()
    return True


def hdl_wid_19(params: WIDParams):
    """
    Take action to create an l2cap channel or rfcomm channel for an OBEX connection.
    """
    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()

    btp.bip_sdp_discover()
    btp.bip_wait_for_sdp_finished()
    sdp_conn = btp.bip_get_sdp_connection()
    if sdp_conn is None:
        return False

    if params.test_case_name == "BIP/CL/GOEP/BC/BV-02-C":
        if not sdp_conn.rfcomm_channel:
            return False
        btp.bip_connect_rfcomm(channel=sdp_conn.rfcomm_channel)
        return btp.bip_wait_for_transport_connected()

    if sdp_conn.l2cap_psm:
        btp.bip_connect_l2cap(psm=sdp_conn.l2cap_psm)
    elif sdp_conn.rfcomm_channel:
        btp.bip_connect_rfcomm(channel=sdp_conn.rfcomm_channel)

    return btp.bip_wait_for_transport_connected()


def hdl_wid_20(params: WIDParams):
    """
    Take action to create an l2cap channel for an OBEX connection.
    """
    btp.gap_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()

    btp.bip_sdp_discover()
    btp.bip_wait_for_sdp_finished()
    sdp_conn = btp.bip_get_sdp_connection()
    if sdp_conn is None:
        return False

    if sdp_conn.l2cap_psm:
        btp.bip_connect_l2cap(psm=sdp_conn.l2cap_psm)
    else:
        btp.bip_connect_l2cap()

    return btp.bip_wait_for_transport_connected()


def hdl_wid_22(params: WIDParams):
    """
    Take action to initiate an OBEX CONNECT REQ for BIP.
    """
    tc = params.test_case_name

    prim_conn_type = {
        BIPConnType.PRIM_REMOTE_DISPLAY: [
            "BIP/RDI/FSF/BV-10-C", "BIP/RDI/RMD/BV-01-C", "BIP/RDI/MFS/BV-07-C",
            "BIP/RDI/FFC/BV-09-C", "BIP/RDI/FFC/BV-07-C", "BIP/RDI/FFC/BV-05-C",
            "BIP/RDI/FFC/BV-03-C", "BIP/RDI/FFC/BV-01-C", "BIP/RDI/MFS/BV-25-C",
            "BIP/RDI/MFS/BV-24-C", "BIP/RDI/FSF/BV-09-C"],
        BIPConnType.PRIM_REMOTE_CAMERA: [
            "BIP/RCI/RMC/BV-02-C", "BIP/RCI/FSF/BV-02-C", "BIP/RCI/FSF/BV-01-C",
            "BIP/RCI/MFS/BV-22-C", "BIP/RCI/MFS/BV-21-C", "BIP/RCI/MFS/BV-20-C",
            "BIP/RCI/MFS/BV-19-C"],
        BIPConnType.PRIM_IMAGE_PULL: [
            "BIP/IPLI/PLL/BV-01-C", "BIP/IPLI/MFS/BV-09-C", "BIP/IPLI/MFS/BV-08-C",
            "BIP/IPLI/MFS/BV-07-C", "BIP/IPLI/FFC/BV-07-C", "BIP/IPLI/FFC/BV-05-C",
            "BIP/IPLI/FFC/BV-03-C", "BIP/IPLI/FFC/BV-01-C", "BIP/IPLI/MFS/BV-15-C",
            "BIP/IPLI/MFS/BV-13-C", "BIP/IPLI/MFS/BV-11-C", "BIP/IPLI/MFS/BV-10-C"],
        BIPConnType.PRIM_AUTO_ARCHIVE: [
            "BIP/AAR/ACH/BV-01-C", "BIP/AAR/FSF/BV-08-C", "BIP/AAI/FFC/BV-08-C",
            "BIP/AAI/FFC/BV-06-C", "BIP/AAI/FFC/BV-02-C", "BIP/AAI/MFS/BV-16-C",
            "BIP/AAI/MFS/BV-12-C", "BIP/AAI/MFS/BV-14-C", "BIP/AAI/FFC/BV-04-C"],
        BIPConnType.PRIM_ADVANCED_IMAGE_PRINTING: [
            "BIP/AIPI/FFC/BV-01-C", "BIP/AIPI/ADP/BV-01-C", "BIP/AIPI/MFS/BV-17-C",
            "BIP/AIPI/FSF/BV-05-C"],
    }

    sec_conn_type_map = {
        BIPConnType.SEC_ARCHIVED_OBJECTS: [
            "BIP/AAI/ACH/BV-01-C", "BIP/AAR/MFS/BV-09-C", "BIP/AAR/MFS/BV-08-C",
            "BIP/AAR/MFS/BV-13-C", "BIP/AAR/MFS/BV-15-C", "BIP/AAR/FFC/BV-01-C",
            "BIP/AAR/FFC/BV-03-C", "BIP/AAR/FFC/BV-05-C", "BIP/AAR/FFC/BV-07-C"],
        BIPConnType.SEC_REFERENCED_OBJECTS: [
            "BIP/AIPR/FFC/BV-02-C", "BIP/AIPR/FSF/BV-06-C", 
            "BIP/AIPR/ADP/BV-01-C","BIP/AIPR/MFS/BV-18-C"],
    }

    sec_server_register = {
        BIPConnType.SEC_REFERENCED_OBJECTS: [
            "BIP/AIPI/ADP/BV-01-C", "BIP/AIPI/FFC/BV-01-C",
            "BIP/AIPI/MFS/BV-17-C", "BIP/AIPI/FSF/BV-05-C"],
        BIPConnType.SEC_ARCHIVED_OBJECTS: [
            "BIP/AAR/ACH/BV-01-C", "BIP/AAI/MFS/BV-12-C", "BIP/AAI/MFS/BV-14-C",
            "BIP/AAI/MFS/BV-16-C", "BIP/AAI/FFC/BV-02-C", "BIP/AAI/FFC/BV-04-C",
            "BIP/AAI/FFC/BV-06-C", "BIP/AAI/FFC/BV-08-C"],
    }

    def lookup(mapping):
        for conn_type, cases in mapping.items():
            if tc in cases:
                return conn_type
        return None

    if tc in ["BIP/AAR/MFS/BV-07-C", "BIP/AAR/MFS/BV-10-C", "BIP/AAR/MFS/BV-11-C"]:
        return True

    sec_conn_type = lookup(sec_conn_type_map)
    if sec_conn_type is not None:
        btp.bip_second_connect(conn_type=sec_conn_type)
        return btp.bip_wait_for_client_connected(role=BIPObexRole.SECONDARY)

    conn_type = lookup(prim_conn_type) or BIPConnType.PRIM_IMAGE_PUSH
    btp.bip_client_connect(conn_type=conn_type)
    if not btp.bip_wait_for_client_connected():
        return False

    register_type = lookup(sec_server_register)
    if register_type is not None:
        btp.bip_second_server_register(conn_type=register_type)

    if tc in ["BIP/CL/GOEP/SRM/BV-01-C", "BIP/CL/GOEP/SRM/BV-03-C"]:
        img, encoding, pixel = btp.bip_prepare_put_image()
        btp.bip_put_image(img, encoding, pixel)
        if not btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP,
            rsp_code=OBEXRspCode.SUCCESS):
            return False
    if tc in ["BIP/CL/GOEP/SRMP/BV-01-C"]:
        img, encoding, pixel = btp.bip_prepare_put_image()
        btp.bip_put_image(img, encoding, pixel)
        return btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP, rsp_code=OBEXRspCode.SUCCESS,timeout = 60)
    return True


def hdl_wid_23(params: WIDParams):
    """
    Take action to send GetCapabilities.
    """
    if params.test_case_name in ["BIP/AAR/MFS/BV-07-C", "BIP/AAR/MFS/BV-11-C",
                                "BIP/AAR/MFS/BV-13-C","BIP/AAR/FFC/BV-01-C"]:
        btp.bip_second_get_capabilities()
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_CAPS_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)
    btp.bip_get_capabilities()
    return btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_GET_CAPS_RSP, rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_24(params: WIDParams):
    """
    Take action to send GetImagesList
    """
    app_params = {BIPAppParamTag.NB_RETURNED_HANDLES: 0xFFFF,
                  BIPAppParamTag.LIST_START_OFFSET: 0,
                  BIPAppParamTag.LATEST_CAPTURED_IMAGES: 0}
    hdr = {OBEXHdr.APP_PARAM: app_params,
           OBEXHdr.IMG_DESCRIPTION: b""}
    data = bytearray()
    btp.bip_add_headers(data, hdr)

    secondary_cases = ["BIP/AAI/ACH/BV-01-C", "BIP/AAR/MFS/BV-09-C",
                       "BIP/AAR/MFS/BV-08-C", "BIP/AAR/MFS/BV-10-C",
                       "BIP/AAR/MFS/BV-11-C", "BIP/AAR/MFS/BV-13-C",
                       "BIP/AAR/MFS/BV-15-C", "BIP/AAR/FFC/BV-03-C"]
    if params.test_case_name in secondary_cases:
        btp.bip_second_get_image_list(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_image_list(data=data)
    handles = btp.bip_get_image_list_format()
    if handles is None:
        return False
    get_stack().bip.image_db.set_last_image_list(handles)
    return True


def hdl_wid_25(params: WIDParams):
    """
    Take action to send GetImagesList that will result in Total Number of Images.
    """
    tc = params.test_case_name

    zero_handles_cases = ["BIP/IPLI/FFC/BV-05-C", "BIP/RDI/FFC/BV-05-C",
                          "BIP/AAR/FFC/BV-05-C"]
    latest_captured_cases = ["BIP/IPLI/FFC/BV-07-C", "BIP/RDI/FFC/BV-07-C",
                             "BIP/AAR/FFC/BV-07-C", "BIP/AAI/FFC/BV-08-C"]
    secondary_cases = ["BIP/AAR/FFC/BV-05-C", "BIP/AAR/FFC/BV-07-C"]

    app_params = {
        BIPAppParamTag.NB_RETURNED_HANDLES: 0x0 if tc in zero_handles_cases else 0xFFFF,
        BIPAppParamTag.LIST_START_OFFSET: 0,
        BIPAppParamTag.LATEST_CAPTURED_IMAGES: 1 if tc in latest_captured_cases else 0}
    hdr = {OBEXHdr.APP_PARAM: app_params,
           OBEXHdr.IMG_DESCRIPTION: b""}
    data = bytearray()
    btp.bip_add_headers(data, hdr)

    if tc in secondary_cases:
        btp.bip_second_get_image_list(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_image_list(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP,
        rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_27(params: WIDParams):
    """
    Take action to send GetImagesList that have filtering parameter set to <param>.
    """
    filter_values = {
        'created': '19700101T000000Z-*',
        'modified': '19700101T000000Z-*',
        'encoding': 'JPEG',
        'pixel': '0*0-65535*65535',
    }

    desc = (params.description or '').lower()
    param = 'created'
    for name in ('created', 'modified', 'encoding', 'pixel'):
        if name in desc:
            param = name
            break
    value = filter_values[param]

    img_desc_xml = (
        '<image-handles-descriptor version="1.0">'
        f'<filtering-parameters {param}="{value}"/>'
        '</image-handles-descriptor>\x00')

    app_params = {BIPAppParamTag.NB_RETURNED_HANDLES: 0xFFFF,
                  BIPAppParamTag.LIST_START_OFFSET: 0,
                  BIPAppParamTag.LATEST_CAPTURED_IMAGES: 0}
    hdr = {OBEXHdr.APP_PARAM: app_params,
           OBEXHdr.IMG_DESCRIPTION: img_desc_xml}

    data = bytearray()
    btp.bip_add_headers(data, hdr)
    if params.test_case_name == "BIP/AAR/MFS/BV-07-C":
        btp.bip_second_get_image_list(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_LIST_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_image_list(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_LIST_RSP,
        rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_28(params: WIDParams):
    """
    Take action to send GetImageProperties.
    """
    m = re.search(r'handle\s+(\d{7})', params.description)
    handle = (m.group(1) if m else '1000001').encode("utf-16-be")
    hdr = {OBEXHdr.IMG_HANDLE: handle}
    data = bytearray()
    btp.bip_add_headers(data, hdr)
    if params.test_case_name == "BIP/AAR/MFS/BV-15-C":
        btp.bip_second_get_image_properties(data=data)
        return btp.bip_wait_for_operation_complete(
                event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_PROPERTIES_RSP,
                rsp_code=OBEXRspCode.SUCCESS,
                role=BIPObexRole.SECONDARY)

    btp.bip_get_image_properties(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_PROPERTIES_RSP,
        rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_29(params: WIDParams):
    """
    Take action to send GetImage for handle 1000001.
    """
    handle = b''
    m = re.search(r'handle\s+(\d{7})', params.description)
    if m:
        handle = m.group(1).encode("utf-16-be")
    hdr = {OBEXHdr.IMG_HANDLE: handle,
           OBEXHdr.IMG_DESCRIPTION: b""}
    data = bytearray()
    btp.bip_add_headers(data, hdr)

    secondary_cases = ["BIP/AAI/ACH/BV-01-C", "BIP/AAR/MFS/BV-09-C",
                       "BIP/AAR/MFS/BV-08-C", "BIP/AAR/MFS/BV-11-C"]
    if params.test_case_name in secondary_cases:
        btp.bip_second_get_image(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_IMAGE_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_image(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_IMAGE_RSP,
        rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_30(params: WIDParams):
    """
    Take action to send GetLinkedThumbnail for handle 1000001.
    """
    handle = ''
    m = re.search(r'handle\s+(\d{7})', params.description)
    if m:
        handle = m.group(1).encode("utf-16-be")
    hdr = {OBEXHdr.IMG_HANDLE: handle}
    data = bytearray()
    btp.bip_add_headers(data, hdr)
    if params.test_case_name == "BIP/AAR/MFS/BV-10-C":
        btp.bip_second_get_linked_thumbnail(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_THUMBNAIL_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_linked_thumbnail(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_LINKED_THUMBNAIL_RSP,
        rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_31(params: WIDParams):
    """
    Take action to send GetLinkedAttachment for handle 1000001.
    """
    handle = b''
    m = re.search(r'handle\s+(\d{7})', params.description)
    if m:
        handle = m.group(1).encode("utf-16-be")
    hdr = {OBEXHdr.IMG_HANDLE: handle}
    data = bytearray()
    btp.bip_add_headers(data, hdr)
    name = None
    if params.test_case_name == "BIP/AAR/MFS/BV-15-C":
        btp.bip_second_get_image_properties(data=data)
        name = btp.bip_get_attachment_names(role=BIPObexRole.SECONDARY)
    else:
        btp.bip_get_image_properties(data=data)
        name = btp.bip_get_attachment_names()

    if name is None:
        log('hdl_wid_31: no attachment name resolved from GetImageProperties, failing')
        return False
    if isinstance(name, (list, tuple)):
        if not name:
            log('hdl_wid_31: empty attachment name list, failing')
            return False
        name = name[0]

    data = bytearray()
    hdr = {OBEXHdr.IMG_HANDLE: handle,
           OBEXHdr.NAME: name}
    btp.bip_add_headers(data, hdr)

    if params.test_case_name == "BIP/AAR/MFS/BV-15-C":
        btp.bip_second_get_linked_attachment(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_LINKED_ATTACHMENT_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_linked_attachment(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_GET_LINKED_ATTACHMENT_RSP,
        rsp_code=OBEXRspCode.SUCCESS)

def hdl_wid_32(params: WIDParams):
    """
    Take action to send DeleteImage for handle 1000002.
    """
    handle = None
    m = re.search(r'handle\s+(\d{7})', params.description)
    if m:
        handle = m.group(1).encode("utf-16-be")
    hdr = {OBEXHdr.IMG_HANDLE: handle}
    data = bytearray()
    btp.bip_add_headers(data, hdr)
    if params.test_case_name == "BIP/AAR/MFS/BV-13-C":
        btp.bip_second_delete_image(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_DELETE_IMAGE_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_delete_image(data=data)
    return btp.bip_wait_for_operation_complete(
        event=defs.BTP_BIP_EV_CLIENT_DELETE_IMAGE_RSP,
        rsp_code=OBEXRspCode.SUCCESS)



def hdl_wid_33(_: WIDParams):
    """
    Take action to send PutImage request.
    """
    img, encoding, pixel = btp.bip_prepare_put_image()
    btp.bip_put_image(img, encoding, pixel)
    return btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_PUT_IMAGE_RSP, rsp_code=OBEXRspCode.SUCCESS,timeout = 60)


def hdl_wid_34(params: WIDParams):
    """
    Take action to send PutLinkedThumbnail request.
    """
    btp.bip_put_linked_thumbnail()
    if not btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_PUT_LINKED_THUMBNAIL_RSP, rsp_code=OBEXRspCode.SUCCESS, timeout=60):
        log('hdl_wid_34: PutLinkedThumbnail failed')
        return False
    if params.test_case_name == "BIP/IPSI/MFS/BV-05-C":
        btp.bip_put_linked_attachment()
        if not btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_PUT_LINKED_ATTACHMENT_RSP, rsp_code=OBEXRspCode.SUCCESS, timeout=60):
            log('hdl_wid_34: PutLinkedAttachment failed')
            return False

    return True

def hdl_wid_35(params: WIDParams):
    """
    Take action to create an l2cap channel or rfcomm channel for a
    secondary OBEX connection.
    """
    conn = btp.bip_get_connection()
    if conn is None:
        return False

    uuid = BIPImagingSvclass.IMAGING_ARCHIVE
    conn_type = BIPConnType.SEC_ARCHIVED_OBJECTS
    conn_role = BIPObexRole.SECONDARY

    if params.test_case_name in ["BIP/AIPR/FFC/BV-02-C", "BIP/AIPR/FSF/BV-06-C",
                                 "BIP/AIPR/ADP/BV-01-C", "BIP/AIPR/MFS/BV-18-C"]:
        uuid = BIPImagingSvclass.IMAGING_REFOBJS
        conn_type = BIPConnType.SEC_REFERENCED_OBJECTS

    btp.bip_sdp_discover(uuid=uuid)
    btp.bip_wait_for_sdp_finished()
    sdp_conn = btp.bip_get_sdp_connection()

    if sdp_conn and sdp_conn.l2cap_psm:
        btp.bip_second_connect_l2cap(psm=sdp_conn.l2cap_psm)
        btp.bip_wait_for_transport_connected()
    elif sdp_conn and sdp_conn.rfcomm_channel:
        btp.bip_second_connect_rfcomm(channel=sdp_conn.rfcomm_channel)
        btp.bip_wait_for_transport_connected()

    if params.test_case_name in ["BIP/AAR/MFS/BV-07-C", "BIP/AAR/MFS/BV-10-C",
                                 "BIP/AAR/MFS/BV-11-C"]:
        btp.bip_second_connect(conn_type=conn_type)
        btp.bip_wait_for_client_connected(role=conn_role)

    return True


def hdl_wid_36(_: WIDParams):
    """
    Take action to send StartArchive.
    """
    data = bytearray()
    # Archived Objects service UUID: 8E61F95E-1A79-11D4-8EA4-00805F9B9834
    archived_obj_uuid = bytes.fromhex('8E61F95E1A7911D48EA400805F9B9834')
    hdr = {OBEXHdr.APP_PARAM: {BIPAppParamTag.SERVICE_ID: archived_obj_uuid}}
    btp.bip_add_headers(data, hdr)
    btp.bip_start_archive(data=data)
    return True

def hdl_wid_37(_: WIDParams):
    """
    Take action to send StartPrint
    """
    data = bytearray()
    # Referenced Objects service UUID: 8E61F95F-1A79-11D4-8EA4-00805F9B9834
    ref_obj_uuid = bytes.fromhex('8E61F95F1A7911D48EA400805F9B9834')
    hdr = {OBEXHdr.APP_PARAM: {BIPAppParamTag.SERVICE_ID: ref_obj_uuid}}
    btp.bip_add_headers(data, hdr)
    btp.bip_start_print(data=data)
    return True

def hdl_wid_38(params: WIDParams):
    """
    Take action to send GetPartialImage
    """
    handle = b''
    m = re.search(r'handle\s+(\d{7})', params.description or '')
    if m:
        handle = m.group(1).encode("utf-16-be")
    else:
        handle = '1000001'.encode("utf-16-be")

    role = BIPObexRole.PRIMARY
    if params.test_case_name in ["BIP/AIPR/FFC/BV-02-C", "BIP/AIPR/FSF/BV-06-C",
                                 "BIP/AIPR/ADP/BV-01-C", "BIP/AIPR/MFS/BV-18-C"]:
        role = BIPObexRole.SECONDARY

    if role == BIPObexRole.SECONDARY:
        # Referenced Objects has no GetImageProperties; the Name is the image
        # file name referenced via the IMG SRC tag in the printer-control
        # object, which the server-side StartPrint handler parsed and stored.
        name = get_stack().bip.image_db.get_print_img_src()
        if not name:
            log('hdl_wid_38: no IMG SRC resolved from StartPrint, failing')
            return False
    else:
        data = bytearray()
        btp.bip_add_headers(data, {OBEXHdr.IMG_HANDLE: handle})
        btp.bip_get_image_properties(data=data)
        name = btp.bip_get_attachment_names(role=role)

        if not name:
            log('hdl_wid_38: no attachment name resolved from GetImageProperties, failing')
            return False
        if isinstance(name, (list, tuple)):
            name = name[0]

    app_params = {BIPAppParamTag.PARTIAL_FILE_LENGTH: 0xFFFFFFFF,
                  BIPAppParamTag.PARTIAL_FILE_START_OFFSET: 0}
    hdr = {OBEXHdr.NAME: name,
           OBEXHdr.APP_PARAM: app_params}
    data = bytearray()
    btp.bip_add_headers(data, hdr)

    if role == BIPObexRole.SECONDARY:
        btp.bip_second_get_partial_image(data=data)
        return btp.bip_wait_for_operation_complete(
            event=defs.BTP_BIP_EV_SECOND_CLIENT_GET_PARTIAL_IMAGE_RSP,
            rsp_code=OBEXRspCode.SUCCESS,
            role=BIPObexRole.SECONDARY)

    btp.bip_get_partial_image(data=data)
    return btp.bip_wait_for_operation_complete(event=defs.BTP_BIP_EV_CLIENT_GET_PARTIAL_IMAGE_RSP, rsp_code=OBEXRspCode.SUCCESS)


def hdl_wid_39(_: WIDParams):
    """
    Take action to send GetMonitoringImage with StoreFlag set to 0x00
    """
    data = bytearray()
    hdr = {OBEXHdr.APP_PARAM: {BIPAppParamTag.STORE_FLAG: 0x00}}
    btp.bip_add_headers(data, hdr)
    btp.bip_get_monitoring_image(data=data)
    return True

def hdl_wid_40(_: WIDParams):
    """
    Take action to send GetMonitoringImage with StoreFlag set to 0x01
    """
    data = bytearray()
    hdr = {OBEXHdr.APP_PARAM: {BIPAppParamTag.STORE_FLAG: 0x01}}
    btp.bip_add_headers(data, hdr)
    btp.bip_get_monitoring_image(data=data)
    return True

def hdl_wid_41(params: WIDParams):
    """
    Take action to send RemoteDisplay for handle.
    """
    handle = None
    m = re.search(r'handle\s+(\d{7})', params.description)
    if m:
        handle = m.group(1)

    if params.test_case_name == "BIP/RDI/MFS/BV-25-C":
        handles = get_stack().bip.image_db.get_last_image_list()
        handle = handles[0]
        display_func = BIPRemoteDisplay.SELECT_IMAGE
    elif params.test_case_name == "BIP/RDI/MFS/BV-24-C":
        handle = btp.bip_get_put_image_handle()
        if handle is None:
            return False
        display_func = BIPRemoteDisplay.SELECT_IMAGE

    if params.test_case_name in ["BIP/RDI/FSF/BV-09-C", "BIP/RDI/RMD/BV-01-C"]:
        display_func = BIPRemoteDisplay.NEXT_IMAGE
    elif params.test_case_name == "BIP/RDI/FSF/BV-10-C":
        display_func = BIPRemoteDisplay.PREVIOUS_IMAGE
    elif params.test_case_name in ["BIP/RDI/MFS/BV-24-C", "BIP/RDI/MFS/BV-25-C"]:
        display_func = BIPRemoteDisplay.SELECT_IMAGE
    else:
        display_func = BIPRemoteDisplay.CURRENT_IMAGE

    btp.bip_remote_display(handle=handle, display_func=display_func)
    return True


def hdl_wid_4004(params: WIDParams):
    """
    Please accept the OBEX CONNECT REQ.
    """
    role = BIPObexRole.PRIMARY
    if btp.bip_has_pending_second_connect():
        btp.bip_second_connect_rsp(rsp_code=OBEXRspCode.SUCCESS)
    else:
        btp.bip_connect_rsp(rsp_code=OBEXRspCode.SUCCESS)
    return btp.bip_wait_for_client_connected(role=role)


def hdl_wid_4017(params: WIDParams):
    """
    Please accept the l2cap channel connection for an OBEX connection.
    """
    return btp.bip_wait_for_transport_connected()


def hdl_wid_4050(_: WIDParams):
    """
    Take action to reject the ACTION command sent by PTS.
    """
    return True


def hdl_wid_4051(_: WIDParams):
    """
    Was the currently displayed file or folder received by the IUT?
    """
    return True


def hdl_wid_4091(_: WIDParams):
    """
    Take action to reject the SESSION command sent by PTS.
    """
    return True

def hdl_wid_4054(_: WIDParams):
    """
    Was the currently displayed file or folder sent by the IUT?
    """
    return True

def hdl_wid_4058(_: WIDParams):
    """
    Please respond to the PUT REQUEST with an SRM ENABLED header
    and an SRMP WAIT header.
    """
    return True


def hdl_wid_4800(_: WIDParams):
    """
    Please remove pairing from the IUT then click OK.
    """
    btp.gap_unpair()
    return True


def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.
    """
    btp.gap_set_connectable()
    btp.gap_set_general_discoverable()
    return True
