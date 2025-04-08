#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

"""Script to test MMI description parser, MmiParser.

The purpose of this script is to keep all types of MMI descriptions that need
parsing in one place. This enables doing regression testing of MmiParser in
case a new description parsing is added.

"""

from autopts.ptsprojects.testcase import MmiParser

descriptions = [

    # project_name: GATT
    # wid: 69
    # test_case_name: TC_GAC_CL_BV_01_C
    # description: Please send prepare write request with handle = '00D3'O and size = '45' to the PTS.

    # Description: Verify that the Implementation Under Test (IUT) can send data according to negotiate MTU size.
    # style: MMI_Style_Ok_Cancel2 0x11141

    (("Please send prepare write request with handle = '00D3'O and size = '45' to the PTS.\n\n"
      "Description: Verify that the Implementation Under Test (IUT) can send data according to negotiate MTU size."),
     ['00D3', '45']),

    # project_name: GATT
    # wid: 27
    # test_case_name: TC_GAD_CL_BV_04_C
    # description: Discover all characteristics of service UUID= '180A'O,
    # Service start handle = 0x0030, end handle = 0x0047.

    # Description: Verify that the Implementation Under Test (IUT) can send Discover all charactieristics of a service.
    # style: MMI_Style_Ok_Cancel2 0x11141

    (("Discover all characteristics of service UUID= '180A'O,  Service start handle = 0x0030, end handle = 0x0047.\n\n"
      "Description: Verify that the Implementation Under Test (IUT) "
      "can send Discover all charactieristics of a service."),
     ["180A", "0x0030", "0x0047"]),

    # project_name: GATT
    # wid: 20
    # test_case_name: TC_GAD_CL_BV_02_C
    # description: Please send discover primary services with UUID value set
    # to '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O to the PTS.

    # Description: Verify that the Implementation Under Test (IUT) can send
    # Discover Primary Services UUID =
    # '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O.

    # style: MMI_Style_Ok_Cancel2 0x11141

    (("Please send discover primary services with UUID value set to '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O "
      "to the PTS.\n\nDescription: Verify that the Implementation Under Test (IUT) can send Discover Primary "
      "Services UUID = '0000-A00C-0000-0000-0123-4567-89AB-CDEF'O."),
     ["0000-A00C-0000-0000-0123-4567-89AB-CDEF",
      "0000-A00C-0000-0000-0123-4567-89AB-CDEF"]),

    # project_name: GATT
    # wid: 52
    # test_case_name: TC_GAR_CL_BV_04_C

    # description: Please confirm IUT Handle='cd'O characteristic
    # value='11223344556677889900123456789012345678901234567890123456789011223344556677889900112233'O
    # in random selected adopted database. Click Yes if it matches the IUT,
    # othwise click No.

    # Description: Verify that the Implementation Under Test (IUT) can send Read long characteristic to PTS
    # random select adopted database.
    # style: MMI_Style_Yes_No1 0x11044

    (("Please confirm IUT Handle='cd'O characteristic "
      "value='11223344556677889900123456789012345678901234567890123456789011223344556677889900112233'O "
      "in random selected adopted database. Click Yes if it matches the IUT, othwise click No.\n\n"
      "Description: Verify that the Implementation Under Test (IUT) can send Read long characteristic "
      "to PTS random select adopted database."),
     ["cd", "11223344556677889900123456789012345678901234567890123456789011223344556677889900112233"]),

    # this one is more of a verfication, than descripion that needs to be parsed
    # by MmiParser

    # project_name: GATT
    # wid: 24
    # test_case_name: TC_GAD_CL_BV_03_C
    # description: Please confirm IUT receive include services:
    # Attribute Handle = 0x0002 Included Service Attribute handle = 0x0080,End Group Handle = 0x0085,
    # Service UUID = 0x3C3A

    # Attribute Handle = 0x0021 Included Service Attribute handle = 0x0001,End Group Handle = 0x0006,
    # Service UUID = 0x2805

    # Attribute Handle = 0x0091 Included Service Attribute handle = 0x0001,End Group Handle = 0x0006,
    # Service UUID = 0x2805

    # Click Yes if IUT receive it, otherwise click No.

    # Description: Verify that the Implementation Under Test (IUT) can send Discover all include services in database.
    # style: MMI_Style_Yes_No1 0x11044

    (("Please confirm IUT receive include services:\nAttribute Handle = 0x0002 Included Service Attribute handle "
      "= 0x0080,End Group Handle = 0x0085,Service UUID = 0x3C3A\n\nAttribute Handle = 0x0021 Included Service "
      "Attribute handle = 0x0001,End Group Handle = 0x0006,Service UUID = 0x2805\n\nAttribute Handle = 0x0091 "
      "Included Service Attribute handle = 0x0001,End Group Handle = 0x0006,Service UUID = 0x2805\n\n"
      "Click Yes if IUT receive it, otherwise click No.\n\n"
      "Description: Verify that the Implementation Under Test (IUT) "
      "can send Discover all include services in database."),
     ["0x0002", "0x0080", "0x0085", "0x3C3A",
      "0x0021", "0x0001", "0x0006", "0x2805",
      "0x0091", "0x0001", "0x0006", "0x2805"])
]

if __name__ == '__main__':
    print("Descriptions:")
    for item in descriptions:
        print(item, "\n")

    print("\nInitiating parsing")

    MMI = MmiParser()

    for item in descriptions:
        description, args = item
        print("\nParsing: %r\nExpecting: %r" % (description, args))
        MMI.parse_description(description)
        print("Got:", 5 * " ", MMI.args)
        assert args == MMI.args, \
            "Error parsing description found=%r, expected=%r" % (MMI.args, args)
        print("OK")
