#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""Platform independent PTS types"""

# log type as on Windows in PTSControl._PTS_LOGTYPE
PTS_LOGTYPE_INFRASTRUCTURE      = 0
PTS_LOGTYPE_START_TEST          = 1
PTS_LOGTYPE_END_TEST            = 2
PTS_LOGTYPE_IMPLICIT_SEND       = 3
PTS_LOGTYPE_MESSAGE             = 4
PTS_LOGTYPE_ERROR               = 5
PTS_LOGTYPE_SEND_EVENT          = 6
PTS_LOGTYPE_RECEIVE_EVENT       = 7
PTS_LOGTYPE_FINAL_VERDICT       = 8
PTS_LOGTYPE_PRELIMINARY_VERDICT = 9
PTS_LOGTYPE_EVENT_SUMMARY       = 10

PTS_LOGTYPE_STRING = [
    "PTS_LOGTYPE_INFRASTRUCTURE",
    "PTS_LOGTYPE_START_TEST",
    "PTS_LOGTYPE_END_TEST",
    "PTS_LOGTYPE_IMPLICIT_SEND",
    "PTS_LOGTYPE_MESSAGE",
    "PTS_LOGTYPE_ERROR",
    "PTS_LOGTYPE_SEND_EVENT",
    "PTS_LOGTYPE_RECEIVE_EVENT",
    "PTS_LOGTYPE_FINAL_VERDICT",
    "PTS_LOGTYPE_PRELIMINARY_VERDICT",
    "PTS_LOGTYPE_EVENT_SUMMARY"
]

"""PTS MMI styles"""
MMI_Style_Ok_Cancel1     = 0x11041
MMI_Style_Ok_Cancel2     = 0x11141
MMI_Style_Ok             = 0x11040
MMI_Style_Yes_No1        = 0x11044
MMI_Style_Yes_No_Cancel1 = 0x11043
MMI_Style_Abort_Retry1   = 0x11042
MMI_Style_Edit1          = 0x12040
MMI_Style_Edit2          = 0x12140

MMI_STYLE_STRING = {
    MMI_Style_Ok_Cancel1     : "MMI_Style_Ok_Cancel1",
    MMI_Style_Ok_Cancel2     : "MMI_Style_Ok_Cancel2",
    MMI_Style_Ok             : "MMI_Style_Ok",
    MMI_Style_Yes_No1        : "MMI_Style_Yes_No1",
    MMI_Style_Yes_No_Cancel1 : "MMI_Style_Yes_No_Cancel1",
    MMI_Style_Abort_Retry1   : "MMI_Style_Abort_Retry1",
    MMI_Style_Edit1          : "MMI_Style_Edit1",
    MMI_Style_Edit2          : "MMI_Style_Edit2"
}

PTSCONTROL_E_GUI_UPDATE_FAILED                           = 0x849C0001
PTSCONTROL_E_PTS_FILE_FAILED_TO_INITIALIZE               = 0x849C0002
PTSCONTROL_E_FAILED_TO_CREATE_WORKSPACE                  = 0x849C0003
PTSCONTROL_E_CLIENT_LOG_NOT_EXPECTED_TO_FAIL             = 0x849C0004
PTSCONTROL_E_FAILED_TO_OPEN_WORKSPACE                    = 0x849C0005
PTSCONTROL_E_PROJECT_NOT_FOUND                           = 0x849C0010
PTSCONTROL_E_TESTCASE_NOT_FOUND                          = 0x849C0011
PTSCONTROL_E_TESTCASE_NOT_STARTED                        = 0x849C0012
PTSCONTROL_E_INVALID_TEST_SUITE                          = 0x849C0013
PTSCONTROL_E_PTS_VERSION_NOT_FOUND                       = 0x849C0014
PTSCONTROL_E_PROJECT_VERSION_NOT_FOUND                   = 0x849C0015
PTSCONTROL_E_TESTCASE_NOT_ACTIVE                         = 0x849C0016
PTSCONTROL_E_TESTCASE_TIMEOUT                            = 0x849C0017
PTSCONTROL_E_INVALID_PIXIT_PARAM_VALUE                   = 0x849C0020
PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED                     = 0x849C0021
PTSCONTROL_E_PIXIT_PARAM_UPDATE_FAILED                   = 0x849C0022
PTSCONTROL_E_PIXIT_PARAM_NOT_FOUND                       = 0x849C0023
PTSCONTROL_E_TEST_SUITE_PARAM_UPDATE_FAILED              = 0x849C0024
PTSCONTROL_E_PICS_ENTRY_UPDATE_FAILED                    = 0x849C0030
PTSCONTROL_E_PICS_ENTRY_NOT_FOUND                        = 0x849C0031
PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED                      = 0x849C0032
PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_ALREADY_REGISTERED   = 0x849C0041
PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_NOT_EXPECTED_TO_FAIL = 0x849C0042
PTSCONTROL_E_BLUETOOTH_ADDRESS_NOT_FOUND                 = 0x849C0043
PTSCONTROL_E_INTERNAL_ERROR                              = 0x849C0044
PTSCONTROL_E_FUNCTION_NOT_IMPLEMENTED                    = 0x849C0099
E_NOINTERFACE                                            = 0x80004002
CO_E_SERVER_EXEC_FAILURE                                 = 0x80080005


# the following errors are not documented in the "EXTENDED AUTOMATING - USING
# PTSCONTROL API", but they occur occasionally due to PTS process crash

# System.Runtime.InteropServices.COMException (0x800706BA): The RPC server is
# unavailable. (Exception from HRESULT: 0x800706BA)
E_RPC_SERVER_UNAVAILABLE                                 = 0x800706BA

# System.Runtime.InteropServices.COMException (0x800706BE): The remote
# procedure call failed. (Exception from HRESULT: 0x800706BE)
E_RPC_CALL_FAILED                                        = 0x800706BE


# these errors are not raised by PTS on Windows, they happen on Linux only
E_BTP_ERROR                                              = "BTP ERROR"
E_XML_RPC_ERROR                                          = "XML-RPC ERROR"
E_BTP_TIMEOUT                                            = "BTP TIMEOUT"
# unhandled exception
E_FATAL_ERROR                                            = "FATAL ERROR"


PTSCONTROL_E_STRING = {
    PTSCONTROL_E_GUI_UPDATE_FAILED                           : "PTSCONTROL_E_GUI_UPDATE_FAILED",
    PTSCONTROL_E_PTS_FILE_FAILED_TO_INITIALIZE               : "PTSCONTROL_E_PTS_FILE_FAILED_TO_INITIALIZE",
    PTSCONTROL_E_FAILED_TO_CREATE_WORKSPACE                  : "PTSCONTROL_E_FAILED_TO_CREATE_WORKSPACE",
    PTSCONTROL_E_CLIENT_LOG_NOT_EXPECTED_TO_FAIL             : "PTSCONTROL_E_CLIENT_LOG_NOT_EXPECTED_TO_FAIL",
    PTSCONTROL_E_FAILED_TO_OPEN_WORKSPACE                    : "PTSCONTROL_E_FAILED_TO_OPEN_WORKSPACE",
    PTSCONTROL_E_PROJECT_NOT_FOUND                           : "PTSCONTROL_E_PROJECT_NOT_FOUND",
    PTSCONTROL_E_TESTCASE_NOT_FOUND                          : "PTSCONTROL_E_TESTCASE_NOT_FOUND",
    PTSCONTROL_E_TESTCASE_NOT_STARTED                        : "PTSCONTROL_E_TESTCASE_NOT_STARTED",
    PTSCONTROL_E_INVALID_TEST_SUITE                          : "PTSCONTROL_E_INVALID_TEST_SUITE",
    PTSCONTROL_E_PTS_VERSION_NOT_FOUND                       : "PTSCONTROL_E_PTS_VERSION_NOT_FOUND",
    PTSCONTROL_E_PROJECT_VERSION_NOT_FOUND                   : "PTSCONTROL_E_PROJECT_VERSION_NOT_FOUND",
    PTSCONTROL_E_TESTCASE_NOT_ACTIVE                         : "PTSCONTROL_E_TESTCASE_NOT_ACTIVE",
    # shortened, user friendly status for timeout
    PTSCONTROL_E_TESTCASE_TIMEOUT                            : "PTS TIMEOUT",
    # PTSCONTROL_E_TESTCASE_TIMEOUT                            : "PTSCONTROL_E_TESTCASE_TIMEOUT",
    PTSCONTROL_E_INVALID_PIXIT_PARAM_VALUE                   : "PTSCONTROL_E_INVALID_PIXIT_PARAM_VALUE",
    PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED                     : "PTSCONTROL_E_PIXIT_PARAM_NOT_CHANGED",
    PTSCONTROL_E_PIXIT_PARAM_UPDATE_FAILED                   : "PTSCONTROL_E_PIXIT_PARAM_UPDATE_FAILED",
    PTSCONTROL_E_PIXIT_PARAM_NOT_FOUND                       : "PTSCONTROL_E_PIXIT_PARAM_NOT_FOUND",
    PTSCONTROL_E_TEST_SUITE_PARAM_UPDATE_FAILED              : "PTSCONTROL_E_TEST_SUITE_PARAM_UPDATE_FAILED",
    PTSCONTROL_E_PICS_ENTRY_UPDATE_FAILED                    : "PTSCONTROL_E_PICS_ENTRY_UPDATE_FAILED",
    PTSCONTROL_E_PICS_ENTRY_NOT_FOUND                        : "PTSCONTROL_E_PICS_ENTRY_NOT_FOUND",
    PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED                      : "PTSCONTROL_E_PICS_ENTRY_NOT_CHANGED",
    PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_ALREADY_REGISTERED   : "PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_ALREADY_REGISTERED",
    PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_NOT_EXPECTED_TO_FAIL : "PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_NOT_EXPECTED_TO_FAIL",
    PTSCONTROL_E_BLUETOOTH_ADDRESS_NOT_FOUND                 : "PTSCONTROL_E_BLUETOOTH_ADDRESS_NOT_FOUND",
    PTSCONTROL_E_INTERNAL_ERROR                              : "PTSCONTROL_E_INTERNAL_ERROR",
    PTSCONTROL_E_FUNCTION_NOT_IMPLEMENTED                    : "PTSCONTROL_E_FUNCTION_NOT_IMPLEMENTED",
    E_NOINTERFACE                                            : "E_NOINTERFACE",
    CO_E_SERVER_EXEC_FAILURE                                 : "CO_E_SERVER_EXEC_FAILURE",
    E_RPC_SERVER_UNAVAILABLE                                 : "E_RPC_SERVER_UNAVAILABLE",
    E_RPC_CALL_FAILED                                        : "E_RPC_CALL_FAILED",
    E_BTP_ERROR                                              : E_BTP_ERROR,
    E_XML_RPC_ERROR                                          : E_XML_RPC_ERROR,
    E_BTP_TIMEOUT                                            : E_BTP_TIMEOUT,
    E_FATAL_ERROR                                            : E_FATAL_ERROR,
}
