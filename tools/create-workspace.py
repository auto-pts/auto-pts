#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

"""Windows IronPython script to create PTS workspace

The workspace is created using *.pts file from the Test Plan Generator.

Run this script as follows:

cd auto-pts
ipy ./tools/create-workspace.py ./workspaces/pts_file.pts ./workspaces

"""

import os
import re
import sys
import time
import logging
import argparse
import fileinput

import Interop.PTSControl as PTSControl
import clr
import System

from autopts.ptsprojects import ptstypes

# load the PTS interop assembly
clr.AddReferenceToFile("Interop.PTSControl.dll")

log = logging.debug


class PyPTSControl:
    """PTS control interface.

    This class contains cherry picked functionality from ptscontrol.PyPTS

    """

    def __init__(self):
        self.pts = None

        # This is done to have valid pts in case client does not restart_pts
        # and uses other methods. Normally though, the client should
        # restart_pts, see its docstring for the details
        #
        # Another reason: PTS starting from version 6.2 returns
        # PTSCONTROL_E_IMPLICIT_SEND_CALLBACK_ALREADY_REGISTERED 0x849C004 in
        # RegisterImplicitSendCallbackEx if PTS from previous autoptsserver is
        # used
        self.restart_pts()

    def restart_pts(self):
        """Restarts PTS

        Timeouts break some PTS functionality, hence it is good idea to start a
        new instance of PTS every time. For details see:

        https://www.bluetooth.org/pts/issues/view_issue.cfm?id=13794

        This function will block for couple of seconds while PTS starts

        """

        log("%s", self.restart_pts.__name__)

        self.stop_pts()
        time.sleep(3)  # otherwise there are COM errors occasionally
        self.start_pts()

    def start_pts(self):
        """Starts PTS

        This function will block for couple of seconds while PTS starts"""

        log("%s", self.start_pts.__name__)

        self.pts = PTSControl.PTSControlClass()

    def stop_pts(self):
        """Stops PTS"""

        log("%s", self.stop_pts.__name__)

        pts_process_list = System.Diagnostics.Process.GetProcessesByName("PTS")

        log("Got PTS process list: %s", pts_process_list)

        # in reality there should be only one pts process
        for pts_process in pts_process_list:
            log("About to kill PTS process: %s", pts_process)
            try:
                pts_process.CloseMainWindow()
                pts_process.WaitForExit()
                pts_process.Close()
            except Exception as error:
                log("Exception when killing PTS process: %r", error)


def parse_args():
    """Parse command line arguments and options"""

    arg_parser = argparse.ArgumentParser(
        description="IronPython script to create PTS workspace")

    arg_parser.add_argument("pts_file_path",
                            help="Path of PTS (with .pts extension) file")

    arg_parser.add_argument("workspace_path",
                            help="The path to the folder where the new "
                                 "workspace should be created")

    arg_parser.add_argument("-i", "--iut-bd-addr",
                            help="A 64 bit unsigned integer that contains the "
                                 "Bluetooth Device Address (BDADDR) of the "
                                 "Implementation Under Test (IUT). By default fake "
                                 "address will be used.")

    arg_parser.add_argument("-w", "--workspace-name",
                            help="The name of the workspace to be created."
                                 "By default the name of PTS file will be used.")

    args = arg_parser.parse_args()

    return args


def file_line_count(file_name):
    """Return line count of a file"""
    with open(file_name) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def patch_workspace_file(workspace_file):
    """Patch workspace file to remove invalid information

    The information removed is:
    PATH='C:\\PATH\\auto-pts\\workspaces\\qsd_zephyr_mv11_20160623'

    It is replaced with
    PATH=""

    This information is not valid on other machines, hence it is removed

    """
    log("%s %s", patch_workspace_file.__name__, workspace_file)

    line_count = file_line_count(workspace_file)

    for line in fileinput.input(workspace_file, inplace=1):
        line = line.rstrip()

        if "PATH=" in line:
            line = re.sub('PATH=".*?"', 'PATH=""', line)

        # pristine workspace file does not have newline at end of file
        if fileinput.filelineno() == line_count:
            print(line, end=' ')
        else:
            print(line)


def init_logging():
    """Initialize logging"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # log to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    format_template = "%(asctime)s %(levelname)s : %(message)s"
    formatter = logging.Formatter(format_template)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def main():
    """Main."""
    init_logging()

    args = parse_args()

    # absolute (full) path is required
    pts_file_path = os.path.abspath(args.pts_file_path)
    workspace_path = os.path.abspath(args.workspace_path)

    if args.iut_bd_addr:
        iut_bd_addr = int(args.iut_bd_addr, base=16)
    else:
        iut_bd_addr = 0xABCDEF1234

    if args.workspace_name:
        workspace_name = args.workspace_name
    else:
        workspace_name = (
                "autopts_" + os.path.basename(os.path.splitext(pts_file_path)[0]))

    workspace_dir = os.path.join(workspace_path, workspace_name)
    workspace_file = os.path.join(workspace_dir, workspace_name + ".pqw6")

    # if workspace exits PTS throws:
    # PTSCONTROL_E_FAILED_TO_CREATE_WORKSPACE 0x849C0003
    if os.path.exists(workspace_dir):
        sys.exit("Workspace %r exist!" % workspace_file)

    pts_control = PyPTSControl()
    pts = pts_control.pts

    log("CreateWorkspace %r, %r, %r, %r",
        iut_bd_addr, pts_file_path, workspace_name, workspace_path)

    try:
        pts.CreateWorkspace(iut_bd_addr, pts_file_path, workspace_name,
                            workspace_path)

        patch_workspace_file(workspace_file)

    except System.Runtime.InteropServices.COMException as exc:
        log("Exception in CreateWorkspace")
        log(exc)

        hresult = int(System.UInt32(exc.HResult))
        error_code = ptstypes.PTSCONTROL_E_STRING[hresult]
        log("Error code: %s", error_code)

    pts_control.stop_pts()


if __name__ == "__main__":
    main()
