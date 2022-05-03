# BlueZ Support

This page describes the best known method to run AutoPTS with BlueZ and the Bluetooth device on Linux.

Note that the below instruction is tested on Ubuntu 18.04.

## Setup

### Build BlueZ

To test BlueZ with AutoPTS, it needs `btpclient` in addition to BlueZ Daemon. `btpclient` is included in [tools directory of BlueZ source](https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/tools/btpclient.c).

Clone bluez source and build

```bash
git clone https://git.kernel.org/pub/scm/bluetooth/bluez.git
cd bluez
./bootstrap-configure
make
```

### Run BlueZ Daemon

Stop the BlueZ Daemon installed on the system (if it is running) and run `bluetoothd` from the build source.

```bash
sudo systemctl stop bluetooth.service
cd bluez
sudo ./src/bluetoothd -d -E -n
```

## Run

### Running AutoPTS Server (Windows)

Use the `workspaces/bluez/bluez.pts` to create a new workspace(.pqw6).
Then run `autoptsserver.py`

```bash
python autoptsserver.py
```

### Running AutoPTS Client for BlueZ

Once AutoPTS Server is running, run AutoPTS Client.

```text
usage: autoptsclient-bluez.py [-h] [-i IP_ADDR [IP_ADDR ...]]
                              [-l LOCAL_ADDR [LOCAL_ADDR ...]] [-a BD_ADDR]
                              [-d] [-c TEST_CASES [TEST_CASES ...]]
                              [-e EXCLUDED [EXCLUDED ...]] [-r RETRY]
                              [--btpclient_path BTPCLIENT_PATH]
                              workspace

PTS automation client

positional arguments:
  workspace             Path to PTS workspace file to use for testing. It
                        should have pqw6 extension. The file should be located
                        on the machine, where automation server is running.
  btpclient_path        Path to Bluez tool btpclient

optional arguments:
  -h, --help            show this help message and exit
  -i IP_ADDR [IP_ADDR ...], --ip_addr IP_ADDR [IP_ADDR ...]
                        IP address of the PTS automation servers
  -l LOCAL_ADDR [LOCAL_ADDR ...], --local_addr LOCAL_ADDR [LOCAL_ADDR ...]
                        Local IP address of PTS automation client
  -a BD_ADDR, --bd-addr BD_ADDR
                        Bluetooth device address of the IUT
  -d, --debug-logs      Enable the PTS maximum logging. Equivalent to running
                        test case in PTS GUI using 'Run (Debug Logs)'
  -c TEST_CASES [TEST_CASES ...], --test-cases TEST_CASES [TEST_CASES ...]
                        Names of test cases to run. Groups of test cases can
                        be specified by profile names
  -e EXCLUDED [EXCLUDED ...], --excluded EXCLUDED [EXCLUDED ...]
                        Names of test cases to exclude. Groups of test cases
                        can be specified by profile names
  -r RETRY, --retry RETRY
                        Repeat test if failed. Parameter specifies maximum
                        repeat count per test
  --btpclient_path BTPCLIENT_PATH
                        Path to btpclient.
```

### Example

```bash
# Run all GAP test cases.
# AutoPTS Server IP: 192.168.0.18
# Local IP Address:  192.168.0.15
./autoptsclient-bluez.py "C:\Users\tester\Documents\Profile Tuning Suite\bluez\bluez.pqw6" --btpclient_path=/home/han1/work/bluez/tools/btpclient -i 192.168.0.18 -l 192.168.0.15 -c GAP
```

### Logs

AutoPTS Clinet log can be found under `logs` folder.
`btpclient` log is generated to `iut_bluez.log`
