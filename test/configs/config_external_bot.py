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

from autopts.bot.iut_config.zephyr import iut_config

BotProjects = []

z = external_nrf52 = {
    'name': 'external',
    'bot_module': 'test/mocks/external_bot.py',
}

# ****************************************************************************
# AutoPTS configuration
# ****************************************************************************
z['auto_pts'] = {
    'server_ip': ['192.168.3.2', '192.168.3.2'],
    'local_ip': ['192.168.3.2', '192.168.3.2'],
    'cli_port': [65001, 65003],
    'srv_port': [65000, 65002],
    'project_path': '/path/to/project',
    'workspace': 'external-master',
    'database_file': 'path/to/externalTestCase.db',
    'store': True,
    'board': 'nrf52',
    'tty_file': 'ttyUSB',  # fake tty file
    'debugger_snr': '123456789',
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
z['git'] = {
    'external': {
        'path': 'path/to/repo',
        'remote': 'origin',
        'branch': 'master',
        'stash_changes': False,
        'update_repo': False,
    },
}

# ****************************************************************************
# Mailbox configuration
#
# To send an email report with test result summary
# ****************************************************************************
z['mail'] = {
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
    # "subject": "Custom email subject",
}

# ****************************************************************************
# Github configuration
#
# To commit and push logs to GitHub.
# Configured ssh-agent must be started earlier.
# ****************************************************************************
z['githubdrive'] = {
    'path': 'path/to/repo',
    'remote': 'origin',
    'branch': 'main',
    'subdir': 'host/',
    'commit_msg': '{branch}_{timestamp}_{commit_sha}',
}

# ****************************************************************************
# Google Drive configuration
#
# To put the tests execution logs to Google Drive
# ****************************************************************************
z['gdrive'] = {
    "root_directory_id": "<GoogleDriveDirID>",
    "credentials_file": "/path/to/credentials.json",
}

# ****************************************************************************
# IUT configuration
#
# To apply test case specific changes in IUT configuration
# ****************************************************************************
z['iut_config'] = iut_config

BotProjects.append(external_nrf52)
