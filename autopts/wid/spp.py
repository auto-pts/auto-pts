#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright 2026, NXP.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#

import logging
from time import sleep
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.types import WIDParams

log = logging.debug

def spp_wid_hdl(wid, description, test_case_name):
    # Local table lookup first; otherwise hand over to generic handler.
    from autopts.wid import generic_wid_hdl
    log(f'{spp_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])

def hdl_wid_0(_: WIDParams):
    """
    Make the Implementation Under Test (IUT) discoverable and connectable.

    Description: Implements WID 0 for SPP profile - makes the IUT discoverable
    and connectable for the tester to initiate connection.
    """
    stack = get_stack()

    # Make IUT discoverable and connectable
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    # Register SPP server on RFCOMM channel 5
    btp.spp_register_server(channel=5)

    btp.rfcomm_listen(channel=5)

    return True

def hdl_wid_1(params: WIDParams):
    """Initiate a RFCOMM session using the server channel number found on the SDP record and start a new data link connection."""
    btp.gap_start_discov(transport='bredr', discov_type='passive', mode='general')
    sleep(10)
    btp.gap_stop_discov()

    if not btp.check_discov_results(addr_type=defs.BTP_BR_ADDRESS_TYPE):
        return False

    btp.gap_conn(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    btp.gap_wait_for_connection()

    btp.spp_discover(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)
    stack = get_stack()
    # Wait for SPP discovered event
    stack.spp.wait_for_discovered()

    # Verify that discovery was successful
    if not stack.spp.discovered_channel:
        logging.error("SPP service discovery failed - no channel found")
        return False

    logging.debug("SPP service discovered: addr=%s, addr_type=%d, channel=%d",
                  stack.spp.discovered_addr,
                  stack.spp.discovered_addr_type,
                  stack.spp.discovered_channel)

    btp.rfcomm_connect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=stack.spp.discovered_channel)

    return True

def hdl_wid_2(_: WIDParams):
    """Please Disconnect the RFCOMM session."""
    stack = get_stack()
    btp.rfcomm_disconnect(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE, channel=stack.spp.discovered_channel)
    return True

def hdl_wid_3(_: WIDParams):
    """
    Please delete the pairing with the PTS using the Implementation Under Test (IUT), then click Ok.

    Description: Implements WID 3 for SPP profile - deletes any existing pairing
    with the PTS to ensure a clean state for the test.
    """
    stack = get_stack()

    # Delete pairing/bonding with PTS
    btp.gap_unpair(bd_addr_type=defs.BTP_BR_ADDRESS_TYPE)

    return True

def hdl_wid_20000(_: WIDParams):
    """
    Please prepare IUT into a connectable mode in BR/EDR.

    Description: Verify that the Implementation Under Test (IUT) can accept
    GATT connect request from PTS.
    """
    stack = get_stack()

    # Register SPP server on RFCOMM channel 5
    btp.spp_register_server(channel=5)
    # Make IUT discoverable and connectable for BR/EDR
    btp.gap_set_conn()
    btp.gap_set_gendiscov()

    return True
