# Windows Prerequisites

Since this PTS automation framework uses IronPython it needs COM interop
assembly Interop.PTSConrol.dll to be located in the same directory as the
automation scripts.

You need to use 32 bit IronPython to run these scripts because PTS is a 32 bit
application.

To be able to run PTS in automation mode, there should be no PTS instances
running in the GUI mode. Hence, before running these scripts close the PTS GUI.

# PTS workspace setup

Before running any scripts you have to create a workspace in the PTS,
add needed projects to the workspace and configure PICs and PIXITs.

Alternatively, you can use auto-pts workspaces. Auto-pts provides ready PTS
workspaces with readily configured PICS in the "workspaces"
directory. Currently it provides workspaces for the Zephyr HCI stack. To select
ready made workspace pass to the auto-pts client as the workspace argument:

  * zephyr-hci

# Running in client/server mode

The auto-pts framework uses a client server architecture. With this setup the
PTS automation server runs on Windows and the client runs on GNU/Linux. So on
Windows you start the server:

`ipy.exe autoptsserver.py`

And on GNU/Linux you select either the Android or Zephyr client, then pass it
the IP address of the server and the path to the PTS workspace file on the
Windows machine. So for AOSP BlueZ projects:

`./autoptsclient-aospbluez.py IP_ADDRESS "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6"`

For Zephyr projects running under QEMU:

Start a proxy for bluetooth adapter by using btproxy from BlueZ:

`sudo bluez/tools/btproxy -u -z`

Then start the client:

`./autoptsclient-zephyr.py IP_ADDRESS "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6" zephyr.elf`

Zephyr running in Arduino:

`./autoptsclient-zephyr.py IP_ADDRESS "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6" zephyr.elf -t /dev/ttyUSB0 -b arduino_101 -d`

The command to run auto-pts client using auto-pts Zephyr HCI workspace is:

`./autoptsclient-zephyr.py IP_ADDRESS zephyr-hci zephyr.elf -t /dev/ttyUSB0 -b arduino_101 -d`

# Running AutoPTSClientBot

AutoPTSClientBot has been added to automate running test cases on various
configurations and reporting the results.
Initial bot implementation supports running Zephyr tests on nrf52 board.

**Key features**

- Scheduler to run the script periodically
- Fetching recent project sources
- Applying changes to project configuration files via "iut_config"
with "overlay" that need to be applied for "test_cases"
- Building ZephyrOS image
- Flashing board
- Running all the test cases
- Archiving test execution logs
- Storing the results in Excel spreadsheet file
    - test case statuses
    - pie chart
- Sending the files to the Google Drive
- Sending e-mail

**Configuration**

Bot is configured via "bot/config.py" file. Sample `bot/config.py.sample` file
is provided. The configuration file is composed of project configurations.
This may contain few sections:
- 'name' - AutoPTS project name
- 'auto_pts' - AutoPTS configuration
    - 'server_ip' - AutoPTSServer IP address
    - 'client_port' - local AutoPTSClient port
    - 'project_path' - path to project source directory
    - 'workspace' - PTS workspace path to be used
    - 'board' - IUT used. Currently nrf52 is supported only
    - 'enable_max_logs' - enable debug logs
    - 'retry' - maximum repeat count per test
    - 'bd_addr' - IUT Bluetooth Address (optional)
- 'mail' - Mail configuration (optional)
    - 'sender' - sender e-mail address
    - 'smtp_host', 'smtp_port' - sender SMTP configuration
    - 'name' - to be used in message footer
    - 'passwd' - sender mailbox password. When Google account is used [allow
    less secure apps to access account](https://myaccount.google.com/lesssecureapps)
    - 'recipients' - list of e-mail addresses
- 'gdrive' - GDrive configuration (optional)
    - 'root_directory_id' - Root Directory ID, can be obtained from URL,
    `https://drive.google.com/drive/u/0/folders/<GoogleDriveDirID>`
    - 'credentials_file' - path to credentials file to access Google Account.
    Read more [here](https://developers.google.com/drive/v3/web/quickstart/python).
- 'iut_config' - IUT configuration overlay. This is used to apply test case
specific changes in IUT configuration. It consists of dict of configuration
names and related key: value pairs:
    - 'overlay' - changes in config to be applied
    - 'test_cases' - test cases to be ran with this config
- 'scheduler' - Scheduler configuration (optional)
    - "weekday": "time" dictionary.

**Installation**

Install required Python modules (
schedule,
gitpython,
xlsxwriter,
google-api-python-client
) with:

    cd ~/auto-pts  # or to your directory where AutoPTS is cloned
    pip2 install --user -r bot/requirements.txt


**Usage**

    cd ~/auto-pts  # or to your directory where AutoPTS is cloned
    ./autoptsclient_bot.py


# Running test script on Windows

It is also possible to run tests on Windows, without using client/server mode
of auto-pts. On Windows instead of starting the auto-pts server start test
script as:

`ipy.exe autopts.py`

autopts.py has been used to test AOSP BlueZ Bluetooth stack, and serves a good
reference on how to create a tester for Windows.

# Generating Interop Assembly

On Windows, run this command:

`TlbImp.exe PTSControl.dll /out:Interop.PTSControl.dll /verbose`
