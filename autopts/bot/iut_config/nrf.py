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

iut_config_mmdl = {
    "default": {  # Default west build without option -- -DCONF_FILE=<file.conf>
        "test_cases": [
            'MMDL',
        ],
    },
}

iut_config_mesh = {
    "default": {  # Default west build without option -- -DCONF_FILE=<file.conf>
        "test_cases": [
            'MESH',
        ],
    },
    # "mesh_subnet_count.conf": {
    #     "overlay": {'CONFIG_BT_MESH_SUBNET_COUNT': '1'},
    #     "test_cases": ['MESH/NODE/CFG/NKL/BI-03-C']
    # },
}
