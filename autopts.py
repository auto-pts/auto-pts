'''PTS automation IronPython script

To use it you have to have installed COM interop assembly to the bin directory
of PTS, like:

cp Interop.PTSConrol.dll C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\bin\

Since PTS requires admin rights, you have to run this script as admin. You need
to use 32 bit IronPython to run this script because PTS is a 32 bit
application.

Run this is script in admin terminal as follows:

ipy.exe autopts.py

'''

import clr
import sys

import subprocess
import time
import System
import ctypes
libc = ctypes.cdll.msvcrt # for wcscpy_s

# load the PTS interop assembly
clr.AddReferenceToFileAndPath(
    r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\bin\Interop.PTSControl.dll")

import Interop.PTSControl as p

# WORKSPACE = r'C:\Users\rmstoi\Documents\Profile Tuning Suite\AOSP on Mako\AOSP on Mako.pqw6'
# WORKSPACE = r'C:\Users\rmstoi\Documents\Profile Tuning Suite\AOSP on HammerHead\AOSP on HammerHead.pqw6'
WORKSPACE = r'C:\Users\rmstoi\Documents\Profile Tuning Suite\AOSP on Flo\AOSP on Flo.pqw6'

# make sure adb is in path or modify this variable
ADB = "adb.exe"
USE_ADB = True

# PTS bluetooth address in standard form
BD_ADDR = ""

# instance of PTSControl COM class
PTS = None

# child process required by the test case
CHILD_PROCESS = None
CHILD_PROCESS_COMMAND = None

class TestCase:
    def __init__(self, project, test_case, status = "init"):
        self.project = project
        self.test_case = test_case
        # final verdict
        self.status = status

    def __str__(self):
        return "%s %s %s" % (self.project, self.test_case, self.status)

class btmgmt:
    '''Incomplete wrapper around btmgmt. The methods are added as needed.'''

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

# list of executed test cases (TestCase objects)
# TODO: which with print_results could become a class of its own, could also
# get rid of [-1] this way, with something like update_current_result
RESULTS = []

def print_results():
    if not RESULTS:
        return
            
    print "Results:"
    print "========"
    
    for test_case in RESULTS:
        print test_case

class PTSLogger(p.IPTSControlClientLogger):

    def __init__(self):
        pass

# interface IPTSControlClientLogger : IUnknown {
#     HRESULT _stdcall Log(
#                     [in] _PTS_LOGTYPE logType, 
#                     [in] LPWSTR szLogType, 
#                     [in] LPWSTR szTime, 
#                     [in] LPWSTR pszMessage);
# };
    def Log(self, log_type, logtype_string, log_time, log_message):
        print "LOG:",
        print log_type, logtype_string, log_time, log_message

        # mark test case as started
        if log_type == p._PTS_LOGTYPE.PTS_LOGTYPE_START_TEST:
            RESULTS[-1].status = "Started"

        # mark the final verdict of the test case
        elif log_type == p._PTS_LOGTYPE.PTS_LOGTYPE_FINAL_VERDICT:
            if "PASS" in log_message:
                verdict = "PASS" 
            elif "INCONC" in log_message:
                verdict = "INCONC"
            elif "FAIL" in log_message:
                verdict = "FAIL"
            else:
                verdict = "UNKNOWN VERDICT: %s" % log_message

            print verdict    
            RESULTS[-1].status = verdict

# interface IPTSImplicitSendCallbackEx : IUnknown {
#     HRESULT _stdcall OnImplicitSend(
#                     [in] LPWSTR pszProjectName, 
#                     [in] unsigned short wID, 
#                     [in] LPWSTR pszTestCase, 
#                     [in] LPWSTR pszDescription, 
#                     [in] unsigned long style, 
#                     [in, out] LPWSTR pszResponse, 
#                     [in] unsigned long responseSize, 
#                     [in, out] long* pbResponseIsPresent);
# };
class PTSSender(p.IPTSImplicitSendCallbackEx):
    def OnImplicitSend(self, project_name, wid, test_case, description, style,
                       response, response_size, response_is_present):
        print "\n********************"
        print "BEGIN OnImplicitSend:"
        print "project_name:", project_name
        print "wid:", wid
        print "test_case:", test_case
        print "description:", description
        print "style: Ox%x" % style
        print "response:", repr(response), type(response), id(response)
        print "response_size:", response_size
        print "response_is_present:", response_is_present, type(response_is_present)

        response_is_present.Value = 1

        # MMI_Style_Yes_No1
        if style == 0x11044:

            # answer No
            if wid == 19 and project_name == "L2CAP" and test_case == "TC_ERM_BV_07_C" or \
               wid == 19 and project_name == "L2CAP" and test_case == "TC_ERM_BV_22_C" or \
               wid == 120 and project_name == "GAP" and test_case == "TC_DISC_LIMM_BV_01_C" or \
               wid == 120 and project_name == "GAP" and test_case == "TC_DISC_LIMM_BV_03_C" or \
               wid == 120 and project_name == "GAP" and test_case == "TC_DISC_GENM_BV_01_C" or \
               wid == 120 and project_name == "GAP" and test_case == "TC_DISC_GENM_BV_03_C":
                libc.wcscpy_s(response, response_size, u"No")

            # answer Yes
            else:
                libc.wcscpy_s(response, response_size, u"Yes")

        # actually style == 0x11141, MMI_Style_Ok_Cancel2
        else:
            libc.wcscpy_s(response, response_size, u"OK")

        print "written resonse is:"
        libc._putws(response)
        libc.fflush(None); 

        print "after setting respose:"
        print "response:", response, type(response), id(response)
        print "response_is_present:", response_is_present, type(response_is_present)

        stop_child = False

        # some test cases require the child process to be termintated (Ctrl-C
        # on terminal)
        if wid == 15 and project_name == "RFCOMM" and test_case == "TC_RFC_BV_04_C":
            stop_child = True
        if wid == 14 and project_name == "RFCOMM" and test_case == "TC_RFC_BV_07_C":
            stop_child = True

        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CED_BV_01_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CED_BV_03_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CED_BV_04_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CED_BV_09_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_02_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_03_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_08_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_09_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_11_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_COS_CFD_BV_12_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_IEX_BV_01_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_01_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_02_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_03_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_04_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_05_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BV_10_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BV_11_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BI_01_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BI_02_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BI_03_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BI_04_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_CMC_BI_05_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_CMC_BI_06_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_CPU_BV_02_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_CPU_BI_01_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_REJ_BI_01_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_REJ_BI_02_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_CFC_BV_02_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_CFC_BV_03_C":
            stop_child = True
        if wid == 22 and project_name == "L2CAP" and test_case == "TC_LE_CFC_BV_07_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_LE_CFC_BV_08_C":
            stop_child = True

        if stop_child and CHILD_PROCESS:
            print "STOPPING CHILD CAUSE OF MMI REQUEST"
            CHILD_PROCESS.kill()

        print "END OnImplicitSend:"
        print "********************"
        print 

def pts_update_pixit_param(project_name, param_name, new_param_value):
    '''Wrapper to catch exceptions that PTS throws if PIXIT param is already
    set to the same value.

    PTS throws exception if the value passed to UpdatePixitParam is the same as
    the value when PTS was started.

    In C++ HRESULT error with this value is returned:
    PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED (0x849C0021)

    The wrapped COM method is:
    HRESULT UpdatePixitParam(LPCWSTR pszProjectName, LPCWSTR pszParamName,
                             LPCWSTR pszNewParamValue);

    '''
    print "\nUpdatePixitParam(%s, %s, %s)" % (project_name, param_name, new_param_value)

    try:
        PTS.UpdatePixitParam(project_name, param_name, new_param_value)
    except System.Runtime.InteropServices.COMException as e:
        print 'Exception in UpdatePixitParam "%s", is pixit param aready set?' % (e.Message,)

def pts_update_pics(project_name, entry_name, bool_value):
    '''Wrapper to catch exceptions that PTS throws if PICS entry is already
    set to the same value.

    PTS throws exception if the value passed to UpdatePics is the same as
    the value when PTS was started.

    In C++ HRESULT error with this value is returned:
    PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED (0x849C0032)

    The wrapped COM method is:
    HRESULT UpdatePics(LPCWSTR pszProjectName, LPCWSTR pszEntryName,
                       BOOL bValue);
    '''
    print "\nUpdatePics(%s, %s, %s)" % (project_name, entry_name, bool_value)

    try:
        PTS.UpdatePics(project_name, entry_name, bool_value)
    except System.Runtime.InteropServices.COMException as e:
        print 'Exception in UpdatePics "%s", is pics value aready set?' % (e.Message,)

def exec_iut_cmd(iut_cmd, wait = False, use_adb_shell = USE_ADB):
    if use_adb_shell:
        cmd = "%s shell %s" % (ADB, iut_cmd)
    else:
        cmd = iut_cmd

    print "starting child process", repr(cmd)
    p = subprocess.Popen(cmd)
    if wait:
        p.wait()

    return p

def exec_adb_root():
    '''Runs "adb root" command'''
    exec_iut_cmd("adb root", True, False)
    # it takes an instance of time to get adbd restarted with root permissions
    exec_iut_cmd("adb wait-for-device", True, False)

def run_test_case(project, test_case, command = None):
    global CHILD_PROCESS_COMMAND
    global CHILD_PROCESS

    print "Running test case:", project, test_case, command

    CHILD_PROCESS_COMMAND = command

    RESULTS.append(TestCase(project, test_case))

    # TODO: Starting commands before running test case in pts works
    # with RFCOMM, but does not seem to work with L2CAP, more general
    # solution is needed
    if CHILD_PROCESS_COMMAND:
        CHILD_PROCESS = exec_iut_cmd(CHILD_PROCESS_COMMAND)

    PTS.RunTestCase(project, test_case)

    # TODO: pointless to sleep with last test case

    # in accordance with PTSControlClient.cpp:
    # // Allow device to settle down
    # Sleep(3000);
    # otherwise 4th test case just blocks eternally
    time.sleep(3)

    if CHILD_PROCESS:
        CHILD_PROCESS.kill()

    CHILD_PROCESS = None
    CHILD_PROCESS_COMMAND = None

def test_l2cap():
    '''Initial IUT config: powered connectable br/edr le advertising
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

    '''
    run_test_case("L2CAP", "TC_COS_CED_BV_01_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_03_C", "l2test -y -N 1 -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_04_C", "l2test -n -P 4113 %s" % (BD_ADDR,))

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
    # run_test_case("L2CAP", "TC_COS_CED_BV_05_C", "btmgmt ssp off;l2test -r -P 4113 %s; btmgmt ssp on" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_07_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_08_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_09_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CED_BV_11_C", "l2test -u -P 4113 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_COS_CED_BI_01_C")

    # TODO: just like TC_COS_CED_BV_05_C
    # run_test_case("L2CAP", "TC_COS_CFD_BV_01_C")
    run_test_case("L2CAP", "TC_COS_CFD_BV_02_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFD_BV_03_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFD_BV_08_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFD_BV_09_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFD_BV_11_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFD_BV_12_C", "l2test -n -P 4113 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_COS_IEX_BV_01_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_IEX_BV_02_C")

    run_test_case("L2CAP", "TC_COS_ECH_BV_01_C")
    run_test_case("L2CAP", "TC_COS_ECH_BV_02_C", "l2ping -c1 %s" % (BD_ADDR,))

    btmgmt.advertising_off()
    run_test_case("L2CAP", "TC_COS_CFC_BV_01_C", "l2test -y -N 1 -b 40 -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFC_BV_02_C", "l2test -y -N 1 -b 1 -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFC_BV_03_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFC_BV_04_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))
    # TODO: this one requiers two l2test processes
    # run_test_case("L2CAP", "TC_COS_CFC_BV_05_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))
    btmgmt.advertising_on()

    run_test_case("L2CAP", "TC_CLS_UCD_BV_01_C")
    run_test_case("L2CAP", "TC_CLS_UCD_BV_02_C", "l2test -s -G -N 1 -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CLS_UCD_BV_03_C", "l2test -s -E -G -N 1 -P 4113 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_EXF_BV_01_C")
    run_test_case("L2CAP", "TC_EXF_BV_02_C")
    run_test_case("L2CAP", "TC_EXF_BV_03_C")
    run_test_case("L2CAP", "TC_EXF_BV_05_C")

    run_test_case("L2CAP", "TC_CMC_BV_01_C", "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_02_C", "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_03_C", "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_04_C", "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_05_C", "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_06_C", "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_07_C", "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_08_C", "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_09_C", "l2test -r -X basic -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_10_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_11_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_12_C",  "l2test -z -X ertm %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_13_C",  "l2test -z -X streaming %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_14_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_15_C",  "l2test -r -X streaming -P 4113")

    run_test_case("L2CAP", "TC_CMC_BI_01_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_02_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_03_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_04_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_05_C",  "l2test -r -X basic -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_06_C",  "l2test -r -X basic -P 4113")

    run_test_case("L2CAP", "TC_FOC_BV_01_C",  "l2test -r -X ertm -P 4113 -F 0")
    run_test_case("L2CAP", "TC_FOC_BV_02_C",  "l2test -r -X ertm -P 4113 -F 0")
    run_test_case("L2CAP", "TC_FOC_BV_03_C",  "l2test -r -X ertm -P 4113 -F 0")

    run_test_case("L2CAP", "TC_OFS_BV_01_C",  "l2test -x -X ertm -P 4113 -F 0 -N 1")
    run_test_case("L2CAP", "TC_OFS_BV_02_C",  "l2test -r -X ertm -P 4113 -F 0")
    run_test_case("L2CAP", "TC_OFS_BV_03_C",  "l2test -x -X streaming -P 4113 -F 0 -N 1")
    run_test_case("L2CAP", "TC_OFS_BV_04_C",  "l2test -d -X streaming -P 4113 -F 0")
    run_test_case("L2CAP", "TC_OFS_BV_05_C",  "l2test -x -X ertm -P 4113 -N 1")
    run_test_case("L2CAP", "TC_OFS_BV_06_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_OFS_BV_07_C",  "l2test -x -X streaming -P 4113 -F 0 -N 1")
    run_test_case("L2CAP", "TC_OFS_BV_08_C",  "l2test -d -X streaming -P 4113")

    run_test_case("L2CAP", "TC_ERM_BV_01_C",  "l2test -x -X ertm -P 4113 -N 3 -Y 3")
    run_test_case("L2CAP", "TC_ERM_BV_02_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BV_03_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BV_05_C",  "l2test -x -X ertm -P 4113 -N 2 -Y 2")
    run_test_case("L2CAP", "TC_ERM_BV_06_C",  "l2test -x -X ertm -P 4113 -N 2 -Y 2")
    run_test_case("L2CAP", "TC_ERM_BV_07_C",  "l2test -r -H 1000 -K 10000 -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BV_08_C",  "l2test -x -X ertm -P 4113 -N 1")
    run_test_case("L2CAP", "TC_ERM_BV_09_C",  "l2test -X ertm -P 4113")

    # TODO: occasionally on flo fails with PTS has received an unexpected
    # L2CAP_DISCONNECT_REQ from the IUT. Sometimes passes.
    # sometimes: "MTC: The Retransmission Timeout Timer (adjusted) of PTS
    # has timed out. The IUT should have sent a S-frame by now."
    # Sometimes passes.
    # also fails in gui if you restart l2cap and run test case again.
    # only solvable by clicking "Delete Link Key" toolbar button of PTS.
    # thought TSPX_delete_link_key is set to TRUE
    run_test_case("L2CAP", "TC_ERM_BV_10_C",  "l2test -x -X ertm -P 4113 -N 1")

    run_test_case("L2CAP", "TC_ERM_BV_11_C",  "l2test -x -X ertm -P 4113 -N 1 -Q 1")
    run_test_case("L2CAP", "TC_ERM_BV_12_C",  "l2test -x -X ertm -P 4113 -R -N 1 -Q 1")
    run_test_case("L2CAP", "TC_ERM_BV_13_C",  "l2test -x -X ertm -P 4113 -N 2")
    run_test_case("L2CAP", "TC_ERM_BV_14_C",  "l2test -x -X ertm -P 4113 -N 4")
    run_test_case("L2CAP", "TC_ERM_BV_15_C",  "l2test -x -X ertm -P 4113 -N 4")
    run_test_case("L2CAP", "TC_ERM_BV_17_C",  "l2test -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BV_18_C",  "l2test -x -X ertm -P 4113 -N 1")
    run_test_case("L2CAP", "TC_ERM_BV_19_C",  "l2test -x -X ertm -P 4113 -N 1")
    run_test_case("L2CAP", "TC_ERM_BV_20_C",  "l2test -x -X ertm -P 4113 -N 1")
    run_test_case("L2CAP", "TC_ERM_BV_21_C",  "l2test -x -X ertm -P 4113 -D 2000 -N 2")
    run_test_case("L2CAP", "TC_ERM_BV_22_C",  "l2test -r -H 1000 -K 10000 -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BV_23_C",  "l2test -x -X ertm -P 4113 -N 2")

    run_test_case("L2CAP", "TC_ERM_BI_02_C",  "l2test -X ertm -P 4113")
    run_test_case("L2CAP", "TC_ERM_BI_03_C",  "l2test -x -X ertm -P 4113 -N 2")
    run_test_case("L2CAP", "TC_ERM_BI_04_C",  "l2test -x -X ertm -P 4113 -N 2")
    run_test_case("L2CAP", "TC_ERM_BI_05_C",  "l2test -x -X ertm -P 4113 -N 2")

    run_test_case("L2CAP", "TC_STM_BV_01_C",  "l2test -x -X streaming -P 4113 -N 3 -Y 3")
    run_test_case("L2CAP", "TC_STM_BV_02_C",  "l2test -d -X streaming -P 4113")
    run_test_case("L2CAP", "TC_STM_BV_03_C",  "l2test -x -X streaming -P 4113 -N 2")

    # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13206
    # TODO DANGEROUS CASE: crashes pts sometimes, report to  as pts bug?
    # run_test_case("L2CAP", "TC_FIX_BV_01_C",  "l2test -z -P 4113 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CPU_BV_01_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))
    btmgmt.advertising_off()
    run_test_case("L2CAP", "TC_LE_CPU_BV_02_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CPU_BI_01_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))
    btmgmt.advertising_on()
    run_test_case("L2CAP", "TC_LE_CPU_BI_02_C",  "l2test -r -V le_public -J 4")
    btmgmt.advertising_off()
    run_test_case("L2CAP", "TC_LE_REJ_BI_01_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_REJ_BI_02_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CFC_BV_01_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CFC_BV_02_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))

    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    pts_update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "FALSE")
    run_test_case("L2CAP", "TC_LE_CFC_BV_03_C",  "l2test -x -N 1 -V le_public %s" % (BD_ADDR,))
    pts_update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "TRUE")

    run_test_case("L2CAP", "TC_LE_CFC_BV_04_C",  "l2test -n -V le_public -P 241 %s" % (BD_ADDR,))
    btmgmt.advertising_on()

    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    pts_update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "FALSE")
    run_test_case("L2CAP", "TC_LE_CFC_BV_05_C",  "l2test -r -V le_public -J 4")
    # PTS issue #12853
    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    run_test_case("L2CAP", "TC_LE_CFC_BV_06_C",  "l2test -x -b 1 -V le_public %s" % (BD_ADDR,))
    pts_update_pixit_param("L2CAP", "TSPX_iut_role_initiator", "TRUE")

    btmgmt.advertising_off()
    # does not pass in automation mode:
    # https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13225
    run_test_case("L2CAP", "TC_LE_CFC_BV_07_C",  "l2test -u -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BI_01_C",  "l2test -u -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_08_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_09_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_16_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))

    btmgmt.advertising_on()

    # PTS issue #12730
    # l2test -s -N 1 <bdaddr>
    # l2test -s -N 1 -V le_public <bdaddr>
    # run_test_case("L2CAP", "TC_LE_CID_BV_02_I",  "")

    # PTS issue #12730
    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    # l2test -w -N 1
    # l2test -w -N 1 -V le_public
    # run_test_case("L2CAP", "TC_LE_CID_BV_01_C",  "")

def test_rfcomm():
    run_test_case("RFCOMM", "TC_RFC_BV_01_C", "rctest -n -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_02_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_03_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_04_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_05_C", "rctest -n -P 4 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_06_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_07_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_08_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_11_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_13_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_15_C", "rctest -r -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_17_C", "rctest -d -P 1 %s" % (BD_ADDR,))
    run_test_case("RFCOMM", "TC_RFC_BV_19_C")

    # INC PTS issue #13011
    run_test_case("RFCOMM", "TC_RFC_BV_21_C")
    run_test_case("RFCOMM", "TC_RFC_BV_22_C")

    run_test_case("RFCOMM", "TC_RFC_BV_25_C", "rctest -r -P 1 %s" % (BD_ADDR,))

def test_gap():
    btmgmt.discoverable_off()
    run_test_case("GAP", "TC_MOD_NDIS_BV_01_C")

    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_MOD_LDIS_BV_01_C")
    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_MOD_LDIS_BV_02_C")
    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_MOD_LDIS_BV_03_C")

    btmgmt.discoverable_on()
    run_test_case("GAP", "TC_MOD_GDIS_BV_01_C")
    run_test_case("GAP", "TC_MOD_GDIS_BV_02_C")

    btmgmt.connectable_off()
    run_test_case("GAP", "TC_MOD_NCON_BV_01_C")

    btmgmt.connectable_on()
    run_test_case("GAP", "TC_MOD_CON_BV_01_C")

    btmgmt.connectable_off()
    btmgmt.advertising_on()
    run_test_case("GAP", "TC_DISC_NONM_BV_01_C")

    btmgmt.connectable_on()
    btmgmt.discoverable_off()
    run_test_case("GAP", "TC_DISC_NONM_BV_02_C")

    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_DISC_LIMM_BV_01_C")

    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_DISC_LIMM_BV_02_C")

    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_DISC_LIMM_BV_03_C")

    btmgmt.discoverable_off()
    btmgmt.power_off()
    btmgmt.bredr_off()
    btmgmt.power_on()
    btmgmt.discoverable_limited(30)
    run_test_case("GAP", "TC_DISC_LIMM_BV_04_C")

    btmgmt.discoverable_on()
    run_test_case("GAP", "TC_DISC_GENM_BV_01_C")

    btmgmt.bredr_on()
    run_test_case("GAP", "TC_DISC_GENM_BV_02_C")
    run_test_case("GAP", "TC_DISC_GENM_BV_03_C")

    btmgmt.power_off()
    btmgmt.bredr_off()
    btmgmt.power_on()
    btmgmt.discoverable_on()
    run_test_case("GAP", "TC_DISC_GENM_BV_04_C")
    btmgmt.bredr_on()

    # TODO grep for pts in output of "find -l" to find the answer to the last
    # pts dialog
    run_test_case("GAP", "TC_DISC_LIMP_BV_01_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_LIMP_BV_02_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_LIMP_BV_03_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_LIMP_BV_04_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_LIMP_BV_05_C", "btmgmt find -l")

    run_test_case("GAP", "TC_DISC_GENP_BV_01_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_GENP_BV_02_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_GENP_BV_03_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_GENP_BV_04_C", "btmgmt find -l")
    run_test_case("GAP", "TC_DISC_GENP_BV_05_C", "btmgmt find -l")

def main():
    '''Main.'''
    global BD_ADDR
    global PTS

    pts_logger = PTSLogger()
    pts_sender = PTSSender()

    PTS = p.PTSControlClass()

    PTS.SetControlClientLoggerCallback(pts_logger)
    PTS.RegisterImplicitSendCallbackEx(pts_sender)

    pts_version = clr.StrongBox[System.UInt32]()
    PTS.GetPTSVersion(pts_version)
    print "PTS Version: %x" % int(pts_version)

    bt_address = clr.StrongBox[System.UInt64]()
    PTS.GetPTSBluetoothAddress(bt_address)
    bt_address_int = int(bt_address)
    print "PTS Bluetooth Address: %x" % bt_address_int

    bt_address_upper = ("%x" % bt_address_int).upper()

    BD_ADDR = "00"
    for i in range(0, len(bt_address_upper), 2):
        BD_ADDR += ":" + bt_address_upper[i:i + 2]

    print "PTS BD_ADDR:", BD_ADDR

    print "Workspace", WORKSPACE
    PTS.OpenWorkspace(WORKSPACE)

    if USE_ADB: # IUT commands require root permissions
        exec_adb_root()

    print "\n\n\nRunning test cases..."

    test_gap()
    # test_l2cap()
    # test_rfcomm()
    # run_test_case("DID", "TC_SDI_BV_1_I")

    print_results()

    print "\nBye!"

if __name__ == "__main__":
    main()
