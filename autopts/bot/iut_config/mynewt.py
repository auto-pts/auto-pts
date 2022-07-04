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

# Stable MyNewt IUT config

iut_config = {
    "default.conf": {
        "test_cases": [
            'GAP', 'GATT', 'L2CAP', 'SM', 'MESH',
        ],
    },

    "privacy.conf": {
        "overlay": {'BTTESTER_PRIVACY_MODE': '1'},
        "test_cases": [
            'GAP/BROB/BCST/BV-03-C',
            'GAP/BROB/BCST/BV-05-C'
            'GAP/CONN/ACEP/BV-03-C',
            'GAP/CONN/ACEP/BV-04-C',
            'GAP/CONN/DCEP/BV-05-C',
            'GAP/CONN/DCEP/BV-06-C',
            'GAP/CONN/GCEP/BV-05-C',
            'GAP/CONN/GCEP/BV-06-C',
            'GAP/CONN/SCEP/BV-03-C',
            'GAP/CONN/UCON/BV-06-C',
            'GAP/DISC/GENM/BV-03-C',
            'GAP/PRIV/CONN/BV-10-C',
            'GAP/PRIV/CONN/BV-11-C',
            'GAP/PRIV/CONN/BI-01-C',
            'GAP/PRIV/CONN/BI-10-C',
        ]},

    "sec_m1l4.conf": {
        "overlay": {
            'BLE_SM_LEGACY': '0',
            'BLE_SM_SC': '1',
            'BLE_SM_SC_ONLY': '0',
            'BLE_SM_LVL': '4',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-21-C',
            'GAP/SEC/SEM/BV-22-C',
            'GAP/SEC/SEM/BV-24-C',
            'GAP/SEC/SEM/BV-26-C',
            'GAP/SEC/SEM/BV-27-C',
        ]
    },

    "sec_m1l2.conf": {
        "overlay": {
            'BLE_SM_LEGACY': '1',
            'BLE_SM_SC': '1',
            'BLE_SM_SC_ONLY': '0',
            'BLE_SM_LVL': '2',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-37-C',
            'GAP/SEC/SEM/BV-39-C',
            'GAP/SEC/SEM/BV-41-C',
            'GAP/SEC/SEM/BV-43-C',
            'GAP/SEC/SEM/BV-56-C',
            'GAP/SEC/SEM/BV-57-C',
            'GAP/SEC/SEM/BV-59-C'
        ]
    },

    "sec_m1l3.conf": {
        "overlay": {
            'BLE_SM_LEGACY': '1',
            'BLE_SM_SC': '1',
            'BLE_SM_SC_ONLY': '0',
            'BLE_SM_LVL': '3',
        },
        "test_cases": [
            'GAP/SEC/SEM/BV-38-C',
            'GAP/SEC/SEM/BV-40-C',
            'GAP/SEC/SEM/BV-42-C',
            'GAP/SEC/SEM/BV-44-C',
            'GAP/SEC/SEM/BV-60-C',
        ]
    },

    "sc_only.conf": {
        "overlay": {
            'BLE_SM_LEGACY': '0',
            'BLE_SM_SC': '1',
            'BLE_SM_SC_ONLY': '1',
            'BLE_SM_LVL': '4',
            'BLE_SM_MITM': '1'
        },
        "test_cases": [
            'GAP/SEC/SEM/BI-09-C',
            'GAP/SEC/SEM/BI-10-C',
            'GAP/SEC/SEM/BI-20-C',
            'GAP/SEC/SEM/BI-21-C',
            'GAP/SEC/SEM/BI-22-C',
            'GAP/SEC/SEM/BI-23-C',
            'GAP/SEC/SEM/BV-23-C',
            'GAP/SEC/SEM/BV-28-C',
            'GAP/SEC/SEM/BV-29-C',
            'GAP/SEC/SEM/BV-58-C',
            'GAP/SEC/SEM/BV-61-C'
        ]
    },

    "key_dist_no_csrk.conf": {
        "overlay": {
            'BLE_SM_OUR_KEY_DIST': '3',
        },
        "test_cases": [
            'GAP/BOND/BON/BV-04-C',
        ]
    },

    "nrpa.conf": {
        "overlay": {
            'BTTESTER_PRIVACY_MODE': '1',
            'BTTESTER_USE_NRPA': '1',
        },
        "test_cases": ['GAP/BROB/BCST/BV-04-C']
    },

    "l2cap_param_update.conf": {
        "overlay": {'BTTESTER_CONN_PARAM_UPDATE': '1'},
        "test_cases": [
            'GAP/CONN/CPUP/BV-01-C',
            'GAP/CONN/CPUP/BV-02-C',
            'GAP/CONN/CPUP/BV-03-C',
            'GAP/CONN/CPUP/BV-06-C',
            'L2CAP/LE/CPU/BV-01-C',
        ]
    },

    "l2cap_mtu_eq_mps.conf": {
        "overlay": {'BTTESTER_L2CAP_COC_MTU': '100'},
        "test_cases": [
            'L2CAP/COS/ECFC/BV-04-C',
        ]
    },
}
