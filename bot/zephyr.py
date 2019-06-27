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
import re
import subprocess
import sys
import time
import datetime
import collections

import autoptsclient_common as autoptsclient
import ptsprojects.zephyr as autoprojects
import ptsprojects.stack as stack
from pybtp import btp
from ptsprojects.zephyr.iutctl import get_iut

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


def _validate_pair(ob):
    try:
        if not (len(ob) == 2):
            raise ValueError
    except BaseException:
        return False

    return True


def source_zephyr_env(zephyr_wd):
    """Sets the project environment variables
    :param zephyr_wd: Zephyr source path
    :return: environment variables set
    """
    logging.debug("{}: {}".format(source_zephyr_env.__name__, zephyr_wd))

    cmd = ['source', './zephyr-env.sh', '&&', 'env']
    cmd = subprocess.list2cmdline(cmd)

    p = subprocess.Popen(cmd, cwd=zephyr_wd, shell=True,
                         stdout=subprocess.PIPE)

    lines = p.stdout.readlines()
    # XXX: Doesn't parse functions for now
    filtered_lines = filter(lambda x: (not x.startswith(('BASH_FUNC',
                                                         ' ', '}'))), lines)
    pairs = map(lambda l: l.decode('UTF-8').rstrip().split('=', 1),
                filtered_lines)
    valid_pairs = filter(_validate_pair, pairs)
    env = dict(valid_pairs)
    p.communicate()

    return env


def flash_nrf52(tester_outdir):
    """ Flash Zephyr binary for nrf52 board
    :param cwd: Zephyr build directory
    :return: TTY path
    """
    check_call(['nrfjprog', '--eraseall', '-f', 'nrf52'])
    check_call(['nrfjprog', '--program', 'zephyr/zephyr.hex', '-f', 'nrf52'],
               cwd=tester_outdir)
    check_call(['nrfjprog', '-p'])

    return get_tty_path("J-Link")



def flash_reel(tester_outdir):
    """ Flash Zephyr binary for reel board
    :param cwd: Zephyr build directory
    :return: TTY path
    """
    check_call(['pyocd', 'flash', '-t', 'nrf52', 'zephyr/zephyr.hex'],
               cwd=tester_outdir)

    return get_tty_path("DAPLink")


def build_and_flash(zephyr_wd, board, conf_file=None):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param conf_file: configuration file to be used
    :return: TTY path
    """
    logging.debug("{}: {} {} {}". format(build_and_flash.__name__, zephyr_wd,
                                         board, conf_file))
    tester_outdir = os.path.join(zephyr_wd, "tests", "bluetooth", "tester",
                                 "outdir")

    if os.path.isdir(tester_outdir):
        check_call(['rm', '-rf', tester_outdir], cwd=zephyr_wd)

    os.makedirs(tester_outdir)

    # Set Zephyr project env variables
    env = source_zephyr_env(zephyr_wd)

    cmd = ['cmake', '-GNinja', '-DBOARD={}'.format(board)]
    if conf_file:
        cmd.append('-DCONF_FILE={}'.format(conf_file))
    cmd.append('..')

    check_call(cmd, env=env, cwd=tester_outdir)
    check_call(['ninja'], env=env, cwd=tester_outdir)

    if board == 'nrf52840_pca10056':
        tty = flash_nrf52(tester_outdir)
    elif board == 'reel_board':
        tty = flash_reel(tester_outdir)
    else:
        # Unsupported board and stop here
        tty = None

    return tty

def flush_serial(tty):
    """Clear the serial port buffer
    :param tty: file path of the terminal
    :return: None
    """
    if not tty:
        return

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

    with open(base_conf, 'r') as base:
        with open(cfg_name, 'w') as config:
            for line in base.readlines():
                re_config = re.compile(
                    r'(?P<config_key>\w+)=(?P<config_value>\w+)*')
                match = re_config.match(line)
                if match and match.group('config_key') in overlay:
                    v = overlay.pop(match.group('config_key'))
                    config.write(
                        "{}={}\n".format(
                            match.group('config_key'), v))
                else:
                    config.write(line)

            # apply what's left
            for k, v in overlay.items():
                config.write("{}={}\n".format(k, v))

    os.chdir(cwd)


autopts2board = {
    None: None,
    'nrf52': 'nrf52840_pca10056',
    'reel_board' : 'reel_board'
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
        device, serial = line.decode().rstrip().split(" ")
        serial_devices[device] = serial

    for device, serial in serial_devices.items():
        if name in device:
            tty = os.path.basename(serial)
            return "/dev/{}".format(tty)

    return None


def get_test_cases(ptses):
    """Get all test cases
    :param pts: PTS proxy instance
    :return: ZTestCase list
    """
    test_cases = autoprojects.gap.test_cases(ptses[0])
    test_cases += autoprojects.gatt.test_cases(ptses[0])
    test_cases += autoprojects.sm.test_cases(ptses[0])
    test_cases += autoprojects.l2cap.test_cases(ptses[0])
    mesh_test_cases, additional_mesh_test_cases = \
        autoprojects.mesh.test_cases(ptses)
    test_cases += mesh_test_cases
    additional_test_cases = additional_mesh_test_cases

    return test_cases, additional_test_cases


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

    callback_thread = autoptsclient.init_core()

    ptses = []
    for ip, local in zip(args['server_ip'], args['local_ip']):
        ptses.append(autoptsclient.init_pts(ip,
                                            args["workspace"],
                                            args["bd_addr"],
                                            args["enable_max_logs"],
                                            callback_thread,
                                            "zephyr_" + str(args["board"]),
                                            local))

    btp.init(get_iut)
    # Main instance of PTS
    pts = ptses[0]

    # Read PTS Version and keep it for later use
    args['pts_ver'] = "%s" % pts.get_version()

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init(callback_thread.set_pending_response,
                          callback_thread.clear_pending_responses)
    cache = autoptsclient.cache_workspace(pts)

    default_conf = "default.conf"
    default_to_omit = []

    for config, value in iut_config.items():
        for test_case in value.get('test_cases', []):
            default_to_omit.append(test_case)
        if 'test_cases' not in value:
            default_conf = config

    for config, value in iut_config.items():
        if 'overlay' in value:
            apply_overlay(args["project_path"], default_conf, config,
                          value['overlay'])
            to_run = value['test_cases']
            to_omit = None
        elif 'test_cases' not in value:  # DEFAULT CASE
            to_run = None
            to_omit = default_to_omit
        else:
            continue

        tty = build_and_flash(args["project_path"], autopts2board[args["board"]],
                        config)
        logging.debug("TTY path: %s" % tty)

        flush_serial(tty)
        time.sleep(10)

        autoprojects.iutctl.init(args["kernel_image"], tty, args["board"])

        # Setup project PIXITS
        autoprojects.gap.set_pixits(ptses[0])
        autoprojects.gatt.set_pixits(ptses[0])
        autoprojects.sm.set_pixits(ptses[0])
        autoprojects.l2cap.set_pixits(ptses[0])
        autoprojects.mesh.set_pixits(ptses)

        test_cases, additional_test_cases = get_test_cases(ptses)
        if to_run or to_omit:
            test_cases = autoptsclient.get_test_cases_subset(test_cases,
                                                             to_run, to_omit)

        status_count, results_dict, regressions = autoptsclient.run_test_cases(
            ptses, test_cases, additional_test_cases, int(args["retry"]))
        total_regressions += regressions

        for k, v in status_count.items():
            if k in status.keys():
                status[k] += v
            else:
                status[k] = v

        results.update(results_dict)
        autoprojects.iutctl.cleanup()

    for test_case_name in results.keys():
        descriptions[test_case_name] = \
            autoptsclient.get_test_case_description(cache, test_case_name)

    autoptsclient.cache_cleanup(cache)

    pts.unregister_xmlrpc_ptscallback()

    return status, results, descriptions, total_regressions


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

def main(cfg):

    start_time = time.time()

    args = cfg['auto_pts']
    args['kernel_image'] = os.path.join(args['project_path'], 'tests',
                                        'bluetooth', 'tester', 'outdir',
                                        'zephyr', 'zephyr.elf')

    zephyr_hash = bot.common.update_repos(args['project_path'],
                                          cfg["git"])['zephyr']

    summary, results, descriptions, regressions = \
        run_tests(args, cfg.get('iut_config', {}))

    results = collections.OrderedDict(sorted(results.items()))

    report_file = bot.common.make_report_xlsx(results, summary, regressions,
                                              descriptions)
    report_txt = bot.common.make_report_txt(results, zephyr_hash["desc"])
    logs_file = bot.common.archive_recursive("logs")

    end_time = time.time()

    if 'gdrive' in cfg:
        drive = bot.common.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload(report_file)
        drive.upload(report_txt)
        drive.upload(logs_file)
        drive.upload("TestCase.db")

    if 'mail' in cfg:
        print("Sending email ...")

        # keep mail related context to simplify the code
        mail_ctx = {}

        # Summary
        mail_ctx["summary"] = bot.common.status_dict2summary_html(summary)

        # Regression and test case description
        mail_ctx["regression"] = bot.common.regressions2html(regressions,
                                                             descriptions)

        # Zephyr commit id link in HTML format

        # Commit id may have "-dirty" if the source is dirty.
        commit_id = zephyr_hash["commit"]
        if commit_id.endswith('-dirty'):
            commit_id = commit_id[:-6]
        mail_ctx["zephyr_hash"] = bot.common.url2html(zephyr_hash_url(commit_id),
                                                      zephyr_hash["desc"])

        # Log in Google drive in HTML format
        if 'gdrive' in cfg:
            mail_ctx["log_url"] = bot.common.url2html(url, "Results on Google Drive")
        else:
            mail_ctx["log_url"] = "Not Available"

        # Elapsed Time
        mail_ctx["elapsed_time"] = str(datetime.timedelta(
                                       seconds = (end_time - start_time)))

        subject, body = compose_mail(args, cfg['mail'], mail_ctx)

        bot.common.send_mail(cfg['mail'], subject, body,
                             [report_file, report_txt])

        print("Done")

    bot.common.cleanup()

    print("\nBye!")
    sys.stdout.flush()
    return 0
