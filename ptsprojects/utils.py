import logging
import subprocess

# make sure adb is in path or modify this variable
ADB = "adb.exe"
USE_ADB = True

log = logging.debug

class btmgmt:
    """Incomplete wrapper around btmgmt. The methods are added as needed."""

    @staticmethod
    def power_off():
        exec_iut_cmd("btmgmt power off", True)

    @staticmethod
    def power_on():
        exec_iut_cmd("btmgmt power on", True)

    @staticmethod
    def advertising_on():
        exec_iut_cmd("btmgmt advertising on", True)

    @staticmethod
    def advertising_off():
        exec_iut_cmd("btmgmt advertising off", True)

    @staticmethod
    def connectable_on():
        exec_iut_cmd("btmgmt connectable on", True)

    @staticmethod
    def connectable_off():
        exec_iut_cmd("btmgmt connectable off", True)

    @staticmethod
    def bondable_on():
        exec_iut_cmd("btmgmt bondable on", True)

    @staticmethod
    def bondable_off():
        exec_iut_cmd("btmgmt bondable off", True)

    @staticmethod
    def discoverable_on():
        exec_iut_cmd("btmgmt discov on", True)

    @staticmethod
    def discoverable_off():
        exec_iut_cmd("btmgmt discov off", True)

    @staticmethod
    def discoverable_limited(limit):
        exec_iut_cmd("btmgmt discov limited %d" % limit, True)

    @staticmethod
    def bredr_on():
        exec_iut_cmd("btmgmt bredr on", True)

    @staticmethod
    def bredr_off():
        exec_iut_cmd("btmgmt bredr off", True)

def exec_iut_cmd(iut_cmd, wait = False, use_adb_shell = USE_ADB):
    """Runs command in the IUT"""
    if use_adb_shell:
        cmd = "%s shell %s" % (ADB, iut_cmd)
    else:
        cmd = iut_cmd

    process = subprocess.Popen(cmd,
                               stdout = subprocess.PIPE,
                               stderr = subprocess.STDOUT)

    process_desc = "%s pid %s" % (repr(cmd), process.pid)

    log("started child process %s" % process_desc)

    # TODO: communicate waits, this means output of not waited commands is not
    # logged, using logging.root.handlers[0].stream as stdout and stderr when
    # creating process causes exceptions "IOError: System.IO.IOException: The
    # OS handle's position is not what FileStream expected.". So find a trivial
    # way to log the output of non-blocking (wait is False) processes
    if wait:
        output = process.communicate()[0]
        if output:
            log("child process %s output:\n%s", process_desc, output)

    return process

def exec_adb_root():
    """Runs 'adb root' in Android IUT. This is needed cause IUT commands require
    root permissions"""
    if not USE_ADB:
        return

    """Runs "adb root" command"""
    exec_iut_cmd("adb root", True, False)
    # it takes an instance of time to get adbd restarted with root permissions
    exec_iut_cmd("adb wait-for-device", True, False)
