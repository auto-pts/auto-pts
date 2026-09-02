# AutoPTS Configuration

## Table of Contents

- [General](#general)
  - [`config_path`](#config_path)
  - [`iut_mode`](#iut_mode)
  - [`autopts_mode`](#autopts_mode)
  - [`workspace`](#workspace)
  - [`copy_workspace`](#copy_workspace)
  - [`bd_addr`](#bd_addr)
  - [`pts_addr_map`](#pts_addr_map)
  - [`restricted_pts_addrs`](#restricted_pts_addrs)
  - [`pts_addr`](#pts_addr)
  - [`iut_targets`](#iut_targets)
  - [`iut_target_selection`](#iut_target_selection)
- [Connection](#connection)
  - [`srv_port`](#srv_port)
  - [`cli_port`](#cli_port)
  - [`ip_addr`](#ip_addr)
  - [`local_addr`](#local_addr)
  - [`btp_tcp_ip`](#btp_tcp_ip)
  - [`btp_tcp_port`](#btp_tcp_port)
  - [`btpclient_path`](#btpclient_path)
- [Logging](#logging)
  - [`enable_max_logs`](#enable_max_logs)
  - [`btmon`](#btmon)
  - [`rtt_log`](#rtt_log)
  - [`rtt_log_syncto`](#rtt_log_syncto)
- [Recovery](#recovery)
  - [`recovery`](#recovery)
  - [`not_recover`](#not_recover)
  - [`superguard`](#superguard)
  - [`max_server_restart_time`](#max_server_restart_time)
  - [`ykush`](#ykush)
  - [`ykush_replug_delay`](#ykush_replug_delay)
  - [`active_hub_server`](#active_hub_server)
  - [`usb_replug_available`](#usb_replug_available)
  - [`use_backup`](#use_backup)
- [Test Case Execution](#test case execution)
  - [`test_cases`](#test_cases)
  - [`test_cases_file`](#test_cases_file)
  - [`excluded`](#excluded)
  - [`test_case_limit`](#test_case_limit)
  - [`retry`](#retry)
  - [`no_retry_on_regression`](#no_retry_on_regression)
  - [`repeat_until_fail`](#repeat_until_fail)
  - [`stress_test`](#stress_test)
  - [`wid_run`](#wid_run)
  - [`wid_usage`](#wid_usage)
- [Database](#database)
  - [`store`](#store)
  - [`database_file`](#database_file)
- [Hardware](#hardware)
  - [`tty_file`](#tty_file)
  - [`tty_alias`](#tty_alias)
  - [`tty_baudrate`](#tty_baudrate)
  - [`net_tty_file`](#net_tty_file)
  - [`device_core`](#device_core)
  - [`rtscts`](#rtscts)
  - [`debugger_snr`](#debugger_snr)
  - [`board_name`](#board_name)
  - [`pylink_reset`](#pylink_reset)
  - [`btattach_bin`](#btattach_bin)
  - [`btattach_at_every_test_case`](#btattach_at_every_test_case)
  - [`btproxy_bin`](#btproxy_bin)
  - [`external_audio`](#external_audio)
- [QEMU](#qemu)
  - [`qemu_bin`](#qemu_bin)
  - [`qemu_options`](#qemu_options)
  - [`kernel_cpu`](#kernel_cpu)
- [HCI](#hci)
  - [`hci`](#hci)
  - [`hid_vid`](#hid_vid)
  - [`hid_pid`](#hid_pid)
  - [`hid_serial`](#hid_serial)
  - [`btmgmt_bin`](#btmgmt_bin)
  - [`setcap_cmd`](#setcap_cmd)
- [Build](#build)
  - [`project_path`](#project_path)
  - [`tester_app_dir`](#tester_app_dir)
  - [`no_build`](#no_build)
  - [`kernel_image`](#kernel_image)
  - [`project_repos`](#project_repos)
  - [`build_env_cmd`](#build_env_cmd)
- [Other](#other)
  - [`sudo`](#sudo)
  - [`gdb`](#gdb)
  - [`cron_optim`](#cron_optim)
  - [`simple_mode`](#simple_mode)
  - [`server_args`](#server_args)


## General

<a id="config_path"></a>

### `config_path`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `` |
| CLI |  |

#### Description

Path to bot config.py to use for testing.

#### Example

**CLI**
(positional argument)
```bash
'path/to/my_bot_config.py'
```

**Bot config file**
```python
"config_path": 'path/to/my_bot_config.py'
```

<a id="iut_mode"></a>

### `iut_mode`

Specify the mode of the IUT.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| Choices | `tty`, `qemu`, `native`, `btpclient_path` |
| CLI | `--iut-mode`, `--iut_mode` |

#### Description

Specify the mode of the IUT (Identity Under Test). If the option is not provided, mode will be inferred from the parameters.

#### Example

**Bot config file**
```python
"iut_mode": 'None'
```

<a id="autopts_mode"></a>

### `autopts_mode`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `auto_tcp_ip` |
| Choices | `auto_tcp_ip`, `gui_client_only`, `fake_proxy`, `auto_client_only` |
| CLI | `--autopts-mode`, `--autopts_mode` |

#### Description

Specify AutoPTS client mode, which determines the method of communication with the PTS.

#### Example

**Bot config file**
```python
"autopts_mode": 'None'
```

<a id="workspace"></a>

### `workspace`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `` |
| CLI |  |

#### Description

Path to PTS workspace file to use for testing. It should have pqw6 extension. The file should be located on the machine, where automation server is running.

#### Example

**CLI**
(positional argument)
```bash
'autoptsclient-zephyr.py path/to/zephyr.pqw6'
```

**Bot config file**
```python
"workspace": 'path/to/zephyr.pqw6'
```

<a id="copy_workspace"></a>

### `copy_workspace`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `True` |
| CLI | `--nc` |

#### Description

Open the original PTS workspace instead of copying it. Warning: workspace file might be modified by the PTS.

<a id="bd_addr"></a>

### `bd_addr`

Bluetooth device address of the IUT.

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `` |
| CLI | `-a`, `--bd-addr` |

#### Description

Bluetooth device address of the IUT.

#### Example

**CLI**
```bash
-a 12:34:56:65:43:21
```

**Bot config file**
```python
"bd_addr": '12:34:56:65:43:21'
```

<a id="pts_addr_map"></a>

### `pts_addr_map`

| Property | Value |
|----------|-------|
| Type | `dict` |
| Default | `None` |
| CLI | N/A |

#### Description

Mapping of PTS instances to Bluetooth addresses.

#### Example

**Bot config file**
```python
"pts_addr_map": {'GAP/CONN/CPUP/BV-08-C': '12:34:56:65:43:21', 'GAP/CONN/CPUP/BV-10-C': '12:34:56:65:43:21'}
```

<a id="restricted_pts_addrs"></a>

### `restricted_pts_addrs`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | N/A |

#### Description

List of Bluetooth addresses of the PTS dongles that will be used only during test cases specified with pts_addr_map.

#### Example

**Bot config file**
```python
"restricted_pts_addrs": ['12:34:56:65:43:21']
```

<a id="pts_addr"></a>

### `pts_addr`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | N/A |

#### Description

List of Bluetooth addresses of the PTS dongles. Required only for gui_client_only mode.

#### Example

**Bot config file**
```python
"pts_addr": ['12:34:56:65:43:21']
```

<a id="iut_targets"></a>

### `iut_targets`

| Property | Value |
|----------|-------|
| Type | `UnionType[dict, list]` |
| Default | `None` |
| CLI | N/A |

#### Description

Provide a dictionary containing multiple IUT targets configurations. Required for test cases with multiple IUTs.

#### Example

**Bot config file**
```python
"iut_targets": [{'name': 'iut0', 'board': 'nrf54l', 'kernel_cpu': 'native_sim', 'setcap_cmd': 'sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe', 'tty_baudrate': 1000000, 'tty_alias': '/dev/serial/by-id/usb-SEGGER_J-Link_001234567890-if02', 'debugger_snr': '1234567890', 'device_core': 'Cortex-M33', 'build_env_cmd': 'source /path/to/.venv/bin/activate', 'hci': 0, 'active_hub_server': {'ip': '127.0.0.1', 'tcp_port': 65100, 'usb_port': 4, 'replug_delay': 5}, 'btmon': True}, {'name': 'iut1', 'board': 'nrf54l', 'kernel_cpu': 'native_sim', 'setcap_cmd': 'sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe', 'tty_baudrate': 1000000, 'tty_alias': '/dev/serial/by-id/usb-SEGGER_J-Link_009876543210-if02', 'debugger_snr': '9876543210', 'device_core': 'Cortex-M33', 'build_env_cmd': 'source /path/to/.venv/bin/activate', 'hci': 1, 'btmon': True}]
```

<a id="iut_target_selection"></a>

### `iut_target_selection`

| Property | Value |
|----------|-------|
| Type | `UnionType[dict, str]` |
| Default | `None` |
| CLI | `--iut_target_selection` |

#### Description

Mapping of IUT targets to specific test cases. Specify a dictionary with the mappingor a path to a JSON file containing the dictionary.

#### Example

**CLI**
```bash
--iut_target_selection path/to/targets.json
```

**Bot config file**
```python
"iut_target_selection": {'default_iut_map': {0: 'iut0'}, 'rules': [{'iut_map': {0: 'iut1'}, 'test_cases': ['GAP/CONN/CPUP/BV-08-C', 'GAP/CONN/CPUP/BV-10-C']}, {'iut_map': {0: 'iut1', 1: 'iut0'}, 'test_cases': ['CSIP/SR/SP/BV-06-C']}]}
```


## Connection

<a id="srv_port"></a>

### `srv_port`

| Property | Value |
|----------|-------|
| Type | `list[int]` |
| Default | `[65000]` |
| CLI | `-S`, `--srv_port` |

#### Description

Ports of the interface exposed by the AutoPTS servers. One port corresponds to one PTS instance.

#### Example

**CLI**
```bash
-S 65000 65002 65004
```

**Bot config file**
```python
"srv_port": [65000, 65002, 65004]
```

<a id="cli_port"></a>

### `cli_port`

| Property | Value |
|----------|-------|
| Type | `list[int]` |
| Default | `[65001]` |
| CLI | `-C`, `--cli_port` |

#### Description

Ports of the callback interface exposed by AutoPTS client. One port corresponds to one PTS instance.

#### Example

**CLI**
```bash
-C 65001 65003 65005
```

**Bot config file**
```python
"cli_port": [65001, 65003, 65005]
```

<a id="ip_addr"></a>

### `ip_addr`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `-i`, `--ip_addr` |

#### Description

IP addresses of the interface exposed by the AutoPTS servers. One IP corresponds to one PTS instance.

#### Example

**CLI**
```bash
-i 192.168.2.2 192.168.2.2
```

**Bot config file**
```python
"ip_addr": '192.168.2.2 192.168.2.2'
```

<a id="local_addr"></a>

### `local_addr`

Local IP addresses of the AutoPTS client.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `-l`, `--local_addr` |

#### Description

Local IP addresses of the interface exposed by the AutoPTS servers. One IP corresponds to one PTS instance.

#### Example

**CLI**
```bash
-l 192.168.2.1 192.168.2.1
```

**Bot config file**
```python
"local_addr": '192.168.2.1 192.168.2.1'
```

<a id="btp_tcp_ip"></a>

### `btp_tcp_ip`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `127.0.0.1` |
| IUT parameter | Yes |
| CLI | `--btp-tcp-ip`, `--btp_tcp_ip` |

#### Description

IP address of the external BTP client.

#### Example

**CLI**
```bash
--btp-tcp-ip 127.0.0.1
```

**Bot config file**
```python
"btp_tcp_ip": '127.0.0.1'
```

<a id="btp_tcp_port"></a>

### `btp_tcp_port`

| Property | Value |
|----------|-------|
| Type | `list[int]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--btp-tcp-port`, `--btp_tcp_port` |

#### Description

TCP port used by the external BTP client.

#### Example

**CLI**
```bash
--btp-tcp-port 9000
```

**Bot config file**
```python
"btp_tcp_port": '9000'
```

<a id="btpclient_path"></a>

### `btpclient_path`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--btpclient-path`, `--btpclient_path` |

#### Description

Path to the external BTP client executable.

#### Example

**CLI**
```bash
--btpclient-path /path/to/btpclient
```

**Bot config file**
```python
"btpclient_path": '/path/to/btpclient'
```


## Logging

<a id="enable_max_logs"></a>

### `enable_max_logs`

Enable PTS maximum logging.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `-d`, `--debug-logs` |

#### Description

Enable the PTS maximum logging. Equivalent to running test case in PTS GUI using 'Run (Debug Logs)'.

#### Example

**Bot config file**
```python
"enable_max_logs": True
```

<a id="btmon"></a>

### `btmon`

Capture btmon logs.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--btmon` |

#### Description

Capture btsnoop logs over RTT and decode them with btmon. Requires RTT support on the IUT.

#### Example

**Bot config file**
```python
"btmon": True
```

<a id="rtt_log"></a>

### `rtt_log`

Capture RTT logs.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--rtt-log` |

#### Description

Capture IUT logs from the RTT buffer. Requires RTT support on the IUT.

#### Example

**Bot config file**
```python
"rtt_log": True
```

<a id="rtt_log_syncto"></a>

### `rtt_log_syncto`

| Property | Value |
|----------|-------|
| Type | `float` |
| Default | `0` |
| IUT parameter | Yes |
| CLI | `--rtt-log-syncto` |

#### Description

Continue RTT logging for the specified number of seconds after the test case finishes.

#### Example

**CLI**
```bash
--rtt-log-syncto 5
```

**Bot config file**
```python
"rtt_log_syncto": '5'
```


## Recovery

<a id="recovery"></a>

### `recovery`

Enable automatic recovery.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--recovery` |

#### Description

Specify if autoptsclient should try to recover itself after a negative test status.

#### Example

**Bot config file**
```python
"recovery": True
```

<a id="not_recover"></a>

### `not_recover`

Statuses that should not trigger recovery.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `['PASS', 'INCONC', 'FAIL', 'NOT_IMPLEMENTED', 'INDCSV']` |
| CLI | `--not_recover` |

#### Description

Specify test statuses for which autoptsclient should not attempt recovery.

#### Example

**CLI**
```bash
--not_recover "PASS" "BTP ERROR"
```

**Bot config file**
```python
"not_recover": ['PASS', 'BTP ERROR']
```

<a id="superguard"></a>

### `superguard`

Recovery timeout in minutes.

| Property | Value |
|----------|-------|
| Type | `float` |
| Default | `0` |
| CLI | `--superguard` |

#### Description

Specify the amount of time in minutes after which SuperGuard will trigger recovery steps.

#### Example

**CLI**
```bash
--superguard 15
```

**Bot config file**
```python
"superguard": '15'
```

<a id="max_server_restart_time"></a>

### `max_server_restart_time`

| Property | Value |
|----------|-------|
| Type | `int` |
| Default | `120` |
| CLI | `--max_server_restart_time` |

#### Description

Maximum time allowed for restarting the automation server.

#### Example

**CLI**
```bash
--max_server_restart_time 120
```

**Bot config file**
```python
"max_server_restart_time": '120'
```

<a id="ykush"></a>

### `ykush`

YKUSH ports used during recovery.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--ykush` |

#### Description

Specify YKUSH downstream port numbers used during recovery to power cycle the IUT device.

#### Example

**CLI**
```bash
--ykush 1 3
```

**Bot config file**
```python
"ykush": '1 3'
```

<a id="ykush_replug_delay"></a>

### `ykush_replug_delay`

| Property | Value |
|----------|-------|
| Type | `list[float]` |
| Default | `3` |
| IUT parameter | Yes |
| CLI | `--ykush_replug_delay` |

#### Description

Time needed for the device to cool down after YKUSH power off.

#### Example

**CLI**
```bash
--ykush_replug_delay 3
```

**Bot config file**
```python
"ykush_replug_delay": '3'
```

<a id="active_hub_server"></a>

### `active_hub_server`

| Property | Value |
|----------|-------|
| Type | `list[dict]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | N/A |

#### Description

Configuration of an external active USB hub server.

#### Example

**Bot config file**
```python
"active_hub_server": {'ip': '127.0.0.1', 'tcp_port': 65100, 'usb_port': 4, 'replug_delay': 5}
```

<a id="usb_replug_available"></a>

### `usb_replug_available`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--usb-replug-available`, `--usb_replug_available` |

#### Description

Specify whether USB replug functionality is available.

#### Example

**Bot config file**
```python
"usb_replug_available": True
```

<a id="use_backup"></a>

### `use_backup`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | N/A |

#### Description

The bot collects a backup of the stats, so in case of unexpected termination the bot can continue the test series from the test case where it was interrupted. Useful with a cron that can detect the bot's crash or freeze and restart it automatically.

#### Example

**Bot config file**
```python
"use_backup": True
```


## Test Case Execution

<a id="test_cases"></a>

### `test_cases`

Names of test cases to run.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `-c`, `--test-cases` |

#### Description

Names of test cases to run. Groups of test cases can be specified by profile names. Option can be used multiple times.

#### Example

**CLI**
```bash
-c GAP/BROB/BCST/BV-01-C GAP/CONN
```

**Bot config file**
```python
"test_cases": ['GAP/BROB/BCST/BV-01-C', 'GAP/CONN']
```

<a id="test_cases_file"></a>

### `test_cases_file`

Read test cases from a file.

| Property | Value |
|----------|-------|
| Type | `Path` |
| Default | `None` |
| CLI | `--test-cases-file` |

#### Description

A file containing test case names, one per line. Use instead of the --test-cases/-c option.

#### Example

**CLI**
```bash
--test-cases-file path/to/testcases.txt
```

**Bot config file**
```python
"test_cases_file": 'path/to/testcases.txt'
```

<a id="excluded"></a>

### `excluded`

Names of test cases to exclude.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `-e`, `--excluded` |

#### Description

Names of test cases to exclude. Groups of test cases can also be specified by profile names.

#### Example

**CLI**
```bash
-e GAP/BROB/BCST/BV-01-C GAP/CONN
```

**Bot config file**
```python
"excluded": ['GAP/BROB/BCST/BV-01-C', 'GAP/CONN']
```

<a id="test_case_limit"></a>

### `test_case_limit`

Maximum number of test cases to execute.

| Property | Value |
|----------|-------|
| Type | `int` |
| Default | `0` |
| CLI | `--test_case_limit` |

#### Description

Limit the number of executed test cases. All remaining test cases will be skipped.

#### Example

**CLI**
```bash
--test_case_limit 100
```

**Bot config file**
```python
"test_case_limit": 100
```

<a id="retry"></a>

### `retry`

Retry failed test cases.

| Property | Value |
|----------|-------|
| Type | `int` |
| Default | `0` |
| CLI | `-r`, `--retry` |

#### Description

Repeat a failed test case. The value specifies the maximum number of retries per test case.

#### Example

**CLI**
```bash
-r 3
```

**Bot config file**
```python
"retry": 3
```

<a id="no_retry_on_regression"></a>

### `no_retry_on_regression`

Retry only regression failures.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--no_retry_on_regression` |

#### Description

Retry failed test cases only if the failure is considered a regression. Non-regression failures are not retried even when the retry count is greater than zero.

#### Example

**Bot config file**
```python
"no_retry_on_regression": True
```

<a id="repeat_until_fail"></a>

### `repeat_until_fail`

Repeat until a test no longer passes.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--repeat_until_fail` |

#### Description

Repeat each test case until the verdict is different from PASS.

#### Example

**Bot config file**
```python
"repeat_until_fail": True
```

<a id="stress_test"></a>

### `stress_test`

Repeat all test cases. The repeat counter will be set to 'retry' parameter value.

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--stress_test` |

#### Description

Repeat every test case even if the previous execution passed. The repeat counter will be set to 'retry' parameter value.

#### Example

**Bot config file**
```python
"stress_test": True
```

<a id="wid_run"></a>

### `wid_run`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `--wid_run`, `--wid-run` |

#### Description

Run all test cases from the selected service/profile that use the specified WID.

#### Example

**CLI**
```bash
--wid_run GAP 35
```

**Bot config file**
```python
"wid_run": 'GAP 35'
```

<a id="wid_usage"></a>

### `wid_usage`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | N/A |

#### Description

Generate a csv wid report with specific wids and tests using them.

#### Example

**Bot config file**
```python
"wid_usage": True
```


## Database

<a id="store"></a>

### `store`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `-s`, `--store` |

#### Description

Enable storing test results in TestCase.db.

#### Example

**Bot config file**
```python
"store": True
```

<a id="database_file"></a>

### `database_file`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `TestCase.db` |
| CLI | `--database-file` |

#### Description

Path to the SQLite database file used for test results.

#### Example

**CLI**
```bash
--database-file TestCase.db
```

**Bot config file**
```python
"database_file": 'TestCase.db'
```


## Hardware

<a id="tty_file"></a>

### `tty_file`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `-t`, `--tty-file` |

#### Description

Use the specified TTY/COM device for BTP communication with the IUT. QEMU and HCI modes are disabled when this option is used.

#### Example

**CLI**
```bash
-t /dev/ttyACM0
```

**Bot config file**
```python
"tty_file": '/dev/ttyACM0'
```

<a id="tty_alias"></a>

### `tty_alias`

TTY alias(es) to be resolved.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `` |
| IUT parameter | Yes |
| CLI | `--tty_alias` |

#### Example

**CLI**
```bash
--tty_alias /dev/serial/by-id/usb-SEGGER_J-Link_001234567890-if02
```

**Bot config file**
```python
"tty_alias": '/dev/serial/by-id/usb-SEGGER_J-Link_001234567890-if02'
```

<a id="tty_baudrate"></a>

### `tty_baudrate`

TTY baudrate.

| Property | Value |
|----------|-------|
| Type | `list[int]` |
| Default | `115200` |
| IUT parameter | Yes |
| CLI | `--tty-baudrate`, `--tty_baudrate` |

#### Description

Baudrate used for TTY communication.

#### Example

**CLI**
```bash
--tty-baudrate 115200
```

**Bot config file**
```python
"tty_baudrate": 115200
```

<a id="net_tty_file"></a>

### `net_tty_file`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--net-tty-file` |

#### Description

TTY/COM device used to capture logs from the network core, if the board exposes a separate serial port.

#### Example

**CLI**
```bash
--net-tty-file /dev/ttyACM1
```

**Bot config file**
```python
"net_tty_file": '/dev/ttyACM1'
```

<a id="device_core"></a>

### `device_core`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `NRF52840_XXAA` |
| IUT parameter | Yes |
| CLI | `--device_core` |

#### Description

Device core used for J-Link related features such as RTT logging and btmon.

#### Example

**CLI**
```bash
--device_core NRF52840_XXAA
```

**Bot config file**
```python
"device_core": 'NRF52840_XXAA'
```

<a id="rtscts"></a>

### `rtscts`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--rtscts` |

#### Description

Enable UART RTS/CTS hardware flow control.

#### Example

**Bot config file**
```python
"rtscts": True
```

<a id="debugger_snr"></a>

### `debugger_snr`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `-j`, `--jlink` |

#### Description

Specify the J-Link serial number manually.

#### Example

**CLI**
```bash
-j 1050123456
```

**Bot config file**
```python
"debugger_snr": '1050123456'
```

<a id="board_name"></a>

### `board_name`

Board name.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `-b`, `--board` |

#### Description

Board used for testing. The selected board determines the board-specific reset and build/flash implementation.

#### Example

**Bot config file**
```python
"board_name": 'None'
```

<a id="pylink_reset"></a>

### `pylink_reset`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--pylink_reset` |

#### Description

Use pylink reset for board recovery/reset.

#### Example

**Bot config file**
```python
"pylink_reset": True
```

<a id="btattach_bin"></a>

### `btattach_bin`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--btattach-bin`, `--btattach_bin` |

#### Description

Path to the btattach executable.

#### Example

**CLI**
```bash
--btattach-bin /usr/bin/btattach
```

**Bot config file**
```python
"btattach_bin": '/usr/bin/btattach'
```

<a id="btattach_at_every_test_case"></a>

### `btattach_at_every_test_case`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--btattach-at-every-test-case`, `--btattach_at_every_test_case` |

#### Description

Restart btattach before executing every test case.

#### Example

**Bot config file**
```python
"btattach_at_every_test_case": True
```

<a id="btproxy_bin"></a>

### `btproxy_bin`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| CLI | `--btproxy-bin`, `--btproxy_bin` |

#### Description

Path to the btproxy executable.

#### Example

**CLI**
```bash
--btproxy-bin /usr/bin/btproxy
```

**Bot config file**
```python
"btproxy_bin": '/usr/bin/btproxy'
```

<a id="external_audio"></a>

### `external_audio`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| CLI | `--external-audio` |

#### Description

Type of external audio support to use.

#### Example

**CLI**
```bash
--external-audio wireplumber
```

**Bot config file**
```python
"external_audio": 'wireplumber'
```


## QEMU

<a id="qemu_bin"></a>

### `qemu_bin`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--qemu-bin`, `--qemu_bin` |

#### Description

Path to the QEMU executable.

#### Example

**CLI**
```bash
--qemu-bin /usr/bin/qemu-system-arm
```

**Bot config file**
```python
"qemu_bin": '/usr/bin/qemu-system-arm'
```

<a id="qemu_options"></a>

### `qemu_options`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `` |
| IUT parameter | Yes |
| CLI | `--qemu-options`, `--qemu_options` |

#### Description

Additional command line options passed to QEMU.

#### Example

**CLI**
```bash
--qemu-options -cpu cortex-m3 -machine lm3s6965evb
```

**Bot config file**
```python
"qemu_options": '-cpu cortex-m3 -machine lm3s6965evb'
```

<a id="kernel_cpu"></a>

### `kernel_cpu`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `qemu_cortex_m3` |
| IUT parameter | Yes |
| CLI | `--kernel-cpu`, `--kernel_cpu` |

#### Description

CPU type used when building the kernel image.

#### Example

**CLI**
```bash
--kernel-cpu qemu_cortex_m3
```

**Bot config file**
```python
"kernel_cpu": 'qemu_cortex_m3'
```


## HCI

<a id="hci"></a>

### `hci`

| Property | Value |
|----------|-------|
| Type | `list[int]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--hci` |

#### Description

Specify the HCI controller number.

#### Example

**CLI**
```bash
--hci 0
```

**Bot config file**
```python
"hci": '0'
```

<a id="hid_vid"></a>

### `hid_vid`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--hid-vid`, `--hid_vid` |

#### Description

Specify the USB vendor ID of the HCI controller (hexadecimal string).

#### Example

**CLI**
```bash
--hid-vid 2fe3
```

**Bot config file**
```python
"hid_vid": '2fe3'
```

<a id="hid_pid"></a>

### `hid_pid`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--hid-pid`, `--hid_pid` |

#### Description

Specify the USB product ID of the HCI controller (hexadecimal string).

#### Example

**CLI**
```bash
--hid-pid 000b
```

**Bot config file**
```python
"hid_pid": '000b'
```

<a id="hid_serial"></a>

### `hid_serial`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--hid-serial`, `--hid_serial` |

#### Description

Specify the USB serial number of the HCI controller.

#### Example

**CLI**
```bash
--hid-serial 1234567890123456
```

**Bot config file**
```python
"hid_serial": '1234567890123456'
```

<a id="btmgmt_bin"></a>

### `btmgmt_bin`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--btmgmt-bin`, `--btmgmt_bin` |

#### Description

Path to the btmgmt executable.

#### Example

**CLI**
```bash
--btmgmt-bin /usr/bin/btmgmt
```

**Bot config file**
```python
"btmgmt_bin": '/usr/bin/btmgmt'
```

<a id="setcap_cmd"></a>

### `setcap_cmd`

Command used to grant HCI capabilities.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--setcap-cmd`, `--setcap_cmd` |

#### Description

Command used to grant the required Linux capabilities for native HCI mode (for example using setcap).

#### Example

**CLI**
```bash
--setcap-cmd sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe
```

**Bot config file**
```python
"setcap_cmd": 'sudo /usr/sbin/setcap cap_net_raw,cap_net_admin,cap_sys_admin+ep /path/to/zephyr.exe'
```


## Build

<a id="project_path"></a>

### `project_path`

Project repository path.

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| IUT parameter | Yes |
| CLI | `--project_path` |

#### Description

Absolute path to the project repository containing sources needed to build the tester application.

#### Example

**CLI**
```bash
--project_path path/to/tester/dir
```

**Bot config file**
```python
"project_path": 'path/to/tester/dir'
```

<a id="tester_app_dir"></a>

### `tester_app_dir`

Tester application directory.

| Property | Value |
|----------|-------|
| Type | `Path` |
| Default | `tests/bluetooth/tester` |
| CLI | `--tester_app_dir` |

#### Description

Path to the tester application relative to project_path. Used for build and flash in bot mode.

#### Example

**CLI**
```bash
--tester_app_dir path/to/tester/dir
```

**Bot config file**
```python
"tester_app_dir": 'path/to/tester/dir'
```

<a id="no_build"></a>

### `no_build`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--nb` |

#### Description

Skip build and flash steps in bot mode.

#### Example

**Bot config file**
```python
"no_build": True
```

<a id="kernel_image"></a>

### `kernel_image`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | `--kernel-image`, `--kernel_image` |

#### Description

OS kernel image to be used for testing, e.g. elf file for qemu, exe for native.

#### Example

**CLI**
(positional argument)
```bash
'autoptsclient-zephyr.py path/to/zephyr.pqw6 path/to/zephyr.exe'
```

**Bot config file**
```python
"kernel_image": 'path/to/zephyr.exe'
```

<a id="project_repos"></a>

### `project_repos`

| Property | Value |
|----------|-------|
| Type | `list[str]` |
| Default | `None` |
| CLI | N/A |

#### Description

An additional argument that is used for build and flash stage. Its usage is board-specific.

#### Example

**Bot config file**
```python
"project_repos": ['path/to/repo1', 'path/to/repo2']
```

<a id="build_env_cmd"></a>

### `build_env_cmd`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| CLI | N/A |

#### Description

Add the `build_env_cmd` option to allow configuring a shell command that activates the environment before running `west build` or `west flash`.

#### Example

**Bot config file**
```python
"build_env_cmd": 'source ~/zephyrproject/.venv/bin/activate'
```


## Other

<a id="sudo"></a>

### `sudo`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | `--sudo` |

#### Description

Allow running with with elevated privileges.

#### Example

**Bot config file**
```python
"sudo": True
```

<a id="gdb"></a>

### `gdb`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| IUT parameter | Yes |
| CLI | `--gdb` |

#### Description

Skip board resets to avoid disconnecting the GDB server.

#### Example

**Bot config file**
```python
"gdb": True
```

<a id="cron_optim"></a>

### `cron_optim`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | N/A |

#### Description

Terminate PTS.exe and Fts.exe before pulling PTS logs from autopts server

#### Example

**Bot config file**
```python
"cron_optim": True
```

<a id="simple_mode"></a>

### `simple_mode`

| Property | Value |
|----------|-------|
| Type | `bool` |
| Default | `False` |
| CLI | N/A |

#### Description

Start testing with the simple client layer. Allows for using bot config file without entering Bot layers, so it skips build-and-flash stage and postprocessing logs.

#### Example

**Bot config file**
```python
"simple_mode": True
```

<a id="server_args"></a>

### `server_args`

| Property | Value |
|----------|-------|
| Type | `str` |
| Default | `None` |
| CLI | N/A |

#### Description

autopts server arguments used in AUTO_CLIENT_ONLY mode.

#### Example

**Bot config file**
```python
"server_args": '-S 65000 65002'
```
