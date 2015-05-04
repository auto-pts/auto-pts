"""PTS automation IronPython script

To use it you have to have installed COM interop assembly to the bin directory
of PTS, like:

cp Interop.PTSConrol.dll C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\bin\

Since PTS requires admin rights, you have to run this script as admin. You need
to use 32 bit IronPython to run this script because PTS is a 32 bit
application.

Run this is script in admin terminal as follows:

ipy.exe autopts.py

"""

import os
import sys
import time
import logging
import argparse
import subprocess

import ctypes
libc = ctypes.cdll.msvcrt # for wcscpy_s

import ptscontrol

# make sure adb is in path or modify this variable
ADB = "adb.exe"
USE_ADB = True

# instance of ptscontrol.PyPTS
PTS = None

log = logging.debug

class TestCmd:
    """A command ran in IUT during test case execution"""

    def __init__(self, command, start_wid = None, stop_wid = None):
        """stop_wid - some test cases require the child process (this test command) to
                      be termintated (Ctrl-C on terminal) in response to dialog
                      with this wid
        """
        self.command = command
        self.start_wid = start_wid
        self.stop_wid = stop_wid
        self.process = None
        self.__started = False

    def start(self):
        if self.__started:
            return

        self.__started = True

        log("starting child process %s" % self)
        self.process = exec_iut_cmd(self.command)

    def stop(self):
        if not self.__started:
            return

        log("stopping child process %s" % self)
        self.process.kill()

    def __str__(self):
        return "%s %s %s" % (self.command, self.start_wid, self.stop_wid)

class TestFunc:
    """Some test commands, like setting PIXIT, PICS are functions. This is a
    wrapper around functions"""
    def __init__(self, func, *args, **kwds):
        self.__func = func
        self.__args = args
        self.__kwds = kwds
        self.start_wid = None
        self.stop_wid = None

    def start(self):
        log("Starting test function: %s" % str(self))
        self.__func(*self.__args, **self.__kwds)

    def stop(self):
        pass

    def __str__(self):
        return "%s %s %s" % (self.__func, self.__args, self.__kwds)

class TestFuncCleanUp(TestFunc):
    """Clean-up function that is invoked after running test case in PTS."""
    pass

def is_cleanup_func(func):
    """'Retruns True if func is an in an instance of TestFuncCleanUp"""
    return isinstance(func, TestFuncCleanUp)

class TestCase:
    def __init__(self, project_name, test_case_name, cmds = [], no_wid = None):
        """cmds - a list of TestCmd and TestFunc or single instance of them
        no_wid - a wid (tag) to respond No to"""
        self.project_name = project_name
        self.name = test_case_name
        # a.k.a. final verdict
        self.status = "init"

        if isinstance(cmds, list):
            self.cmds = cmds
        else:
            self.cmds = [cmds]

        if no_wid is not None and not isinstance(no_wid, int):
            raise Exception("no_wid should be int, and not %s" % (repr(no_wid),))

        self.no_wid = no_wid

    def __str__(self):
        return "%s %s" % (self.project_name, self.name)

    def on_implicit_send(self, project_name, wid, test_case_name, description, style,
                         response, response_size, response_is_present):

        log("%s %s", self, self.on_implicit_send.__name__)

        # this should never happen, pts does not run tests in parallel
        assert project_name == self.project_name and \
            test_case_name == self.name

        response_is_present.Value = 1

        # MMI_Style_Yes_No1
        if style == 0x11044:
            # answer No
            if self.no_wid and wid == self.no_wid:
                libc.wcscpy_s(response, response_size, u"No")

            # answer Yes
            else:
                libc.wcscpy_s(response, response_size, u"Yes")

        # actually style == 0x11141, MMI_Style_Ok_Cancel2
        else:
            libc.wcscpy_s(response, response_size, u"OK")

        # start/stop command if triggered by wid
        for cmd in self.cmds:
            # start command
            if cmd.start_wid == wid:
                cmd.start()

            # stop command
            if cmd.stop_wid == wid:
                cmd.stop()

    def run(self):

        log("About to run test case %s %s with commands:" %
            (self.project_name, self.name))
        for cmd in self.cmds:
            log(cmd)

        # start commands that don't have start trigger (lack start_wid) and are
        # not cleanup functions
        for cmd in self.cmds:
            if cmd.start_wid is None and not is_cleanup_func(cmd):
                cmd.start()

        log("Running test case %s %s" % (self.project_name, self.name))
        PTS.run_test_case_object(self)
        log("Done Running test case %s %s" % (self.project_name, self.name))

        # run the clean-up commands
        for cmd in self.cmds:
            if is_cleanup_func(cmd):
                cmd.start()

        # in accordance with PTSControlClient.cpp:
        # // Allow device to settle down
        # Sleep(3000);
        # otherwise 4th test case just blocks eternally
        time.sleep(3)

        for cmd in self.cmds:
            cmd.stop()

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
    """Runs "adb root" command"""
    exec_iut_cmd("adb root", True, False)
    # it takes an instance of time to get adbd restarted with root permissions
    exec_iut_cmd("adb wait-for-device", True, False)

def get_test_cases_l2cap():
    """Initial IUT config: powered connectable br/edr le advertising
    Bluetooth in UI should be turned off then:

    Not needed for Nexus 7
    echo 1 > /sys/class/rfkill/rfkill0/state

    setprop ctl.start hciattach
    btmgmt le on
    btmgmt connectable on
    btmgmt advertising on
    btmgmt ssp on
    btmgmt power on

    PIXIT TSPX_delete_link_key must be set to TRUE, that is cause in automation
    there is no API call respective to the "Delete Link Key" PTS toolbar
    button.

    """


    test_cases = [
        TestCase("L2CAP", "TC_COS_CED_BV_01_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_03_C",
                 TestCmd("l2test -y -N 1 -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_04_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),

        # TODO: PTS issue #12351
        # the command is
        # btmgmt power off && btmgmt ssp off && btmgmt power on && l2test -r -P 4113 00:1B:DC:07:32:03 && btmgmt ssp on
        #
        # for some reason without power off I get
        # "Set Secure Simple Pairing for hci0 failed with status 0x0a (Busy)"
        # so problem with that command also ssp on won't run before l2test is killed, which
        # will kill whole command
        #
        # Hence, support for multiple commands is needed
        # run_test_case("L2CAP", "TC_COS_CED_BV_05_C", "btmgmt ssp off;l2test -r -P 4113 %s; btmgmt ssp on" % (PTS.bd_addr(),))
        TestCase("L2CAP", "TC_COS_CED_BV_07_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13)),
        TestCase("L2CAP", "TC_COS_CED_BV_08_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13)),
        TestCase("L2CAP", "TC_COS_CED_BV_09_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CED_BV_11_C",
                 TestCmd("l2test -u -P 4113 %s" % PTS.bd_addr(), start_wid = 13)),

        TestCase("L2CAP", "TC_COS_CED_BI_01_C"),

        # TODO: just like TC_COS_CED_BV_05_C
        # TestCase("L2CAP", "TC_COS_CFD_BV_01_C")
        TestCase("L2CAP", "TC_COS_CFD_BV_02_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_03_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_08_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_09_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_11_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_CFD_BV_12_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_COS_IEX_BV_01_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_IEX_BV_02_C"),

        TestCase("L2CAP", "TC_COS_ECH_BV_01_C"),
        TestCase("L2CAP", "TC_COS_ECH_BV_02_C",
                 TestCmd("l2ping -c1 %s" % PTS.bd_addr(), start_wid = 26)),

        TestCase("L2CAP", "TC_COS_CFC_BV_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -y -N 1 -b 40 -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22)]),
        TestCase("L2CAP", "TC_COS_CFC_BV_02_C",
                 TestCmd("l2test -y -N 1 -b 1 -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_CFC_BV_03_C",
                 TestCmd("l2test -u -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_COS_CFC_BV_04_C",
                 [TestCmd("l2test -u -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22),
                  TestFunc(btmgmt.advertising_on)]),
    
        # TODO: this one requiers two l2test processes
        # TestCase("L2CAP", "TC_COS_CFC_BV_05_C", "l2test -u -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22),

        TestCase("L2CAP", "TC_CLS_UCD_BV_01_C"),
        TestCase("L2CAP", "TC_CLS_UCD_BV_02_C",
                 TestCmd("l2test -s -G -N 1 -P 4113 %s" % PTS.bd_addr(), start_wid = 13)),
        TestCase("L2CAP", "TC_CLS_UCD_BV_03_C",
                 TestCmd("l2test -s -E -G -N 1 -P 4113 %s" % PTS.bd_addr(), start_wid = 13)),

        TestCase("L2CAP", "TC_EXF_BV_01_C"),
        TestCase("L2CAP", "TC_EXF_BV_02_C"),
        TestCase("L2CAP", "TC_EXF_BV_03_C"),
        TestCase("L2CAP", "TC_EXF_BV_05_C"),

        TestCase("L2CAP", "TC_CMC_BV_01_C",
                  TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_04_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_05_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_06_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_07_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_08_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_09_C",
                 TestCmd("l2test -r -X basic -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_10_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),

        TestCase("L2CAP", "TC_CMC_BV_11_C",
                 TestCmd("l2test -n -P 4113 %s" % PTS.bd_addr(), start_wid = 13, stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BV_12_C",
                 TestCmd("l2test -z -X ertm %s" % PTS.bd_addr(), start_wid = 13)),
        TestCase("L2CAP", "TC_CMC_BV_13_C",
                 TestCmd("l2test -z -X streaming %s" % PTS.bd_addr(), start_wid = 13)),
        TestCase("L2CAP", "TC_CMC_BV_14_C",
                 TestCmd("l2test -r -X streaming -P 4113")),
        TestCase("L2CAP", "TC_CMC_BV_15_C",
                 TestCmd("l2test -r -X streaming -P 4113")),

        TestCase("L2CAP", "TC_CMC_BI_01_C",
                 TestCmd("l2test -r -X ertm -P 4113", stop_wid = 22)),
        TestCase("L2CAP", "TC_CMC_BI_02_C",
                 TestCmd("l2test -r -X ertm -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_03_C",
                 TestCmd("l2test -r -X streaming -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_04_C",
                 TestCmd("l2test -r -X streaming -P 4113", stop_wid = 14)),
        TestCase("L2CAP", "TC_CMC_BI_05_C",
                 TestCmd("l2test -r -X basic -P 4113", stop_wid = 22)),
        TestCase("L2CAP", "TC_CMC_BI_06_C",
                 TestCmd("l2test -r -X basic -P 4113", stop_wid = 22)),

        TestCase("L2CAP", "TC_FOC_BV_01_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_FOC_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_FOC_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),

        TestCase("L2CAP", "TC_OFS_BV_01_C",
                 TestCmd("l2test -x -X ertm -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113 -F 0")),
        TestCase("L2CAP", "TC_OFS_BV_03_C",
                 TestCmd("l2test -x -X streaming -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_04_C",
                 TestCmd("l2test -d -X streaming -P 4113 -F 0")),
        TestCase("L2CAP", "TC_OFS_BV_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_06_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_OFS_BV_07_C",
                 TestCmd("l2test -x -X streaming -P 4113 -F 0 -N 1")),
        TestCase("L2CAP", "TC_OFS_BV_08_C",
                 TestCmd("l2test -d -X streaming -P 4113")),

        TestCase("L2CAP", "TC_ERM_BV_01_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 3 -Y 3")),
        TestCase("L2CAP", "TC_ERM_BV_02_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_03_C",
                 TestCmd("l2test -r -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2 -Y 2")),
        TestCase("L2CAP", "TC_ERM_BV_06_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2 -Y 2")),
        TestCase("L2CAP", "TC_ERM_BV_07_C",
                 TestCmd("l2test -r -H 1000 -K 10000 -X ertm -P 4113", start_wid = 15),
                 no_wid = 19),
        TestCase("L2CAP", "TC_ERM_BV_08_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_09_C",
                 TestCmd("l2test -X ertm -P 4113")),

        # TODO: occasionally on flo fails with PTS has received an unexpected
        # L2CAP_DISCONNECT_REQ from the IUT. Sometimes passes.
        # sometimes: "MTC: The Retransmission Timeout Timer (adjusted) of PTS
        # has timed out. The IUT should have sent a S-frame by now."
        # Sometimes passes.
        # also fails in gui if you restart l2cap and run test case again.
        # only solvable by clicking "Delete Link Key" toolbar button of PTS.
        # thought TSPX_delete_link_key is set to TRUE
        TestCase("L2CAP", "TC_ERM_BV_10_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),

        TestCase("L2CAP", "TC_ERM_BV_11_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1 -Q 1")),
        TestCase("L2CAP", "TC_ERM_BV_12_C",
                 TestCmd("l2test -x -X ertm -P 4113 -R -N 1 -Q 1")),
        TestCase("L2CAP", "TC_ERM_BV_13_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BV_14_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 4")),
        TestCase("L2CAP", "TC_ERM_BV_15_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 4")),
        TestCase("L2CAP", "TC_ERM_BV_17_C",
                 TestCmd("l2test -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BV_18_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_19_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_20_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 1")),
        TestCase("L2CAP", "TC_ERM_BV_21_C",
                 TestCmd("l2test -x -X ertm -P 4113 -D 2000 -N 2")),
        TestCase("L2CAP", "TC_ERM_BV_22_C",
                 TestCmd("l2test -r -H 1000 -K 10000 -X ertm -P 4113", start_wid = 15),
                 no_wid = 19),
        TestCase("L2CAP", "TC_ERM_BV_23_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),

        TestCase("L2CAP", "TC_ERM_BI_02_C",
                 TestCmd("l2test -X ertm -P 4113")),
        TestCase("L2CAP", "TC_ERM_BI_03_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BI_04_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),
        TestCase("L2CAP", "TC_ERM_BI_05_C",
                 TestCmd("l2test -x -X ertm -P 4113 -N 2")),

        TestCase("L2CAP", "TC_STM_BV_01_C",
                 TestCmd("l2test -x -X streaming -P 4113 -N 3 -Y 3")),
        TestCase("L2CAP", "TC_STM_BV_02_C",
                 TestCmd("l2test -d -X streaming -P 4113")),
        TestCase("L2CAP", "TC_STM_BV_03_C",
                 TestCmd("l2test -x -X streaming -P 4113 -N 2")),

        # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13206
        # TODO DANGEROUS CASE: crashes pts sometimes, report to  as pts bug?
        # TestCase("L2CAP", "TC_FIX_BV_01_C",
        #          TestCmd("l2test -z -P 4113 %s" % PTS.bd_addr(), start_wid = 49))

        TestCase("L2CAP", "TC_LE_CPU_BV_01_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % PTS.bd_addr())),
        TestCase("L2CAP", "TC_LE_CPU_BV_02_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -n -V le_public -J 4 %s" % PTS.bd_addr(), stop_wid = 22)]),

        TestCase("L2CAP", "TC_LE_CPU_BI_01_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % PTS.bd_addr(), stop_wid = 22)),
        TestCase("L2CAP", "TC_LE_CPU_BI_02_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestCmd("l2test -r -V le_public -J 4")]),

        TestCase("L2CAP", "TC_LE_REJ_BI_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -n -V le_public -J 4 %s" % PTS.bd_addr(), stop_wid = 22)]),
        TestCase("L2CAP", "TC_LE_REJ_BI_02_C",
                 TestCmd("l2test -n -V le_public -J 4 %s" % PTS.bd_addr(), stop_wid = 22)),

        TestCase("L2CAP", "TC_LE_CFC_BV_01_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % PTS.bd_addr())),

        TestCase("L2CAP", "TC_LE_CFC_BV_02_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 22)),

        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_03_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestFunc(PTS.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "FALSE"),
                  TestCmd("l2test -x -N 1 -V le_public %s" % PTS.bd_addr(), stop_wid = 22),
                  TestFuncCleanUp(btmgmt.advertising_off),
                  TestFuncCleanUp(PTS.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "TRUE")]),

        TestCase("L2CAP", "TC_LE_CFC_BV_04_C",
                 TestCmd("l2test -n -V le_public -P 241 %s" % PTS.bd_addr())),

        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_05_C",
                 [TestFunc(btmgmt.advertising_on),
                  TestFunc(PTS.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "FALSE"),
                  TestCmd("l2test -r -V le_public -J 4")]),

        # PTS issue #12853
        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        TestCase("L2CAP", "TC_LE_CFC_BV_06_C",
                 [TestCmd("l2test -x -b 1 -V le_public %s" % PTS.bd_addr()),
                  TestFuncCleanUp(PTS.update_pixit_param, "L2CAP", "TSPX_iut_role_initiator", "TRUE")]),

        # does not pass in automation mode and makes PTS unstable:
        # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13225
        # TestCase("L2CAP", "TC_LE_CFC_BV_07_C",
        #          [TestFunc(btmgmt.advertising_off),
        #           TestCmd("l2test -u -V le_public %s" % PTS.bd_addr(),
        #                   start_wid = 51, stop_wid = 22)]),
        TestCase("L2CAP", "TC_LE_CFC_BI_01_C",
                 [TestFunc(btmgmt.advertising_off),
                  TestCmd("l2test -u -V le_public %s" % PTS.bd_addr())]),
        TestCase("L2CAP", "TC_LE_CFC_BV_08_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % PTS.bd_addr(), stop_wid = 14)),
        TestCase("L2CAP", "TC_LE_CFC_BV_09_C",
                 TestCmd("l2test -n -V le_public -P 37 %s" % PTS.bd_addr())),
        TestCase("L2CAP", "TC_LE_CFC_BV_16_C",
                 [TestCmd("l2test -n -V le_public -P 37 %s" % PTS.bd_addr()),
                  TestFuncCleanUp(btmgmt.advertising_on)])

        # PTS issue #12730
        # l2test -s -N 1 <bdaddr>
        # l2test -s -N 1 -V le_public <bdaddr>
        # TestCase("L2CAP", "TC_LE_CID_BV_02_I",  "")

        # PTS issue #12730
        # Note: PIXIT TSPX_iut_role_initiator=FALSE
        # l2test -w -N 1
        # l2test -w -N 1 -V le_public
        # TestCase("L2CAP", "TC_LE_CID_BV_01_C",  "")
    ]

    return test_cases

def get_test_cases_rfcomm():
    test_cases = [
        TestCase("RFCOMM", "TC_RFC_BV_01_C",
                 TestCmd("rctest -n -P 1 %s" % PTS.bd_addr(), 20)),

        TestCase("RFCOMM", "TC_RFC_BV_02_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_03_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_04_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr(), stop_wid = 15)),

        TestCase("RFCOMM", "TC_RFC_BV_05_C",
                 TestCmd("rctest -n -P 4 %s" % PTS.bd_addr(), 20)),

        TestCase("RFCOMM", "TC_RFC_BV_06_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_07_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr(), stop_wid = 14)),

        TestCase("RFCOMM", "TC_RFC_BV_08_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_11_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_13_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_15_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_17_C",
                 TestCmd("rctest -d -P 1 %s" % PTS.bd_addr())),

        TestCase("RFCOMM", "TC_RFC_BV_19_C"),

        # INC PTS issue #13011
        TestCase("RFCOMM", "TC_RFC_BV_21_C"),
        TestCase("RFCOMM", "TC_RFC_BV_22_C"),

        TestCase("RFCOMM", "TC_RFC_BV_25_C",
                 TestCmd("rctest -r -P 1 %s" % PTS.bd_addr()))
    ]

    return test_cases

def get_test_cases_gap():
    test_cases = [
        TestCase("GAP", "TC_MOD_NDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_off)),

        TestCase("GAP", "TC_MOD_LDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_MOD_LDIS_BV_02_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_MOD_LDIS_BV_03_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),

        TestCase("GAP", "TC_MOD_GDIS_BV_01_C",
                 TestFunc(btmgmt.discoverable_on)),
        TestCase("GAP", "TC_MOD_GDIS_BV_02_C"),

        TestCase("GAP", "TC_MOD_NCON_BV_01_C",
                 TestFunc(btmgmt.connectable_off)),

        TestCase("GAP", "TC_MOD_CON_BV_01_C",
                 TestFunc(btmgmt.connectable_on)),

        TestCase("GAP", "TC_DISC_NONM_BV_01_C",
                 [TestFunc(btmgmt.connectable_off),
                  TestFunc(btmgmt.advertising_on)]),

        TestCase("GAP", "TC_DISC_NONM_BV_02_C",
                 [TestFunc(btmgmt.connectable_on),
                  TestFunc(btmgmt.discoverable_off)]),

        TestCase("GAP", "TC_DISC_LIMM_BV_01_C",
                 TestFunc(btmgmt.discoverable_limited, 30), no_wid = 120),
        TestCase("GAP", "TC_DISC_LIMM_BV_02_C",
                 TestFunc(btmgmt.discoverable_limited, 30)),
        TestCase("GAP", "TC_DISC_LIMM_BV_03_C",
                 TestFunc(btmgmt.discoverable_limited, 30), no_wid = 120),

        TestCase("GAP", "TC_DISC_LIMM_BV_04_C",
                 [TestFunc(btmgmt.discoverable_off),
                  TestFunc(btmgmt.power_off),
                  TestFunc(btmgmt.bredr_off),
                  TestFunc(btmgmt.power_on),
                  TestFunc(btmgmt.discoverable_limited, 30)]),

        TestCase("GAP", "TC_DISC_GENM_BV_01_C",
                 TestFunc(btmgmt.discoverable_on), no_wid = 120),
        TestCase("GAP", "TC_DISC_GENM_BV_02_C",
                 TestFunc(btmgmt.bredr_on)),
        TestCase("GAP", "TC_DISC_GENM_BV_03_C", no_wid = 120),

        TestCase("GAP", "TC_DISC_GENM_BV_04_C",
                 [TestFunc(btmgmt.power_off),
                  TestFunc(btmgmt.bredr_off),
                  TestFunc(btmgmt.power_on),
                  TestFunc(btmgmt.discoverable_on),
                  TestFuncCleanUp(btmgmt.bredr_on)]),

        # TODO grep for pts in output of "find -l" to find the answer to the last
        # pts dialog
        TestCase("GAP", "TC_DISC_LIMP_BV_01_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_02_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_03_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_04_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_LIMP_BV_05_C", TestCmd("btmgmt find -l")),

        TestCase("GAP", "TC_DISC_GENP_BV_01_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_02_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_03_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_04_C", TestCmd("btmgmt find -l")),
        TestCase("GAP", "TC_DISC_GENP_BV_05_C", TestCmd("btmgmt find -l")),

        TestCase("GAP", "TC_IDLE_GIN_BV_01_C",
                 TestCmd("btmgmt find", start_wid = 146)),
        TestCase("GAP", "TC_IDLE_LIN_BV_01_C",
                 TestCmd("hcitool scan --iac=liac", start_wid = 146)),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_IDLE_NAMP_BV_01_C"),

        TestCase("GAP", "TC_IDLE_NAMP_BV_02_C",
                 TestFunc(btmgmt.advertising_on)),

        TestCase("GAP", "TC_CONN_NCON_BV_01_C",
                 TestFunc(btmgmt.connectable_off), no_wid = 120),
        TestCase("GAP", "TC_CONN_NCON_BV_02_C", no_wid = 120),
        TestCase("GAP", "TC_CONN_NCON_BV_03_C", no_wid = 120),

        TestCase("GAP", "TC_CONN_DCON_BV_01_C",
                 TestFunc(btmgmt.connectable_on), no_wid = 120),

        TestCase("GAP", "TC_CONN_UCON_BV_01_C"),
        TestCase("GAP", "TC_CONN_UCON_BV_02_C"),
        TestCase("GAP", "TC_CONN_UCON_BV_03_C"),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_CONN_ACEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_GCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_GCEP_BV_02_C"),

        # TestCase("GAP", "TC_CONN_SCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_DCEP_BV_01_C"),
        # TestCase("GAP", "TC_CONN_DCEP_BV_03_C"),
        TestCase("GAP", "TC_CONN_CPUP_BV_01_C",
                 TestFunc(btmgmt.advertising_on)),
        # TestCase("GAP", "TC_CONN_CPUP_BV_02_C",
        #          TestFunc(btmgmt.advertising_on)),
        TestCase("GAP", "TC_CONN_CPUP_BV_03_C",
                 TestFunc(btmgmt.advertising_on)),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_CONN_CPUP_BV_04_C"),
        # TestCase("GAP", "TC_CONN_CPUP_BV_05_C"),
        # TestCase("GAP", "TC_CONN_CPUP_BV_06_C"),
        # TestCase("GAP", "TC_CONN_TERM_BV_01_C"),
        # TestCase("GAP", "TC_CONN_PRDA_BV_01_C"),
        # TestCase("GAP", "TC_CONN_PRDA_BV_02_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_01_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_02_C"),
        # TestCase("GAP", "TC_BOND_NBON_BV_03_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_01_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_02_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_03_C"),
        # TestCase("GAP", "TC_BOND_BON_BV_04_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_11_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_12_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_13_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_14_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_17_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_18_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_19_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_20_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_21_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_22_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_23_C"),
        # TestCase("GAP", "TC_SEC_AUT_BV_24_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BV_01"),
        # TestCase("GAP", "TC_SEC_CSIGN_BV_02"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_01_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_02_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_03_C"),
        # TestCase("GAP", "TC_SEC_CSIGN_BI_04_C"),
        #
        # PTS issue #12951
        # Note: PIXITs required to be changed:
        # TSPX_using_public_device_address: FALSE
        # TSPX_using_random_device_address: TRUE
        # echo 30 > /sys/kernel/debug/bluetooth/hci0/
        # 				rpa_timeout
        # btmgmt power off
        # btmgmt privacy on
        # btmgmt power on
        # TestCase("GAP", "TC_PRIV_CONN_BV_10_C")
        #
        # INC
        # PTS issue #12952
        # JIRA #BA-186
        # TestCase("GAP", "TC_PRIV_CONN_BV_11_C")
        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_ADV_BV_02_C"),
        # TestCase("GAP", "TC_ADV_BV_03_C"),
        # TestCase("GAP", "TC_ADV_BV_05_C"),
        # TestCase("GAP", "TC_GAT_BV_01_C"),
        # TestCase("GAP", "TC_DM_NCON_BV_01_C"),
        # TestCase("GAP", "TC_DM_CON_BV_01_C"),
        # TestCase("GAP", "TC_DM_NBON_BV_01_C", TestFunc(btmgmt.bondable_off)),
        # TODO: must script/automate haltest
        # TestCase("TC_DM_BON_BV_01_C"),
        TestCase("GAP", "TC_DM_GIN_BV_01_C"),
        TestCase("GAP", "TC_DM_LIN_BV_01_C"),
        TestCase("GAP", "TC_DM_NAD_BV_01_C"),
        # TestCase("GAP", "TC_DM_NAD_BV_02_C"),

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_DM_LEP_BV_01_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_02_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_04_C",
        #          TestCmd("l2test -n %s" % PTS.bd_addr())),
        # TestCase("GAP", "TC_DM_LEP_BV_05_C",
        #          [TestCmd("btmgmt find -b"),
        #           TestCmd("l2test -n %s" % PTS.bd_addr())])

        # TODO: must script/automate haltest
        # TestCase("GAP", "TC_DM_LEP_BV_06_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_07_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_08_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_09_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_10_C"),
        # TestCase("GAP", "TC_DM_LEP_BV_11_C"),
    ]

    return test_cases

def parse_args():
    """Parses command line arguments and options"""
    required_ext = ".pqw6" # valid PTS workspace file extension

    arg_parser = argparse.ArgumentParser(
        description = "PTS automation IronPython script")

    arg_parser.add_argument(
        "workspace",
        help = "Path to PTS workspace to use for testing. It should have %s "
        "extension" % (required_ext,))

    args = arg_parser.parse_args()

    # check that aruments and options are sane
    if not os.path.isfile(args.workspace):
        raise Exception("Workspace file '%s' does not exist" %
                        (args.workspace,))

    specified_ext = os.path.splitext(args.workspace)[1]
    if required_ext != specified_ext:
        raise Exception(
            "Workspace file '%s' extension is wrong, should be %s" %
            (args.workspace, required_ext))

    return args

def init_pts(workspace):
    """Initializes PTS COM objects
    
    workspace -- Path to PTS workspace to use for testing.

    """
    global PTS

    PTS = ptscontrol.PyPTS()

    log("PTS Version: %x", PTS.get_version())
    log("PTS Bluetooth Address: %x", PTS.get_bluetooth_address())
    log("PTS BD_ADDR: %s" % PTS.bd_addr())

    PTS.open_workspace(workspace)

def init():
    "Initialization procedure"

    args = parse_args()

    script_name = os.path.basename(sys.argv[0]) # in case it is full path
    script_name_no_ext = os.path.splitext(script_name)[0]

    log_filename = "%s.log" % (script_name_no_ext,)
    logging.basicConfig(format = '%(name)s [%(asctime)s] %(message)s',
                        filename = log_filename,
                        filemode = 'w',
                        level = logging.DEBUG)

    init_pts(args.workspace)

    if USE_ADB: # IUT commands require root permissions
        exec_adb_root()

def get_max_test_case_desc(test_cases):
    '''Takes a list of test cases and return a tuple of longest project name
    and test case name.
    '''

    max_project_name = 0
    max_test_case_name = 0

    for test_case in test_cases:
        project_name_len = len(test_case.project_name)
        test_case_name_len = len(test_case.name)

        if project_name_len > max_project_name:
            max_project_name = project_name_len

        if test_case_name_len > max_test_case_name:
            max_test_case_name = test_case_name_len

    return (max_project_name, max_test_case_name)

def main():
    """Main."""
    init()

    # test_cases = get_test_cases_rfcomm()
    # test_cases = get_test_cases_l2cap()
    test_cases = get_test_cases_gap()

    log("Running test cases...")

    num_test_cases = len(test_cases)
    num_test_cases_width = len(str(num_test_cases))
    max_project_name, max_test_case_name = get_max_test_case_desc(test_cases)
    margin = 3

    for index, test_case in enumerate(test_cases):
        print (str(index + 1).rjust(num_test_cases_width) +
               "/" +
               str(num_test_cases).ljust(num_test_cases_width + margin) +
               test_case.project_name.ljust(max_project_name + margin) +
               test_case.name.ljust(max_test_case_name + margin - 1)),
        test_case.run()
        print test_case.status

    print "\nBye!"

if __name__ == "__main__":
    main()
