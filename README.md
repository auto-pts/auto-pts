# Windows Prerequisites

Since this PTS automation framework uses IronPython it needs COM interop
assembly Interop.PTSConrol.dll to be located in the same directory as the
automation scripts. Currently assembly is provided with auto-pts so you don't
have to generate it yourself.

You need to use 32 bit IronPython to run these scripts because PTS is a 32 bit
application.

To be able to run PTS in automation mode, there should be no PTS instances
running in the GUI mode. Hence, before running these scripts close the PTS GUI.

# PTS workspace setup

Before running any scripts you have to create a workspace in the PTS,
add needed projects to the workspace and configure PICs and PIXITs.

Alternatively, you can use auto-pts workspaces. Auto-pts provides ready PTS
workspaces with readily configured PICS in the "workspaces"
directory. Currently it provides workspaces for the Zephyr HCI
stack. To select ready made workspace pass to the auto-pts client as argument
one of these:

  * zephyr-hci

# Running in client/server mode

The auto-pts framework uses a client server architecture. With this setup the
PTS automation server runs on Windows and the client runs on GNU/Linux. So on
Windows you start the server:

`ipy.exe autoptsserver.py`

And on GNU/Linux you select either the Android or Zephyr client, then pass it
the IP address of the server and the path to the PTS project file on the
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

#Running test script on Windows

It is also possible to run tests on Windows, without using client/server mode
of auto-pts. On Windows instead of starting the auto-pts server start test
script as:

`ipy.exe autopts.py`

autopts.py has been used to test AOSP BlueZ Bluetooth stack, and serves a good
reference on how to create a tester for Windows.

# Generating Interop Assembly

On Windows, run this command:

`TlbImp.exe PTSControl.dll /out:Interop.PTSControl.dll /verbose`

Currently assembly is provided with auto-pts so you don't have to generate it
yourself.