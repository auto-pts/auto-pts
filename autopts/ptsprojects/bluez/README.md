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

### Using PipeWire for audio

By default the tests run with BlueZ in standalone mode. For audio-related profiles you can route audio through PipeWire instead.
To do this, configure your system WirePlumber (the PipeWire session manager) instance with Bluetooth audio disabled so it does
not claim Bluetooth devices, and start the Auto-PTS client with `--external-audio=wireplumber`:

```bash
./autoptsclient-bluez.py "C:\Users\tester\Documents\Profile Tuning Suite\bluez\bluez.pqw6" --btpclient_path=/home/han1/work/bluez/tools/btpclient -i 192.168.0.18 -l 192.168.0.15 --external-audio=wireplumber -c BAP
```

For each test case, the test harness will automatically start and stop a secondary WirePlumber instance using specific
configurations. This test-managed WirePlumber instance is separate from your system-wide PipeWire session and handles Bluetooth
audio for the duration of that individual test case.

Note:

- During development phase, Auto-PTS or PipeWire developers can run tests with a locally built (uninstalled) PipeWire by starting
  the build-provided shell in the PipeWire source directory and running the Auto-PTS client from that shell:

  ```bash
  cd /path/to/pipewire
  make shell
  # inside the make-provided shell, run the client as before
  cd /path/to/auto-pts
  ./autoptsclient-bluez.py "C:\Users\tester\Documents\Profile Tuning Suite\bluez\bluez.pqw6" --btpclient_path=/home/han1/work/bluez/tools/btpclient -i 192.168.0.18 -l 192.168.0.15 --external-audio=wireplumber -c BAP
  ```

#### Sample WirePlumber Bluetooth disabling configuration
For a system install place the file under `~/.config/wireplumber/wireplumber.conf.d/disable-bluetooth.conf`.
During PipeWire development place it in the PipeWire source tree at `</path/to/pipewire>/subprojects/wireplumber/src/config/wireplumber.conf.d/disable-bluetooth.conf`.

The file contents should be:
```conf
wireplumber.profiles = {
  main = {
    hardware.bluetooth = disabled
  }
}
```

### Logs

AutoPTS Client log can be found under `logs` folder.
`btpclient` log is generated to `iut-bluez.log`, PipeWire/WirePlumber log is generated to `iut-bluez-audio.log`.
