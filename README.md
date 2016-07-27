# Windows Prerequisites

Since this PTS automation framework uses IronPython it needs COM interop
assembly Interop.PTSConrol.dll to be located in the same directory as the
automation scripts.

PTS requires admin rights, therefore you have to run these scripts on Windows
as admin. Basically, you need to run a terminal application as admin and start
the scripts from there.

You need to use 32 bit IronPython to run these scripts because PTS is a 32 bit
application.

To be able to run PTS in automation mode, there should be no PTS instances
running in the GUI mode. Hence, before running these scripts close the PTS GUI.

# Running

Before running any scipts you have to create a workspace in the PTS, add needed
projects to the workspace and configure PICs and PIXITs.

To run standalone Windows PTS automation script:

`ipy.exe autopts.py`

The framework also supports client server architecture. With this setup the PTS
automation server runs on Windows and the client runs on GNU/Linux. So on Windows
you start the server:

`ipy.exe autoptsserver.py`

And on GNU/Linux you select the either the Android or Zephyr client, then pass
it the IP address of the server and the path to the PTS project file on the
Windows machine. So for AOSP BlueZ projects:

`./autoptsclient-aospbluez.py IP_ADDRESS "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6"`

And for Zephyr projects:

Start a proxy for bluetooth adapter by using btproxy from BlueZ:

`sudo bluez/tools/btproxy -u`

Then start the client:

`./autoptsclient-zephyr.py <config>`

# Generating Interop Assembly

On Windows, run this command:

`TlbImp.exe PTSControl.dll /out:Interop.PTSControl.dll /verbose`

# Using configuration file

Configuration file (autoptsclient.conf) contains autoptsclient related symbols and paths used by script.

`PTS_WORKSPACE_PATH` - path to the PTS workspace on PTS Server.

`SERVER_ADDRESS` - autoptsserver workstation IP address

`IUT_INIT_SCRIPT` - Script that will be executed as one of TC pre-run commands. It may be used to e.g. reset IUT etc.

If you have trouble with your configuration, see autoptsclient.conf example:

```
[DEFAULT]
PTS_WORKSPACE_PATH=E:\Users\<user_name>\Documents\Profile Tuning Suite\%(workspace_name)s\%(workspace_name)s.pqw6
SERVER_ADDRESS=192.168.100.1

[config 1]
WORKSPACE_NAME=foo
IUT_INIT_SCRIPT=./<foo_init.sh>

[config 2]
WORKSPACE_NAME=bar
IUT_INIT_SCRIPT=./<bar_init.sh>
```

Example QEMU init script:
```
#!/bin/sh

KERNEL_IMAGE_PATH=<path_to_kernel_image>

qemu-system-arm -cpu cortex-m3 -machine lm3s6965evb -nographic -serial mon:stdio -serial unix:/tmp/bt-server-bredr -serial unix:/tmp/bt-stack-tester -kernel ${KERNEL_IMAGE_PATH}
```
