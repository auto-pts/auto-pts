# Table of Contents

   * [Introduction](#introduction)
   * [Architecture](#architecture)
   * [Windows Prerequisites](#windows-prerequisites)
   * [Generating Interop Assembly](#generating-interop-assembly)
   * [PTS Workspace Setup](#pts-workspace-setup)
   * [Running in Client/Server Mode](#running-in-clientserver-mode)
   * [Running Test Script on Windows](#running-test-script-on-windows)
   * [Running AutoPTSClientBot](#running-autoptsclientbot)
   * [IRC Channel on freenode.net](#irc-channel-on-freenodenet)

# Introduction

The Bluetooth Profile Tuning Suite (PTS) is a Bluetooth testing tool provided by Bluetooth SIG. The PTS is a Windows program that is normally used in manual mode via its GUI.

auto-pts is the Bluetooth PTS automation framework. auto-pts uses PTSControl COM API of PTS to automate testing.

Over 460 test cases have been automated for Zephyr OS and Mynewt OS which reduced testing time from one man-month to 9 hours. auto-pts has been used to automate testing of three Bluetooth stacks thus far:

* BlueZ
* Zephyr BLE
* Mynewt NimBLE

# Architecture

![](images/autp-pts-architecture-diagram.png)

**auto-pts server**: Implemented in Python 3. Runs on Windows and provides over-the-network XML-RPC interface to PTS.

**auto-pts client**: Implemented in Python 2.7. Runs on GNU/Linux, communicates with the auto-pts server (to start/stop test cases, to send response to PTS inquiries) and communicates with the Implementation Under Test to take appropriate actions.

**Implementation Under Test (IUT)**: It is the host running Bluetooth stack to be tested, this could be an emulator or real hardware. The IUT is controlled by using Bluetooth Test Protocol.

**Bluetooth Test Protocol (BTP)**: Used to communicate with the IUT. See `doc/btp_spec.txt`

# Linux Prerequisites

1. `socat` that is used to transfer BTP data stream from UART's tty file.

        sudo apt-get install python-setuptools socat

2. Additionally, install required Python modules with:

        python2 -m pip install --user -r autoptsclient_requirements.txt

# Windows Prerequisites

To be able to run PTS in automation mode, there should be no PTS instances running in the GUI mode. Hence, before running these scripts close the PTS GUI.

1. Install required modules with:

        python.exe -m pip install --user -r autoptsserver_requirements.txt

# PTS Workspace Setup

Before running any scripts you have to create a workspace in the PTS, add needed projects to the workspace and configure PICs and PIXITs.

Alternatively, you can use auto-pts workspaces. Auto-pts provides ready PTS workspaces with readily configured PICS in the "workspaces" directory. The list of available workspaces:

  * bluez
  * Mynewt Nimble Host
  * zephyr-master
  * zephyr-v1.14
  * zephyr-v2.2.0

# Running in Client/Server Mode

The auto-pts framework uses a client server architecture. With this setup the PTS automation server runs on Windows and the client runs on GNU/Linux.

The command below starts AutoPTS server on Windows:

    python.exe autoptsserver.py

There are separate `autoptsclient-*.py` scripts to lunch AutoPTS Client depending on the tested stack.

**Testing Zephyr Host Stack on QEMU**

Start a proxy for Bluetooth adapter by using `btproxy` tool from BlueZ:

    sudo bluez/tools/btproxy -u -z

Then start the AutoPTS Client using e.g. own workspace file:

    ./autoptsclient-zephyr.py "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6" zephyr.elf -i SERVER_IP -l LOCAL_IP

**Testing Zephyr combined (controller + host) build on nRF52**:

    ./autoptsclient-zephyr.py zephyr-master <path>/zephyr.elf -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nrf52


**Testing Mynewt build on nRF52**:

    ./autoptsclient-mynewt.py "Mynewt Nimble Host" -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nordic_pca10056

**Testing BlueZ on Linux

See [ptsprojects/bluez/README.md](./ptsprojects/bluez/README.md)

# Running AutoPTSClientBot

AutoPTSClientBot has been added to automate running test cases on various
configurations and reporting the results.

**Key features**

- Fetching recent project sources
- Applying changes to project configuration files via "iut_config"
with "overlay" that need to be applied for "test_cases"
- Building ZephyrOS/MynewtOS image
- Flashing board
- Running all the test cases
- Archiving test execution logs
- Storing the results in Excel spreadsheet file
    - test case statuses
    - pie chart
- Sending the files to the Google Drive
- Sending e-mail

**Configuration**

The Bot configuration file is located in `bot` . Sample files `bot/config.py.zephyr.sample`
and `bot/config.py.mynewt.sample` are provided. The file contains setup and project-specific configuration.

This may contain few sections:
- `name` - AutoPTS project name
* `auto_pts` - AutoPTS configuration
    - `server_ip` - AutoPTSServer IP address
    - `client_port` - local AutoPTSClient port
    - `project_path` - path to project source directory
    - `workspace` - PTS workspace path to be used
    - `board` - IUT used. Currently nrf52 is supported only
    - `enable_max_logs` - enable debug logs
    - `retry` - maximum repeat count per test
    - `bd_addr` - IUT Bluetooth Address (optional)
- `mail` - Mail configuration (optional)
    - `sender` - sender e-mail address
    - `smtp_host`, `smtp_port` - sender SMTP configuration
    - `name` - to be used in message footer
    - `passwd` - sender mailbox password. When Google account is used [allow
    less secure apps to access account](https://myaccount.google.com/lesssecureapps)
    - `recipients` - list of e-mail addresses
* `gdrive` - GDrive configuration (optional)
    - `root_directory_id` - Root Directory ID, can be obtained from URL,
    `https://drive.google.com/drive/u/0/folders/<GoogleDriveDirID>`
    - `credentials_file` - path to credentials file to access Google Account.
    Read more [here](https://developers.google.com/drive/v3/web/quickstart/python).
- `iut_config` - IUT configuration overlay. This is used to apply test case
specific changes in IUT configuration. It consists of dict of configuration
names and related key: value pairs:
    - `overlay` - changes in config to be applied
    - `test_cases` - test cases to be ran with this config
* `scheduler` - Scheduler configuration (optional)
    - `weekday`: "time" dictionary.

**Installation**

Install required Python modules with:

    pip2 install --user -r bot/requirements.txt

**Usage**

    ./autoptsclient_bot.py

# IRC Channel on freenode.net

Our IRC channel on freenode.net is #autopts
