# Getting Started
 Follow the steps below to set up the project, install dependencies, 
and enable automatic code formatting and linting.

---

### Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```
---

### 2. Install Dependencies

Install dependencies listed in `requirements_ci.txt`:

```bash
pip install -r requirements_ci.txt
```

We recommend using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```

---

## Code Style & Formatting

This project uses:

- [`Ruff`](https://docs.astral.sh/ruff/) – for fast PEP8 linting and auto-fixing

Ruff is configured via `pyproject.toml`, so no additional config files are needed.

### Style Checks and Auto-Fixing
Two helper scripts are provided for working with code style:

#### Check style:
```bash
python autopts/style_tools.py check
```
This will run `ruff check` and log the output to `logs/pep8/ruff_check.log`.

#### Auto-fix style issues:
```bash
python autopts/style_tools.py fix
```
This will run `ruff check --fix` and apply fixes. Output is logged to `logs/pep8/ruff_fix.log`.

---

### Manual Usage

You can also run `ruff` directly:

```bash
ruff check .
ruff check . --fix
```

---
### (Optional) Pre-commit Hook

To automatically check code style before each commit:

1. Install `pre-commit`:
```bash
pip install pre-commit
pre-commit install
```

2. Now each commit will trigger `ruff` automatically:

```bash
git commit -m "Your message"
```
---


###  GitHub Actions – Automatic Style Check

A workflow is configured in `.github/workflows/full-style-matrix.yml` to automatically check code style on every push or pull request to `main` or `master`.

### What it does:
- Checks code with `ruff`

This ensures consistent code quality across all contributions.

---

# Table of Contents

   * [Introduction](#introduction)
   * [Architecture](#architecture)
   * [Linux Prerequisites](#linux-prerequisites)
   * [Windows Prerequisites](#windows-prerequisites)
   * [PTS Workspace Setup](#pts-workspace-setup)
   * [Running in Client/Server Mode](#running-in-clientserver-mode)
   * [Running AutoPTSClientBot](#running-autoptsclientbot)
   * [Zephyr with AutoPTS step-by-step setup tutorial](#zephyr-with-autopts-step-by-step-setup-tutorial)
   * [Tutorials](#tutorials)
   * [More examples of run and tips](#more-examples-of-run-and-tips)
   * [Slack Channel](#slack-channel)

# Introduction

The Bluetooth Profile Tuning Suite (PTS) is a Bluetooth testing tool provided by Bluetooth SIG. The PTS is a Windows program that is normally used in manual mode via its GUI.

auto-pts is the Bluetooth PTS automation framework. auto-pts uses PTSControl COM API of PTS to automate testing.

Over 630 test cases have been automated for Zephyr OS and Mynewt OS which reduced testing time from 'one man - 2 months' to 15 hours. auto-pts has been used to automate testing of three Bluetooth stacks thus far:

* BlueZ
* Zephyr BLE
* Mynewt NimBLE

# Architecture

2 setups are available:

### Linux + Windows

![](images/auto-pts-architecture-linux-diagram.png)

### Windows

![](images/auto-pts-architecture-win10-diagram.png)


**auto-pts server**: Implemented in Python 3. Runs on Windows and provides over-the-network XML-RPC interface to PTS.

**auto-pts client**: Implemented in Python 3. Runs on GNU/Linux or Windows, communicates with the auto-pts server (to start/stop test cases, to send response to PTS inquiries) and communicates with the Implementation Under Test to take appropriate actions.

**Implementation Under Test (IUT)**: It is the host running Bluetooth stack to be tested, this could be an emulator or real hardware. The IUT is controlled by using Bluetooth Test Protocol.

**Bluetooth Test Protocol (BTP)**: Used to communicate with the IUT. See `doc/btp_spec.txt`

# Linux Prerequisites

For auto-pts client under Linux:

1. `socat` that is used to transfer BTP data stream from UART's tty file.

        sudo apt-get install python-setuptools socat

2. Additionally, install required Python modules with:

        python3 -m pip install --user -r autoptsclient_requirements.txt

3. If using Nordic nRF board as DUT, install `nrfutil` tool.

    3.1. Follow the instructions https://docs.nordicsemi.com/bundle/nrfutil/page/guides/installing.html. 

    3.2. Install `nrfutil device` command with:

          nrfutil install device

The rest of the setup is platform/mode specific:

### BlueZ

See [ptsprojects/bluez/README.md](autopts/ptsprojects/bluez/README.md)

### Zephyr BLE

See [Zephyr with AutoPTS step-by-step setup tutorial](#zephyr-with-autopts-step-by-step-setup-tutorial)

### Mynewt NimBLE

Perform setup from [Apache MyNewt](https://mynewt.apache.org/latest/get_started/index.html), typically:

1. [Install Newt](https://mynewt.apache.org/latest/newt/install/newt_linux.html)
2. [Instal toolchain and J-Link](https://mynewt.apache.org/latest/get_started/native_install/cross_tools.html)
3. Test setup with [Blinky project](https://mynewt.apache.org/latest/tutorials/blinky/nRF52.html)

# Windows Prerequisites

For auto-pts server:

To be able to run PTS in automation mode, there should be no PTS instances running in the GUI mode. Hence, before running these scripts close the PTS GUI.

1. Install required modules with:

        python.exe -m pip install --user -r autoptsserver_requirements.txt

For auto-pts client:

1. Install required modules with:

        python.exe -m pip install --user -r autoptsclient_requirements.txt

2. Download socat.exe from https://sourceforge.net/projects/unix-utils/files/socat/1.7.3.2/ and add to PATH socat.exe directory.

The rest of the auto-pts client setup is platform/mode specific:

### Zephyr BLE

Check out [Zephyr with AutoPTS step-by-step setup tutorial](#zephyr-with-autopts-step-by-step-setup-tutorial)

### MyNewt NimBle

For building and flashing app image Newt tool is required. On Windows it should
be installed as MSYS2 application.

In MSYS2 MinGW x64 application:
1. Install [MSYS2/MinGW](https://www.msys2.org) from installer and run
    ```shell
    $ pacman -Syu
    $ pacman -Su
    ```
2. Install Git
    ```shell
    $ pacman -S git
    ```
3. Install Go
   ```shell
   $ pacman -S mingw-w64-x86_64-go
   ```
   If this command fails with error like:
   ```shell
   File /var/cache/pacman/pkg/mingw-w64-x86_64-libpng-1.6.12-1-any.pkg.tar.xz is corrupted (invalid or corrupted package (PGP signature)).
   ```
   keys need to be updated:
   ```shell
   $ pacman-key --init
   $ pacman-key --populate msys2
   $ pacman-key --refresh-keys
   ```
4. Install Newt tool. For testing Mynewt from master branch we often require
   in-dev versions of Newt tool, from master branch. To install just latest
   release:
   ```shell
   $ wget -P /tmp https://github.com/apache/mynewt-newt/archive/mynewt_1_8_0_tag.tar.gz
   $ tar -xzf /tmp/mynewt_1_8_0_tag.tar.gz
   $ cd mynewt-newt-mynewt_1_8_0_tag/mynewt-newt/newt
   $ go get
   $ go build
   $ /home/user_name/mynewt-newt/newt/newt.exe
   ```
   To install Newt in-dev version:
   ```shell
   $ git clone https://github.com/apache/mynewt-newt.git
   $ cd mynewt-newt/newt
   $ go get
   $ go build
   $ mv /home/user_name/mynewt-newt/newt/newt.exe /usr/bin
   ```
   You can verify installation by calling `newt version`
5. To install cross-compilation tools follow [this](https://github.com/apache/mynewt-documentation/blob/master/docs/get_started/native_install/cross_tools.rst)
   guide
6. Setup Mynewt Project using [this](https://github.com/apache/mynewt-documentation/blob/master/docs/get_started/project_create.rst)
   guide
7. Python functions must use environment we just setup, so functions calling
   shell commands like `check_call` must use MSYS. In Windows we must setup
   environment variable to specify this.
   1. open Environment Variables settings by pressing <kbd>⊞ Win</kbd>+<kbd>R</kbd>
      and typing `systempropertiesadvanced`.
   2. Click “Environment Variables” button
   3. In “Environment Variables” click `New`
   4. As `Variable Name` set `MSYS2_BASH_PATH`
   5. As `Variable Value` set `C:\msys64\usr\bin\bash.exe`

# PTS Workspace Setup

Before running any scripts you have to create a workspace in the PTS, add needed projects to the workspace and configure PICs and PIXITs.

Alternatively, you can use auto-pts workspaces. Auto-pts provides ready PTS workspaces with readily configured PICS in the "workspaces" directory. The list of available workspaces:

  * bluez
  * nimble-master
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

    ./autoptsclient-zephyr.py zephyr-master -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nrf52

**Testing Zephyr Host Stack on native posix**:

    ./autoptsclient-zephyr.py zephyr-master <path>/zephyr.exe -i SERVER_IP -l LOCAL_IP --hci 0

**Testing Mynewt build on nRF52**:

    ./autoptsclient-mynewt.py nimble-master -i SERVER_IP -l LOCAL_IP -t /dev/ttyACM0 -b nordic_pca10056

**Testing BlueZ on Linux**:

See [ptsprojects/bluez/README.md](autopts/ptsprojects/bluez/README.md)

# Running AutoPTSClientBot

See [AutoPTSClientBot readme](autopts/bot/README.md)

# Zephyr with AutoPTS step-by-step setup tutorial
Check out the guide how to set up AutoPTS for Zephyr + nRF52 under:
- Linux + Windows 10 virtual machine

  https://docs.zephyrproject.org/latest/connectivity/bluetooth/autopts/autopts-linux.html

- Windows 10

  https://docs.zephyrproject.org/latest/connectivity/bluetooth/autopts/autopts-win10.html

# Tutorials

- [How to create PTS workspace](doc/tutorials/create_workspace.md)
- [How to add support for a PTS profile](doc/tutorials/add_test_case.md)

# More examples of run and tips

**Run many instances of autoptsserver on one Windows**

Run in first console:

    $ python autoptsserver.py

and in second console:

    $ python autoptsserver.py -S 65002

or both in one console

    $ python autoptsserver.py -S 65000 65002

**Run many autoptsclient-zephyr.py instances on one machine**

Under Windows, run in first console: (-S 65000 -C 65001 by default)

    $ python ./autoptsclient-zephyr.py zephyr-master -t COM3 -b nrf52

and in second console:

    $ python ./autoptsclient-zephyr.py zephyr-master -t COM4 -b nrf52 -S 65002 -C 65003

and more. Note that IP 127.0.0.1 is default, so there is no need to specify with -i and -l options.

Under Linux, run in first console: (-S 65000 -C 65001 by default)

    $ ./autoptsclient-zephyr.py zephyr-master -i 192.168.4.2 192.168.4.2 -l 192.168.4.1 192.168.4.1 -t /dev/ttyACM0 -b nrf52

in second console:

    $ ./autoptsclient-zephyr.py zephyr-master -i 192.168.4.2 192.168.4.2 -l 192.168.4.1 192.168.4.1 -t /dev/ttyACM1 -b nrf52 -S 65002 -C 65003

**Example run of autoptsclient-zephyr for MESH testing:**

In some test cases 2 instances of PTS are needed. So run autoptsserver with 2 instances:

    $ python autoptsserver.py -S 65000 65002

Under Windows, run in second console:

    $ python ./autoptsclient-zephyr.py zephyr-master -t COM3 -b nrf52 -c MESH -S 65000 65002 -C 65001 65003

Under Linux, run in one console:

    $ ./autoptsclient-zephyr.py zephyr-master -i 192.168.4.2 192.168.4.2 -l 192.168.4.1 192.168.4.1 -t /dev/ttyACM0 -b nrf52 -c MESH -S 65000 65002 -C 65001 65003

#### Recovery tips

This feature was created to enable long runs of bot without supervision, because in continuous development some regressions on IUT or PTS side sometimes loop a test case somewhere.

**Recover autoptsserver after exception**

Autoptsserver can recover itself after python exception or after request received from autoptsclient.
If you have YKUSH hub, you can run server with option --ykush, so recovery steps will include re-plugin of PTS dongles:

    $ python autoptsserver.py -S 65000 65002 --ykush 1 2

where 1 and 2 are numbers of YKUSH USB ports (More about [YKUSH hub](https://www.yepkit.com/products/ykush)).

Helpful --superguard option will blindly trigger recovery after given amount of time in minutes:

    $ python autoptsserver.py -S 65000 65002 --superguard 15

**Recover autoptsclient after exception**

Recovery of autoptsclient can be enabled with --recovery option and is triggered after python exception or test case result other than PASS, INCONC or FAIL.
Then it sends recovery request to autoptsserver, restarting and reinitializing PTSes.

    $ python ./autoptsclient-zephyr.py zephyr-master -t COM3 -b nrf52 --recovery

Options --superguard and --ykush works on autoptsclient same as on autoptsserver. So when run with --superguard 15, after 15 minutes of unfinished test case, superguard will force recovery. With option --ykush \<port\> the IUT board will be re-plugged during recovery.

# Community

Use this [link](https://discord.com/invite/Ck7jw53nU2) to join Discord server. After that enter [#bt-qualification](https://discord.com/channels/720317445772017664/733036879062106264) channel (under Bluetooth section). Although Discord server is for Zephyr Project topics are not limited to Zephyr.

You may also seek IUT specific help on:

* [Apache Mynewt (NimBLE)](https://mynewt.apache.org)
* [Zephyr Project](https://zephyrproject.org)
* [BlueZ](https://www.bluez.org)
