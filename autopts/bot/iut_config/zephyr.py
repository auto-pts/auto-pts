#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
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

# Stable Zephyr IUT config

iut_config = {
    "prj.conf": {},  # Default config file name

    "enforce_mitm.conf": {
        "overlay": {
            'CONFIG_BT_SMP_ENFORCE_MITM': 'y',
        },
        "test_cases": [
            'SM/PER/PKE/BV-05-C',
            'SM/PER/SCPK/BI-04-C',
            'SM/CEN/OOB/BI-01-C',
            'SM/PER/OOB/BV-04-C',
            'SM/PER/OOB/BI-02-C',
        ]
    },

    "sc_m1l2.conf": {
        "overlay": {
            'CONFIG_BT_PRIVACY': 'y',
            'CONFIG_BT_SMP_ENFORCE_MITM': 'n',
        },
        "test_cases": [
            'SM/CEN/KDU/BI-02-C',
            'SM/CEN/KDU/BI-03-C',
            'SM/PER/KDU/BI-02-C',
            'SM/PER/KDU/BI-03-C',
            'GAP/SEC/SEM/BV-37-C',
            'GAP/SEC/SEM/BV-39-C',
            'GAP/SEC/SEM/BV-41-C',
            'GAP/SEC/SEM/BV-43-C',
        ]
    },

    "sc_m1l3.conf": {
        "overlay": {
            'CONFIG_BT_PRIVACY': 'y',
            'CONFIG_BT_SMP_ENFORCE_MITM': 'y',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-38-C',
            'GAP/SEC/SEM/BV-40-C',
            'GAP/SEC/SEM/BV-42-C',
            'GAP/SEC/SEM/BV-44-C',
        ]
    },

    "sec_m1l4.conf": {
        "overlay": {
            'CONFIG_BT_PRIVACY': 'y',
            'CONFIG_BT_SMP_ENFORCE_MITM': 'y',
            'CONFIG_BT_SMP_SC_ONLY': 'y',
            'CONFIG_BT_SMP_SC_PAIR_ONLY': 'y',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-21-C',
            'GAP/SEC/SEM/BV-22-C',
            'GAP/SEC/SEM/BV-23-C',
            'GAP/SEC/SEM/BV-24-C',
            'GAP/SEC/SEM/BV-26-C',
            'GAP/SEC/SEM/BV-27-C',
            'GAP/SEC/SEM/BV-28-C',
            'GAP/SEC/SEM/BV-58-C',
            'GAP/SEC/SEM/BV-61-C',
            'GAP/SEC/SEM/BV-29-C',
            'GAP/SEC/SEM/BI-09-C',
            'GAP/SEC/SEM/BI-10-C',
            'GAP/SEC/SEM/BI-20-C',
            'GAP/SEC/SEM/BI-21-C',
            'GAP/SEC/SEM/BI-22-C',
            'GAP/SEC/SEM/BI-23-C',
        ]
    },

    "privacy.conf": {
        "overlay": {
            'CONFIG_BT_PRIVACY': 'y',
            'CONFIG_BT_RPA_TIMEOUT': '30',
        },
        "test_cases": [
            'GAP/PRIV/CONN/BV-10-C',
            'GAP/PRIV/CONN/BV-11-C',
            'GAP/CONN/ACEP/BV-03-C',
            'GAP/CONN/ACEP/BV-04-C',
            'GAP/CONN/DCEP/BV-05-C',
            'GAP/CONN/DCEP/BV-06-C',
            'GAP/CONN/DCON/BV-04-C',
            'GAP/CONN/DCON/BV-05-C',
            'GAP/CONN/GCEP/BV-05-C',
            'GAP/CONN/GCEP/BV-06-C',
            'GAP/CONN/PRDA/BV-02-C',
            'GAP/CONN/NCON/BV-02-C',
            'GAP/CONN/UCON/BV-06-C',
            'GAP/BROB/BCST/BV-03-C',
            'GAP/BROB/BCST/BV-04-C',
            'GAP/BROB/BCST/BV-05-C',
            'GAP/BROB/OBSV/BV-06-C',
            'GAP/DISC/RPA/BV-01-C',
            'GAP/GAT/BV-18-C',
            'SM/CEN/KDU/BV-05-C',
            'SM/CEN/KDU/BV-10-C',
            'SM/CEN/KDU/BV-11-C',
            'SM/PER/KDU/BV-02-C',
            'SM/PER/KDU/BV-08-C',
        ]
    },

    "csip_privacy.conf": {
        "pre_overlay": ["overlay-le-audio.conf", "privacy.conf"],
        "test_cases": [
            'CSIP'
        ]
    },

    "eatt_two_channels.conf": {
        "overlay": {
            'CONFIG_BT_EATT_MAX': '2',
        },
        "test_cases": [
            'L2CAP/TIM/BV-03-C',
        ]
    },

    "ots_no_dir_list.conf": {
        "overlay": {
            'CONFIG_BT_OTS_DIR_LIST_OBJ': 'n',
        },
        "test_cases": [
            'OTS/SR/OLE/BI-03-C',
        ]
    },

    "overlay-le-audio.conf": {
        "overlay": {
            # The overlay file exists in zephyr repo. Leave this empty.
        },
        "test_cases": [
            'AICS', 'ASCS', 'BAP', 'BASS', 'CAP', 'CAS', 'CCP', 'CSIP', 'CSIS', 'GMAP',
            'GMCS', 'GTBS', 'HAP', 'HAS', 'IAS', 'MCP', 'MCS', 'MICP', 'MICS', 'PACS',
            'PBP', 'TBS', 'TMAP', 'VCP', 'VCS', 'VOCS',
        ]
    },

    "overlay-mesh.conf": {
        "overlay": {
            # The overlay file exists in zephyr repo. Leave this empty.
        },
        "test_cases": [
            'MESH'
        ]
    },

    "mesh_rpr_persistent_storage.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_SECURE_STORAGE': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_SETTINGS_NVS': 'y',
            'CONFIG_BT_MESH_SETTINGS_WORKQ_STACK_SIZE': '1200'
        },
        "test_cases": [
            'MESH/SR/RPR/PDU/BV-02-C',
            'MESH/SR/RPR/PDU/BV-03-C',
            'MESH/SR/RPR/PDU/BV-04-C',
            'MESH/SR/RPR/LNK/BV-25-C',
            'MESH/SR/RPR/PDU/BI-01-C',
            'MESH/SR/RPR/PDU/BI-02-C',
            'MESH/SR/RPR/PDU/BI-03-C',
            'MESH/NODE/CFG/COMP/BV-01-C'
            'MESH/SR/RPR/LNK/BI-05-C',
            'MESH/NODE/TNPT/BV-13-C',
        ]
    },

    "mesh_proxy_sol.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_MESH_PROXY_CLIENT': 'y',
            'CONFIG_BT_MESH_PROXY_SOLICITATION': 'y',
            'CONFIG_BT_MESH_OD_PRIV_PROXY_CLI': 'y',
            'CONFIG_BT_MESH_OD_PRIV_PROXY_SRV': 'y',
            'CONFIG_BT_MESH_SOL_PDU_RPL_CLI': 'y',
        },
        "test_cases": [
            'MESH/SR/MPXS/BV-12-C',
            'MESH/SR/MPXS/BV-13-C',
            'MESH/SR/ODP/BV-01-C',
            'MESH/CL/ODP/BV-01-C',
            'MESH/SR/SRPL/BV-01-C',
            'MESH/CL/SRPL/BV-01-C',
            'MESH/CL/MPXS/BV-09-C',
        ]
    },

    "mesh_dfd_dfu.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_SECURE_STORAGE': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_SETTINGS_WORKQ_STACK_SIZE': '1200',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000',
        },
        "test_cases": [
            'DFUM/SR/FD/BV-48-C',
            'DFUM/SR/FD/BV-59-C'
        ]
    },

    "mesh_dfd_srv.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_SECURE_STORAGE': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_SETTINGS_WORKQ_STACK_SIZE': '1200',
            'CONFIG_BT_MESH_DFU_SRV': 'n',
            'CONFIG_BT_MESH_DFD_SRV_OOB_UPLOAD': 'y',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MIN': '256',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MAX': '256'
        },
        "test_cases": [
            'DFU/SR-CL/GEN/BV-01-C',
            'DFUM/CL/FU',
            'DFUM/SR/FD',
            'MBTM/SR/BT',
        ]
    },

    "mesh_dfu_srv.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_SECURE_STORAGE': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_SETTINGS_WORKQ_STACK_SIZE': '1200',
            'CONFIG_BT_MESH_DFD_SRV': 'n',
            'CONFIG_BT_MESH_DFD_SRV_OOB_UPLOAD': 'y',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MIN': '256',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MAX': '256'
        },
        "test_cases": [
            'DFUM/SR/FU'
        ]
    },

    "mesh_blob_cli.conf": {
        "pre_overlay": "overlay-mesh.conf",
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_SECURE_STORAGE': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_SETTINGS_WORKQ_STACK_SIZE': '1200',
            'CONFIG_BT_MESH_DFD_SRV': 'n',
            'CONFIG_BT_MESH_DFU_SRV': 'n',
            'CONFIG_BT_MESH_BLOB_SRV': 'n',
            'CONFIG_BT_MESH_DFD_SRV_OOB_UPLOAD': 'y',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MIN': '256',
            'CONFIG_BT_MESH_BLOB_BLOCK_SIZE_MAX': '256'
        },
        "test_cases": [
            'MBTM/CL/BT'
        ]
    },

    "br_sec_sc_only.conf": {
        "overlay": {
            'CONFIG_BT_CLASSIC': 'y',
            'CONFIG_BT_CENTRAL': 'y',
            'CONFIG_BT_PERIPHERAL': 'y',
            'CONFIG_BT_SMP': 'y',
            'CONFIG_BT_L2CAP_DYNAMIC_CHANNEL': 'y',
            'CONFIG_BT_PAGE_TIMEOUT': '0xFFFF',
            'CONFIG_BT_SMP_SC_ONLY': 'y',
            'CONFIG_BT_SMP_SC_PAIR_ONLY': 'y',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-11-C',
            'GAP/SEC/SEM/BV-12-C',
            'GAP/SEC/SEM/BV-13-C',
            'GAP/SEC/SEM/BV-47-C',
            'GAP/SEC/SEM/BV-16-C',
            'GAP/SEC/SEM/BV-17-C',
            'GAP/SEC/SEM/BV-18-C',
            'GAP/SEC/SEM/BV-54-C',
            'GAP/SEC/SEM/BI-32-C',
            'GAP/SEC/SEM/BV-25-C',
            'GAP/SEC/SEM/BV-30-C',
        ]
    },

    "br_sec_ks_128.conf": {
        "overlay": {
            'CONFIG_BT_CLASSIC': 'y',
            'CONFIG_BT_CENTRAL': 'y',
            'CONFIG_BT_PERIPHERAL': 'y',
            'CONFIG_BT_SMP': 'y',
            'CONFIG_BT_L2CAP_DYNAMIC_CHANNEL': 'y',
            'CONFIG_BT_PAGE_TIMEOUT': '0xFFFF',
            'CONFIG_BT_SMP_MIN_ENC_KEY_SIZE': '16',
        },
        "test_cases": [
            'GAP/SEC/SEM/BI-14-C',
            'GAP/SEC/SEM/BI-15-C',
            'GAP/SEC/SEM/BI-16-C',
            'GAP/SEC/SEM/BI-04-C',
            'GAP/SEC/SEM/BI-17-C',
            'GAP/SEC/SEM/BI-18-C',
            'GAP/SEC/SEM/BI-19-C',
            'GAP/SEC/SEM/BI-08-C',
        ]
    },

    "br_l2cap_ret_fc.conf": {
        "overlay": {
            'CONFIG_BT_CLASSIC': 'y',
            'CONFIG_BT_CENTRAL': 'y',
            'CONFIG_BT_PERIPHERAL': 'y',
            'CONFIG_BT_SMP': 'y',
            'CONFIG_BT_L2CAP_DYNAMIC_CHANNEL': 'y',
            'CONFIG_BT_PAGE_TIMEOUT': '0xFFFF',
            'CONFIG_BT_L2CAP_RET': 'y',
            'CONFIG_BT_L2CAP_FC': 'y',
            'CONFIG_BT_L2CAP_ENH_RET': 'n',
            'CONFIG_BT_L2CAP_STREAM': 'n',
            'CONFIG_BT_L2CAP_FCS': 'n',
            'CONFIG_BT_L2CAP_EXT_WIN_SIZE': 'n',
            'CONFIG_BT_L2CAP_MAX_WINDOW_SIZE': '5',
        },
        "test_cases": [
            'L2CAP/COS/CFD/BV-10-C',
            'L2CAP/COS/RTX/BV-01-C',
            'L2CAP/COS/RTX/BV-02-C',
            'L2CAP/COS/RTX/BV-03-C',
            'L2CAP/COS/CED/BV-10-C',
            'L2CAP/COS/FLC/BV-01-C',
            'L2CAP/COS/FLC/BV-02-C',
            'L2CAP/COS/FLC/BV-03-C',
            'L2CAP/COS/FLC/BV-04-C',
            'L2CAP/COS/CFD/BV-13-C',
        ]
    },

    "br_l2cap_cls.conf": {
        "overlay": {
            'CONFIG_BT_CLASSIC': 'y',
            'CONFIG_BT_CENTRAL': 'y',
            'CONFIG_BT_PERIPHERAL': 'y',
            'CONFIG_BT_SMP': 'y',
            'CONFIG_BT_L2CAP_DYNAMIC_CHANNEL': 'y',
            'CONFIG_BT_PAGE_TIMEOUT': '0xFFFF',
            'CONFIG_BT_L2CAP_CLS': 'y',
        },
        "test_cases": [
            'L2CAP/CLS/CLR/BV-01-C',
            'L2CAP/CLS/UCD/BV-01-C',
            'L2CAP/CLS/UCD/BV-02-C',
            'L2CAP/CLS/UCD/BV-03-C',
            'L2CAP/CLS/CID/BV-01-C',
        ]
    },

    "gap_le_sec_mode3_bis.conf": {
        "overlay": {
            'CONFIG_BT_ISO_BROADCASTER': 'y',
            'CONFIG_BT_ISO_SYNC_RECEIVER': 'y',
            'CONFIG_BT_ISO_CENTRAL': 'y',
            'CONFIG_BT_ISO_PERIPHERAL': 'y',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-31-C',
            'GAP/SEC/SEM/BV-32-C',
            'GAP/SEC/SEM/BV-34-C',
            'GAP/SEC/SEM/BV-35-C',
        ]
    },
}

retry_config = {
}
