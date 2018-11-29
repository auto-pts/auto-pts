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
    pairs = map(lambda l: l.decode('UTF-8').rstrip().split('=', 1), lines)
    valid_pairs = filter(_validate_pair, pairs)
    env = dict(valid_pairs)
    p.communicate()

    # Those are not properly parsed, remove them, we don't need them
    env.pop('BASH_FUNC_module%%', None)
    env.pop('BASH_FUNC_scl%%', None)

    return env


def build_and_flash(zephyr_wd, board, conf_file=None):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param conf_file: configuration file to be used
    :return: None
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
    check_call(['nrfjprog', '--eraseall', '-f', 'nrf52'])
    check_call(['nrfjprog', '--program', 'zephyr/zephyr.hex', '-f', 'nrf52'],
               cwd=tester_outdir)
    check_call(['nrfjprog', '-p'])


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
    'nrf52': 'nrf52840_pca10056'
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

    tty = get_tty_path("J-Link")
    callback_thread = autoptsclient.init_core()

    ptses = []
    for ip in args["server_ip"]:
        ptses.append(autoptsclient.init_pts(ip,
                                            args["workspace"],
                                            args["bd_addr"],
                                            args["enable_max_logs"],
                                            callback_thread,
                                            "zephyr_" + str(args["board"])))

    btp.init(get_iut)
    # Main instance of PTS
    pts = ptses[0]

    stack.init_stack()
    stack_inst = stack.get_stack()
    stack_inst.synch_init(callback_thread.set_pending_response,
                          callback_thread.clear_pending_responses)
    cache = autoptsclient.cache_workspace(pts)

    default_conf = None
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

        build_and_flash(args["project_path"], autopts2board[args["board"]],
                        config)
        flush_serial(tty)
        time.sleep(10)

        autoprojects.iutctl.init(args["kernel_image"], tty, args["board"])

        test_cases, additional_test_cases = get_test_cases(ptses)
        if to_run or to_omit:
            test_cases = autoptsclient.get_test_cases_subset(test_cases,
                                                             to_run, to_omit)

        status_count, results_dict, regressions = autoptsclient.run_test_cases(
            ptses, test_cases, additional_test_cases, int(args["retry"]))

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

    return status, results, descriptions, regressions


def main(cfg):
    args = cfg['auto_pts']
    args['kernel_image'] = os.path.join(args['project_path'], 'tests',
                                        'bluetooth', 'tester', 'outdir',
                                        'zephyr', 'zephyr.elf')

    zephyr_hash = \
        bot.common.update_sources(os.path.abspath(args['project_path']),
                                  'upstream')

    summary, results, descriptions, regressions = \
        run_tests(args, cfg.get('iut_config', {}))

    report_file = bot.common.make_report_xlsx(results, summary, regressions,
                                              descriptions)
    logs_file = bot.common.archive_recursive("logs")

    if 'gdrive' in cfg:
        drive = bot.common.Drive(cfg['gdrive'])
        url = drive.new_workdir(args['board'])
        drive.upload(report_file)
        drive.upload(logs_file)
        drive.upload("TestCase.db")

    if 'mail' in cfg:
        summary_html = bot.common.status_dict2summary_html(summary)
        url_html = bot.common.url2html(url, "Results on Google Drive")

        # Provide test case description
        _regressions = []
        for name in regressions:
            _regressions.append(
                name + " - " + descriptions.get(name, "no description"))

        reg_html = bot.common.regressions2html(_regressions)
        bot.common.send_mail(cfg['mail'], None, zephyr_hash, args["board"],
                             [summary_html, reg_html, url_html])

    bot.common.cleanup()

    print("\nBye!")
    sys.stdout.flush()
    return 0
