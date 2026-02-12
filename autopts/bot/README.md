# Running AutoPTSClientBot

AutoPTSClientBot has been added to automate running test cases on various
configurations and reporting the results.

**Key features**

- Fetching recent project sources
- Applying changes to project configuration files via "iut_config"
with "overlay" that need to be applied for "test_cases"
- setting test-specific retry count via "retry_config"
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
    - `iut_mode` - Specifies the mode of the IUT (e.g. native, qemu, tty)
    - `workspace` - Path to PTS workspace .pqw6 file to use for testing. THe file should be located where automation 
  server is running.
    - `project_path` - path to project source directory
    - `tester_app_dir` - path to tester application directory relative to project_path. Only works for Zephyr based projects.
    - `cli_port` - AutoPTSClient port(s). If running with multiple servers(PTS dongles), specify the ports in
  config_project.py as follows: 'srv_port': [65001, 65003, 65005]
    - `srv_port` - AutoPTSServer port(s). If running with multiple servers(PTS dongles), specify the ports in
  config_project.py as follows: 'srv_port': [65000, 65002, 65004]
    - `ip_addr` - IP address of the PTS automation servers.
    - `client_ip` - AutoPTSClient IP address/es
    - `server_ip` - AutoPTSServer IP address/es
    - `store` - set True to save run results in a database .db file (default False)
    - `rtt_log` - collect IUT logs via RTT J-Link buffer named "Logger"
    - `btmon` - collect IUT btsnoops with btmon
    - `device_core` - Specify the device core for JLink related features, e.g. BTMON or RTT logging
    - `qemu_bin` - The path to the QEMU executable, e.g. /usr/bin/qemu-system-arm
    - `qemu_options` - Additional options for the qemu, e.g. -cpu cortex-m3 -machine lm3s6965evb
    - `btattach_bin` - The path to the btattach executable, e.g. /usr/bin/btattach
    - `btattach_at_every_test_case` - Use btattach at every test case
    - `btproxy_bin` - The path to the btproxy executable, e.g. /usr/bin/btproxy
    - `btmgmt_bin` - The path to the btmgmt executable, e.g. /usr/bin/btmgmt
    - `hid_vid` - Specify the VID of the USB device used as a HCI controller (hexadecimal string, e.g. '2fe3')
    - `hid_pid` - Specify the PID of the USB device used as a HCI controller (hexadecimal string, e.g. '000b')
    - `hid_serial` - Specify the serial number of the USB device used as a HCI controller
    - `kernel_cpu` - The type of CPU that will be used for building an image, e.g. qemu_cortex_m3
    - `setcap_cmd` - Command to set HCI access permissions for zephyr.exe in native mode,
  e.g. sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe. To allow sudo setcap
  without password, add to visudo a line like this: youruser ALL=(ALL) NOPASSWD: /usr/sbin/setcap
    - `hci` - Specify the number of the HCI controller
    - `database_file` - custom path to database .db file (default path: <project-dir>/TestCase.db)
    - `board` - IUT used. Currently nrf52 is supported only
    - `enable_max_logs` - enable debug logs
    - `retry` - maximum repeat count per test
    - `no_retry_on_regression` - When skip_retry is used, failed test cases are handled as follows: if test failure is 
  not a regression, test case will not be retried (i.e. retry is ignored). If the failure is regression, test case  will
  be retried for retry number of times. If you set retry to zero, no failed test cases will be retried.
    - `stress test` - repeat every test `retry` number of times, even if result was PASS
    - `bd_addr` - IUT Bluetooth Address (optional)
    - `recovery` - enable recovery after non-valid result (optional)
    - `superguard` - force recovery when server has been idle for the given time (optional)
    - `ykush` - reconnect board/PTS dongle during recovery, if YKUSH Switchable Hub is used (optional)
    - `ykush_replug_delay` - delay ykush replug
    - `repeat_until_fail` - keep repeating test case until fail verdict
    - `test_case_limit` - limits number of test cases to be run. Useful when passing test group as an argument
    - `pylink_reset' - Use pylink reset
    - `no_build` - Skip build and flash in bot mode
    - `dongle_init_retry` - number of times autoptsserver will try to launch
    - `build_env_cmd` - path to virtual environment needed for build and flash step
    - `copy` - Create a copy of workspace file
    - `wid_usage` - Create a report of wid usage
- `git` - Git repositories configuration (optional)
    - `path` - path to project repo
    - `remote` - git remote repo name
    - `branch` - branch selected at git checkout
    - `stash_changes` - stash changes if local repo is dirty
    - `update_repo` - if False, prevents bot from updating the repo
- `mail` - Mail configuration (optional)
    - `sender` - sender e-mail address
    - `smtp_host`, `smtp_port` - sender SMTP configuration
    - `subject` - overrides default email title
    - `name` - to be used in message footer
    - `passwd` - sender mailbox password. When Google account is used [allow
    less secure apps to access account](https://myaccount.google.com/lesssecureapps)
    - `recipients` - list of e-mail addresses
    - `start_tls` - put SMTP server into TLS mode
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
    - `excluded` - Names of test cases to exclude. Groups of test cases can be specified by profile names.
- `retry_config` - allows to set test-specific retry count. This value overrides
default setting `retry`, allowing to both increase and decrease it. This setting
is in form of dictionary of testcase names and retry counts (as `int`)
* `scheduler` - Scheduler configuration (optional)
    - `weekday`: "time" dictionary.

**Installation**

Install required Python modules with:

    pip3 install --user -r bot/requirements.txt

**Usage**

    ./autoptsclient_bot.py
