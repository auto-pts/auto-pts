#!/usr/bin/env python

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
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

import logging
import os
import subprocess
import sys
import time
import datetime
import collections
import serial
import autoptsclient_common as autoptsclient
import ptsprojects.zephyr as autoprojects
from ptsprojects.zephyr.iutctl import get_iut, log
import bot.common


def check_call(cmd, env=None, cwd=None, shell=True):
    """Run command with arguments.  Wait for command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets current directory before execution
    :param shell: if true, the command will be executed through the shell
    :return: returncode
    """
    executable = '/bin/bash'
    cmd = subprocess.list2cmdline(cmd)

    if sys.platform == 'win32':
        executable = None
        shell = False

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell, executable=executable)


def build_and_flash(zephyr_wd, board, tty, conf_file=None):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param tty path
    :param conf_file: configuration file to be used
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, zephyr_wd,
                                         board, conf_file)
    tester_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")

    check_call('rm -rf build/'.split(), cwd=tester_dir)

    cmd = ['west', 'build', '-p', 'auto', '-b', board]
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        cmd.extend(('--', '-DOVERLAY_CONFIG={}'.format(conf_file)))

    if sys.platform == 'win32':
        cmd = subprocess.list2cmdline(cmd)
        cmd = ['bash.exe', '-c', '-i', cmd]  # bash.exe == wsl

    check_call(cmd, cwd=tester_dir)
    check_call(['west', 'flash', '--skip-rebuild',
                '--board-dir', tty], cwd=tester_dir)


def flush_serial(tty):
    """Clear the serial port buffer
    :param tty: file path of the terminal
    :return: None
    """
    if not tty:
        return

    if sys.platform == 'win32':
        com = "COM" + str(int(tty["/dev/ttyS".__len__():]) + 1)
        ser = serial.Serial(com, 115200, timeout=5)
        ser.flushInput()
        ser.flushOutput()
    else:
        check_call(['while', 'read', '-t', '0', 'var', '<', tty, ';', 'do',
                    'continue;', 'done'])


def apply_overlay(zephyr_wd, base_conf, cfg_name, overlay):
    """Duplicates default_conf configuration file and applies overlay changes
    to it.
    :param zephyr_wd: Zephyr source path
    :param base_conf: base configuration file
    :param cfg_name: new configuration file name
    :param overlay: defines changes to be applied
    :return: None
    """
    tester_app_dir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester")
    cwd = os.getcwd()

    os.chdir(tester_app_dir)

    with open(cfg_name, 'w') as config:
        for k, v in list(overlay.items()):
            config.write("{}={}\n".format(k, v))

    os.chdir(cwd)


autopts2board = {
    None: None,
    'nrf52': 'nrf52840dk_nrf52840',
    'reel_board': 'reel_board'
}


def get_tty_path(name):
    """Returns tty path (eg. /dev/ttyUSB0) of serial device with specified name
    :param name: device name
    :return: tty path if device found, otherwise None
    """
    serial_devices = {}
    ls = subprocess.Popen(["ls", "-l", "/dev/serial/by-id"],
                          stdout=subprocess.PIPE)

    awk = subprocess.Popen("awk '{if (NF > 5) print $(NF-2), $NF}'",
                           stdin=ls.stdout,
                           stdout=subprocess.PIPE,
                           shell=True)

    end_of_pipe = awk.stdout
    for line in end_of_pipe:
        device, filepath = line.decode().rstrip().split(" ")
        serial_devices[device] = filepath

    for device, filepath in list(serial_devices.items()):
        if name in device:
            tty = os.path.basename(filepath)
            return "/dev/{}".format(tty)

    return None


def zephyr_hash_url(commit):
    """ Create URL for commit in Zephyr
    :param commit: Commit ID to append
    :return: URL of commit
    """
    return "{}/commit/{}".format(autoprojects.ZEPHYR_PROJECT_URL,
                                 commit)


def compose_mail(args, mail_cfg, mail_ctx):
    """ Create a email body
    """

    iso_cal = datetime.date.today().isocalendar()
    ww_dd_str = "WW%s.%s" % (iso_cal[1], iso_cal[2])

    body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session - {} </h1>
    <h2>1. IUT Setup</h2>
    <p><b> Type:</b> Zephyr <br>
    <b> Board:</b> {} <br>
    <b> Source:</b> {} </p>
    <h2>2. PTS Setup</h2>
    <p><b> OS:</b> Windows 10 <br>
    <b> Platform:</b> VirtualBox <br>
    <b> Version:</b> {} </p>
    <h2>3. Test Results</h2>
    <p><b>Execution Time</b>: {}</p>
    {}
    {}
    <h3>Logs</h3>
    {}
    <p>Sincerely,</p>
    <p> {}</p>
    '''.format(ww_dd_str, args["board"], mail_ctx["zephyr_hash"],
               args['pts_ver'], mail_ctx["elapsed_time"], mail_ctx["summary"],
               mail_ctx["regression"], mail_ctx["log_url"], mail_cfg['name'])

    if 'subject' in mail_cfg:
        subject = mail_cfg['subject']
    else:
        subject = "AutoPTS test session results"

    subject = "%s - %s" % (subject, ww_dd_str)

    return subject, body


class ZephyrBotConfigArgs(bot.common.BotConfigArgs):
    def __init__(self, args):
        super().__init__(args)
        self.board_name = args['board']
        self.tty_file = args['tty_file']


class ZephyrBotCliParser(bot.common.BotCliParser):
    def __init__(self, add_help=True):
        super().__init__(description="PTS automation client",
                         board_names=autoprojects.iutctl.Board.names,
                         add_help=add_help)


class ZephyrBotClient(bot.common.BotClient):
    def __init__(self):
        super().__init__(get_iut, 'zephyr', autoprojects.iutctl.Board.names)
        self.arg_parser = ZephyrBotCliParser()
        self.parse_config = ZephyrBotConfigArgs
        self.config_default = "prj.conf"

    def apply_config(self, args, config, value):
        if 'overlay' in value:
            apply_overlay(args.project_path, self.config_default, config,
                          value['overlay'])

        log("TTY path: %s" % args.tty_file)

        if not args.no_build:
            build_and_flash(args.project_path, autopts2board[args.board_name],
                            args.tty_file, config)

            flush_serial(args.tty_file)
            time.sleep(10)


class ZephyrClient(autoptsclient.Client):
    def __init__(self):
        super().__init__(get_iut, 'zephyr', autoprojects.iutctl.Board.names)


SimpleClient = ZephyrClient
BotCliParser = ZephyrBotCliParser


def main(cfg):

    bot.common.pre_cleanup()

    start_time = time.time()

    args = cfg['auto_pts']
    args['kernel_image'] = os.path.join(args['project_path'], 'tests',
                                        'bluetooth', 'tester', 'outdir',
                                        'zephyr', 'zephyr.elf')

    if 'git' in cfg:
        zephyr_hash = bot.common.update_repos(args['project_path'],
                                              cfg['git'])['zephyr']
    else:
        zephyr_hash = {'desc': '', 'commit': ''}

    if 'ykush' in args:
        autoptsclient.board_power(args['ykush'], True)
        time.sleep(1)

    args['tty_file'], jlink_srn = bot.common.get_free_device()

    try:
        summary, results, descriptions, regressions = \
            ZephyrBotClient().run_tests(args, cfg.get('iut_config', {}))
    except Exception as e:
        bot.common.release_device(jlink_srn)
        raise e

    bot.common.release_device(jlink_srn)
    results = collections.OrderedDict(sorted(results.items()))

    report_file = bot.common.make_report_xlsx(results, summary, regressions,
                                              descriptions)
    report_txt = bot.common.make_report_txt(results, zephyr_hash["desc"])
    logs_folder = bot.common.archive_testcases("logs")

    end_time = time.time()
    url = None

    if 'gdrive' in cfg:
        drive = bot.common.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload(report_file)
        drive.upload(report_txt)
        drive.upload_folder(logs_folder)
        drive.upload("TestCase.db")
        bot.common.upload_bpv_logs(drive, ZephyrBotConfigArgs(args))

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {"summary": bot.common.status_dict2summary_html(summary),
                    "regression": bot.common.regressions2html(regressions,
                                                              descriptions)}

        # Summary

        # Regression and test case description

        # Zephyr commit id link in HTML format

        # Commit id may have "-dirty" if the source is dirty.
        commit_id = zephyr_hash["commit"]
        if commit_id.endswith('-dirty'):
            commit_id = commit_id[:-6]
        mail_ctx["zephyr_hash"] = bot.common.url2html(zephyr_hash_url(commit_id),
                                                      zephyr_hash["desc"])

        # Log in Google drive in HTML format
        if 'gdrive' in cfg and url:
            mail_ctx["log_url"] = bot.common.url2html(url, "Results on Google Drive")
        else:
            mail_ctx["log_url"] = "Not Available"

        # Elapsed Time
        mail_ctx["elapsed_time"] = str(datetime.timedelta(
                                       seconds=(end_time - start_time)))

        subject, body = compose_mail(args, cfg['mail'], mail_ctx)

        bot.common.send_mail(cfg['mail'], subject, body,
                             [report_file, report_txt])

        print("Done")

    bot.common.cleanup()

    print("\nBye!")
    sys.stdout.flush()
    return 0
