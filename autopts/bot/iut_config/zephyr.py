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
            'MICS', 'VCP'
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
        },
        "test_cases": [
            'MESH/SR/RPR/PDU/BV-02-C',
            'MESH/SR/RPR/PDU/BV-03-C',
            'MESH/SR/RPR/LNK/BI-03-C',
            'MESH/SR/RPR/LNK/BV-21-C',
            'MESH/SR/RPR/LNK/BV-23-C',
            'MESH/SR/RPR/LNK/BV-26-C'
        ]
    },
    "mesh_rpr_persistent_storage.conf": {
        "overlay": {
            'CONFIG_BT_MESH_ECDH_P256_HMAC_SHA256_AES_CCM': 'n',
            'CONFIG_BT_SETTINGS': 'y',
            'CONFIG_FLASH_PAGE_LAYOUT': 'y',
            'CONFIG_FLASH': 'y',
            'CONFIG_FLASH_MAP': 'y',
            'CONFIG_FCB': 'y',
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
            'DFU/CL/FU/BV-01-C',
            'DFU/CL/FU/BV-02-C',
            'DFU/CL/FU/BV-03-C',
            'DFU/SR/FD/BV-01-C',
            'DFU/SR/FD/BV-02-C',
            'DFU/SR/FD/BV-03-C',
            'DFU/SR/FD/BV-04-C',
            'DFU/SR/FD/BV-05-C',
            'DFU/SR/FD/BV-06-C',
            'DFU/SR/FD/BV-07-C',
            'DFU/SR/FD/BV-08-C',
            'DFU/SR/FD/BV-09-C',
            'DFU/SR/FD/BV-10-C',
            'DFU/SR/FD/BV-11-C',
            'DFU/SR/FD/BV-12-C',
            'DFU/SR/FD/BV-19-C',
            'DFU/SR/FD/BV-20-C',
            'DFU/SR/FD/BV-21-C',
            'DFU/SR/FD/BV-22-C',
            'DFU/SR/FD/BV-23-C',
            'DFU/SR/FD/BV-24-C',
            'DFU/SR/FD/BV-25-C',
            'DFU/SR/FD/BV-26-C',
            'DFU/SR/FD/BV-27-C',
            'DFU/SR/FD/BV-28-C',
            'DFU/SR/FD/BV-29-C',
            'DFU/SR/FD/BV-30-C',
            'DFU/SR/FD/BV-31-C',
            'DFU/SR/FD/BV-32-C',
            'DFU/SR/FD/BV-33-C',
            'DFU/SR/FD/BV-34-C',
            'DFU/SR/FD/BV-59-C',
            'DFU/SR/FD/BV-50-C',
            'DFU/SR/FD/BV-35-C',
            'DFU/SR/FD/BV-36-C',
            'DFU/SR/FD/BV-37-C',
            'DFU/SR/FD/BV-38-C',
            'DFU/SR/FD/BV-39-C',
            'DFU/SR/FD/BV-40-C',
            'DFU/SR/FD/BV-41-C',
            'DFU/SR/FD/BV-51-C',
            'DFU/SR/FD/BV-42-C',
            'DFU/SR/FD/BV-43-C',
            'DFU/SR/FD/BV-44-C',
            'DFU/SR/FD/BV-45-C',
            'DFU/SR/FD/BV-46-C',
            'DFU/SR/FD/BV-49-C',
            'DFU/SR/FD/BV-52-C',
            'DFU/SR/FD/BV-53-C',
            'DFU/SR/FD/BV-54-C',
            'DFU/SR/FD/BV-55-C',
            'DFU/SR/FD/BV-56-C',
            'DFU/SR/FD/BV-57-C',
            'DFU/SR/FD/BV-58-C',
            'MBT/SR/BT/BV-01-C',
            'MBT/SR/BT/BV-02-C',
            'MBT/SR/BT/BV-03-C',
            'MBT/SR/BT/BV-04-C',
            'MBT/SR/BT/BV-05-C',
            'MBT/SR/BT/BV-06-C',
            'MBT/SR/BT/BV-07-C',
            'MBT/SR/BT/BV-08-C',
            'MBT/SR/BT/BV-09-C',
            'MBT/SR/BT/BV-10-C',
            'MBT/SR/BT/BV-11-C',
            'MBT/SR/BT/BV-12-C',
            'MBT/SR/BT/BV-13-C',
            'MBT/SR/BT/BV-14-C',
            'MBT/SR/BT/BV-15-C',
            'MBT/SR/BT/BV-16-C',
            'MBT/SR/BT/BV-17-C',
            'MBT/SR/BT/BV-18-C',
            'MBT/SR/BT/BV-19-C',
            'MBT/SR/BT/BV-20-C',
            'MBT/SR/BT/BV-21-C',
            'MBT/SR/BT/BV-22-C',
            'MBT/SR/BT/BV-23-C',
            'MBT/SR/BT/BV-24-C',
            'MBT/SR/BT/BV-25-C',
            'MBT/SR/BT/BV-26-C',
            'MBT/SR/BT/BV-27-C',
            'MBT/SR/BT/BV-28-C',
            'MBT/SR/BT/BV-29-C',
            'MBT/SR/BT/BV-30-C',
            'MBT/SR/BT/BV-31-C',
            'MBT/SR/BT/BV-32-C',
            'MBT/SR/BT/BV-33-C',
            'MBT/SR/BT/BV-34-C',
            'MBT/SR/BT/BV-35-C',
            'MBT/SR/BT/BV-36-C',
            'MBT/SR/BT/BV-37-C',
            'MBT/SR/BT/BI-01-C',
            'MBT/SR/BT/BI-02-C',
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
            'MBT/SR/BT/BV-38-C'
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
            'DFU/SR/FU/BV-01-C',
            'DFU/SR/FU/BV-02-C',
            'DFU/SR/FU/BV-03-C',
            'DFU/SR/FU/BV-04-C',
            'DFU/SR/FU/BV-05-C',
            'DFU/SR/FU/BV-06-C',
            'DFU/SR/FU/BV-07-C',
            'DFU/SR/FU/BV-08-C',
            'DFU/SR/FU/BV-09-C',
            'DFU/SR/FU/BV-10-C',
            'DFU/SR/FU/BV-11-C',
            'DFU/SR/FU/BV-12-C',
            'DFU/SR/FU/BV-13-C',
            'DFU/SR/FU/BV-14-C',
            'DFU/SR/FU/BV-15-C',
            'DFU/SR/FU/BV-16-C',
            'DFU/SR/FU/BV-17-C',
            'DFU/SR/FU/BV-18-C',
            'DFU/SR/FU/BV-19-C',
            'DFU/SR/FU/BV-20-C',
            'DFU/SR/FU/BV-21-C',
            'DFU/SR/FU/BV-22-C',
            'DFU/SR/FU/BV-23-C',
            'DFU/SR/FU/BV-24-C',
            'DFU/SR/FU/BV-27-C',
            'MBT/CL/BT/BV-01-C',
            'MBT/CL/BT/BV-02-C',
            'MBT/CL/BT/BV-03-C',
            'MBT/CL/BT/BV-04-C',
            'MBT/CL/BT/BV-05-C',
            'MBT/CL/BT/BV-06-C',
            'MBT/CL/BT/BV-07-C',
            'MBT/CL/BT/BV-08-C'
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
            'DFU/SR/FD/BV-48-C',
        ]
    },
}

retry_config = {
}
