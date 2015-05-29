"""Incomplete wrapper around btmgmt. The functions are added as needed."""

from ptsprojects.utils import exec_iut_cmd

def power_off():
    exec_iut_cmd("btmgmt power off", True)

def power_on():
    exec_iut_cmd("btmgmt power on", True)

def advertising_on():
    exec_iut_cmd("btmgmt advertising on", True)

def advertising_off():
    exec_iut_cmd("btmgmt advertising off", True)

def connectable_on():
    exec_iut_cmd("btmgmt connectable on", True)

def connectable_off():
    exec_iut_cmd("btmgmt connectable off", True)

def bondable_on():
    exec_iut_cmd("btmgmt bondable on", True)

def bondable_off():
    exec_iut_cmd("btmgmt bondable off", True)

def discoverable_on():
    exec_iut_cmd("btmgmt discov on", True)

def discoverable_off():
    exec_iut_cmd("btmgmt discov off", True)

def discoverable_limited(limit):
    exec_iut_cmd("btmgmt discov limited %d" % limit, True)

def bredr_on():
    exec_iut_cmd("btmgmt bredr on", True)

def bredr_off():
    exec_iut_cmd("btmgmt bredr off", True)
