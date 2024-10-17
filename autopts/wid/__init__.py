#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2019, Intel Corporation.
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
from typing import NamedTuple

from .wid import generic_wid_hdl
from .l2cap import l2cap_wid_hdl
from .mesh import mesh_wid_hdl, mesh_wid_hdl_rpr_2ptses
from .mesh import mesh_wid_hdl, mesh_wid_hdl_rpr_2ptses,\
    mesh_wid_hdl_rpr_persistent_storage,\
    mesh_wid_hdl_rpr_persistent_storage_alt
from .mmdl import mmdl_wid_hdl
from .vcs import vcs_wid_hdl
from .ias import ias_wid_hdl
from .vocs import vocs_wid_hdl
from .aics import aics_wid_hdl
from .pacs import pacs_wid_hdl
from .ascs import ascs_wid_hdl
from .bap import bap_wid_hdl
from .has import has_wid_hdl
from .csis import csis_wid_hdl
from .csip import csip_wid_hdl
from .micp import micp_wid_hdl
from .mics import mics_wid_hdl
from .ccp import ccp_wid_hdl
from .vcp import vcp_wid_hdl
from .mcp import mcp_wid_hdl
from .bass import bass_wid_hdl
from .gmcs import gmcs_wid_hdl
from .csip import csip_wid_hdl
from .tbs import tbs_wid_hdl
from .gtbs import gtbs_wid_hdl
from .tmap import tmap_wid_hdl
from .ots import ots_wid_hdl
from .bas import bas_wid_hdl
# GENERATOR append 1
