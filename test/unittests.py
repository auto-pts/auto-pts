import os
import shutil
import sys
import unittest
from os.path import dirname, abspath
from unittest.mock import patch

from autopts.client import FakeProxy
from autoptsclient_bot import import_bot_projects, import_bot_module
from test.mocks.mocked_test_cases import mock_workspace_test_cases, test_case_list_generation_samples


class TestCaseRunStatsMock:
    def __init__(self, projects, test_cases, retry_count, db=None):
        pass

    def update(self, test_case_name, duration, status):
        return [], []

    def get_results(self):
        return {}

    def get_regressions(self):
        return []

    def get_progresses(self):
        return []

    def get_status_count(self):
        return {}

    def print_summary(self):
        pass


class MyTestCase(unittest.TestCase):
    def setUp(self):
        os.chdir(dirname(dirname(abspath(__file__))))
        open('ttyUSB', 'w').close()
        shutil.copy('test/configs/config_zephyr.py', 'autopts/bot/config.py')

    def tearDown(self):
        os.remove('ttyUSB')
        os.remove('autopts/bot/config.py')

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

        def mock_run_test_cases(ptses, test_case_instances, args, retry_config=None):
            return TestCaseRunStatsMock([], [], 0)

        for args in testargs:
            with patch.object(sys, 'argv', args.split(' ')):
                projects, _ = import_bot_projects()
                project = projects[0]
                bot_module = import_bot_module(project)

                # Use monkey patching and mocking
                bot_module.autoptsclient.run_test_cases = mock_run_test_cases
                bot_module.autoptsclient.print = mock_run_test_cases

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
                    bot_client.apply_config = lambda _args, config_name, *_: \
                        self.assertTrue(set(_args.test_cases) == set(expected[config_name]),
                                        f'mock_iut_config_{i} use case failed')
                    bot_client.run_test_cases()


if __name__ == '__main__':
    unittest.main()
