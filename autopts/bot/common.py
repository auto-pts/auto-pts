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
import time
import json
from pathlib import Path
from argparse import Namespace
from autopts import client as autoptsclient
from autopts.client import CliParser, Client, TestCaseRunStats, init_logging
from autopts.config import MAX_SERVER_RESTART_TIME, TEST_CASES_JSON, ALL_STATS_JSON, TC_STATS_JSON, \
    ALL_STATS_RESULTS_XML, TC_STATS_RESULTS_XML, BOT_STATE_JSON
from autopts.ptsprojects.boards import get_free_device, get_tty, get_debugger_snr
from autopts.ptsprojects.testcase_db import DATABASE_FILE

PROJECT_DIR = os.path.dirname(  # auto-pts repo directory
                os.path.dirname(  # autopts module directory
                    os.path.dirname(  # bot module directory
                        os.path.abspath(__file__))))  # this file directory

log = logging.debug


def cleanup_tmp_files():
    files = [ALL_STATS_RESULTS_XML,
             TC_STATS_RESULTS_XML,
             TEST_CASES_JSON,
             ALL_STATS_JSON,
             TC_STATS_JSON,
             BOT_STATE_JSON,
             ]

    for file in files:
        if os.path.exists(file):
            os.remove(file)


class BuildAndFlashException(Exception):
    pass


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
        self.tty_alias = args.get('tty_alias', None)
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
        self.repeat_until_fail = args.get('repeat_until_fail', False)
        self.stress_test = args.get('stress_test', False)
        self.ykush = args.get('ykush', None)
        self.ykush_replug_delay = args.get('ykush_replug_delay', 3)
        self.recovery = args.get('recovery', False)
        self.superguard = float(args.get('superguard', 0))
        self.cron_optim = args.get('cron_optim', False)
        self.project_repos = args.get('repos', None)
        self.test_case_limit = args.get('test_case_limit', 0)
        self.simple_mode = args.get('simple_mode', False)
        self.server_args = args.get('server_args', None)
        self.pylink_reset = args.get('pylink_reset', False)
        self.max_server_restart_time = args.get('max_server_restart_time', MAX_SERVER_RESTART_TIME)
        self.use_backup = args.get('use_backup', False)

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
        # Backup files with test cases and stats from a previous test run that
        # has been stopped unexpectedly.
        self.backup = {'available': False,
                       'create': False,
                       'all_stats': None,
                       'tc_stats': None,
                       'test_cases_file': TEST_CASES_JSON,
                       'all_stats_file': ALL_STATS_JSON,
                       'tc_stats_file': TC_STATS_JSON}

    def parse_or_find_tty(self, args):
        if args.tty_alias:
            args.tty_file = args.tty_alias
        elif args.tty_file is None:
            if args.debugger_snr is None:
                args.tty_file, args.debugger_snr = get_free_device(args.board_name)
            else:
                args.tty_file = get_tty(args.debugger_snr)

            if args.tty_file is None:
                log('TTY mode: No free device found')
        elif args.debugger_snr is None:
            args.debugger_snr = get_debugger_snr(args.tty_file)

    def load_backup_of_previous_run(self):
        """
        If the backup mode was enabled in the previous test run, and it
        has been terminated unexpectedly, it is possible to resume the test series
        from the last remembered config/test_case.
        """

        continue_test_case = None
        continue_config = None
        if os.path.exists(self.backup['all_stats_file']):
            self.backup['all_stats'] = TestCaseRunStats.load_from_backup(self.backup['all_stats_file'])
            continue_config = self.backup['all_stats'].pending_config

            # The last config and test case preformed in the broken test run
            if os.path.exists(self.backup['tc_stats_file']):
                self.backup['tc_stats'] = TestCaseRunStats.load_from_backup(self.backup['tc_stats_file'])
                continue_config = self.backup['tc_stats'].pending_config
                continue_test_case = self.backup['tc_stats'].pending_test_case

        if not continue_config:
            return

        with open(self.backup['test_cases_file']) as f:
            data = f.read()
            test_cases_per_config = json.loads(data)
            run_order = list(test_cases_per_config.keys())

        # Skip already completed configs
        config_index = run_order.index(continue_config)
        if continue_test_case:
            # Skip already completed test cases and the faulty one
            tc_index = test_cases_per_config[continue_config].index(continue_test_case)
            test_cases_per_config[continue_config] = test_cases_per_config[continue_config][tc_index + 1:]
            
            if not test_cases_per_config[continue_config]:
                # The faulty test case was the last one in the config. Move to the next config
                self.backup['tc_stats'].update(continue_test_case, 0, 'TIMEOUT')
                self._merge_stats(self.backup['all_stats'], self.backup['tc_stats'])
                self.backup['all_stats'].save_to_backup(self.backup['all_stats_file'])
                self.backup['tc_stats'] = None
                config_index += 1
                continue_test_case = None

        _args = {}
        self.backup['args_per_config'] = _args
        self.backup['available'] = True
        self.backup['run_order'] = run_order[config_index:]

        if not self.backup['run_order']:
            # All test cases done, the last one was faulty
            self.backup['all_stats'].test_run_completed = True
            return

        continue_config = self.backup['run_order'][0]

        for config in self.backup['run_order']:
            _args[config] = copy.deepcopy(self.args)
            _args[config].test_cases = test_cases_per_config[config]

        # Skip build and flash for the pending config as it has been
        # already done in previous test run.
        _args[continue_config].no_build = True

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

        if errmsg:
            return errmsg

        if self.args.use_backup:
            self.load_backup_of_previous_run()
        else:
            cleanup_tmp_files()

        # Remove default root handler that was created at the first logging.debug
        logging.getLogger().handlers.clear()
        init_logging('_' + '_'.join(str(x) for x in self.args.cli_port))

        return errmsg

    def apply_config(self, args, config, value):
        pass

    def _yield_next_config(self):
        limit_counter = 0

        if self.backup['available']:
            if self.backup['all_stats'].test_run_completed:
                # All test cases have been completed before termination
                return

            _args = self.backup['args_per_config']
            run_order = self.backup['run_order']
        else:
            _run_order, _args = get_filtered_test_cases(self.iut_config, self.args,
                                                        self.config_default, self.ptses[0])

            run_order = []
            test_cases = {}
            for config in _run_order:
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

                test_cases[config] = _args[config].test_cases
                run_order.append(config)

            if self.args.use_backup:
                with open(self.backup['test_cases_file'], 'w') as file:
                    file.write(json.dumps(test_cases, indent=4))

        for config in run_order:
            yield config, _args[config]

    def _backup_tc_stats(self, config=None, test_case=None, stats=None, **kwargs):
        if not self.backup or not stats:
            return

        stats.pending_config = config
        stats.pending_test_case = test_case
        stats.save_to_backup(self.backup['tc_stats_file'])

    def _merge_stats(self, all_stats, stats):
        all_stats.merge(stats)

        if os.path.exists(stats.xml_results):
            os.remove(stats.xml_results)

        if os.path.exists(TC_STATS_JSON):
            os.remove(TC_STATS_JSON)

    def run_test_cases(self):
        all_stats = self.backup['all_stats']
        stats = self.backup['tc_stats']

        if not all_stats:
            all_stats = TestCaseRunStats([], [], 0, xml_results_file=ALL_STATS_RESULTS_XML)
            self.backup['all_stats'] = all_stats

            if self.args.use_backup:
                all_stats.save_to_backup(self.backup['all_stats_file'])

        projects = self.ptses[0].get_project_list()

        for config, config_args in self._yield_next_config():
            try:
                if not stats:
                    stats = TestCaseRunStats(projects,
                                             config_args.test_cases,
                                             config_args.retry,
                                             self.test_case_database,
                                             xml_results_file=TC_STATS_RESULTS_XML)

                    if self.args.use_backup:
                        self._backup_tc_stats(config=config, test_case=None, stats=stats)

                self.apply_config(config_args, config, self.iut_config[config])

                stats = autoptsclient.run_test_cases(self.ptses,
                                                     self.test_cases,
                                                     config_args,
                                                     stats,
                                                     config=config,
                                                     pre_test_case_fn=self._backup_tc_stats)

            except BuildAndFlashException:
                log(f'Build and flash step failed for config {config}')

                for tc in config_args.test_cases:
                    status = 'BUILD_OR_FLASH ERROR'
                    stats.update(tc, time.time(), status)

            if stats:
                self._merge_stats(all_stats, stats)
                stats = None

            if self.args.use_backup:
                all_stats.save_to_backup(self.backup['all_stats_file'])

        # End of bot run - all test cases completed

        if all_stats.num_test_cases == 0:
            print(f'\nNo test cases were run. Please verify your config.\n')
            return all_stats

        print(f'\nFinal Bot Summary:\n')
        all_stats.print_summary()

        if self.args.use_backup:
            all_stats.test_run_completed = True
            all_stats.save_to_backup(self.backup['all_stats_file'])

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


def get_filtered_test_cases(iut_config, bot_args, config_default, pts):
    _args = {}
    config_default = config_default
    _args[config_default] = bot_args

    # These contain values passed with -c and -e options
    included = sort_and_reduce_prefixes(_args[config_default].test_cases)
    excluded = sort_and_reduce_prefixes(_args[config_default].excluded)
    _args[config_default].excluded = []
    _args[config_default].test_cases = []

    # Ask the PTS about test cases available in the workspace
    filtered_test_cases = autoptsclient.get_test_cases(pts, included, excluded)

    # Save the iut_config key run order.
    run_order = list(iut_config.keys())

    # Make sure that default config is processed last and gets from the remaining test cases
    distribution_order = copy.deepcopy(run_order)
    if config_default in run_order:
        distribution_order.remove(config_default)
        distribution_order.append(config_default)

    # Distribute test cases among .conf files
    remaining_test_cases = copy.deepcopy(filtered_test_cases)
    for config in distribution_order:
        value = iut_config[config]

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
            config_default in iut_config and \
            len(iut_config[config_default].get('test_cases', [])) == 0:
        _args[config_default].test_cases = filtered_test_cases

    return run_order, _args


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
    sys.stdout.flush()

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
        cleanup_tmp_files()
    except OSError:
        pass
