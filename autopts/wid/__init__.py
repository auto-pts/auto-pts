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
from .aics import aics_wid_hdl
from .ascs import ascs_wid_hdl
from .bap import bap_wid_hdl
from .bass import bass_wid_hdl
from .ccp import ccp_wid_hdl
from .csip import csip_wid_hdl
from .csis import csis_wid_hdl
from .gmcs import gmcs_wid_hdl
from .gtbs import gtbs_wid_hdl
from .has import has_wid_hdl
from .ias import ias_wid_hdl
from .l2cap import l2cap_wid_hdl
from .mcp import mcp_wid_hdl
from .mesh import (
                   mesh_wid_hdl,
                   mesh_wid_hdl_rpr_2ptses,
                   mesh_wid_hdl_rpr_persistent_storage,
                   mesh_wid_hdl_rpr_persistent_storage_alt,
)
from .micp import micp_wid_hdl
from .mics import mics_wid_hdl
from .mmdl import mmdl_wid_hdl
from .ots import ots_wid_hdl
from .pacs import pacs_wid_hdl
from .pbp import pbp_wid_hdl
from .tbs import tbs_wid_hdl
from .tmap import tmap_wid_hdl
from .vcp import vcp_wid_hdl
from .vcs import vcs_wid_hdl
from .vocs import vocs_wid_hdl
from .wid import generic_wid_hdl

__all__ = [
    "aics_wid_hdl",
    "ascs_wid_hdl",
    "bap_wid_hdl",
    "bass_wid_hdl",
    "ccp_wid_hdl",
    "csip_wid_hdl",
    "csis_wid_hdl",
    "gmcs_wid_hdl",
    "gtbs_wid_hdl",
    "has_wid_hdl",
    "ias_wid_hdl",
    "l2cap_wid_hdl",
    "mcp_wid_hdl",
    "mesh_wid_hdl",
    "mesh_wid_hdl_rpr_2ptses",
    "mesh_wid_hdl_rpr_persistent_storage",
    "mesh_wid_hdl_rpr_persistent_storage_alt",
    "micp_wid_hdl",
    "mics_wid_hdl",
    "mmdl_wid_hdl",
    "ots_wid_hdl",
    "pacs_wid_hdl",
    "pbp_wid_hdl",
    "tbs_wid_hdl",
    "tmap_wid_hdl",
    "vcp_wid_hdl",
    "vcs_wid_hdl",
    "vocs_wid_hdl",
    "generic_wid_hdl",
]


# GENERATOR append 1
