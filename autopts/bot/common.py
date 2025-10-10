#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
# Copyright (c) 2025, Atmosic.
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
import collections
import copy
import datetime
import importlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import traceback
from argparse import Namespace
from pathlib import Path

from autopts import client as autoptsclient
from autopts.bot.common_features import github, google_drive, mail, report
from autopts.client import Client, CliParser, TestCaseRunStats, init_logging
from autopts.config import AUTOPTS_ROOT_DIR, MAX_SERVER_RESTART_TIME, generate_file_paths, SERIAL_BAUDRATE
from autopts.ptsprojects.boards import get_debugger_snr, get_free_device, get_tty, release_device
from autopts.ptsprojects.testcase_db import DATABASE_FILE

log = logging.debug


def get_deepest_dirs(logs_tree, dst_tree, max_depth):
    def recursive(directory, depth=3):
        depth -= 1

        for file in os.scandir(directory):
            if file.is_dir():
                if depth > 0:
                    recursive(file.path, depth)
                else:
                    dst_file = os.path.join(dst_tree, file.name)
                    try:
                        shutil.move(file.path, dst_file)
                    except BaseException:  # skip waiting for BPV to release the file
                        try:
                            shutil.copy(file.path, dst_file)
                        except BaseException as e2:
                            print(e2)

    recursive(logs_tree, max_depth)


class BuildAndFlashException(Exception):
    pass


class BotCliParser(CliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        self.iut_mode = args.get('iut_mode', None)
        self.workspace = args['workspace']
        self.project_path = args['project_path']
        self.srv_port = args.get('srv_port', [65000])
        self.cli_port = args.get('cli_port', [65001])
        self.ip_addr = args.get('server_ip', ['127.0.0.1'] * len(self.srv_port))
        self.local_addr = args.get('local_ip', ['127.0.0.1'] * len(self.cli_port))
        self.server_count = args.get('server_count', len(self.cli_port))
        self.tty_file = args.get('tty_file', None)
        self.board_name = args.get('board', None)
        self.tty_alias = args.get('tty_alias', None)
        self.net_tty_file = args.get('net_tty_file', None)
        self.tty_baudrate = int(args.get('tty_baudrate', SERIAL_BAUDRATE))
        self.debugger_snr = args.get('debugger_snr', None)
        self.kernel_image = args.get('kernel_image', None)
        self.database_file = args.get('database_file', DATABASE_FILE)
        self.store = args.get('store', False)
        self.rtt_log = args.get('rtt_log', False)
        self.btmon = args.get('btmon', False)
        self.device_core = args.get('device_core', 'NRF52840_XXAA')
        self.qemu_bin = args.get('qemu_bin', None)
        self.qemu_options = args.get('qemu_options', '-cpu cortex-m3 -machine lm3s6965evb')
        self.btattach_bin = args.get('btattach_bin', None)
        self.btattach_at_every_test_case = args.get('btattach_at_every_test_case', False)
        self.btproxy_bin = args.get('btproxy_bin', None)
        self.btmgmt_bin = args.get('btmgmt_bin', None)
        self.hid_vid = args.get('hid_vid', None)
        self.hid_pid = args.get('hid_pid', None)
        self.hid_serial = args.get('hid_serial', None)
        self.kernel_cpu = args.get('kernel_cpu', 'qemu_cortex_m3')
        self.setcap_cmd = args.get('setcap_cmd', None)
        self.hci = args.get('hci', None)
        self.test_cases = args.get('test_cases', [])
        self.excluded = args.get('excluded', [])

        self.bd_addr = args.get('bd_addr', '')
        self.enable_max_logs = args.get('enable_max_logs', False)
        self.retry = args.get('retry', 0)
        self.repeat_until_fail = args.get('repeat_until_fail', False)
        self.stress_test = args.get('stress_test', False)
        self.ykush = args.get('ykush', None)
        self.ykush_replug_delay = args.get('ykush_replug_delay', 3)
        self.active_hub_server = args.get('active_hub_server', None)
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
        self.no_build = args.get('no_build', False)
        self.dongle_init_retry = args.get('dongle_init_retry', 5)
        self.build_env_cmd = args.get('build_env_cmd', None)
        self.copy = args.get('copy', True)
        self.wid_usage = args.get('wid_usage', False)

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
                       'tc_stats': None}
        # Parser for more informative test failure information
        self.fail_info_parser = None
        self.error_txt_content = ""

    def parse_or_find_tty(self, args):
        if args.tty_alias:
            args.tty_file = args.tty_alias
        elif args.tty_file is None:
            if args.debugger_snr is None:
                args.tty_file, args.debugger_snr = get_free_device(args.board_name)
            else:
                args.tty_file = get_tty(args.debugger_snr, args.board_name)

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

        self.load_test_case_database()

        continue_test_case = None
        continue_config = None
        if os.path.exists(self.file_paths['ALL_STATS_JSON_FILE']):
            self.backup['all_stats'] = TestCaseRunStats.load_from_backup(self.file_paths['ALL_STATS_JSON_FILE'])
            self.backup['all_stats'].db = self.test_case_database
            continue_config = self.backup['all_stats'].pending_config

            # The last config and test case preformed in the broken test run
            if os.path.exists(self.file_paths['TC_STATS_JSON_FILE']):
                self.backup['tc_stats'] = TestCaseRunStats.load_from_backup(self.file_paths['TC_STATS_JSON_FILE'])
                self.backup['tc_stats'].db = self.test_case_database
                continue_config = self.backup['tc_stats'].pending_config
                continue_test_case = self.backup['tc_stats'].pending_test_case

        if not continue_config:
            return

        with open(self.file_paths['TEST_CASES_JSON_FILE']) as f:
            data = f.read()
            test_cases_per_config = json.loads(data)
            run_order = list(test_cases_per_config.keys())

        # Skip already completed configs
        config_index = run_order.index(continue_config)
        if continue_test_case:
            # Skip already completed test cases and the faulty one
            tc_index = test_cases_per_config[continue_config].index(continue_test_case)
            test_cases_per_config[continue_config] = test_cases_per_config[continue_config][tc_index + 1:]
            self.backup['tc_stats'].index += 1
            self.backup['tc_stats'].update(continue_test_case, 0, 'TIMEOUT')

            if not test_cases_per_config[continue_config]:
                # The faulty test case was the last one in the config. Move to the next config
                self._merge_stats(self.backup['all_stats'], self.backup['tc_stats'])
                self.backup['all_stats'].save_to_backup(self.file_paths['ALL_STATS_JSON_FILE'])
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

        if 'file_paths' in self.bot_config:
            generate_file_paths(self.bot_config['file_paths'])

        # Remove default root handler that was created at the first logging.debug
        logging.getLogger().handlers.clear()
        self.args, errmsg = self.arg_parser.parse(bot_config_namespace)
        self.args.retry_config = bot_config_dict.get('retry_config', None)

        if errmsg:
            return errmsg

        if self.args.use_backup and os.path.exists(self.file_paths['BOT_STATE_JSON_FILE']):
            self.load_backup_of_previous_run()
        else:
            self.bot_pre_cleanup()

        return errmsg

    def apply_config(self, args, config, value):
        pass

    def bot_pre_cleanup(self):
        """Perform cleanup before test run
        :return: None
        """
        files_to_save = [
            self.file_paths['TMP_DIR'],
            self.file_paths['IUT_LOGS_DIR'],
        ]

        save_dir = os.path.join(self.file_paths['OLD_LOGS_DIR'],
                                datetime.datetime.now().strftime("%Y_%m_%d_%H_%M"))
        save_files(files_to_save, save_dir)

    def bot_post_cleanup(self):
        files_to_save = [
            self.file_paths['ALL_STATS_RESULTS_XML_FILE'],
            self.file_paths['TC_STATS_RESULTS_XML_FILE'],
            self.file_paths['TEST_CASES_JSON_FILE'],
            self.file_paths['ALL_STATS_JSON_FILE'],
            self.file_paths['TC_STATS_JSON_FILE'],
            self.file_paths['BOT_STATE_JSON_FILE'],
        ]

        save_dir = self.file_paths['BOT_STATE_DIR']
        save_files(files_to_save, save_dir)

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
                        log('Limit of test cases reached. No more test cases will be run.')
                        break

                    if test_case_number > limit:
                        _args[config].test_cases = _args[config].test_cases[:limit]
                        test_case_number = limit

                    limit_counter += test_case_number

                test_cases[config] = _args[config].test_cases
                run_order.append(config)

            if self.args.use_backup:
                with open(self.file_paths['TEST_CASES_JSON_FILE'], 'w') as file:
                    file.write(json.dumps(test_cases, indent=4))

        for config in run_order:
            yield config, _args[config]

    def _backup_tc_stats(self, config=None, test_case=None, stats=None, **kwargs):
        if not self.backup or not stats:
            return

        stats.pending_config = config
        stats.pending_test_case = test_case
        stats.save_to_backup(self.file_paths['TC_STATS_JSON_FILE'])

    def _merge_stats(self, all_stats, stats):
        all_stats.merge(stats)

        if os.path.exists(stats.xml_results):
            os.remove(stats.xml_results)

        if os.path.exists(self.file_paths['TC_STATS_JSON_FILE']):
            os.remove(self.file_paths['TC_STATS_JSON_FILE'])

    def run_test_cases(self):
        all_stats = self.backup['all_stats']
        stats = self.backup['tc_stats']

        if not all_stats:
            all_stats = TestCaseRunStats([], [], 0, xml_results_file=self.file_paths['ALL_STATS_RESULTS_XML_FILE'])
            self.backup['all_stats'] = all_stats

            if self.args.use_backup:
                all_stats.save_to_backup(self.file_paths['ALL_STATS_JSON_FILE'])

        projects = self.ptses[0].get_project_list()

        for config, config_args in self._yield_next_config():
            try:
                if not stats:
                    stats = TestCaseRunStats(projects,
                                             config_args.test_cases,
                                             config_args.retry,
                                             self.test_case_database,
                                             xml_results_file=self.file_paths['TC_STATS_RESULTS_XML_FILE'])
                    stats.session_log_dir = all_stats.session_log_dir

                    if self.args.use_backup:
                        self._backup_tc_stats(config=config, test_case=None, stats=stats)

                self.apply_config(config_args, config, self.iut_config[config])

                stats = autoptsclient.run_test_cases(self.ptses,
                                                     self.test_cases,
                                                     config_args,
                                                     stats,
                                                     config=config,
                                                     pre_test_case_fn=self._backup_tc_stats,
                                                     file_paths=copy.deepcopy(self.file_paths))

            except BuildAndFlashException:
                log(f'Build and flash step failed for config {config}')
                for tc in config_args.test_cases:
                    status = 'BUILD_OR_FLASH ERROR'
                    stats.update(tc, time.time(), status)

            if stats:
                self._merge_stats(all_stats, stats)
                stats = None

            if self.args.use_backup:
                all_stats.save_to_backup(self.file_paths['ALL_STATS_JSON_FILE'])

        # End of bot run - all test cases completed
        if all_stats.num_test_cases == 0:
            print('\nNo test cases were run. Please verify your config.\n')
            return all_stats

        print('\nFinal Bot Summary:\n')
        all_stats.print_summary()

        if self.args.use_backup:
            all_stats.test_run_completed = True
            all_stats.save_to_backup(self.file_paths['ALL_STATS_JSON_FILE'])

        try:
            mapping = {'GMCS': 'MCS',
                       'GTBS': 'TBS'}
            results = all_stats.get_results()
            descriptions = {}
            for test_case_name in list(results.keys()):
                try:
                    project_name = test_case_name.split('/')[0]
                    project_name = mapping.get(project_name, project_name)
                    descriptions[test_case_name] = \
                        self.ptses[0].get_test_case_description(project_name, test_case_name)
                except:
                    log(f'Failed to get description of {test_case_name}')

            all_stats.update_descriptions(descriptions)
            all_stats.pts_ver = str(self.ptses[0].get_version())
            all_stats.platform = str(self.ptses[0].get_system_model())
            all_stats.system_version = str(self.ptses[0].get_system_version())
            if self.args.use_backup:
                all_stats.save_to_backup(self.file_paths['ALL_STATS_JSON_FILE'])
        except BaseException as e:
            log(f'Failed to generate some stats, {e}.')

        return all_stats

    def start(self, args=None):
        """
        Extend this method in a derived class, if needed, to handle
        sending logs, reports, etc.
        """

        if os.path.exists(self.file_paths['BOT_STATE_JSON_FILE']):
            print(f'Continuing the previous terminated test run '
                  f'(remove {self.file_paths["TMP_DIR"]} to start freshly)')

            with open(self.file_paths['BOT_STATE_JSON_FILE']) as f:
                data = f.read()
                bot_state = json.loads(data)
                self.bot_config = bot_state['bot_config']

        else:
            # Start fresh test run

            bot_state = {'start_time': time.time()}

            if 'githubdrive' in self.bot_config:
                github.update_sources(self.bot_config['githubdrive']['path'],
                                      self.bot_config['githubdrive']['remote'],
                                      self.bot_config['githubdrive']['branch'], True)

            if 'git' in self.bot_config:
                bot_state['repos_info'] = github.update_repos(
                    self.bot_config['auto_pts']['project_path'],
                    self.bot_config["git"])
                bot_state['repo_status'] = report.make_repo_status(bot_state['repos_info'])
            else:
                bot_state['repos_info'] = {}
                bot_state['repo_status'] = ''

            if self.bot_config['auto_pts'].get('use_backup', False):
                os.makedirs(self.file_paths["TMP_DIR"], exist_ok=True)
                bot_state['bot_config'] = self.bot_config

                with open(self.file_paths['BOT_STATE_JSON_FILE'], "w") as f:
                    f.write(json.dumps(bot_state, indent=4))

        try:
            stats = self.run_tests()
        except:
            self.error_txt_content += traceback.format_exc() + "\n"
            raise
        finally:
            release_device(self.args.tty_file)
            report.make_error_txt(self.error_txt_content, self.file_paths['ERROR_TXT_FILE'])

        if (self.fail_info_parser):
            stats.additional_fail_info_cb = self.fail_info_parser

        report_data = bot_state
        report_data['end_time'] = time.time()
        report_data['end_time_stamp'] = datetime.datetime.fromtimestamp(
            report_data['end_time']).strftime("%Y_%m_%d_%H_%M_%S")
        report_data['start_time_stamp'] = datetime.datetime.fromtimestamp(
            bot_state['start_time']).strftime("%Y_%m_%d_%H_%M_%S")

        report_data['project_name'] = self.autopts_project_name
        report_data['status_count'] = stats.get_status_count()
        report_data['tc_results'] = stats.get_results()
        report_data['descriptions'] = stats.get_descriptions()
        report_data['regressions'] = stats.get_regressions()
        report_data['progresses'] = stats.get_progresses()
        report_data['new_cases'] = stats.get_new_cases()
        report_data['deleted_cases'] = []
        report_data['pts_ver'] = stats.pts_ver
        report_data['platform'] = stats.platform
        report_data['system_version'] = stats.system_version
        report_data['database_file'] = self.bot_config['auto_pts'].get('database_file', DATABASE_FILE)

        if self.args.wid_usage:
            stats.get_wid_usage()

        report_data['tc_results'] = collections.OrderedDict(sorted(report_data['tc_results'].items()))

        report_data['errata'] = report.get_errata([
            os.path.join(AUTOPTS_ROOT_DIR, 'errata/common.yaml'),
            os.path.join(AUTOPTS_ROOT_DIR, f'errata/{self.autopts_project_name}.yaml')
        ])

        report_data['pts_logs_folder'], report_data['pts_xml_folder'] = \
            report.pull_server_logs(self.args,
                                    self.file_paths['TMP_DIR'],
                                    self.file_paths['PTS_XMLS_DIR'])

        report.make_report_xlsx(self.file_paths['REPORT_XLSX_FILE'],
                                report_data['tc_results'],
                                report_data['status_count'],
                                report_data['regressions'],
                                report_data['progresses'],
                                report_data['descriptions'],
                                report_data['pts_xml_folder'],
                                report_data['errata'])

        report.make_report_txt(self.file_paths['REPORT_TXT_FILE'],
                               report_data['tc_results'],
                               report_data['regressions'],
                               report_data['progresses'],
                               report_data['repo_status'],
                               report_data['errata'])

        if 'githubdrive' in self.bot_config or 'gdrive' in self.bot_config:
            self.make_report_folder(report_data)

            if 'gdrive' in self.bot_config:
                self.upload_logs_to_gdrive(report_data)

            if 'githubdrive' in self.bot_config:
                self.upload_logs_to_github(report_data)

        if 'mail' in self.bot_config:
            self.send_email(report_data)

        self.bot_post_cleanup()

        if self.error_txt_content:
            report.make_error_txt(self.error_txt_content, self.file_paths['ERROR_TXT_FILE'])

        print("Done")

    def run_tests(self):
        # Entry point of the simple client layer
        return super().start()

    def make_readme_md(self, readme_md_path, report_data):
        """Creates README.md for Github logging repo
        """
        readme_file = readme_md_path
        profile_summary = report.ascii_profile_summary(report_data['tc_results'])

        Path(os.path.dirname(readme_file)).mkdir(parents=True, exist_ok=True)

        with open(readme_file, 'w') as f:
            readme_body = f'''# AutoPTS report

    Start time: {report_data["start_time_stamp"]}

    End time: {report_data["end_time_stamp"]}

    PTS version: {report_data["pts_ver"]}

    Test Group/Profile Summary: {profile_summary}

    Repositories:

'''
            f.write(readme_body)

            for name, info in report_data['repos_info'].items():
                f.write(f'\t{name}: {info["commit"]} [{info["desc"]}]\n')

        return readme_file

    def make_report_folder(self, report_data):
        """Creates folder containing .txt and .xlsx reports, pulled logs
        from autoptsserver, iut logs and additional README.md.
        """
        shutil.rmtree(self.file_paths['REPORT_DIR'], ignore_errors=True)
        Path(self.file_paths['REPORT_DIR']).mkdir(parents=True, exist_ok=True)

        if 'githubdrive' in self.bot_config:
            report_data['deleted_cases'] = \
                report.make_report_diff(self.bot_config['githubdrive'].get('old_report_txt', ''),
                                        self.file_paths['REPORT_DIFF_TXT_FILE'],
                                        report_data['tc_results'],
                                        report_data['regressions'],
                                        report_data['progresses'],
                                        report_data['new_cases'])

        report_data['readme_file'] = self.make_readme_md(self.file_paths['REPORT_README_MD_FILE'], report_data)

        attachments = [
            self.file_paths['REPORT_DIFF_TXT_FILE'],
            self.file_paths['REPORT_TXT_FILE'],
            (self.file_paths['REPORT_TXT_FILE'], f'report_{report_data["start_time_stamp"]}.txt'),
            (self.file_paths['REPORT_XLSX_FILE'], f'report_{report_data["start_time_stamp"]}.xlsx'),
            self.file_paths['REPORT_README_MD_FILE'],
            report_data['database_file'],
            report_data['pts_xml_folder'],
        ]

        iut_logs_new = os.path.join(self.file_paths['REPORT_DIR'], 'iut_logs')
        pts_logs_new = os.path.join(self.file_paths['REPORT_DIR'], 'pts_logs')
        get_deepest_dirs(self.file_paths['IUT_LOGS_DIR'], iut_logs_new, 3)
        get_deepest_dirs(report_data['pts_logs_folder'], pts_logs_new, 3)

        self.generate_attachments(report_data, attachments)

        self.pack_report_folder(report_data, attachments)

    def generate_attachments(self, report_data, attachments):
        """Overwrite this if needed"""
        pass

    def pack_report_folder(self, report_data, attachments):
        report_dir = self.file_paths['REPORT_DIR']

        for item in attachments:
            if isinstance(item, tuple):
                src_file, dst_file = item
                dst_file = os.path.join(report_dir, dst_file)
            else:
                src_file = item
                dst_file = os.path.join(report_dir, os.path.basename(src_file))

            try:
                if not os.path.exists(src_file):
                    log(f'The file {src_file} does not exist')
                    continue

                if os.path.isdir(src_file):
                    try:
                        shutil.move(src_file, dst_file)
                        continue
                    except Exception as e:
                        log(f"Failed to move directory {src_file} → {dst_file}: {e}")

                try:
                    shutil.copy(src_file, dst_file)
                except Exception as e:
                    log(f"Failed to copy file {src_file} → {dst_file}: {e}")

            except Exception as e:
                traceback.print_exception(e)

    def upload_logs_to_github(self, report_data):
        log("Uploading to Github ...")

        if 'commit_msg' not in report_data:
            report_data['commit_msg'] = report_data['start_time_stamp']

        report_data['github_link'], self.file_paths['REPORT_DIR'] = \
            report.github_push_report(self.file_paths['REPORT_DIR'],
                                      self.bot_config['githubdrive'],
                                      report_data['commit_msg'])

    def upload_logs_to_gdrive(self, report_data):
        board_name = self.bot_config['auto_pts']['board']
        gdrive_config = self.bot_config['gdrive']

        log('Archiving the report folder ...')
        report.archive_testcases(self.file_paths['REPORT_DIR'], depth=2)

        log('Connecting to GDrive ...')
        drive = google_drive.Drive(gdrive_config)

        log('Creating GDrive directory ...')
        report_data['gdrive_url'] = drive.new_workdir(board_name)
        log(report_data['gdrive_url'])

        log("Uploading to GDrive ...")
        drive.upload_folder(self.file_paths['REPORT_DIR'])

    def send_email(self, report_data):
        log("Sending email ...")

        descriptions = report_data['descriptions']

        mail_ctx = {'project_name': report_data['project_name'],
                    'repos_info': report_data['repo_status'],
                    'summary': [mail.status_dict2summary_html(report_data['status_count'])],
                    'profile_summary': mail.html_profile_summary(report_data['tc_results']),
                    'log_url': [],
                    'board': self.bot_config['auto_pts']['board'],
                    'platform': report_data['platform'],
                    'pts_ver': report_data['pts_ver'],
                    'system_version': report_data['system_version'],
                    'additional_info': '',
                    }

        mail_ctx.update(self.bot_config['mail'])

        if report_data['regressions']:
            mail_ctx['summary'].append(mail.regressions2html(report_data['regressions'], descriptions))

        if report_data['progresses']:
            mail_ctx['summary'].append(mail.progresses2html(report_data['progresses'], descriptions))

        if report_data['new_cases']:
            mail_ctx['summary'].append(mail.new_cases2html(report_data['new_cases'], descriptions))

        if report_data['deleted_cases']:
            mail_ctx['summary'].append(mail.deleted_cases2html(report_data['deleted_cases'], descriptions))

        mail_ctx['summary'] = '<br>'.join(mail_ctx['summary'])

        if 'gdrive' in self.bot_config and 'gdrive_url' in report_data:
            mail_ctx['log_url'].append(mail.url2html(report_data['gdrive_url'], "Results on Google Drive"))

        if 'githubdrive' in self.bot_config and 'github_link' in report_data:
            mail_ctx['log_url'].append(mail.url2html(report_data['github_link'], 'Results on Github'))

        mail_ctx['log_url'] = '<br>'.join(mail_ctx['log_url'])

        if not mail_ctx['log_url']:
            mail_ctx['log_url'] = 'Not Available'

        mail_ctx["elapsed_time"] = str(datetime.timedelta(
            seconds=(int(report_data['end_time'] - report_data['start_time']))))

        if 'additional_info_path' in mail_ctx:
            try:
                with open(mail_ctx['additional_info_path']) as file:
                    mail_ctx['additional_info'] = f'{file.read()} <br>'
            except Exception as e:
                logging.exception(e)

        subject, body = self.compose_mail(mail_ctx)

        mail.send_mail(self.bot_config['mail'], subject, body,
                       [self.file_paths['REPORT_XLSX_FILE'],
                        self.file_paths['REPORT_TXT_FILE']])

    def compose_mail(self, mail_ctx):
        """ Create a email body
        """
        iso_cal = datetime.date.today().isocalendar()
        ww_dd_str = f"WW{iso_cal[1]}.{iso_cal[2]}"

        body = '''
    <p>This is automated email and do not reply.</p>
    <h1>Bluetooth test session - {ww_dd_str} </h1>
    {additional_info}
    <h2>1. IUT Setup</h2>
    <p><b> Type:</b> {project_name} <br>
    <b> Board:</b> {board} <br>
    <b> Source:</b> {repos_info} </p>
    <h2>2. PTS Setup</h2>
    <p><b> OS:</b> {system_version} <br>
    <b> Platform:</b> {platform} <br>
    <b> Version:</b> {pts_ver} </p>
    <h2>3. Test Results</h2>
    <p><b>Execution Time</b>: {elapsed_time}</p>
    {summary}
    {profile_summary}
    <h3>Logs</h3>
    {log_url}
    <p>Sincerely,</p>
    <p>{name}</p>
'''

        if 'body' in mail_ctx:
            body = mail_ctx['body']

        body = body.format(ww_dd_str=ww_dd_str, **mail_ctx)

        subject = mail_ctx.get('subject', 'AutoPTS test session results')
        subject = f"{subject} - {ww_dd_str}"

        return subject, body


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


class TestGroup:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.pass_rate = 0.0

    def get_pass_rate(self):
        if self.total > 0:
            self.pass_rate = (self.passed / float(self.total)) * 100


def get_tc_res_data(tc_results, test_groups):
    """Gets test results from repord_data['tc_results']and returns
     dictionary containing profile name as key, TestGroup object as value
     e.g. test_groups = {'ASCS' = TestGroup()}"""
    for tc, res in list(tc_results.items()):
        result = res["parsed_result"]
        profile = tc.split('/')[0]
        if profile not in test_groups.keys():
            test_groups[profile] = TestGroup()
        if result == 'PASS':
            test_groups[profile].passed += 1
        else:
            test_groups[profile].failed += 1
        test_groups[profile].total += 1

    return test_groups


# ****************************************************************************
# Miscellaneous
# ****************************************************************************


def _prepare_command(cmd, cwd, shell):
    """
    Normalize command across platforms.

    :param cmd: command to run
    :param cwd: working directory
    :param shell: if true, the command will be executed through the shell
    :return: tuple (cmd, cwd, shell, executable)
    """
    executable = None

    if isinstance(cmd, (list, tuple)):
        cmd = subprocess.list2cmdline(cmd)

    if sys.platform == 'win32':
        if isinstance(cwd, str) and cwd.startswith('wsl:'):
            cmd = ["wsl.exe", "--cd", cwd.removeprefix('wsl:'), "--", "/bin/bash", "-i", "-c", cmd]
            cwd = None
        else:
            cmd = [os.path.expandvars('$MSYS2_BASH_PATH'), '-c', cmd]

        shell = False
    else:
        executable = '/bin/bash' if shell else None

    return cmd, cwd, shell, executable


def check_call(cmd, env=None, cwd=None, shell=True, stdout=True, stderr=True):
    """Run command with arguments. Wait for the command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets the current directory before execution
    :param shell: if true, the command will be executed through the shell
    :param stdout: if False, redirected to /dev/null
    :param stderr: if False, redirected to /dev/null
    :return: returncode
    """
    cmd, cwd, shell, executable = _prepare_command(cmd, cwd, shell)

    if stdout:
        stdout = None
    else:
        stdout = subprocess.DEVNULL

    if stderr:
        stderr = None
    else:
        stderr = subprocess.DEVNULL

    logging.debug(f'Running cmd: {cmd}')
    sys.stdout.flush()

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell, executable=executable,
                                 stdout=stdout, stderr=stderr)


def check_output(cmd, env=None, cwd=None, shell=True):
    """Run command with arguments. Capture standard output. Wait for the command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets the current directory before execution
    :param shell: if true, the command will be executed through the shell
    :return: stdout as bytes
    """
    cmd, cwd, shell, executable = _prepare_command(cmd, cwd, shell)

    logging.debug(f'Running cmd: {cmd}')
    sys.stdout.flush()

    return subprocess.check_output(cmd, cwd=cwd, shell=shell, env=env, executable=executable)


def get_workspace(workspace):
    for root, dirs, _ in os.walk(os.path.join(AUTOPTS_ROOT_DIR, 'autopts/workspaces'),
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
            return f"/dev/{tty}"

    return None


def get_absolute_module_path(config_path):
    # Path to the config file can be specified as 'config',
    # 'config.py' or 'path/to/conifg.py'.

    _path = os.path.abspath(config_path)
    if os.path.isfile(_path):
        return _path

    _path = os.path.join(AUTOPTS_ROOT_DIR, f'autopts/bot/{config_path}')
    if os.path.isfile(_path):
        return _path

    _path = os.path.join(AUTOPTS_ROOT_DIR, f'autopts/bot/{config_path}.py')
    if os.path.isfile(_path):
        return _path

    return None


def load_module_from_path(cfg):
    config_path = get_absolute_module_path(cfg)
    if not os.path.isfile(config_path):
        log(f'{config_path} does not exist!')
        return None

    config_dirname = os.path.dirname(config_path)
    sys.path.insert(0, config_dirname)
    module_name = Path(config_path).stem
    module = importlib.import_module(module_name)
    sys.path.remove(config_dirname)

    return module


def save_files(files_to_save, save_dir: str):
    try:
        for file_path in files_to_save:
            if os.path.exists(file_path):
                Path(save_dir).mkdir(parents=True, exist_ok=True)
                break

        for file_path in files_to_save:
            if os.path.exists(file_path):
                dst_file_path = os.path.join(save_dir, os.path.basename(file_path))
                shutil.move(file_path, dst_file_path)
    except OSError:
        pass
