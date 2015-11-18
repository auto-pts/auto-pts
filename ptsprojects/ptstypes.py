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
