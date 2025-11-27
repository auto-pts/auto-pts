#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
# Copyright (c) 2024, Codecoup.
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

from autopts.ptsprojects.stack.layers.a2dp import A2DP
from autopts.ptsprojects.stack.layers.aics import AICS
from autopts.ptsprojects.stack.layers.ascs import ASCS
from autopts.ptsprojects.stack.layers.bap import BAP
from autopts.ptsprojects.stack.layers.cap import CAP
from autopts.ptsprojects.stack.layers.ccp import CCP
from autopts.ptsprojects.stack.layers.core import CORE
from autopts.ptsprojects.stack.layers.csip import CSIP
from autopts.ptsprojects.stack.layers.csis import CSIS
from autopts.ptsprojects.stack.layers.gap import Gap
from autopts.ptsprojects.stack.layers.gatt import Gatt
from autopts.ptsprojects.stack.layers.gattcl import GattCl
from autopts.ptsprojects.stack.layers.gmcs import GMCS
from autopts.ptsprojects.stack.layers.gtbs import GTBS
from autopts.ptsprojects.stack.layers.hap import HAP
from autopts.ptsprojects.stack.layers.ias import IAS
from autopts.ptsprojects.stack.layers.l2cap import L2cap
from autopts.ptsprojects.stack.layers.mcp import MCP
from autopts.ptsprojects.stack.layers.mesh import Mesh
from autopts.ptsprojects.stack.layers.micp import MICP
from autopts.ptsprojects.stack.layers.mics import MICS
from autopts.ptsprojects.stack.layers.ots import OTS
from autopts.ptsprojects.stack.layers.pacs import PACS
from autopts.ptsprojects.stack.layers.pbp import PBP
from autopts.ptsprojects.stack.layers.sdp import SDP
from autopts.ptsprojects.stack.layers.tbs import TBS
from autopts.ptsprojects.stack.layers.tmap import TMAP
from autopts.ptsprojects.stack.layers.vcp import VCP
from autopts.ptsprojects.stack.layers.vcs import VCS
from autopts.ptsprojects.stack.layers.vocs import VOCS

# GENERATOR append 1
from autopts.ptsprojects.stack.synch import Synch
from autopts.pybtp import common

STACK = None
log = logging.debug


class Stack:
    def __init__(self):
        self.supported_svcs = 0
        self.supported_cmds = 0
        self.synch = None

        self.gap = None
        self.mesh = None
        self.l2cap = None
        self.gatt = None
        self.gatt_cl = None
        self.vcs = None
        self.ias = None
        self.vocs = None
        self.aics = None
        self.pacs = None
        self.ascs = None
        self.bap = None
        self.core = None
        self.micp = None
        self.mics = None
        self.ccp = None
        self.vcp = None
        self.mcp = None
        self.gmcs = None
        self.hap = None
        self.cap = None
        self.csip = None
        self.tbs = None
        self.gtbs = None
        self.tmap = None
        self.ots = None
        self.pbp = None
        self.sdp = None
        self.csis = None
        self.a2dp = None
        # GENERATOR append 2
        self.supported_svcs_cmds = common.supported_svcs_cmds

    def is_svc_supported(self, svc):
        svc_value = self.supported_svcs_cmds.get(svc, {}).get("service", 0)
        return (self.supported_svcs & svc_value) > 0

    def gap_init(self, name=None, manufacturer_data=None, appearance=None,
                 svc_data=None, flags=None, svcs=None, uri=None, periodic_data=None,
                 le_supp_feat=None):
        self.gap = Gap(name, manufacturer_data, appearance, svc_data, flags,
                       svcs, uri, periodic_data, le_supp_feat)

    def mesh_init(self, uuid, uuid_lt2=None):
        if self.mesh:
            return

        self.mesh = Mesh(uuid, uuid_lt2)

    def l2cap_init(self, psm, initial_mtu):
        self.l2cap = L2cap(psm, initial_mtu)

    def gatt_init(self):
        self.gatt = Gatt()
        self.gatt_cl = self.gatt

    def vcs_init(self):
        self.vcs = VCS()

    def aics_init(self):
        self.aics = AICS()

    def vocs_init(self):
        self.vocs = VOCS()

    def ias_init(self):
        self.ias = IAS()

    def pacs_init(self):
        self.pacs = PACS()

    def ascs_init(self):
        self.ascs = ASCS()

    def bap_init(self):
        self.bap = BAP()

    def ccp_init(self):
        self.ccp = CCP()

    def core_init(self):
        if self.core:
            self.core.cleanup()
        else:
            self.core = CORE()

    def micp_init(self):
        self.micp = MICP()

    def mics_init(self):
        self.mics = MICS()

    def mcp_init(self):
        self.mcp = MCP()

    def gmcs_init(self):
        self.gmcs = GMCS()

    def gatt_cl_init(self):
        self.gatt_cl = GattCl()

    def synch_init(self):
        if not self.synch:
            self.synch = Synch()
        else:
            self.synch.reinit()

    def vcp_init(self):
        self.vcp = VCP()

    def hap_init(self):
        self.hap = HAP()

    def cap_init(self):
        self.cap = CAP()

    def csip_init(self):
        self.csip = CSIP()

    def tbs_init(self):
        self.tbs = TBS()

    def gtbs_init(self):
        self.gtbs = GTBS()

    def tmap_init(self):
        self.tmap = TMAP()

    def ots_init(self):
        self.ots = OTS()

    def pbp_init(self):
        self.pbp = PBP()

    def sdp_init(self):
        self.sdp = SDP()

    def csis_init(self, size):
        self.csis = CSIS(size)

    def a2dp_init(self):
        self.a2dp = A2DP()

    # GENERATOR append 3

    def cleanup(self):
        if self.gap:
            self.gap = Gap(self.gap.name, self.gap.manufacturer_data, None, None, None, None, None)

        if self.mesh:
            self.mesh = Mesh(self.mesh.get_dev_uuid(), self.mesh.get_dev_uuid_lt2())

        if self.vcs:
            self.vcs_init()

        if self.aics:
            self.aics_init()

        if self.vocs:
            self.vocs_init()

        if self.ias:
            self.ias_init()

        if self.pacs:
            self.pacs_init()

        if self.ascs:
            self.ascs_init()

        if self.bap:
            self.bap_init()

        if self.micp:
            self.micp_init()

        if self.ccp:
            self.ccp_init()

        if self.mics:
            self.mics_init()

        if self.gmcs:
            self.gmcs_init()

        if self.gatt:
            self.gatt_init()

        if self.gatt_cl:
            self.gatt_cl_init()

        if self.synch:
            self.synch_init()

        if self.core:
            self.core_init()

        if self.vcp:
            self.vcp_init()

        if self.mcp:
            self.mcp_init()

        if self.hap:
            self.hap_init()

        if self.cap:
            self.cap_init()

        if self.csip:
            self.csip_init()

        if self.tbs:
            self.tbs_init()

        if self.gtbs:
            self.gtbs_init()

        if self.tmap:
            self.tmap_init()

        if self.ots:
            self.ots_init()

        if self.pbp:
            self.pbp_init()

        if self.sdp:
            self.sdp_init()

        if self.csis:
            self.csis_init(self.csis.set_size)

        if self.a2dp:
            self.a2dp_init()

        # GENERATOR append 4


def init_stack():
    global STACK

    STACK = Stack()
    STACK.synch_init()


def cleanup_stack():
    global STACK

    STACK = None


def get_stack():
    return STACK
