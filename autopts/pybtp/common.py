from . import defs

supported_svcs_cmds = {
    "CORE": {
        "service": 1 << defs.BTP_SERVICE_ID_CORE,
        "supported_commands": defs.BTP_CORE_CMD_READ_SUPPORTED_COMMANDS
    },
    "GAP": {
        "service": 1 << defs.BTP_SERVICE_ID_GAP,
        "supported_commands": defs.BTP_GAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "GATT": {
        "service": 1 << defs.BTP_SERVICE_ID_GATT,
        "supported_commands": defs.BTP_GATT_CMD_READ_SUPPORTED_COMMANDS
    },
    "L2CAP": {
        "service": 1 << defs.BTP_SERVICE_ID_L2CAP,
        "supported_commands": defs.BTP_L2CAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "MESH": {
        "service": 1 << defs.BTP_SERVICE_ID_MESH,
        "supported_commands": defs.BTP_MESH_CMD_READ_SUPPORTED_COMMANDS
    },
    "MESH_MMDL": {
        "service": 1 << defs.BTP_SERVICE_ID_MMDL,
        "supported_commands": defs.BTP_MMDL_CMD_READ_SUPPORTED_COMMANDS
    },
    "GATT_CL": {
        "service": 1 << defs.BTP_SERVICE_ID_GATTC,
        "supported_commands": defs.BTP_GATTC_CMD_READ_SUPPORTED_COMMANDS
    },
    "VCS": {
        "service": 1 << defs.BTP_SERVICE_ID_VCS,
        "supported_commands": defs.BTP_VCS_CMD_READ_SUPPORTED_COMMANDS
    },
    "IAS": {
        "service": 1 << defs.BTP_SERVICE_ID_IAS
    },
    "AICS": {
        "service": 1 << defs.BTP_SERVICE_ID_AICS,
        "supported_commands": defs.BTP_AICS_CMD_READ_SUPPORTED_COMMANDS
    },
    "VOCS": {
        "service": 1 << defs.BTP_SERVICE_ID_VOCS,
        "supported_commands": defs.BTP_VOCS_CMD_READ_SUPPORTED_COMMANDS
    },
    "PACS": {
        "service": 1 << defs.BTP_SERVICE_ID_PACS,
        "supported_commands": defs.BTP_PACS_CMD_READ_SUPPORTED_COMMANDS
    },
    "ASCS": {
        "service": 1 << defs.BTP_SERVICE_ID_ASCS,
        "supported_commands": defs.BTP_ASCS_CMD_READ_SUPPORTED_COMMANDS
    },
    "BAP": {
        "service": 1 << defs.BTP_SERVICE_ID_BAP,
        "supported_commands": defs.BTP_BAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "MICP": {
        "service": 1 << defs.BTP_SERVICE_ID_MICP,
        "supported_commands": defs.BTP_MICP_CMD_READ_SUPPORTED_COMMANDS
    },
    "HAS": {
        "service": 1 << defs.BTP_SERVICE_ID_HAS,
        "supported_commands": defs.BTP_HAS_CMD_READ_SUPPORTED_COMMANDS
    },
    "CSIS": {
        "service": 1 << defs.BTP_SERVICE_ID_CSIS,
        "supported_commands": defs.BTP_CSIS_CMD_READ_SUPPORTED_COMMANDS
    },
    "MICS": {
        "service": 1 << defs.BTP_SERVICE_ID_MICS,
        "supported_commands": defs.BTP_MICS_CMD_READ_SUPPORTED_COMMANDS
    },
    "CCP": {
        "service": 1 << defs.BTP_SERVICE_ID_CCP,
        "supported_commands": defs.BTP_CCP_CMD_READ_SUPPORTED_COMMANDS
    },
    "VCP": {
        "service": 1 << defs.BTP_SERVICE_ID_VCP,
        "supported_commands": defs.BTP_VCP_CMD_READ_SUPPORTED_COMMANDS
    },
    "MCP": {
        "service": 1 << defs.BTP_SERVICE_ID_MCP,
        "supported_commands": defs.BTP_MCP_CMD_READ_SUPPORTED_COMMANDS
    },
    "GMCS": {
        "service": 1 << defs.BTP_SERVICE_ID_GMCS,
        "supported_commands": defs.BTP_GMCS_CMD_READ_SUPPORTED_COMMANDS
    },
    "HAP": {
        "service": 1 << defs.BTP_SERVICE_ID_HAP,
        "supported_commands": defs.BTP_HAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "CAP": {
        "service": 1 << defs.BTP_SERVICE_ID_CAP,
        "supported_commands": defs.BTP_CAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "CSIP": {
        "service": 1 << defs.BTP_SERVICE_ID_CSIP,
        "supported_commands": defs.BTP_CSIP_CMD_READ_SUPPORTED_COMMANDS
    },
    "TBS": {
        "service": 1 << defs.BTP_SERVICE_ID_TBS,
        "supported_commands": defs.BTP_TBS_CMD_READ_SUPPORTED_COMMANDS
    },
    "TMAP": {
        "service": 1 << defs.BTP_SERVICE_ID_TMAP,
        "supported_commands": defs.BTP_TMAP_CMD_READ_SUPPORTED_COMMANDS
    },
    "OTS": {
        "service": 1 << defs.BTP_SERVICE_ID_OTS,
        "supported_commands": defs.BTP_OTS_CMD_READ_SUPPORTED_COMMANDS
    },
    "PBP": {
        "service": 1 << defs.BTP_SERVICE_ID_PBP,
        "supported_commands": defs.BTP_PBP_CMD_READ_SUPPORTED_COMMANDS
    },
    "CAS": {
        "supported_commands": defs.BTP_CAS_CMD_READ_SUPPORTED_COMMANDS
    },
    "BASS": {
        "supported_commands": defs.BTP_BASS_CMD_READ_SUPPORTED_COMMANDS
    }
}

reg_unreg_service = {
    "gap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GAP),
    "gatt_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "gatt_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATT),
    "l2cap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                  defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "l2cap_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                    defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_L2CAP),
    "mesh_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "mesh_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MESH),
    "mmdl_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MMDL),
    "mmdl_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                   defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MMDL),
    "gatt_cl_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                    defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATTC),
    "gatt_cl_unreg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_UNREGISTER_SERVICE,
                      defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GATTC),
    "vcs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VCS),
    "vocs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VOCS),
    "aics_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_AICS),
    "ias_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_IAS),
    "pacs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_PACS),
    "ascs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_ASCS),
    "bap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_BAP),
    "has_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_HAS),
    "csis_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CSIS),
    "micp_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MICP),
    "mics_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MICS),
    "ccp_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CCP),
    "vcp_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_VCP),
    "cas_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CAS),
    "mcp_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_MCP),
    "gmcs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_GMCS),
    "hap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_HAP),
    "cap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CAP),
    "csip_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_CSIP),
    "tbs_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_TBS),
    "tmap_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                 defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_TMAP),
    "ots_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_OTS),
    "pbp_reg": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_PBP),
    # GENERATOR append 4
    "read_supp_cmds": (defs.BTP_SERVICE_ID_CORE,
                       defs.BTP_CORE_CMD_READ_SUPPORTED_COMMANDS,
                       defs.BTP_INDEX_NONE, ""),
    "read_supp_svcs": (defs.BTP_SERVICE_ID_CORE,
                       defs.BTP_CORE_CMD_READ_SUPPORTED_SERVICES,
                       defs.BTP_INDEX_NONE, ""),
    "log_message": (defs.BTP_SERVICE_ID_CORE, defs.BTP_CORE_CMD_LOG_MESSAGE,
                    defs.BTP_INDEX_NONE),
}
