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

`./autoptsclient-zephyr.py IP_ADDRESS "C:\Users\USER_NAME\Documents\Profile Tuning Suite\PTS_PROJECT\PTS_PROJECT.pqw6"`

# Generating Interop Assembly

On Windows, run this command:

`TlbImp.exe PTSControl.dll /out:Interop.PTSControl.dll /verbose`
