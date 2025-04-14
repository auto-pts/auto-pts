import os
import shutil
import sys
import unittest
from os.path import abspath, dirname
from pathlib import Path
from unittest.mock import patch

from autopts.bot.common_features import report
from autopts.client import FakeProxy, TestCaseRunStats
from autopts.config import FILE_PATHS
from autopts.ptsprojects.testcase_db import TestCaseTable
from autoptsclient_bot import import_bot_module, import_bot_projects
from test.mocks.mocked_test_cases import mock_workspace_test_cases, test_case_list_generation_samples

DATABASE_FILE = 'test/mocks/zephyr_database.db'


def delete_file(file_path):
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path, ignore_errors=True)
    except Exception:
        pass


class MyTestCase(unittest.TestCase):
    def setUp(self):
        os.chdir(dirname(dirname(abspath(__file__))))
        open('ttyUSB', 'w').close()
        shutil.copy('test/configs/config_zephyr.py', 'autopts/bot/config.py')

    def tearDown(self):
        os.remove('ttyUSB')
        delete_file('autopts/bot/config.py')
        for name in FILE_PATHS:
            delete_file(FILE_PATHS[name])

    def test_bot_startup_import_bot_projects(self):
        """Check that all supported methods of passing a config file
        to the bot client work.
        """

        testargs = [('autoptsclient_bot.py', True),
                    ('autoptsclient_bot.py config', True),
                    ('autoptsclient_bot.py config.py', True),
                    ('autoptsclient_bot.py -a -b -c', True),
                    ('autoptsclient_bot.py test/configs/config_external_bot.py', True),
                    ('autoptsclient_bot.py test/configs/config_zephyr.py -a -b -c', True),
                    ('autoptsclient_bot.py fake_config', False),
                    ('autoptsclient_bot.py fake_config.py', False),
                    ('autoptsclient_bot.py test/configs/fake_config.py', False),
                    ]

        for args, expected in testargs:
            with patch.object(sys, 'argv', args.split(' ')):
                projects, _ = import_bot_projects()
                assert (projects is not None) == expected

    def test_bot_startup_import_bot_module(self):
        """Check that importing bot modules work"""

        testargs = ['autoptsclient_bot.py test/configs/config_zephyr.py',
                    'autoptsclient_bot.py test/configs/config_mynewt.py',
                    'autoptsclient_bot.py test/configs/config_external_bot.py',
                    ]

        for args in testargs:
            with patch.object(sys, 'argv', args.split(' ')):
                projects, _ = import_bot_projects()
                project = projects[0]
                bot_module = import_bot_module(project)
                assert bot_module is not None

    def test_bot_startup_parse_config(self):
        """Check parsing in BotClient derived classes."""

        testargs = ['autoptsclient_bot.py test/configs/config_zephyr.py',
                    'autoptsclient_bot.py test/configs/config_mynewt.py',
                    'autoptsclient_bot.py test/configs/config_external_bot.py',
                    ]

        for args in testargs:
            with patch.object(sys, 'argv', args.split(' ')):
                projects, _ = import_bot_projects()
                project = projects[0]
                bot_module = import_bot_module(project)
                bot_client_class = getattr(bot_module, 'BotClient', None)
                bot_client = bot_client_class()

                # In case of error parser will return error message or throw
                # an exception
                errmsg = bot_client.parse_config_and_args(project)
                assert errmsg == ''
                assert bot_client.arg_parser is not None
                assert bot_client.parse_config is not None
                assert bot_client.bot_config is not None
                assert bot_client.iut_config is not None
                assert bot_client.args is not None

    def test_bot_run_test_cases(self):
        """Check generation of test case list."""

        testargs = ['autoptsclient_bot.py test/configs/config_zephyr.py',
                    # 'autoptsclient_bot.py test/configs/config_mynewt.py',
                    ]

        def mock_get_project_list():
            return mock_workspace_test_cases.keys()

        def mock_get_test_case_list(project):
            return mock_workspace_test_cases[project]

        def mock_run_test_cases(ptses, test_case_instances, args, stats, **kwargs):
            return TestCaseRunStats([], [], 0, xml_results_file=FILE_PATHS['ALL_STATS_RESULTS_XML_FILE'])

        for args in testargs:
            with patch.object(sys, 'argv', args.split(' ')):
                projects, _ = import_bot_projects()
                project = projects[0]
                bot_module = import_bot_module(project)

                # Use monkey patching and mocking
                bot_module.autoptsclient.run_test_cases = mock_run_test_cases

                bot_client_class = getattr(bot_module, 'BotClient', None)

                for i, (iut_config, expected) in enumerate(test_case_list_generation_samples, 1):
                    bot_client = bot_client_class()
                    bot_client.parse_config_and_args(project)

                    fake_pts = FakeProxy()
                    fake_pts.get_project_list = mock_get_project_list
                    fake_pts.get_test_case_list = mock_get_test_case_list
                    fake_pts.get_system_model = lambda: 'TempleOS'
                    bot_client.ptses.append(fake_pts)

                    bot_client.iut_config = iut_config

                    def fake_apply_config(_args, config_name, *_):
                        assert set(_args.test_cases) == set(expected[config_name]), \
                            f'mock_iut_config_{i} use case failed'

                    bot_client.apply_config = fake_apply_config

                    bot_client.run_test_cases()

    def test_generate_stats(self):
        # Test useful for debugging stats and reports generation

        database_file = DATABASE_FILE
        test_case_db = TestCaseTable('zephyr', database_file)
        errata = report.get_errata('zephyr')
        start_time = 1693378197  # result of time.time()
        duration = 30  # seconds
        end_time = start_time + duration

        test_cases = []
        for project in mock_workspace_test_cases:
            for tc in mock_workspace_test_cases[project]:
                test_cases.append(tc)

        regressions_id = [5, 6, 7, 8]
        progresses_id = [9, 10, 11, 12]
        new_cases_id = [13, 14, 15]

        stats1 = TestCaseRunStats(mock_workspace_test_cases.keys(),
                                  test_cases, 0, None, xml_results_file=FILE_PATHS['ALL_STATS_RESULTS_XML_FILE'])
        # Mock results from a first bot run, to generate regressions,
        # progresses, new cases in a second one.
        for i, tc in enumerate(test_cases):
            status = 'PASS'
            if i in progresses_id:
                status = 'FAIL'
            if i in new_cases_id:
                continue

            stats1.update(tc, end_time, status)
            test_case_db.update_statistics(tc, duration, status)
            end_time = start_time + duration

        results = stats1.get_results()
        regressions = stats1.get_regressions()
        progresses = stats1.get_progresses()

        githubdrive = {
            'path': 'test/mocks/bluetooth-qualification',
            'subdir': 'host/',
        }

        report.make_report_txt(FILE_PATHS['REPORT_TXT_FILE'], results,
                               regressions, progresses, '', errata)
        assert os.path.exists(FILE_PATHS['REPORT_TXT_FILE'])

        first_report_txt = os.path.join(
            githubdrive['path'], githubdrive['subdir'], 'autopts_report',
            os.path.basename(FILE_PATHS['REPORT_TXT_FILE']))

        Path(os.path.dirname(first_report_txt)).mkdir(parents=True, exist_ok=True)
        shutil.move(FILE_PATHS['REPORT_TXT_FILE'], first_report_txt)

        stats = TestCaseRunStats(mock_workspace_test_cases.keys(),
                                 test_cases, 0, test_case_db, xml_results_file=FILE_PATHS['ALL_STATS_RESULTS_XML_FILE'])

        # Mock results from a second bot run.
        # Note one deleted test case.
        for i, tc in enumerate(test_cases[:-1]):
            status = 'PASS'
            if i in regressions_id:
                status = 'FAIL'

            stats.update(tc, end_time, status)
            test_case_db.update_statistics(tc, duration, status)
            end_time = start_time + duration

        summary = stats.get_status_count()
        results = stats.get_results()
        descriptions = stats.get_descriptions()
        regressions = stats.get_regressions()
        progresses = stats.get_progresses()
        new_cases = stats.get_new_cases()

        start_timestamp = '30_08_2023_08_50_01'
        end_time = '30_08_2023_11_30_23'
        repos_info = {'zephyr': {'commit': '123456', 'desc': 'zephyr'}}
        pts_ver = '8_5_0'

        iut_logs = FILE_PATHS['IUT_LOGS_DIR']
        pts_logs = os.path.join(FILE_PATHS['TMP_DIR'], 'zephyr-master')
        xmls = FILE_PATHS['PTS_XMLS_DIR']
        Path(iut_logs).mkdir(parents=True, exist_ok=True)
        Path(pts_logs).mkdir(parents=True, exist_ok=True)
        Path(xmls).mkdir(parents=True, exist_ok=True)

        report.make_report_xlsx(FILE_PATHS['REPORT_XLSX_FILE'], results, summary,
                                regressions, progresses, descriptions, xmls, errata)
        assert os.path.exists(FILE_PATHS['REPORT_XLSX_FILE'])

        report.make_report_txt(FILE_PATHS['REPORT_TXT_FILE'], results,
                               regressions, progresses, '', errata)
        assert os.path.exists(FILE_PATHS['REPORT_TXT_FILE'])

        report.make_report_diff('', FILE_PATHS['REPORT_DIFF_TXT_FILE'],
                                results, regressions, progresses, new_cases)
        assert os.path.exists(FILE_PATHS['REPORT_DIFF_TXT_FILE'])


if __name__ == '__main__':
    unittest.main()
