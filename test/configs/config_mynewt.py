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

# Sample user_config file
# Apply your changes and rename it to config.py

from autopts.bot.iut_config.mynewt import iut_config

BotProjects = []

m = mynewt_nrf52 = {
    'name': 'mynewt'
}

# ****************************************************************************
# AutoPTS configuration
# ****************************************************************************
m['auto_pts'] = {
    'server_ip': ['192.168.0.2'],
    'client_port': 6001,
    'local_ip': ['192.168.0.100'],
    'project_path': '/path/to/project',
    'workspace': 'nimble-master',
    'debugger_snr': 'xxxxxxxx',
    'tty_file': 'ttyUSB',  # fake tty file
    'database_file': 'path/to/mynewtTestCase.db',
    'store': True,
    'board': 'nordic_pca10056',
    'enable_max_logs': False,
    'retry': 2,
    'bd_addr': '',
    # 'ykush': '3',  # 1|2|3|a
    'recovery': False,
    'superguard': 15,  # minutes
}

# ****************************************************************************
# Git repositories configuration
# ****************************************************************************
m['git'] = {
    'apache-mynewt-core': {
        'path': 'repos/apache-mynewt-core',
        'remote': 'origin',
        'branch': 'master',
        'stash_changes': False,
    },
    'apache-mynewt-nimble': {
        'path': 'repos/apache-mynewt-nimble',
        'remote': 'origin',
        'branch': 'master',
        'stash_changes': False,
    },
    'mcuboot': {
        'path': 'repos/mcuboot',
        'remote': 'origin',
        'branch': 'main',
        'stash_changes': False,
    },
}

# ****************************************************************************
# Mailbox configuration
#
# To send an email report with test result summary
# ****************************************************************************
m['mail'] = {
    "sender": "john.doe@example.com",
    "smtp_host": 'smtp.example.com',
    "smtp_port": 587,
    "name": "John",
    "passwd": "<PASSWD>",
    "start_tls": False,
    "recipients": [
        "1234@example.com",
        "5678@example.com",
    ],
}

# ****************************************************************************
# Google Drive configuration
#
# To put the tests execution logs to Google Drive
# ****************************************************************************
m['gdrive'] = {
    "root_directory_id": "<GoogleDriveDirID>",
    "credentials_file": "/path/to/credentials.json",
}

# ****************************************************************************
# IUT configuration
#
# To apply test case specific changes in IUT configuration
# ****************************************************************************

m['iut_config'] = iut_config

# ****************************************************************************
# Scheduler configuration
#
# To run the tests periodically
# ****************************************************************************
# m['scheduler'] = {
#     'monday': '10:20',
#     'friday': '20:00',
# }

BotProjects.append(mynewt_nrf52)
