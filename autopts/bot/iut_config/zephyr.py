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
            'GAP/BROB/OBSV/BV-06-C',
            'GAP/DISC/RPA/BV-01-C',
            'SM/CEN/KDU/BV-05-C',
            'SM/CEN/KDU/BV-10-C',
            'SM/CEN/KDU/BV-11-C',
            'SM/PER/KDU/BV-02-C',
            'SM/PER/KDU/BV-08-C',
        ]
    },

    "privacy_default_timeout.conf": {
        "overlay": {
            'CONFIG_BT_PRIVACY': 'y',
        },
        "test_cases": [
            'MESH/NODE/IVU/BV-(XY+0)-C',
            'MESH/NODE/IVU/BV-(XY+1)-C',
            'MESH/NODE/IVU/BV-(XY+0)-C',
            'MESH/NODE/IVU/BV-(XY+1)',
            'MESH/NODE/IVU/BV-(XY+2)',
            'MESH/NODE/IVU/BV-(XY+3)',
            'MESH/NODE/IVU/BV-(XY+4)',
            'MESH/NODE/IVU/BI-(XY+0)-C',
            'MESH/NODE/IVU/BI-(XY+1)-C',
            'MESH/NODE/IVU/BI-(XY+2)-C',
            'MESH/NODE/IVU/BI-(XY+3)-C',
            'MESH/NODE/IVU/BI-(XY+4)-C',
            'MESH/NODE/KR/BV-(XY+0)-C',
            'MESH/NODE/KR/BV-(XY+1)-C',
            'MESH/NODE/KR/BI-(XY+0)-C',
            'MESH/CFGCL/KR/BV-(XY+0)-C',
            'MESH/CFGCL/KR/BV-(XY+1)-C'
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

    "overlay-le-audio.conf": {
        "overlay": {
            # The overlay file exists in zephyr repo. Leave this empty.
        },
        "test_cases": [
            'VOCS', 'VCS', 'AICS', 'IAS', 'PACS', 'ASCS', 'BAP', 'HAS', 'CSIS', 'MICP',
            'MICS'
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

    "mesh_rpr.conf": {
        "overlay": {
            'CONFIG_BT_MESH_ECDH_P256_HMAC_SHA256_AES_CCM': 'n',
            'CONFIG_BT_MESH_LARGE_COMP_DATA_SRV': 'n'
        },
        "test_cases": [
            'MESH/SR/RPR/PDU/BV-02-C',
            'MESH/SR/RPR/PDU/BV-03-C',
            'MESH/SR/RPR/LNK/BV-23-C',
            'MESH/SR/RPR/LNK/BV-25-C',
            'MESH/SR/RPR/LNK/BV-26-C'
        ]
    },
    "mesh_rpr_persistent_storage.conf": {
        "overlay": {
            'CONFIG_BT_MESH_ECDH_P256_HMAC_SHA256_AES_CCM': 'n',
            'CONFIG_BT_MESH_LARGE_COMP_DATA_SRV': 'n',
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_FCB': 'y',
        },
        "test_cases": [
            'MESH/SR/RPR/LNK/BI-05-C',
            'MESH/SR/RPR/PDU/BV-04-C',
            'MESH/SR/RPR/LNK/BV-25-C',
            'MESH/SR/RPR/PDU/BI-03-C',
            'MESH/NODE/CFG/COMP/BV-01-C'
        ]
    },

    "mesh_dfd_srv.conf": {
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_DFU_SRV': 'n',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000'
        },
        "test_cases": [
            'MMDL/CL/FU',
            'MMDL/SR/FD',
            'MMDL/SR/BT'
        ]
    },

    # It is faster to rebuild app that requires sending large amount of
    # data than execute all tests like that.
    "long_data_mesh_dfd_srv.conf": {
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_DFU_SRV': 'n',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '15000'
        },
        "test_cases": [
            'MMDL/SR/BT/BV-38-C'
        ]
    },

    "mesh_dfu_srv.conf": {
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_DFD_SRV': 'n'
        },
        "test_cases": [
            'MMDL/SR/FU',
            'MMDL/CL/BT',
        ]
    },

    "mesh_dfd_dfu.conf": {
        "overlay": {
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_NVS': 'y',
            'CONFIG_BT_MESH_BLOB_SIZE_MAX': '5000'
        },
        "test_cases": [
            'MMDL/SR/FD/BV-48-C',
        ]
    },
}

retry_config = {
}
