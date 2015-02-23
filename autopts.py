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

# TODO: adb root should be executed beforehand, otherwise none of the commands will work on device
ADB = r"C:\Users\rmstoi\AppData\Local\Android\android-sdk\platform-tools\adb.exe"
USE_ADB = True

BD_ADDR = ""
PTS = None

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

class Logger(p.IPTSControlClientLogger):

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
class Sender(p.IPTSImplicitSendCallbackEx):
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

        # answer yes to yes/no question, like in case of
        # if wid == 22 and project_name == "L2CAP" and test_case == "TC_COS_CFC_BV_01_C":
        if style == 0x11044:
            libc.wcscpy_s(response, response_size, u"Yes")

        # actually style == 0x11141
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
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BV_10_C":
            stop_child = True
        if wid == 14 and project_name == "L2CAP" and test_case == "TC_CMC_BV_11_C":
            stop_child = True

        if stop_child and CHILD_PROCESS:
            print "STOPPING CHILD CAUSE OF MMI REQUEST"
            CHILD_PROCESS.kill()

        print "END OnImplicitSend:"
        print "********************"
        print 

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
        if USE_ADB:
            cmd = "%s shell %s" % (ADB, CHILD_PROCESS_COMMAND)
        else:
            cmd = CHILD_PROCESS_COMMAND

        print "starting child process", CHILD_PROCESS_COMMAND
        CHILD_PROCESS = subprocess.Popen(cmd)

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

    # TODO: the following three cases require advertising to be off
    # todo this one gives Unknown L2CA CM message, even in pts
    # run_test_case("L2CAP", "TC_COS_CFC_BV_01_C", "l2test -y -N 1 -b 40 -V le_public -P 37 %s" % (BD_ADDR,))
    # run_test_case("L2CAP", "TC_COS_CFC_BV_02_C", "l2test -y -N 1 -b 1 -V le_public -P 37 %s" % (BD_ADDR,))
    # TODO: this one gets huge amount of messages, unlike unlike ui and does not pass
    # run_test_case("L2CAP", "TC_COS_CFC_BV_03_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_COS_CFC_BV_04_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))
    # TODO: this one requiers two l2test processes
    # run_test_case("L2CAP", "TC_COS_CFC_BV_05_C", "l2test -u -V le_public -P 37 %s" % (BD_ADDR,))

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
    # TODO: these two seem to be reluctant to pass, with UI removing link key solves it
    run_test_case("L2CAP", "TC_CMC_BV_08_C", "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_09_C", "l2test -r -X basic -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_10_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_11_C", "l2test -n -P 4113 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_12_C",  "l2test -z -X ertm %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_13_C",  "l2test -z -X streaming %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_CMC_BV_14_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BV_15_C",  "l2test -r -X streaming -P 4113")

    # TODO: seem to get INCONC, need to remove link key?
    run_test_case("L2CAP", "TC_CMC_BI_01_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_02_C",  "l2test -r -X ertm -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_03_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_04_C",  "l2test -r -X streaming -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_05_C",  "l2test -r -X basic -P 4113")
    run_test_case("L2CAP", "TC_CMC_BI_06_C",  "l2test -r -X basic -P 4113")

    # TODO: inconc
    run_test_case("L2CAP", "TC_FOC_BV_01_C",  "l2test -r -X ertm -P 4113 -F 0")
    run_test_case("L2CAP", "TC_FOC_BV_02_C",  "l2test -r -X ertm -P 4113 -F 0")
    run_test_case("L2CAP", "TC_FOC_BV_03_C",  "l2test -r -X ertm -P 4113 -F 0")

    # TODO: inconc
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

    run_test_case("L2CAP", "TC_FIX_BV_01_C",  "l2test -z -P 4113 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CPU_BV_01_C",  "l2test -n -V le_public -J 4")
    run_test_case("L2CAP", "TC_LE_CPU_BV_02_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CPU_BI_01_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CPU_BI_02_C",  "l2test -r -V le_public -J 4")

    run_test_case("L2CAP", "TC_LE_REJ_BI_01_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_REJ_BI_02_C",  "l2test -n -V le_public -J 4 %s" % (BD_ADDR,))

    run_test_case("L2CAP", "TC_LE_CFC_BV_01_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_02_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    # run_test_case("L2CAP", "TC_LE_CFC_BV_03_C",  "l2test -x -N 1 -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_04_C",  "l2test -n -V le_public -P 241 %s" % (BD_ADDR,))

    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    # run_test_case("L2CAP", "TC_LE_CFC_BV_05_C",  "l2test -r -V le_public -J 4")

    # PTS issue #12853
    # Note: PIXIT TSPX_iut_role_initiator=FALSE
    # run_test_case("L2CAP", "TC_LE_CFC_BV_06_C",  "l2test -x -b 1 -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_07_C",  "l2test -u -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BI_01_C",  "l2test -u -V le_public %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_08_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_09_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))
    run_test_case("L2CAP", "TC_LE_CFC_BV_16_C",  "l2test -n -V le_public -P 37 %s" % (BD_ADDR,))

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

def main():
    '''Main.'''
    global BD_ADDR
    global PTS

    logger = Logger()
    sender = Sender()

    PTS = p.PTSControlClass()

    PTS.SetControlClientLoggerCallback(logger)
    PTS.RegisterImplicitSendCallbackEx(sender)

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
    
    print "\n\n\nRunning test cases..."

    test_l2cap()
#    test_rfcomm()
#    run_test_case("DID", "TC_SDI_BV_1_I")

    print_results()

    print "\nBye!"

if __name__ == "__main__":
    main()
