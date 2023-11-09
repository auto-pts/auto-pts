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
import copy
import importlib
import logging
import os
import subprocess
import sys
import shutil

from pathlib import Path
from argparse import Namespace
from autopts import client as autoptsclient
from autopts.client import CliParser, Client, TestCaseRunStats, init_logging
from autopts.ptsprojects.boards import get_free_device, get_tty, get_debugger_snr
from autopts.ptsprojects.testcase_db import DATABASE_FILE

PROJECT_DIR = os.path.dirname(  # auto-pts repo directory
                os.path.dirname(  # autopts module directory
                    os.path.dirname(  # bot module directory
                        os.path.abspath(__file__))))  # this file directory

log = logging.debug


class BotCliParser(CliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_argument('--nb', dest='no_build', action='store_true',
                          help='Skip build and flash in bot mode.', default=False)

        self.add_argument('--simple', action='store_true',
                          help='Skip build and flash in bot mode.', default=False)

    def add_positional_args(self):
        self.add_argument("config_path", nargs='?', default='config.py',
                          help="Path to config.py to use for testing.")


class BotConfigArgs(Namespace):
    """
    Translates arguments provided in 'config.py' file as dictionary
    into a namespace used by common Client.
    """

    def __init__(self, args, **kwargs):
        super().__init__(**kwargs)
        self.workspace = args['workspace']
        self.project_path = args['project_path']
        self.srv_port = args.get('srv_port', [65000])
        self.cli_port = args.get('cli_port', [65001])
        self.ip_addr = args.get('server_ip', ['127.0.0.1'] * len(self.srv_port))
        self.local_addr = args.get('local_ip', ['127.0.0.1'] * len(self.cli_port))
        self.server_count = args.get('server_count', len(self.cli_port))
        self.tty_file = args.get('tty_file', None)
        self.debugger_snr = args.get('debugger_snr', None)
        self.kernel_image = args.get('kernel_image', None)
        self.database_file = args.get('database_file', DATABASE_FILE)
        self.store = args.get('store', False)
        self.rtt_log = args.get('rtt_log', False)
        self.btmon = args.get('btmon', False)
        self.device_core = args.get('device_core', 'NRF52840_XXAA')
        self.test_cases = []
        self.excluded = []

        self.bd_addr = args.get('bd_addr', '')
        self.enable_max_logs = args.get('enable_max_logs', False)
        self.retry = args.get('retry', 0)
        self.stress_test = args.get('stress_test', False)
        self.ykush = args.get('ykush', None)
        self.recovery = args.get('recovery', False)
        self.superguard = float(args.get('superguard', 0))
        self.cron_optim = args.get('cron_optim', False)
        self.project_repos = args.get('repos', None)
        self.test_case_limit = args.get('test_case_limit', 0)
        self.simple_mode = args.get('simple_mode', False)
        self.server_args = args.get('server_args', None)

        if self.server_args is not None:
            from autoptsserver import SvrArgumentParser
            _server_args = SvrArgumentParser(
                "PTS automation server").parse_args(self.server_args.split())
            _server_args.builtin_server = True
            self.server_args = []
            for i in range(len(_server_args.srv_port)):
                args_copy = copy.deepcopy(_server_args)
                args_copy.srv_port = _server_args.srv_port[i]
                args_copy.ykush = _server_args.ykush[i] if _server_args.ykush else None
                args_copy.dongle = _server_args.dongle[i] if _server_args.dongle else None
                self.server_args.append(args_copy)


class BotClient(Client):
    def __init__(self, get_iut, project, name, bot_config_class=BotConfigArgs,
                 parser_class=BotCliParser):
        # Please extend this bot client
        super().__init__(get_iut, project, name, parser_class)
        # Parser of the bot configuration dictionary loaded from config.py
        self.parse_config = bot_config_class
        # The bot configuration dictionary. It will be parsed and overlayed
        # with cli arguments into self.args namespace.
        self.bot_config = None
        # Name of the default .conf file in the iut_config.
        self.config_default = "default.conf"
        # The iut_config dictionary loaded from config.py
        self.iut_config = None

    def parse_or_find_tty(self, args):
        if args.tty_file is None:
            if args.debugger_snr is None:
                args.tty_file, args.debugger_snr = get_free_device(args.board_name)
            else:
                args.tty_file = get_tty(args.debugger_snr)

            if args.tty_file is None:
                log('TTY mode: No free device found')
        elif args.debugger_snr is None:
            args.debugger_snr = get_debugger_snr(args.tty_file)

    def parse_config_and_args(self, bot_config_dict=None):
        if self.bot_config is not None:
            # Do not parse a second time in the simple client layer
            return ''

        self.bot_config = bot_config_dict
        self.iut_config = bot_config_dict.get('iut_config', {})
        bot_config_namespace = self.parse_config(bot_config_dict['auto_pts'])
        self.parse_or_find_tty(bot_config_namespace)
        self.args, errmsg = self.arg_parser.parse(bot_config_namespace)
        self.args.retry_config = bot_config_dict.get('retry_config', None)

        if not errmsg:
            # Remove default root handler that was created at first logging.debug
            logging.getLogger().handlers.clear()
            init_logging('_' + '_'.join(str(x) for x in self.args.cli_port))

        return errmsg

    def apply_config(self, args, config, value):
        pass

    def run_test_cases(self):
        _args = {}
        limit_counter = 0
        all_stats = None

        config_default = self.config_default
        _args[config_default] = self.args

        # These contain values passed with -c and -e options
        included = sort_and_reduce_prefixes(_args[config_default].test_cases)
        excluded = sort_and_reduce_prefixes(_args[config_default].excluded)
        _args[config_default].excluded = []
        _args[config_default].test_cases = []

        # Ask the PTS about test cases available in the workspace
        filtered_test_cases = autoptsclient.get_test_cases(self.ptses[0], included, excluded)

        # Save the iut_config key run order.
        run_order = list(self.iut_config.keys())

        # Make sure that default config is processed last and gets from the remaining test cases
        distribution_order = copy.deepcopy(run_order)
        if config_default in run_order:
            distribution_order.remove(config_default)
            distribution_order.append(config_default)

        # Distribute test cases among .conf files
        remaining_test_cases = copy.deepcopy(filtered_test_cases)
        for config in distribution_order:
            value = self.iut_config[config]

            # Merge .confs without 'test_cases' into the default one
            if 'test_cases' not in value:
                # The 'test_cases' can be skipped only in the default config.
                # It means: Run all remaining after distribution test cases
                # with the default config.
                continue

            _args[config] = copy.deepcopy(_args[config_default])

            for prefix in value['test_cases']:
                for tc in filtered_test_cases:
                    if tc.startswith(prefix):
                        _args[config].test_cases.append(tc)
                        remaining_test_cases.remove(tc)

                filtered_test_cases = copy.deepcopy(remaining_test_cases)

        # Remaining test cases will be run with the default .conf file
        # if default .conf doesn't have already defined test cases
        if len(_args[config_default].test_cases) == 0 and \
                config_default in self.iut_config and \
                len(self.iut_config[config_default].get('test_cases', [])) == 0:
            _args[config_default].test_cases = filtered_test_cases

        for config in run_order:
            if _args.get(config) is None:
                test_case_number = 0
            else:
                test_case_number = len(_args[config].test_cases)

            if test_case_number == 0:
                log(f'No test cases for {config} config, ignored.')
                continue

            if self.args.test_case_limit:
                limit = self.args.test_case_limit - limit_counter
                if limit == 0:
                    log(f'Limit of test cases reached. No more test cases will be run.')
                    break

                if test_case_number > limit:
                    _args[config].test_cases = _args[config].test_cases[:limit]
                    test_case_number = limit

                limit_counter += test_case_number

            self.apply_config(_args[config], config, self.iut_config[config])

            stats = autoptsclient.run_test_cases(self.ptses, self.test_cases, _args[config])

            if all_stats is None:
                all_stats = stats
            else:
                all_stats = all_stats.merge(all_stats, stats)

        # End of bot run - all test cases completed

        if all_stats is None:
            print(f'\nNo test cases were run. Please verify your config.\n')
            return TestCaseRunStats([], [], 0, None)

        all_stats.print_summary()

        print(f'\nFinal Bot Summary:\n')

        try:
            results = all_stats.get_results()
            descriptions = {}
            for test_case_name in list(results.keys()):
                project_name = test_case_name.split('/')[0]
                descriptions[test_case_name] = \
                    self.ptses[0].get_test_case_description(project_name, test_case_name)

            all_stats.update_descriptions(descriptions)
            all_stats.pts_ver = '{}'.format(self.ptses[0].get_version())
            all_stats.platform = '{}'.format(self.ptses[0].get_system_model())
        except:
            log('Failed to generate some stats.')

        return all_stats

    def start(self, args=None):
        # Extend this method in a derived class to handle sending
        # logs, reports, etc.
        self.run_tests()

    def run_tests(self):
        # Entry point of the simple client layer
        return super().start()


def sort_and_reduce_prefixes(prefixes):
    sorted_prefixes = sorted(prefixes, key=len)
    final_prefixes = []

    for s in sorted_prefixes:
        duplicated = False

        for f in final_prefixes:
            if s.startswith(f):
                duplicated = True
                break

        if not duplicated:
            final_prefixes.append(s)

    return final_prefixes


# ****************************************************************************
# Miscellaneous
# ****************************************************************************


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

    logging.debug(f'Running cmd: {cmd}')

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell, executable=executable)


def get_workspace(workspace):
    for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, 'autopts/workspaces'),
                                     topdown=True):
        for name in dirs:
            if name == workspace:
                return os.path.join(root, name)
    return None


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


def get_absolute_module_path(config_path):
    # Path to the config file can be specified as 'config',
    # 'config.py' or 'path/to/conifg.py'.

    _path = os.path.abspath(config_path)
    if os.path.isfile(_path):
        return _path

    _path = os.path.join(PROJECT_DIR, f'autopts/bot/{config_path}')
    if os.path.isfile(_path):
        return _path

    _path = os.path.join(PROJECT_DIR, f'autopts/bot/{config_path}.py')
    if os.path.isfile(_path):
        return _path

    return None


def load_module_from_path(cfg):
    config_path = get_absolute_module_path(cfg)
    if not os.path.isfile(config_path):
        log('{} does not exists!'.format(config_path))
        return None

    config_dirname = os.path.dirname(config_path)
    sys.path.insert(0, config_dirname)
    module_name = Path(config_path).stem
    module = importlib.import_module(module_name)
    sys.path.remove(config_dirname)

    return module


def pre_cleanup():
    """Perform cleanup before test run
    :return: None
    """
    try:
        shutil.copytree("logs", "oldlogs", dirs_exist_ok=True)
        shutil.rmtree("logs")
    except OSError:
        pass


def cleanup():
    """Perform cleanup
    :return: None
    """
    try:
        pass
    except OSError:
        pass
