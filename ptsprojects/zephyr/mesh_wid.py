#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Codecoup.
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

log = logging.debug

def mesh_wid_hdl(wid, description):
    log("%s, %r, %r", mesh_wid_hdl.__name__, wid, description)

    try:
        return handler[wid](description)
    except KeyError:
        log("wid nb: %d, not implemented!", wid)


# wid handlers section begin
def hdl_wid_12(desc):
    pass

handler = {
    12 : hdl_wid_12,
}
