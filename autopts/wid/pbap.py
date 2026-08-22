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

from autopts.ptsprojects.stack import PBAPInfo
from autopts.pybtp import btp, defs
from autopts.pybtp.types import (
    BtPbapApplParamTagId,
    IOCap,
    OBEXHdr,
    OBEXRspCode,
    PBAPPropertySelector,
    PBAPPullType,
    WIDParams,
)

log = logging.debug


def pbap_wid_hdl(wid, description, test_case_name):
    from autopts.wid import generic_wid_hdl
    log(f'{pbap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(params: WIDParams):
    """
    description: Send a PullPhoneBook request with name=telecom/pb.vcf
    """
    data_ba = bytearray()
    name = params.description.split('=')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if params.test_case_name == 'PBAP/PCE/PBD/BV-38-C':
        # X - BT - UCI
        ps = PBAPPropertySelector.X_BT_UCI
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    elif params.test_case_name in ["PBAP/PCE/PBD/BV-39-C", "PBAP/PCE/PBD/BV-41-C"]:
        # no X-BT-UCI
        ps = PBAPPropertySelector.N
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    elif params.test_case_name == "PBAP/PCE/PBD/BV-40-C":
        # X - BT - UID
        ps = PBAPPropertySelector.X_BT_UID
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if params.test_case_name != 'PBAP/PCE/PDF/BV-06-C':
        if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
            return False

    return True


def hdl_wid_2(params: WIDParams):
    """
    description: Send a PullPhoneBook request with MaxListCount = 0 and name=telecom/pb.vcf
    """
    data_ba = bytearray()

    name = params.description.split('name=')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 0x0}
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_3(params: WIDParams):
    """
    description: Send a PullPhoneBook request with ResetNewMissedCalls = 1 and name=telecom/mch.vcf
    """
    data_ba = bytearray()

    name = params.description.split('name=')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.RESET_NEW_MISSED_CALLS: 0x1}
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_4(params: WIDParams):
    """
    description: Send a PullPhoneBook request with no ResetNewMissedCalls and name=telecom/mch.vcf
    """
    data_ba = bytearray()

    name = params.description.split('name=')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_5(params: WIDParams):
    """
    description: Send a PullPhoneBook request with vCardSelector and name=telecom/pb.vcf
    """
    data_ba = bytearray()

    name = params.description.split('name=')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if params.test_case_name == "PBAP/PCE/PBD/BV-44-C":
        value = (PBAPPropertySelector.VERSION | PBAPPropertySelector.FN |
                 PBAPPropertySelector.N | PBAPPropertySelector.EMAIL | PBAPPropertySelector.TEL)
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.VCARD_SELECTOR: value}

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_6(params: WIDParams):
    """
    description: Send a PullPhoneBook request with vCardSelector and vCardSelectorOperator and name= telecom/pb.vcf
    """
    data_ba = bytearray()

    name = params.description.split('name=')[1].lstrip()

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)

    vs = (PBAPPropertySelector.VERSION | PBAPPropertySelector.FN |
          PBAPPropertySelector.N | PBAPPropertySelector.EMAIL)
    vso = 0x0

    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {
            BtPbapApplParamTagId.VCARD_SELECTOR: vs,
            BtPbapApplParamTagId.VCARD_SELECTOR_OPERATOR: vso
        }
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_8(params: WIDParams):
    """
    description: Make sure you set folder to /root/telecom
    """
    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    return True


def hdl_wid_9(params: WIDParams):
    """
    description: Send a PullvCardListing request for phonebook pb
    """
    data_ba = bytearray()

    # Set path to /telecom
    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False

    name = 'pb'
    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    # Add search parameters if specified in description
    if "search value set to PTS" in params.description:
        sp = 0x0  # Search property
        sv = 'PTS'  # Search value
        hdr[OBEXHdr.APP_PARAM] = {
            BtPbapApplParamTagId.SEARCH_PROPERTY: sp,
            BtPbapApplParamTagId.SEARCH_VALUE: sv
        }

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)

    if params.test_case_name != "PBAP/PCE/PBF/BV-03-C":
        if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__):
            return False

    return True


def hdl_wid_10(params: WIDParams):
    """
    description: Send a PullvCardListing request with MaxListCount = 0  for phonebook pb
    """
    data_ba = bytearray()

    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    name = params.description.split(' ')[-1]
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 0x0}
    }

    if btp.pbap_connection_is_l2cap():
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)
    result = btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__)
    if not result:
        return False
    return True


def hdl_wid_11(params: WIDParams):
    """
    description: Send a PullvCardListing request with ResetNewMissedCalls = 1  for phonebook mch
    """
    data_ba = bytearray()
    name = params.description.split(' ')[-1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.RESET_NEW_MISSED_CALLS: 0x1}
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__):
        return False
    return True


def hdl_wid_12(params: WIDParams):
    """
    description: Send a PullvCardListing request with No ResetNewMissedCalls for phonebook mch
    """
    data_ba = bytearray()
    name = params.description.split(' ')[-1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__):
        return False
    return True


def hdl_wid_13(params: WIDParams):
    """
    description: Send a PullvCardListing request with vCardSelector for phonebook pb
    """
    data_ba = bytearray()
    name = params.description.split(' ')[-1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    ps = PBAPPropertySelector.N
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.VCARD_SELECTOR: ps}
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__):
        return False
    return True


def hdl_wid_14(params: WIDParams):
    """
    description: Send a PullvCardListing request with no vCardSelector  for phonebook mch
    """
    data_ba = bytearray()
    name = params.description.split(' ')[-1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDLISTING,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_listing(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_listing.__name__):
        return False
    return True


def hdl_wid_15(params: WIDParams):
    """
    description: Send a PullvCardEntry request in phonebook.
    """
    # Set path to correct folder
    if params.test_case_name != "PBAP/PCE/PBF/BV-02-C":
        folder_name = params.description.split(' ')[-1]
        btp.pbap_pce_set_phone_book(path=folder_name)
        if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
            return False
    else:
        btp.pbap_pce_set_phone_book(path='telecom')
        if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
            return False
        btp.pbap_pce_set_phone_book(path='pb')
        if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
            return False

    data_ba = bytearray()
    name = '1.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDENTRY,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    # Add property selector based on test case
    if params.test_case_name == "PBAP/PCE/PBB/BV-33-C":
        ps = PBAPPropertySelector.X_BT_UCI
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    elif params.test_case_name in ["PBAP/PCE/PBB/BV-34-C", "PBAP/PCE/PBB/BV-36-C"]:
        ps = PBAPPropertySelector.N
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    elif params.test_case_name == "PBAP/PCE/PBB/BV-35-C":
        ps = PBAPPropertySelector.X_BT_UID
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    elif params.test_case_name == "PBAP/PCE/PBB/BV-37-C":
        ps = PBAPPropertySelector.PHOTO
        hdr[OBEXHdr.APP_PARAM] = {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}

    if hdr.get(OBEXHdr.APP_PARAM) is None:
        hdr[OBEXHdr.APP_PARAM] = {}
    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_entry(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_entry.__name__):
        return False

    # Navigate back up
    btp.pbap_pce_set_phone_book(path='..')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False

    return True


def hdl_wid_16(params: WIDParams):
    """
    description: Send a PullvCardEntry request which filter for Name (N) and Telephone (TEL)
    """
    # Navigate to /telecom/pb
    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='pb')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False

    data_ba = bytearray()
    name = '0.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    ps = PBAPPropertySelector.N | PBAPPropertySelector.TEL
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDENTRY,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.PROPERTY_SELECTOR: ps}
    }

    hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT: 10})
    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_entry(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_entry.__name__):
        return False
    return True


def hdl_wid_17(params: WIDParams):
    """
    description: Send a PullvCardEntry request with X-BT-UID
    """
    data_ba = bytearray()
    name = 'X-BT-UID:1234567890ABCDEF1234567890000001'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.VCARDENTRY,
        OBEXHdr.NAME: name,
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_vcard_entry(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_vcard_entry.__name__):
        return False
    return True


def hdl_wid_18(params: WIDParams):
    """
    description: Make sure you set folder to /telecom
    """
    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    return True


def hdl_wid_20(params: WIDParams):
    """
    description: Click Ok if the Implementation Under Test (IUT) was prompted to accept the PBAP connection.
    """
    return True


def hdl_wid_21(params: WIDParams):
    """
    description: Make sure you set folder to /root/SIM1/telecom.
    """
    btp.pbap_pce_set_phone_book(path='/')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='SIM1')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    btp.pbap_pce_set_phone_book(path='telecom')
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_set_phone_book.__name__):
        return False
    return True


def hdl_wid_22(params: WIDParams):
    """
    description: Verify the content vcard sent by the IUT is accurate.
    """
    return True


def hdl_wid_23(params: WIDParams):
    """
    description: Please add or remove a Contact. Please OK when done.
    """
    btp.pbap_delete_vcard_entry('PTS')
#     btp.pbap_reset_pfv()
#     btp.pbap_reset_slv()
    return True


def hdl_wid_24(params: WIDParams):
    """
    description: Please modify a field other than N, FN, TEL, EMAIL, MAILER, ADR or X-BT-UCI of an existing contact
    """
    btp.pbap_modify_vcard_property('PTS', 'ORG', 'City Hospital')
    return True


def hdl_wid_25(params: WIDParams):
    """
    description: Please modify the N, TEL, EMAIL, MAILER, ADR or X-BT-UCI of an existing contact
    """
    btp.pbap_modify_vcard_property('PTS', 'TEL', 'TYPE=CELL:+12343423847')
    return True


def hdl_wid_26(params: WIDParams):
    """
    description: Please Reset DBI.
    """
    btp.pbap_reset_bdi()
    return True


def hdl_wid_27(params: WIDParams):
    """
    description: Verify that the phonebook size =  10
    """
    return True


def hdl_wid_28(params: WIDParams):
    """
    description: Verify that the new missed calls is not set to 0 for phonebook  telecom/mch
    """
    return True


def hdl_wid_29(params: WIDParams):
    """
    description: Send a PullPhoneBook request with photo property settelecom/pb.vcf
    """
    data_ba = bytearray()
    name = params.description.split('set')[1]

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    # PHOTO property selector
    value = PBAPPropertySelector.PHOTO
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.VCARD_SELECTOR: value}
    }

    is_l2cap = btp.pbap_connection_is_l2cap()
    if is_l2cap:
        hdr.update({OBEXHdr.SRM: 0x01})

#     hdr[OBEXHdr.APP_PARAM].update({BtPbapApplParamTagId.MAX_LIST_COUNT : 10})
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=is_l2cap)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False
    return True


def hdl_wid_32(params: WIDParams):
    """
    description: Verify that the new missed calls =  0
    """
    return True


def hdl_wid_33(params: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for PBAP.
    """
    target = bytearray([0x79, 0x61, 0x35, 0xf0, 0xf0, 0xc5,
                     0x11, 0xd8, 0x09, 0x66, 0x08, 0x00,
                     0x20, 0x0c, 0x9a, 0x66])
    hdr = {
        OBEXHdr.TARGET: target
    }

    features = btp.pbap_get_sdp_connection().supported_features
    if features != 0:
        local_feature = btp.pbap_get_pbap_connection().conn_info[PBAPInfo.LOCAL_SUPPORT_FEATURE]
        appl = {OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.SUPPORTED_FEATURES: local_feature}}
        hdr.update(appl)

    data_ba = bytearray()
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_pce_connect(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_connect.__name__):
        return False
    return True


def hdl_wid_36(params: WIDParams):
    """
    description: Take action to initiate an OBEX CONNECT REQ for PBAP without authentication.
    """
    target = bytearray([0x79, 0x61, 0x35, 0xf0, 0xf0, 0xc5,
                     0x11, 0xd8, 0x09, 0x66, 0x08, 0x00,
                     0x20, 0x0c, 0x9a, 0x66])
    hdr = {
        OBEXHdr.TARGET: target
    }

    features = btp.pbap_get_sdp_connection().supported_features
    if features != 0:
        local_feature = btp.pbap_get_pbap_connection().conn_info[PBAPInfo.LOCAL_SUPPORT_FEATURE]
        appl = {OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.SUPPORTED_FEATURES: local_feature}}
        hdr.update(appl)

    data_ba = bytearray()
    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_pce_connect(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_connect.__name__):
        return False
    return True


def hdl_wid_37(params: WIDParams):
    """
    description: Is the IUT capable of establishing connection to an unpaired device?
    """
    return True


def hdl_wid_38(params: WIDParams):
    """
    description: Click OK when the IUT becomes connectable.
    """
    btp.gap_set_conn()
    # btp.gap_set_io_cap(IOCap.no_input_output)
    btp.gap_set_gendiscov()
    return True


def hdl_wid_39(params: WIDParams):
    """
    description: Verify the content of the phonebook sent by the IUT is accurate.
    """
    return True


def hdl_wid_49(params: WIDParams):
    """
    description: Using the Implementation Under Test(IUT), initiate ACL Create Connection Request to the PTS
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    return True


def hdl_wid_4004(params: WIDParams):
    """
    description: Please accept the OBEX CONNECT REQ.
    """
#     if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pse_connect_rsp.__name__):
#         return False
    return True


def hdl_wid_4007(params: WIDParams):
    """
    description: Please accept the OBEX DISCONNECT REQ command.
    """
    return True


def hdl_wid_4010(params: WIDParams):
    """
    description:  Please accept the GET REQUEST with an SRM ENABLED header.
    """
    return True


def hdl_wid_4016(params: WIDParams):
    """
    description: Please accept the SET_PATH command.
    """
    except_state = OBEXRspCode.SUCCESS
    if params.test_case_name == 'PBAP/PSE/PBB/BI-01-C':
        except_state = OBEXRspCode.NOT_FOUND
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pse_set_phone_book_rsp.__name__, except_state=except_state):
        return False
    return True


def hdl_wid_4017(params: WIDParams):
    """
    description:  Please accept the l2cap channel connection for an OBEX connection
    """
    return True


def hdl_wid_4018(params: WIDParams):
    """
    description:  Please accept the rfcomm channel connection for an OBEX connection.
    """
    return True


def hdl_wid_4031(params: WIDParams):
    """
    description: Take action to initiate an OBEX DISCONNECT REQ
    """
    btp.pbap_pce_disconnect()
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_disconnect.__name__):
        return False
    return True


def hdl_wid_4034(params: WIDParams):
    """
    description: Take action to send a GET request without an SRM header.  Then allow the operation to complete as normal
    """
    data_ba = bytearray()
    name = 'telecom/pb.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 10}
    }

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=False)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False

    return True


def hdl_wid_4035(params: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header.  Then allow the operation to complete as normal.
    """

    data_ba = bytearray()
    name = 'telecom/pb.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.SRM: 0x01,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 10}
    }

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=True)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False

    return True


def hdl_wid_4036(params: WIDParams):
    """
    description: Take action to send a GET request with an SRM ENABLED header
    and an SRMP WAIT header. Then allow the operation to complete as normal.
    """
    data_ba = bytearray()
    name = 'telecom/pb.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.SRM: 0x01,
        OBEXHdr.SRMP: 0x01,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 10}
    }

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=True)
    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRMP, value=True)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False

    return True


def hdl_wid_4047(params: WIDParams):
    """
    description: Take action to create an l2cap channel for an OBEX connection.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    btp.pbap_sdp_discover()
    if not btp.pbap_wait_for_sdp_finished():
        return False
    psm = btp.pbap_get_sdp_connection().l2cap_psm
    btp.pbap_pce_l2cap_connect(psm=psm)
    if not btp.pbap_wait_for_transport_connected():
        return False
    return True


def hdl_wid_4048(params: WIDParams):
    """
    description: Take action to create an rfcomm channel for an OBEX connection
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    btp.pbap_sdp_discover()
    if not btp.pbap_wait_for_sdp_finished():
        return False
    channel = btp.pbap_get_sdp_connection().rfcomm_channel
    btp.pbap_pce_rfcomm_connect(channel=channel)
    if not btp.pbap_wait_for_transport_connected():
        return False
    return True


def hdl_wid_4050(params: WIDParams):
    """
    description:  Take action to reject the ACTION command sent by PTS.
    """
    return True


def hdl_wid_4054(params: WIDParams):
    """
    description: Was the currently displayed file or folder sent by the IUT?
    """
    return True


def hdl_wid_4056(params: WIDParams):
    """
    description: Was the currently displayed vcard sent by the IUT?
    """
    return True


def hdl_wid_4088(params: WIDParams):
    """
    description: Take action to ABORT the current operation.
    """
    btp.pbap_pce_abort()
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_abort.__name__):
        return False
    return True


def hdl_wid_4090(params: WIDParams):
    """
    description: Take action to send a GET REQUEST with an SRM ENABLED header
    and an SRMP WAIT header. The next GET REQUEST must also contain an SRMP
    WAIT header. The third GET REQUEST must not contain an SRMP WAIT header.
    """
    data_ba = bytearray()
    name = 'telecom/pb.vcf'

    conn_id = btp.pbap_get_info(None, PBAPInfo.CONN_ID)
    hdr = {
        OBEXHdr.CONN_ID: conn_id,
        OBEXHdr.TYPE: PBAPPullType.PHONEBOOK,
        OBEXHdr.NAME: name,
        OBEXHdr.SRM: 0x01,
        OBEXHdr.SRMP: 0x01,
        OBEXHdr.APP_PARAM: {BtPbapApplParamTagId.MAX_LIST_COUNT: 10}
    }

    btp.pbap_add_headers(data_ba, hdr)

    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRM, value=True)
    btp.pbap_set_info(key=PBAPInfo.LOCAL_SRMP, value=2)
    btp.pbap_pce_pull_phonebook(buf=data_ba)
    if not btp.pbap_wait_for_func_finished(func_name=btp.pbap_pce_pull_phonebook.__name__):
        return False

    return True


def hdl_wid_4091(params: WIDParams):
    """
    description:  Take action to reject the SESSION command sent by PTS.
    """
    return True


def hdl_wid_4100(params: WIDParams):
    """
    description: Take action to create an l2cap channel or rfcomm channel for an OBEX connection.
    """
    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()
    btp.pbap_sdp_discover()
    if not btp.pbap_wait_for_sdp_finished():
        return False
#     transport = defs.PBAP_TRANSPORT_L2CAP
    if params.test_case_name in ['PBAP/PCE/SSM/BV-10-C', 'PBAP/PCE/PBF/BV-03-C', 'PBAP/PCE/PDF/BV-06-C']:
        channel = btp.pbap_get_sdp_connection().rfcomm_channel
        btp.pbap_pce_rfcomm_connect(channel=channel)
    else:
        psm = btp.pbap_get_sdp_connection().l2cap_psm
        btp.pbap_pce_l2cap_connect(psm=psm)
    if not btp.pbap_wait_for_transport_connected():
        return False
    return True


def hdl_wid_4800(params: WIDParams):
    """
    description: Please remove pairing from the Implementation Under Test (IUT), then click Ok
    """
    btp.gap_unpair()
    return True


def hdl_wid_20000(params: WIDParams):
    """
    description: Please prepare IUT into a connectable mode in BR/EDR.
    """
    btp.gap_set_conn()
    btp.gap_set_io_cap(IOCap.no_input_output)
    btp.gap_set_gendiscov()
    return True
