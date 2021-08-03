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
import datetime
import logging
import os
import subprocess
import sys
import time

import autoptsclient_common as autoptsclient
import ptsprojects.mynewt as autoprojects
import ptsprojects.stack as stack
from pybtp import btp
from ptsprojects.mynewt.iutctl import get_iut

import bot.common


def check_call(cmd, env=None, cwd=None, shell=True):
    """Run command with arguments.  Wait for command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets current directory before execution
    :param shell: if true, the command will be executed through the shell
    :return: returncode
    """
    cmd = subprocess.list2cmdline(cmd)

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell)


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
        device, serial = line.decode().rstrip().split(" ")
        serial_devices[device] = serial

    for device, serial in list(serial_devices.items()):
        if name in device:
            tty = os.path.basename(serial)
            return "/dev/{}".format(tty)

    return None


def build_and_flash(project_path, board, overlay=None):
    """Build and flash Mynewt binary
    :param project_path: Mynewt source path
    :param board: IUT
    :param overlay: configuration map to be used
    :return: TTY path
    """
    logging.debug("%s: %s %s %s", build_and_flash.__name__, project_path,
                  board, overlay)

    check_call('rm -rf bin/'.split(), cwd=project_path)
    check_call('rm -rf targets/{}_boot/'.format(board).split(),
               cwd=project_path)
    check_call('rm -rf targets/bttester/'.split(), cwd=project_path)

    check_call('newt target create {}_boot'.format(board).split(),
               cwd=project_path)
    check_call('newt target create bttester'.split(), cwd=project_path)

    check_call(
        'newt target set {0}_boot bsp=@apache-mynewt-core/hw/bsp/{0}'.format(
            board).split(), cwd=project_path)
    check_call(
        'newt target set {}_boot app=@mcuboot/boot/mynewt'.format(
            board).split(), cwd=project_path)

    check_call(
        'newt target set bttester bsp=@apache-mynewt-core/hw/bsp/{}'.format(
            board).split(), cwd=project_path)
    check_call(
        'newt target set bttester app=@apache-mynewt-nimble/apps/bttester'.split(),
        cwd=project_path)

    if overlay is not None:
        config = ':'.join(['{}={}'.format(k, v) for k, v in list(overlay.items())])
        check_call('newt target set bttester syscfg={}'.format(config).split(),
                   cwd=project_path)

    check_call('newt build {}_boot'.format(board).split(), cwd=project_path)
    check_call('newt build bttester'.split(), cwd=project_path)

    check_call('newt create-image -2 {}_boot timestamp'.format(board).split(),
               cwd=project_path)
    check_call('newt create-image -2 bttester timestamp'.split(), cwd=project_path)

    check_call('newt load {}_boot'.format(board).split(), cwd=project_path)
    check_call('newt load bttester'.split(), cwd=project_path)

    return get_tty_path("J-Link")


def get_target_description(project_path):
    return subprocess.check_output('newt target show bttester', shell=True,
                                   cwd=project_path)


def get_target_config(project_path):
    return subprocess.check_output('newt target config flat bttester',
                                   shell=True, cwd=project_path)


def get_newt_info(project_path):
    return subprocess.check_output('newt info',
                                   shell=True, cwd=project_path)


def get_newt_version(project_path):
    return subprocess.check_output('newt version',
                                   shell=True, cwd=project_path)


def get_build_info_file(project_path):
    file_name = "build_info.txt"
    build_info_str = ''

    build_info_str += 'newt info:\n'
    build_info_str += bytes.hex(get_newt_info(project_path))
    build_info_str += '\n'

    build_info_str += 'newt version:\n'
    build_info_str += bytes.hex(get_newt_version(project_path))
    build_info_str += '\n'

    build_info_str += 'newt target show:\n'
    build_info_str += bytes.hex(get_target_description(project_path))
    build_info_str += '\n'

    build_info_str += 'newt target config:\n'
    build_info_str += bytes.hex(get_target_config(project_path))
    build_info_str += '\n'

    with open(file_name, "w") as text_file:
        text_file.write(build_info_str)

    return file_name


def make_repo_status(repos_info):
    status_list = []

    for name, info in list(repos_info.items()):
        status_list.append('{}={}'.format(name, info['commit']))

    return ', '.join(status_list)


class PtsInitArgs:
    """
    Translates arguments provided in 'config.py' file to be used by
    'autoptsclient.init_pts' function
    """

    def __init__(self, args):
        self.workspace = args["workspace"]
        self.bd_addr = args["bd_addr"]
        self.enable_max_logs = args.get('enable_max_logs', False)
        self.retry = args.get('retry', 0)
        self.stress_test = args.get('stress_test', False)
        self.test_cases = []
        self.excluded = []
        self.srv_port = args.get('srv_port', [65000])
        self.cli_port = args.get('cli_port', [65001])
        self.ip_addr = args.get('server_ip', ['127.0.0.1'] * len(self.srv_port))
        self.local_addr = args.get('local_ip', ['127.0.0.1'] * len(self.cli_port))
        self.ykush = args.get('ykush', None)
        self.recovery = args.get('recovery', False)
        self.superguard = 60 * float(args.get('superguard', 0))


def run_tests(args, iut_config):
    """Run test cases
    :param args: AutoPTS arguments
    :param iut_config: IUT configuration
    :return: tuple of (status, results) dictionaries
    """
    results = {}
    status = {}
    descriptions = {}
    total_regressions = []
    _args = {}

    config_default = "default.conf"
    _args[config_default] = PtsInitArgs(args)

    for config, value in list(iut_config.items()):
        if 'test_cases' not in value:
            # Rename default config
            _args[config] = _args.pop(config_default)
            config_default = config
            continue

        if config != config_default:
            _args[config] = PtsInitArgs(args)

        _args[config].test_cases = value.get('test_cases', [])

        if 'overlay' in value:
            _args[config_default].excluded += _args[config].test_cases

    while True:
        try:
            ptses = autoptsclient.init_pts(_args[config_default],
                                           "mynewt_" + str(args["board"]))

            btp.init(get_iut)

            # Main instance of PTS
            pts = ptses[0]

            # Read PTS Version and keep it for later use
            args['pts_ver'] = "%s" % pts.get_version()
        except Exception as exc:
            logging.exception(exc)
            if _args[config_default].recovery:
                ptses = exc.args[1]
                for pts in ptses:
                    autoptsclient.recover_autoptsserver(pts)
                time.sleep(20)
                continue
            raise exc
        break

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init([pts.callback_thread for pts in ptses])

    for config, value in list(iut_config.items()):
        overlay = None

        if 'overlay' in value:
            overlay = value['overlay']

        tty = build_and_flash(args["project_path"], args["board"], overlay)
        logging.debug("TTY path: %s",  tty)

        time.sleep(10)

        autoprojects.iutctl.init(tty, args["board"])

        # Setup project PIXITS
        autoptsclient.setup_project_name('mynewt')
        autoptsclient.setup_project_pixits(ptses)

        test_cases = autoptsclient.setup_test_cases(ptses)

        status_count, results_dict, regressions = autoptsclient.run_test_cases(
            ptses, test_cases, _args[config])
        total_regressions += regressions

        for k, v in list(status_count.items()):
            if k in list(status.keys()):
                status[k] += v
            else:
                status[k] = v

        results.update(results_dict)
        autoprojects.iutctl.cleanup()

    for test_case_name in list(results.keys()):
        project_name = test_case_name.split('/')[0]
        descriptions[test_case_name] = \
            pts.get_test_case_description(project_name, test_case_name)

    autoptsclient.shutdown_pts(ptses)

    return status, results, descriptions, total_regressions


def compose_mail(args, mail_cfg, mail_ctx):
    """ Create a email body
    """

    body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session</h1>
    <h2>1. IUT Setup</h2>
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
    '''.format(args["board"], mail_ctx["mynewt_repo_status"],
               args['pts_ver'], mail_ctx["elapsed_time"], mail_ctx["summary"],
               mail_ctx["regression"], mail_ctx["log_url"], mail_cfg['name'])

    subject = "[Mynewt Nimble] AutoPTS test session results"

    return subject, body


def main(cfg):
    print("Mynewt bot start!")

    bot.common.pre_cleanup()

    start_time = time.time()

    args = cfg['auto_pts']

    if 'git' in cfg:
        repos_info = bot.common.update_repos(args['project_path'], cfg["git"])
        repo_status = make_repo_status(repos_info)
    else:
        repo_status = ''

    summary, results, descriptions, regressions = \
        run_tests(args, cfg.get('iut_config', {}))

    report_file = bot.common.make_report_xlsx(results, summary, regressions,
                                              descriptions)
    report_txt = bot.common.make_report_txt(results, repo_status)
    logs_folder = bot.common.archive_testcases("logs")

    build_info_file = get_build_info_file(os.path.abspath(args['project_path']))

    end_time = time.time()
    url = None

    if 'gdrive' in cfg:
        drive = bot.common.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload(report_file)
        drive.upload(report_txt)
        drive.upload_folder(logs_folder)
        drive.upload(build_info_file)
        drive.upload("TestCase.db")
        bot.common.upload_bpv_logs(drive, PtsInitArgs(args))

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {"summary": bot.common.status_dict2summary_html(summary),
                    "regression": bot.common.regressions2html(regressions,
                                                              descriptions), "mynewt_repo_status": repo_status}

        # Summary

        # Regression and test case description

        # Log in Google drive in HTML format
        if 'gdrive' in cfg and url:
            mail_ctx["log_url"] = bot.common.url2html(url,
                                                      "Results on Google Drive")
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
