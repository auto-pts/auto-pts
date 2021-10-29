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

"""Wrapper around btp messages. The functions are added as needed."""

from autopts.ptsprojects.stack import get_stack


def var_store_get_passkey(description):
    pk = get_stack().gap.get_passkey()
    if pk:
        return str(pk).zfill(6)
    return '000000'


def var_store_get_wrong_passkey(description):
    passkey = get_stack().gap.get_passkey()

    # Passkey is in range 0-999999
    passkey = int(passkey)
    if passkey > 0:
        return str(passkey - 1).zfill(6)
    return str(passkey + 1).zfill(6)
